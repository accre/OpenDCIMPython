"""
CLI entry point for the python OpenDCIM api
"""
import argparse
import sys

from dcim.client import DCIMClient
from dcim.errors import DCIMNotFoundError, DCIMAuthenticationError
from dcim.util import expand_brackets


AUTH_ERROR_MSG = """\
OpenDCIM server authentication failed. Check your .dcim.conf file or
the system /etc/dcim.conf file to ensure that a valid OpenDCIM host
url and credentials have been set.
"""


def locate(args):
    """
    Prints the physical rack location of the specified device, i.e.
    if invoked with ``dcim locate node24`` it will print the datacenter,
    cabinet label, and cabinet position of the device. If the ``--parents``
    option is present, enclosing chassis devices will be listed.

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim locate node[21-23]`` and will print the location of all
    specified devices.

    After printing, the function exits with return code 0 if all devices
    were located or 1 otherwise.
    """
    devices = expand_brackets(args.device)
    error_count = 0
    client = DCIMClient(caching=True)

    for device in devices:
        try:
            result = client.locate(device)
            print('{}: {}, {}, U{}'.format(device, result['datacenter'],
                    result['cabinet'], result['position']))
            if result['parent_devices'] and args.parents:
                print('{}: parent devices: {}'.format(
                    device, result['parent_devices']))
        except DCIMNotFoundError:
            print('Device label {} was not found.'.format(device))
            error_count += 1

    if error_count:
        sys.exit(1)
    else:
        sys.exit(0)


def model(args):
    """
    Prints the make, model, and serial number of the specified device.

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim model node[21-23]`` and will print information about all
    specified devices.

    After printing, the function exits with return code 0 if all devices
    were located or 1 otherwise.
    """
    devices = expand_brackets(args.device)
    error_count = 0
    client = DCIMClient(caching=True)

    for device in devices:
        try:
            result = client.model(device)
            print('{}: {} {} SN: {}'.format(device, result['make'],
                    result['model'], result['serial']))
        except DCIMNotFoundError:
            print('Device label {} was not found.'.format(device))
            error_count += 1

    if error_count:
        sys.exit(1)
    else:
        sys.exit(0)

def showrack(args):
    """
    Print an ASCII-art representation of the cabinet at the specified
    location with the devices contained in each position.

    If the ``--model`` option is present, the make, model, and serial
    number will be printed along with each device.
    """
    try:
        client = DCIMClient(caching=True)
        client.showrack(args.location, display=True, devinfo=args.model)
        sys.exit(0)
    except DCIMNotFoundError:
        print('No cabinet was found at {}.'.format(args.location))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_locate = subparsers.add_parser('locate')
    parser_locate.add_argument('device', type=str)
    parser_locate.add_argument(
        '-p', '--parents',
        action='store_true'
    )
    parser_locate.set_defaults(func=locate)

    parser_model = subparsers.add_parser('model')
    parser_model.add_argument('device', type=str)
    parser_model.set_defaults(func=model)

    parser_showrack = subparsers.add_parser('showrack')
    parser_showrack.add_argument('location', type=str)
    parser_showrack.add_argument(
        '-m', '--model',
        action='store_true'
    )
    parser_showrack.set_defaults(func=showrack)

    args = parser.parse_args()
    try:
        args.func(args)
    except DCIMAuthenticationError:
        print(AUTH_ERROR_MSG)
        sys.exit(1)


if __name__ == '__main__':
    main()
