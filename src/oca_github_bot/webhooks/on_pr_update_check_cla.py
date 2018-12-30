# Copyright (c) Camptocamp 2018

from ..router import router
from ..tasks.check_cla import check_cla


@router.register("pull_request")
async def on_pr_check_cla(event, gh, *args, **kwargs):
    """
    On Pull Request update, check the CLA
    """
    owner = event.data["repository"]["owner"]["login"]
    repo = event.data["repository"]["name"]
    pull_user = event.data["pull_request"]["user"]["login"]
    number = event.data["number"]
    action = event.data["action"]

    check_cla.delay(owner, repo, pull_user, number, action)
