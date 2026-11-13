# Copyright 2026 Maxime Chambreuil - Gray Matter Logic
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.webhooks import on_pr_review_gate

from .common import EventMock


@pytest.mark.asyncio
async def test_on_pr_review_gate(mocker):
    mocker.patch("oca_github_bot.webhooks.on_pr_review_gate.review_gate.delay")
    event = EventMock(
        data={
            "repository": {"full_name": "OCA/some-repo"},
            "pull_request": {"number": 12},
        }
    )
    await on_pr_review_gate.on_pr_review_gate(event)
    on_pr_review_gate.review_gate.delay.assert_called_once_with("OCA", "some-repo", 12)
