import base64
import hashlib
import hmac
import os
import json

import requests


GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
SECRET = os.environ.get('SECRET')


def lambda_handler(event, context):
    path = event['rawPath']
    if 'body' in event:
        if event['isBase64Encoded']:
            body = base64.b64decode(event['body'])
        else:
            body = event['body'].encode()
    else:
        body = b""
    signature = event['headers']['x-hub-signature-256'].split("=")[1]
    hashsum = hmac.new(SECRET.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    if hashsum != signature:
        return {
            'statusCode': 401,
            'body': 'Bad signature'
        }
    if path == "/this-repo-has-n-stars":
        # https://docs.github.com/en/developers/webhooks-and-events/webhook-events-and-payloads#star
        payload = json.loads(body)
        repository = payload['repository']
        repository_url = repository['url']
        stars = repository['stargazers_count']

        new_name = f"This-Repo-Has-{stars}-Star{'s' if stars != 1 else ''}"
        new_description = f"Thanks for stopping by! This repository now has {stars} star{'s' if stars != 1 else ''}~🌟🌟🌟"
        headers = {'Authorization': f"Bearer {GITHUB_TOKEN}"}
        data = {
            'name': new_name,
            'description': new_description
        }
        response = requests.patch(repository_url, headers=headers, json=data)
        return {'statusCode': response.status_code, 'body': "OK"}
    else:
        return {'statusCode': 404, 'body': ""}
