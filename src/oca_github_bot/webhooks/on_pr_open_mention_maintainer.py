# Copyright 2019 Simone Rubino - Agile Business Group
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from ..config import REVIEW_GATE_AS_FIRST_FILTER
from ..router import router
from ..tasks.mention_maintainer import mention_maintainer

_logger = logging.getLogger(__name__)


@router.register("pull_request", action="opened")
@router.register("pull_request", action="reopened")
async def on_pr_open_mention_maintainer(event, *args, **kwargs):
    """
    Whenever a PR is opened, mention the maintainers of modified addons.
    """
    if REVIEW_GATE_AS_FIRST_FILTER:
        # Mentions wait until mechanical checks + CI are green.
        return
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    mention_maintainer.delay(org, repo, pr)
