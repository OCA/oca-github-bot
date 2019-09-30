# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import logging
import os
from functools import wraps

_logger = logging.getLogger("oca_gihub_bot.tasks")


def switchable(switch_name=None):
    def wrap(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            sname = switch_name
            if switch_name is None:
                sname = func.__name__

            if BOT_TASKS != ["all"] and sname not in BOT_TASKS:
                _logger.debug("Method %s skipped (Disabled by config)", sname)
                return
            return func(*args, **kwargs)

        return func_wrapper

    return wrap


HTTP_HOST = os.environ.get("HTTP_HOST")
HTTP_PORT = int(os.environ.get("HTTP_PORT") or "8080")

GITHUB_SECRET = os.environ.get("GITHUB_SECRET")
GITHUB_LOGIN = os.environ.get("GITHUB_LOGIN")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_ORG = os.environ.get("GITHUB_ORG")
GIT_NAME = os.environ.get("GIT_NAME")
GIT_EMAIL = os.environ.get("GIT_EMAIL")

ODOO_URL = os.environ.get("ODOO_URL")
ODOO_DB = os.environ.get("ODOO_DB")
ODOO_LOGIN = os.environ.get("ODOO_LOGIN")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD")

BROKER_URI = os.environ.get("BROKER_URI", os.environ.get("REDIS_URI", "redis://queue"))

SENTRY_DSN = os.environ.get("SENTRY_DSN")

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# Coma separated list of task to run
# By default all configured tasks are run.
# Available tasks:
#  delete_branch,tag_approved,tag_ready_to_merge,gen_addons_table,
#  gen_addons_readme,gen_addons_icon,setuptools_odoo,merge_bot,tag_needs_review
BOT_TASKS = os.environ.get("BOT_TASKS", "all").split(",")

GITHUB_STATUS_IGNORED = [
    "ci/runbot",
    "codecov/project",
    "codecov/patch",
    "coverage/coveralls",
]
GITHUB_CHECK_SUITES_IGNORED = ["Codecov"]
MERGE_BOT_INTRO_MESSAGES = [
    "On my way to merge this fine PR!",
    "This PR looks fantastic, let's merge it!",
    "Hey, thanks for contributing! Proceeding to merge this for you.",
    "What a great day to merge this nice PR. Let's do it!",
]

SIMPLE_INDEX_ROOT = os.environ.get("SIMPLE_INDEX_ROOT")

CLABOT_CACHE = os.environ.get("CLABOT_CACHE", "clabot_cache.db")


CLA_KO_MESSAGE = """Hey @{pull_user},
thank you for your Pull Request and contribution to the OCA.

It looks like some users haven't signed our **C**ontributor **L**icense
**A**greement, yet.

1. You can get our full Contributor License Agreement (CLA) here:
http://odoo-community.org/page/website.cla

2. Your company (with Enterprise CLA) or every users listed below (with
Individual CLA) should complete and sign it

3. Do not forget to include your complete data (company and/or personal) and
the covered Github login(s).

4. Please scan the document(s) and send them back to cla@odoo-community.org,

Here is a list of the users :
{users_ko}
Appreciation of efforts,

--
OCA CLAbot"""

CLA_OK_MESSAGE = """Hey @{pull_user},

We acknowledge that the following users have signed our **C**ontributor
**L**icense **A**greement: {users_ok}

Appreciation of efforts,

--
OCA CLAbot"""
