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
    devices = expand_brackets(args.device)
    error_count = 0
    client = DCIMClient()

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

    args = parser.parse_args()
    try:
        args.func(args)
    except DCIMAuthenticationError:
        print(AUTH_ERROR_MSG)
        sys.exit(1)


if __name__ == '__main__':
    main()
