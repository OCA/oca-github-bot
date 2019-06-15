# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from oca_github_bot.version_branch import (
    is_main_branch_bot_branch,
    is_merge_bot_branch,
    is_protected_branch,
    make_merge_bot_branch,
    parse_merge_bot_branch,
)


def test_is_main_branch_bot_branch():
    assert not is_main_branch_bot_branch("6.1")
    assert not is_main_branch_bot_branch("7.0")
    assert is_main_branch_bot_branch("8.0")
    assert is_main_branch_bot_branch("12.0")
    assert not is_main_branch_bot_branch("10.0-something")


def test_is_protected_branch():
    assert is_protected_branch("master")
    assert is_protected_branch("6.0")
    assert is_protected_branch("12.0")
    assert not is_protected_branch("10.0-something")


def test_is_merge_bot_branch():
    assert is_merge_bot_branch("ocabot-merge-pr-100-to-12.0-by-toto-bump-patch")
    assert not is_merge_bot_branch("cabot-merge-pr-a100-to-12.0-by-titi-bump-no")
    assert not is_merge_bot_branch("ocabot-merge-pr-100-to-something-by-toto-bump-no")


def test_make_merge_bot_branch():
    assert (
        make_merge_bot_branch("100", "12.0", "toto", "patch")
        == "ocabot-merge-pr-100-to-12.0-by-toto-bump-patch"
    )


def test_parse_merge_bot_branch():
    assert parse_merge_bot_branch("ocabot-merge-pr-100-to-12.0-by-toto-bump-patch") == (
        "100",
        "12.0",
        "toto",
        "patch",
    )
    assert parse_merge_bot_branch("ocabot-merge-pr-100-to-12.0-by-toto-bump-no") == (
        "100",
        "12.0",
        "toto",
        None,
    )
