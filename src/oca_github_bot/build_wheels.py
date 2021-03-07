# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging
import os
import sys
import tempfile

from oca_github_bot.pypi import RsyncDistPublisher

from .manifest import addon_dirs_in, get_manifest, get_odoo_series_from_version
from .process import check_call

_logger = logging.getLogger(__name__)


def _bdist_wheel(setup_dir, dist_dir, python_tag=None):
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
        ]
        if python_tag:
            cmd.extend(["--python-tag", python_tag])
        check_call(cmd, cwd=setup_dir)
        _check_wheels(dist_dir)


def _build_and_check_wheel(addon_dir, dist_dir):
    manifest = get_manifest(addon_dir)
    if not manifest.get("installable", True):
        return False
    series = get_odoo_series_from_version(manifest.get("version", ""))
    if series < (8, 0):
        return False
    addon_name = os.path.basename(addon_dir)
    setup_dir = os.path.join(addon_dir, "..", "setup", addon_name)
    setup_file = os.path.join(setup_dir, "setup.py")
    if not os.path.isfile(setup_file):
        return False
    _bdist_wheel(setup_dir, dist_dir, python_tag="py2" if series < (11, 0) else "py3")
    return True


def _check_wheels(dist_dir):
    wheels = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
    check_call(["twine", "check"] + wheels, cwd=dist_dir)


def build_and_check_wheel(addon_dir):
    with tempfile.TemporaryDirectory() as dist_dir:
        _build_and_check_wheel(addon_dir, dist_dir)


def build_and_publish_wheel(addon_dir, simple_index_root, dry_run=False):
    with tempfile.TemporaryDirectory() as dist_dir:
        if _build_and_check_wheel(addon_dir, dist_dir):
            _publish_dist_dir_to_simple_index(dist_dir, simple_index_root, dry_run)


def build_and_publish_wheels(addons_dir, simple_index_root, dry_run=False):
    for addon_dir in addon_dirs_in(addons_dir, installable_only=True):
        build_and_publish_wheel(addon_dir, simple_index_root, dry_run)


def build_and_publish_metapackage_wheel(
    addons_dir, simple_index_root, series, dry_run=False
):
    setup_dir = os.path.join(addons_dir, "setup", "_metapackage")
    setup_file = os.path.join(setup_dir, "setup.py")
    if not os.path.isfile(setup_file):
        return
    with tempfile.TemporaryDirectory() as dist_dir:
        _bdist_wheel(
            setup_dir, dist_dir, python_tag="py2" if series < (11, 0) else "py3"
        )
        _publish_dist_dir_to_simple_index(dist_dir, simple_index_root, dry_run)


def _publish_dist_dir_to_simple_index(dist_dir, simple_index_root, dry_run=False):
    RsyncDistPublisher(simple_index_root, dry_run).publish(dist_dir)
