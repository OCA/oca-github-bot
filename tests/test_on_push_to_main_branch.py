# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.webhooks import on_push_to_main_branch

from .common import EventMock


@pytest.mark.asyncio
async def test_on_push_to_main_branch_1(mocker):
    mocker.patch("oca_github_bot.webhooks.on_push_to_main_branch.main_branch_bot.delay")
    event = EventMock(
        {"repository": {"full_name": "OCA/some-repo"}, "ref": "refs/heads/11.0"}
    )
    await on_push_to_main_branch.on_push_to_main_branch(event, None)
    on_push_to_main_branch.main_branch_bot.delay.assert_called_once_with(
        "OCA", "some-repo", "11.0", build_wheels=False
    )
