# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from ..router import router
from ..tasks.main_branch_bot import main_branch_bot

_logger = logging.getLogger(__name__)


@router.register("push", ref="refs/heads/8.0")
@router.register("push", ref="refs/heads/9.0")
@router.register("push", ref="refs/heads/10.0")
@router.register("push", ref="refs/heads/11.0")
async def on_push_to_main_branch(event, gh, *args, **kwargs):
    """
    On push to main branches, run the main branch bot task.
    """
    org, repo = event.data["repository"]["full_name"].split("/")
    branch = event.data["ref"].split("/")[-1]
    main_branch_bot.delay(org, repo, branch)
