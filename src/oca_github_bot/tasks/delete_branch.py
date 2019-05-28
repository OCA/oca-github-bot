# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import github
from ..config import switchable
from ..github import gh_call
from ..queue import getLogger, task

_logger = getLogger(__name__)


@task()
@switchable()
def delete_branch(org, repo, branch, dry_run=False):
    with github.repository(org, repo) as gh_repo:
        gh_branch = gh_call(gh_repo.ref, f"heads/{branch}")
        if dry_run:
            _logger.info(f"DRY-RUN delete branch {branch} in {org}/{repo}")
        else:
            _logger.info(f"deleting branch {branch} in {org}/{repo}")
            gh_call(gh_branch.delete)
