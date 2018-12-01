# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import pytest


@pytest.fixture
def git_clone(tmp_path):
    """
    A pytest fixture that yields a tmp_path containing a git clone
    of a dummy repository.
    """
    remote = tmp_path / "remote"
    remote.mkdir()
    subprocess.check_call(["git", "init", "--bare"], cwd=remote)
    clone = tmp_path / "clone"
    subprocess.check_call(["git", "clone", str(remote), "clone"], cwd=tmp_path)
    subprocess.check_call(["git", "config", "user.name", "test"], cwd=clone)
    subprocess.check_call(
        ["git", "config", "user.email", "test@example.com"], cwd=clone
    )
    somefile = clone / "somefile"
    with somefile.open("w"):
        pass
    subprocess.check_call(["git", "add", "somefile"], cwd=clone)
    subprocess.check_call(["git", "commit", "-m", "add somefile"], cwd=clone)
    subprocess.check_call(["git", "push", "origin", "master"], cwd=clone)
    yield clone
