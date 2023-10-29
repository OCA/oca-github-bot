# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re
import subprocess
from pathlib import Path

from oca_github_bot.github import (
    git_commit_if_needed,
    git_get_current_branch,
    git_get_head_sha,
)


def test_git_get_head_sha(git_clone):
    sha = git_get_head_sha(git_clone)
    assert re.match("^[a-f0-9]{40}$", sha)


def test_git_get_current_branch(git_clone):
    assert git_get_current_branch(git_clone) == "master"
    subprocess.check_call(["git", "checkout", "-b", "abranch"], cwd=git_clone)
    assert git_get_current_branch(git_clone) == "abranch"


def test_git_commit_if_needed_no_change(tmp_path: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=tmp_path)
    subprocess.check_call(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path
    )
    subprocess.check_call(["git", "config", "user.name", "test"], cwd=tmp_path)
    toto = tmp_path / "toto"
    toto.touch()
    git_commit_if_needed("toto", "initial commit", cwd=tmp_path)
    head_sha = git_get_head_sha(tmp_path)
    # no change
    git_commit_if_needed("toto", "no commit", cwd=tmp_path)
    assert git_get_head_sha(tmp_path) == head_sha
    # change in existing file
    toto.write_text("toto")
    git_commit_if_needed("toto", "toto changed", cwd=tmp_path)
    head_sha2 = git_get_head_sha(tmp_path)
    assert head_sha2 != head_sha
    # add subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    titi = subdir / "titi"
    titi.touch()
    git_commit_if_needed("subdir", "titi added", cwd=tmp_path)
    head_sha3 = git_get_head_sha(tmp_path)
    assert head_sha3 != head_sha2
    # add glob
    subdir.joinpath("pyproject.toml").touch()
    git_commit_if_needed("*/pyproject.toml", "pyproject.toml added", cwd=tmp_path)
    head_sha4 = git_get_head_sha(tmp_path)
    assert head_sha4 != head_sha3
