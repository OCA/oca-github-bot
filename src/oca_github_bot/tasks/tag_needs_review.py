# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..config import switchable
from ..github import gh_call, repository
from ..queue import getLogger, task

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
            if dry_run:
                _logger.info(f"DRY-RUN add {LABEL_NEEDS_REVIEW} label")
            else:
                gh_call(gh_issue.add_labels, LABEL_NEEDS_REVIEW)
