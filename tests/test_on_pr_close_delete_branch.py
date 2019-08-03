# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.webhooks import on_pr_close_delete_branch

from .common import EventMock


@pytest.mark.asyncio
async def test_on_pr_close_delete_branch(mocker):
    mocker.patch(
        "oca_github_bot.webhooks.on_pr_close_delete_branch.delete_branch.delay"
    )
    event = EventMock(
        data={
            "repository": {"full_name": "OCA/some-repo"},
            "pull_request": {
                "head": {"repo": {"fork": False}, "ref": "pr-branch"},
                "merged": True,
            },
        }
    )
    await on_pr_close_delete_branch.on_pr_close_delete_branch(event, None)
    on_pr_close_delete_branch.delete_branch.delay.assert_called_once_with(
        "OCA", "some-repo", "pr-branch"
    )
