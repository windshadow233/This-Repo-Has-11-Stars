import base64
import hashlib
import hmac
import os
import json

import requests


GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')


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
    if path == "/this-repo-has-n-stars":
        secret = os.environ.get('SECRET')
        hashsum = hmac.new(secret.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
        if hashsum != signature:
            return {
                'statusCode': 401,
                'body': 'Bad signature'
            }
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
        requests.patch(repository_url, headers=headers, json=data)

        readme_url = repository_url + '/contents/README.md'
        res = requests.get(readme_url, headers=headers)
        content = base64.b64decode(res.json()['content']).decode()
        lines = content.split('\n\n')
        lines[0] = f"# It's True 💗 This Repo Has {stars} Stars!"
        new_content = '\n\n'.join(lines)
        encoded_content = base64.b64encode(new_content.encode()).decode()
        sha = res.json()['sha']
        data = {
            "message": f"Update star count to {stars}",
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(readme_url, json=data, headers=headers)
        return {'statusCode': response.status_code, 'body': "OK"}
    else:
        return {'statusCode': 404, 'body': ""}
