# Copyright (c) initOS GmbH 2019
# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..config import GITHUB_CHECK_SUITES_IGNORED, GITHUB_STATUS_IGNORED
from ..router import router
from ..tasks.merge_bot import merge_bot_status
from ..version_branch import is_merge_bot_branch


@router.register("check_suite")
async def on_check_suite_merge_bot(event, gh, *args, **kwargs):
    org, repo = event.data["repository"]["full_name"].split("/")
    branch_name = event.data["check_suite"]["head_branch"]
    sha = event.data["check_suite"]["head_sha"]
    status = event.data["check_suite"]["status"]
    app = event.data["check_suite"]["app"]["name"]

    if app in GITHUB_CHECK_SUITES_IGNORED:
        return
    if status != "completed":
        return
    if not is_merge_bot_branch(branch_name):
        return

    merge_bot_status.delay(org, repo, branch_name, sha)


@router.register("status")
async def on_status_merge_bot(event, gh, *args, **kwargs):
    org, repo = event.data["repository"]["full_name"].split("/")
    sha = event.data["sha"]
    state = event.data["state"]
    branches = event.data.get("branches", [])
    context = event.data["context"]

    if context in GITHUB_STATUS_IGNORED:
        return
    if state == "pending":
        return
    for branch in branches:
        branch_name = branch["name"]
        if is_merge_bot_branch(branch_name):
            break
    else:
        return

    merge_bot_status.delay(org, repo, branch_name, sha)
