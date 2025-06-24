#  Copyright 2022 Simone Rubino - TAKOBI
#  Distributed under the MIT License (http://opensource.org/licenses/MIT).
import os.path
import re

from .. import config, github
from ..config import switchable
from ..manifest import addon_dirs_in
from ..process import check_call
from ..queue import getLogger, task
from .migration_issue_bot import _find_branch_milestone, _find_issue

_logger = getLogger(__name__)


def _get_added_modules(org, repo, gh_pr):
    target_branch = gh_pr.base.ref
    with github.temporary_clone(org, repo, target_branch) as clonedir:
        # We need a list now because otherwise modules
        # are yielded when the directory is already changed
        existing_addons_paths = list(addon_dirs_in(clonedir, installable_only=True))

        pr_branch = f"tmp-pr-{gh_pr.number}"
        check_call(
            ["git", "fetch", "origin", f"refs/pull/{gh_pr.number}/head:{pr_branch}"],
            cwd=clonedir,
        )
        check_call(["git", "checkout", pr_branch], cwd=clonedir)
        pr_addons_paths = addon_dirs_in(clonedir, installable_only=True)

        new_addons_paths = {
            addon_path
            for addon_path in pr_addons_paths
            if addon_path not in existing_addons_paths
        }
    return new_addons_paths


def is_migration_pr(org, repo, pr):
    """
    Determine if the PR is a migration.
    """
    with github.login() as gh:
        gh_repo = gh.repository(org, repo)
        gh_pr = gh_repo.pull_request(pr)
        target_branch = gh_pr.base.ref
        milestone = _find_branch_milestone(gh_repo, target_branch)
        gh_migration_issue = _find_issue(gh_repo, milestone, target_branch)

        # The PR is mentioned in the migration issue
        pr_regex = re.compile(rf"#({gh_pr.number})")
        found_pr = pr_regex.findall(gh_migration_issue.body)
        if found_pr:
            return True

        # The added module is mentioned in the migration issue
        new_addons_paths = _get_added_modules(org, repo, gh_pr)
        new_addons = map(os.path.basename, new_addons_paths)
        for addon in new_addons:
            module_regex = re.compile(rf"- \[[ x]] {addon}")
            found_module = module_regex.search(gh_migration_issue.body)
            if found_module:
                return True

        # The Title of the PR contains [MIG]
        pr_title = gh_pr.title
        if "[MIG]" in pr_title:
            return True
    return False


@task()
@switchable("comment_migration_guidelines")
def comment_migration_guidelines(org, repo, pr, dry_run=False):
    migration_reminder = config.MIGRATION_GUIDELINES_REMINDER
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        return github.gh_call(gh_pr.create_comment, migration_reminder)
