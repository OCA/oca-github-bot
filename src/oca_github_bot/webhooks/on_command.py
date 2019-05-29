# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..commands import parse_commands
from ..router import router


@router.register("issue_comment", action="created")
async def on_command(event, gh, *args, **kwargs):
    """On pull request review, tag if approved or ready to merge."""
    if not event.data["issue"].get("pull_request"):
        # ignore issue comments
        return
    org, repo = event.data["repository"]["full_name"].split("/")
    pr = event.data["issue"]["number"]
    username = event.data["comment"]["user"]["login"]
    text = event.data["comment"]["body"]

    for command in parse_commands(text):
        command.delay(org, repo, pr, username)
