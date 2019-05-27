# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from .. import github, manifest
from ..github import git_push_if_needed, temporary_clone
from ..queue import getLogger, task
from ..version_branch import is_main_branch_bot_branch

_logger = getLogger(__name__)


def _gen_addons_table(org, repo, branch, dry_run):
    _logger.info("oca-gen-addons-table in %s/%s@%s", org, repo, branch)
    gen_addons_table_cmd = ["oca-gen-addons-table"]
    if not dry_run:
        gen_addons_table_cmd.append("--commit")
    subprocess.check_output(gen_addons_table_cmd, stderr=subprocess.STDOUT)


def _gen_addons_readme(org, repo, branch, dry_run):
    _logger.info("oca-gen-addon-readme in %s/%s@%s", org, repo, branch)
    gen_addon_readme_cmd = [
        "oca-gen-addon-readme",
        "--org-name",
        org,
        "--repo-name",
        repo,
        "--branch",
        branch,
        "--addons-dir",
        ".",
    ]
    if not dry_run:
        gen_addon_readme_cmd.append("--commit")
    subprocess.check_output(gen_addon_readme_cmd, stderr=subprocess.STDOUT)


def _gen_addons_icon(org, repo, branch, dry_run):
    _logger.info("oca-gen-addon-icon in %s/%s@%s", org, repo, branch)
    gen_addon_icon_cmd = ["oca-gen-addon-icon", "--addons-dir", "."]
    if not dry_run:
        gen_addon_icon_cmd.append("--commit")
    subprocess.check_output(gen_addon_icon_cmd, stderr=subprocess.STDOUT)


def _setuptools_odoo_make_default(org, repo, branch, dry_run):
    _logger.info("setuptools-odoo-make-default in %s/%s@%s\n", org, repo, branch)
    make_default_setup_cmd = [
        "setuptools-odoo-make-default",
        "--addons-dir",
        ".",
        "--metapackage",
        org.lower() + "-" + repo,
        "--clean",
    ]
    if not dry_run:
        make_default_setup_cmd.append("--commit")
    subprocess.check_output(make_default_setup_cmd, stderr=subprocess.STDOUT)


@task()
def main_branch_bot(org, repo, branch, dry_run=False):
    if not is_main_branch_bot_branch(branch):
        return
    with temporary_clone(org, repo, branch):
        if not manifest.is_addons_dir("."):
            return
        _logger.info(f"main_branch_bot {org}/{repo}@{branch}")
        # update addons table in README.md
        _gen_addons_table(org, repo, branch, dry_run)
        # generate README.rst
        _gen_addons_readme(org, repo, branch, dry_run)
        # generate icon
        _gen_addons_icon(org, repo, branch, dry_run)
        # generate/clean default setup.py
        _setuptools_odoo_make_default(org, repo, branch, dry_run)
        # push changes to git, if any
        if dry_run:
            _logger.info(f"DRY-RUN git push in {org}/{repo}@{branch}")
        else:
            _logger.info(f"git push in {org}/{repo}@{branch}")
            git_push_if_needed("origin", branch)


@task()
def main_branch_bot_all_repos(org, dry_run=False):
    with github.login() as gh:
        for repo in gh.repositories_by(org):
            for branch in repo.branches():
                main_branch_bot.delay(org, repo.name, branch.name, dry_run)
