# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.version_branch import (
    is_main_branch_bot_branch,
    is_merge_bot_branch,
    is_protected_branch,
    is_supported_main_branch,
    make_merge_bot_branch,
    parse_merge_bot_branch,
    search_merge_bot_branch,
)

from .common import set_config


def test_is_main_branch_bot_branch():
    assert not is_main_branch_bot_branch("6.1")
    assert not is_main_branch_bot_branch("7.0")
    assert is_main_branch_bot_branch("8.0")
    assert is_main_branch_bot_branch("12.0")
    assert not is_main_branch_bot_branch("10.0-something")
    with set_config(MAIN_BRANCH_BOT_MIN_VERSION="10.0"):
        assert is_main_branch_bot_branch("10.0")
        assert is_main_branch_bot_branch("12.0")
        assert not is_main_branch_bot_branch("7.0")


def test_is_protected_branch():
    assert is_protected_branch("master")
    assert is_protected_branch("6.0")
    assert is_protected_branch("12.0")
    assert not is_protected_branch("10.0-something")


def test_is_merge_bot_branch():
    assert is_merge_bot_branch("12.0-ocabot-merge-pr-100-by-toto-bump-patch")
    assert not is_merge_bot_branch("12.0-cabot-merge-pr-a100-by-titi-bump-no")
    assert is_merge_bot_branch("master-ocabot-merge-pr-100-by-toto-bump-no")


def test_make_merge_bot_branch():
    assert (
        make_merge_bot_branch("100", "12.0", "toto", "patch")
        == "12.0-ocabot-merge-pr-100-by-toto-bump-patch"
    )


def test_parse_merge_bot_branch():
    assert parse_merge_bot_branch("12.0-ocabot-merge-pr-100-by-toto-bump-patch") == (
        "100",
        "12.0",
        "toto",
        "patch",
    )
    assert parse_merge_bot_branch("12.0-ocabot-merge-pr-100-by-toto-bump-no") == (
        "100",
        "12.0",
        "toto",
        "nobump",
    )


def test_merge_bot_branch_name():
    # ocabot-merge must not change, as other tools may depend on it.
    # The rest of the branch name must be considered opaque and fit for the bot
    # needs only.
    assert "ocabot-merge" in make_merge_bot_branch("100", "12.0", "toto", "patch")


def test_search_merge_bot_branch():
    text = "blah blah 12.0-ocabot-merge-pr-100-by-toto-bump-no more stuff"
    assert search_merge_bot_branch(text) == "12.0-ocabot-merge-pr-100-by-toto-bump-no"
    text = "blah blah more stuff"
    assert search_merge_bot_branch(text) is None


@pytest.mark.parametrize(
    ("branch_name", "min_version", "expected"),
    [
        ("8.0", None, True),
        ("8.0", "8.0", True),
        ("8.0", "9.0", False),
    ],
)
def test_is_supported_branch(branch_name, min_version, expected):
    assert is_supported_main_branch(branch_name, min_version) is expected
