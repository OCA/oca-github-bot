# Copyright (c) GRAP SCIC SA 2020 (http://www.grap.coop)
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import github
from ..queue import task


@task()
def add_pr_comment(org, repo, pr, message):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        github.gh_call(gh_pr.create_comment, message)
