# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.tag_approved import tag_approved
from .on_command import _on_command


@router.register("pull_request_review")
async def on_pr_review(event, gh, *args, **kwargs):
    """On pull request review, tag if approved or ready to merge."""
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    username = event.data["review"]["user"]["login"]
    text = event.data["review"]["body"]
    tag_approved.delay(org, repo, pr)
    await _on_command(org, repo, pr, username, text)
