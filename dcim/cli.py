"""
CLI entry point for the python OpenDCIM api
"""
import argparse
import sys

from dcim.client import DCIMClient
from dcim.errors import DCIMNotFoundError, DCIMAuthenticationError
from dcim.util import expand_hostlist
from dcim.__version__ import __version__


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

    To identify a device by serial number rather than label/host, use
    the option ``--serial`` or ``-s``.

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim locate node[21-23]`` and will print the location of all
    specified devices.

    After printing, the function exits with return code 0 if all devices
    were located or 1 otherwise.
    """
    if args.serial:
        devices = [args.device]
        identifier = 'SerialNo'
    else:
        devices = expand_hostlist(args.device)
        identifier = 'Label'

    error_count = 0
    client = DCIMClient(caching=True)

    for device in devices:
        try:
            result = client.locate(device, identifier=identifier)
            print('{}: {}, {}, U{}'.format(
                    result['label'], result['datacenter'],
                    result['cabinet'], result['position']))
            if result['parent_devices'] and args.parents:
                print('{}: parent devices: {}'.format(
                    device, result['parent_devices']))
        except DCIMNotFoundError:
            print('Device {} {} was not found.'.format(identifier, device))
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
    devices = expand_hostlist(args.device)
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


def status(args):
    """
    Prints the status and owner of the specified device.

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim model node[21-23]`` and will print information about all
    specified devices.

    After printing, the function exits with return code 0 if all devices
    were located or 1 otherwise.
    """
    devices = expand_hostlist(args.device)
    error_count = 0
    client = DCIMClient(caching=True)

    for device in devices:
        try:
            result = client.status(device)
            print('{}: status {}, owner {}'.format(device, result['status'],
                    result['owner']))
        except DCIMNotFoundError:
            print('Device label {} was not found.'.format(device))
            error_count += 1

    if error_count:
        sys.exit(1)
    else:
        sys.exit(0)


def relabel(args):
    """
    Relabels a device with current label "device" with label "newlabel"
    """
    client = DCIMClient(caching=True)
    try:
        result = client.relabel_device(args.device, args.newlabel)
    except DCIMNotFoundError:
        print('Device label {} was not found.'.format(device))
        sys.exit(1)
    sys.exit(0)


def setstatus(args):
    """
    Sets the status field of the specified device(s).

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim setstatus node[21-23] Provisioning`` and will set the status for
    all specified devices.

    After modifying, the function exits with return code 0 if all devices
    were successfully modified or 1 otherwise.
    """
    devices = expand_hostlist(args.devices)
    error_count = 0
    client = DCIMClient()

    for device in devices:
        try:
            result = client.set_device_status(device, args.status)
        except DCIMNotFoundError:
            print('Device label {} was not found.'.format(device))
            error_count += 1

    if error_count:
        sys.exit(1)
    else:
        sys.exit(0)


def setowner(args):
    """
    Sets the departmental owner field of the specified device(s).

    For devices labeled with consecutive numbers, i.e. node21, node22,
    node23, the command can be invoked with a range in brackets
    as ``dcim setstatus node[21-23] Provisioning`` and will set the status for
    all specified devices.

    After modifying, the function exits with return code 0 if all devices
    were successfully modified or 1 otherwise.
    """
    devices = expand_hostlist(args.devices)
    error_count = 0
    client = DCIMClient()

    for device in devices:
        try:
            result = client.set_device_owner(device, args.owner)
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

    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help="Print the version of OpenDCIMPython"
    )

    subparsers = parser.add_subparsers()

    parser_locate = subparsers.add_parser('locate', help=locate.__doc__)
    parser_locate.add_argument('device', type=str)
    parser_locate.add_argument(
        '-p', '--parents',
        action='store_true',
        help='Show the enclosing chassis of the device, if any'
    )
    parser_locate.add_argument(
        '-s', '--serial',
        action='store_true',
        help='Identify the device by serial number rather than hostname/label'
    )
    parser_locate.set_defaults(func=locate)

    parser_model = subparsers.add_parser('model', help=model.__doc__)
    parser_model.add_argument('device', type=str)
    parser_model.set_defaults(func=model)

    parser_status = subparsers.add_parser('status', help=status.__doc__)
    parser_status.add_argument('device', type=str)
    parser_status.set_defaults(func=status)

    parser_relabel = subparsers.add_parser('relabel', help=relabel.__doc__)
    parser_relabel.add_argument('device', type=str)
    parser_relabel.add_argument('newlabel', type=str)
    parser_relabel.set_defaults(func=relabel)

    parser_setstatus = subparsers.add_parser('setstatus', help=setstatus.__doc__)
    parser_setstatus.add_argument('devices', type=str)
    parser_setstatus.add_argument('status', type=str)
    parser_setstatus.set_defaults(func=setstatus)

    parser_setowner = subparsers.add_parser('setowner', help=setowner.__doc__)
    parser_setowner.add_argument('devices', type=str)
    parser_setowner.add_argument('owner', type=str)
    parser_setowner.set_defaults(func=setowner)

    parser_showrack = subparsers.add_parser('showrack', help=showrack.__doc__)
    parser_showrack.add_argument('location', type=str)
    parser_showrack.add_argument(
        '-m', '--model',
        action='store_true',
        help='Print the make, model, and SN of each device'
    )
    parser_showrack.set_defaults(func=showrack)

    args = parser.parse_args()

    if args.version:
        print('OpenDCIMPython version {0}'.format(__version__))
        sys.exit(0)

    if not hasattr(args, 'func') or not args.func:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except DCIMAuthenticationError:
        print(AUTH_ERROR_MSG)
        sys.exit(1)


if __name__ == '__main__':
    main()
