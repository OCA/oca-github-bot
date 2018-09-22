# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from ..router import router

_logger = logging.getLogger(__name__)


@router.register("pull_request", action="closed")
async def on_pr_open_label_new_contributor(event, gh, *args, **kwargs):
    """
    Whenever a PR is opened, set label "new contributor"
    if the author has less than 4 commits in OCA repositories.
    """
    # TODO
    pass
