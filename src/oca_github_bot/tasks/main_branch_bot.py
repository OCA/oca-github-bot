# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from .. import github, manifest
from ..build_wheels import build_and_publish_metapackage_wheel, build_and_publish_wheels
from ..config import (
    GEN_ADDON_ICON_EXTRA_ARGS,
    GEN_ADDON_README_EXTRA_ARGS,
    GEN_ADDONS_TABLE_EXTRA_ARGS,
    dist_publisher,
    switchable,
)
from ..github import git_push_if_needed, temporary_clone
from ..manifest import get_odoo_series_from_branch
from ..process import check_call
from ..queue import getLogger, task
from ..version_branch import is_main_branch_bot_branch

_logger = getLogger(__name__)


@switchable("gen_addons_table")
def _gen_addons_table(org, repo, branch, cwd):
    _logger.info("oca-gen-addons-table in %s/%s@%s", org, repo, branch)
    gen_addons_table_cmd = ["oca-gen-addons-table", "--commit"]
    check_call(
        gen_addons_table_cmd, cwd=cwd, extra_cmd_args=GEN_ADDONS_TABLE_EXTRA_ARGS
    )


@switchable("gen_addons_readme")
def _gen_addons_readme(org, repo, branch, cwd):
    _logger.info("oca-gen-addon-readme in %s/%s@%s", org, repo, branch)
    gen_addon_readme_cmd = [
        "oca-gen-addon-readme",
        "--if-source-changed",
        "--org-name",
        org,
        "--repo-name",
        repo,
        "--branch",
        branch,
        "--addons-dir",
        cwd,
        "--commit",
    ]
    check_call(
        gen_addon_readme_cmd, cwd=cwd, extra_cmd_args=GEN_ADDON_README_EXTRA_ARGS
    )


@switchable("gen_addons_icon")
def _gen_addons_icon(org, repo, branch, cwd):
    _logger.info("oca-gen-addon-icon in %s/%s@%s", org, repo, branch)
    gen_addon_icon_cmd = ["oca-gen-addon-icon", "--addons-dir", cwd, "--commit"]
    check_call(gen_addon_icon_cmd, cwd=cwd)


@switchable("setuptools_odoo")
def _setuptools_odoo_make_default(org, repo, branch, cwd):
    _logger.info("setuptools-odoo-make-default in %s/%s@%s\n", org, repo, branch)
    make_default_setup_cmd = [
        "setuptools-odoo-make-default",
        "--addons-dir",
        cwd,
        "--metapackage",
        org.lower() + "-" + repo,
        "--clean",
        "--commit",
    ]
    check_call(
        make_default_setup_cmd, cwd=cwd, extra_cmd_args=GEN_ADDON_ICON_EXTRA_ARGS
    )


def main_branch_bot_actions(org, repo, branch, cwd):
    """
    Run main branch bot actions on a local git checkout.

    'cwd' is the directory containing the root of a local git checkout.
    """
    _logger.info(f"main_branch_bot {org}/{repo}@{branch}")
    # update addons table in README.md
    _gen_addons_table(org, repo, branch, cwd)
    # generate README.rst
    _gen_addons_readme(org, repo, branch, cwd)
    # generate icon
    _gen_addons_icon(org, repo, branch, cwd)
    # generate/clean default setup.py
    _setuptools_odoo_make_default(org, repo, branch, cwd)


@task()
def main_branch_bot(org, repo, branch, build_wheels, dry_run=False):
    if not is_main_branch_bot_branch(branch):
        return
    with github.repository(org, repo) as gh_repo:
        if gh_repo.fork:
            return
    with temporary_clone(org, repo, branch) as clone_dir:
        if not manifest.is_addons_dir(clone_dir):
            return
        main_branch_bot_actions(org, repo, branch, clone_dir)
        # push changes to git, if any
        if dry_run:
            _logger.info(f"DRY-RUN git push in {org}/{repo}@{branch}")
        else:
            _logger.info(f"git push in {org}/{repo}@{branch}")
            git_push_if_needed("origin", branch, cwd=clone_dir)
        if build_wheels:
            build_and_publish_wheels(clone_dir, dist_publisher, dry_run)
            build_and_publish_metapackage_wheel(
                clone_dir,
                dist_publisher,
                get_odoo_series_from_branch(branch),
                dry_run,
            )


@task()
def main_branch_bot_all_repos(org, build_wheels, dry_run=False):
    with github.login() as gh:
        for repo in gh.repositories_by(org):
            for branch in repo.branches():
                main_branch_bot.delay(
                    org, repo.name, branch.name, build_wheels, dry_run
                )
