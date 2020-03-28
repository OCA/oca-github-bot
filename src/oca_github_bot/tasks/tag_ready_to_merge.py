# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from datetime import datetime, timedelta

from .. import github
from ..config import MIN_PR_AGE, switchable
from ..github import gh_call, gh_datetime
from ..queue import getLogger, task

_logger = getLogger(__name__)


LABEL_READY_TO_MERGE = "ready to merge"
READY_TO_MERGE_COMMENT = (
    "This PR has the `approved` label and "
    "has been created more than 5 days ago. "
    "It should therefore be ready to merge by a maintainer "
    "(or a PSC member if the concerned addon has "
    "no declared maintainer). 🤖"
)


@task()
@switchable()
def tag_ready_to_merge(org, repo=None, dry_run=False):
    """Add the ``ready to merge`` tag to all PRs where conditions are met."""
    with github.login() as gh:
        max_created = datetime.utcnow() - timedelta(days=MIN_PR_AGE)
        query = [
            "type:pr",
            "state:open",
            "status:success",
            "label:approved",
            '-label:"ready to merge"',
            f"created:<{gh_datetime(max_created)}",
        ]
        if repo:
            query.append(f"repo:{org}/{repo}")
        else:
            query.append(f"org:{org}")
        for issue in gh.search_issues(" ".join(query)):
            if dry_run:
                _logger.info(
                    f"DRY-RUN add {LABEL_READY_TO_MERGE} "
                    f"label to PR {issue.html_url}"
                )
            else:
                _logger.info(f"add {LABEL_READY_TO_MERGE} label to PR {issue.html_url}")
                gh_issue = issue.issue
                gh_call(gh_issue.add_labels, LABEL_READY_TO_MERGE)
                gh_pr = gh_issue.pull_request()
                gh_call(gh_pr.create_comment, READY_TO_MERGE_COMMENT)
