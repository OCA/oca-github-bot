# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from ..queue import task, getLogger

_logger = getLogger(__name__)


@task()
def main_branch_bot(org, repo, branch):
    _logger.info("*** main_branch_bot", org, repo, branch)
