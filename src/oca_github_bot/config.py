# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os

import tools.config as oca_m_t_config

HTTP_HOST = os.environ.get("HTTP_HOST")
HTTP_PORT = int(os.environ.get("HTTP_PORT") or "8080")

GITHUB_SECRET = os.environ.get("GITHUB_SECRET")
GITHUB_LOGIN = os.environ.get("GITHUB_LOGIN", "OCA-git-bot")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GIT_NAME = os.environ.get("GIT_NAME", GITHUB_LOGIN)
GIT_EMAIL = os.environ.get("GIT_EMAIL", "oca-git-bot@odoo-community.org")

ODOO_URL = os.environ.get("ODOO_URL", "https://odoo-community.org")
ODOO_DB = os.environ.get("ODOO_DB", "odoo_community_v11")
ODOO_LOGIN = os.environ.get("ODOO_LOGIN")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD")

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost")

SENTRY_DSN = os.environ.get("SENTRY_DSN")

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

MAIN_BRANCH_BOT_EXCLUDED_REPOS = oca_m_t_config.NOT_ADDONS
MAIN_BRANCH_BOT_BRANCHES = ("8.0", "9.0", "10.0", "11.0", "12.0")
PROTECTED_BRANCHES = oca_m_t_config.MAIN_BRANCHES + ("master",)
