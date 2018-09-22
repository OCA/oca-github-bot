# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..queue import task, getLogger

from .. import github
from ..github import gh_call

_logger = getLogger(__name__)


@task()
def delete_branch(org, repo, branch, dry_run=False):
    with github.repository(org, repo) as gh_repo:
        gh_branch = gh_call(gh_repo.ref, f"heads/{branch}")
        if dry_run:
            _logger.info(f"DRY-RUN delete branch {branch} in {org}/{repo}")
        else:
            gh_call(gh_branch.delete)
