# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import contextmanager

import appdirs
import github3
from celery.exceptions import Retry

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


def gh_date(d):
    return d.isoformat()


def gh_datetime(utc_dt):
    return utc_dt.isoformat()[:19] + "+00:00"


class BranchNotFoundError(RuntimeError):
    pass


@contextmanager
def temporary_clone(org, repo, branch):
    """ context manager that clones a git branch and cd to it, with cache """
    # init cache directory
    cache_dir = appdirs.user_cache_dir("oca-mqt")
    repo_cache_dir = os.path.join(cache_dir, "github.com", org.lower(), repo.lower())
    if not os.path.isdir(repo_cache_dir):
        os.makedirs(repo_cache_dir)
        subprocess.check_call(["git", "init", "--bare"], cwd=repo_cache_dir)
    repo_url = f"https://{config.GITHUB_TOKEN}@github.com/{org}/{repo}"
    # fetch all branches into cache
    fetch_cmd = [
        "git",
        "fetch",
        "--quiet",
        "--force",
        repo_url,
        "refs/heads/*:refs/heads/*",
    ]
    subprocess.check_call(fetch_cmd, cwd=repo_cache_dir)
    # check if branch exist
    branches = subprocess.check_output(
        ["git", "branch"], universal_newlines=True, cwd=repo_cache_dir
    )
    branches = [b.strip() for b in branches.split()]
    if branch not in branches:
        raise BranchNotFoundError()
    # clone to temp dir, with --reference to cache
    tempdir = tempfile.mkdtemp()
    try:
        clone_cmd = [
            "git",
            "clone",
            "--quiet",
            "--reference",
            repo_cache_dir,
            "--branch",
            branch,
            "--",
            repo_url,
            tempdir,
        ]
        subprocess.check_call(clone_cmd)
        cwd = os.getcwd()
        os.chdir(tempdir)
        try:
            if config.GIT_NAME:
                subprocess.check_call(["git", "config", "user.name", config.GIT_NAME])
            if config.GIT_EMAIL:
                subprocess.check_call(["git", "config", "user.email", config.GIT_EMAIL])
            yield
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(tempdir)
