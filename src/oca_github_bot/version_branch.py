# Copyright (c) ACSONE SA/NV 2018-2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

ODOO_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)$")
MERGE_BOT_BRANCH_RE = re.compile(
    r"ocabot-merge-"
    r"pr-(?P<pr>\d+)-"
    r"to-(?P<target_branch>\d+\.\d+)-"
    r"by-(?P<username>.+)-"
    r"bump-(?P<bumpversion>[a-z]+)"
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
    bumpversion = mo.group("bumpversion")
    if bumpversion == "no":
        bumpversion = None
    return (
        mo.group("pr"),
        mo.group("target_branch"),
        mo.group("username"),
        bumpversion,
    )


def make_merge_bot_branch(pr, target_branch, username, bumpversion):
    if not bumpversion:
        bumpversion = "no"
    return f"ocabot-merge-pr-{pr}-to-{target_branch}-by-{username}-bump-{bumpversion}"


def search_merge_bot_branch(text):
    mo = MERGE_BOT_BRANCH_RE.search(text)
    if mo:
        return mo.group(0)
