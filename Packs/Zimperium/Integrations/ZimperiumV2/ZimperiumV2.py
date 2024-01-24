from typing import Dict, Tuple
from dateparser import parse
import urllib3
from CommonServerPython import *
import demistomock as demisto

# Disable insecure warnings
urllib3.disable_warnings()

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


class Client(BaseClient):
    """
    Client to use in the ZimperiumV2 integration. Overrides BaseClient
    """

    def __init__(self, base_url: str, client_id: str, client_secret: str, verify: bool):
        self._headers = {'Content-Type': 'application/json'}
        super().__init__(base_url=base_url, verify=verify, headers=self._headers)
        access_token = self.auth(client_id, client_secret)
        self._headers['Authorization'] = f'Bearer {access_token}'

    def auth(self, client_id: str, client_secret: str):
        """
        Args:
            client_id: The client id for authentication
            client_secret: The client secret for authentication

        Return:
            access_token for requests authentication.
        """
        body = {
            'clientId': client_id,
            'secret': client_secret,
        }
        response = self._http_request(method='POST', url_suffix='/auth/v1/api_keys/login', json_data=body)
        access_token = response.get('accessToken')
        return access_token

    def users_search(self, size: int, page: int, team_id: Optional[str] = None, user_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            size: response size.
            page: response page.
            user_id:
            team_id:

        Returns:
            Response from API.
        """
        params = assign_params(**{
            'page': page,
            'size': size,
            'teamId': team_id,
        })

        return self._http_request(method='GET', url_suffix=f'auth/public/v1/users/{user_id if user_id else ""}',
                                  headers=self._headers,
                                  params=params)

    def device_search(self, size: int, page: int, after: Optional[str] = None, before: Optional[str] = None,
                      team_name: Optional[str] = None, model: Optional[str] = None, bundle_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            size: response size.
            page: response page.
            after:
            before:
            device_id:
            team_name:
            model:
            bundle_id:

        Returns:
            Response from API.
        """
        params = assign_params(**{
            'page': page,
            'size': size,
            'after': after,
            'before': before,
            'teamName': team_name,
            'model': model,
            'zappInstance.bundleId': bundle_id,
        })

        return self._http_request(method='GET', url_suffix=f'/devices/public/v2/devices/start-scroll',
                                  headers=self._headers, params=params)

    def device_by_id(self, device_id: str):
        """Search events by sending a GET request.

        Args:
            device_id:

        Returns:
            Response from API.
        """

        return self._http_request(method='GET', url_suffix=f'/devices/public/v2/devices/{device_id}',
                                  headers=self._headers)

    def report_get(self, app_version_id: str):
        """Search events by sending a GET request.

        Args:
            app_version_id: The Id to get the app version JSON report.

        Returns:
            Response from API.
        """

        return self._http_request(method='GET', url_suffix=f'/devices/public/v1/appVersions/'
                                                           f'{app_version_id}/json',
                                  headers=self._headers)

    def threat_search(self, after: str, size: Optional[int] = None,
                      page: Optional[int] = 0,
                      before: Optional[str] = None,
                      search_params: Optional[Dict] = None,
                      team_id: Optional[str] = None,
                      operating_system: Optional[str] = None,
                      severity: Optional[List] = None,
                      sort: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            size: response size.
            page: response page.
            after:
            before:
            search_params:
            team_id:
            operating_system:
            severity:
            sort:
        Returns:
            Response from API.
        """
        params = {
            'page': page,
            'size': size,
            'module': 'ZIPS',
            'after': after,
            'before': before,
            'teamId': team_id,
            'os': operating_system,
            'severityName': severity,
            'sort': sort
        }
        params.update(search_params)

        params = assign_params(**params)

        return self._http_request(method='GET', url_suffix='/threats/public/v1/threats', headers=self._headers,
                                  params=params)

    def app_version_list(self, size: int, page: int, bundle_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            bundle_id: The Bundle ID of the app to get its app version.
            size: response size.
            page: response page.

        Returns:
            Response from API.
        """
        params = assign_params(**{
            'query': f'bundleId=={bundle_id}' if bundle_id else None,
            'page': page,
            'size': size,
        })
        return self._http_request(method='GET', url_suffix='/devices/public/v1/appVersions',
                                  headers=self._headers, params=params)

    def device_cve_get(self, cve_id: str, size: int, page: int, after: Optional[str] = None, before: Optional[str] = None,
                       team_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            cve_id:
            size: response size.
            page: response page.
            after:
            before:
            team_id:
        Returns:
            Response from API.
        """
        params = assign_params(**{
            'page': page,
            'size': size,
            'module': 'ZIPS',
            'after': after,
            'before': before,
            'teamId': team_id,
            'cveId': cve_id
        })

        return self._http_request(method='GET', url_suffix='/devices/public/v2/devices/data-cve-filter', headers=self._headers,
                                  params=params)

    def policy_group_list(self, module: Optional[str] = 'ZIPS'):
        """Search events by sending a GET request.

        Returns:
            Response from API.
        """
        params = {
            'module': module if module else 'ZIPS',
        }
        return self._http_request(method='GET', url_suffix='/mtd-policy/public/v1/groups/page',
                                  headers=self._headers, params=params)

    def devices_os_version(self, os_version: str, size: int, page: int, deleted: Optional[bool] = None,
                           os_patch_date: Optional[str] = None,
                           after: Optional[str] = None, before: Optional[str] = None, team_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            os_version:
            deleted:
            os_patch_date:
            size: response size.
            page: response page.
            after:
            before:
            team_id:
        Returns:
            Response from API.
        """
        params = assign_params(**{
            'page': page,
            'size': size,
            'module': 'ZIPS',
            'after': after,
            'before': before,
            'teamId': team_id,
            'osPatchDate': os_patch_date,
            'osVersion': os_version,
            'deleted': deleted,
        })

        return self._http_request(method='GET', url_suffix='/devices/public/v2/devices/data-version-filter',
                                  headers=self._headers,
                                  params=params)

    def cve_devices_get(self, size: int, page: int, device_id: str):
        """Search events by sending a GET request.

        Args:
            device_id:
            size: response size.
            page: response page.
        Returns:
            Response from API.
        """
        params = assign_params(**{
            'page': page,
            'size': size,
            'module': 'ZIPS',
        })

        return self._http_request(method='GET',
                                  url_suffix=f'/devices/public/v2/devices/{device_id}/cves',
                                  headers=self._headers,
                                  params=params)

    def policy_privacy(self, policy_id: str):
        """Search events by sending a GET request.

        Args:
            policy_id:

        Returns:
            Response from API.
        """
        return self._http_request(method='GET',
                                  url_suffix=f'/mtd-policy/public/v1/privacy/policies/{policy_id}',
                                  headers=self._headers)

    def policy_threat(self, policy_id: str):
        """Search events by sending a GET request.

        Args:
            policy_id:

        Returns:
            Response from API.
        """

        return self._http_request(method='GET',
                                  url_suffix=f'/mtd-policy/public/v1/trm/policies/{policy_id}',
                                  headers=self._headers)

    def policy_phishing(self, policy_id: str):
        """Search events by sending a GET request.

        Args:
            policy_id:

        Returns:
            Response from API.
        """

        return self._http_request(method='GET',
                                  url_suffix=f'/mtd-policy/public/v1/phishing/policies/{policy_id}',
                                  headers=self._headers)

    def policy_app_settings(self, app_settings_policy_id: str):
        """Search events by sending a GET request.

        Args:
            app_settings_policy_id:

        Returns:
            Response from API.
        """
        return self._http_request(method='GET',
                                  url_suffix=f'/mtd-policy/public/v1/app-settings/policies/{app_settings_policy_id}',
                                  headers=self._headers)

    def policy_device_inactivity_list(self, size: int, page: int, team_id: Optional[str] = None):
        """Search events by sending a GET request.

        Args:
            team_id:
            size: response size.
            page: response page.

        Returns:
            Response from API.
        """
        params = assign_params(**{
            'teamId': team_id,
            'page': page,
            'size': size,
        })
        return self._http_request(method='GET', url_suffix='/devices/public/v1/dormancy/policies',
                                  headers=self._headers, params=params)

    def policy_device_inactivity_get(self, policy_id: str):
        """Search events by sending a GET request.

        Args:
            policy_id:

        Returns:
            Response from API.
        """
        return self._http_request(method='GET', url_suffix=f'/devices/public/v1/dormancy/policies/{policy_id}',
                                  headers=self._headers)


def test_module(client: Client, first_fetch_time) -> str:
    """
    Performs basic get request to get incident samples
    """
    client.users_search(size=10, page=0)
    if demisto.params().get('isFetch'):
        client.threat_search(size=10, page=0, after=first_fetch_time)

    return 'ok'


def users_search_command(client: Client, args: Dict) -> CommandResults:
    """Search users.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    team_id = args.get('team_id')
    user_id = args.get('user_id')
    size = page_size if page_size else limit

    response = client.users_search(size=size, page=page, team_id=team_id, user_id=user_id)

    content = response.get('content') if not user_id else response

    hr = tableToMarkdown(name='Users search', t=content,
                         headers=['id', 'firstName', 'lastName', 'email', 'created', 'modified', 'teams'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.User',
        outputs=content,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def devices_search_command(client: Client, args: Dict) -> CommandResults:
    """Search devices.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    after = arg_to_datetime(args.get('after'))
    before = arg_to_datetime(args.get('before'))
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    team_name = args.get('team_name')
    model = args.get('model')
    bundle_id = args.get('bundle_id')

    after_srt = after.strftime(DATE_FORMAT) if after else None
    before_str = before.strftime(DATE_FORMAT) if before else None

    size = page_size if page_size else limit

    response = client.device_search(size=size, page=page, after=after_srt,
                                    before=before_str, team_name=team_name,
                                    model=model, bundle_id=bundle_id)

    content = response.get('content')
    hr_output = content.copy()

    for item in hr_output:
        bundle_id_item = dict_safe_get(content, ['zappInstance', 'bundleId'])
        item.update({'bundleId': bundle_id_item})

    hr = tableToMarkdown(name='Device search', t=hr_output,
                         headers=['id', 'model', 'fullType', 'os', 'bundleId', 'created', 'bundleId'],
                         removeNull=True,
                         date_fields=['lastSeen'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.Device',
        outputs=content,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def device_by_id_command(client: Client, args: Dict) -> CommandResults:
    """Search devices.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    device_id = args.get('device_id')

    response = client.device_by_id(device_id=device_id)
    bundle_id_item = dict_safe_get(response, ['zappInstance', 'bundleId'])
    response.update({'bundleId': bundle_id_item})

    hr = tableToMarkdown(name='Device', t=response,
                         headers=['id', 'model', 'fullType', 'os', 'bundleId', 'created', 'bundleId'],
                         removeNull=True,
                         date_fields=['lastSeen'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.Device',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def report_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    app_version_id = args.get('app_version_id')

    response = client.report_get(app_version_id=app_version_id)

    hr = tableToMarkdown(name='Report', t=response.get('report', {}).get('scanDetails'),
                         headers=["riskType", "kind", "description", "location", "importance"],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.Report',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def threat_search_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    after = arg_to_datetime(args.get('after'), required=True, arg_name='after')
    before = arg_to_datetime(args.get('before'))
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    search_params = argToList(args.get('search_params'))
    team_id = args.get('team_id')
    operating_system = args.get('os')
    severity = args.get('severity')

    after_srt = after.strftime(DATE_FORMAT) if after else None
    before_str = before.strftime(DATE_FORMAT) if before else None

    search_params_dict = {key: value for param in search_params for key, value in [param.split('=', 1)]}
    size = page_size if page_size else limit

    response = client.threat_search(size=size, page=page, after=after_srt,
                                    before=before_str, search_params=search_params_dict,
                                    team_id=team_id, operating_system=operating_system, severity=severity)

    hr = tableToMarkdown(name='Threat search', t=response.get('content'),
                         headers=['id', 'severityName', 'state', 'vectorName',
                                  'threatTypeName', 'os',
                                  'deviceId', 'teamName'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.Threat',
        outputs=response.get('content'),
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def app_version_list_command(client: Client, args: Dict) -> CommandResults:
    """List app versions.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    bundle_id = args.get('bundle_id')
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))

    size = page_size if page_size else limit

    response = client.app_version_list(bundle_id=bundle_id, size=size, page=page)

    hr = tableToMarkdown(name='App Version List', t=response.get('content'),
                         headers=['id', 'name', 'bundleId', 'version', 'platform',
                                  'security', 'classification', 'created', 'updatedOn'],
                         date_fields=['created', 'updatedOn'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.AppVersion',
        outputs=response.get('content'),
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def device_cve_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    cve_id = args.get('cve_id')
    after = arg_to_datetime(args.get('after'))
    before = arg_to_datetime(args.get('before'))
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    team_id = args.get('team_id')

    after_srt = after.strftime(DATE_FORMAT) if after else None
    before_str = before.strftime(DATE_FORMAT) if before else None

    size = page_size if page_size else limit

    response = client.device_cve_get(cve_id=cve_id, size=size, page=page, after=after_srt,
                                     before=before_str, team_id=team_id, )

    hr = tableToMarkdown(name='Device CVE', t=response.get('content'),
                         headers=['id', 'teamId', 'os'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.DeviceCVE',
        outputs=response.get('content'),
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def devices_os_version_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    os_version = args.get('os_version')
    os_patch_date = arg_to_datetime(args.get('os_patch_date'))
    deleted = argToBoolean(args.get('deleted')) if args.get('deleted') else None
    after = arg_to_datetime(args.get('after'))
    before = arg_to_datetime(args.get('before'))
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    team_id = args.get('team_id')

    after_srt = after.strftime(DATE_FORMAT) if after else None
    os_patch_date_str = os_patch_date.strftime('YYYY-MM-DD') if os_patch_date else None
    before_str = before.strftime(DATE_FORMAT) if before else None

    size = page_size if page_size else limit

    response = client.devices_os_version(os_version=os_version, size=size, page=page, after=after_srt,
                                         before=before_str, team_id=team_id, deleted=deleted, os_patch_date=os_patch_date_str)

    hr = tableToMarkdown(name='Device Os Version', t=response.get('content'),
                         headers=['id', 'teamId', 'os'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.DeviceOsVersion',
        outputs=response.get('content'),
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def cve_devices_get_command(client: Client, args: Dict) -> CommandResults:
    """Search CVE for specific device.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    device_id = args.get('device_id')
    size = page_size if page_size else limit

    response = client.cve_devices_get(size=size, page=page, device_id=device_id)

    hr = tableToMarkdown(name='CVE on Device', t=response.get('content'),
                         headers=['id', 'type', 'severity', 'url', 'activeExploit', 'exploitPocUrl'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.CVEDevice',
        outputs=response.get('content'),
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_group_list_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    module = args.get('module')
    response = client.policy_group_list(module)

    hr = tableToMarkdown(name='Policy Group List', t=response.get('content'),
                         headers=['id', 'team', 'name', 'emmConnectionId'],
                         headerTransform=pascalToSpace,
                         removeNull=True)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyGroup',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_privacy_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    policy_id = args.get('policy_id')

    response = client.policy_privacy(policy_id=policy_id)

    hr = tableToMarkdown(name='Privacy Policy', t=response,
                         headers=['id', 'accountId', 'groups',
                                  'name', 'rules', 'created', 'modified', 'team', 'teamId'],
                         headerTransform=pascalToSpace,
                         removeNull=True)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyPrivacy',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_threat_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    policy_id = args.get('policy_id')

    response = client.policy_threat(policy_id=policy_id)

    hr = tableToMarkdown(name='Threat Policy', t=response,
                         headers=['id', 'accountId', 'groups',
                                  'name', 'rules', 'created', 'modified', 'team', 'teamId'],
                         headerTransform=pascalToSpace,
                         removeNull=True)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyThreat',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_phishing_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    policy_id = args.get('policy_id')

    response = client.policy_phishing(policy_id=policy_id)

    hr = tableToMarkdown(name='Phishing Policy', t=response,
                         headers=['id', 'accountId', 'groups',
                                  'name', 'created', 'modified', 'team', 'teamId',
                                  'phishingDetectionAction', 'phishingPolicyType'],
                         headerTransform=pascalToSpace,
                         removeNull=True)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyPhising',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_app_settings_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """

    app_settings_policy_id = args.get('app_settings_policy_id')

    response = client.policy_app_settings(app_settings_policy_id=app_settings_policy_id)

    # TODO: whitch outputs?
    hr = tableToMarkdown(name='Policy App Settings', t=response,
                         headers=['id', 'name', 'teamId'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyAppSetting',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_device_inactivity_list_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    page = arg_to_number(args.get('page', '0'))
    page_size = arg_to_number(args.get('page_size'))
    limit = arg_to_number(args.get('limit', '50'))
    team_id = args.get('team_id')

    size = page_size if page_size else limit

    response = client.policy_device_inactivity_list(size=size, page=page, team_id=team_id)

    hr = tableToMarkdown(name='Device Inactivity List', t=response,
                         headers=['id', 'name', 'teamId'],
                         headerTransform=pascalToSpace)

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyDeviceInactivity',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def policy_device_inactivity_get_command(client: Client, args: Dict) -> CommandResults:
    """Search threats.

    Args:
        client: Client object with request.
        args: Usually demisto.args()

    Returns:
        Outputs.
    """
    policy_id = args.get('policy_id')

    response = client.policy_device_inactivity_get(policy_id=policy_id)

    hr = tableToMarkdown(name='Device Inactivity List', t=response,
                         headers=['id', 'name', 'teamId', 'accountId', 'pendingActivationSettings',
                                  'inactiveAppSettings', 'groups', 'created', 'modified',
                                  ],
                         headerTransform=pascalToSpace,
                         removeNull=True,
                         date_fields=['created', 'modified']
                         )

    command_results = CommandResults(
        outputs_prefix='Zimperium.PolicyDeviceInactivity',
        outputs=response,
        outputs_key_field='id',
        readable_output=hr,
        raw_response=response,
    )
    return command_results


def fetch_incidents(client: Client, last_run: dict, fetch_query: str,
                    first_fetch_time: str, max_fetch: int, look_back: int) -> Tuple[list, dict]:
    """
    This function will execute each interval (default is 1 minute).

    Args:
        client (Client): Zimperium V2 client
        last_run (dateparser.time): The greatest incident created_time we fetched from last fetch
        fetch_query: fetch query to search
        first_fetch_time (dateparser.time): If last_run is None then fetch all incidents since first_fetch_time
        max_fetch: max events to fetch
        look_back: Minutes to look back when fetching

    Returns:
        next_run: This will be last_run in the next fetch-incidents
        incidents: Incidents that will be created
    """
    demisto.debug(f"Last run before the fetch run: {last_run}")
    start_time, end_time = get_fetch_run_time_range(
        last_run=last_run,
        first_fetch=first_fetch_time,
        look_back=look_back,
        date_format=DATE_FORMAT,
    )
    demisto.debug(f"fetching incidents between {start_time=} and {end_time=}")

    search_params = {key: value for param in fetch_query for key, value in [param.split('=', 1)]}
    demisto.debug(f'The query for fetch: {search_params}')

    res = client.threat_search(after=start_time)
    incidents_res = res.get('content', [])
    demisto.debug(f'Got {len(incidents_res)} incidents from the API, before filtering')

    incidents_filtered = filter_incidents_by_duplicates_and_limit(
        incidents_res=incidents_res,
        last_run=last_run,
        fetch_limit=max_fetch,
        id_field='id'
    )
    demisto.debug(f'After filtering, there are {len(incidents_filtered)} incidents')

    incidents: list[dict] = []
    for incident in incidents_filtered:
        occurred = timestamp_to_datestring(incident.get('timestamp'))
        incident['timestamp'] = occurred
        incidents.append({
            'name': f"Threat on Device ID {incident.get('deviceId')}",
            'occurred': occurred,
            'dbotMirrorId': incident.get('id'),
            'severity': incident.get('severity'),
            'rawJSON': json.dumps(incident)
        })

    last_run = update_last_run_object(
        last_run=last_run,
        incidents=incidents,
        fetch_limit=max_fetch,
        start_fetch_time=start_time,
        end_fetch_time=end_time,
        look_back=look_back,
        created_time_field='timestamp',
        id_field='id',
        date_format=DATE_FORMAT,
        increase_last_run_time=True
    )
    demisto.debug(f"Last run after the fetch run: {last_run}")
    return incidents, last_run


def main():
    params = demisto.params()
    client_id = params.get('credentials', {}).get('identifier')
    client_secret = params.get('credentials', {}).get('password')
    base_url = urljoin(params.get('url'), '/api')
    verify = not params.get('insecure', False)

    # fetch params
    max_fetch = arg_to_number(params.get('max_fetch', 50)) or 50
    fetch_query = params.get('fetch_query')
    first_fetch = params.get('fetch_time', '7 days').strip()
    look_back = arg_to_number(params.get('look_back')) or 1

    first_fetch_time = arg_to_datetime(first_fetch)
    first_fetch_time_str = first_fetch_time.strftime(DATE_FORMAT) if first_fetch_time else None

    command = demisto.command()
    args = demisto.args()
    demisto.debug(f'Command being called is {demisto.command()}')
    try:
        client = Client(base_url=base_url, client_id=client_id, client_secret=client_secret, verify=verify)
        if command == 'test-module':
            # This is the call made when pressing the integration Test button.
            return_results(test_module(client, first_fetch_time_str))

        elif command == 'fetch-incidents':
            incidents, next_run = fetch_incidents(
                client=client,
                last_run=demisto.getLastRun(),
                fetch_query=fetch_query,
                first_fetch_time=first_fetch_time_str,
                max_fetch=max_fetch,
                look_back=look_back,
            )
            demisto.setLastRun(next_run)
            demisto.incidents(incidents)

        elif command == 'zimperium-users-search':
            return_results(users_search_command(client, args))

        elif command == 'zimperium-devices-search':
            return_results(devices_search_command(client, args))

        elif command == 'zimperium-device-get-by-id':
            return_results(device_by_id_command(client, args))

        elif command == 'zimperium-report-get':
            return_results(report_get_command(client, args))

        elif command == 'zimperium-threat-search':
            return_results(threat_search_command(client, args))

        elif command == 'zimperium-app-version-list':
            return_results(app_version_list_command(client, args))

        elif command == 'zimperium-devices-cve-get':
            return_results(device_cve_get_command(client, args))

        elif command == 'zimperium-devices-os-version':
            return_results(devices_os_version_command(client, args))

        elif command == 'zimperium-cve-devices-get':
            return_results(cve_devices_get_command(client, args))

        # TODO: issue with the API call
        # elif command == 'zimperium-vulnerability-get':
        #     return_results(vulnerability_get_command(client, args))

        elif command == 'zimperium-policy-group-list':
            return_results(policy_group_list_command(client, args))

        elif command == 'zimperium-policy-privacy-get':
            return_results(policy_privacy_get_command(client, args))

        elif command == 'zimperium-policy-threat-get':
            return_results(policy_threat_get_command(client, args))

        elif command == 'zimperium-policy-phishing-get':
            return_results(policy_phishing_get_command(client, args))

        elif command == 'zimperium-policy-app-settings-get':
            return_results(policy_app_settings_get_command(client, args))

        elif command == 'zimperium-policy-device-inactivity-list':
            return_results(policy_device_inactivity_list_command(client, args))

        elif command == 'zimperium-policy-device-inactivity-get':
            return_results(policy_device_inactivity_get_command(client, args))
        else:
            raise NotImplementedError(f'Command "{command}" is not implemented.')

    except Exception as err:
        return_error(str(err), err)


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
