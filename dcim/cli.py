"""
CLI entry point for the python OpenDCIM api
"""
import argparse
import sys

import dcim.api as api
from dcim.errors import DCIMNotFoundError


def locate(args):
    try:
        result = api.locate(args.device)
    except DCIMNotFoundError:
        print('Device label {} was not found.'.format(args.device))
        sys.exit(1)

    print('{}: {}, {}, U{}'.format(args.device, result['datacenter'],
            result['cabinet'], result['position']))
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    parser_locate = subparsers.add_parser('locate')
    parser_locate.add_argument('device', type=str)
    parser_locate.set_defaults(func=locate)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
