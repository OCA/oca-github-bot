# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from ..github import temporary_clone
from ..queue import task, getLogger

_logger = getLogger(__name__)


def _gen_addons_table(org, repo, branch, dry_run):
    _logger.info("oca-gen-addons-table in %s/%s@%s", org, repo, branch)
    gen_addons_table_cmd = ["oca-gen-addons-table"]
    if not dry_run:
        gen_addons_table_cmd.append("--commit")
    subprocess.check_call(gen_addons_table_cmd)


def _gen_addons_readme(org, repo, branch, dry_run):
    _logger.info("oca-gen-addon-readme in %s/%s@%s", org, repo, branch)
    gen_addon_readme_cmd = [
        "oca-gen-addon-readme",
        "--repo-name",
        repo,
        "--branch",
        branch,
        "--addons-dir",
        ".",
    ]
    if not dry_run:
        gen_addon_readme_cmd.append("--commit")
    subprocess.check_call(gen_addon_readme_cmd)


def _setuptools_odoo_make_default(org, repo, branch, dry_run):
    _logger.info("setuptools-odoo-make-default in %s/%s@%s\n", org, repo, branch)
    make_default_setup_cmd = [
        "setuptools-odoo-make-default",
        "--addons-dir",
        ".",
        "--metapackage",
        "oca-" + repo,
        "--clean",
    ]
    if not dry_run:
        make_default_setup_cmd.append("--commit")
    subprocess.check_call(make_default_setup_cmd)


@task()
def main_branch_bot(org, repo, branch, dry_run=False):
    with temporary_clone(org, repo, branch):
        # update addons table in README.md
        _gen_addons_table(org, repo, branch, dry_run)
        # generate README.rst
        _gen_addons_readme(org, repo, branch, dry_run)
        # generate/clean default setup.py
        _setuptools_odoo_make_default(org, repo, branch, dry_run)
        # push changes to git, if any
        if not dry_run:
            _logger.info("git push in %s/%s@%s\n", org, repo, branch)
            subprocess.check_call(["git", "push", "origin", branch])
