# Copyright (c) ACSONE SA/NV 2021
from io import StringIO
from pathlib import PosixPath
from typing import Iterator, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from lxml import etree


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
