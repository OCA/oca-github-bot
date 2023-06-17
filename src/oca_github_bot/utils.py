# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re
import shlex
import time
from typing import Sequence

from . import config


def hide_secrets(s: str) -> str:
    # TODO do we want to hide other secrets ?
    return s.replace(config.GITHUB_TOKEN, "***")


def retry_on_exception(
    func, exception_regex: str, max_retries: int = 3, sleep_time: float = 5.0
):
    """Retry a function call if it raises an exception matching a regex."""
    counter = 0
    while True:
        try:
            return func()
        except Exception as e:
            if not re.search(exception_regex, str(e)):
                raise
            if counter >= max_retries:
                raise
            counter += 1
            time.sleep(sleep_time)


def cmd_to_str(cmd: Sequence[str]) -> str:
    return shlex.join(str(c) for c in cmd)
