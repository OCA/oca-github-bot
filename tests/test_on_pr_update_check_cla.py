# Copyright (c) Alexandre Fayolle 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest
from oca_github_bot.webhooks import on_pr_update_check_cla

from .common import EventMock


@pytest.mark.asyncio
async def test_on_update_pr_check_cla(mocker):
    mocker.patch("oca_github_bot.webhooks.on_pr_update_check_cla.check_cla.delay")
    event = EventMock(
        {
            "repository": {
                "full_name": "OCA/some-repo",
                "name": "some-repo",
                "owner": {"login": "mylogin"},
            },
            "pull_request": {"user": {"login": "pr_user_login"}},
            "number": 42,
            "action": "synchronize",
        }
    )
    await on_pr_update_check_cla.on_pr_check_cla(event, None)
    on_pr_update_check_cla.check_cla.delay.assert_called_once_with(
        "mylogin", "some-repo", "pr_user_login", 42, "synchronize"
    )
