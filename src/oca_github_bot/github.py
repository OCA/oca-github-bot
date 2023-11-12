# Copyright (c) ACSONE SA/NV 2018-2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import functools
import logging
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

import appdirs
import github3
from celery.exceptions import Retry

from . import config
from .process import CalledProcessError, call, check_call, check_output
from .utils import retry_on_exception

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
    """context manager that clones a git branch into a tremporary directory,
    and yields the temp dir name, with cache"""
    # init cache directory
    cache_dir = appdirs.user_cache_dir("oca-mqt")
    repo_cache_dir = os.path.join(cache_dir, "github.com", org.lower(), repo.lower())
    if not os.path.isdir(repo_cache_dir):
        os.makedirs(repo_cache_dir)
        check_call(["git", "init", "--bare"], cwd=repo_cache_dir)
    repo_url = f"https://github.com/{org}/{repo}"
    repo_url_with_token = f"https://{config.GITHUB_TOKEN}@github.com/{org}/{repo}"
    # fetch all branches into cache
    fetch_cmd = [
        "git",
        "fetch",
        "--quiet",
        "--force",
        "--prune",
        repo_url,
        "refs/heads/*:refs/heads/*",
    ]
    retry_on_exception(
        functools.partial(check_call, fetch_cmd, cwd=repo_cache_dir),
        "error: cannot lock ref",
        sleep_time=10.0,
    )
    # check if branch exist
    branches = check_output(["git", "branch"], cwd=repo_cache_dir)
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
        check_call(clone_cmd, cwd=".")
        if config.GIT_NAME:
            check_call(["git", "config", "user.name", config.GIT_NAME], cwd=tempdir)
        if config.GIT_EMAIL:
            check_call(["git", "config", "user.email", config.GIT_EMAIL], cwd=tempdir)
        check_call(
            ["git", "remote", "set-url", "--push", "origin", repo_url_with_token],
            cwd=tempdir,
        )
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def git_push_if_needed(remote, branch, cwd=None):
    """
    Push current HEAD to remote branch.

    Return True if push succeeded, False if there was nothing to push.
    Raises a celery Retry exception in case of non-fast-forward push.
    """
    r = call(["git", "diff", "--quiet", "--exit-code", remote + "/" + branch], cwd=cwd)
    if r == 0:
        return False
    try:
        check_call(["git", "push", remote, branch], cwd=cwd, log_error=False)
    except CalledProcessError as e:
        if "non-fast-forward" in e.output:
            raise Retry(
                exc=e,
                message="Retrying because a non-fast-forward git push was attempted.",
            )
        else:
            _logger.error(
                f"command {e.cmd} failed with return code {e.returncode} "
                f"and output:\n{e.output}"
            )
            raise
    return True


def github_user_can_push(gh_repo, username):
    for collaborator in gh_call(gh_repo.collaborators):
        if username == collaborator.login and collaborator.permissions.get("push"):
            return True
    return False


def git_get_head_sha(cwd):
    """Get the sha of the git HEAD in current directory"""
    return check_output(["git", "rev-parse", "HEAD"], cwd=cwd).strip()


def git_get_current_branch(cwd):
    return check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).strip()


def git_commit_if_needed(glob_pattern, msg, cwd):
    files = [p.absolute() for p in Path(cwd).glob(glob_pattern)]
    if not files:
        return  # no match nothing to commit
    check_call(["git", "add", *files], cwd=cwd)
    if call(["git", "diff", "--cached", "--quiet", "--exit-code"], cwd=cwd) == 0:
        return  # nothing added
    return check_call(["git", "commit", "-m", msg], cwd=cwd)
