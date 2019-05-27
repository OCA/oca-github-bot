# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..github import temporary_clone
from ..queue import getLogger, task

_logger = getLogger(__name__)


@task()
def merge_bot(org, repo, pr, target_branch, user, dry_run=False):
    # 1. check user has write access
    with temporary_clone(org, repo, target_branch):
        # 2. rebase on target branch
        pass
