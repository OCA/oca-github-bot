# Copyright (c) ACSONE SA/NV 2024
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import github
from ..config import MODULE_LABEL_COLOR, switchable
from ..manifest import git_modified_addons
from ..process import check_call
from ..queue import task
from ..utils import compute_module_label_name
from ..version_branch import is_main_branch_bot_branch


def _label_modified_addons(gh, org, repo, pr, dry_run):
    gh_repo = gh.repository(org, repo)
    gh_pr = gh.pull_request(org, repo, pr)
    target_branch = gh_pr.base.ref
    pr_branch = f"tmp-pr-{pr}"
    with github.temporary_clone(org, repo, target_branch) as clone_dir:
        check_call(
            ["git", "fetch", "origin", f"pull/{pr}/head:{pr_branch}"],
            cwd=clone_dir,
        )
        check_call(["git", "checkout", pr_branch], cwd=clone_dir)
        modified_addons, _ = git_modified_addons(clone_dir, target_branch)
        if not modified_addons:
            return
        gh_issue = github.gh_call(gh_pr.issue)

        new_labels = set()
        for modified_addon in modified_addons:
            label_name = compute_module_label_name(modified_addon)
            # We create label at repo level, because it is possible to
            # to set description in create_label() function
            # (and not in issue.add_labels())
            if label_name not in [x.name for x in gh_repo.labels()] and not dry_run:
                github.gh_call(
                    gh_repo.create_label,
                    name=label_name,
                    description=f"Module {modified_addon}",
                    color=MODULE_LABEL_COLOR.replace("#", ""),
                )
            new_labels.add(label_name)

        if is_main_branch_bot_branch(target_branch):
            new_labels.add(f"series:{target_branch}")
        new_labels = new_labels - {label.name for label in gh_issue.labels()}
        if new_labels and not dry_run:
            for new_label in new_labels:
                github.gh_call(gh_issue.add_labels, new_label)


@task()
@switchable("label_modified_addons")
def label_modified_addons(org, repo, pr, dry_run=False):
    with github.login() as gh:
        _label_modified_addons(gh, org, repo, pr, dry_run)
