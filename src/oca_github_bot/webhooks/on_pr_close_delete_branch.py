# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from tools.oca_projects import MAIN_BRANCHES

from ..router import router
from ..tasks.delete_branch import delete_branch

_logger = logging.getLogger(__name__)


@router.register("pull_request", action="closed")
async def on_pr_close_delete_branch(event, gh, *args, **kwargs):
    """
    Whenever a PR is closed, delete the branch
    Only delete the branch if it's not from a forked repo

    This is mostly for demonstration purposes.
    """
    forked = event.data["pull_request"]["head"]["repo"]["fork"]
    merged = event.data["pull_request"]["merged"]
    branch = event.data["pull_request"]["head"]["ref"]
    org, repo = event.data["repository"]["full_name"].split("/")

    if not forked and merged and branch not in MAIN_BRANCHES and branch != "master":
        delete_branch.delay(org, repo, branch)
