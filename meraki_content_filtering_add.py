import meraki
import json

# --- Configuration ---
NETWORK_ID = ""  # Replace with your Meraki Network ID
JSON_CONFIG_FILE = "contentFilteringoutput.json"

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI()

def update_content_filtering(network_id, config_data):
    """
    Updates the content filtering settings for a given network.
    """
    try:
        # Get the data from JSON
        allowed_patterns = config_data.get("allowedUrlPatterns", [])
        blocked_categories_raw = config_data.get("blockedUrlCategories", [])
        blocked_patterns = config_data.get("blockedUrlPatterns", [])
        
        # Extract just the IDs from blocked categories if they're objects
        # The API expects a list of strings like ["meraki:contentFiltering/category/C2", ...]
        blocked_categories = []
        if blocked_categories_raw:
            if isinstance(blocked_categories_raw[0], dict):
                # If categories are objects with 'id' field, extract the IDs
                blocked_categories = [cat["id"] for cat in blocked_categories_raw]
            else:
                # If they're already strings, use as-is
                blocked_categories = blocked_categories_raw
        
        print(f"Attempting to update content filtering with:")
        print(f"  Allowed URL Patterns: {len(allowed_patterns)} patterns")
        print(f"  Blocked URL Categories: {len(blocked_categories)} categories")
        print(f"  Blocked URL Patterns: {len(blocked_patterns)} patterns")
        print(f"\nFirst few blocked categories: {blocked_categories[:3]}")
        
        response = dashboard.appliance.updateNetworkApplianceContentFiltering(
            network_id,
            allowedUrlPatterns=allowed_patterns,
            blockedUrlCategories=blocked_categories,
            blockedUrlPatterns=blocked_patterns
        )
        
        print(f"\n✓ Content filtering updated successfully for network {network_id}.")
        print("\nResponse from API:")
        print(json.dumps(response, indent=2))
        
    except meraki.APIError as e:
        print(f"✗ Error updating content filtering for network {network_id}: {e}")
        print(f"Status code: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Message: {e.message}")

def load_config_from_json(file_path):
    """
    Loads content filtering configuration from a JSON file.
    """
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        print(f"Loaded configuration from {file_path}:")
        print(json.dumps(config, indent=2))
        return config
    except FileNotFoundError:
        print(f"Error: JSON configuration file not found at {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}")
        return None

if __name__ == "__main__":
    # Load configuration from JSON file
    config_data = load_config_from_json(JSON_CONFIG_FILE)
    
    if config_data:
        # Update content filtering for the specified network
        update_content_filtering(NETWORK_ID, config_data)
    else:
        print("Failed to load configuration. Exiting.")