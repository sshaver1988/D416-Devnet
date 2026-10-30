#!/usr/bin/env python3
"""
Script to authenticate with Cisco DNA Center (Catalyst Center) devnet sandbox
and retrieve device and client enrichment details.
"""

import argparse
from pprint import pprint

from dnacentersdk import DNACenterAPI

# Cisco DevNet Sandbox credentials
# Always-On Catalyst Center (DNA Center) Sandbox
DNAC_URL = "https://sandboxdnac.cisco.com"
DNAC_USERNAME = "devnetuser"
DNAC_PASSWORD = "Cisco123!"

def main():
    """
    Main function to authenticate and get devices from DNA Center
    """
    parser = argparse.ArgumentParser(
        description="Retrieve Catalyst Center devices and client details."
    )
    parser.add_argument(
        "--entity-type",
        choices=("network_user_id", "mac_address"),
        help="Client identifier type for enrichment details; prompted if omitted.",
    )
    parser.add_argument(
        "--entity-value",
        help="User ID or client MAC address to enrich; prompted if omitted.",
    )
    args = parser.parse_args()

    if args.entity_type is None:
        print("Select client identifier type:")
        print("1. MAC address")
        print("2. Network user ID")
        choice = input("Enter 1 or 2: ").strip()
        entity_types = {"1": "mac_address", "2": "network_user_id"}
        if choice not in entity_types:
            parser.error("choose 1 (MAC address) or 2 (network user ID)")
        args.entity_type = entity_types[choice]

    if args.entity_value is None:
        args.entity_value = input("Enter the client MAC address or network user ID: ").strip()
        if not args.entity_value:
            parser.error("the client identifier cannot be empty")

    print("Connecting to Cisco DNA Center...")
    
    # Create a DNACenterAPI connection object
    # Using verify=False to bypass SSL certificate verification
    api = DNACenterAPI(username=DNAC_USERNAME,
                      password=DNAC_PASSWORD,
                      base_url=DNAC_URL,
                      verify=False)
    
    print("Successfully authenticated with DNA Center")
    
    # Get the list of devices
    print("\nRetrieving list of devices...")
    devices = api.devices.get_device_list()

    # Retrieve enriched details for clients connected to the network.
    print("\nRetrieving client details...")
    clients = api.clients.get_client_enrichment_details(
        headers={
            "entity_type": args.entity_type,
            "entity_value": args.entity_value,
            "__persistbapioutput": True,
        }
    )

    print("\nClient enrichment details:")
    pprint(clients)

    # Print the devices
    print(f"\nFound {len(devices.response)} devices:")
    print("-" * 80)
    
    for device in devices.response:
        print(f"Device Name: {device.hostname}")
        print(f"Device Type: {device.type}")
        print(f"Management IP: {device.managementIpAddress}")
        print(f"Platform ID: {device.platformId}")
        print(f"Serial Number: {device.serialNumber}")
        print(f"Software Version: {device.softwareVersion}")
        print(f"Up Time: {device.upTime}")
        print(f"Status: {device.reachabilityStatus}")
        print("-" * 80)
    
if __name__ == "__main__":
    main() 