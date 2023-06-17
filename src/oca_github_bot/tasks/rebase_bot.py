# Copyright (c) ForgeFlow, S.L. 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import config, github
from ..config import switchable
from ..manifest import user_can_push
from ..process import CalledProcessError, check_call
from ..queue import getLogger, task
from ..utils import cmd_to_str, hide_secrets

_logger = getLogger(__name__)


@task()
@switchable("rebase_bot")
def rebase_bot_start(org, repo, pr, username, dry_run=False):
    with github.login() as gh:
        gh_pr = gh.pull_request(org, repo, pr)
        target_branch = gh_pr.base.ref
        remote = gh_pr.head._repo_owner
        pr_branch = f"tmp-pr-{pr}"
        try:
            with github.temporary_clone(org, repo, target_branch) as clone_dir:
                if not remote:
                    github.gh_call(
                        gh_pr.create_comment,
                        f"Sorry @{username}, impossible to rebase because "
                        f"unknown remote.",
                    )
                    return
                check_call(
                    ["git", "fetch", "origin", f"pull/{pr}/head:{pr_branch}"],
                    cwd=clone_dir,
                )
                check_call(["git", "checkout", pr_branch], cwd=clone_dir)
                if not user_can_push(gh, org, repo, username, clone_dir, target_branch):
                    github.gh_call(
                        gh_pr.create_comment,
                        f"Sorry @{username} you are not allowed to rebase.\n\n"
                        f"To do so you must either have push permissions on "
                        f"the repository, or be a declared maintainer of all "
                        f"modified addons.\n\n"
                        f"If you wish to adopt an addon and become it's "
                        f"[maintainer]"
                        f"(https://odoo-community.org/page/maintainer-role), "
                        f"open a pull request to add "
                        f"your GitHub login to the `maintainers` key of its "
                        f"manifest.",
                    )
                    return
                # do rebase
                check_call(["git", "fetch", "origin", target_branch], cwd=clone_dir)
                check_call(["git", "rebase", f"origin/{target_branch}"], cwd=clone_dir)
                # push rebase
                true_pr_branch = gh_pr.head.ref
                if dry_run:
                    _logger.info(
                        f"DRY-RUN git push in {remote}/{repo}@{true_pr_branch}"
                    )
                else:
                    _logger.info(f"git push in {remote}/{repo}@{true_pr_branch}")
                    check_call(
                        [
                            "git",
                            "remote",
                            "add",
                            remote,
                            f"https://github.com/{remote}/{repo}.git",
                        ],
                        cwd=clone_dir,
                    )
                    check_call(
                        [
                            "git",
                            "remote",
                            "set-url",
                            "--push",
                            remote,
                            f"https://{config.GITHUB_TOKEN}@github.com/{remote}/{repo}",
                        ],
                        cwd=clone_dir,
                    )
                    check_call(
                        [
                            "git",
                            "push",
                            "--force",
                            remote,
                            f"{pr_branch}:{true_pr_branch}",
                        ],
                        cwd=clone_dir,
                        log_error=False,
                    )
                github.gh_call(
                    gh_pr.create_comment,
                    f"Congratulations, PR rebased to [{target_branch}]"
                    f"(https://github.com/{org}/{repo}/commits/{target_branch}).",
                )
        except CalledProcessError as e:
            cmd = cmd_to_str(e.cmd)
            github.gh_call(
                gh_pr.create_comment,
                hide_secrets(
                    f"@{username} The rebase process failed, because "
                    f"command `{cmd}` failed with output:\n```\n{e.output}\n```"
                ),
            )
            raise
        except Exception as e:
            github.gh_call(
                gh_pr.create_comment,
                hide_secrets(
                    f"@{username} The rebase process failed, because of exception {e}."
                ),
            )
            raise
