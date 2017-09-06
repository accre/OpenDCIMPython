"""
The OpenDCIM python convenience API
"""
from dcim.client import DCIMClient


def locate(device):
    with DCIMClient() as client:
        return client.locate(device)

locate.__doc__ = DCIMClient.locate.__doc__
