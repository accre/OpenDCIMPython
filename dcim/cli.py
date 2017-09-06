"""
CLI entry point for the python OpenDCIM api
"""
import argparse
import sys

import dcim.api as api
from dcim.errors import DCIMNotFoundError, DCIMAuthenticationError


AUTH_ERROR_MSG = """\
OpenDCIM server authentication failed. Check your .dcim.conf file or
the system /etc/dcim.conf file to ensure that a valid OpenDCIM host
url and credentials have been set.
"""


def locate(args):
    try:
        result = api.locate(args.device)
    except DCIMNotFoundError:
        print('Device label {} was not found.'.format(args.device))
        sys.exit(1)

    print('{}: {}, {}, U{}'.format(args.device, result['datacenter'],
            result['cabinet'], result['position']))
    if result['parent_devices'] and args.parents:
        print('{}: parent devices: {}'.format(
            args.device, result['parent_devices']))
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
