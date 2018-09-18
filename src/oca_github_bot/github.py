# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import github3

from . import config


def login():
    return github3.login(token=config.GITHUB_TOKEN)
