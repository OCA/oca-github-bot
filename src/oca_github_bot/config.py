# Copyright (c) ACSONE SA/NV 2018
# Distributed under the MIT License (http://opensource.org/licenses/MIT).

import os


HTTP_HOST = os.environ.get("HTTP_HOST")
HTTP_PORT = int(os.environ.get("HTTP_PORT") or "8080")

GITHUB_SECRET = os.environ.get("GITHUB_SECRET")
GITHUB_LOGIN = os.environ.get("GITHUB_LOGIN", "OCA-git-bot")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

ODOO_URL = os.environ.get("ODOO_URL", "https://odoo-community.org")
ODOO_DB = os.environ.get("ODOO_DB", "odoo_community_v11")
ODOO_LOGIN = os.environ.get("ODOO_LOGIN")
ODOO_PASSWORD = os.environ.get("ODOO_PASSWORD")

REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost")

SENTRY_DSN = "https://99fc59617eae4e1e98a3ef2d1a6a3f16@sentry.io/1281903"

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
