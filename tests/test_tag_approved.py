# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from unittest.mock import MagicMock

import pytest

from oca_github_bot.tasks import tag_approved as tag_approved_module
from oca_github_bot.tasks.tag_approved import LABEL_APPROVED, tag_approved
from oca_github_bot.tasks.tag_ready_to_merge import LABEL_READY_TO_MERGE


def _review(login, state):
    review = MagicMock()
    review.state = state
    review.user.login = login
    return review


def _label(name):
    label = MagicMock()
    label.name = name
    return label


@pytest.fixture
def gh_pr(mocker):
    """Mock the GitHub API so that ``tag_approved`` works on a fake PR."""
    github_mock = mocker.patch("oca_github_bot.tasks.tag_approved.github")
    gh_repo = github_mock.repository.return_value.__enter__.return_value
    pr = MagicMock()
    pr.url = "https://github.com/OCA/some-repo/pull/1"
    pr.mergeable = True
    pr.draft = False
    gh_repo.pull_request.return_value = pr
    # gh_call just calls the function
    mocker.patch(
        "oca_github_bot.tasks.tag_approved.gh_call",
        side_effect=lambda func, *args, **kwargs: func(*args, **kwargs),
    )
    mocker.patch("oca_github_bot.tasks.tag_approved.tag_ready_to_merge.delay")
    mocker.patch("oca_github_bot.tasks.tag_approved.APPROVALS_REQUIRED", 2)
    return pr


def _set_labels(gh_pr, *names):
    gh_pr.issue.return_value.labels.return_value = [_label(name) for name in names]


def test_tag_approved_adds_label(gh_pr):
    gh_pr.reviews.return_value = [
        _review("reviewer1", "APPROVED"),
        _review("reviewer2", "APPROVED"),
    ]
    _set_labels(gh_pr)
    tag_approved("OCA", "some-repo", 1)
    gh_pr.issue.return_value.add_labels.assert_called_once_with(LABEL_APPROVED)
    gh_pr.issue.return_value.remove_label.assert_not_called()
    tag_approved_module.tag_ready_to_merge.delay.assert_called_once_with("OCA")


def test_tag_approved_removes_label_on_changes_requested(gh_pr):
    gh_pr.reviews.return_value = [
        _review("reviewer1", "APPROVED"),
        _review("reviewer2", "CHANGES_REQUESTED"),
    ]
    _set_labels(gh_pr, LABEL_APPROVED, LABEL_READY_TO_MERGE)
    tag_approved("OCA", "some-repo", 1)
    gh_pr.issue.return_value.add_labels.assert_not_called()
    assert gh_pr.issue.return_value.remove_label.call_args_list == [
        ((LABEL_APPROVED,),),
        ((LABEL_READY_TO_MERGE,),),
    ]
    tag_approved_module.tag_ready_to_merge.delay.assert_not_called()


def test_tag_approved_draft_pr_not_approved(gh_pr):
    """A draft PR must not be approved, even with enough approvals."""
    gh_pr.draft = True
    gh_pr.reviews.return_value = [
        _review("reviewer1", "APPROVED"),
        _review("reviewer2", "APPROVED"),
    ]
    _set_labels(gh_pr)
    tag_approved("OCA", "some-repo", 1)
    gh_pr.issue.return_value.add_labels.assert_not_called()
    tag_approved_module.tag_ready_to_merge.delay.assert_not_called()


def test_tag_approved_draft_pr_removes_labels(gh_pr):
    """Converting an approved PR to draft removes the approved labels."""
    gh_pr.draft = True
    gh_pr.reviews.return_value = [
        _review("reviewer1", "APPROVED"),
        _review("reviewer2", "APPROVED"),
    ]
    _set_labels(gh_pr, LABEL_APPROVED, LABEL_READY_TO_MERGE)
    tag_approved("OCA", "some-repo", 1)
    gh_pr.issue.return_value.add_labels.assert_not_called()
    assert gh_pr.issue.return_value.remove_label.call_args_list == [
        ((LABEL_APPROVED,),),
        ((LABEL_READY_TO_MERGE,),),
    ]
    tag_approved_module.tag_ready_to_merge.delay.assert_not_called()
