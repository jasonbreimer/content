#!/usr/bin/env bash
# This script triggers a cleanup build machines job in gitlab-CI.

# For this script to work you will need to use a trigger token (see here for more about that: https://docs.gitlab.com/ee/ci/triggers/#create-a-pipeline-trigger-token)

# This script requires the gitlab-ci trigger token. The branch to run against is an optional second parameter
# (the default is the current branch). The Slack channel to send messages to is an optional
# third parameter (the default is the 'dmst-build-test')

# Ways to run this script are:
# trigger_cleanup_build_machines.sh -ct <trigger-token> [-b <branch-name> -ch <slack-channel-name>]
if [ "$#" -lt "1" ]; then
  echo "Usage:
  $0 -ct <token>

  [-ct, --ci-token]      The ci gitlab trigger token.
  [-b, --branch]         The branch name. Default is the current branch.
  [-ch, --slack-channel] A Slack channel to send notifications to. Default is dmst-build-test.
  [-m, --machine]        The machine to clean, default None.
  [-mt --machine-type]   The machine type, default nightly
  [-mc --machine-count]  The number of machines to lock, default all
  [-p --lock-path]       The gcp lock path, default content-locks/locks-xsiam-ga-nightly
  "
  echo "Get the trigger token from here https://vault.paloaltonetworks.local/home#R2VuZXJpY1NlY3JldERldGFpbHM6RGF0YVZhdWx0OmIyMzJiNDU0LWEzOWMtNGY5YS1hMTY1LTQ4YjRlYzM1OTUxMzpSZWNvcmRJbmRleDowOklzVHJ1bmNhdGVk" # disable-secrets-detection  TODO
  exit 1
fi

_branch="$(git branch  --show-current)"
_slack_channel="dmst-build-test"
_machine_type="nightly"
_machine=None
_machine_count="all"
_lock_path="content-locks/locks-xsiam-ga-nightly"

# Parsing the user inputs.

while [[ "$#" -gt 0 ]]; do
  case $1 in

  -ct|--ci-token) _ci_token="$2"
    shift
    shift;;

  -b|--branch) _branch="$2"
    shift
    shift;;

  -ch|--slack-channel) _slack_channel="$2"
    shift
    shift;;

  -m|--machine) _machine="$2"
    shift
    shift;;
  -mt|--machine-type) _machine_type="$2"
    shift
    shift;;
  -mc|--machine-count) _machine_count="$2"
    shift
    shift;;
  -p|--lock-path) _lock_path="$2"
    shift
    shift;;

  *)    # unknown option.
    shift;;
  esac
done

if [ -z "$_ci_token" ]; then
    echo "You must provide a ci token."
    exit 1
fi
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/trigger_build_url.sh"

curl "$BUILD_TRIGGER_URL" --form "ref=${_branch}" --form "token=${_ci_token}" \
    --form "variables[BUILD_MACHINES_CLEANUP]=true" \
    --form "variables[SLACK_CHANNEL]=${_slack_channel}" \
    --form "variables[LOCK_MACHINE_NAME]=${_machine}" \
    --form "variables[CLOUD_MACHINES_TYPE]=${_machine_type}" \
    --form "variables[CLOUD_MACHINES_COUNT]=${_machine_count}" \
    --form "variables[GCS_LOCKS_PATH]=${_lock_path}"\
     | jq
