from ncclient import manager
import xmltodict
import sys

HOST = "10.10.20.48"
USER = "developer"
PASS = "C1sco12345"
PORT = 830

def main():
    try:
        with manager.connect(
            host=HOST,
            port=PORT,
            username=USER,
            password=PASS,
            hostkey_verify=False,
            device_params={'name': 'iosxe'},
            timeout=30
        ) as conn:
            print(f"Successfully connected to {HOST}")

            # Pull running config directly without a fragile XML filter
            response = conn.get_config(source='running')
            data = xmltodict.parse(response.xml)

            # Access the native interface container
            native_interfaces = data.get('rpc-reply', {}).get('data', {}).get('native', {}).get('interface', {})

            print("\nInterface                 IP Address          Subnet Mask")
            print("-" * 55)

            for intf_type, intf_entry in native_interfaces.items():
                if isinstance(intf_entry, dict):
                    intf_entry = [intf_entry]
                elif not isinstance(intf_entry, list):
                    continue

                for intf in intf_entry:
                    name = f"{intf_type}{intf.get('name', '')}"
                    ip_data = intf.get('ip', {}).get('address', {}).get('primary', {})
                    ip_address = ip_data.get('address', 'unassigned')
                    netmask = ip_data.get('mask', 'N/A')

                    print(f"{name:<25} {ip_address:<18} {netmask}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()