# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from oca_github_bot.utils import hide_secrets

from .common import set_config


def test_hide_secrets_nothing_to_hide():
    with set_config(GITHUB_TOKEN="token"):
        assert "nothing to hide" == hide_secrets("nothing to hide")


def test_hide_secrets_github_token():
    with set_config(GITHUB_TOKEN="token"):
        assert "git push https://***@github.com" == hide_secrets(
            "git push https://token@github.com"
        )
