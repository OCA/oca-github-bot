# Copyright (c) ACSONE SA/NV 2018-2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

ODOO_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)$")
MERGE_BOT_BRANCH_RE = re.compile(
    r"^ocabot-merge-pr-(?P<pr>\d+)-to-(?P<target_branch>\d+\.\d+)-by-(?P<username>.+)$"
)


def is_main_branch_bot_branch(branch_name):
    mo = ODOO_VERSION_RE.match(branch_name)
    if not mo:
        return False
    return int(mo.group("major")) >= 8


def is_protected_branch(branch_name):
    if branch_name == "master":
        return True
    return bool(ODOO_VERSION_RE.match(branch_name))


def is_merge_bot_branch(branch):
    return branch and bool(MERGE_BOT_BRANCH_RE.match(branch))


def parse_merge_bot_branch(branch):
    mo = MERGE_BOT_BRANCH_RE.match(branch)
    return mo.group("pr"), mo.group("target_branch"), mo.group("username")


def make_merge_bot_branch(pr, target_branch, username):
    return f"ocabot-merge-pr-{pr}-to-{target_branch}-by-{username}"
