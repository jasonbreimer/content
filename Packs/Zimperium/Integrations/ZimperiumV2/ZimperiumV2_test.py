import pytest
import io
from CommonServerPython import *
from ZimperiumV2 import Client, users_search_command, devices_search_command, device_by_id_command, report_get_command, threat_search_command, app_version_list_command, device_cve_get_command, devices_os_version_command, cve_devices_get_command, policy_group_list_command, policy_privacy_get_command, policy_threat_get_command, policy_phishing_get_command, policy_app_settings_get_command, policy_device_inactivity_list_command, policy_device_inactivity_get_command
SERVER_URL = 'https://test_url.com/api'


def util_load_json(path):
    with io.open(path, mode='r', encoding='utf-8') as f:
        return json.loads(f.read())


@pytest.fixture()
def client(requests_mock):
    requests_mock.post(f'{SERVER_URL}/auth/v1/api_keys/login', json={'accessToken': 'token'})
    return Client(base_url=SERVER_URL, client_id='test', client_secret='test', verify=True)


def test_users_search_command(client, requests_mock):
    """
        When: Running zimperium-users-search
        Given: team_id and user_id
        Then: validate the command result returned.
        """
    args = {'team_id': '3', 'user_id': '01'}
    mock_response_users_search = util_load_json(
        './test_data/users_search.json')

    requests_mock.get(f'{SERVER_URL}/auth/public/v1/users/01', json=mock_response_users_search)
    results = users_search_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.User'
    assert results.outputs_key_field == 'id'
    assert results.raw_response == mock_response_users_search
    assert results.outputs.get('id') == '01'


def test_device_by_id_command(client, requests_mock):
    """
        When: running zimperium-device-get-by-id
        Given: team_name
        Then: validate the command result returned.
        """
    args = {'device_id': '1'}
    mock_response_device_search = util_load_json(
        './test_data/device_by_id_get.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v2/devices/1', json=mock_response_device_search)
    results = device_by_id_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.Device'
    assert results.outputs.get('id') == '1'
    assert results.outputs_key_field == 'id'
    assert 'Device' in results.readable_output


def test_devices_search_command(client, requests_mock):
    """
        When: running zimperium-devices-search
        Given: team_name
        Then: validate the command result returned.
        """
    args = {'team_name': 'Default'}
    mock_response_device_search = util_load_json(
        './test_data/device_search.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v2/devices/start-scroll', json=mock_response_device_search)
    results = devices_search_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.Device'
    assert results.outputs[0].get('id') == mock_response_device_search.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device search' in results.readable_output


def test_report_get_command(client, requests_mock):
    """
        When: running zimperium-report-get comand.
        Given: The app version id.
        Then: validate the command result returned.
        """
    args = {'app_version_id': '6'}
    mock_response_report_get = util_load_json(
        './test_data/report_get.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v1/appVersions/6/json', json=mock_response_report_get)
    results = report_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.Report'
    assert results.outputs.get('platform') == 'android'
    assert 'Report' in results.readable_output
    assert results.raw_response == mock_response_report_get


def test_threat_search_command(client, requests_mock):
    """
        When: running zimperium-threat-search command
        Given: time to search threats after it, threats related to some team_id
        Then: validate the command result returned.
    """
    args = {'after': '3 month', 'team_id': '3'}
    mock_response_threat_search = util_load_json(
        './test_data/threat_search.json')

    requests_mock.get(f'{SERVER_URL}/threats/public/v1/threats', json=mock_response_threat_search)
    results = threat_search_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.Threat'
    assert results.outputs[0].get('id') == mock_response_threat_search.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Threat search' in results.readable_output
    assert results.raw_response == mock_response_threat_search


def test_app_version_list_command(client, requests_mock):
    """
        When: running zimperium-app-version-list
        Given: bundle id to filter by.
        Then: validate the command result returned.
        """
    args = {'bundle_id': 'bundle.id'}
    mock_response_app_version_list = util_load_json(
        './test_data/app_version_list.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v1/appVersions', json=mock_response_app_version_list)
    results = app_version_list_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.AppVersion'
    assert results.outputs[0].get('id') == mock_response_app_version_list.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'App Version List' in results.readable_output
    assert results.raw_response == mock_response_app_version_list


def test_device_cve_get_command(client, requests_mock):
    """
        When: running zimperium-devices-cve-get
        Given: bundle id to filter by.
        Then: validate the command result returned.
        """
    args = {'cve_id': 'cve_1'}
    mock_response_app_version_list = util_load_json(
        './test_data/device_cve_get.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v2/devices/data-cve-filter', json=mock_response_app_version_list)
    results = device_cve_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.DeviceCVE'
    assert results.outputs[0].get('id') == mock_response_app_version_list.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device CVE' in results.readable_output
    assert results.raw_response == mock_response_app_version_list


def test_devices_os_version_command(client, requests_mock):
    """
        When: running zimperium-devices-os-version command.
        Given: os_vesrion of the device to filter by.
        Then: validate the command result returned.
        """
    args = {'os_version': '9'}
    mock_response_devices_os_version = util_load_json(
        './test_data/devices_os_version.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v2/devices/data-version-filter', json=mock_response_devices_os_version)
    results = devices_os_version_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.DeviceOsVersion'
    assert results.outputs[0].get('id') == mock_response_devices_os_version.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device Os Version' in results.readable_output
    assert results.raw_response == mock_response_devices_os_version


def test_cve_devices_get_command(client, requests_mock):
    """
        When: running zimperium-cve-devices-get command.
        Given: device_id to filter by.
        Then: validate the command result returned.
        """
    args = {'device_id':
            '2a'}
    mock_response_cve_devices_get = util_load_json(
        './test_data/cve_devices_get.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v2/devices/2a/cves', json=mock_response_cve_devices_get)
    results = cve_devices_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.CVEDevice'
    assert results.outputs[0].get('id') == mock_response_cve_devices_get.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device CVE' in results.readable_output
    assert results.raw_response == mock_response_cve_devices_get


def test_policy_group_list_command(client, requests_mock):
    """
        When: running zimperium-policy-group-list command
        Given: no arguments
        Then: validate the command result returned.
        """
    args = {}
    mock_response_policy_group_list = util_load_json(
        './test_data/policy_group_list.json')

    requests_mock.get(f'{SERVER_URL}/mtd-policy/public/v1/groups/page', json=mock_response_policy_group_list)
    results = policy_group_list_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyGroup'
    assert results.outputs[0].get('id') == mock_response_policy_group_list.get('content', [''])[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Policy Group List' in results.readable_output
    assert results.raw_response == mock_response_policy_group_list


def test_policy_privacy_get_command(client, requests_mock):
    """
        When: running zimperium-policy-privacy-get command
        Given: no args
        Then: validate the command result returned.
        """
    args = {'policy_id': 'a2'}
    mock_response_policy_privacy = util_load_json(
        './test_data/policy_privacy.json')

    requests_mock.get(f'{SERVER_URL}/mtd-policy/public/v1/privacy/policies/a2', json=mock_response_policy_privacy)
    results = policy_privacy_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyPrivacy'
    assert results.outputs.get('id') == mock_response_policy_privacy.get('id')
    assert results.outputs_key_field == 'id'
    assert 'Privacy Policy' in results.readable_output
    assert results.raw_response == mock_response_policy_privacy


def test_policy_threat_get_command(client, requests_mock):
    """
        When: running zimperium-policy-threat-get command.
        Given: policy_id to get information about.
        Then: validate the command result returned.
        """
    args = {'policy_id': 'e2'}
    mock_response_policy_threat = util_load_json(
        './test_data/policy_threat.json')

    requests_mock.get(f'{SERVER_URL}/mtd-policy/public/v1/trm/policies/e2', json=mock_response_policy_threat)
    results = policy_threat_get_command(client=client, args=args)
    assert results.outputs_prefix == 'Zimperium.PolicyThreat'
    assert results.outputs.get('id') == mock_response_policy_threat.get('id')
    assert results.outputs_key_field == 'id'
    assert 'Threat Policy' in results.readable_output
    assert results.raw_response == mock_response_policy_threat


def test_policy_phishing_get_command(client, requests_mock):
    """
        When: running zimperium-policy-phishing-get command.
        Given: policy_id to get information about.
        Then: validate the command result returned.
        """
    args = {'policy_id': '25'}
    mock_response_policy_phishing = util_load_json(
        './test_data/policy_phishing.json')

    requests_mock.get(f'{SERVER_URL}/mtd-policy/public/v1/phishing/policies/25', json=mock_response_policy_phishing)
    results = policy_phishing_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyPhising'
    assert results.outputs.get('id') == mock_response_policy_phishing.get('id')
    assert results.outputs_key_field == 'id'
    assert 'Phishing Policy' in results.readable_output
    assert results.raw_response == mock_response_policy_phishing


def test_policy_app_settings_get_command(client, requests_mock):
    """
        When: running zimperium-policy-app-settings-get command.
        Given: policy_id to get information about.
        Then: validate the command result returned.
        """
    args = {'app_settings_policy_id': '9e'}
    mock_response_policy_app_settings = util_load_json(
        './test_data/policy_app_settings.json')

    requests_mock.get(f'{SERVER_URL}/mtd-policy/public/v1/app-settings/policies/9e', json=mock_response_policy_app_settings)
    results = policy_app_settings_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyAppSetting'
    assert results.outputs.get('id') == mock_response_policy_app_settings.get('id')
    assert results.outputs_key_field == 'id'
    assert 'Policy App Settings' in results.readable_output
    assert results.raw_response == mock_response_policy_app_settings


def test_policy_device_inactivity_list_command(client, requests_mock):
    """
        When: running zimperium-policy-device-inactivity-list command.
        Given: team_id to filter by.
        Then: validate the command result returned.
        """
    args = {'team_id': '33'}
    mock_response_policy_device_inactivity_list = util_load_json(
        './test_data/policy_device_inactivity_list.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v1/dormancy/policies', json=mock_response_policy_device_inactivity_list)
    results = policy_device_inactivity_list_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyDeviceInactivity'
    assert results.outputs[0].get('id') == mock_response_policy_device_inactivity_list[0].get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device Inactivity' in results.readable_output
    assert results.raw_response == mock_response_policy_device_inactivity_list


def test_policy_device_inactivity_get_command(client, requests_mock):
    """
        When: running zimperium-policy-device-inactivity-get command.
        Given: policy_id to get information about.
        Then: validate the command result returned.
        """
    args = {'policy_id': 'ff'}
    mock_response_policy_device_inactivity_get = util_load_json(
        './test_data/policy_device_inactivity_get.json')

    requests_mock.get(f'{SERVER_URL}/devices/public/v1/dormancy/policies/ff', json=mock_response_policy_device_inactivity_get)
    results = policy_device_inactivity_get_command(client=client, args=args)

    assert results.outputs_prefix == 'Zimperium.PolicyDeviceInactivity'
    assert results.outputs.get('id') == mock_response_policy_device_inactivity_get.get('id')
    assert results.outputs_key_field == 'id'
    assert 'Device Inactivity' in results.readable_output
    assert results.raw_response == mock_response_policy_device_inactivity_get


# TODO: fetch test
