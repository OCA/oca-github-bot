# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest
from oca_github_bot.commands import (
    InvalidCommandError,
    InvalidOptionsError,
    parse_commands,
)


def test_parse_command_not_a_command():
    with pytest.raises(InvalidCommandError):
        list(parse_commands("/ocabot not_a_command"))


def test_parse_command_multi():
    cmds = list(
        parse_commands(
            """
                ...
                /ocabot merge major
                /ocabot   merge   patch
                /ocabot merge patch
                ...
            """
        )
    )
    assert len(cmds) == 3


def test_parse_command_merge():
    cmds = list(parse_commands("/ocabot merge major"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion == "major"
    cmds = list(parse_commands("/ocabot merge minor"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion == "minor"
    cmds = list(parse_commands("/ocabot merge patch"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion == "patch"
    cmds = list(parse_commands("/ocabot merge"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion is None
    with pytest.raises(InvalidOptionsError):
        list(parse_commands("/ocabot merge brol"))
