# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import pytest
from celery.exceptions import Retry

from oca_github_bot.github import git_push_if_needed


def test_git_push_if_needed(git_clone):
    assert not git_push_if_needed("origin", "master", cwd=git_clone)
    afile = git_clone / "afile"
    with afile.open("w"):
        pass
    subprocess.check_call(["git", "add", "afile"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add afile"], cwd=git_clone)
    assert git_push_if_needed("origin", "master", cwd=git_clone)
    assert not git_push_if_needed("origin", "master", cwd=git_clone)
    subprocess.check_call(["git", "reset", "--hard", "HEAD^"], cwd=git_clone)
    with pytest.raises(Retry):
        git_push_if_needed("origin", "master", cwd=git_clone)
