# Copyright (c) ACSONE SA/NV 2019
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
                /ocabot merge, please
                /ocabot merge  minor, please
                /ocabot merge minor, please
                /ocabot merge.
                /ocabot merge patch. blah
                /ocabot merge minor # ignored
                ...
            """
        )
    )
    assert [(cmd.name, cmd.options) for cmd in cmds] == [
        ("merge", ["major"]),
        ("merge", ["patch"]),
        ("merge", ["patch"]),
        ("merge", []),
        ("merge", ["minor"]),
        ("merge", ["minor"]),
        ("merge", []),
        ("merge", ["patch"]),
        ("merge", ["minor"]),
    ]


def test_parse_command_2():
    cmds = list(
        parse_commands(
            "Great contribution, thanks!\r\n\r\n"
            "/ocabot merge\r\n\r\n"
            "Please forward port it to 12.0."
        )
    )
    assert [(cmd.name, cmd.options) for cmd in cmds] == [("merge", [])]


def test_parse_command_merge():
    cmds = list(parse_commands("/ocabot merge major"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion_mode == "major"
    cmds = list(parse_commands("/ocabot merge minor"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion_mode == "minor"
    cmds = list(parse_commands("/ocabot merge patch"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion_mode == "patch"
    cmds = list(parse_commands("/ocabot merge"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion_mode is None
    with pytest.raises(InvalidOptionsError):
        list(parse_commands("/ocabot merge brol"))


def test_parse_command_comment():
    body = """
> {merge_command}
> Some comment {merge_command}
>> Double comment! {merge_command}
This is the one {merge_command} patch
    """.format(
        merge_command="/ocabot merge"
    )
    command = list(parse_commands(body))
    assert len(command) == 1
    command = command[0]
    assert command.name == "merge"
    assert command.bumpversion_mode == "patch"
