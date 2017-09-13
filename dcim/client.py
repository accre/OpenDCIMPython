"""
Client wrapper for interactions with the OpenDCIM server and
configuration.
"""
import configparser
import os.path

import requests
import urllib3

from dcim.errors import (
    DCIMConfigurationError,
    DCIMNotFoundError,
    DCIMAuthenticationError
)
from dcim.util import draw_rack


client_config = None


class DCIMClient(object):
    """
    OpenDCIM Client object to utilize requests.Session connection-pooling
    """
    def __init__(self):
        _maybe_set_configuration()

        self.session = requests.Session()
        self.session.auth = (
            client_config['username'],
            client_config['password']
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.session.close()

    def _request(self, method, path, **kwargs):
        url = '{}/{}'.format(client_config['baseurl'], path)
        if 'verify' not in kwargs and not client_config['ssl_verify']:
            kwargs['verify'] = False

        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            raise DCIMAuthenticationError(
                'OpenDCIM authentication failed, server response: {}'
                .format(resp.text)
            )
        return resp

    def _get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def locate(self, device):
        """
        Returns the datacenter, cabinet, and rack position of the specified
        device, as well as a list of parent devices.

        Note that if multiple devices share the same label, only the first
        device will be located.

        :param str device: Label of the device to be located

        :returns: The datacenter, cabinet, and rack position of the device,
            and a list of parent devices.
        :rtype: dict
        """
        resp = self._get('api/v1/device', params={'Label': device})
        try:
            dev_info = resp.json()['device'][0]
        except IndexError:
            raise DCIMNotFoundError(
                'Device label {} was not found.'.format(device)
            ) from None

        parents = []
        while dev_info['ParentDevice']:
            resp = self._get(
                'api/v1/device/{}'.format(dev_info['ParentDevice'])
            )
            dev_info = resp.json()['device']
            parents.append(dev_info['Label'])

        position = dev_info['Position']

        resp = self._get('api/v1/cabinet/{}'.format(dev_info['Cabinet']))
        cab_info = resp.json()['cabinet'][0]
        location = cab_info['Location']
        
        resp = self._get(
            'api/v1/datacenter/{}'.format(cab_info['DataCenterID'])
        )
        datacenter = resp.json()['datacenter'][0]['Name']

        return {
            'datacenter': datacenter,
            'cabinet': location,
            'position': position,
            'parent_devices': parents
        }

    def showrack(self, location, display=False, width=72):
        """
        Return and optionally print to standard output an ASCII-art
        representation of the Cabinet specified by the given location.

        Note that if multiple cabinets share the same location only
        the first cabinet found will be displayed.

        :param str location: Location of the cabinet to be shown
        :param bool display: Print results to stdout if True
        :param int width: Width of the cabinet drawing in characters.

        :returns: ASCII-art representation of the cabinet
        :rtype: list(str)
        """
        resp = self._get('api/v1/cabinet', params={'Location': location})
        try:
            cabinet = resp.json()['cabinet'][0]
        except IndexError:
            raise DCIMNotFoundError(
                'Cabinet at location {} was not found.'.format(location)
            ) from None

        height = int(cabinet['CabinetHeight'])
        cabinet_id = cabinet['CabinetID']

        resp = self._get('api/v1/device', params={'Cabinet': cabinet_id})
        devices = resp.json()['device']
        parents = [d for d in devices if not d['ParentDevice']]
        labels = []
        positions = []
        heights = []

        for dev in parents:
            label = dev['Label']
            positions.append(dev['Position'])
            heights.append(dev['Height'])
            children = [
                d for d in devices if d['ParentDevice'] == dev['DeviceID']
            ]
            if children:
                label += ' ('
                label += ', '.join(child['Label'] for child in children)
                label += ')'
            labels.append(label)

        return draw_rack(
            height,
            width=width - 8,
            labels=labels,
            positions=positions,
            heights=heights,
            display=display
        )


def configure(baseurl, username, password, ssl_verify=True):
    """
    Set the OpenDCIM client configuration.

    :param str baseurl: base url for the OpenDCIM server
    :param str username: username to access the OpenDCIM server
    :param str password: password to access the OpenDCIM server
    :param bool ssl_verify: Skip ssl certificate verification if set to False
    """
    global client_config
    client_config = {
        'baseurl': baseurl,
        'username': username,
        'password': password
    }
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _maybe_set_configuration():
    """
    Try to set the client configuration if it is not set by reading the
    user or system configuration file.
    """
    global client_config
    if client_config is not None:
        return

    conf_file = os.path.expanduser('~/.dcim.conf')
    if not os.path.isfile(conf_file):
        conf_file = '/etc/dcim.conf'

    client_config = _parse_config_file(conf_file)


def _parse_config_file(filename):
    """
    Parse the specified configuration file

    :returns: Configured baseurl, username, and password
    :rtype: dict
    """
    try:
        config = configparser.ConfigParser()
        config.read(filename)
        ssl_verify = True
        if config['dcim'].get('ssl_verify', '').lower() == 'false':
            ssl_verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return {
            'baseurl': config['dcim']['baseurl'],
            'username': config['dcim']['username'],
            'password': config['dcim']['password'],
            'ssl_verify': ssl_verify
        }
    except Exception:
        raise DCIMConfigurationError()
