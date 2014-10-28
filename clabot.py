#!/usr/bin/env python3

import argparse
import configparser
import hashlib
import hmac
import json
import re
import pprint
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests
from requests.auth import HTTPBasicAuth
from erppeek import Client


class GithubHookHandler(BaseHTTPRequestHandler):

    _github_allowed_events = []

    def _validate_signature(self, repo, data, hub_signature):
        digest_type, signature = hub_signature.split('=')
        if digest_type != 'sha1':
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
        return hmac.compare_digest(mac.hexdigest(), signature)

    def do_POST(self):

        content_length = int(self.headers['Content-Length'] or 0)
        content_type = self.headers['Content-Type']
        hub_signature = self.headers['X-Hub-Signature']
        github_event = self.headers['X-GitHub-Event']

        if github_event not in self._github_allowed_events:
            self.send_response(400)
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
        except:
            self.send_response(400)
            return

        if not self._validate_signature(repo, post_data, hub_signature):
            self.send_response(401)
            return

        if self.handle_payload(payload):
            self.send_response(200)
        else:
            self.send_response(400)


class PullRequestHandler(GithubHookHandler):

    _github_allowed_events = ['pull_request']

    def _get_users_not_signed_cla(self, users):
        config = self.server.config
        users_no_sign = []

        client = Client(
            config['odoo_host'],
            config['odoo_database'],
            config['odoo_user'],
            config['odoo_password']
        )
        for user in users:
            condition = [
                (config['odoo_github_login_field'], '=', user),
                ('category_id', '=', config['odoo_cla_categ']),
            ]
            if not client.search('res.partner', condition):
                users_no_sign.append(user)
        return users_no_sign

    def handle_payload(self, event):

        if event['action'] not in ('opened', 'synchronize'):
            return False

        config = self.server.config
        base_url = config['github_base_url']
        login = config['github_login']
        password = config['github_password']

        owner = event['repository']['owner']['login']
        repo = event['repository']['name']
        number = event['number']

        path = '/repos/{owner}/{repo}/pulls/{number}/commits'
        path = path.format(owner=owner, repo=repo, number=number)
        params = {'per_page': 250}  # maximum allowed
        res = requests.get(
            base_url + path,
            params=params,
            auth=HTTPBasicAuth(login, password)
        )
        commits = res.json()
        user = event['pull_request']['user']['login']
        users = [c['author']['login'] for c in commits]
        users = list(set(users))
        users_no_sign = self._get_users_not_signed_cla(users)

        if users_no_sign:
            path = '/repos/{owner}/{repo}/issues/{number}/comments'
            path = path.format(owner=owner, repo=repo, number=number)

            user = event['pull_request']['user']['login']
            users = ''
            for user in users_no_sign:
                users += '+ @%s \n' % user
            cla_message = config['cla_message'].format(user=user, users=users)
            data = {'body': cla_message}

            res = requests.post(
                base_url + path,
                data=json.dumps(data),
                auth=HTTPBasicAuth(login, password)
            )
        return True


def run(config):

    config = config['clabot']
    server_address = (config['interface'], int(config['port']))
    server = HTTPServer(server_address, PullRequestHandler)
    server.config = config

    print('CLA bot listening on %s:%i' % server_address)
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
