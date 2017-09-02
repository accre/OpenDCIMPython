# OpenDCIMPython

Python wrapper and CLI for OpenDCIM REST API

## CLI Usage

The command line interface requires the user to set either a `.dcim.conf` file
in their home directory or a system config `/etc/dcim.conf`. The
configuration file should have the following format:

    [dcim]
    baseurl = https://opendcim.mydatacenter.com
    username = myuser
    password = SECRET
    ssl_verify = True  # optional
