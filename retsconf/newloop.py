"""Create the Loopback3 interface on an IOS XE device using RESTCONF.

Run with ``python retsconf/newloop.py``. Set ``RESTCONF_PASSWORD`` to avoid
the interactive password prompt.
"""

import argparse
import base64
import getpass
import json
import os
import ssl
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_HOST = "10.10.20.48"
DEFAULT_USERNAME = "developer"
INTERFACE_PATH = (
    "/restconf/data/ietf-interfaces:interfaces/interface=Loopback3"
)
LOOPBACK_CONFIG = {
    "ietf-interfaces:interface": {
        "name": "Loopback3",
        "type": "iana-if-type:softwareLoopback",
        "enabled": True,
        "ietf-ip:ipv4": {
            "address": [
                {
                    "ip": "33.33.33.33",
                    "netmask": "255.255.255.255",
                }
            ]
        },
    }
}


def main():
    parser = argparse.ArgumentParser(
        description="Create Loopback3 on an IOS XE device over RESTCONF."
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("RESTCONF_HOST", DEFAULT_HOST),
        help="Device hostname or IP address (default: %(default)s)",
    )
    parser.add_argument(
        "--username",
        default=os.environ.get("RESTCONF_USERNAME", DEFAULT_USERNAME),
        help="RESTCONF username (default: %(default)s)",
    )
    parser.add_argument(
        "--verify-tls",
        action="store_true",
        help="Verify the device TLS certificate (disabled by default for this lab device)",
    )
    args = parser.parse_args()

    password = os.environ.get("RESTCONF_PASSWORD")
    if password is None:
        password = getpass.getpass("RESTCONF password: ")

    credentials = base64.b64encode(
        f"{args.username}:{password}".encode("utf-8")
    ).decode("ascii")
    request = Request(
        f"https://{args.host}{INTERFACE_PATH}",
        data=json.dumps(LOOPBACK_CONFIG).encode("utf-8"),
        headers={
            "Accept": "application/yang-data+json",
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/yang-data+json",
        },
        method="PUT",
    )
    tls_context = (
        ssl.create_default_context()
        if args.verify_tls
        else ssl._create_unverified_context()
    )

    try:
        with urlopen(request, timeout=15, context=tls_context) as response:
            print(
                f"Loopback3 configured successfully "
                f"(HTTP {response.status})."
            )
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="replace").strip()
        message = f"RESTCONF request failed with HTTP {error.code}"
        if details:
            message += f": {details}"
        print(message, file=sys.stderr)
        return 1
    except URLError as error:
        print(f"Could not connect to RESTCONF device: {error.reason}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())