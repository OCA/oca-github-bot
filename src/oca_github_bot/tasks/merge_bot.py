# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import contextlib
import random
from enum import Enum

from .. import github
from ..build_wheels import build_and_publish_wheel
from ..config import (
    GITHUB_CHECK_SUITES_IGNORED,
    GITHUB_STATUS_IGNORED,
    MERGE_BOT_INTRO_MESSAGES,
    dist_publisher,
    switchable,
)
from ..manifest import (
    bump_manifest_version,
    bump_version,
    get_manifest,
    git_modified_addon_dirs,
    is_addon_dir,
    user_can_push,
)
from ..process import CalledProcessError, call, check_call
from ..queue import getLogger, task
from ..utils import cmd_to_str, hide_secrets
from ..version_branch import make_merge_bot_branch, parse_merge_bot_branch
from .main_branch_bot import main_branch_bot_actions
from .migration_issue_bot import _mark_migration_done_in_migration_issue

_logger = getLogger(__name__)

LABEL_MERGED = "merged 🎉"
LABEL_MERGING = "bot is merging ⏳"


class MergeStrategy(Enum):
    rebase_autosquash = 1
    merge = 2


def _git_delete_branch(remote, branch, cwd):
    try:
        # delete merge bot branch
        check_call(["git", "push", remote, f":{branch}"], cwd=cwd, log_error=False)
    except CalledProcessError as e:
        if "unable to delete" in e.output:
            # remote branch may not exist on remote
            pass
        else:
            _logger.error(
                f"command {e.cmd} failed with return code {e.returncode} "
                f"and output:\n{e.output}"
            )
            raise


def _remove_merging_label(github, gh_pr, dry_run=False):
    gh_issue = github.gh_call(gh_pr.issue)
    labels = [label.name for label in gh_issue.labels()]
    if LABEL_MERGING in labels:
        if dry_run:
            _logger.info(f"DRY-RUN remove {LABEL_MERGING} label from PR {gh_pr.url}")
        else:
            _logger.info(f"remove {LABEL_MERGING} label from PR {gh_pr.url}")
            github.gh_call(gh_issue.remove_label, LABEL_MERGING)


def _get_merge_bot_intro_message():
    i = random.randint(0, len(MERGE_BOT_INTRO_MESSAGES) - 1)
    return MERGE_BOT_INTRO_MESSAGES[i]


@switchable("merge_bot_towncrier")
def _merge_bot_towncrier(org, repo, target_branch, addon_dirs, bumpversion_mode, cwd):
    for addon_dir in addon_dirs:
        # Run oca-towncrier: this updates and git add readme/HISTORY.rst
        # if readme/newsfragments contains files and does nothing otherwise.
        _logger.info(f"oca-towncrier {org}/{repo}@{target_branch} for {addon_dirs}")
        version = bump_version(get_manifest(addon_dir)["version"], bumpversion_mode)
        check_call(
            [
                "oca-towncrier",
                "--org",
                org,
                "--repo",
                repo,
                "--addon-dir",
                addon_dir,
                "--version",
                version,
                "--commit",
            ],
            cwd=cwd,
        )


def _merge_bot_merge_pr(org, repo, merge_bot_branch, cwd, dry_run=False):
    pr, target_branch, username, bumpversion_mode = parse_merge_bot_branch(
        merge_bot_branch
    )
    # first check if the merge bot branch is still on top of the target branch
    check_call(["git", "checkout", target_branch], cwd=cwd)
    r = call(
        ["git", "merge-base", "--is-ancestor", target_branch, merge_bot_branch], cwd=cwd
    )
    if r != 0:
        _logger.info(
            f"{merge_bot_branch} can't be fast forwarded on {target_branch}, retrying."
        )
        intro_message = (
            f"It looks like something changed on `{target_branch}` in the meantime.\n"
            f"Let me try again (no action is required from you)."
        )
        merge_bot_start(
            org,
            repo,
            pr,
            username,
            bumpversion_mode,
            dry_run=dry_run,
            intro_message=intro_message,
        )
        return False
    # Get modified addons list on the PR and not on the merge bot branch
    # because travis .pot generation may sometimes touch
    # other addons unrelated to the PR and we don't want to bump
    # version on those. This is also the least surprising approach, bumping
    # version only on addons visibly modified on the PR, and not on
    # other addons that may be modified by the bot for reasons unrelated
    # to the PR.
    check_call(["git", "fetch", "origin", f"refs/pull/{pr}/head:tmp-pr-{pr}"], cwd=cwd)
    check_call(["git", "checkout", f"tmp-pr-{pr}"], cwd=cwd)
    modified_addon_dirs, _, _ = git_modified_addon_dirs(cwd, target_branch)
    check_call(["git", "checkout", merge_bot_branch], cwd=cwd)

    head_sha = github.git_get_head_sha(cwd)

    # list installable modified addons only
    modified_installable_addon_dirs = [
        d for d in modified_addon_dirs if is_addon_dir(d, installable_only=True)
    ]

    # Update HISTORY.rst using towncrier, before generating README.rst.
    # We don't do this if nobump is specified, because updating the changelog
    # is something we only do when "releasing", and patch|minor|major is
    # the way to mean "release" in OCA.
    if bumpversion_mode != "nobump":
        _merge_bot_towncrier(
            org,
            repo,
            target_branch,
            modified_installable_addon_dirs,
            bumpversion_mode,
            cwd,
        )

    # bump manifest version of modified installable addons
    if bumpversion_mode != "nobump":
        for addon_dir in modified_installable_addon_dirs:
            # bumpversion is last commit (after readme generation etc
            # and before building wheel),
            # so setuptools-odoo and whool generate a round version number
            # (without .dev suffix).
            bump_manifest_version(addon_dir, bumpversion_mode, git_commit=True)

    # run the main branch bot actions only if there are modified addon directories,
    # so we don't run them when the merge bot branch for non-addons repos
    if modified_addon_dirs:
        # this includes setup.py and README.rst generation
        main_branch_bot_actions(org, repo, target_branch, cwd=cwd)

    # squash post merge commits into one (bumpversion, readme generator, etc),
    # to avoid a proliferation of automated actions commits
    if github.git_get_head_sha(cwd) != head_sha:
        check_call(["git", "reset", "--soft", head_sha], cwd=cwd)
        check_call(["git", "commit", "-m", "[BOT] post-merge updates"], cwd=cwd)

    # We publish to PyPI before merging, because we don't want to merge
    # if PyPI rejects the upload for any reason. There is a possibility
    # that the upload succeeds and then the merge fails, but that should be
    # exceptional, and it is better than the contrary.
    for addon_dir in modified_installable_addon_dirs:
        build_and_publish_wheel(addon_dir, dist_publisher, dry_run)

    if dry_run:
        _logger.info(f"DRY-RUN git push in {org}/{repo}@{target_branch}")
    else:
        _logger.info(f"git push in {org}/{repo}@{target_branch}")
        check_call(
            ["git", "push", "origin", f"{merge_bot_branch}:{target_branch}"], cwd=cwd
        )

    # TODO wlc unlock modified_addons

    # delete merge bot branch
    _git_delete_branch("origin", merge_bot_branch, cwd=cwd)

    # notify sucessful merge in PR comments and labels
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        gh_repo = gh.repository(org, repo)
        merge_sha = github.git_get_head_sha(cwd=cwd)
        github.gh_call(
            gh_pr.create_comment,
            f"Congratulations, your PR was merged at {merge_sha}. "
            f"Thanks a lot for contributing to {org}. ❤️",
        )
        gh_issue = github.gh_call(gh_pr.issue)
        _remove_merging_label(github, gh_pr, dry_run=dry_run)
        if dry_run:
            _logger.info(f"DRY-RUN add {LABEL_MERGED} label to PR {gh_pr.url}")
        else:
            _logger.info(f"add {LABEL_MERGED} label to PR {gh_pr.url}")
            github.gh_call(gh_issue.add_labels, LABEL_MERGED)
        github.gh_call(gh_pr.close)

        # Check line in migration issue if required
        _mark_migration_done_in_migration_issue(gh_repo, target_branch, gh_pr)
    return True


def _prepare_merge_bot_branch(
    merge_bot_branch, target_branch, pr_branch, pr, username, merge_strategy, cwd
):
    if merge_strategy == MergeStrategy.merge:
        # nothing to do on the pr branch
        pass
    elif merge_strategy == MergeStrategy.rebase_autosquash:
        # rebase the pr branch onto the target branch
        check_call(["git", "checkout", pr_branch], cwd=cwd)
        check_call(["git", "rebase", "--autosquash", "-i", target_branch], cwd=cwd)
    # create the merge commit
    check_call(["git", "checkout", "-B", merge_bot_branch, target_branch], cwd=cwd)
    msg = f"Merge PR #{pr} into {target_branch}\n\nSigned-off-by {username}"
    check_call(["git", "merge", "--no-ff", "-m", msg, pr_branch], cwd=cwd)


@task()
@switchable("merge_bot")
def merge_bot_start(
    org,
    repo,
    pr,
    username,
    bumpversion_mode,
    dry_run=False,
    intro_message=None,
    merge_strategy=MergeStrategy.merge,
):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        merge_bot_branch = make_merge_bot_branch(
            pr, target_branch, username, bumpversion_mode
        )
        pr_branch = f"tmp-pr-{pr}"
        try:
            with github.temporary_clone(org, repo, target_branch) as clone_dir:
                # create merge bot branch from PR and rebase it on target branch
                check_call(
                    ["git", "fetch", "origin", f"pull/{pr}/head:{pr_branch}"],
                    cwd=clone_dir,
                )
                check_call(["git", "checkout", pr_branch], cwd=clone_dir)
                if not user_can_push(gh, org, repo, username, clone_dir, target_branch):
                    github.gh_call(
                        gh_pr.create_comment,
                        f"Sorry @{username} you are not allowed to merge.\n\n"
                        f"To do so you must either have push permissions on "
                        f"the repository, or be a declared maintainer of all "
                        f"modified addons.\n\n"
                        f"If you wish to adopt an addon and become it's "
                        f"[maintainer]"
                        f"(https://odoo-community.org/page/maintainer-role), "
                        f"open a pull request to add "
                        f"your GitHub login to the `maintainers` key of its "
                        f"manifest.",
                    )
                    return
                # TODO for each modified addon, wlc lock / commit / push
                # TODO then pull target_branch again
                _prepare_merge_bot_branch(
                    merge_bot_branch,
                    target_branch,
                    pr_branch,
                    pr,
                    username,
                    merge_strategy,
                    cwd=clone_dir,
                )
                # push and let tests run again; delete on origin
                # to be sure GitHub sees it as a new branch and relaunches all checks
                _git_delete_branch("origin", merge_bot_branch, cwd=clone_dir)
                check_call(["git", "push", "origin", merge_bot_branch], cwd=clone_dir)
                if not intro_message:
                    intro_message = _get_merge_bot_intro_message()
                github.gh_call(
                    gh_pr.create_comment,
                    f"{intro_message}\n"
                    f"Prepared branch [{merge_bot_branch}]"
                    f"(https://github.com/{org}/{repo}/commits/{merge_bot_branch}), "
                    f"awaiting test results.",
                )
        except CalledProcessError as e:
            cmd = cmd_to_str(e.cmd)
            github.gh_call(
                gh_pr.create_comment,
                hide_secrets(
                    f"@{username} The merge process could not start, because "
                    f"command `{cmd}` failed with output:\n```\n{e.output}\n```"
                ),
            )
            raise
        except Exception as e:
            github.gh_call(
                gh_pr.create_comment,
                hide_secrets(
                    f"@{username} The merge process could not start, because "
                    f"of exception {e}."
                ),
            )
            raise
        else:
            gh_issue = github.gh_call(gh_pr.issue)
            _logger.info(f"add {LABEL_MERGING} label to PR {gh_pr.url}")
            github.gh_call(gh_issue.add_labels, LABEL_MERGING)


def _get_commit_success(org, repo, pr, gh_commit):
    """Test commit status, using both status and check suites APIs"""
    success = None  # None means don't know / in progress
    gh_status = github.gh_call(gh_commit.status)
    for status in gh_status.statuses:
        if status.context in GITHUB_STATUS_IGNORED:
            # ignore
            _logger.info(
                f"Ignoring status {status.context} for PR #{pr} of {org}/{repo}"
            )
            continue
        if status.state == "success":
            _logger.info(
                f"Successful status {status.context} for PR #{pr} of {org}/{repo}"
            )
            success = True
        elif status.state == "pending":
            # in progress
            _logger.info(
                f"Pending status {status.context} for PR #{pr} of {org}/{repo}"
            )
            return None
        else:
            _logger.info(
                f"Unsuccessful status {status.context} {status.state} for "
                f"PR #{pr} of {org}/{repo}"
            )
            return False
    gh_check_suites = github.gh_call(gh_commit.check_suites)
    for check_suite in gh_check_suites:
        if check_suite.app.name in GITHUB_CHECK_SUITES_IGNORED:
            # ignore
            _logger.info(
                f"Ignoring check suite {check_suite.app.name} for "
                f"PR #{pr} of {org}/{repo}"
            )
            continue
        if check_suite.conclusion == "success":
            _logger.info(
                f"Successful check suite {check_suite.app.name} for "
                f"PR #{pr} of {org}/{repo}"
            )
            success = True
        elif not check_suite.conclusion:
            # not complete
            check_runs = list(github.gh_call(check_suite.check_runs))
            if not check_runs:
                _logger.info(
                    f"Ignoring check suite {check_suite.app.name} "
                    f"that has no check runs for "
                    f"PR #{pr} of {org}/{repo}"
                )
                continue
            _logger.info(
                f"Pending check suite {check_suite.app.name} for "
                f"PR #{pr} of {org}/{repo}"
            )
            return None
        else:
            _logger.info(
                f"Unsuccessful check suite {check_suite.app.name} "
                f"{check_suite.conclusion} for PR #{pr} of {org}/{repo}"
            )
            return False
    return success


@task()
@switchable("merge_bot")
def merge_bot_status(org, repo, merge_bot_branch, sha):
    with contextlib.suppress(github.BranchNotFoundError):
        with github.temporary_clone(org, repo, merge_bot_branch) as clone_dir:
            head_sha = github.git_get_head_sha(cwd=clone_dir)
            if head_sha != sha:
                # the branch has evolved, this means that this status
                # does not correspond to the last commit of the bot, ignore it
                return
            pr, _, username, _ = parse_merge_bot_branch(merge_bot_branch)
            with github.login() as gh:
                gh_repo = gh.repository(org, repo)
                gh_pr = gh.pull_request(org, repo, pr)
                gh_commit = github.gh_call(gh_repo.commit, sha)
                success = _get_commit_success(org, repo, pr, gh_commit)
                if success is None:
                    # checks in progress
                    return
                elif success:
                    try:
                        _merge_bot_merge_pr(org, repo, merge_bot_branch, clone_dir)
                    except CalledProcessError as e:
                        cmd = cmd_to_str(e.cmd)
                        github.gh_call(
                            gh_pr.create_comment,
                            hide_secrets(
                                f"@{username} The merge process could not be "
                                f"finalized, because "
                                f"command `{cmd}` failed with output:\n```\n"
                                f"{e.output}\n```"
                            ),
                        )
                        _remove_merging_label(github, gh_pr)
                        raise
                    except Exception as e:
                        github.gh_call(
                            gh_pr.create_comment,
                            hide_secrets(
                                f"@{username} The merge process could not be "
                                f"finalized because an exception was raised: {e}."
                            ),
                        )
                        _remove_merging_label(github, gh_pr)
                        raise
                else:
                    github.gh_call(
                        gh_pr.create_comment,
                        f"@{username} your merge command was aborted due to failed "
                        f"check(s), which you can inspect on "
                        f"[this commit of {merge_bot_branch}]"
                        f"(https://github.com/{org}/{repo}/commits/{sha}).\n\n"
                        f"After fixing the problem, you can re-issue a merge command. "
                        f"Please refrain from merging manually as it will most "
                        f"probably make the target branch red.",
                    )
                    check_call(
                        ["git", "push", "origin", f":{merge_bot_branch}"], cwd=clone_dir
                    )
                    _remove_merging_label(github, gh_pr)
