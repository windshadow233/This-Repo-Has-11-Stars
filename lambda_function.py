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
        # Update repo name & description
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
        # Update title
        readme_url = repository_url + '/contents/README.md'
        res = requests.get(readme_url, headers=headers)
        sha = res.json()['sha']
        content = base64.b64decode(res.json()['content']).decode()
        lines = content.split('\n\n')[:4]
        lines[0] = f"# It's True 💗 This Repo Has {stars} Star{'s' if stars != 1 else ''}!"
        # Update stargazers
        stargazers_url = repository_url + "/stargazers"
        res = requests.get(stargazers_url, headers={'Accept': 'application/vnd.github.v3.star+json', 'Authorization': f"Bearer {GITHUB_TOKEN}"}).json()
        table = "| No. | Avatar | Username | Starred At |\n" \
                "| :---: | :---: | :---: | :---: |"
        for i, info in enumerate(res):
            user = info['user']
            table += f"\n| {i} | <img src='{user['avatar_url']}' width='50'> | {user['login']} | {info['starred_at']} |"
        lines.append(table)
        new_content = '\n\n'.join(lines)
        encoded_content = base64.b64encode(new_content.encode()).decode()
        data = {
            "message": f"Update star count to {stars}",
            "content": encoded_content,
            "sha": sha
        }
        response = requests.put(readme_url, json=data, headers=headers)
        return {'statusCode': response.status_code, 'body': "OK"}
    else:
        return {'statusCode': 404, 'body': ""}
