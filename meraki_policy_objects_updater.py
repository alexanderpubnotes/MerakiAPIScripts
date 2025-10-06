import meraki
import json
import time

# --- Configuration ---
ORGANIZATION_ID = ""  # Your Meraki Organization ID
JSON_FILE = "policy_objects.json"
DRY_RUN = True  # Set to False to actually make changes

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI(suppress_logging=True)

def get_existing_policy_objects(org_id):
    """
    Get all existing policy objects in the organization.
    Returns a dict with object names as keys.
    """
    try:
        objects = dashboard.organizations.getOrganizationPolicyObjects(org_id)
        return {obj['name']: obj for obj in objects}
    except meraki.APIError as e:
        print(f"Error retrieving policy objects: {e}")
        return {}

def get_existing_policy_object_groups(org_id):
    """
    Get all existing policy object groups in the organization.
    Returns a dict with group names as keys.
    """
    try:
        groups = dashboard.organizations.getOrganizationPolicyObjectsGroups(org_id)
        return {grp['name']: grp for grp in groups}
    except meraki.APIError as e:
        print(f"Error retrieving policy object groups: {e}")
        return {}

def create_policy_object(org_id, name, obj_type, value, dry_run=True):
    """
    Create a single policy object.
    """
    if dry_run:
        print(f"  [DRY RUN] Would create object: {name} ({obj_type}: {value})")
        return {"id": f"fake_id_{name}", "name": name}
    
    try:
        # Map our type names to Meraki API requirements
        if obj_type == "ip":
            response = dashboard.organizations.createOrganizationPolicyObject(
                org_id,
                name=name,
                category="network",
                type="cidr",
                cidr=f"{value}/32"  # Single IP becomes /32
            )
        elif obj_type == "cidr":
            response = dashboard.organizations.createOrganizationPolicyObject(
                org_id,
                name=name,
                category="network",
                type="cidr",
                cidr=value
            )
        elif obj_type == "fqdn":
            response = dashboard.organizations.createOrganizationPolicyObject(
                org_id,
                name=name,
                category="network",
                type="fqdn",
                fqdn=value
            )
        else:
            print(f"  ✗ Unknown type: {obj_type}")
            return None
        
        print(f"  ✓ Created object: {name}")
        return response
    except meraki.APIError as e:
        print(f"  ✗ Error creating object {name}: {e}")
        return None

def create_policy_object_group(org_id, group_name, object_ids, dry_run=True):
    """
    Create a policy object group with the given objects.
    """
    if dry_run:
        print(f"  [DRY RUN] Would create group: {group_name} with {len(object_ids)} objects")
        return {"id": f"fake_group_id_{group_name}", "name": group_name}
    
    try:
        response = dashboard.organizations.createOrganizationPolicyObjectsGroup(
            org_id,
            name=group_name,
            objectIds=object_ids
        )
        print(f"  ✓ Created group: {group_name}")
        return response
    except meraki.APIError as e:
        print(f"  ✗ Error creating group {group_name}: {e}")
        return None

def update_policy_object_group(org_id, group_id, object_ids, dry_run=True):
    """
    Update an existing policy object group with new object IDs.
    """
    if dry_run:
        print(f"  [DRY RUN] Would update group with {len(object_ids)} objects")
        return True
    
    try:
        response = dashboard.organizations.updateOrganizationPolicyObjectsGroup(
            org_id,
            group_id,
            objectIds=object_ids
        )
        print(f"  ✓ Updated group")
        return response
    except meraki.APIError as e:
        print(f"  ✗ Error updating group: {e}")
        return None

def process_policy_objects(org_id, groups_config, dry_run=True):
    """
    Process all groups and objects from the JSON configuration.
    """
    print("\n" + "=" * 70)
    print("Step 1: Retrieving existing policy objects and groups")
    print("=" * 70)
    
    existing_objects = get_existing_policy_objects(org_id)
    existing_groups = get_existing_policy_object_groups(org_id)
    
    print(f"Found {len(existing_objects)} existing policy objects")
    print(f"Found {len(existing_groups)} existing policy object groups")
    
    # Track what we create
    created_objects = 0
    skipped_objects = 0
    created_groups = 0
    updated_groups = 0
    
    print("\n" + "=" * 70)
    print("Step 2: Processing policy objects and groups")
    print("=" * 70)
    
    for group_name, group_data in groups_config.items():
        print(f"\n--- Processing Group: {group_name} ---")
        objects = group_data.get("objects", [])
        print(f"Objects to process: {len(objects)}")
        
        # Create/track object IDs for this group
        object_ids = []
        
        for idx, obj in enumerate(objects, 1):
            obj_type = obj["type"]
            obj_value = obj["value"]
            obj_name = f"{group_name}_{idx}"
            
            # Check if object already exists
            if obj_name in existing_objects:
                print(f"  ⊙ Object already exists: {obj_name}")
                object_ids.append(existing_objects[obj_name]["id"])
                skipped_objects += 1
            else:
                # Create new object
                result = create_policy_object(org_id, obj_name, obj_type, obj_value, dry_run)
                if result:
                    object_ids.append(result["id"])
                    created_objects += 1
                    # Rate limiting - be nice to the API
                    if not dry_run:
                        time.sleep(0.2)
        
        # Create or update the group
        if object_ids:
            if group_name in existing_groups:
                print(f"\n  Group '{group_name}' already exists, updating...")
                update_policy_object_group(
                    org_id, 
                    existing_groups[group_name]["id"], 
                    object_ids, 
                    dry_run
                )
                updated_groups += 1
            else:
                print(f"\n  Creating new group: {group_name}")
                create_policy_object_group(org_id, group_name, object_ids, dry_run)
                created_groups += 1
                if not dry_run:
                    time.sleep(0.2)
    
    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Policy Objects Created: {created_objects}")
    print(f"Policy Objects Skipped (already exist): {skipped_objects}")
    print(f"Policy Object Groups Created: {created_groups}")
    print(f"Policy Object Groups Updated: {updated_groups}")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No actual changes were made")
        print("Set DRY_RUN = False to apply changes")
    else:
        print("\n✓ All changes have been applied!")

def load_json_config(filename):
    """
    Load the policy objects configuration from JSON file.
    """
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config.get("groups", {})
    except FileNotFoundError:
        print(f"✗ Error: JSON file not found: {filename}")
        return None
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in {filename}")
        return None

def get_organization_id():
    """
    Automatically get the organization ID if not specified.
    """
    try:
        orgs = dashboard.organizations.getOrganizations()
        if len(orgs) == 1:
            return orgs[0]['id']
        else:
            print("\nMultiple organizations found:")
            for i, org in enumerate(orgs, 1):
                print(f"{i}. {org['name']} (ID: {org['id']})")
            choice = int(input("\nSelect organization number: ")) - 1
            return orgs[choice]['id']
    except meraki.APIError as e:
        print(f"Error retrieving organizations: {e}")
        return None

if __name__ == "__main__":
    print("=" * 70)
    print("Meraki Policy Objects Bulk Updater")
    print("=" * 70)
    
    # Get organization ID
    org_id = ORGANIZATION_ID if ORGANIZATION_ID else get_organization_id()
    if not org_id:
        print("✗ Error: Could not determine organization ID")
        exit(1)
    
    print(f"\nOrganization ID: {org_id}")
    print(f"JSON Config File: {JSON_FILE}")
    print(f"Mode: {'DRY RUN (no changes will be made)' if DRY_RUN else 'LIVE (changes will be applied)'}")
    
    # Load configuration
    groups_config = load_json_config(JSON_FILE)
    if not groups_config:
        exit(1)
    
    print(f"\nLoaded {len(groups_config)} policy object groups from JSON")
    
    # Confirm before proceeding in live mode
    if not DRY_RUN:
        print("\n⚠️  WARNING: You are running in LIVE mode!")
        response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Operation cancelled.")
            exit(0)
    
    # Process everything
    process_policy_objects(org_id, groups_config, dry_run=DRY_RUN)