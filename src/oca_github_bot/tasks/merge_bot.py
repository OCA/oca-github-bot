# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os
import random
import subprocess
from enum import Enum

from .. import github
from ..build_wheels import build_and_check_wheel, build_and_publish_wheel
from ..config import (
    GITHUB_CHECK_SUITES_IGNORED,
    GITHUB_STATUS_IGNORED,
    MERGE_BOT_INTRO_MESSAGES,
    SIMPLE_INDEX_ROOT,
    switchable,
)
from ..manifest import bump_manifest_version, git_modified_addon_dirs, is_maintainer
from ..queue import getLogger, task
from ..version_branch import make_merge_bot_branch, parse_merge_bot_branch
from .main_branch_bot import main_branch_bot_actions

_logger = getLogger(__name__)

LABEL_MERGED = "merged 🎉"


class MergeStrategy(Enum):
    rebase_autosquash = 1
    merge = 2


def _git_call(cmd, cwd="."):
    subprocess.check_output(
        cmd, universal_newlines=True, stderr=subprocess.STDOUT, cwd=cwd
    )


def _git_delete_branch(remote, branch):
    try:
        # delete merge bot branch
        _git_call(["git", "push", remote, f":{branch}"])
    except subprocess.CalledProcessError as e:
        if "unable to delete" in e.output:
            # remote branch may not exist on remote
            pass
        else:
            raise


def _get_merge_bot_intro_message():
    i = random.randint(0, len(MERGE_BOT_INTRO_MESSAGES) - 1)
    return MERGE_BOT_INTRO_MESSAGES[i]


def _merge_bot_merge_pr(org, repo, merge_bot_branch, dry_run=False):
    pr, target_branch, username, bumpversion = parse_merge_bot_branch(merge_bot_branch)
    # first check if the merge bot branch is still on top of the target branch
    _git_call(["git", "checkout", target_branch])
    r = subprocess.call(
        ["git", "merge-base", "--is-ancestor", target_branch, merge_bot_branch]
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
            bumpversion,
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
    _git_call(["git", "fetch", "origin", f"refs/pull/{pr}/head:tmp-pr-{pr}"])
    _git_call(["git", "checkout", f"tmp-pr-{pr}"])
    modified_addon_dirs, _ = git_modified_addon_dirs(".", target_branch)
    # Run main branch bot actions before bump version.
    # Do not run the main branch bot if there are no modified addons,
    # because it is dedicated to addons repos.
    _git_call(["git", "checkout", merge_bot_branch])
    if modified_addon_dirs:
        main_branch_bot_actions(org, repo, target_branch)
    for addon_dir in modified_addon_dirs:
        # TODO wlc lock and push
        # TODO msgmerge and commit
        if bumpversion:
            bump_manifest_version(addon_dir, bumpversion, git_commit=True)
            build_and_check_wheel(addon_dir)
    if dry_run:
        _logger.info(f"DRY-RUN git push in {org}/{repo}@{target_branch}")
    else:
        _logger.info(f"git push in {org}/{repo}@{target_branch}")
        _git_call(["git", "push", "origin", f"{merge_bot_branch}:{target_branch}"])
    # build and publish wheel
    if bumpversion and modified_addon_dirs and SIMPLE_INDEX_ROOT:
        for addon_dir in modified_addon_dirs:
            build_and_publish_wheel(addon_dir, SIMPLE_INDEX_ROOT, dry_run)
    # TODO wlc unlock modified_addons
    _git_delete_branch("origin", merge_bot_branch)
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        merge_sha = github.git_get_head_sha()
        github.gh_call(
            gh_pr.create_comment,
            f"Congratulations, your PR was merged at {merge_sha}. "
            f"Thanks a lot for contributing to {org}. ❤️",
        )
        gh_issue = github.gh_call(gh_pr.issue)
        if dry_run:
            _logger.info(f"DRY-RUN add {LABEL_MERGED} label to PR {gh_pr.url}")
        else:
            _logger.info(f"add {LABEL_MERGED} label to PR {gh_pr.url}")
            github.gh_call(gh_issue.add_labels, LABEL_MERGED)
        github.gh_call(gh_pr.close)
    return True


def _user_can_merge(gh, org, repo, username, addons_dir, target_branch):
    """
    Check if a user is allowed to merge.

    addons_dir must be a git clone of the branch to merge to target_branch.
    """
    gh_repo = gh.repository(org, repo)
    if github.github_user_can_push(gh_repo, username):
        return True
    modified_addon_dirs, other_changes = git_modified_addon_dirs(
        addons_dir, target_branch
    )
    if other_changes or not modified_addon_dirs:
        return False
    # if we are modifying addons only, then the user must be maintainer of
    # all of them on the target branch
    current_branch = github.git_get_current_branch(cwd=addons_dir)
    try:
        _git_call(["git", "checkout", target_branch], cwd=addons_dir)
        return is_maintainer(username, modified_addon_dirs)
    finally:
        _git_call(["git", "checkout", current_branch], cwd=addons_dir)


def _prepare_merge_bot_branch(
    merge_bot_branch, target_branch, pr_branch, pr, username, merge_strategy
):
    if merge_strategy == MergeStrategy.merge:
        # nothing to do on the pr branch
        pass
    elif merge_strategy == MergeStrategy.rebase_autosquash:
        # rebase the pr branch onto the target branch
        _git_call(["git", "checkout", pr_branch])
        _git_call(
            ["git", "rebase", "--autosquash", "-i", target_branch],
            env=dict(os.environ, GIT_SEQUENCE_EDITOR="true"),
        )
    # create the merge commit
    _git_call(["git", "checkout", "-B", merge_bot_branch, target_branch])
    msg = f"Merge PR #{pr} into {target_branch}\n\nSigned-off-by {username}"
    _git_call(["git", "merge", "--no-ff", "-m", msg, pr_branch])


@task()
@switchable("merge_bot")
def merge_bot_start(
    org,
    repo,
    pr,
    username,
    bumpversion=None,
    dry_run=False,
    intro_message=None,
    merge_strategy=MergeStrategy.merge,
):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        merge_bot_branch = make_merge_bot_branch(
            pr, target_branch, username, bumpversion
        )
        pr_branch = f"tmp-pr-{pr}"
        try:
            with github.temporary_clone(org, repo, target_branch):
                # create merge bot branch from PR and rebase it on target branch
                _git_call(["git", "fetch", "origin", f"pull/{pr}/head:{pr_branch}"])
                _git_call(["git", "checkout", pr_branch])
                if not _user_can_merge(gh, org, repo, username, ".", target_branch):
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
                )
                # push and let tests run again; delete on origin
                # to be sure GitHub sees it as a new branch and relaunches all checks
                _git_delete_branch("origin", merge_bot_branch)
                _git_call(["git", "push", "origin", merge_bot_branch])
                if not intro_message:
                    intro_message = _get_merge_bot_intro_message()
                github.gh_call(
                    gh_pr.create_comment,
                    f"{intro_message}\n"
                    f"Prepared branch [{merge_bot_branch}]"
                    f"(https://github.com/{org}/{repo}/commits/{merge_bot_branch}), "
                    f"awaiting test results.",
                )
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            github.gh_call(
                gh_pr.create_comment,
                f"@{username} The merge process could not start, because "
                f"command `{cmd}` failed with output:\n```\n{e.output}\n```",
            )
            raise
        except Exception as e:
            github.gh_call(
                gh_pr.create_comment,
                f"@{username} The merge process could not start, because "
                f"of exception {e}.",
            )
            raise


def _get_commit_success(gh_commit):
    """ Test commit status, using both status and check suites APIs """
    success = None  # None means don't know / in progress
    old_travis = False
    gh_status = github.gh_call(gh_commit.status)
    for status in gh_status.statuses:
        if status.context in GITHUB_STATUS_IGNORED:
            # ignore
            continue
        if status.state == "success":
            success = True
            # <hack>
            if status.context.startswith("continuous-integration/travis-ci"):
                old_travis = True
            # </hack>
        elif status.state == "pending":
            # in progress
            return None
        else:
            return False
    gh_check_suites = github.gh_call(gh_commit.check_suites)
    for check_suite in gh_check_suites:
        if check_suite.app.name in GITHUB_CHECK_SUITES_IGNORED:
            # ignore
            continue
        if check_suite.conclusion == "success":
            success = True
        elif not check_suite.conclusion:
            # not complete
            # <hack>
            if check_suite.app.name == "Travis CI" and old_travis:
                # ignore incomplete new Travis when old travis status is ok
                continue
            # </hack>
            return None
        else:
            return False
    return success


@task()
@switchable("merge_bot")
def merge_bot_status(org, repo, merge_bot_branch, sha):
    with github.temporary_clone(org, repo, merge_bot_branch):
        head_sha = github.git_get_head_sha()
        if head_sha != sha:
            # the branch has evolved, this means that this status
            # does not correspond to the last commit of the bot, ignore it
            return
        pr, _, username, _ = parse_merge_bot_branch(merge_bot_branch)
        with github.login() as gh:
            gh_repo = gh.repository(org, repo)
            gh_pr = gh.pull_request(org, repo, pr)
            gh_commit = github.gh_call(gh_repo.commit, sha)
            success = _get_commit_success(gh_commit)
            if success is None:
                # checks in progress
                return
            elif success:
                try:
                    _merge_bot_merge_pr(org, repo, merge_bot_branch)
                except subprocess.CalledProcessError as e:
                    cmd = " ".join(e.cmd)
                    github.gh_call(
                        gh_pr.create_comment,
                        f"@{username} The merge process could not be "
                        f"finalized, because "
                        f"command `{cmd}` failed with output:\n```\n{e.output}\n```",
                    )
                    raise
                except Exception as e:
                    github.gh_call(
                        gh_pr.create_comment,
                        f"@{username} The merge process could not be "
                        f"finalized because an exception was raised: {e}.",
                    )
                    raise
            else:
                github.gh_call(
                    gh_pr.create_comment,
                    f"@{username} your merge command was aborted due to failed "
                    f"check(s), which you can inspect on "
                    f"[this commit of {merge_bot_branch}]"
                    f"(https://github.com/{org}/{repo}/commits/{sha}).\n\n"
                    f"After fixing the problem, you can re-issue a merge command. "
                    f"Please refrain from merging manually as it will most probably "
                    f"make the target branch red.",
                )
                _git_call(["git", "push", "origin", f":{merge_bot_branch}"])
