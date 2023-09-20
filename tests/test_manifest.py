# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import subprocess

import pytest

from oca_github_bot.github import git_get_head_sha
from oca_github_bot.manifest import (
    NoManifestFound,
    OdooSeriesNotDetected,
    bump_manifest_version,
    bump_version,
    get_manifest,
    get_manifest_path,
    get_odoo_series_from_branch,
    get_odoo_series_from_version,
    git_modified_addon_dirs,
    git_modified_addons,
    is_addon_dir,
    is_addons_dir,
    is_maintainer,
    is_maintainer_other_branches,
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
    m.write_text("{'name': 'addon', 'installable': False}")
    assert is_addon_dir(tmp_path)
    m.write_text("{'name': 'addon', 'installable': False}")
    assert not is_addon_dir(tmp_path, installable_only=True)
    m.write_text("{'name': 'addon', 'installable': True}")
    assert is_addon_dir(tmp_path, installable_only=True)


def test_is_addons_dir(tmp_path):
    addon1 = tmp_path / "addon1"
    addon1.mkdir()
    assert not is_addons_dir(tmp_path)
    m = addon1 / "__manifest__.py"
    m.write_text("{'name': 'addon'}")
    assert is_addons_dir(tmp_path)
    m.write_text("{'name': 'addon', 'installable': False}")
    assert is_addons_dir(tmp_path)
    m.write_text("{'name': 'addon', 'installable': False}")
    assert not is_addons_dir(tmp_path, installable_only=True)
    m.write_text("{'name': 'addon', 'installable': True}")
    assert is_addons_dir(tmp_path, installable_only=True)


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


def test_git_modified_addons(git_clone):
    # create an addon, commit it, and check it is modified
    addon_dir = git_clone / "addon"
    addon_dir.mkdir()
    manifest_path = addon_dir / "__manifest__.py"
    manifest_path.write_text("{'name': 'the addon'}")
    subprocess.check_call(["git", "add", "."], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add addon"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == ({"addon"}, False)
    # push and check addon is not modified
    subprocess.check_call(["git", "push", "origin", "master"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == (set(), False)
    # same test with the setup dir
    setup_dir = git_clone / "setup" / "addon"
    setup_dir.mkdir(parents=True)
    (setup_dir / "setup.py").write_text("")
    subprocess.check_call(["git", "add", "setup"], cwd=git_clone)
    subprocess.check_call(
        ["git", "commit", "-m", "[BOT] add addon setup"], cwd=git_clone
    )
    assert git_modified_addons(git_clone, "origin/master") == (set(), True)
    (setup_dir / "odoo" / "addons").mkdir(parents=True)
    (setup_dir / "odoo" / "addons" / "addon").symlink_to("../../../../addon")
    subprocess.check_call(["git", "add", "setup"], cwd=git_clone)
    subprocess.check_call(
        ["git", "commit", "-m", "[BOT] add addon setup"], cwd=git_clone
    )
    assert git_modified_addons(git_clone, "origin/master") == ({"addon"}, False)
    assert git_modified_addon_dirs(git_clone, "origin/master") == (
        [str(git_clone / "addon")],
        False,
        {"addon"},
    )
    # add a second addon, and change the first one
    addon2_dir = git_clone / "addon2"
    addon2_dir.mkdir()
    manifest2_path = addon2_dir / "__manifest__.py"
    manifest2_path.write_text("{'name': 'the 2nd addon'}")
    (addon_dir / "__init__.py").write_text("")
    (git_clone / "README").write_text("")
    subprocess.check_call(["git", "add", "."], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add addon2"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == (
        {"addon", "addon2"},
        True,  # because of README at repo root
    )
    # remove the first and test it does not appear in result
    subprocess.check_call(["git", "tag", "beforerm"], cwd=git_clone)
    subprocess.check_call(["git", "rm", "-r", "addon"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] rm addon"], cwd=git_clone)
    assert git_modified_addons(git_clone, "beforerm") == (set(), True)


def test_git_modified_addons_merge_base(git_clone):
    # create addon2 on master
    addon2_dir = git_clone / "addon2"
    addon2_dir.mkdir()
    (addon2_dir / "__manifest__.py").write_text("{'name': 'addon2'}")
    subprocess.check_call(["git", "add", "addon2"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add addon2"], cwd=git_clone)
    assert git_modified_addons(git_clone, "origin/master") == ({"addon2"}, False)
    # create addon1 on a new branch
    subprocess.check_call(["git", "checkout", "-b" "addon1"], cwd=git_clone)
    addon1_dir = git_clone / "addon1"
    addon1_dir.mkdir()
    (addon1_dir / "__manifest__.py").write_text("{'name': 'addon1'}")
    subprocess.check_call(["git", "add", "addon1"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add addon1"], cwd=git_clone)
    assert git_modified_addons(git_clone, "master") == ({"addon1"}, False)
    # modify addon2 on master
    subprocess.check_call(["git", "checkout", "master"], cwd=git_clone)
    (addon2_dir / "__manifest__.py").write_text("{'name': 'modified addon2'}")
    subprocess.check_call(["git", "add", "addon2"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] upd addon2"], cwd=git_clone)
    # check comparison of addon1 to master only gives addon1
    subprocess.check_call(["git", "checkout", "addon1"], cwd=git_clone)
    assert git_modified_addons(git_clone, "master") == ({"addon1"}, False)
    # add same commit in master and addon1
    subprocess.check_call(["git", "checkout", "master"], cwd=git_clone)
    addon3_dir = git_clone / "addon3"
    addon3_dir.mkdir()
    (addon3_dir / "__manifest__.py").write_text("{'name': 'addon3'}")
    subprocess.check_call(["git", "add", "addon3"], cwd=git_clone)
    subprocess.check_call(["git", "commit", "-m", "[BOT] add addon3"], cwd=git_clone)
    assert git_modified_addons(git_clone, "HEAD^") == ({"addon3"}, False)
    commit = git_get_head_sha(cwd=git_clone)
    subprocess.check_call(["git", "checkout", "addon1"], cwd=git_clone)
    subprocess.check_call(["git", "cherry-pick", commit], cwd=git_clone)
    assert git_modified_addons(git_clone, "master") == ({"addon1"}, False)


def test_get_odoo_series_from_branch():
    assert get_odoo_series_from_branch("12.0") == (12, 0)
    with pytest.raises(OdooSeriesNotDetected):
        get_odoo_series_from_branch("12.0.0")


def test_get_odoo_series_from_version():
    assert get_odoo_series_from_version("12.0.1.0.0") == (12, 0)
    assert get_odoo_series_from_version("6.1.1.0.0") == (6, 1)
    with pytest.raises(OdooSeriesNotDetected):
        get_odoo_series_from_version("1.0.0")
    with pytest.raises(OdooSeriesNotDetected):
        get_odoo_series_from_version("1.0")
    with pytest.raises(OdooSeriesNotDetected):
        get_odoo_series_from_version("12.0.1")


def test_is_maintainer(tmp_path):
    addon1 = tmp_path / "addon1"
    addon1.mkdir()
    (addon1 / "__manifest__.py").write_text(
        "{'name': 'addon1', 'maintainers': ['u1', 'u2']}"
    )
    addon2 = tmp_path / "addon2"
    addon2.mkdir()
    (addon2 / "__manifest__.py").write_text("{'name': 'addon2', 'maintainers': ['u2']}")
    addon3 = tmp_path / "addon3"
    addon3.mkdir()
    (addon3 / "__manifest__.py").write_text("{'name': 'addon3'}")
    assert is_maintainer("u1", [addon1])
    assert not is_maintainer("u1", [addon2])
    assert not is_maintainer("u1", [addon1, addon2])
    assert is_maintainer("u2", [addon1, addon2])
    assert not is_maintainer("u2", [addon1, addon2, addon3])
    assert not is_maintainer("u1", [tmp_path / "not_an_addon"])


def test_is_maintainer_other_branches():
    assert is_maintainer_other_branches(
        "OCA", "mis-builder", "sbidoul", {"mis_builder"}, ["12.0"]
    )
    assert not is_maintainer_other_branches(
        "OCA", "mis-builder", "fpdoo", {"mis_builder"}, ["12.0"]
    )
