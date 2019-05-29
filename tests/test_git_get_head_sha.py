# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

from oca_github_bot.github import git_get_head_sha


def test_git_get_head_sha(git_clone):
    sha = git_get_head_sha()
    assert re.match("^[a-f0-9]{40}$", sha)
