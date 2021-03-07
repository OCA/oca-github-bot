# Copyright (c) ACSONE SA/NV 2021
"""Utilities to work with PEP 503 package indexes."""
import logging
import os
from io import StringIO
from pathlib import PosixPath
from typing import Iterator, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from lxml import etree

from .process import check_call

_logger = logging.getLogger(__name__)


def files_on_index(
    index_url: str, project_name: str
) -> Iterator[Tuple[str, Optional[Tuple[str, str]]]]:
    """Iterate files available on an index for a given project name."""
    project_name = project_name.replace("_", "-")
    base_url = urljoin(index_url, project_name + "/")

    r = requests.get(base_url)
    if r.status_code == 404:
        # project not found on this index
        return
    r.raise_for_status()
    parser = etree.HTMLParser()
    tree = etree.parse(StringIO(r.text), parser)
    for a in tree.iterfind("//a"):
        parsed_url = urlparse(a.get("href"))
        p = PosixPath(parsed_url.path)
        if parsed_url.fragment:
            hash_type, hash_value = parsed_url.fragment.split("=", 2)[:2]
            yield p.name, (hash_type, hash_value)
        else:
            yield p.name, None


def exists_on_index(index_url: str, filename: str) -> bool:
    """Check if a distribution exists on a package index."""
    project_name = filename.split("-", 1)[0]
    for filename_on_index, _ in files_on_index(index_url, project_name):
        if filename_on_index == filename:
            return True
    return False


class DistPublisher:
    def publish(self, dist_dir: str) -> None:
        raise NotImplementedError()


class MultiDistPublisher(DistPublisher):
    def __init__(self):
        self._dist_publishers = []

    def add(self, dist_publisher: DistPublisher) -> None:
        self._dist_publishers.append(dist_publisher)

    def publish(self, dist_dir: str) -> None:
        for dist_publisher in self._dist_publishers:
            dist_publisher.publish(dist_dir)


class RsyncDistPublisher(DistPublisher):
    def __init__(self, rsync_target, dry_run):
        self._rsync_target = rsync_target
        self._dry_run = dry_run

    def publish(self, dist_dir: str) -> None:
        pkgname = _find_pkgname_in_dist_dir(dist_dir)
        # --ignore-existing: never overwrite an existing package
        # os.path.join: make sure directory names end with /
        cmd = [
            "rsync",
            "-rv",
            "--ignore-existing",
            "--no-perms",
            "--chmod=ugo=rwX",
            os.path.join(dist_dir, ""),
            os.path.join(self._rsync_target, pkgname, ""),
        ]
        if self._dry_run:
            _logger.info("DRY-RUN" + " ".join(cmd))
        else:
            _logger.info(" ".join(cmd))
            check_call(cmd, cwd=".")


def _find_pkgname_in_dist_dir(dist_dir: str) -> str:
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
