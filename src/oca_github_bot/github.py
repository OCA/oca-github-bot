# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from contextlib import contextmanager
import logging

import github3

from . import config

_logger = logging.getLogger(__name__)


@contextmanager
def login():
    """GitHub login as decorator so a pool can be implemented later."""
    yield github3.login(token=config.GITHUB_TOKEN)


@contextmanager
def repository(org, repo):
    with login() as gh:
        yield gh.repository(org, repo)


def gh_call(func, *args, **kwargs):
    """Intercept GitHub call to wait when the API rate limit is reached."""
    # TODO
    return func(*args, **kwargs)
