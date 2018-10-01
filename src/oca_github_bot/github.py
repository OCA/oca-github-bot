# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from contextlib import contextmanager
from celery.exceptions import Retry
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
    try:
        return func(*args, **kwargs)
    except github3.exceptions.ForbiddenError as e:
        if not e.response.headers.get("X-RateLimit-Remaining", 1):
            raise Retry(
                message="Retry task after rate limit reset",
                exc=e,
                when=e.response.headers.get("X-RateLimit-Reset"),
            )
        raise
