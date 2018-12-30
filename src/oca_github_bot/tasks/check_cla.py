# Copyright (c) Camptocamp 2018
# Copyright (c) Akretion 2014
import re
import sqlite3

from .. import config, github
from ..odoo_client import login
from ..queue import getLogger, task

_logger = getLogger(__name__)
RE_WEBLATE_COMMIT_MSG = r"""^Translated using Weblate.*
Translate-URL: https://translation\.odoo-community\.org/"""


_logger = getLogger(__name__)


@task()
def check_cla(owner, repo, pull_user, pr_number, action):
    checker = CLACheck(owner, repo, pull_user, pr_number, action)
    return checker.check_cla()


class CLACheck:
    def __init__(self, owner, repo, pull_user, pr_number, action):
        self.owner = owner
        self.repo = repo
        self.pull_user = pull_user
        self.pr_number = pr_number
        self.action = action
        self.pr_key = f"{self.pull_user}/{self.owner}/{self.repo}/{self.pr_number}"
        self.db = sqlite3.connect(config.CLABOT_CACHE)

    SQL_SELECT_MISS_CACHE_USERS = """
    SELECT login,pull_request FROM login_cla_ko WHERE login IN ({placeholder})
    """
    SQL_DELETE_MISS_CACHE = """
    DELETE FROM login_cla_ko WHERE login IN ({placeholder})
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
    def gh_pull_request(self):
        with github.repository(self.owner, self.repo) as repo:
            return repo.pull_request(self.pr_number)

    def _get_commit_users(self):
        users_login = set()
        users_no_login = set()
        gh_commits = self.gh_pull_request.commits()
        for gh_commit in gh_commits:
            u_login, u_no_login = get_commit_author(gh_commit)
            users_login |= u_login
            users_no_login |= u_no_login
        return users_login, users_no_login

    # FIXME make async
    def check_cla(self):
        # method "handle_payload" in clabot.py
        if self.action not in ("opened", "synchronize"):
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
                users_ko += f"+ @{user}\n"
            for user in users_no_sign:
                users_ko += f"+ @{user} (login unknown in OCA database)\n"
            for user, email in users_no_login:
                users_ko += f"+ {user} <{email}> (no github login found)\n"

            if send_miss_notification:
                message = config["cla_ko_message"].format(
                    pull_user=self.pull_user, users_ko=users_ko
                )
                github.comment_issue(self.owner, self.repo, self.pr_number, message)

                no_cla = ", ".join(users_oca_no_sign) or ""
                unknown_login = ", ".join(users_no_sign) or ""
                no_gh_login = (
                    ", ".join(f"{name} <{email}>" for name, email in users_no_login)
                    if users_no_login
                    else ""
                )
                _logger.info(
                    f"PR: {self.owner}/{self.repo}#{self.pr_number}: "
                    f"no CLA for [{no_cla}], "
                    f"unknown OCA login for [{unknown_login}], "
                    f"no github login for [{no_gh_login}]"
                )

            else:
                _logger.info(
                    f"PR: {self.owner}/{self.repo}#{self.pr_number}: "
                    f"CLA notification already sent"
                )

        else:
            _logger.info(f"PR {self.owner}/{self.repo}#{self.pr_number}: " f"CLA OK")

        if users_sign_notify:
            sign_notifications = {}
            for user_sign, pr in users_sign_notify:
                sign_notifications.setdefault(pr, []).append(user_sign)

            for pr, users_sign in sign_notifications.items():
                pull_user, owner, repo, number = pr.split("/")
                users_ok = ""
                for user in users_sign:
                    users_ok += f"+ @{user}\n"

                message = config.cla_ok_message.format(
                    pull_user=pull_user, users_ok=users_ok
                )
                github.comment_issue(owner, repo, number, message)
                signed = ", ".join(users_sign)
                _logger.info(
                    f"PR {self.owner}/{self.repo}#{self.pr_number}: "
                    f"CLA OK for [{signed}]"
                )

        return True

    def _check_cla_of_users(self, users):

        send_miss_notification = True
        users_no_sign = []
        users_oca_no_sign = []
        users_sign = []
        users_sign_notify = []
        sql_select_hit_cache = """
        SELECT login FROM login_cla_ok WHERE login IN ({placeholder})
        """

        placeholder = ",".join("?" * len(users))
        res = self.db.execute(
            sql_select_hit_cache.format(placeholder=placeholder), users
        )
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
            placeholder = ",".join("?" * len(users))
            res = self.db.execute(
                self.SQL_SELECT_MISS_CACHE_USERS.format(placeholder=placeholder), users
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
        placeholder = ",".join("?" * len(users_signed))
        res = self.db.execute(
            self.SQL_SELECT_MISS_CACHE_USERS.format(placeholder=placeholder),
            users_signed,
        )
        if res:
            users_sign_notify = res.fetchall()
            self.db.execute(
                self.SQL_DELETE_MISS_CACHE.format(placeholder=placeholder), users_signed
            )
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


def get_commit_author(gh_commit):
    """
    Check a commit from the github api json
    """
    message = gh_commit.commit.message
    if re.match(RE_WEBLATE_COMMIT_MSG, message, re.S):
        # don't enforce CLA check on translations
        return set(), set()
    users_login = set()
    users_no_login = set()
    if gh_commit.committer and gh_commit.committer.login:
        author = gh_commit.committer.login
        users_login.add(author)
    else:
        author = gh_commit.commit.committer.name
        author_email = gh_commit.commit.committer.email
        users_no_login.add((author, author_email))
    if gh_commit.author and gh_commit.author.login:
        author = gh_commit.author.login
        users_login.add(author)
    else:
        author = gh_commit.commit.author.name
        author_email = gh_commit.commit.author.email
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
