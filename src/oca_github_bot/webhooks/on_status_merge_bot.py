# Copyright (c) initOS GmbH 2019
# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..config import GITHUB_CHECK_SUITES_IGNORED, GITHUB_STATUS_IGNORED
from ..router import router
from ..tasks.merge_bot import merge_bot_status
from ..version_branch import is_merge_bot_branch, search_merge_bot_branch


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


@router.register("check_run")
async def on_check_run_merge_bot(event, gh, *args, **kwargs):
    # This one is a hack to work around a strange behaviour of GitHub/Travis.
    # Normally, we get a check_suite call when all checks are done.
    # But when the merge bot branch is created on a commit that is
    # already in the PR (i.e. when the rebase of the PR was a fast forward),
    # we only get a check_run call, and no check_suite. Moreover we have
    # no clean reference to the head branch in payload, so we attempt to
    # extract it from the some text present in the payload.
    org, repo = event.data["repository"]["full_name"].split("/")
    branch_name = event.data["check_run"]["check_suite"]["head_branch"]
    sha = event.data["check_run"]["check_suite"]["head_sha"]
    status = event.data["check_run"]["status"]
    app = event.data["check_run"]["check_suite"]["app"]["name"]
    output = event.data["check_run"]["output"]["text"]

    if app in GITHUB_CHECK_SUITES_IGNORED:
        return
    if status != "completed":
        return
    if is_merge_bot_branch(branch_name):
        # we should get the corresponding check suite call later
        # so we do nothing with this check_run call
        return
    if not output:
        return
    branch_name = search_merge_bot_branch(output)
    if not branch_name:
        # this check_run is not for a merge bot branch
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
