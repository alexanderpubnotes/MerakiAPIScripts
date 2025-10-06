import json
import ipaddress
import re

# --- Configuration ---
INPUT_FILE = "policy_objects.txt"
OUTPUT_FILE = "policy_objects.json"

def detect_type(value):
    """
    Automatically detect if value is IP, CIDR, or FQDN.
    """
    value = value.strip()
    
    # Try to parse as IP address
    try:
        ipaddress.ip_address(value)
        return "ip"
    except ValueError:
        pass
    
    # Try to parse as CIDR network
    try:
        ipaddress.ip_network(value, strict=False)
        return "cidr"
    except ValueError:
        pass
    
    # Check if it looks like a valid FQDN/domain pattern
    # Allows wildcards, domains, subdomains
    if re.match(r'^(\*\.)?([a-zA-Z0-9-]+\.)*[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$', value):
        return "fqdn"
    
    # If it contains wildcard but didn't match above pattern, still treat as FQDN
    if '*' in value or '?' in value:
        return "fqdn"
    
    # Default to FQDN for anything else (safer assumption)
    return "fqdn"

def parse_text_file(filename):
    """
    Parse text file and create structured policy object groups.
    
    Expected format:
    GroupName1
    value1
    value2
    value3
    
    GroupName2
    value1
    value2
    
    Or with comments:
    # This is a comment
    GroupName1
    192.168.1.1
    10.0.0.0/8
    *.example.com
    """
    groups = {}
    current_group = None
    
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check if this line is a group name (doesn't look like IP/FQDN/CIDR)
            # Group names shouldn't contain dots, slashes, or wildcards
            if not any(char in line for char in ['.', '/', '*', ':']):
                # This is a new group name
                current_group = line
                if current_group not in groups:
                    groups[current_group] = {"objects": []}
                continue
            
            # This is a value (IP, CIDR, or FQDN)
            if current_group is None:
                print(f"Warning: Line {line_num} has value '{line}' but no group defined. Skipping.")
                continue
            
            # Detect type and add to current group
            value_type = detect_type(line)
            groups[current_group]["objects"].append({
                "type": value_type,
                "value": line
            })
    
    return groups

def generate_json(groups, output_file):
    """
    Generate JSON file from parsed groups.
    """
    output = {"groups": groups}
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=4)
    
    return output

def display_summary(groups):
    """
    Display a summary of what was parsed.
    """
    print("\n" + "=" * 70)
    print("Policy Object Groups Summary")
    print("=" * 70)
    
    total_objects = 0
    for group_name, group_data in groups.items():
        object_count = len(group_data["objects"])
        total_objects += object_count
        
        # Count by type
        type_counts = {}
        for obj in group_data["objects"]:
            obj_type = obj["type"]
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
        
        print(f"\n✓ {group_name}")
        print(f"  Total objects: {object_count}")
        for obj_type, count in type_counts.items():
            print(f"    - {obj_type}: {count}")
        
        # Show first few examples
        print(f"  Examples:")
        for obj in group_data["objects"][:3]:
            print(f"    - {obj['value']} ({obj['type']})")
        if object_count > 3:
            print(f"    ... and {object_count - 3} more")
    
    print("\n" + "=" * 70)
    print(f"Total Groups: {len(groups)}")
    print(f"Total Objects: {total_objects}")
    print("=" * 70)

if __name__ == "__main__":
    print("=" * 70)
    print("Policy Object Text to JSON Converter")
    print("=" * 70)
    
    try:
        # Parse the text file
        print(f"\nReading from: {INPUT_FILE}")
        groups = parse_text_file(INPUT_FILE)
        
        if not groups:
            print("\n✗ No policy object groups found in the file.")
            print("\nExpected format:")
            print("  GroupName1")
            print("  192.168.1.1")
            print("  10.0.0.0/8")
            print("  *.example.com")
            print("  ")
            print("  GroupName2")
            print("  value1")
            print("  value2")
        else:
            # Generate JSON
            generate_json(groups, OUTPUT_FILE)
            
            # Display summary
            display_summary(groups)
            
            print(f"\n✓ JSON file created: {OUTPUT_FILE}")
            print("\nThis file is ready to use with your policy object updater script!")
    
    except FileNotFoundError:
        print(f"\n✗ Error: File '{INPUT_FILE}' not found.")
        print("\nPlease create the file with the following format:")
        print("  GroupName1")
        print("  192.168.1.1")
        print("  *.example.com")
        print("  10.0.0.0/8")
        print("  ")
        print("  GroupName2")
        print("  value1")
        print("  value2")
    except Exception as e:
        print(f"\n✗ Error: {e}")