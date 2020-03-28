# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from oca_github_bot import config


@config.switchable()
def ping_method(msg):
    return msg


@config.switchable("ping_method_switch")
def ping_method_2(msg):
    return msg


def test_switchable_method():
    assert config.BOT_TASKS == ["all"]
    assert ping_method("test") == "test"
    assert ping_method_2("test") == "test"
    config.BOT_TASKS_DISABLED = ["ping_method"]
    assert ping_method("test") is None
    assert ping_method_2("test") == "test"
    config.BOT_TASKS_DISABLED = []
    config.BOT_TASKS = []
    assert ping_method("test") is None
    assert ping_method_2("test") is None
    config.BOT_TASKS = ["ping_method"]
    assert ping_method("test") == "test"
    assert ping_method_2("test") is None
    config.BOT_TASKS = ["ping_method", "ping_method_switch"]
    assert ping_method("test") == "test"
    assert ping_method_2("test") == "test"
