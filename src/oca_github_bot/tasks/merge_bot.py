# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from ..github import temporary_clone
from ..manifest import bump_manifest_version, git_modified_addons
from ..queue import getLogger, task
from ..version_branch import make_merge_bot_branch
from .main_branch_bot import main_branch_bot_actions

_logger = getLogger(__name__)


@task()
def merge_bot_start(
    org, repo, pr, target_branch, user, bumpversion=None, dry_run=False
):
    # TODO check user has write access when reaching this point
    # TODO error handling
    with temporary_clone(org, repo, target_branch):
        # create merge bot branch from PR and rebase it on target branch
        merge_bot_branch = make_merge_bot_branch(pr, target_branch)
        subprocess.check_output(
            ["git", "fetch", "origin", f"pull/{pr}/head:{merge_bot_branch}"]
        )
        subprocess.check_output(["git", "checkout", merge_bot_branch])
        subprocess.check_output(["git", "rebase", target_branch])
        # run main branch bot actions
        main_branch_bot_actions(org, repo, target_branch, dry_run)
        if bumpversion:
            for addon in git_modified_addons(".", target_branch):
                bump_manifest_version(addon, bumpversion, git_commit=True)
        # push
        subprocess.check_call(["git", "push", "--force", "origin", merge_bot_branch])
