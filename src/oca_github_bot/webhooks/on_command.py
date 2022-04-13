# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..commands import CommandError, parse_commands
from ..config import OCABOT_EXTRA_DOCUMENTATION, OCABOT_USAGE
from ..router import router
from ..tasks.add_pr_comment import add_pr_comment


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
    await _on_command(org, repo, pr, username, text)


async def _on_command(org, repo, pr, username, text):
    try:
        for command in parse_commands(text):
            command.delay(org, repo, pr, username)
    except CommandError as e:
        # Add a comment on the current PR, if
        # the command was misunderstood by the bot
        add_pr_comment.delay(
            org,
            repo,
            pr,
            f"Hi @{username}. Your command failed:\n\n"
            f"``{e}``.\n\n"
            f"{OCABOT_USAGE}\n\n"
            f"{OCABOT_EXTRA_DOCUMENTATION}",
        )
