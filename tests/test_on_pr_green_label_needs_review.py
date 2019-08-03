# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.webhooks import on_pr_green_label_needs_review

from .common import EventMock


@pytest.mark.asyncio
async def test_on_pr_green_label_needs_review(mocker):
    mocker.patch(
        "oca_github_bot.webhooks.on_pr_green_label_needs_review.tag_needs_review.delay"
    )
    event = EventMock(
        data={
            "repository": {"full_name": "OCA/some-repo"},
            "check_suite": {"pull_requests": [{"number": 1}], "conclusion": "success"},
        }
    )
    await on_pr_green_label_needs_review.on_pr_green_label_needs_review(event, None)
    on_pr_green_label_needs_review.tag_needs_review.delay.assert_called_once_with(
        "OCA", 1, "some-repo", "success"
    )
