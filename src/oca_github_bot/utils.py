# Copyright (c) ACSONE SA/NV 2021
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import hashlib
import re
import shlex
import time
from collections.abc import Sequence

from . import config

# Max size allowed by github for label name
_MAX_LABEL_SIZE = 50
# Size of the hash, added at the end of the label name
# if module name is too long
_HASH_SIZE = 5


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


def compute_module_label_name(module_name: str) -> str:
    """To avoid error if label name is too long
    we cut big label, and finish by a hash of the module name.
    (The full module name will be present in the description).
    Short module name exemple :
    - module : 'web_responsive'
    - label : 'mod:web_responsive'
    Long module name exemple :
    - module : 'account_invoice_supplierinfo_update_triple_discount'
    - label : 'mod:account_invoice_supplierinfo_update_trip bf3f3'
    """
    label_name = f"mod:{module_name}"
    if len(label_name) > _MAX_LABEL_SIZE:
        module_hash = hashlib.sha256(bytes(module_name, "utf-8")).hexdigest()
        label_name = (
            f"{label_name[: (_MAX_LABEL_SIZE - (_HASH_SIZE + 1))]}"
            f" {module_hash[:_HASH_SIZE]}"
        )
    return label_name
