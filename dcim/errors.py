"""
Exception subclasses for dcim specific errors
"""
class DCIMError(Exception):
    """A DCIM related error occurred."""


class DCIMConfigurationError(DCIMError):
    """The DCIM configuration file is missing or incorrect."""


class DCIMAuthenticationError(DCIMError):
    """Could not authenticate with the OpenDCIM server."""


class DCIMNotFoundError(DCIMError, ValueError):
    """The requested DCIM record was not found."""
