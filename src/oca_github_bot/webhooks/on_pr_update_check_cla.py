# Copyright (c) Camptocamp 2018

from ..router import router
from ..tasks.check_cla import check_cla


@router.register("pull_request")
async def on_pr_check_cla(event, gh, *args, **kwargs):
    check_cla.delay(event, gh)
