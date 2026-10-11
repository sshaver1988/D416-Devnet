import json

# Load the saved configuration JSON
with open("cat8kv_config.json", "r") as f:
    config_data = json.load(f)

print(f"{'Interface':<25} {'IP Address':<18} {'Subnet Mask'}")
print("-" * 60)

# 1. Parse via Cisco Native Model (under data -> native -> interface)
native_interfaces = config_data.get("native", {}).get("interface", {})

for intf_type, intf_entry in native_interfaces.items():
    # Handle single interface (dict) vs multiple interfaces (list)
    if isinstance(intf_entry, dict):
        intf_entry = [intf_entry]
    elif not isinstance(intf_entry, list):
        continue

    for intf in intf_entry:
        name = f"{intf_type}{intf.get('name', '')}"
        
        # Extract IP address and mask if present
        ip_info = intf.get("ip", {}).get("address", {}).get("primary", {})
        ip_addr = ip_info.get("address", "unassigned")
        netmask = ip_info.get("mask", "N/A")
        
        print(f"{name:<25} {ip_addr:<18} {netmask}")