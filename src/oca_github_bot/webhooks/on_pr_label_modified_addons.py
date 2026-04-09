# Copyright (c) ACSONE SA/NV 2024
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging

from ..router import router
from ..tasks.label_modified_addons import label_modified_addons

_logger = logging.getLogger(__name__)


@router.register("pull_request", action="opened")
@router.register("pull_request", action="reopened")
@router.register("pull_request", action="synchronize")
async def on_pr_label_modified_addons(event, *args, **kwargs):
    """
    Whenever a PR is opened, add labels based on modified addons.
    """
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    label_modified_addons.delay(org, repo, pr)
