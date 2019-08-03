import celery
import pytest
import requests
from github3.exceptions import ForbiddenError

from oca_github_bot.github import gh_call


def _fail_just_like_that():
    response = requests.Response()
    raise ForbiddenError(response)


def _fail_ratelimit():
    response = requests.Response()
    response.headers.update({"X-RateLimit-Remaining": 0, "X-RateLimit-Reset": -1})
    raise ForbiddenError(response)


def test_github_failure(mocker):
    with pytest.raises(celery.exceptions.Retry):
        # this will restart the task
        gh_call(_fail_ratelimit)
    with pytest.raises(ForbiddenError):
        # an unhandled error
        gh_call(_fail_just_like_that)
