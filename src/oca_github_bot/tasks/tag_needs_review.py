# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..config import REVIEW_GATE_AS_FIRST_FILTER, switchable
from ..github import gh_call, repository
from ..queue import getLogger, task
from ..review_gate import LABEL_BOT_CHECKS_PASSED
from .mention_maintainer import mention_maintainer

_logger = getLogger(__name__)

LABEL_NEEDS_REVIEW = "needs review"
LABEL_WIP = "work in progress"


@task()
@switchable()
def tag_needs_review(org, pr, repo, status, dry_run=False):
    """On a successful execution of the CI tests, adds the `needs review`
    label to the pull request if it doesn't have `wip:` at the
    begining of the title (case insensitive). Removes the tag if the CI
    fails.
    """
    with repository(org, repo) as gh_repo:
        gh_pr = gh_call(gh_repo.pull_request, pr)
        gh_issue = gh_call(gh_pr.issue)
        labels = [label.name for label in gh_issue.labels()]
        has_wip = (
            gh_pr.title.lower().startswith(("wip:", "[wip]")) or LABEL_WIP in labels
        )
        if status == "success" and not has_wip:
            if REVIEW_GATE_AS_FIRST_FILTER and LABEL_BOT_CHECKS_PASSED not in labels:
                _logger.info(
                    "skip %s: mechanical checks have not passed yet", LABEL_NEEDS_REVIEW
                )
                return
            already = LABEL_NEEDS_REVIEW in labels
            if dry_run:
                _logger.info(f"DRY-RUN add {LABEL_NEEDS_REVIEW} label")
            elif not already:
                gh_call(gh_issue.add_labels, LABEL_NEEDS_REVIEW)
            if REVIEW_GATE_AS_FIRST_FILTER and not already:
                mention_maintainer.delay(org, repo, pr)
