# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.version_branch import make_merge_bot_branch
from oca_github_bot.webhooks import on_status_merge_bot

from .common import EventMock


def create_test_data(branch, status, conclusion, sha=None):
    return {
        "repository": {"full_name": "OCA/some-repo"},
        "check_suite": {
            "head_branch": branch,
            "head_sha": sha if sha else "0" * 40,
            "status": status,
            "conclusion": conclusion,
            "app": {"name": "Travis CI"},
        },
    }


def mock_merge_bot_functions(mocker):
    mocker.patch("oca_github_bot.webhooks.on_status_merge_bot.merge_bot_status.delay")


@pytest.mark.asyncio
async def test_on_check_suite_invalid_branch(mocker):
    mock_merge_bot_functions(mocker)

    # Completed
    data = create_test_data("changes", "completed", "success")
    event = EventMock(data)
    await on_status_merge_bot.on_check_suite_merge_bot(event, None)
    on_status_merge_bot.merge_bot_status.delay.assert_not_called()

    # Running
    data = create_test_data("changes", "in_progress", None)
    event = EventMock(data)
    await on_status_merge_bot.on_check_suite_merge_bot(event, None)
    on_status_merge_bot.merge_bot_status.delay.assert_not_called()


@pytest.mark.asyncio
async def test_on_check_suite_valid_branch(mocker):
    mock_merge_bot_functions(mocker)

    branch = make_merge_bot_branch(42, "12.0", "toto", "patch")
    sha = "1" * 40
    data = create_test_data(branch, "completed", "failure", sha)
    event = EventMock(data)
    await on_status_merge_bot.on_check_suite_merge_bot(event, None)
    on_status_merge_bot.merge_bot_status.delay.assert_called_once_with(
        "OCA", "some-repo", branch, sha
    )


@pytest.mark.asyncio
async def test_on_check_suite_valid_branch_in_progress(mocker):
    mock_merge_bot_functions(mocker)

    branch = make_merge_bot_branch(42, "12.0", "toto", "patch")
    sha = "1" * 40
    data = create_test_data(branch, "in_progress", "success", sha)
    event = EventMock(data)
    await on_status_merge_bot.on_check_suite_merge_bot(event, None)
    on_status_merge_bot.merge_bot_status.delay.assert_not_called()
