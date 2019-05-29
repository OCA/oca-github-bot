# Copyright (c) initOS GmbH 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest
from oca_github_bot.version_branch import make_merge_bot_branch
from oca_github_bot.webhooks import on_check_suite

from .common import EventMock


def create_test_data(branch, status, conclusion, sha=None):
    return {
        "repository": {"full_name": "OCA/some-repo"},
        "check_suite": {
            "head_branch": branch,
            "head_sha": sha if sha else "0" * 40,
            "status": status,
            "conclusion": conclusion,
        },
    }


def mock_merge_bot_functions(mocker):
    mocker.patch(
        "oca_github_bot.webhooks.on_check_suite.merge_bot_status_success.delay"
    )
    mocker.patch(
        "oca_github_bot.webhooks.on_check_suite.merge_bot_status_failure.delay"
    )


@pytest.mark.asyncio
async def test_on_check_suite_invalid_branch(mocker):
    mock_merge_bot_functions(mocker)

    # Completed
    data = create_test_data("changes", "completed", "success")
    event = EventMock(data)
    await on_check_suite.on_check_suite(event, None)
    on_check_suite.merge_bot_status_success.delay.assert_not_called()
    on_check_suite.merge_bot_status_failure.delay.assert_not_called()

    # Running
    data = create_test_data("changes", "in_progress", None)
    event = EventMock(data)
    await on_check_suite.on_check_suite(event, None)
    on_check_suite.merge_bot_status_success.delay.assert_not_called()
    on_check_suite.merge_bot_status_failure.delay.assert_not_called()


@pytest.mark.asyncio
async def test_on_check_suite_valid_branch_success(mocker):
    mock_merge_bot_functions(mocker)

    branch = make_merge_bot_branch(42, "12.0")
    sha = "1" * 40
    # Completed
    data = create_test_data(branch, "completed", "success", sha)
    event = EventMock(data)
    await on_check_suite.on_check_suite(event, None)
    on_check_suite.merge_bot_status_success.delay.assert_called_once_with(
        "OCA", "some-repo", branch, sha
    )
    on_check_suite.merge_bot_status_failure.delay.assert_not_called()


@pytest.mark.asyncio
async def test_on_check_suite_valid_branch_failure(mocker):
    mock_merge_bot_functions(mocker)

    branch = make_merge_bot_branch(42, "12.0")
    sha = "1" * 40
    data = create_test_data(branch, "completed", "failure", sha)
    event = EventMock(data)
    await on_check_suite.on_check_suite(event, None)
    on_check_suite.merge_bot_status_success.delay.assert_not_called()
    on_check_suite.merge_bot_status_failure.delay.assert_called_once_with(
        "OCA", "some-repo", branch, sha
    )


@pytest.mark.asyncio
async def test_on_check_suite_valid_branch_in_progress(mocker):
    mock_merge_bot_functions(mocker)

    branch = make_merge_bot_branch(42, "12.0")
    sha = "1" * 40
    data = create_test_data(branch, "in_progress", "success", sha)
    event = EventMock(data)
    await on_check_suite.on_check_suite(event, None)
    on_check_suite.merge_bot_status_success.delay.assert_not_called()
    on_check_suite.merge_bot_status_failure.delay.assert_not_called()
