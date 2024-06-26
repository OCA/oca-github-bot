# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).
import tempfile
from pathlib import Path

import pytest

from oca_github_bot.pypi import TwineDistPublisher, exists_on_index


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("pip-21.0.1-py3-none-any.whl", True),
        ("pip-20.4-py3-none-any.whl", False),
        ("not_a_pkg-1.0-py3-none-any.whl", False),
    ],
)
@pytest.mark.vcr()
def test_exists_on_index(filename, expected):
    assert exists_on_index("https://pypi.org/simple/", filename) is expected


@pytest.mark.vcr()
def test_twine_publisher_file_exists():
    """Basic test for the twine publisher.

    This test succeeds despite the bogus upload URL, because the file exists,
    so no upload is attempted.
    """
    publisher = TwineDistPublisher(
        "https://pypi.org/simple/", "https://pypi.org/legacy", "username", "password"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "odoo9_addon_mis_builder-9.0.3.5.0-py2-none-any.whl"
        filepath.touch()
        publisher.publish(tmpdir, dry_run=False)
