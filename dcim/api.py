"""
The OpenDCIM python convenience API

This API allows for use of client functionality by using a default client
object, similar to how the ``requests`` package will automatically
create a session. This should not be used when function calls are repeated
many times as it will not make use of TLS connection pooling and keep-alive.
"""
from dcim.client import DCIMClient


def locate(device):
    with DCIMClient() as client:
        return client.locate(device)

locate.__doc__ = DCIMClient.locate.__doc__


def showrack(location, display=False, width=72):
    with DCIMClient() as client:
        return client.showrack(location, display=display, width=width)

showrack.__doc__ = DCIMClient.showrack.__doc__
    
