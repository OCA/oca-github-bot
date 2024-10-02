# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import atexit
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Tuple, Union

from .config import WHEEL_BUILD_TOOLS
from .manifest import addon_dirs_in, get_manifest, get_odoo_series_from_version
from .process import check_call
from .pypi import DistPublisher

_logger = logging.getLogger(__name__)


class Builder:
    _builder: Union["Builder", None] = None

    @classmethod
    def get(cls) -> "Builder":
        if cls._builder is None:
            cls._builder = cls()
        return cls._builder

    def __init__(self):
        self.env_dir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, self.env_dir)
        self.env_python = Path(self.env_dir) / "bin" / "python"
        check_call(
            [sys.executable, "-m", "venv", self.env_dir],
            cwd=".",
        )
        check_call(
            [self.env_python, "-m", "pip", "install", "--upgrade"] + WHEEL_BUILD_TOOLS,
            cwd=".",
        )
        check_call(
            [self.env_python, "-m", "pip", "check"],
            cwd=".",
        )

    def build_wheel(self, project_dir: Path, dist_dir: str) -> None:
        with tempfile.TemporaryDirectory() as empty_dir:
            # Start build from an empty directory, to avoid accidentally importing
            # python files from the addon root directory during the build process.
            check_call(
                [
                    self.env_python,
                    "-P",
                    "-m",
                    "build",
                    "--wheel",
                    "--outdir",
                    dist_dir,
                    "--no-isolation",
                    project_dir,
                ],
                cwd=empty_dir,
            )
        self._check_wheels(dist_dir)
        return True

    def build_wheel_legacy(
        self, project_dir: Path, dist_dir: str, python_tag: Union[str, None] = None
    ) -> None:
        with tempfile.TemporaryDirectory() as bdist_dir:
            cmd = [
                self.env_python,
                "setup.py",
                "bdist_wheel",
                "--dist-dir",
                dist_dir,
                "--bdist-dir",
                bdist_dir,
            ]
            if python_tag:
                cmd.extend(["--python-tag", python_tag])
            check_call(cmd, cwd=project_dir)
        self._check_wheels(dist_dir)
        return True

    def _check_wheels(self, dist_dir: Path) -> None:
        wheels = [f for f in os.listdir(dist_dir) if f.endswith(".whl")]
        check_call(["twine", "check"] + wheels, cwd=dist_dir)

    def build_addon_wheel(self, addon_dir: Path, dist_dir: str) -> None:
        manifest = get_manifest(addon_dir)
        if not manifest.get("installable", True):
            return False

        series = get_odoo_series_from_version(manifest.get("version", ""))

        if series >= (12, 0) and (addon_dir / "pyproject.toml").is_file():
            return self.build_wheel(addon_dir, dist_dir)

        setup_py_dir = addon_dir / ".." / "setup" / addon_dir.name
        if series >= (8, 0) and (setup_py_dir / "setup.py").is_file():
            return self.build_wheel_legacy(
                setup_py_dir, dist_dir, python_tag="py2" if series < (11, 0) else "py3"
            )

        return False


def build_and_check_wheel(addon_dir: str):
    with tempfile.TemporaryDirectory() as dist_dir:
        Builder.get().build_addon_wheel(Path(addon_dir), dist_dir)


def build_and_publish_wheel(
    addon_dir: str, dist_publisher: DistPublisher, dry_run: bool
):
    with tempfile.TemporaryDirectory() as dist_dir:
        if Builder.get().build_addon_wheel(Path(addon_dir), dist_dir):
            dist_publisher.publish(dist_dir, dry_run)


def build_and_publish_wheels(
    addons_dir: str, dist_publisher: DistPublisher, dry_run: bool
):
    for addon_dir in addon_dirs_in(addons_dir, installable_only=True):
        with tempfile.TemporaryDirectory() as dist_dir:
            if Builder.get().build_addon_wheel(Path(addon_dir), dist_dir):
                dist_publisher.publish(dist_dir, dry_run)


def build_and_publish_metapackage_wheel(
    addons_dir: str,
    dist_publisher: DistPublisher,
    series: Tuple[int, int],
    dry_run: bool,
):
    setup_dir = Path(addons_dir) / "setup" / "_metapackage"
    setup_file = setup_dir / "setup.py"
    if not setup_file.is_file():
        return
    with tempfile.TemporaryDirectory() as dist_dir:
        # Workaround for recent setuptools not generating long_description
        # anymore (before it was generating UNKNOWN), and a long_description
        # is required by twine check. We could fix setuptools-odoo-makedefault
        # but that would not backfill the legacy. So here we are...
        if "long_description" not in setup_file.read_text():
            setup_dir.joinpath("setup.cfg").write_text(
                "[metadata]\nlong_description = UNKNOWN\n"
            )
        if Builder.get().build_wheel_legacy(
            setup_dir, dist_dir, python_tag="py2" if series < (11, 0) else "py3"
        ):
            dist_publisher.publish(dist_dir, dry_run)
