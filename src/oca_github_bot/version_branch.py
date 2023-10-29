# Copyright (c) ACSONE SA/NV 2018-2019
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import re

from packaging import version

from . import config

ODOO_VERSION_RE = re.compile(r"^(?P<major>\d+)\.(?P<minor>\d+)$")
MERGE_BOT_BRANCH_RE = re.compile(
    r"(?P<target_branch>\S+)"
    r"-ocabot-merge"
    r"-pr-(?P<pr>\d+)"
    r"-by-(?P<username>\S+)"
    r"-bump-(?P<bumpversion_mode>(no|patch|minor|major))"
)


def is_supported_main_branch(branch_name, min_version=None):
    if not ODOO_VERSION_RE.match(branch_name):
        return False
    branch_version = version.parse(branch_name)
    if min_version and branch_version < version.parse(min_version):
        return False
    return True


def is_main_branch_bot_branch(branch_name):
    return is_supported_main_branch(
        branch_name, min_version=config.MAIN_BRANCH_BOT_MIN_VERSION
    )


def is_protected_branch(branch_name):
    if branch_name == "master":
        return True
    return bool(ODOO_VERSION_RE.match(branch_name))


def is_merge_bot_branch(branch):
    return branch and bool(MERGE_BOT_BRANCH_RE.match(branch))


def parse_merge_bot_branch(branch):
    mo = MERGE_BOT_BRANCH_RE.match(branch)
    bumpversion_mode = mo.group("bumpversion_mode")
    if bumpversion_mode == "no":
        bumpversion_mode = "nobump"
    return (
        mo.group("pr"),
        mo.group("target_branch"),
        mo.group("username"),
        bumpversion_mode,
    )


def make_merge_bot_branch(pr, target_branch, username, bumpversion_mode):
    if not bumpversion_mode:
        bumpversion_mode = "no"
    return f"{target_branch}-ocabot-merge-pr-{pr}-by-{username}-bump-{bumpversion_mode}"


def search_merge_bot_branch(text):
    mo = MERGE_BOT_BRANCH_RE.search(text)
    if mo:
        return mo.group(0)
