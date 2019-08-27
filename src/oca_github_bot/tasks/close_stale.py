# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from datetime import datetime

from dateutil.relativedelta import relativedelta

from .. import github
from ..config import switchable
from ..github import gh_call, gh_datetime
from ..queue import getLogger, task

_logger = getLogger(__name__)


INACTIVITY_PERIOD = relativedelta(years=1)
LABEL_STALE = "stale"
CLOSING_AS_STALE_COMMENT = (
    "This PR had no activity for a long time. 😴 "
    "It's therefore being closed as stale. 💔 "
    "Please, reopen if this PR is still relevant. 🤖"
)


@task()
@switchable()
def close_stale(org, repo=None, dry_run=False):
    """Close all stale PRs where conditions are met."""
    with github.login() as gh:
        query = [
            "type:pr",
            "state:open",
            f"updated:<{gh_datetime(datetime.utcnow() - INACTIVITY_PERIOD)}",
        ]
        if repo:
            query.append(f"repo:{org}/{repo}")
        else:
            query.append(f"org:{org}")
        for issue in gh.search_issues(" ".join(query)):
            if dry_run:
                _logger.info(f"DRY-RUN close PR {issue.html_url} as stale")
            else:
                _logger.info(f"close PR {issue.html_url} as stale")
                gh_issue = issue.issue
                gh_call(gh_issue.add_labels, LABEL_STALE)
                gh_pr = gh_issue.pull_request()
                gh_call(gh_pr.create_comment, CLOSING_AS_STALE_COMMENT)
                gh_call(gh_pr.close)
