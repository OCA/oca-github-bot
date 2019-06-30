# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os
import subprocess
import sys
import tempfile

from .manifest import addon_dirs_in, get_manifest, get_odoo_series_from_version


def _build_wheel(addon_dir, dist_dir):
    manifest = get_manifest(addon_dir)
    if not manifest.get("installable", True):
        return
    series = get_odoo_series_from_version(manifest.get("version", ""))
    if series < (8, 0):
        return
    addon_name = os.path.basename(addon_dir)
    setup_dir = os.path.join(addon_dir, "..", "setup", addon_name)
    setup_file = os.path.join(setup_dir, "setup.py")
    if not os.path.isfile(setup_file):
        return
    with tempfile.TemporaryDirectory() as tempdir:
        bdist_dir = os.path.join(tempdir, "build")
        os.mkdir(bdist_dir)
        cmd = [
            sys.executable,
            "setup.py",
            "bdist_wheel",
            "--dist-dir",
            dist_dir,
            "--bdist-dir",
            bdist_dir,
            "--python-tag",
            "py2" if series < (11, 0) else "py3",
        ]
        subprocess.check_output(cmd, cwd=setup_dir, stderr=subprocess.STDOUT)


def _check_wheels(dist_dir):
    wheels = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    subprocess.check_output(
        ["twine", "check"] + wheels, cwd=dist_dir, stderr=subprocess.STDOUT
    )


def build_and_check_wheel(addon_dir):
    with tempfile.TemporaryDirectory() as dist_dir:
        _build_wheel(addon_dir, dist_dir)
        _check_wheels(dist_dir)


def build_and_publish_wheel(addon_dir, simple_index_root):
    with tempfile.TemporaryDirectory() as dist_dir:
        _build_wheel(addon_dir, dist_dir)
        _check_wheels(dist_dir)
        _publish_dist_dir_to_simple_index(dist_dir, simple_index_root)


def build_and_publish_wheels(addons_dir, simple_index_root):
    for addon_dir in addon_dirs_in(addons_dir):
        build_and_publish_wheel(addon_dir, simple_index_root)


def _publish_dist_dir_to_simple_index(dist_dir, simple_index_root):
    pkgname = _find_pkgname(dist_dir)
    fulltarget = os.path.join(simple_index_root, pkgname, "")
    # --ignore-existing: never overwrite an existing package
    # os.path.join: make sure directory names end with /
    subprocess.check_call(
        ["rsync", "-rv", "--ignore-existing", os.path.join(dist_dir, ""), fulltarget]
    )


def _find_pkgname(dist_dir):
    """ Find the package name by looking at .whl files """
    pkgname = None
    for f in os.listdir(dist_dir):
        if f.endswith(".whl"):
            new_pkgname = f.split("-")[0].replace("_", "-")
            if pkgname and new_pkgname != pkgname:
                raise RuntimeError(f"Multiple packages names in {dist_dir}")
            pkgname = new_pkgname
    if not pkgname:
        raise RuntimeError(f"Package name not found in {dist_dir}")
    return pkgname
