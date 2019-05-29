# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import pytest
from oca_github_bot.manifest import (
    NoManifestFound,
    bump_manifest_version,
    bump_version,
    get_manifest,
    get_manifest_path,
    git_modified_addons,
    is_addon_dir,
    is_addons_dir,
    set_manifest_version,
)


def test_is_addons_dir_empty(tmpdir):
    tmpdir.mkdir("addon")
    assert not is_addons_dir(str(tmpdir))


def test_is_addons_dir_one_addon(tmpdir):
    p = tmpdir.mkdir("addon").join("__manifest__.py")
    p.write("{'name': 'addon'}")
    assert is_addons_dir(str(tmpdir))


def test_is_addon_dir(tmp_path):
    assert not is_addon_dir(tmp_path)
    m = tmp_path / "__manifest__.py"
    m.write_text("{'name': 'addon'}")
    assert is_addon_dir(tmp_path)


def test_get_manifest_path(tmp_path):
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    assert not get_manifest_path(addon_dir)
    with pytest.raises(NoManifestFound):
        get_manifest(addon_dir)
    manifest_path = addon_dir / "__manifest__.py"
    with manifest_path.open("w") as f:
        f.write("{'name': 'the addon'}")
    assert get_manifest_path(addon_dir) == str(manifest_path)
    assert get_manifest(addon_dir)["name"] == "the addon"


def test_set_addon_version(tmp_path):
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    manifest_path = addon_dir / "__manifest__.py"
    with manifest_path.open("w") as f:
        f.write("{'name': 'thé addon', 'version': '1.0.0'}")
    set_manifest_version(addon_dir, "2.0.1")
    m = get_manifest(addon_dir)
    assert m["version"] == "2.0.1"
    assert m["name"] == "thé addon"


def test_bump_version():
    assert bump_version("12.0.1.0.0", "major") == "12.0.2.0.0"
    assert bump_version("12.0.1.1.1", "major") == "12.0.2.0.0"
    assert bump_version("12.0.1.0.0", "minor") == "12.0.1.1.0"
    assert bump_version("12.0.1.0.1", "minor") == "12.0.1.1.0"
    assert bump_version("12.0.1.0.0", "patch") == "12.0.1.0.1"
    with pytest.raises(RuntimeError):
        bump_version("1.0", "major")
    with pytest.raises(RuntimeError):
        bump_version("1.0.1", "major")
    with pytest.raises(RuntimeError):
        bump_version("12.0.1.0.0", "none")


def test_bump_manifest_version(tmp_path):
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    manifest_path = addon_dir / "__manifest__.py"
    with manifest_path.open("w") as f:
        f.write("{'name': 'the addon', 'version': '12.0.1.0.0'}")
    bump_manifest_version(addon_dir, "minor")
    m = get_manifest(addon_dir)
    assert m["version"] == "12.0.1.1.0"


def tests_git_modified_addons(git_clone):
    # create an addon, commit it, and check it is modified
    addon_dir = git_clone / "addon"
    addon_dir.mkdir()
    manifest_path = addon_dir / "__manifest__.py"
    manifest_path.write_text("{'name': 'the addon'}")
    subprocess.check_call(["git", "add", "."], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "add addon"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == {"addon"}
    # push and check addon is not modified
    subprocess.check_call(["git", "push", "origin", "master"], cwd=git_clone)
    assert not git_modified_addons(git_clone, "origin/master")
    # same test with the setup dir
    setup_dir = git_clone / "setup" / "addon"
    setup_dir.mkdir(parents=True)
    (setup_dir / "setup.py").write_text("")
    subprocess.check_call(["git", "add", "setup"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "add addon setup"], cwd=git_clone)
    assert not git_modified_addons(git_clone, "origin/master")
    (setup_dir / "odoo" / "addons").mkdir(parents=True)
    (setup_dir / "odoo" / "addons" / "addon").symlink_to("../../../../addon")
    subprocess.check_call(["git", "add", "setup"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "add addon setup"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == {"addon"}
    # add a second addon, and change the first one
    addon2_dir = git_clone / "addon2"
    addon2_dir.mkdir()
    manifest2_path = addon2_dir / "__manifest__.py"
    manifest2_path.write_text("{'name': 'the 2nd addon'}")
    (addon_dir / "__init__.py").write_text("")
    (git_clone / "README").write_text("")
    subprocess.check_call(["git", "add", "."], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "add addon2"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == {"addon", "addon2"}
