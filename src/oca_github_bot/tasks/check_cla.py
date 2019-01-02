# Copyright (c) Camptocamp 2018
# Copyright (c) Akretion 2014
from ..cla import CLAChecker
from ..queue import getLogger, task

_logger = getLogger(__name__)


_logger = getLogger(__name__)


@task()
def check_cla(owner, repo, pull_user, pr_number, action):
    checker = CLAChecker(owner, repo, pull_user, pr_number, action)
    return checker.check_cla()
