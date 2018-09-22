# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.tag_ready_to_merge import tag_ready_to_merge


@router.register("pull_request_review")
async def on_pr_review(event, gh, *args, **kwargs):
    """On pull request review, tag if approved or ready to merge."""
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    tag_ready_to_merge.delay(org, repo, pr)
