# Copyright (c) Camptocamp 2018

import logging
from ..router import router

_logger = logging.getLogger(__name__)


@router.register("pull_request")
async def on_pr_check_cla(event, gh, *args, **kwargs):
    
