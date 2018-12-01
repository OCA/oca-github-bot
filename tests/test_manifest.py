# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest
from oca_github_bot.manifest import (
    NoManifestFound,
    bump_manifest_version,
    bump_version,
    get_manifest,
    get_manifest_path,
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
    assert bump_version("12.0.1.0.0", "minor") == "12.0.1.1.0"
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
