import meraki
import json

# --- Configuration ---
NETWORK_ID = ""  # Replace with your Meraki Network ID

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI()

def get_current_content_filtering(network_id):
    """
    Retrieves current content filtering settings (for backup/verification).
    """
    try:
        response = dashboard.appliance.getNetworkApplianceContentFiltering(network_id)
        print("Current content filtering settings:")
        print(json.dumps(response, indent=2))
        return response
    except meraki.APIError as e:
        print(f"Error retrieving content filtering: {e}")
        return None

def clear_content_filtering(network_id, backup=True):
    """
    Clears all content filtering settings for a given network.
    Sets all URL patterns and categories to empty lists.
    """
    try:
        # Optionally backup current settings first
        if backup:
            print("\n--- Backing up current settings ---")
            current_settings = get_current_content_filtering(network_id)
            if current_settings:
                backup_filename = f"content_filtering_backup_{network_id}.json"
                with open(backup_filename, 'w') as f:
                    json.dump(current_settings, f, indent=2)
                print(f"✓ Backup saved to: {backup_filename}\n")
        
        print(f"--- Clearing content filtering for network {network_id} ---")
        
        # Clear all settings by passing empty lists
        response = dashboard.appliance.updateNetworkApplianceContentFiltering(
            network_id,
            allowedUrlPatterns=[],
            blockedUrlCategories=[],
            blockedUrlPatterns=[]
        )
        
        print(f"✓ Content filtering cleared successfully for network {network_id}.")
        print("\nNew settings:")
        print(json.dumps(response, indent=2))
        
        return response
        
    except meraki.APIError as e:
        print(f"✗ Error clearing content filtering for network {network_id}: {e}")
        print(f"Status code: {e.status}")
        print(f"Reason: {e.reason}")
        print(f"Message: {e.message}")
        return None

def confirm_action():
    """
    Asks user to confirm before clearing settings.
    """
    print("=" * 60)
    print("WARNING: This will CLEAR ALL content filtering settings!")
    print("=" * 60)
    response = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    return response in ['yes', 'y']

if __name__ == "__main__":
    if not NETWORK_ID:
        print("Error: Please set the NETWORK_ID in the script.")
    else:
        # Ask for confirmation before clearing
        if confirm_action():
            clear_content_filtering(NETWORK_ID, backup=True)
        else:
            print("Operation cancelled.")