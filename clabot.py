#!/usr/bin/env python3

import argparse
import configparser
import hashlib
import sqlite3
import hmac
import json
import logging
import os
import re
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from requests.auth import HTTPBasicAuth
from erppeek import Client

SQL_DATABASE_SCRIPT = '''
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

'''

SQL_SELECT_HIT_CACHE = '''
    SELECT login FROM login_cla_ok WHERE login IN (%s)
'''

SQL_INSERT_HIT_CACHE = '''
    INSERT OR IGNORE INTO login_cla_ok(login, date_cla_ok)
    VALUES(?, CURRENT_DATE)
'''

SQL_SELECT_MISS_CACHE_USERS = '''
    SELECT login,pull_request FROM login_cla_ko WHERE login IN (%s)
'''

SQL_SELECT_MISS_CACHE_PR = '''
    SELECT login,pull_request FROM login_cla_ko WHERE pull_request=?
'''

SQL_INSERT_MISS_CACHE = '''
    INSERT OR IGNORE INTO login_cla_ko(login, date_cla_ko, pull_request)
    VALUES(?, CURRENT_DATE, ?)
'''

SQL_DELETE_MISS_CACHE = '''
    DELETE FROM login_cla_ko WHERE login IN (%s)
'''

SQL_SELECT_MISS_CACHE_NOLOGIN_PR = '''
    SELECT email,pull_request FROM nologin_cla_ko WHERE pull_request=?
'''

SQL_INSERT_MISS_CACHE_NOLOGIN = '''
    INSERT OR IGNORE INTO nologin_cla_ko(email, date_cla_ko, pull_request)
    VALUES(?, CURRENT_DATE, ?)
'''

SQL_DELETE_MISS_CACHE = '''
    DELETE FROM login_cla_ko WHERE login IN (%s)
'''

RE_WEBLATE_COMMIT_MSG = r'''^Translated using Weblate.*
Translate-URL: https://translation\.odoo-community\.org/'''


try:
    compare_digest = hmac.compare_digest
except AttributeError:
    def compare_digest(a, b):
        return a == b


_logger = logging.getLogger('clabot')


class GithubHookHandler(BaseHTTPRequestHandler):

    _github_allowed_events = []

    def _validate_signature(self, repo, data, hub_signature):

        m = re.search('^sha1=(.*)', hub_signature or '')
        if m:
            signature = m.group(1)
        else:
            return False

        config = self.server.config
        token_key = 'token_' + repo
        secret = None
        if token_key in config:
            secret = config[token_key]
        if not secret:
            secret = config['default_token']

        mac = hmac.new(
            bytes(secret, 'utf-8'), msg=data, digestmod=hashlib.sha1)

        return compare_digest(mac.hexdigest(), signature)

    def do_POST(self):

        content_length = int(self.headers['Content-Length'] or 0)
        content_type = self.headers['Content-Type']
        hub_signature = self.headers['X-Hub-Signature']
        github_event = self.headers['X-GitHub-Event']
        _logger.info('Event: %s', github_event)
        if github_event == 'ping':
            self.send_response(200, 'pong')
            self.end_headers()
            return

        if github_event not in self._github_allowed_events:
            self.send_response(400, 'unallowed message')
            self.end_headers()
            return

        try:
            post_data = self.rfile.read(content_length)
            if content_type == 'application/json':
                json_data = post_data.decode('utf-8')
            elif content_type == 'application/x-www-form-urlencoded':
                json_data = re.sub(
                    '^payload=', '', unquote(post_data.decode('utf-8'))
                )
            else:
                raise ValueError('Invalid Content-Type')

            payload = json.loads(json_data)
            repo = payload['repository']['name']
        except Exception as exc:
            self.send_response(400, str(exc))
            self.end_headers()
            return

        if not self._validate_signature(repo, post_data, hub_signature):
            self.send_response(401, 'invalid signature')
            self.end_headers()
            return

        if self.handle_payload(payload):
            self.send_response(200, 'OK')
        else:
            self.send_response(400, 'error handling payload')
        self.end_headers()

    def send_response(self, code, message=None):
        _logger.info('response: %s %s', code, message)
        if message is None:
            if code == 200:
                message = 'OK'
            else:
                message = 'NOK'
        return super().send_response(code, message)


class PullRequestHandler(GithubHookHandler):

    _github_allowed_events = ['pull_request']

    def _check_cla(self, users, pull_request):

        config = self.server.config
        cache_conn = self.server.cache_conn
        cache_cr = self.server.cache_cr
        send_miss_notification = True
        users_no_sign = []
        users_oca_no_sign = []
        users_sign = []
        users_sign_notify = []

        if cache_cr:
            placeholders = ','.join('?' * len(users))
            res = cache_cr.execute(
                SQL_SELECT_HIT_CACHE % placeholders, users
            )
            users_cached = [r[0] for r in res.fetchall()]
            users = list(set(users) - set(users_cached))

        client = Client(
            config['odoo_host'],
            config['odoo_database'],
            config['odoo_user'],
            config['odoo_password']
        )
        for user in users:

            condition = [(config['odoo_github_login_field'], '=', user)]
            if not client.search('res.partner', condition):
                users_no_sign.append(user)
                continue

            condition.extend([
                '|',
                ('category_id', '=', config['odoo_icla_categ']),
                ('parent_id.category_id', '=', config['odoo_ecla_categ']),
            ])
            if not client.search('res.partner', condition):
                users_oca_no_sign.append(user)
            else:
                users_sign.append(user)

        if cache_cr:
            if users_sign:
                placeholders = ','.join('?' * len(users_sign))
                res = cache_cr.execute(
                    SQL_SELECT_MISS_CACHE_USERS % placeholders,
                    users_sign
                )
                if res:
                    users_sign_notify = res.fetchall()
                    cache_cr.execute(
                        SQL_DELETE_MISS_CACHE % placeholders,
                        users_sign
                    )
                cache_cr.executemany(SQL_INSERT_HIT_CACHE, (users_sign,))
            if users_no_sign or users_oca_no_sign:

                users = users_no_sign + users_oca_no_sign
                placeholders = ','.join('?' * len(users))
                res = cache_cr.execute(
                    SQL_SELECT_MISS_CACHE_USERS % placeholders, users
                )
                users_no_sign_hit = [r[0] for r in res.fetchall()]
                users_oca_no_sign = list(
                    set(users_oca_no_sign) - set(users_no_sign_hit))
                users_no_sign = list(
                    set(users_no_sign) - set(users_no_sign_hit))

                # Do not send again a notification
                res = cache_cr.execute(
                    SQL_SELECT_MISS_CACHE_PR, (pull_request,))
                send_miss_notification = not res.fetchone()

                login_pr = [(login, pull_request) for login in users_no_sign]
                cache_cr.executemany(SQL_INSERT_MISS_CACHE, login_pr)

        else:
            # the cache is not activated
            # so avoid sending notifications on all pull request commit
            users_sign_notify = None

        if cache_conn:
            cache_conn.commit()

        return users_sign_notify, users_no_sign, users_oca_no_sign, \
            send_miss_notification

    def handle_payload(self, event):

        if event['action'] not in ('opened', 'synchronize'):
            return True

        config = self.server.config
        cache_cr = self.server.cache_cr

        base_url = config['github_base_url']
        login = config['github_login']
        password = config['github_password']

        owner = event['repository']['owner']['login']
        repo = event['repository']['name']
        number = event['number']

        path = '/repos/{owner}/{repo}/pulls/{number}/commits'.format(
            owner=owner, repo=repo, number=number
        )
        params = {'per_page': 250}  # maximum allowed
        res = requests.get(
            base_url + path,
            params=params,
            auth=HTTPBasicAuth(login, password)
        )
        commits = res.json()
        pull_user = event['pull_request']['user']['login']
        users_login = set()
        users_no_login = set()
        for commit in commits:
            u_login, u_no_login = get_commit_author(commit)
            users_no_login |= u_no_login
            users_login |= u_login

        pull_request = '{pull_user}/{owner}/{repo}/{number}'.format(
            pull_user=pull_user, owner=owner, repo=repo, number=number
        )
        users_sign_notify, users_no_sign, \
            users_oca_no_sign, send_miss_notification = self._check_cla(
                list(users_login),
                pull_request,
            )

        pull_user = event['pull_request']['user']['login']

        def post_notification(path, message):

            if self.server.debug:
                _logger.debug('notification:path:' + path)
                _logger.debug('notification:message:' + message)
                return

            data = {'body': message}
            requests.post(
                base_url + path,
                data=json.dumps(data),
                auth=HTTPBasicAuth(login, password)
            )

        # remove no_login users which have already been notified on this PR
        users_no_login = self._cleanup_users_no_login(users_no_login,
                                                      pull_request)

        if users_no_sign or users_oca_no_sign or users_no_login:

            users_ko = ''
            for user in users_oca_no_sign:
                users_ko += '+ @%s\n' % user
            for user in users_no_sign:
                users_ko += '+ @%s (login unknown in OCA database)\n' % user
            for user, email in users_no_login:
                users_ko += ('+ %s <%s> (no github login found)\n' %
                             (user, email))

            if send_miss_notification:
                path = '/repos/{owner}/{repo}/issues/{number}/comments'
                path = path.format(owner=owner, repo=repo, number=number)
                message = config['cla_ko_message'].format(
                    pull_user=pull_user,
                    users_ko=users_ko,
                )
                post_notification(path, message)

                _logger.info('PR: %s/%s#%s: no CLA for [%s], '
                             'unknown OCA login for [%s], '
                             'no github login for [%s]',
                             owner, repo, number,
                             ', '.join(users_oca_no_sign) or '',
                             ', '.join(users_no_sign) or '',
                             ', '.join('%s <%s>' % (name, email)
                                       for name, email in users_no_login)
                             if users_no_login else '',
                             )

            else:
                _logger.info('PR: %s/%s#%s: CLA notification already sent',
                             owner, repo, number
                             )

        else:
            _logger.info('PR %s/%s#%s: CLA OK', owner, repo, number)

        if users_sign_notify:
            sign_notifications = {}
            for user_sign, pr in users_sign_notify:
                sign_notifications.setdefault(pr, []).append(user_sign)

            for pr, users_sign in sign_notifications.items():
                pull_user, owner, repo, number = pr.split('/')
                path = '/repos/{owner}/{repo}/issues/{number}/comments'
                path = path.format(owner=owner, repo=repo, number=number)

                users_ok = ''
                for user in users_sign:
                    users_ok += '+ @%s\n' % user

                message = config['cla_ok_message'].format(
                    pull_user=pull_user,
                    users_ok=users_ok,
                )
                post_notification(path, message)
                _logger.info('PR %s/%s#%s: CLA OK for [%s]',
                             owner, repo, number, ', '.join(users_sign)
                             )

        return True

    def _cleanup_users_no_login(self, users_no_login, pull_request):
        """check if the users without a github login in the list have already been
        notified in the PR. If so, remove them from the list to avoid notifying
        again and again.
        return a set of (name, email) for unnotified users.
        """
        cache_cr = self.server.cache_cr
        if not cache_cr:
            return users_no_login
        res = cache_cr.execute(
            SQL_SELECT_MISS_CACHE_NOLOGIN_PR,
            (pull_request,)
        )
        notified_miss = set(r[0] for r in res.fetchall())
        remaining_no_login = set((name, email)
                                 for name, email in users_no_login
                                 if email not in notified_miss)
        self._insert_miss_no_login(remaining_no_login, pull_request)
        return remaining_no_login

    def _insert_miss_no_login(self, users_no_login, pull_request):
        cache_cr = self.server.cache_cr
        if not cache_cr:
            return
        for name, email in users_no_login:
            cache_cr.execute(SQL_INSERT_MISS_CACHE_NOLOGIN,
                             (email, pull_request))


def get_commit_author(commit):
    """
    Check a commit from the github api json
    """
    message = commit['commit']['message']
    if re.match(RE_WEBLATE_COMMIT_MSG,
                message,
                re.S):
        # don't enforce CLA check on translations
        return set(), set()
    users_login = set()
    users_no_login = set()
    if commit['committer'] and 'login' in commit['committer']:
        author = commit['committer']['login']
        users_login.add(author)
    else:
        author = commit['commit']['committer']['name']
        author_email = commit['commit']['committer']['email']
        users_no_login.add((author, author_email))
    if commit['author'] and 'login' in commit['author']:
        author = commit['author']['login']
        users_login.add(author)
    else:
        author = commit['commit']['author']['name']
        author_email = commit['commit']['author']['email']
        users_no_login.add((author, author_email))

    return users_login, users_no_login


def run(config):

    config = config['clabot']

    debug = config.getboolean('debug')
    logging.basicConfig(level=debug and logging.DEBUG or logging.INFO)
    _logger.debug('Server started in DEBUG mode')

    server_address = (config.get('interface'), config.getint('port'))

    cache_file = config.get('cache_file')
    cache_conn = None
    cache_cr = None
    if cache_file:
        if not os.path.isfile(cache_file):
            _logger.info('create sqlite3 file cache "%s"', cache_file)
        try:
            cache_conn = sqlite3.connect(cache_file)
            cache_cr = cache_conn.cursor()
            cache_cr.executescript(SQL_DATABASE_SCRIPT)
            _logger.info('use file cache "%s"', cache_file)
        except Exception as err:
            _logger.error('unable to create or use cache file "%s": %s',
                          cache_file,
                          err
                          )

    if not cache_cr:
        _logger.warn('cache not activated')

    server = HTTPServer(server_address, PullRequestHandler)
    server.debug = debug
    server.config = config
    server.cache_conn = cache_conn
    server.cache_cr = cache_cr

    _logger.info('CLA bot listening on %s:%i' % server_address)
    server.serve_forever()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Minimal CLA bot server')
    parser.add_argument(
        'config_file',
        help='Configuration ini file',
        type=str
    )
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config_file)

    run(config)
