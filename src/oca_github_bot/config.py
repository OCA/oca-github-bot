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
GITHUB_ORG = os.environ.get("GITHUB_ORG", "OCA")
GIT_NAME = os.environ.get("GIT_NAME")
GIT_EMAIL = os.environ.get("GIT_EMAIL")

ODOO_URL = os.environ.get("ODOO_URL", "https://odoo-community.org")
ODOO_DB = os.environ.get("ODOO_DB", "odoo_community_v11")
ODOO_LOGIN = os.environ.get("ODOO_LOGIN")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD")

BROKER_URI = os.environ.get("BROKER_URI", os.environ.get("REDIS_URI", "redis://queue"))

SENTRY_DSN = os.environ.get("SENTRY_DSN")

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# coma separated list of task to run
# by default all configured tasks are run.
# defined tasks:
#  delete_branch,tag_approved,tag_ready_to_merge,gen_addons_table,gen_addons_readme,
#  gen_addons_icon,setuptools_odoo,merge_bot
BOT_TASKS = os.environ.get("BOT_TASKS", "all").split(",")

GITHUB_STATUS_IGNORED = [
    "ci/runbot",
    "codecov/project",
    "codecov/patch",
    "coverage/coveralls",
]
GITHUB_CHECK_SUITES_IGNORED = ["Codecov"]
