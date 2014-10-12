#!/usr/bin/env python3

import argparse
import configparser
import hashlib
import hmac
import json
import pprint
import os
import sys
import json
import requests
from urllib.parse import unquote
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests.auth import HTTPBasicAuth

config = None
GITHUB_BASE_URL = 'https://api.github.com'

class GithubHookHandler(BaseHTTPRequestHandler):
    
    github_allowed_events = []
    
    def _validate_signature(self, repo, data, hub_signature):
        digest_type, signature = hub_signature.split('=')
        if digest_type != 'sha1':
            return False

        secret = config['clabot']['token_%s' % repo]
        mac = hmac.new(bytes(secret, 'utf-8'), msg=data, digestmod=hashlib.sha1)
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

    def _has_signed_cla(self, user):
        """
            Connect to odoo backend to verify if the user have signed
            the OCA CLA
        """
        return False
    
    def handle_payload(self, event):
        
        if event['action'] not in ('opened','synchronize'):
            self.send_response(400)
            return
        
        user = event['pull_request']['user']['login']

        if not self._has_signed_cla(user):
            # Send CLA comment
            
            path = '/repos/{owner}/{repo}/issues/{number}/comments'
            repo = event['repository']['name']
            owner = event['repository']['owner']['login']
            number = event['number']
            
            path = path.format(
                owner=owner,
                repo=repo,
                number=number,
            )

            cla_message = config['clabot']['cla_message'].format(user=user)
            data = {'body': cla_message}

            login = config['clabot']['github_login']
            password = config['clabot']['github_password']

            res = requests.post(
                GITHUB_BASE_URL+path,
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
