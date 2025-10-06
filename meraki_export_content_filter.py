import meraki
import json

# --- Configuration ---
NETWORK_ID = ""  # Network to export content filtering from
OUTPUT_FILE = "contentFilteringoutput.json"

# Initialize the Meraki Dashboard API
dashboard = meraki.DashboardAPI()

# Category name mappings
CATEGORIES = {
    "meraki:contentFiltering/category/C2": "Arts",
    "meraki:contentFiltering/category/C4": "Job Search",
    "meraki:contentFiltering/category/C5": "Shopping",
    "meraki:contentFiltering/category/C6": "Adult",
    "meraki:contentFiltering/category/C7": "Games",
    "meraki:contentFiltering/category/C8": "Sports and Recreation",
    "meraki:contentFiltering/category/C10": "Society and Culture",
    "meraki:contentFiltering/category/C11": "Government and Law",
    "meraki:contentFiltering/category/C12": "Science and Technology",
    "meraki:contentFiltering/category/C14": "Social Science",
    "meraki:contentFiltering/category/C16": "Hate Speech",
    "meraki:contentFiltering/category/C18": "Infrastructure and Content Delivery Networks",
    "meraki:contentFiltering/category/C22": "Illegal Activities",
    "meraki:contentFiltering/category/C24": "Online Communities",
    "meraki:contentFiltering/category/C25": "Filter Avoidance",
    "meraki:contentFiltering/category/C27": "Advertisements",
    "meraki:contentFiltering/category/C28": "Online Trading",
    "meraki:contentFiltering/category/C31": "Lingerie and Swimsuits",
    "meraki:contentFiltering/category/C34": "Lotteries",
    "meraki:contentFiltering/category/C36": "Weapons",
    "meraki:contentFiltering/category/C37": "Web Hosting",
    "meraki:contentFiltering/category/C44": "Transportation",
    "meraki:contentFiltering/category/C45": "Real Estate",
    "meraki:contentFiltering/category/C46": "Travel",
    "meraki:contentFiltering/category/C47": "Illegal Drugs",
    "meraki:contentFiltering/category/C49": "Gambling",
    "meraki:contentFiltering/category/C50": "Hacking",
    "meraki:contentFiltering/category/C51": "Cheating and Plagiarism",
    "meraki:contentFiltering/category/C52": "Sex Education",
    "meraki:contentFiltering/category/C54": "Pornography",
    "meraki:contentFiltering/category/C55": "Dating",
    "meraki:contentFiltering/category/C56": "Peer File Transfer",
    "meraki:contentFiltering/category/C60": "Non-sexual Nudity",
    "meraki:contentFiltering/category/C64": "Child Abuse Content",
    "meraki:contentFiltering/category/C68": "Freeware and Shareware",
    "meraki:contentFiltering/category/C69": "Social Networking",
    "meraki:contentFiltering/category/C72": "Streaming Video",
    "meraki:contentFiltering/category/C73": "Streaming Audio",
    "meraki:contentFiltering/category/C74": "Astrology",
    "meraki:contentFiltering/category/C75": "Extreme",
    "meraki:contentFiltering/category/C76": "Fashion",
    "meraki:contentFiltering/category/C77": "Alcohol",
    "meraki:contentFiltering/category/C78": "Tobacco",
    "meraki:contentFiltering/category/C79": "Humor",
    "meraki:contentFiltering/category/C82": "Digital Postcards",
    "meraki:contentFiltering/category/C83": "Politics",
    "meraki:contentFiltering/category/C84": "Illegal Downloads",
    "meraki:contentFiltering/category/C86": "Religion",
    "meraki:contentFiltering/category/C87": "Non-governmental Organizations",
    "meraki:contentFiltering/category/C88": "Auctions",
    "meraki:contentFiltering/category/C91": "Dynamic and Residential",
    "meraki:contentFiltering/category/C93": "Entertainment",
    "meraki:contentFiltering/category/C97": "DIY Projects",
    "meraki:contentFiltering/category/C98": "Hunting",
    "meraki:contentFiltering/category/C99": "Military",
    "meraki:contentFiltering/category/C101": "Paranormal",
    "meraki:contentFiltering/category/C103": "Not Actionable",
    "meraki:contentFiltering/category/C104": "Health and Medicine",
    "meraki:contentFiltering/category/C105": "Recipes and Food",
    "meraki:contentFiltering/category/C106": "Nature and Conservation",
    "meraki:contentFiltering/category/C107": "Animals and Pets",
    "meraki:contentFiltering/category/C108": "Web Cache and Archives",
    "meraki:contentFiltering/category/C109": "Cannabis",
    "meraki:contentFiltering/category/C111": "Cryptocurrency",
    "meraki:contentFiltering/category/C112": "Cryptomining",
    "meraki:contentFiltering/category/C114": "Dynamic DNS Provider",
    "meraki:contentFiltering/category/C117": "Museums",
    "meraki:contentFiltering/category/C119": "Terrorism and Violent Extremism",
    "meraki:contentFiltering/category/C120": "URL Shorteners",
    "meraki:contentFiltering/category/C122": "DNS-Tunneling",
    "meraki:contentFiltering/category/T01": "Malware Sites",
    "meraki:contentFiltering/category/T02": "Spyware and Adware",
    "meraki:contentFiltering/category/T03": "Phishing",
    "meraki:contentFiltering/category/T04": "Botnets",
    "meraki:contentFiltering/category/T05": "Spam",
    "meraki:contentFiltering/category/T06": "Exploits",
    "meraki:contentFiltering/category/T09": "Bogon",
    "meraki:contentFiltering/category/T11": "Ebanking Fraud",
    "meraki:contentFiltering/category/T12": "Indicators of Compromise (IOC)",
    "meraki:contentFiltering/category/T13": "Domain Generated Algorithm",
    "meraki:contentFiltering/category/T14": "Open HTTP Proxy",
    "meraki:contentFiltering/category/T15": "Open Mail Relay",
    "meraki:contentFiltering/category/T16": "TOR exit Nodes",
    "meraki:contentFiltering/category/T21": "Cryptojacking",
    "meraki:contentFiltering/category/T22": "Linkshare",
    "meraki:contentFiltering/category/T23": "Malicious Sites"
}

if __name__ == "__main__":
    # Get content filtering settings
    response = dashboard.appliance.getNetworkApplianceContentFiltering(NETWORK_ID)
    
    # Format blocked categories with id and name
    blocked_categories = [
        {"id": cat_id, "name": CATEGORIES.get(cat_id, "Unknown")}
        for cat_id in response.get('blockedUrlCategories', [])
    ]
    
    # Build export structure
    export_data = {
        "blockedUrlCategories": blocked_categories,
        "blockedUrlPatterns": response.get('blockedUrlPatterns', []),
        "allowedUrlPatterns": response.get('allowedUrlPatterns', [])
    }
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(export_data, f, indent=4)
    
    print(f"✓ Exported to {OUTPUT_FILE}")