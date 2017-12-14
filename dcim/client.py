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
    and provide an interface to the OpenDCIM API with helper methods for
    common tasks.
    """
    def __init__(self, caching=False):
        """
        Set up a requests.Session client for OpenDCIM server communication.
        Optionally cache GET requests.

        :param bool caching: Cache the results of GET requests to the
            server in memory if set to True
        """
        _maybe_set_configuration()

        self.session = requests.Session()
        self.session.auth = (
            client_config['username'],
            client_config['password']
        )
        self.caching = caching
        self.cache = {}

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
        """
        Perform a GET request with the given path or return result already
        held in the cache. The cache is keyed using the path and possible
        querystring arguments.
        """
        if self.caching:
            key = (path, frozenset(kwargs.get('params', {}).items()))
            if key in self.cache:
                return self.cache[key]
            else:
                self.cache[key] = self._request('GET', path, **kwargs)
                return self.cache[key]

        return self._request('GET', path, **kwargs)

    def get_device(self, device):
        """
        Return device information for a device by label.

        Note that if multiple devices share the same label, only the first
        device will be returned.

        :param str device: Label of the device
        :returns: Information about the device
        :rtype: dict
        """
        resp = self._get('api/v1/device', params={'Label': device})
        try:
            return resp.json()['device'][0]
        except IndexError:
            raise DCIMNotFoundError(
                'Device label {} was not found.'.format(device)
            ) from None

    def get_all_devices(self):
        """
        Return device information for all devices in OpenDCIM

        :returns: Information about all devices
        :rtype: list(dict)
        """
        resp = self._get('api/v1/device')
        return resp.json()['device']

    def update_device_by_id(self, device_id, updates):
        """
        Update fields of a device given by DeviceID with values
        specifed in a dict.

        :param str|int device_id: DCIM id of a device to update
        :param dict updates: fields to be updated and new values
        """
        resp = self._request(
            'POST',
            'api/v1/device/{}'.format(device_id),
            json=updates
        )
        resp.raise_for_status()

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
        dev_info = self.get_device(device)

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

    def get_cabinet(self, location):
        """
        Return cabinet information for a cabinet by location.

        Note that if multiple cabinets share the same label, only the first
        cabinet will be returned.

        :param str cabinet: Location of the cabinet
        :returns: Information about the cabinet
        :rtype: dict
        """
        resp = self._get('api/v1/cabinet', params={'Location': location})
        try:
            return resp.json()['cabinet'][0]
        except IndexError:
            raise DCIMNotFoundError(
                'Cabinet at location {} was not found.'.format(location)
            ) from None

    def get_cabinet_devices(self, location, nochildren=False):
        """
        Return a list of device information dicts for a cabinet
        specified by location.

        Note that if multiple cabinets share the same label, only the first
        cabinet will be returned.

        :param str cabinet: Location of the cabinet
        :param bool nochildren: If True, do not return devices with
            a parent device (default False)

        :returns: Information about all devices in the cabinet
        :rtype: list(dict)
        """ 
        cabinet = self.get_cabinet(location)
        cabinet_id = cabinet['CabinetID']

        resp = self._get('api/v1/device', params={'Cabinet': cabinet_id})
        devices = resp.json()['device']
        if nochildren:
            return [d for d in devices if not d['ParentDevice']]
        return devices

    def showrack(self, location, display=False, width=72, devinfo=False):
        """
        Return and optionally print to standard output an ASCII-art
        representation of the Cabinet specified by the given location.

        Note that if multiple cabinets share the same location only
        the first cabinet found will be displayed.

        :param str location: Location of the cabinet to be shown
        :param bool display: Print results to stdout if True
        :param int width: Width of the cabinet drawing in characters.
        :param str devinfo: Show make, model, and serial of device if True

        :returns: ASCII-art representation of the cabinet
        :rtype: list(str)
        """
        cabinet = self.get_cabinet(location)
        height = int(cabinet['CabinetHeight'])
        cabinet_id = cabinet['CabinetID']

        devices = self.get_cabinet_devices(location)
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
            if devinfo:
                info = self.model(dev['Label'], dev_info=dev)
                if info['make'] is None:
                    info['make'] = 'Unknown Model'
                    info['model'] = ''
                label += ' [{} {} SN: {}]'.format(
                    info['make'], info['model'], info['serial']
                )
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

    def model(self, device, dev_info=None):
        """
        Return a dict containing the make, model, and serial number
        of the device given by label. If the device has no template
        the make and model are given as None.

        :param str device: label of the device to query
        :param dict dev_info: Device information already retrieved from
            the OpenDCIM. If None, the information will be fetched.

        :returns: make, model, and serial for the device
        :rtype: dict
        """
        if dev_info is None:
            dev_info = self.get_device(device)
        template = dev_info['TemplateID']
        serial = dev_info['SerialNo']
        if not template:
            return {'make': None, 'model': None, 'serial': serial}

        resp = self._get('api/v1/manufacturer')
        makes = {
            int(m['ManufacturerID']): m['Name']
            for m in resp.json()['manufacturer']
        }

        resp = self._get('api/v1/devicetemplate/{}'.format(template))
        template_info = resp.json()['template']
        return {
            'make': makes[int(template_info['ManufacturerID'])],
            'model': template_info['Model'],
            'serial': serial
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
    if not os.path.isfile(conf_file):
        conf_file = '/usr/local/etc/dcim.conf'

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
