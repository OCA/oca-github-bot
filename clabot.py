#!/usr/bin/env python3

import argparse
import configparser
import hashlib
import hmac
import json
import pprint
import os
import sys
import requests
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler

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

        secret = config['clabot']['token_%s' % repo]
        mac = hmac.new(
            bytes(secret, 'utf-8'), msg=data, digestmod=hashlib.sha1)
        return hmac.compare_digest(mac.hexdigest(), signature)

    def do_POST(self):

        content_length = int(self.headers['Content-Length'] or 0)
        hub_signature = self.headers['X-Hub-Signature']
        github_event = self.headers['X-GitHub-Event']

        if github_event not in self.github_allowed_events:
            self.send_response(400)
            return

        post_data = self.rfile.read(content_length)
        try:
            json_data = unquote(post_data.decode('utf-8'))[8:]
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

    github_allowed_events = ['pull_request']

    def _have_signed_cla(self, users):
        """
            Connect to odoo backend to verify if the users have signed
            the OCA CLA
        """

        odoo_server = 'http://%s:%i' % (
            config['clabot']['odoo_host'],
            int(config['clabot']['odoo_port']),
        )
        odoo_db = config['clabot']['odoo_database']
        odoo_user = config['clabot']['odoo_user']
        odoo_password = config['clabot']['odoo_password']
        odoo_cla_categ = config['clabot']['odoo_cla_categ']
        odoo_github_login_field = config['clabot']['odoo_github_login_field']
        return False

        client = Client(odoo_server, odoo_db, odoo_user, odoo_password)

        for user in users:
            condition = [
                (odoo_github_login_field, '=', user),
                ('category_id', '=', odoo_cla_categ),
            ]
            user_ids = client.search('res.partner', condition)
            return False

        return True

    def handle_payload(self, event):

        if event['action'] not in ('opened', 'synchronize'):
            self.send_response(400)
            return

        login = config['clabot']['github_login']
        password = config['clabot']['github_password']

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

            cla_message = config['clabot']['cla_message'].format(user=user)
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

    interface = config['clabot']['interface']
    port = int(config['clabot']['port'])

    server = HTTPServer((interface, port), PullRequestHandler)

    print('CLA bot listening on %s:%i' % (interface, port))
    server.serve_forever()
