#  Copyright 2022 Simone Rubino - TAKOBI
#  Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from ..router import router
from ..tasks.migration_pr_check import comment_migration_guidelines, is_migration_pr

_logger = logging.getLogger(__name__)


@router.register("pull_request", action="opened")
async def on_pr_open_migration_check(event, *args, **kwargs):
    """
    Whenever a PR is opened, if it is a migration PR,
    remind the migration guidelines.
    """
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    if is_migration_pr(org, repo, pr):
        comment_migration_guidelines.delay(org, repo, pr)
