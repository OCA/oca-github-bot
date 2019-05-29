# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..router import router
from ..tasks.merge_bot import merge_bot_status
from ..version_branch import is_merge_bot_branch


@router.register("check_suite", action="completed")
async def on_check_suite(event, gh, *args, **kwargs):
    org, repo = event.data["repository"]["full_name"].split("/")
    branch = event.data["check_suite"]["head_branch"]
    sha = event.data["check_suite"]["head_sha"]
    status = event.data["check_suite"]["status"]

    if is_merge_bot_branch(branch) and status == "completed":
        merge_bot_status.delay(org, repo, branch, sha)
