# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from pathlib import Path

import pytest

from oca_github_bot.utils import cmd_to_str, hide_secrets, retry_on_exception

from .common import set_config


def test_hide_secrets_nothing_to_hide():
    with set_config(GITHUB_TOKEN="token"):
        assert "nothing to hide" == hide_secrets("nothing to hide")


def test_hide_secrets_github_token():
    with set_config(GITHUB_TOKEN="token"):
        assert "git push https://***@github.com" == hide_secrets(
            "git push https://token@github.com"
        )


def test_retry_on_exception_raise_match():
    counter = 0

    def func_that_raises():
        nonlocal counter
        counter += 1
        raise Exception("something")

    max_retries = 2
    sleep_time = 0.1

    try:
        retry_on_exception(
            func_that_raises,
            "something",
            max_retries=max_retries,
            sleep_time=sleep_time,
        )
    except Exception as e:
        assert "something" in str(e)
        assert counter == max_retries + 1


def test_retry_on_exception_raise_no_match():
    counter = 0

    def func_that_raises():
        nonlocal counter
        counter += 1
        raise Exception("somestuff")

    max_retries = 2
    sleep_time = 0.1

    try:
        retry_on_exception(
            func_that_raises,
            "something",
            max_retries=max_retries,
            sleep_time=sleep_time,
        )
    except Exception as e:
        assert "somestuff" in str(e)
        assert counter == 1


def test_retry_on_exception_no_raise():
    counter = 0

    def func_that_raises():
        nonlocal counter
        counter += 1
        return True

    max_retries = 2
    sleep_time = 0.1

    retry_on_exception(
        func_that_raises,
        "something",
        max_retries=max_retries,
        sleep_time=sleep_time,
    )
    assert counter == 1


@pytest.mark.parametrize(
    "cmd, expected",
    [
        (["a", "b"], "a b"),
        (["ls", Path("./user name")], "ls 'user name'"),
        (["a", "b c"], "a 'b c'"),
    ],
)
def test_cmd_to_str(cmd, expected):
    assert cmd_to_str(cmd) == expected
