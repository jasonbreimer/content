import time

import requests
import re
import sys
import argparse
import base64
import json
from datetime import datetime

# Disable insecure warnings
import urllib3
urllib3.disable_warnings()

API_SUFFIX = 'https://api.github.com/repos/demisto/demisto-sdk'
TIMEOUT = 60 * 60 * 6  # 6 hours


def options_handler():
    parser = argparse.ArgumentParser(description='Creates release pull request for demisto-sdk.')

    parser.add_argument('-t', '--access_token', help='Github access token', required=True)
    parser.add_argument('-b', '--release_branch_name', help='The name of the release branch', required=True)

    options = parser.parse_args()
    return options


def main():
    options = options_handler()
    access_token = options.access_token
    release_branch_name = options.release_branch_name

    print(f'Preparing to create Pull request to release branch {release_branch_name}')

    headers = {
        'Authorization': f'Bearer {access_token}',
        'accept': 'application/vnd.github+json'
    }

    # get pyproject.toml file sha
    url = f'{API_SUFFIX}/contents/pyproject.toml'
    response = requests.request('GET', url, params={'ref': release_branch_name}, verify=False)
    if response.status_code != 200:
        print(f'Failed to get the pyproject.toml file from branch {release_branch_name}')
        print(response.text)
        sys.exit(1)
    pyproject_sha = response.json().get('sha')

    # get pyproject.toml file content
    url = f'https://raw.githubusercontent.com/demisto/demisto-sdk/{release_branch_name}/pyproject.toml'
    response = requests.request('GET', url, verify=False)
    if response.status_code != 200:
        print(f'Failed to get the pyproject.toml file content from branch {release_branch_name}')
        print(response.text)
        sys.exit(1)
    pyproject_content = response.text

    # update pyproject.toml content with the release version
    file_text = re.sub(r'\nversion = \"(\d+\.\d+\.\d+)\"\n', f'\nversion = "{release_branch_name}"\n', pyproject_content)
    content = bytes(file_text, encoding='utf8')

    # commit pyproject.toml
    data = {
        'message': 'Commit poetry files',
        'content': base64.b64encode(content).decode("utf-8"),
        'branch': release_branch_name,
        'sha': pyproject_sha
    }

    url = f'{API_SUFFIX}/contents/pyproject.toml'
    response = requests.request('PUT', url, data=json.dumps(data), headers=headers, verify=False)
    if response.status_code != 200:
        print(f'Failed to commit the pyproject.toml file')
        print(response.text)
        sys.exit(1)

    # create the release PR
    data = {
        'base': 'master',
        'head': release_branch_name,
        'title': f'Demisto-sdk release {release_branch_name}',
        'body': ''
    }
    url = f'{API_SUFFIX}/pulls'
    response = requests.request('POST', url, data=json.dumps(data), headers=headers, verify=False)
    if response.status_code != 201:
        print(f'Failed to create pull request for branch {release_branch_name}')
        print(response.text)
        sys.exit(1)

    pr_url = response.json().get('html_url')
    pr_number = response.json().get('number')
    print(f'The Pull request created successfully! {pr_url}')

    # trigger SDK changelog workflow
    print('Triggering SDK changelog workflow')
    inputs = {
        'branch_name': release_branch_name,
        'pr_number': str(pr_number),
        'pr_title': f'demisto-sdk release {release_branch_name}'
    }

    data = {
        'ref': release_branch_name,
        'inputs': inputs
    }
    url = f'{API_SUFFIX}/actions/workflows/sdk-release.yml/dispatches'
    response = requests.request('POST', url, data=json.dumps(data), headers=headers, verify=False)

    if response.status_code != 204:
        print(f'Failed to trigger SDK changelog workflow')
        print(response.text)
        sys.exit(1)
    print('SDK changelog workflow triggered, waiting for it to be finished')
    time.sleep(10)

    url = 'https://api.github.com/repos/demisto/demisto-sdk/actions/workflows/sdk-release.yml/runs'
    response = requests.request('GET', url, params={'branch': release_branch_name}, headers=headers, verify=False)
    if response.status_code != 200:
        print(f'Failed to retrieve SDK changelog workflow')
        print(response.text)
        sys.exit(1)

    # get the latest workflow
    workflow_runs = response.json().get('workflow_runs', [])
    workflow_id = max(
        workflow_runs,
        key=lambda x: datetime.strptime(x["created_at"], "%Y-%m-%dT%H:%M:%SZ"),
    ).get('id')

    # initialize timer
    start = time.time()
    elapsed: float = 0

    # wait to the workflow to finished
    status = ''
    url = f'https://api.github.com/repos/demisto/demisto-sdk/actions/runs/{workflow_id}/jobs'
    while status != 'completed' and elapsed < TIMEOUT:

        response = requests.request('GET', url, headers=headers, verify=False)
        if response.status_code != 200:
            print(f'Failed to retrieve SDK changelog workflow status')
            print(response.text)
            sys.exit(1)

        job_data = response.json().get('jobs', [])[0]
        status = job_data.get('status')
        print('still waiting')
        time.sleep(10)

        elapsed = time.time() - start

    if elapsed >= TIMEOUT:
        sys.exit(1)

    if job_data.get('conclusion') != 'success':
        print(f'Retrieve SDK changelog workflow Failed:')
        print(job_data)
        sys.exit(1)

    print('Retrieve SDK changelog workflow finished successfully')


if __name__ == "__main__":
    main()
