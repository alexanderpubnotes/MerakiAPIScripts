import meraki
import json
import os

# --- Configuration ---
BACKUP_FILE = ""  # Path to network backup JSON file (e.g., "meraki_backups/.../networks/HQ_L_12345.json")
TARGET_NETWORK_ID = ""  # Network to restore TO (can be same or different network)
DRY_RUN = True  # Set to False to actually apply changes

# What to restore (customize as needed)
RESTORE_WIRELESS = True
RESTORE_SWITCH = True
RESTORE_APPLIANCE = True
RESTORE_GROUP_POLICIES = True
RESTORE_ALERTS = True
RESTORE_SYSLOG = True

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI(suppress_logging=True)

def load_backup(filepath):
    """
    Load backup JSON file.
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: Backup file not found: {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in backup file")
        return None

def safe_restore(func, description, dry_run=True, *args, **kwargs):
    """
    Safely attempt to restore a configuration.
    """
    if dry_run:
        print(f"  [DRY RUN] Would restore: {description}")
        return True
    
    try:
        func(*args, **kwargs)
        print(f"  ✓ Restored: {description}")
        return True
    except meraki.APIError as e:
        print(f"  ✗ Failed to restore {description}: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error restoring {description}: {e}")
        return False

def restore_wireless_settings(network_id, wireless_config, dry_run=True):
    """
    Restore wireless configurations.
    """
    if not wireless_config:
        return
    
    print("\n--- Restoring Wireless Settings ---")
    
    # Restore wireless settings
    if wireless_config.get("settings"):
        settings = wireless_config["settings"]
        # Remove read-only fields
        settings.pop("meshing", None)
        safe_restore(
            dashboard.wireless.updateNetworkWirelessSettings,
            "Wireless Settings",
            dry_run,
            network_id,
            **settings
        )
    
    # Restore SSIDs
    if wireless_config.get("ssids"):
        for ssid in wireless_config["ssids"]:
            number = ssid.get("number")
            if number is not None:
                # Remove read-only fields
                ssid_config = {k: v for k, v in ssid.items() if k not in ["number", "splashPage"]}
                safe_restore(
                    dashboard.wireless.updateNetworkWirelessSsid,
                    f"SSID {number} ({ssid.get('name', 'Unnamed')})",
                    dry_run,
                    network_id,
                    number,
                    **ssid_config
                )
    
    # Restore RF profiles
    if wireless_config.get("rfProfiles"):
        for profile in wireless_config["rfProfiles"]:
            # Skip default profiles
            if not profile.get("name", "").startswith("Custom"):
                continue
            profile_config = {k: v for k, v in profile.items() if k not in ["id", "networkId"]}
            safe_restore(
                dashboard.wireless.createNetworkWirelessRfProfile,
                f"RF Profile: {profile.get('name')}",
                dry_run,
                network_id,
                **profile_config
            )

def restore_switch_settings(network_id, switch_config, dry_run=True):
    """
    Restore switch configurations.
    """
    if not switch_config:
        return
    
    print("\n--- Restoring Switch Settings ---")
    
    # Restore switch settings
    if switch_config.get("settings"):
        settings = switch_config["settings"]
        settings.pop("useCombinedPower", None)  # Read-only
        safe_restore(
            dashboard.switch.updateNetworkSwitchSettings,
            "Switch Settings",
            dry_run,
            network_id,
            **settings
        )
    
    # Restore port schedules
    if switch_config.get("portSchedules"):
        for schedule in switch_config["portSchedules"]:
            schedule_config = {k: v for k, v in schedule.items() if k not in ["id", "networkId"]}
            safe_restore(
                dashboard.switch.createNetworkSwitchPortSchedule,
                f"Port Schedule: {schedule.get('name')}",
                dry_run,
                network_id,
                **schedule_config
            )
    
    # Restore access policies
    if switch_config.get("accessPolicies"):
        for policy in switch_config["accessPolicies"]:
            policy_config = {k: v for k, v in policy.items() if k not in ["accessPolicyNumber", "counts"]}
            safe_restore(
                dashboard.switch.createNetworkSwitchAccessPolicy,
                f"Access Policy: {policy.get('name')}",
                dry_run,
                network_id,
                **policy_config
            )
    
    # Restore QoS rules
    if switch_config.get("qosRules"):
        qos_config = switch_config["qosRules"]
        safe_restore(
            dashboard.switch.updateNetworkSwitchQosRules,
            "QoS Rules",
            dry_run,
            network_id,
            **qos_config
        )
    
    # Restore STP settings
    if switch_config.get("stp"):
        stp_config = switch_config["stp"]
        safe_restore(
            dashboard.switch.updateNetworkSwitchStp,
            "STP Settings",
            dry_run,
            network_id,
            **stp_config
        )

def restore_appliance_settings(network_id, appliance_config, dry_run=True):
    """
    Restore appliance/security configurations.
    """
    if not appliance_config:
        return
    
    print("\n--- Restoring Appliance Settings ---")
    
    # Restore VLANs first (other configs may depend on them)
    if appliance_config.get("vlans"):
        for vlan in appliance_config["vlans"]:
            vlan_id = vlan.get("id")
            if vlan_id:
                vlan_config = {k: v for k, v in vlan.items() if k not in ["id", "networkId"]}
                safe_restore(
                    dashboard.appliance.createNetworkApplianceVlan,
                    f"VLAN {vlan_id}",
                    dry_run,
                    network_id,
                    vlan_id,
                    **vlan_config
                )
    
    # Restore L3 firewall rules
    if appliance_config.get("l3FirewallRules"):
        rules = appliance_config["l3FirewallRules"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules,
            "L3 Firewall Rules",
            dry_run,
            network_id,
            **rules
        )
    
    # Restore L7 firewall rules
    if appliance_config.get("l7FirewallRules"):
        rules = appliance_config["l7FirewallRules"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceFirewallL7FirewallRules,
            "L7 Firewall Rules",
            dry_run,
            network_id,
            **rules
        )
    
    # Restore content filtering
    if appliance_config.get("contentFiltering"):
        cf = appliance_config["contentFiltering"]
        # Extract just the IDs from blocked categories if they're objects
        blocked_categories = cf.get("blockedUrlCategories", [])
        if blocked_categories and isinstance(blocked_categories[0], dict):
            blocked_categories = [cat["id"] for cat in blocked_categories]
        
        safe_restore(
            dashboard.appliance.updateNetworkApplianceContentFiltering,
            "Content Filtering",
            dry_run,
            network_id,
            allowedUrlPatterns=cf.get("allowedUrlPatterns", []),
            blockedUrlCategories=blocked_categories,
            blockedUrlPatterns=cf.get("blockedUrlPatterns", [])
        )
    
    # Restore port forwarding
    if appliance_config.get("portForwarding"):
        pf = appliance_config["portForwarding"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceFirewallPortForwardingRules,
            "Port Forwarding Rules",
            dry_run,
            network_id,
            **pf
        )
    
    # Restore 1:1 NAT
    if appliance_config.get("oneToOneNat"):
        nat = appliance_config["oneToOneNat"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceFirewallOneToOneNatRules,
            "1:1 NAT Rules",
            dry_run,
            network_id,
            **nat
        )
    
    # Restore static routes
    if appliance_config.get("staticRoutes"):
        for route in appliance_config["staticRoutes"]:
            route_config = {k: v for k, v in route.items() if k not in ["id", "networkId"]}
            safe_restore(
                dashboard.appliance.createNetworkApplianceStaticRoute,
                f"Static Route: {route.get('name')}",
                dry_run,
                network_id,
                **route_config
            )
    
    # Restore site-to-site VPN
    if appliance_config.get("siteToSiteVpn"):
        vpn = appliance_config["siteToSiteVpn"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceVpnSiteToSiteVpn,
            "Site-to-Site VPN",
            dry_run,
            network_id,
            **vpn
        )
    
    # Restore traffic shaping
    if appliance_config.get("trafficShaping"):
        ts = appliance_config["trafficShaping"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceTrafficShaping,
            "Traffic Shaping",
            dry_run,
            network_id,
            **ts
        )
    
    # Restore security intrusion
    if appliance_config.get("securityIntrusion"):
        si = appliance_config["securityIntrusion"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceSecurityIntrusion,
            "Security Intrusion Settings",
            dry_run,
            network_id,
            **si
        )
    
    # Restore malware protection
    if appliance_config.get("securityMalware"):
        sm = appliance_config["securityMalware"]
        safe_restore(
            dashboard.appliance.updateNetworkApplianceSecurityMalware,
            "Malware Protection",
            dry_run,
            network_id,
            **sm
        )

def restore_group_policies(network_id, policies, dry_run=True):
    """
    Restore group policies.
    """
    if not policies:
        return
    
    print("\n--- Restoring Group Policies ---")
    
    for policy in policies:
        policy_config = {k: v for k, v in policy.items() if k not in ["groupPolicyId"]}
        safe_restore(
            dashboard.networks.createNetworkGroupPolicy,
            f"Group Policy: {policy.get('name')}",
            dry_run,
            network_id,
            **policy_config
        )

def restore_alerts(network_id, alerts, dry_run=True):
    """
    Restore alert settings.
    """
    if not alerts:
        return
    
    print("\n--- Restoring Alert Settings ---")
    
    safe_restore(
        dashboard.networks.updateNetworkAlertsSettings,
        "Alert Settings",
        dry_run,
        network_id,
        **alerts
    )

def restore_syslog(network_id, syslog, dry_run=True):
    """
    Restore syslog settings.
    """
    if not syslog:
        return
    
    print("\n--- Restoring Syslog Settings ---")
    
    safe_restore(
        dashboard.networks.updateNetworkSyslogServers,
        "Syslog Servers",
        dry_run,
        network_id,
        **syslog
    )

def restore_network(backup_data, target_network_id, dry_run=True):
    """
    Restore network configuration from backup.
    """
    network_config = backup_data.get("network", {})
    
    # Get target network info
    try:
        target_network = dashboard.networks.getNetwork(target_network_id)
        print(f"\nTarget Network: {target_network['name']}")
        print(f"Network ID: {target_network_id}")
        print(f"Product Types: {', '.join(target_network.get('productTypes', []))}")
    except meraki.APIError as e:
        print(f"✗ Error: Could not retrieve target network: {e}")
        return
    
    # Restore components based on configuration
    if RESTORE_GROUP_POLICIES:
        restore_group_policies(target_network_id, network_config.get("groupPolicies"), dry_run)
    
    if RESTORE_WIRELESS:
        restore_wireless_settings(target_network_id, network_config.get("wireless"), dry_run)
    
    if RESTORE_SWITCH:
        restore_switch_settings(target_network_id, network_config.get("switch"), dry_run)
    
    if RESTORE_APPLIANCE:
        restore_appliance_settings(target_network_id, network_config.get("appliance"), dry_run)
    
    if RESTORE_ALERTS:
        restore_alerts(target_network_id, network_config.get("alerts"), dry_run)
    
    if RESTORE_SYSLOG:
        restore_syslog(target_network_id, network_config.get("syslogServers"), dry_run)

def main():
    """
    Main restore function.
    """
    print("="*70)
    print("Meraki Configuration Restore Tool")
    print("="*70)
    
    if not BACKUP_FILE:
        print("\n✗ Error: Please specify BACKUP_FILE")
        print("   Example: BACKUP_FILE = 'meraki_backups/.../HQ_L_12345.json'")
        return
    
    if not TARGET_NETWORK_ID:
        print("\n✗ Error: Please specify TARGET_NETWORK_ID")
        print("   Example: TARGET_NETWORK_ID = 'L_123456789'")
        return
    
    # Load backup
    print(f"\nLoading backup from: {BACKUP_FILE}")
    backup_data = load_backup(BACKUP_FILE)
    if not backup_data:
        return
    
    print(f"Mode: {'DRY RUN (no changes will be made)' if DRY_RUN else 'LIVE (changes will be applied)'}")
    
    # Confirm in live mode
    if not DRY_RUN:
        print("\n⚠️  WARNING: You are running in LIVE mode!")
        print("This will modify the target network configuration.")
        response = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Operation cancelled.")
            return
    
    # Perform restore
    restore_network(backup_data, TARGET_NETWORK_ID, dry_run=DRY_RUN)
    
    print("\n" + "="*70)
    if DRY_RUN:
        print("✓ Dry run completed successfully!")
        print("Review the output above, then set DRY_RUN = False to apply changes")
    else:
        print("✓ Restore completed!")
        print("Please verify the configuration in the Meraki Dashboard")
    print("="*70)

if __name__ == "__main__":
    main()