# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

from tools.oca_projects import temporary_clone

from ..queue import task, getLogger

_logger = getLogger(__name__)


@task()
def main_branch_bot(org, repo, branch, dry_run=False):
    with temporary_clone(repo, branch):
        _logger.info("oca-gen-addon-readme in %s/%s@%s", org, repo, branch)
        # generate README.rst
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
        # generate default setup.py
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
        # push changes to git, if any
        if not dry_run:
            _logger.info("git push in %s/%s@%s\n", org, repo, branch)
            subprocess.check_call(["git", "push", "origin", branch])
