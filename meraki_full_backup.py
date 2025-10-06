import meraki
import json
import os
from datetime import datetime

# --- Configuration ---
ORGANIZATION_IDS = []  # Leave empty to backup ALL organizations, or specify: ["org_id_1", "org_id_2"]
OUTPUT_DIR = "meraki_backups"
BACKUP_NETWORKS = True
BACKUP_DEVICES = True
BACKUP_TEMPLATES = True

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI(suppress_logging=True)

def safe_api_call(func, *args, **kwargs):
    """
    Safely call API function and return None if it fails.
    """
    try:
        return func(*args, **kwargs)
    except meraki.APIError:
        return None
    except Exception:
        return None

def backup_organization_settings(org_id):
    """
    Backup organization-level settings.
    """
    print(f"\n  Backing up organization settings...")
    org_data = {}
    
    # Basic org info
    org_data["info"] = safe_api_call(dashboard.organizations.getOrganization, org_id)
    
    # SAML and login security
    org_data["loginSecurity"] = safe_api_call(dashboard.organizations.getOrganizationLoginSecurity, org_id)
    org_data["saml"] = safe_api_call(dashboard.organizations.getOrganizationSaml, org_id)
    org_data["samlIdps"] = safe_api_call(dashboard.organizations.getOrganizationSamlIdps, org_id)
    org_data["samlRoles"] = safe_api_call(dashboard.organizations.getOrganizationSamlRoles, org_id)
    
    # Admins
    org_data["admins"] = safe_api_call(dashboard.organizations.getOrganizationAdmins, org_id)
    
    # Policy objects
    org_data["policyObjects"] = safe_api_call(dashboard.organizations.getOrganizationPolicyObjects, org_id)
    org_data["policyObjectsGroups"] = safe_api_call(dashboard.organizations.getOrganizationPolicyObjectsGroups, org_id)
    
    # Licensing
    org_data["licenses"] = safe_api_call(dashboard.organizations.getOrganizationLicenses, org_id)
    org_data["licensesOverview"] = safe_api_call(dashboard.organizations.getOrganizationLicensesOverview, org_id)
    
    # Inventory
    org_data["inventory"] = safe_api_call(dashboard.organizations.getOrganizationInventoryDevices, org_id)
    
    # Action batches (if any)
    org_data["actionBatches"] = safe_api_call(dashboard.organizations.getOrganizationActionBatches, org_id)
    
    # Alerts
    org_data["alertsProfiles"] = safe_api_call(dashboard.organizations.getOrganizationAlertsProfiles, org_id)
    
    # Adaptive policy
    org_data["adaptivePolicyAcls"] = safe_api_call(dashboard.organizations.getOrganizationAdaptivePolicyAcls, org_id)
    org_data["adaptivePolicyGroups"] = safe_api_call(dashboard.organizations.getOrganizationAdaptivePolicyGroups, org_id)
    org_data["adaptivePolicyPolicies"] = safe_api_call(dashboard.organizations.getOrganizationAdaptivePolicyPolicies, org_id)
    
    # Config templates
    org_data["configTemplates"] = safe_api_call(dashboard.organizations.getOrganizationConfigTemplates, org_id)
    
    # Branding
    org_data["brandingPolicies"] = safe_api_call(dashboard.organizations.getOrganizationBrandingPolicies, org_id)
    
    # SNMPv3
    org_data["snmp"] = safe_api_call(dashboard.organizations.getOrganizationSnmp, org_id)
    
    return org_data

def backup_network_settings(network_id, product_types):
    """
    Backup all settings for a single network.
    """
    network_data = {}
    
    # Basic network info
    network_data["info"] = safe_api_call(dashboard.networks.getNetwork, network_id)
    
    # Network-wide settings
    network_data["settings"] = safe_api_call(dashboard.networks.getNetworkSettings, network_id)
    network_data["groupPolicies"] = safe_api_call(dashboard.networks.getNetworkGroupPolicies, network_id)
    network_data["trafficShaping"] = safe_api_call(dashboard.networks.getNetworkTrafficShapingApplicationCategories, network_id)
    network_data["syslogServers"] = safe_api_call(dashboard.networks.getNetworkSyslogServers, network_id)
    network_data["netflow"] = safe_api_call(dashboard.networks.getNetworkNetflowSettings, network_id)
    network_data["alerts"] = safe_api_call(dashboard.networks.getNetworkAlertsSettings, network_id)
    
    # Wireless settings
    if "wireless" in product_types:
        network_data["wireless"] = {}
        network_data["wireless"]["ssids"] = safe_api_call(dashboard.wireless.getNetworkWirelessSsids, network_id)
        network_data["wireless"]["settings"] = safe_api_call(dashboard.wireless.getNetworkWirelessSettings, network_id)
        network_data["wireless"]["rfProfiles"] = safe_api_call(dashboard.wireless.getNetworkWirelessRfProfiles, network_id)
        network_data["wireless"]["airMarshal"] = safe_api_call(dashboard.wireless.getNetworkWirelessAirMarshal, network_id)
        network_data["wireless"]["bluetooth"] = safe_api_call(dashboard.wireless.getNetworkWirelessBluetoothSettings, network_id)
    
    # Switch settings
    if "switch" in product_types:
        network_data["switch"] = {}
        network_data["switch"]["settings"] = safe_api_call(dashboard.switch.getNetworkSwitchSettings, network_id)
        network_data["switch"]["accessPolicies"] = safe_api_call(dashboard.switch.getNetworkSwitchAccessPolicies, network_id)
        network_data["switch"]["portSchedules"] = safe_api_call(dashboard.switch.getNetworkSwitchPortSchedules, network_id)
        network_data["switch"]["qosRules"] = safe_api_call(dashboard.switch.getNetworkSwitchQosRules, network_id)
        network_data["switch"]["stacks"] = safe_api_call(dashboard.switch.getNetworkSwitchStacks, network_id)
        network_data["switch"]["stp"] = safe_api_call(dashboard.switch.getNetworkSwitchStp, network_id)
        network_data["switch"]["dhcpServerPolicy"] = safe_api_call(dashboard.switch.getNetworkSwitchDhcpServerPolicy, network_id)
    
    # Appliance settings
    if "appliance" in product_types:
        network_data["appliance"] = {}
        network_data["appliance"]["l3FirewallRules"] = safe_api_call(dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules, network_id)
        network_data["appliance"]["l7FirewallRules"] = safe_api_call(dashboard.appliance.getNetworkApplianceFirewallL7FirewallRules, network_id)
        network_data["appliance"]["contentFiltering"] = safe_api_call(dashboard.appliance.getNetworkApplianceContentFiltering, network_id)
        network_data["appliance"]["portForwarding"] = safe_api_call(dashboard.appliance.getNetworkApplianceFirewallPortForwardingRules, network_id)
        network_data["appliance"]["oneToOneNat"] = safe_api_call(dashboard.appliance.getNetworkApplianceFirewallOneToOneNatRules, network_id)
        network_data["appliance"]["oneToManyNat"] = safe_api_call(dashboard.appliance.getNetworkApplianceFirewallOneToManyNatRules, network_id)
        network_data["appliance"]["siteToSiteVpn"] = safe_api_call(dashboard.appliance.getNetworkApplianceVpnSiteToSiteVpn, network_id)
        network_data["appliance"]["vlans"] = safe_api_call(dashboard.appliance.getNetworkApplianceVlans, network_id)
        network_data["appliance"]["staticRoutes"] = safe_api_call(dashboard.appliance.getNetworkApplianceStaticRoutes, network_id)
        network_data["appliance"]["warmSpare"] = safe_api_call(dashboard.appliance.getNetworkApplianceWarmSpare, network_id)
        network_data["appliance"]["trafficShaping"] = safe_api_call(dashboard.appliance.getNetworkApplianceTrafficShaping, network_id)
        network_data["appliance"]["trafficShapingRules"] = safe_api_call(dashboard.appliance.getNetworkApplianceTrafficShapingRules, network_id)
        network_data["appliance"]["vpnBgp"] = safe_api_call(dashboard.appliance.getNetworkApplianceVpnBgp, network_id)
        network_data["appliance"]["settings"] = safe_api_call(dashboard.appliance.getNetworkApplianceSettings, network_id)
        network_data["appliance"]["securityIntrusion"] = safe_api_call(dashboard.appliance.getNetworkApplianceSecurityIntrusion, network_id)
        network_data["appliance"]["securityMalware"] = safe_api_call(dashboard.appliance.getNetworkApplianceSecurityMalware, network_id)
    
    # Camera settings
    if "camera" in product_types:
        network_data["camera"] = {}
        network_data["camera"]["qualityRetention"] = safe_api_call(dashboard.camera.getNetworkCameraQualityRetentionProfiles, network_id)
        network_data["camera"]["wirelessProfiles"] = safe_api_call(dashboard.camera.getNetworkCameraWirelessProfiles, network_id)
    
    # Sensor settings
    if "sensor" in product_types:
        network_data["sensor"] = {}
        network_data["sensor"]["alerts"] = safe_api_call(dashboard.sensor.getNetworkSensorAlertsProfiles, network_id)
    
    # Cellular gateway settings
    if "cellularGateway" in product_types:
        network_data["cellularGateway"] = {}
        network_data["cellularGateway"]["dhcp"] = safe_api_call(dashboard.cellularGateway.getNetworkCellularGatewayDhcp, network_id)
        network_data["cellularGateway"]["subnetPool"] = safe_api_call(dashboard.cellularGateway.getNetworkCellularGatewaySubnetPool, network_id)
    
    return network_data

def backup_device_settings(network_id):
    """
    Backup device-level configurations.
    """
    devices_data = {}
    
    # Get all devices in network
    devices = safe_api_call(dashboard.networks.getNetworkDevices, network_id)
    if not devices:
        return devices_data
    
    for device in devices:
        serial = device['serial']
        model = device.get('model', '')
        device_config = {"info": device}
        
        # Switch port configurations
        if model.startswith('MS'):
            device_config["switchPorts"] = safe_api_call(dashboard.switch.getDeviceSwitchPorts, serial)
        
        # Management interface settings
        device_config["managementInterface"] = safe_api_call(dashboard.devices.getDeviceManagementInterface, serial)
        
        devices_data[serial] = device_config
    
    return devices_data

def backup_template_settings(org_id, template_id, template_name):
    """
    Backup configuration template settings.
    """
    print(f"    Backing up template: {template_name}")
    template_data = {}
    
    # Get template details
    template_data["info"] = safe_api_call(dashboard.organizations.getOrganizationConfigTemplate, org_id, template_id)
    
    # Template switch profiles
    template_data["switchProfiles"] = safe_api_call(dashboard.organizations.getOrganizationConfigTemplateSwitchProfiles, org_id, template_id)
    
    return template_data

def backup_network(org_id, network):
    """
    Backup a single network.
    """
    network_id = network['id']
    network_name = network['name']
    product_types = network.get('productTypes', [])
    
    print(f"  Backing up network: {network_name}")
    
    backup = {
        "network": backup_network_settings(network_id, product_types)
    }
    
    # Backup devices if enabled
    if BACKUP_DEVICES:
        backup["devices"] = backup_device_settings(network_id)
    
    return backup

def backup_organization(org_id):
    """
    Backup entire organization.
    """
    try:
        org_info = dashboard.organizations.getOrganization(org_id)
        org_name = org_info['name']
        print(f"\n{'='*70}")
        print(f"Backing up Organization: {org_name}")
        print(f"Organization ID: {org_id}")
        print(f"{'='*70}")
        
        # Create timestamp folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_org_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in org_name)
        org_dir = os.path.join(OUTPUT_DIR, f"{safe_org_name}_{org_id}", timestamp)
        os.makedirs(org_dir, exist_ok=True)
        
        # Backup organization settings
        org_backup = backup_organization_settings(org_id)
        
        with open(os.path.join(org_dir, "organization.json"), 'w') as f:
            json.dump(org_backup, f, indent=2)
        print(f"  ✓ Organization settings backed up")
        
        # Backup templates
        if BACKUP_TEMPLATES and org_backup.get("configTemplates"):
            templates_dir = os.path.join(org_dir, "templates")
            os.makedirs(templates_dir, exist_ok=True)
            
            print(f"\n  Backing up {len(org_backup['configTemplates'])} templates...")
            for template in org_backup['configTemplates']:
                template_backup = backup_template_settings(org_id, template['id'], template['name'])
                safe_template_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in template['name'])
                
                with open(os.path.join(templates_dir, f"{safe_template_name}.json"), 'w') as f:
                    json.dump(template_backup, f, indent=2)
        
        # Backup networks
        if BACKUP_NETWORKS:
            networks = dashboard.organizations.getOrganizationNetworks(org_id)
            print(f"\n  Backing up {len(networks)} networks...")
            
            networks_dir = os.path.join(org_dir, "networks")
            os.makedirs(networks_dir, exist_ok=True)
            
            for network in networks:
                network_backup = backup_network(org_id, network)
                safe_network_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in network['name'])
                
                with open(os.path.join(networks_dir, f"{safe_network_name}_{network['id']}.json"), 'w') as f:
                    json.dump(network_backup, f, indent=2)
        
        # Create summary
        summary = {
            "backup_date": timestamp,
            "organization_id": org_id,
            "organization_name": org_name,
            "networks_backed_up": len(networks) if BACKUP_NETWORKS else 0,
            "templates_backed_up": len(org_backup.get('configTemplates', [])) if BACKUP_TEMPLATES else 0,
            "backup_location": org_dir
        }
        
        with open(os.path.join(org_dir, "backup_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n  ✓ Backup completed for {org_name}")
        print(f"  Location: {org_dir}")
        
        return True
        
    except meraki.APIError as e:
        print(f"✗ Error backing up organization {org_id}: {e}")
        return False

def main():
    """
    Main backup function.
    """
    print("="*70)
    print("Meraki Complete Backup Tool")
    print("="*70)
    
    # Determine which organizations to backup
    if ORGANIZATION_IDS:
        org_ids = ORGANIZATION_IDS
        print(f"\nBacking up {len(org_ids)} specified organization(s)")
    else:
        print("\nRetrieving all organizations...")
        orgs = dashboard.organizations.getOrganizations()
        org_ids = [org['id'] for org in orgs]
        print(f"Found {len(org_ids)} organization(s) to backup")
    
    # Backup each organization
    successful = 0
    failed = 0
    
    for org_id in org_ids:
        if backup_organization(org_id):
            successful += 1
        else:
            failed += 1
    
    # Final summary
    print("\n" + "="*70)
    print("Backup Complete!")
    print("="*70)
    print(f"Successfully backed up: {successful} organization(s)")
    if failed > 0:
        print(f"Failed backups: {failed} organization(s)")
    print(f"\nAll backups saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()