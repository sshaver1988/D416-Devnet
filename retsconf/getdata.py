"""Fetch operational interface details from a device using RESTCONF.

Run with ``python retsconf/getdata.py``. Set ``RESTCONF_PASSWORD`` to avoid
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
INTERFACES_STATE_PATH = "/restconf/data/ietf-interfaces:interfaces-state"
INTERFACES_CONFIG_PATH = "/restconf/data/ietf-interfaces:interfaces"


def get_interface_list(data, container_name):
    container = data.get(container_name, data)
    if not isinstance(container, dict):
        raise ValueError(f"RESTCONF response does not contain {container_name}")
    interfaces = container.get("interface", [])
    if not isinstance(interfaces, list):
        raise ValueError("RESTCONF interface data is not a list")
    return {interface.get("name", "unknown"): interface for interface in interfaces}


def get_ipv4_address(interface):
    ipv4 = interface.get("ietf-ip:ipv4", interface.get("ipv4", {}))
    if not isinstance(ipv4, dict):
        return "unassigned"
    addresses = ipv4.get("address", [])
    if isinstance(addresses, dict):
        addresses = [addresses]
    for address in addresses:
        if isinstance(address, dict) and address.get("ip"):
            return address["ip"]
    return "unassigned"


def format_interfaces(state_data, config_data):
    state_interfaces = get_interface_list(
        state_data, "ietf-interfaces:interfaces-state"
    )
    config_interfaces = get_interface_list(config_data, "ietf-interfaces:interfaces")

    rows = []
    for name, interface in state_interfaces.items():
        configured_interface = config_interfaces.get(name, {})
        ip_address = get_ipv4_address(configured_interface)
        if ip_address == "unassigned":
            ip_address = get_ipv4_address(interface)

        admin_status = interface.get("admin-status", "unknown").lower()
        oper_status = interface.get("oper-status", "unknown").lower()
        status = "administratively down" if admin_status == "down" else oper_status
        if status not in ("up", "down", "administratively down"):
            status = "unknown"
        protocol = oper_status if oper_status in ("up", "down") else "unknown"
        rows.append((name, ip_address, status, protocol))

    headers = ("Interface", "IP-Address", "Status", "Protocol")
    widths = tuple(
        max(len(header), *(len(row[index]) for row in rows))
        if rows else len(header)
        for index, header in enumerate(headers)
    )
    lines = [
        "  ".join(header.ljust(width) for header, width in zip(headers, widths)),
        "  ".join("-" * width for width in widths),
    ]
    lines.extend(
        "  ".join(value.ljust(width) for value, width in zip(row, widths)).rstrip()
        for row in rows
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve operational interface details over RESTCONF."
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

    def make_request(path):
        return Request(
            f"https://{args.host}{path}",
            headers={
                "Accept": "application/yang-data+json",
                "Authorization": f"Basic {credentials}",
            },
        )

    if args.verify_tls:
        tls_context = ssl.create_default_context()
    else:
        tls_context = ssl._create_unverified_context()

    try:
        with urlopen(
            make_request(INTERFACES_STATE_PATH), timeout=15, context=tls_context
        ) as response:
            interface_state = json.load(response)
        with urlopen(
            make_request(INTERFACES_CONFIG_PATH), timeout=15, context=tls_context
        ) as response:
            interface_config = json.load(response)
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
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        print(f"RESTCONF returned invalid JSON: {error}", file=sys.stderr)
        return 1

    try:
        print(format_interfaces(interface_state, interface_config))
    except (AttributeError, ValueError) as error:
        print(f"Could not format RESTCONF interface data: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())