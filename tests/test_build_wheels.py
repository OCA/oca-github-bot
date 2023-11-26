# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os
import subprocess
import textwrap

import pytest

from oca_github_bot.build_wheels import (
    build_and_publish_metapackage_wheel,
    build_and_publish_wheels,
)
from oca_github_bot.pypi import RsyncDistPublisher


def _init_git_repo(cwd):
    subprocess.check_call(["git", "init"], cwd=cwd)
    subprocess.check_call(["git", "config", "user.name", "test"], cwd=cwd)
    subprocess.check_call(["git", "config", "commit.gpgsign", "false"], cwd=cwd)
    subprocess.check_call(["git", "config", "user.email", "test@example.com"], cwd=cwd)


def _make_addon(
    addons_dir, addon_name, series, metapackage=None, setup_py=True, pyproject=False
):
    addon_dir = addons_dir / addon_name
    addon_dir.mkdir()
    manifest_path = addon_dir / "__manifest__.py"
    manifest_path.write_text(
        repr(
            {
                "name": addon_name,
                "version": series + ".1.0.0",
                "description": "...",
            }
        )
    )
    (addon_dir / "__init__.py").write_text("")
    if pyproject:
        (addon_dir / "pyproject.toml").write_text(
            textwrap.dedent(
                """\
                [build-system]
                requires = ["whool"]
                build-backend = "whool.buildapi"
                """
            )
        )
    subprocess.check_call(["git", "add", addon_name], cwd=addons_dir)
    subprocess.check_call(
        ["git", "commit", "-m", "[BOT] add " + addon_name], cwd=addons_dir
    )
    subprocess.check_call(["git", "clean", "-ffdx", "--", "setup"], cwd=addons_dir)
    if setup_py:
        cmd = ["setuptools-odoo-make-default", "-d", str(addons_dir), "--commit"]
        if metapackage:
            cmd.extend(["--metapackage", metapackage])
        subprocess.check_call(cmd)


@pytest.mark.parametrize("setup_py", [True, False])
def test_build_and_publish_wheels(setup_py, tmp_path):
    addons_dir = tmp_path / "addons_dir"
    addons_dir.mkdir()
    _init_git_repo(addons_dir)
    simple_index_root = tmp_path / "simple_index"
    simple_index_root.mkdir()
    dist_publisher = RsyncDistPublisher(simple_index_root)
    # build with no addons
    build_and_publish_wheels(addons_dir, dist_publisher, dry_run=False)
    assert not os.listdir(simple_index_root)
    # build with one addon
    _make_addon(addons_dir, "addon1", "12.0", setup_py=setup_py, pyproject=not setup_py)
    build_and_publish_wheels(str(addons_dir), dist_publisher, dry_run=False)
    wheel_dirs = os.listdir(simple_index_root)
    assert len(wheel_dirs) == 1
    assert wheel_dirs[0] == "odoo12-addon-addon1"
    wheels = os.listdir(simple_index_root / "odoo12-addon-addon1")
    assert len(wheels) == 1
    assert wheels[0].startswith("odoo12_addon_addon1")
    assert wheels[0].endswith(".whl")
    assert "-py3-" in wheels[0]
    # build with two addons, don't use pyproject.toml for this version
    _make_addon(addons_dir, "addon2", "10.0", setup_py=True, pyproject=False)
    build_and_publish_wheels(str(addons_dir), dist_publisher, dry_run=False)
    wheel_dirs = sorted(os.listdir(simple_index_root))
    assert len(wheel_dirs) == 2
    assert wheel_dirs[0] == "odoo10-addon-addon2"
    wheels = os.listdir(simple_index_root / "odoo10-addon-addon2")
    assert len(wheels) == 1
    assert wheels[0].startswith("odoo10_addon_addon2")
    assert wheels[0].endswith(".whl")
    assert "-py2-" in wheels[0]
    # test tag for Odoo 11, don't use pyproject.toml for this version
    _make_addon(addons_dir, "addon3", "11.0", setup_py=True, pyproject=False)
    build_and_publish_wheels(str(addons_dir), dist_publisher, dry_run=False)
    wheel_dirs = sorted(os.listdir(simple_index_root))
    assert len(wheel_dirs) == 3
    assert wheel_dirs[1] == "odoo11-addon-addon3"
    wheels = os.listdir(simple_index_root / "odoo11-addon-addon3")
    assert len(wheels) == 1
    assert "-py2.py3-" in wheels[0]
    # test Odoo 15+ default addon naming scheme
    _make_addon(addons_dir, "addon4", "15.0", setup_py=setup_py, pyproject=not setup_py)
    build_and_publish_wheels(str(addons_dir), dist_publisher, dry_run=False)
    wheel_dirs = sorted(os.listdir(simple_index_root))
    assert len(wheel_dirs) == 4
    assert wheel_dirs[0] == "odoo-addon-addon4"
    wheels = os.listdir(simple_index_root / "odoo-addon-addon4")
    assert len(wheels) == 1
    assert wheels[0].startswith("odoo_addon_addon4")
    assert wheels[0].endswith(".whl")
    assert "-py3-" in wheels[0]


def test_build_and_publish_metapackage(tmp_path):
    addons_dir = tmp_path / "addons_dir"
    addons_dir.mkdir()
    _init_git_repo(addons_dir)
    simple_index_root = tmp_path / "simple_index"
    simple_index_root.mkdir()
    dist_publisher = RsyncDistPublisher(simple_index_root)
    # build with one addon
    _make_addon(addons_dir, "addon1", "12.0", metapackage="test")
    build_and_publish_metapackage_wheel(
        str(addons_dir), dist_publisher, (12, 0), dry_run=False
    )
    wheels = os.listdir(simple_index_root / "odoo12-addons-test")
    assert len(wheels) == 1
    assert wheels[0].startswith("odoo12_addons_test")
    assert wheels[0].endswith(".whl")
    assert "-py3-" in wheels[0]
