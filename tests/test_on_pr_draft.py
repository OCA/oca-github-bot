# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.webhooks import on_pr_draft

from .common import EventMock


@pytest.mark.asyncio
async def test_on_pr_draft(mocker):
    mocker.patch("oca_github_bot.webhooks.on_pr_draft.tag_approved.delay")
    event = EventMock(
        data={
            "repository": {"full_name": "OCA/some-repo"},
            "pull_request": {"number": 1, "draft": True},
        }
    )
    await on_pr_draft.on_pr_draft(event, None)
    on_pr_draft.tag_approved.delay.assert_called_once_with("OCA", "some-repo", 1)
