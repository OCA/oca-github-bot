# Copyright 2019 Simone Rubino - Agile Business Group
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from celery.task import task

from .. import github
from ..config import switchable
from ..manifest import get_manifest, git_modified_addon_dirs, is_addon_dir
from ..process import check_call
from ..queue import getLogger

_logger = getLogger(__name__)


@task()
@switchable("mention_maintainer")
def mention_maintainer(org, repo, pr, dry_run=False):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        with github.temporary_clone(org, repo, target_branch) as clonedir:
            # Get modified addons list on the PR.
            pr_branch = f"tmp-pr-{pr}"
            check_call(
                ["git", "fetch", "origin", f"refs/pull/{pr}/head:{pr_branch}"],
                cwd=clonedir,
            )
            check_call(["git", "checkout", pr_branch], cwd=clonedir)
            modified_addon_dirs, _ = git_modified_addon_dirs(clonedir, target_branch)
            # Remove not installable addons
            # (case where an addon becomes no more installable).
            modified_installable_addon_dirs = [
                d for d in modified_addon_dirs if is_addon_dir(d, installable_only=True)
            ]

            pr_opener = gh_pr.user.login
            all_mentions_comment = get_maintainers_mentions(
                modified_installable_addon_dirs, pr_opener
            )

        if not all_mentions_comment:
            return False
        if dry_run:
            _logger.info(f"DRY-RUN Comment {all_mentions_comment}")
        else:
            _logger.info(f"Comment {all_mentions_comment}")
            return github.gh_call(gh_pr.create_comment, all_mentions_comment)


def get_maintainers_mentions(addon_dirs, pr_opener):
    all_maintainers = set()
    for addon_dir in addon_dirs:
        maintainers = get_manifest(addon_dir).get("maintainers", [])
        all_maintainers.update(maintainers)
    if pr_opener in all_maintainers:
        all_maintainers.remove(pr_opener)
    if not all_maintainers:
        return ""
    all_mentions = map(lambda m: "@" + m, all_maintainers)
    all_mentions_comment = (
        "Hi " + ", ".join(all_mentions) + ",\n"
        "some modules you are maintaining are being modified, "
        "check this out!"
    )
    return all_mentions_comment
