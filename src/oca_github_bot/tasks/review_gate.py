# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import github
from ..config import REVIEW_GATE_AS_FIRST_FILTER, switchable
from ..github import gh_call
from ..manifest import (
    addon_dirs_in,
    get_addon_name,
    git_modified_addon_dirs,
    is_addon_dir,
)
from ..process import check_call
from ..queue import getLogger, task
from ..review_gate import (
    COMMENT_MARKER,
    LABEL_BOT_CHECKS_PASSED,
    check_addon,
    format_comment,
    merge_results,
)
from .tag_needs_review import tag_needs_review

_logger = getLogger(__name__)


def _upsert_comment(gh_issue, body):
    for comment in gh_issue.comments():
        if COMMENT_MARKER in (comment.body or ""):
            return gh_call(comment.edit, body)
    return gh_call(gh_issue.create_comment, body)


@task()
@switchable("review_gate")
def review_gate(org, repo, pr, dry_run=False):
    """Run mechanical checks and comment on the PR (not a human review)."""
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        with github.temporary_clone(org, repo, target_branch) as clonedir:
            base_names = {
                get_addon_name(d)
                for d in addon_dirs_in(clonedir, installable_only=False)
            }
            pr_branch = f"tmp-pr-{pr}"
            check_call(
                ["git", "fetch", "origin", f"refs/pull/{pr}/head:{pr_branch}"],
                cwd=clonedir,
            )
            check_call(["git", "checkout", pr_branch], cwd=clonedir)
            modified_addon_dirs, _, _ = git_modified_addon_dirs(clonedir, target_branch)
            modified_addon_dirs = [
                d
                for d in modified_addon_dirs
                if is_addon_dir(d, installable_only=False)
            ]
            results = []
            for addon_dir in modified_addon_dirs:
                name = get_addon_name(addon_dir)
                results.append(check_addon(addon_dir, is_new=name not in base_names))
        result = merge_results(results)
        body = format_comment(result)
        gh_issue = gh_pr.issue()
        labels = [label.name for label in gh_issue.labels()]
        if dry_run:
            _logger.info("DRY-RUN review gate on %s/%s#%s: %s", org, repo, pr, body)
            return
        _upsert_comment(gh_issue, body)
        if result.passed:
            if LABEL_BOT_CHECKS_PASSED not in labels:
                gh_call(gh_issue.add_labels, LABEL_BOT_CHECKS_PASSED)
            if REVIEW_GATE_AS_FIRST_FILTER:
                sha = gh_pr.head.sha
                gh_repo = gh.repository(org, repo)
                combined = gh_call(gh_repo.combined_status, sha)
                if getattr(combined, "state", None) == "success":
                    tag_needs_review.delay(org, pr, repo, "success")
        elif LABEL_BOT_CHECKS_PASSED in labels:
            gh_call(gh_issue.remove_label, LABEL_BOT_CHECKS_PASSED)
