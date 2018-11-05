# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

ODOO_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)$")


def is_main_branch_bot_branch(branch_name):
    mo = ODOO_VERSION_RE.match(branch_name)
    if not mo:
        return False
    return int(mo.group("major")) >= 8


def is_protected_branch(branch_name):
    if branch_name == "master":
        return True
    return bool(ODOO_VERSION_RE.match(branch_name))
