from ncclient import manager
import xml.dom.minidom
import sys

# XML configuration payload to create Loopback2 with Cisco native YANG
LOOPBACK_CONFIG = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <Loopback>
        <name>2</name>
        <description>Configured via NETCONF</description>
        <ip>
          <address>
            <primary>
              <address>192.168.2.1</address>
              <mask>255.255.255.0</mask>
            </primary>
          </address>
        </ip>
      </Loopback>
    </interface>
  </native>
</config>
"""

def connect_to_device(host: str, username: str, password: str, port: int = 830) -> manager.Manager:
    """Establishes a NETCONF connection to the device."""
    try:
        connection = manager.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            device_params={'name': 'iosxe'},
            timeout=30
        )
        return connection
    except Exception as e:
        print(f"Failed to connect to {host}: {e}")
        sys.exit(1)

def configure_loopback(connection: manager.Manager) -> None:
    """Configures Loopback2 interface with the specified IP address."""
    try:
        response = connection.edit_config(target='running', config=LOOPBACK_CONFIG)

        print("\nConfiguration Result:")
        print(xml.dom.minidom.parseString(response.xml).toprettyxml())

        if response.ok:
            print("\nLoopback2 interface configured successfully!")
        else:
            print("\nFailed to configure Loopback2 interface")
    except Exception as e:
        print(f"Error configuring interface: {e}")
        raise

def main():
    device = {
        'host': '10.10.20.48',
        'username': 'developer',
        'password': 'C1sco12345',
        'port': 830
    }

    try:
        with connect_to_device(**device) as conn:
            print(f"Successfully connected to {device['host']}")
            configure_loopback(conn)
    except Exception as e:
        print(f"Script execution failed: {e}")

if __name__ == "__main__":
    main()