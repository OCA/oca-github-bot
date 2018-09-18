# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..queue import task, getLogger

from .. import github

_logger = getLogger(__name__)


@task()
def delete_branch(org, repo, branch):
    gh = github.login()
    gh_repo = gh.repository(org, repo)
    gh_branch = gh_repo.ref(f"heads/{branch}")
    gh_branch.delete()
