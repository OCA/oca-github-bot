# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..commands import parse_commands
from ..router import router


@router.register("pull_request_review_comment")
async def on_pr_review_comment(event, gh, *args, **kwargs):
    """On pull request review, tag if approved or ready to merge."""
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["pull_request"]["number"]
    target_branch = event.data["pull_request"]["base"]["ref"]
    user = event.data["comment"]["user"]
    text = event.data["comment"]["body"]

    for command in parse_commands(text):
        command.run.delay(org, repo, pr, target_branch, user)
