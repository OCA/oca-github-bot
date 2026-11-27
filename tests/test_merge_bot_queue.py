# Copyright (c) KMEE INFORMATICA LTDA 2026
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import contextlib
import subprocess
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from oca_github_bot import config
from oca_github_bot.process import CalledProcessError
from oca_github_bot.tasks import merge_bot
from oca_github_bot.tasks.merge_bot import (
    LABEL_MERGING,
    LABEL_QUEUED,
    MERGE_QUEUE_MARKER,
)

BOT = "OCA-git-bot"


def _label(name):
    return SimpleNamespace(name=name)


def _issue(number, state="open", labels=(), base_ref="16.0", comments=()):
    gh_issue = mock.MagicMock()
    gh_issue.number = number
    gh_issue.state = state
    gh_issue.labels.return_value = [_label(name) for name in labels]
    gh_issue.comments.return_value = list(comments)
    gh_issue.pull_request.return_value = SimpleNamespace(
        base=SimpleNamespace(ref=base_ref)
    )
    return gh_issue


def _comment(login, body, created_at):
    return SimpleNamespace(
        user=SimpleNamespace(login=login), body=body, created_at=created_at
    )


def _marker(username, bumpversion_mode):
    return MERGE_QUEUE_MARKER.format(
        username=username, bumpversion_mode=bumpversion_mode
    )


def _gh(issues, commit_dates=None):
    """A fake github3 session, with issues by number and commit dates by sha."""
    gh = mock.MagicMock()
    gh.issue.side_effect = lambda org, repo, number: issues[number]
    gh_repo = gh.repository.return_value
    gh_repo.issues.return_value = list(issues.values())
    gh_repo.commit.side_effect = lambda sha: SimpleNamespace(
        commit=SimpleNamespace(
            committer={"date": (commit_dates or {})[sha].isoformat()}
        )
    )
    return gh


def _git(cwd, *args):
    subprocess.check_call(["git", *args], cwd=cwd)


def test_git_merge_bot_branches(git_clone):
    remote = git_clone.parent / "remote"
    for branch in (
        "master-ocabot-merge-pr-12-by-someone-bump-patch",
        "master-ocabot-merge-pr-13-by-other-bump-nobump",
        "16.0-ocabot-merge-pr-14-by-someone-bump-patch",
        "master-feature",
    ):
        _git(git_clone, "push", "-q", "origin", f"master:refs/heads/{branch}")
    branches = merge_bot._git_merge_bot_branches(str(remote), "master")
    assert sorted((pr, branch) for pr, branch, _ in branches) == [
        (12, "master-ocabot-merge-pr-12-by-someone-bump-patch"),
        (13, "master-ocabot-merge-pr-13-by-other-bump-nobump"),
    ]


def test_active_pr(mocker):
    now = datetime.now(tz=UTC)
    mocker.patch.object(
        merge_bot,
        "_git_merge_bot_branches",
        return_value=[
            (1, "16.0-ocabot-merge-pr-1-by-a-bump-patch", "sha1"),
            (2, "16.0-ocabot-merge-pr-2-by-a-bump-patch", "sha2"),
            (3, "16.0-ocabot-merge-pr-3-by-a-bump-patch", "sha3"),
            (4, "16.0-ocabot-merge-pr-4-by-a-bump-patch", "sha4"),
        ],
    )
    gh = _gh(
        {
            # merged or closed: a leftover branch
            1: _issue(1, state="closed", labels=[LABEL_MERGING]),
            # failed merge: the bot removed the label but not the branch
            2: _issue(2),
            # stuck merge
            3: _issue(3, labels=[LABEL_MERGING]),
            # merge in progress
            4: _issue(4, labels=[LABEL_MERGING]),
        },
        commit_dates={"sha3": now - timedelta(hours=13), "sha4": now},
    )
    assert merge_bot._merge_bot_active_pr(gh, "OCA", "repo", "16.0") == 4
    # a PR never waits for itself
    assert merge_bot._merge_bot_active_pr(gh, "OCA", "repo", "16.0", "4") is None


def test_active_pr_queue_disabled(mocker, monkeypatch):
    monkeypatch.setattr(config, "BOT_TASKS_DISABLED", ["merge_bot_queue"])
    git_merge_bot_branches = mocker.patch.object(merge_bot, "_git_merge_bot_branches")
    assert merge_bot._merge_bot_active_pr(mock.MagicMock(), "OCA", "r", "16.0") is None
    git_merge_bot_branches.assert_not_called()


def test_queue(monkeypatch):
    monkeypatch.setattr(config, "GITHUB_LOGIN", BOT)
    t0 = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    gh = _gh(
        {
            10: _issue(
                10,
                comments=[
                    _comment(BOT, _marker("alice", "patch"), t0 + timedelta(hours=2)),
                    # a command issued again: the last one wins
                    _comment(BOT, _marker("alice", "minor"), t0 + timedelta(hours=3)),
                ],
            ),
            11: _issue(11, comments=[_comment(BOT, _marker("bob", "nobump"), t0)]),
            # queued on another target branch
            12: _issue(
                12, base_ref="18.0", comments=[_comment(BOT, _marker("bob", "x"), t0)]
            ),
            # nobody but the bot can queue a merge
            13: _issue(
                13, comments=[_comment("mallory", _marker("alice", "major"), t0)]
            ),
        }
    )
    queue = merge_bot._merge_bot_queue(gh, "OCA", "repo", "16.0")
    assert [item[1:] for item in queue] == [
        (11, "bob", "nobump"),
        (10, "alice", "minor"),
    ]
    gh.repository.return_value.issues.assert_called_once_with(
        state="open", labels=LABEL_QUEUED
    )


def _patch_login(mocker, gh):
    mocker.patch.object(
        merge_bot.github, "login", return_value=contextlib.nullcontext(gh)
    )


def test_start_queues_when_busy(mocker):
    gh = mock.MagicMock()
    gh_pr = gh.pull_request.return_value
    gh_pr.base.ref = "16.0"
    gh_issue = gh_pr.issue.return_value
    gh_issue.labels.return_value = [_label(LABEL_MERGING)]
    _patch_login(mocker, gh)
    mocker.patch.object(merge_bot, "_merge_bot_active_pr", return_value=7)
    temporary_clone = mocker.patch.object(merge_bot.github, "temporary_clone")
    merge_bot.merge_bot_start("OCA", "repo", 8, "alice", "patch")
    temporary_clone.assert_not_called()
    body = gh_pr.create_comment.call_args.args[0]
    assert "#7 is being merged on `16.0`" in body
    assert _marker("alice", "patch") in body
    gh_issue.add_labels.assert_called_once_with(LABEL_QUEUED)
    # a queued PR does not hold the queue
    gh_issue.remove_label.assert_called_once_with(LABEL_MERGING)


def test_start_releases_queue_when_not_allowed(mocker):
    gh = mock.MagicMock()
    gh.pull_request.return_value.base.ref = "16.0"
    _patch_login(mocker, gh)
    mocker.patch.object(merge_bot, "_merge_bot_active_pr", return_value=None)
    mocker.patch.object(
        merge_bot.github, "temporary_clone", return_value=contextlib.nullcontext(".")
    )
    mocker.patch.object(merge_bot, "check_call")
    mocker.patch.object(merge_bot, "user_can_push", return_value=False)
    dequeue = mocker.patch.object(merge_bot.merge_bot_dequeue, "delay")
    merge_bot.merge_bot_start("OCA", "repo", 8, "alice", "patch")
    dequeue.assert_called_once_with("OCA", "repo", "16.0")


def test_dequeue_waits_for_merge_in_progress(mocker):
    _patch_login(mocker, mock.MagicMock())
    mocker.patch.object(merge_bot, "_merge_bot_active_pr", return_value=7)
    queue = mocker.patch.object(merge_bot, "_merge_bot_queue")
    start = mocker.patch.object(merge_bot, "merge_bot_start")
    merge_bot.merge_bot_dequeue("OCA", "repo", "16.0")
    queue.assert_not_called()
    start.assert_not_called()


def test_dequeue_starts_oldest(mocker):
    t0 = datetime(2026, 11, 27, tzinfo=UTC)
    _patch_login(mocker, mock.MagicMock())
    mocker.patch.object(merge_bot, "_merge_bot_active_pr", return_value=None)
    mocker.patch.object(
        merge_bot,
        "_merge_bot_queue",
        return_value=[(t0, 11, "bob", "nobump"), (t0, 12, "alice", "patch")],
    )
    start = mocker.patch.object(merge_bot, "merge_bot_start")
    merge_bot.merge_bot_dequeue("OCA", "repo", "16.0")
    start.assert_called_once_with("OCA", "repo", 11, "bob", "nobump", dry_run=False)


def test_is_push_race():
    def error(output):
        return CalledProcessError(1, ["git", "push"], output=output)

    assert merge_bot._is_push_race(
        error(" ! [rejected]  16.0-ocabot-merge-pr-1 -> 16.0 (fetch first)")
    )
    assert merge_bot._is_push_race(
        error(" ! [remote rejected] x -> 16.0 (cannot lock ref 'refs/heads/16.0')")
    )
    assert not merge_bot._is_push_race(
        error(" ! [remote rejected] x -> 16.0 (missing necessary objects)")
    )


def test_merge_retries_when_push_is_rejected(git_clone, mocker):
    """Someone pushes to the target branch after the merge bot checked it."""
    remote = git_clone.parent / "remote"
    branch = "master-ocabot-merge-pr-1-by-alice-bump-nobump"
    # the PR, and the merge bot branch prepared from it
    _git(git_clone, "checkout", "-q", "-b", "pr")
    (git_clone / "prfile").write_text("pr")
    _git(git_clone, "add", "prfile")
    _git(git_clone, "commit", "-q", "-m", "the PR")
    _git(git_clone, "push", "-q", "origin", "pr:refs/pull/1/head")
    _git(git_clone, "checkout", "-q", "-b", branch, "master")
    _git(git_clone, "merge", "-q", "--no-ff", "-m", "Merge PR #1", "pr")
    # another merge lands on master meanwhile
    other = git_clone.parent / "other"
    _git(git_clone.parent, "clone", "-q", str(remote), "other")
    _git(
        other,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "another PR",
    )
    _git(other, "push", "-q", "origin", "master")
    retry = mocker.patch.object(merge_bot, "_merge_bot_retry")
    assert not merge_bot._merge_bot_merge_pr("OCA", "repo", branch, str(git_clone))
    retry.assert_called_once_with("OCA", "repo", branch, dry_run=False)
