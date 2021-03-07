# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).
import pytest

from oca_github_bot.pypi import exists_on_index


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
