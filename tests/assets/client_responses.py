"""
Provides requests.Response objects for pre-populating a DCIMClient cache
to use for unit testing.

Responses are constructed corresponding to an example datacenter room
'Foo 101' with a single cabinet 'A01' of height 8U and five devices:

DevID 1: 'node101' - 1U server in position 1
DevID 2: 'node102' - 1U server in position 2
DevID 3: 'chassisA' - 2U chassis in position 4
DevID 4: 'node103' - blade server in chassisA
DevID 5: 'node104' - blade server in chassisA

"""
import json
from copy import deepcopy
from io import BytesIO

from requests import Response

DEFAULT_CABINET = {
    'AssignedTo': '1',
    'CabRowID': '1',
    'CabinetHeight': '10',
    'CabinetID': '1',
    'DataCenterID': '1',
    'DataCenterName': 'Foo 101',
    'FrontEdge': 'Left',
    'InstallationDate': '2017-03-18',
    'Keylock': '',
    'Location': 'A01',
    'LocationSortable': 'A01',
    'MapX1': '386',
    'MapX2': '439',
    'MapY1': '816',
    'MapY2': '847',
    'MaxKW': '0',
    'MaxWeight': '0',
    'Model': '',
    'Notes': '',
    'Rights': 'Read',
    'U1Position': 'Bottom',
    'ZoneID': '0'
}

DEFAULT_DATACENTER = {
    'Administrator': '',
    'ContainerID': '0',
    'DataCenterID': '1',
    'DeliveryAddress': '',
    'DrawingFileName': 'foo-101.png',
    'EntryLogging': '0',
    'MapX': '0',
    'MapY': '0',
    'MaxkW': '0',
    'Name': 'Foo 101',
    'SquareFootage': '4000',
    'U1Position': 'Default',
    'dcconfig': None
}

DEFAULT_DEVICE = {
    'APIPassword': '',
    'APIPort': 0,
    'APIUserName': '',
    'APIUsername': '',
    'AssetTag': '',
    'AuditStamp': '0000-00-00 00:00:00',
    'BackSide': 0,
    'Cabinet': 1,
    'ChassisSlots': 0,
    'CustomValues': None,
    'DeviceID': 1,
    'DeviceType': 'Server',
    'EscalationID': 0,
    'EscalationTimeID': 0,
    'FirstPortNum': 0,
    'HalfDepth': 0,
    'Height': 1,
    'Hypervisor': 'ESX',
    'InstallDate': '2017-08-03',
    'Label': 'node123',
    'MfgDate': '2017-09-15',
    'NominalWatts': 550,
    'Notes': '',
    'Owner': 2,
    'ParentDevice': 0,
    'Ports': 3,
    'Position': 1,
    'PowerSupplyCount': 2,
    'PrimaryContact': 0,
    'PrimaryIP': '192.168.0.1',
    'ProxMoxRealm': '',
    'RearChassisSlots': 0,
    'Reservation': 0,
    'Rights': 'Read',
    'SNMPCommunity': '',
    'SNMPFailureCount': 0,
    'SNMPVersion': '2c',
    'SerialNo': 'ABCDEFGH',
    'TemplateID': 1,
    'WarrantyCo': '',
    'WarrantyExpire': '2022-07-27',
    'Weight': 48,
    'v3AuthPassphrase': '',
    'v3AuthProtocol': 'MD5',
    'v3PrivPassphrase': '',
    'v3PrivProtocol': 'DES',
    'v3SecurityLevel': 'noAuthNoPriv'
}

DEFAULT_MANUFACTURER = {
    'GlobalID': '0',
    'ManufacturerID': '1',
    'Name': 'Ringo',
    'SubscribeToUpdates': '0'
}

DEFAULT_TEMPLATE = {
    'ChassisSlots': 0,
    'CustomValues': [],
    'DeviceType': 'Server',
    'FrontPictureFile': 'ringo-r730-front.png',
    'GlobalID': 1,
    'Height': 1,
    'KeepLocal': 0,
    'ManufacturerID': 1,
    'Model': 'PowerDrum R730',
    'Notes': '',
    'NumPorts': 5,
    'PSCount': 2,
    'RearChassisSlots': 0,
    'RearPictureFile': 'ringo-r730-rear.png',
    'SNMPVersion': '2c',
    'ShareToRepo': 0,
    'TemplateID': 1,
    'Wattage': 400,
    'Weight': 85
}


def populate_cache():
    """
    Return a dict of response objects to simulate a set of cached
    responses from an OpenDCIM server. The cache attribute of a
    dcim.DCIMClient object can be set to the return value of this
    function for testing.
    """
    cache = {}

    ringo = deepcopy(DEFAULT_MANUFACTURER)
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'manufacturer': [ringo]},
        200
    )
    cache[('api/v1/manufacturer', frozenset({}.items()))] = r

    r730 = deepcopy(DEFAULT_TEMPLATE)
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'template': r730},
        200
    )
    cache[('api/v1/devicetemplate/1', frozenset({}.items()))] = r

    dcFoo101 = deepcopy(DEFAULT_DATACENTER)
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'datacenter': [dcFoo101]},
        200
    )
    cache[('api/v1/datacenter/1', frozenset({}.items()))] = r

    cabinetA01 = deepcopy(DEFAULT_CABINET)
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'cabinet': [cabinetA01]},
        200
    )
    cache[('api/v1/cabinet/1', frozenset({}.items()))] = r
    cache[('api/v1/cabinet', frozenset({'Location': 'A01'}.items()))] = r

    node101 = deepcopy(DEFAULT_DEVICE)
    node101['DeviceID'] = 1
    node101['Height'] = 1
    node101['Label'] = 'node101'
    node101['Position'] = 1
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': [node101]},
        200
    )
    cache[('api/v1/device', frozenset({'Label': 'node101'}.items()))] = r
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': node101},
        200
    )
    cache[('api/v1/device/1', frozenset({}.items()))] = r

    node102 = deepcopy(DEFAULT_DEVICE)
    node102['DeviceID'] = 2
    node102['Height'] = 1
    node102['Label'] = 'node102'
    node102['Position'] = 2
    node102['TemplateID'] = 0
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': [node102]},
        200
    )
    cache[('api/v1/device', frozenset({'Label': 'node102'}.items()))] = r
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': node102},
        200
    )
    cache[('api/v1/device/2', frozenset({}.items()))] = r

    chassisA = deepcopy(DEFAULT_DEVICE)
    chassisA['DeviceID'] = 3
    chassisA['Height'] = 2
    chassisA['Label'] = 'chassisA'
    chassisA['Position'] = 4
    chassisA['ChassisSlots'] = 4
    chassisA['DeviceType'] = 'Chassis'
    chassisA['TemplateID'] = 2
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': [chassisA]},
        200
    )
    cache[('api/v1/device', frozenset({'Label': 'chassisA'}.items()))] = r
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': chassisA},
        200
    )
    cache[('api/v1/device/3', frozenset({}.items()))] = r

    node103 = deepcopy(DEFAULT_DEVICE)
    node103['DeviceID'] = 4
    node103['Height'] = 1
    node103['Label'] = 'node103'
    node103['Position'] = 1
    node103['TemplateID'] = 3
    node103['ParentDevice'] = 3
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': [node103]},
        200
    )
    cache[('api/v1/device', frozenset({'Label': 'node103'}.items()))] = r
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': node103},
        200
    )
    cache[('api/v1/device/4', frozenset({}.items()))] = r

    node104 = deepcopy(DEFAULT_DEVICE)
    node104['DeviceID'] = 4
    node104['Height'] = 1
    node104['Label'] = 'node104'
    node104['Position'] = 1
    node104['TemplateID'] = 3
    node104['ParentDevice'] = 3
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': [node104]},
        200
    )
    cache[('api/v1/device', frozenset({'Label': 'node104'}.items()))] = r
    r = construct_json_response(
        {'error': False, 'errorcode': 200, 'device': node104},
        200
    )
    cache[('api/v1/device/4', frozenset({}.items()))] = r

    cab_devices = [node102, node104, chassisA, node101, node103]
    r = construct_json_response(
        {'error': 'False', 'errorcode': 200, 'device': cab_devices},
        200
    )
    cache[('api/v1/device', frozenset({'Cabinet': '1'}.items()))] = r

    return cache


def construct_json_response(input_dict, status_code):
    """
    Return a requests.Response object with content-type application/json
    from a given dict and status code
    """
    resp = Response()
    resp.status_code = status_code
    resp.headers['content-type'] = 'application/json'
    resp.raw = BytesIO(json.dumps(input_dict).encode('utf-8'))
    return resp
