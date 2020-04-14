# Copyright (c) ACSONE SA/NV 2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import pytest

from oca_github_bot.commands import (
    InvalidCommandError,
    InvalidOptionsError,
    OptionsError,
    RequiredOptionError,
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
                /ocabot merge nobump, please
                /ocabot merge  minor, please
                /ocabot merge minor, please
                /ocabot merge nobump.
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
        ("merge", ["nobump"]),
        ("merge", ["minor"]),
        ("merge", ["minor"]),
        ("merge", ["nobump"]),
        ("merge", ["patch"]),
        ("merge", ["minor"]),
    ]


def test_parse_command_2():
    cmds = list(
        parse_commands(
            "Great contribution, thanks!\r\n\r\n"
            "/ocabot merge nobump\r\n\r\n"
            "Please forward port it to 12.0."
        )
    )
    assert [(cmd.name, cmd.options) for cmd in cmds] == [("merge", ["nobump"])]


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
    cmds = list(parse_commands("/ocabot merge nobump"))
    assert len(cmds) == 1
    assert cmds[0].name == "merge"
    assert cmds[0].bumpversion_mode == "nobump"
    with pytest.raises(RequiredOptionError):
        list(parse_commands("/ocabot merge"))
    with pytest.raises(InvalidOptionsError):
        list(parse_commands("/ocabot merge nobump brol"))
    with pytest.raises(OptionsError):
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
