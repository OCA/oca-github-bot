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

config = None
GITHUB_BASE_URL = 'https://api.github.com'


class GithubHookHandler(BaseHTTPRequestHandler):

    github_allowed_events = []

    def _validate_signature(self, repo, data, hub_signature):
        digest_type, signature = hub_signature.split('=')
        if digest_type != 'sha1':
            return False

        secret = config['token_%s' % repo]
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
            if content_type == 'application/x-www-form-urlencoded':
                json_data = re.sub(
                    '^payload=', '', unquote(post_data.decode('utf-8'))
                )
            elif content_type == 'application/json':
                json_data = post_data.decode('utf-8')
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

        self.handle_payload(payload)
        self.send_response(200)


class PullRequestHandler(GithubHookHandler):

    _github_allowed_events = ['pull_request']

    def _have_signed_cla(self, users):
        """
            Connect to odoo backend to verify if the users have signed
            the OCA CLA
        """

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
                return False

        return True

    def handle_payload(self, event):

        if event['action'] not in ('opened', 'synchronize'):
            self.send_response(400)
            return

        login = config['github_login']
        password = config['github_password']

        owner = event['repository']['owner']['login']
        repo = event['repository']['name']
        number = event['number']

        path = '/repos/{owner}/{repo}/pulls/{number}/commits'
        path = path.format(owner=owner, repo=repo, number=number)
        params = {'per_page': 250}  # maximum allowed
        res = requests.get(
            GITHUB_BASE_URL + path,
            params=params,
            auth=HTTPBasicAuth(login, password)
        )
        commits = res.json()
        users = [c['author']['login'] for c in commits]
        users = list(set(users))

        if not self._have_signed_cla(users):
            # Send CLA comment

            path = '/repos/{owner}/{repo}/issues/{number}/comments'
            path = path.format(owner=owner, repo=repo, number=number)

            user = event['pull_request']['user']['login']

            cla_message = config['cla_message'].format(user=user)
            data = {'body': cla_message}

            res = requests.post(
                GITHUB_BASE_URL + path,
                data=json.dumps(data),
                auth=HTTPBasicAuth(login, password)
            )

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Minimal CLA bot server')
    parser.add_argument("config_file", help="configuration ini file", type=str)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read(args.config_file)
    config = config['clabot']

    interface = config['interface']
    port = int(config['port'])

    server = HTTPServer((interface, port), PullRequestHandler)

    print('CLA bot listening on %s:%i' % (interface, port))
    server.serve_forever()
