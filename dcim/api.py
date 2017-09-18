"""
The OpenDCIM python convenience API

This API allows for use of client functionality by using a default client
object, similar to how the ``requests`` package will automatically
create a session. This should not be used when function calls are repeated
many times as it will not make use of TLS connection pooling and keep-alive.
"""
from dcim.client import DCIMClient


def locate(*args, **kwargs):
    with DCIMClient(caching=True) as client:
        return client.locate(*args, **kwargs)

locate.__doc__ = DCIMClient.locate.__doc__


def model(*args, **kwargs):
    with DCIMClient(caching=True) as client:
        return client.model(*args, **kwargs)

model.__doc__ = DCIMClient.model.__doc__


def showrack(*args, **kwargs):
    with DCIMClient(caching=True) as client:
        return client.showrack(*args, **kwargs)

showrack.__doc__ = DCIMClient.showrack.__doc__
    
