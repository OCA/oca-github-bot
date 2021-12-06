# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

from . import config


def hide_secrets(s: str) -> str:
    # TODO do we want to hide other secrets ?
    return s.replace(config.GITHUB_TOKEN, "***")
