# Copyright 2019 Simone Rubino - Agile Business Group
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import config, github
from ..config import switchable
from ..manifest import (
    addon_dirs_in,
    get_maintainers,
    git_modified_addon_dirs,
    is_addon_dir,
)
from ..process import check_call
from ..queue import getLogger, task

_logger = getLogger(__name__)


@task()
@switchable("mention_maintainer")
def mention_maintainer(org, repo, pr, dry_run=False):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        with github.temporary_clone(org, repo, target_branch) as clonedir:
            # Get maintainers existing before the PR changes
            addon_dirs = addon_dirs_in(clonedir, installable_only=True)
            other_branches = config.MAINTAINER_CHECK_ODOO_RELEASES
            main_branches = [target_branch] + other_branches
            maintainers_dict = get_maintainers(
                addon_dirs,
                main_branches=main_branches,
                cwd=clonedir,
            )

            # Get list of addons modified in the PR.
            pr_branch = f"tmp-pr-{pr}"
            check_call(
                ["git", "fetch", "origin", f"refs/pull/{pr}/head:{pr_branch}"],
                cwd=clonedir,
            )
            check_call(["git", "checkout", pr_branch], cwd=clonedir)
            modified_addon_dirs, _, _ = git_modified_addon_dirs(clonedir, target_branch)

            # Remove not installable addons
            # (case where an addon becomes no more installable).
            modified_addon_dirs = [
                d
                for d in modified_addon_dirs
                if is_addon_dir(d, installable_only=True, cwd=clonedir)
            ]

            # Get maintainer of new addons in other branches
            if other_branches:
                new_addons = {
                    addon for addon in modified_addon_dirs if addon not in addon_dirs
                }
                if new_addons:
                    new_maintainers_dict = get_maintainers(
                        new_addons,
                        main_branches=other_branches,
                        cwd=clonedir,
                    )
                    maintainers_dict.update(
                        {
                            new_addon: new_maintainers_dict[new_addon]
                            for new_addon in new_addons
                        }
                    )
                    modified_addon_dirs.extend(new_addons)

        modified_addons_maintainers = set()
        for modified_addon in modified_addon_dirs:
            addon_maintainers = maintainers_dict.get(modified_addon, list())
            modified_addons_maintainers.update(addon_maintainers)

        pr_opener = gh_pr.user.login
        if modified_addon_dirs and not modified_addons_maintainers:
            all_mentions_comment = get_adopt_mention(pr_opener)
        else:
            modified_addons_maintainers.discard(pr_opener)
            all_mentions_comment = get_mention(modified_addons_maintainers)

        if not all_mentions_comment:
            return

        if dry_run:
            _logger.info(f"DRY-RUN Comment {all_mentions_comment}")
        else:
            _logger.info(f"Comment {all_mentions_comment}")
            return github.gh_call(gh_pr.create_comment, all_mentions_comment)


def get_mention(maintainers):
    """Get a comment mentioning all the `maintainers`."""
    maintainers_mentions = list(map(lambda m: "@" + m, maintainers))
    mentions_comment = ""
    if maintainers_mentions:
        mentions_comment = (
            "Hi " + ", ".join(maintainers_mentions) + ",\n"
            "some modules you are maintaining are being modified, "
            "check this out!"
        )
    return mentions_comment


def get_adopt_mention(pr_opener):
    """Get a comment inviting to adopt the module."""
    if config.ADOPT_AN_ADDON_MENTION:
        return config.ADOPT_AN_ADDON_MENTION.format(pr_opener=pr_opener)
    return None
