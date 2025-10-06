import meraki
import json
import os
from datetime import datetime

# --- Configuration ---
ORGANIZATION_ID = ""  # Specify your org ID
OUTPUT_DIR = "meraki_backups"  # Directory to save backup files
INCLUDE_DEVICES = True  # Include device-level configs
INCLUDE_CLIENTS = False  # Include current client lists (can be large)

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI(suppress_logging=True)

def get_organization_id():
    """
    Automatically get the organization ID if not specified.
    """
    try:
        orgs = dashboard.organizations.getOrganizations()
        if len(orgs) == 1:
            return orgs[0]['id']
        else:
            print("Multiple organizations found:")
            for i, org in enumerate(orgs, 1):
                print(f"{i}. {org['name']} (ID: {org['id']})")
            choice = int(input("\nSelect organization number: ")) - 1
            return orgs[choice]['id']
    except meraki.APIError as e:
        print(f"Error retrieving organizations: {e}")
        return None

def export_network_config(network_id, network_name, output_dir):
    """
    Export comprehensive configuration for a single network.
    """
    print(f"  Exporting: {network_name}")
    config = {
        "network_info": {},
        "ssids": [],
        "switches": {},
        "appliance": {},
        "wireless": {},
        "devices": []
    }
    
    try:
        # Basic network info
        config["network_info"] = dashboard.networks.getNetwork(network_id)
        
        # Get product types in this network
        product_types = config["network_info"].get("productTypes", [])
        
        # === Wireless Settings ===
        if "wireless" in product_types:
            try:
                # SSIDs
                config["ssids"] = dashboard.wireless.getNetworkWirelessSsids(network_id)
                
                # Wireless settings
                config["wireless"]["settings"] = dashboard.wireless.getNetworkWirelessSettings(network_id)
                
                # RF Profiles
                try:
                    config["wireless"]["rfProfiles"] = dashboard.wireless.getNetworkWirelessRfProfiles(network_id)
                except:
                    pass
                
            except meraki.APIError as e:
                print(f"    Warning: Could not get wireless configs: {e}")
        
        # === Switch Settings ===
        if "switch" in product_types:
            try:
                # Switch settings
                config["switches"]["settings"] = dashboard.switch.getNetworkSwitchSettings(network_id)
                
                # Switch ports (if you want per-switch port configs)
                # This can be slow for large networks - uncomment if needed
                # config["switches"]["ports"] = {}
                # switches = dashboard.devices.getNetworkDevices(network_id)
                # for switch in [s for s in switches if s.get('model', '').startswith('MS')]:
                #     config["switches"]["ports"][switch['serial']] = dashboard.switch.getDeviceSwitchPorts(switch['serial'])
                
                # Access policies
                try:
                    config["switches"]["accessPolicies"] = dashboard.switch.getNetworkSwitchAccessPolicies(network_id)
                except:
                    pass
                
            except meraki.APIError as e:
                print(f"    Warning: Could not get switch configs: {e}")
        
        # === Appliance Settings ===
        if "appliance" in product_types:
            try:
                # Firewall rules
                config["appliance"]["l3FirewallRules"] = dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(network_id)
                config["appliance"]["l7FirewallRules"] = dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules(network_id)
                
                # Content filtering
                config["appliance"]["contentFiltering"] = dashboard.appliance.getNetworkApplianceContentFiltering(network_id)
                
                # VLANs
                try:
                    config["appliance"]["vlans"] = dashboard.appliance.getNetworkApplianceVlans(network_id)
                except:
                    pass
                
                # Port forwarding
                try:
                    config["appliance"]["portForwarding"] = dashboard.appliance.getNetworkApplianceFirewallPortForwardingRules(network_id)
                except:
                    pass
                
                # Site-to-site VPN
                try:
                    config["appliance"]["siteToSiteVpn"] = dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn(network_id)
                except:
                    pass
                
            except meraki.APIError as e:
                print(f"    Warning: Could not get appliance configs: {e}")
        
        # === Traffic Shaping ===
        try:
            config["trafficShaping"] = dashboard.networks.getNetworkTrafficShapingApplicationCategories(network_id)
        except:
            pass
        
        # === Group Policies ===
        try:
            config["groupPolicies"] = dashboard.networks.getNetworkGroupPolicies(network_id)
        except:
            pass
        
        # === Devices ===
        if INCLUDE_DEVICES:
            try:
                config["devices"] = dashboard.networks.getNetworkDevices(network_id)
            except meraki.APIError as e:
                print(f"    Warning: Could not get devices: {e}")
        
        # === Clients (optional - can be large) ===
        if INCLUDE_CLIENTS:
            try:
                config["clients"] = dashboard.networks.getNetworkClients(network_id, timespan=86400)
            except meraki.APIError as e:
                print(f"    Warning: Could not get clients: {e}")
        
        # Save to file
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in network_name)
        filename = os.path.join(output_dir, f"{safe_name}_{network_id}.json")
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"    ✓ Saved to: {filename}")
        return True
        
    except Exception as e:
        print(f"    ✗ Error exporting {network_name}: {e}")
        return False

def export_organization_overview(org_id, output_dir):
    """
    Export organization-level settings and inventory.
    """
    print("\nExporting organization-level data...")
    org_config = {}
    
    try:
        # Organization info
        org_config["organization"] = dashboard.organizations.getOrganization(org_id)
        
        # All networks
        org_config["networks"] = dashboard.organizations.getOrganizationNetworks(org_id)
        
        # All devices inventory
        org_config["devices_inventory"] = dashboard.organizations.getOrganizationInventoryDevices(org_id)
        
        # License info
        try:
            org_config["licenses"] = dashboard.organizations.getOrganizationLicensesOverview(org_id)
        except:
            pass
        
        # Admins
        try:
            org_config["admins"] = dashboard.organizations.getOrganizationAdmins(org_id)
        except:
            pass
        
        # SAML roles
        try:
            org_config["samlRoles"] = dashboard.organizations.getOrganizationSamlRoles(org_id)
        except:
            pass
        
        # Save organization overview
        filename = os.path.join(output_dir, f"organization_overview_{org_id}.json")
        with open(filename, 'w') as f:
            json.dump(org_config, f, indent=2)
        
        print(f"  ✓ Organization data saved to: {filename}")
        
    except Exception as e:
        print(f"  ✗ Error exporting organization data: {e}")

def main():
    """
    Main function to export all configurations.
    """
    print("=" * 70)
    print("Meraki Configuration Export Tool")
    print("=" * 70)
    
    # Get organization ID
    org_id = ORGANIZATION_ID if ORGANIZATION_ID else get_organization_id()
    if not org_id:
        print("Error: Could not determine organization ID")
        return
    
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(OUTPUT_DIR, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nBackup directory: {output_dir}\n")
    
    # Export organization-level data
    export_organization_overview(org_id, output_dir)
    
    # Get all networks
    try:
        networks = dashboard.organizations.getOrganizationNetworks(org_id)
        print(f"\nFound {len(networks)} networks to export\n")
        
        success_count = 0
        failed_count = 0
        
        for network in networks:
            if export_network_config(network['id'], network['name'], output_dir):
                success_count += 1
            else:
                failed_count += 1
        
        # Summary
        print("\n" + "=" * 70)
        print("Export Complete!")
        print("=" * 70)
        print(f"Successfully exported: {success_count} networks")
        if failed_count > 0:
            print(f"Failed exports: {failed_count} networks")
        print(f"\nAll files saved to: {output_dir}")
        
        # Create a summary file
        summary = {
            "export_date": timestamp,
            "organization_id": org_id,
            "total_networks": len(networks),
            "successful_exports": success_count,
            "failed_exports": failed_count,
            "backup_location": output_dir
        }
        
        summary_file = os.path.join(output_dir, "export_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
    except meraki.APIError as e:
        print(f"Error retrieving networks: {e}")

if __name__ == "__main__":
    main()