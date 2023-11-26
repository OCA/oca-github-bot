# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import github3
import pytest

from oca_github_bot import config


@pytest.fixture
def git_clone(tmp_path):
    """
    A pytest fixture that yields a tmp_path containing a git clone
    of a dummy repository.
    """
    remote = tmp_path / "remote"
    remote.mkdir()
    subprocess.check_call(
        ["git", "init", "--bare", "--initial-branch=master"], cwd=remote
    )
    clone = tmp_path / "clone"
    subprocess.check_call(["git", "clone", str(remote), "clone"], cwd=tmp_path)
    subprocess.check_call(["git", "config", "user.name", "test"], cwd=clone)
    subprocess.check_call(["git", "config", "commit.gpgsign", "false"], cwd=clone)
    subprocess.check_call(
        ["git", "config", "user.email", "test@example.com"], cwd=clone
    )
    somefile = clone / "somefile"
    with somefile.open("w"):
        pass
    subprocess.check_call(["git", "add", "somefile"], cwd=clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add somefile"], cwd=clone)
    subprocess.check_call(["git", "push", "origin", "master"], cwd=clone)
    yield clone


@pytest.fixture(scope="module")
def vcr_config():
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        "filter_headers": [("authorization", "DUMMY")]
    }


@pytest.fixture
def gh():
    """
    github3 test fixture, using the configured GitHub token (if set, to
    record vcr cassettes) or a DUMMY token (if not set, when playing back
    cassettes).
    """
    return github3.login(token=(config.GITHUB_TOKEN or "DUMMY"))
