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
        return self.session.request(method, url, **kwargs)

    def _get(self, path, **kwargs):
        return self._request('GET', path, **kwargs)

    def locate(self, device):
        """
        Returns the datacenter, cabinet, and position of the specified device.
        Note that if multiple devices share the same label, only the first
        device will be located.

        :param str device: Label of the device to be located

        :returns: The datacenter, cabinet, and position of the device
        :rtype: dict
        """
        resp = self._get('api/v1/device', params={'Label': device})
        try:
            dev_info = resp.json()['device'][0]
        except IndexError:
            raise DCIMNotFoundError(
                'Device label {} was not found.'.format(device)
            ) from None
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
            'position': position
        }


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
