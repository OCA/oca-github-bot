# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import pytest

from oca_github_bot.manifest import user_can_push

from .common import commit_addon, make_addon


@pytest.mark.vcr()
def test_user_can_merge_team_member(git_clone, gh):
    assert user_can_push(gh, "OCA", "mis-builder", "sbidoul", git_clone, "master")


@pytest.mark.vcr()
def test_user_can_merge_maintainer(git_clone, gh):
    make_addon(git_clone, "addon1", maintainers=["themaintainer"])
    commit_addon(git_clone, "addon1")
    subprocess.check_call(["git", "checkout", "-b", "thebranch"], cwd=git_clone)
    (git_clone / "addon1" / "data").write_text("")
    commit_addon(git_clone, "addon1")
    assert user_can_push(gh, "OCA", "mis-builder", "themaintainer", git_clone, "master")


@pytest.mark.vcr()
def test_user_can_merge_not_maintainer(git_clone, gh):
    make_addon(git_clone, "addon1")
    commit_addon(git_clone, "addon1")
    subprocess.check_call(["git", "checkout", "-b", "thebranch"], cwd=git_clone)
    (git_clone / "addon1" / "data").write_text("")
    commit_addon(git_clone, "addon1")
    assert not user_can_push(
        gh, "OCA", "mis-builder", "themaintainer", git_clone, "master"
    )


@pytest.mark.vcr()
def test_user_can_merge_not_maintainer_hacker(git_clone, gh):
    make_addon(git_clone, "addon1")
    commit_addon(git_clone, "addon1")
    subprocess.check_call(["git", "checkout", "-b", "thebranch"], cwd=git_clone)
    # themaintainer attempts to add himself as maintainer
    (git_clone / "addon1" / "__manifest__.py").write_text(
        "{'name': 'addon1', 'maintainers': ['themaintainer']}"
    )
    commit_addon(git_clone, "addon1")
    assert not user_can_push(
        gh, "OCA", "mis-builder", "themaintainer", git_clone, "master"
    )
