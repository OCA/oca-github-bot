# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from .. import github
from ..config import GITHUB_CHECK_SUITES_IGNORED, GITHUB_STATUS_IGNORED, switchable
from ..manifest import bump_manifest_version, git_modified_addons
from ..queue import getLogger, task
from ..version_branch import make_merge_bot_branch, parse_merge_bot_branch
from .main_branch_bot import main_branch_bot_actions

_logger = getLogger(__name__)

LABEL_MERGED = "merged 🎉"


def _git_call(cmd):
    subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.STDOUT)


def _merge_bot_merge_pr(org, repo, merge_bot_branch, dry_run=False):
    pr, target_branch, username, bumpversion = parse_merge_bot_branch(merge_bot_branch)
    # first check if the merge bot branch is still on top of the target branch
    _git_call(["git", "checkout", target_branch])
    r = subprocess.call(
        ["git", "merge-base", "--is-ancestor", target_branch, merge_bot_branch]
    )
    if r != 0:
        _logger.info(
            f"{merge_bot_branch} can't be fast forwarded on {target_branch}, "
            f"rebasing again."
        )
        merge_bot_start(org, repo, pr, username, bumpversion, dry_run)
        return False
    # bump version
    _git_call(["git", "checkout", merge_bot_branch])
    if bumpversion:
        for addon in git_modified_addons(".", target_branch):
            bump_manifest_version(addon, bumpversion, git_commit=True)
    # create the merge commit
    _git_call(["git", "checkout", target_branch])
    msg = f"Merge PR #{pr} into {target_branch}\n\nSigned-off-by {username}"
    _git_call(["git", "merge", "--no-ff", "--m", msg, merge_bot_branch])
    _git_call(["git", "push", "origin", target_branch])
    try:
        # delete merge bot branch
        _git_call(["git", "push", "origin", f":{merge_bot_branch}"])
    except subprocess.CalledProcessError:
        # remote branch may not exist on remote
        pass
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        merge_sha = github.git_get_head_sha()
        github.gh_call(
            gh_pr.create_comment,
            f"Merged at {merge_sha}. Don't worry if GitHub says there are "
            f"unmerged commits: it is due to a rebase before merge. "
            f"All your commits safely landed on the main branch.",
        )
        gh_issue = github.gh_call(gh_pr.issue)
        github.gh_call(gh_issue.add_labels, LABEL_MERGED)
        github.gh_call(gh_pr.close)
    return True


@task()
@switchable("merge_bot")
def merge_bot_start(org, repo, pr, username, bumpversion=None, dry_run=False):
    with github.login() as gh:
        if not github.git_user_can_push(gh.repository(org, repo), username):
            gh_pr = gh.pull_request(org, repo, pr)
            github.gh_call(
                gh_pr.create_comment,
                f"Sorry @{username} "
                f"you do not have push permission, so I can't merge for you.",
            )
            return
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        try:
            with github.temporary_clone(org, repo, target_branch):
                # create merge bot branch from PR and rebase it on target branch
                merge_bot_branch = make_merge_bot_branch(
                    pr, target_branch, username, bumpversion
                )
                _git_call(
                    ["git", "fetch", "origin", f"pull/{pr}/head:{merge_bot_branch}"]
                )
                _git_call(["git", "checkout", merge_bot_branch])
                _git_call(["git", "rebase", "--autosquash", target_branch])
                # run main branch bot actions
                main_branch_bot_actions(org, repo, target_branch, dry_run)
                # push and let tests run again
                try:
                    # delete merge bot branch
                    _git_call(["git", "push", "origin", f":{merge_bot_branch}"])
                except subprocess.CalledProcessError:
                    # remote branch may not exist on remote
                    pass
                _git_call(["git", "push", "origin", merge_bot_branch])
                github.gh_call(
                    gh_pr.create_comment,
                    f"Rebased to [{merge_bot_branch}]"
                    f"(https://github.com/{org}/{repo}/commits/{merge_bot_branch})"
                    f", awaiting test results.",
                )
        except subprocess.CalledProcessError as e:
            cmd = " ".join(e.cmd)
            github.gh_call(
                gh_pr.create_comment,
                f"Command `{cmd}` failed with output:\n```\n{e.output}\n```",
            )
            raise


def _get_commit_success(gh_commit):
    """ Test commit status, using both status and check suites APIs """
    success = None  # None means don't know / in progress
    gh_status = github.gh_call(gh_commit.status)
    for status in gh_status.statuses:
        if status.context in GITHUB_STATUS_IGNORED:
            # ignore
            continue
        if status.state == "success":
            success = True
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
        pr, _, _, _ = parse_merge_bot_branch(merge_bot_branch)
        with github.login() as gh:
            gh_repo = gh.repository(org, repo)
            gh_commit = github.gh_call(gh_repo.commit, sha)
            success = _get_commit_success(gh_commit)
            if success is None:
                # checks in progress
                return
            elif success:
                _merge_bot_merge_pr(org, repo, merge_bot_branch)
            else:
                gh_pr = gh.pull_request(org, repo, pr)
                github.gh_call(
                    gh_pr.create_comment,
                    f"Merge command aborted due to a failed check at {sha}.",
                )
                _git_call(["git", "push", "origin", f":{merge_bot_branch}"])
