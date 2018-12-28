# Copyright (c) Camptocamp 2018
# Copyright (c) Akretion 2014
import json
import logging
import re
import sqlite3

import requests  # FIXME remove
from requests.auth import HTTPBasicAuth  # FIXME remove

from .. import config
from ..odoo_client import login
from ..queue import getLogger, task

_logger = logging.getLogger(__name__)
RE_WEBLATE_COMMIT_MSG = r"""^Translated using Weblate.*
Translate-URL: https://translation\.odoo-community\.org/"""


_logger = getLogger(__name__)


@task()
def check_cla(event, gh):
    checker = CLACheck(event, gh)
    return checker.check_cla()


class CLACheck:
    def __init__(self, event, gh):
        self.event = event
        self.gh = gh
        self.db = sqlite3.connect(config.CLABOT_CACHE)

    SQL_SELECT_MISS_CACHE_USERS = """
    SELECT login,pull_request FROM login_cla_ko WHERE login IN (%s)
    """
    SQL_DELETE_MISS_CACHE = """
    DELETE FROM login_cla_ko WHERE login IN (%s)
    """
    SQL_INSERT_HIT_CACHE = """
    INSERT OR IGNORE INTO login_cla_ok(login, date_cla_ok)
    VALUES(?, CURRENT_DATE)
    """
    SQL_SELECT_MISS_CACHE_PR = """
    SELECT login,pull_request FROM login_cla_ko WHERE pull_request=?
    """
    SQL_INSERT_MISS_CACHE = """
    INSERT OR IGNORE INTO login_cla_ko(login, date_cla_ko, pull_request)
    VALUES(?, CURRENT_DATE, ?)
    """
    SQL_SELECT_MISS_CACHE_NOLOGIN_PR = """
    SELECT email,pull_request FROM nologin_cla_ko WHERE pull_request=?
    """

    def _update_cache_users_no_sign(self, users_no_sign):
        login_pr = [(login, self.pr_key) for login in users_no_sign]
        self.db.executemany(self.SQL_INSERT_MISS_CACHE, login_pr)

    @property
    def owner(self):
        return self.event["repository"]["owner"]["login"]

    @property
    def repo(self):
        return self.event["repository"]["name"]

    @property
    def number(self):
        return self.event["number"]

    @property
    def pull_user(self):
        return self.event["pull_request"]["user"]["login"]

    # FIXME: make async
    def _get_pr_commits(self):
        path = "/repos/{owner}/{repo}/pulls/{number}/commits".format(
            owner=self.owner, repo=self.repo, number=self.number
        )
        params = {"per_page": 250}  # maximum allowed
        res = requests.get(  # FIXME this must use the framework
            config.GITHUB_URL + path,
            params=params,
            auth=HTTPBasicAuth(config.GITHUB_LOGIN, config.GITHUB_PASSWORD),
        )
        commits = res.json()
        return commits

    # FIXME make async
    def _get_commit_users(self):
        commits = self._get_pr_commits()
        users_login = set()
        users_no_login = set()
        for commit in commits:
            u_login, u_no_login = get_commit_author(commit)
            users_login |= u_login
            users_no_login |= u_no_login
        return users_login, users_no_login

    @property
    def pr_key(self):
        pr_key = "{pull_user}/{owner}/{repo}/{number}".format(
            pull_user=self.pull_user,
            owner=self.owner,
            repo=self.repo,
            number=self.number,
        )
        return pr_key

    # FIXME make async
    def post_notification(self, path, message):

        if config.DEBUG:
            _logger.debug("notification:path:" + path)
            _logger.debug("notification:message:" + message)
            return

        data = {"body": message}
        requests.post(
            config.GITHUB_URL + path,
            data=json.dumps(data),
            auth=HTTPBasicAuth(config.GITHUB_LOGIN, config.GITHUB_PASSWORD),
        )

    # FIXME make async
    def check_cla(self):
        event = self.event
        # method "handle_payload" in clabot.py
        if event["action"] not in ("opened", "synchronize"):
            return True

        users_login, users_no_login = self._get_commit_users()

        users_info = self._check_cla_of_users(list(users_login))
        users_sign_notify = users_info[0]
        users_no_sign = users_info[1]
        users_oca_no_sign = users_info[2]
        send_miss_notification = users_info[3]
        # remove no_login users which have already been notified on this PR
        users_no_login = self._cleanup_users_no_login(users_no_login)

        if users_no_sign or users_oca_no_sign or users_no_login:

            users_ko = ""
            for user in users_oca_no_sign:
                users_ko += "+ @%s\n" % user
            for user in users_no_sign:
                users_ko += "+ @%s (login unknown in OCA database)\n" % user
            for user, email in users_no_login:
                users_ko += "+ {} <{}> (no github login found)\n".format(user, email)

            if send_miss_notification:
                path = "/repos/{owner}/{repo}/issues/{number}/comments"
                path = path.format(owner=self.owner, repo=self.repo, number=self.number)
                message = config["cla_ko_message"].format(
                    pull_user=self.pull_user, users_ko=users_ko
                )
                self.post_notification(path, message)

                _logger.info(
                    "PR: %s/%s#%s: no CLA for [%s], "
                    "unknown OCA login for [%s], "
                    "no github login for [%s]",
                    self.owner,
                    self.repo,
                    self.number,
                    ", ".join(users_oca_no_sign) or "",
                    ", ".join(users_no_sign) or "",
                    ", ".join(
                        "{} <{}>".format(name, email) for name, email in users_no_login
                    )
                    if users_no_login
                    else "",
                )

            else:
                _logger.info(
                    "PR: %s/%s#%s: CLA notification already sent",
                    self.owner,
                    self.repo,
                    self.number,
                )

        else:
            _logger.info("PR %s/%s#%s: CLA OK", self.owner, self.repo, self.number)

        if users_sign_notify:
            sign_notifications = {}
            for user_sign, pr in users_sign_notify:
                sign_notifications.setdefault(pr, []).append(user_sign)

            for pr, users_sign in sign_notifications.items():
                pull_user, owner, repo, number = pr.split("/")
                path = "/repos/{owner}/{repo}/issues/{number}/comments"
                path = path.format(owner=owner, repo=repo, number=number)

                users_ok = ""
                for user in users_sign:
                    users_ok += "+ @%s\n" % user

                message = config.cla_ok_message.format(
                    pull_user=pull_user, users_ok=users_ok
                )
                self.post_notification(path, message)
                _logger.info(
                    "PR %s/%s#%s: CLA OK for [%s]",
                    self.owner,
                    self.repo,
                    self.number,
                    ", ".join(users_sign),
                )

        return True

    def _check_cla_of_users(self, users):

        send_miss_notification = True
        users_no_sign = []
        users_oca_no_sign = []
        users_sign = []
        users_sign_notify = []
        sql_select_hit_cache = """
        SELECT login FROM login_cla_ok WHERE login IN (%s)
        """

        placeholders = ",".join("?" * len(users))
        res = self.db.execute(sql_select_hit_cache % placeholders, users)
        users_cached = [r[0] for r in res.fetchall()]
        users = list(set(users) - set(users_cached))

        with login() as client:
            for user in users:
                condition = [("github_login", "=", user)]
                if not client.search("res.partner", condition):
                    users_no_sign.append(user)
                    continue

                condition.extend(
                    [
                        "|",
                        ("category_id", "=", "ICLA"),
                        ("parent_id.category_id", "=", "ECLA"),
                    ]
                )
                if not client.search("res.partner", condition):
                    users_oca_no_sign.append(user)
                else:
                    users_sign.append(user)

        users_sign_notify = self._update_cache_cla_signed(users_sign)
        if users_no_sign or users_oca_no_sign:

            users = users_no_sign + users_oca_no_sign
            placeholders = ",".join("?" * len(users))
            res = self.db.execute(
                self.SQL_SELECT_MISS_CACHE_USERS % placeholders, users
            )
            users_no_sign_hit = [r[0] for r in res.fetchall()]
            users_oca_no_sign = list(set(users_oca_no_sign) - set(users_no_sign_hit))
            users_no_sign = list(set(users_no_sign) - set(users_no_sign_hit))

            # Do not send again a notification
            res = self.db.execute(self.SQL_SELECT_MISS_CACHE_PR, (self.pr_key,))
            send_miss_notification = not res.fetchone()

            self._update_cache_users_no_sign(users_no_sign)

        self.db.commit()
        return (
            users_sign_notify,
            users_no_sign,
            users_oca_no_sign,
            send_miss_notification,
        )

    def _update_cache_cla_signed(self, users_signed):
        if not users_signed:
            return []
        placeholders = ",".join("?" * len(users_signed))
        res = self.db.execute(
            self.SQL_SELECT_MISS_CACHE_USERS % placeholders, users_signed
        )
        if res:
            users_sign_notify = res.fetchall()
            self.db.execute(self.SQL_DELETE_MISS_CACHE % placeholders, users_signed)
        self.db.executemany(self.SQL_INSERT_HIT_CACHE, (users_signed,))
        self.db.commit()
        return users_sign_notify

    def _cleanup_users_no_login(self, users_no_login):
        """check if the users without a github login in the list have already been
        notified in the PR. If so, remove them from the list to avoid notifying
        again and again.
        return a set of (name, email) for unnotified users.
        """
        res = self.db.execute(self.SQL_SELECT_MISS_CACHE_NOLOGIN_PR, (self.pr_key,))
        notified_miss = {r[0] for r in res.fetchall()}
        remaining_no_login = {
            (name, email)
            for name, email in users_no_login
            if email not in notified_miss
        }
        self._update_cache_miss_no_login(remaining_no_login)
        return remaining_no_login

    def _update_cache_miss_no_login(self, users_no_login):
        sql = (
            "INSERT OR IGNORE "
            "INTO nologin_cla_ko(email, date_cla_ko, pull_request) "
            "VALUES(?, CURRENT_DATE, ?)"
        )
        pr_key = self.pr_key
        params = [(email, pr_key) for name, email in users_no_login]
        self.db.executemany(sql, params)


def get_commit_author(commit):
    """
    Check a commit from the github api json
    """
    message = commit["commit"]["message"]
    if re.match(RE_WEBLATE_COMMIT_MSG, message, re.S):
        # don't enforce CLA check on translations
        return set(), set()
    users_login = set()
    users_no_login = set()
    if commit["committer"] and "login" in commit["committer"]:
        author = commit["committer"]["login"]
        users_login.add(author)
    else:
        author = commit["commit"]["committer"]["name"]
        author_email = commit["commit"]["committer"]["email"]
        users_no_login.add((author, author_email))
    if commit["author"] and "login" in commit["author"]:
        author = commit["author"]["login"]
        users_login.add(author)
    else:
        author = commit["commit"]["author"]["name"]
        author_email = commit["commit"]["author"]["email"]
        users_no_login.add((author, author_email))

    return users_login, users_no_login


SQL_DATABASE_CREATE = """
    CREATE TABLE IF NOT EXISTS login_cla_ok(
        login VARCHAR(80),
        date_cla_ok TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS login_cla_ok_unique
    ON login_cla_ok(login);
    CREATE INDEX IF NOT EXISTS login_cla_ok_index
    ON login_cla_ok(login);

    CREATE TABLE IF NOT EXISTS login_cla_ko(
        login VARCHAR(80),
        date_cla_ko TEXT,
        pull_request TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS login_cla_ko_unique
    ON login_cla_ko(login, pull_request);
    CREATE INDEX IF NOT EXISTS login_cla_ko_index
    ON login_cla_ko(login, pull_request);

    CREATE TABLE IF NOT EXISTS nologin_cla_ko(
        name VARCHAR(80),
        email VARCHAR(80),
        date_cla_ko TEXT,
        pull_request TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS nologin_cla_ko_unique
    ON nologin_cla_ko(email, pull_request);
    CREATE INDEX IF NOT EXISTS nologin_cla_ko_index
    ON nologin_cla_ko(email, pull_request);

"""


def _init_database(dbfile):
    with sqlite3.connect(dbfile) as db:
        db.executescript(SQL_DATABASE_CREATE)


_init_database(config.CLABOT_CACHE)
