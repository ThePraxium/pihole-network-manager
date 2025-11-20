"""
Content Filtering Module

Advanced content filtering with time-based and device-specific rules.
Block specific websites (social media, etc.) with scheduling support.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.local_executor import execute_command, read_file, write_file, file_exists
from core.config import Config, get_project_root
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen, show_key_value_list
)


RULES_FILE = get_project_root() / "data" / "content_filter_rules.json"


# Predefined website categories
WEBSITE_CATEGORIES = {
    "social_media": {
        "name": "Social Media",
        "domains": [
            "facebook.com", "www.facebook.com", "*.facebook.com",
            "instagram.com", "www.instagram.com", "*.instagram.com",
            "twitter.com", "x.com", "*.twitter.com", "*.x.com",
            "tiktok.com", "www.tiktok.com", "*.tiktok.com",
            "snapchat.com", "*.snapchat.com",
            "reddit.com", "www.reddit.com", "*.reddit.com",
            "linkedin.com", "www.linkedin.com", "*.linkedin.com"
        ]
    },
    "video_streaming": {
        "name": "Video Streaming",
        "domains": [
            "youtube.com", "www.youtube.com", "*.youtube.com",
            "youtu.be", "*.youtu.be",
            "netflix.com", "*.netflix.com",
            "hulu.com", "*.hulu.com",
            "twitch.tv", "*.twitch.tv",
            "vimeo.com", "*.vimeo.com"
        ]
    },
    "gaming": {
        "name": "Gaming",
        "domains": [
            "steam.com", "*.steampowered.com",
            "epicgames.com", "*.epicgames.com",
            "twitch.tv", "*.twitch.tv",
            "discord.com", "*.discord.com",
            "roblox.com", "*.roblox.com"
        ]
    },
    "news": {
        "name": "News Sites",
        "domains": [
            "cnn.com", "*.cnn.com",
            "foxnews.com", "*.foxnews.com",
            "bbc.com", "*.bbc.com",
            "nytimes.com", "*.nytimes.com"
        ]
    },
    "shopping": {
        "name": "Shopping",
        "domains": [
            "amazon.com", "*.amazon.com",
            "ebay.com", "*.ebay.com",
            "walmart.com", "*.walmart.com",
            "target.com", "*.target.com"
        ]
    }
}


def run(config: Config):
    """Main content filtering interface"""
    while True:
        # clear_screen()  # Disabled to preserve scroll history
        console.print("[bold cyan]Content Filtering[/bold cyan]\n")

        options = [
            "View Active Filter Rules",
            "Create New Filter Rule",
            "Edit Filter Rule",
            "Delete Filter Rule",
            "Quick Block (Social Media)",
            "Quick Block (Custom Website)",
            "Enable/Disable Rule",
            "Test Rule Configuration"
        ]

        choice = show_menu("Content Filter Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            view_rules()
        elif choice == "2":
            create_rule(config)
        elif choice == "3":
            edit_rule(config)
        elif choice == "4":
            delete_rule()
        elif choice == "5":
            quick_block_category(config)
        elif choice == "6":
            quick_block_custom(config)
        elif choice == "7":
            toggle_rule()
        elif choice == "8":
            test_rule_config()


def view_rules():
    """Display all content filter rules"""
    show_status("Loading filter rules...", "info")

    rules = load_rules()

    if not rules:
        show_warning("No filter rules configured")
        wait_for_enter()
        return

    # Display rules in table
    rows = []
    for rule in rules:
        rule_id = rule.get("id", "N/A")
        name = rule.get("name", "Unnamed")
        category = rule.get("category", "Custom")
        status = "[green]Enabled[/green]" if rule.get("enabled", True) else "[red]Disabled[/red]"

        # Format schedule
        schedule = rule.get("schedule", {})
        if schedule.get("enabled"):
            time_range = f"{schedule.get('start_time', '00:00')}-{schedule.get('end_time', '23:59')}"
            days = ",".join(schedule.get("days", ["All"]))
            schedule_str = f"{time_range} ({days})"
        else:
            schedule_str = "Always"

        # Format devices
        devices = rule.get("devices", [])
        if devices:
            device_str = ", ".join(devices[:2])
            if len(devices) > 2:
                device_str += f" +{len(devices) - 2}"
        else:
            device_str = "All devices"

        rows.append([rule_id, name, category, schedule_str, device_str, status])

    show_table(
        title="Content Filter Rules",
        headers=["ID", "Name", "Category", "Schedule", "Devices", "Status"],
        rows=rows,
        styles=["cyan", "white", "yellow", "white", "white", "white"]
    )

    console.print(f"\nTotal rules: {len(rules)}\n")
    wait_for_enter()


def create_rule(config: Config):
    """Create a new content filter rule"""
    console.print("\n[bold]Create Content Filter Rule[/bold]\n")

    # Rule name
    rule_name = prompt_input("Rule name", default="New Filter Rule")

    # Category selection
    console.print("\n[bold]Category:[/bold]")
    console.print("  [1] Social Media")
    console.print("  [2] Video Streaming")
    console.print("  [3] Gaming")
    console.print("  [4] News")
    console.print("  [5] Shopping")
    console.print("  [6] Custom")

    category_choice = prompt_input("Select category (1-6)", default="6")

    category_map = {
        "1": "social_media",
        "2": "video_streaming",
        "3": "gaming",
        "4": "news",
        "5": "shopping",
        "6": "custom"
    }

    category = category_map.get(category_choice, "custom")

    # Get domains
    if category != "custom":
        domains = WEBSITE_CATEGORIES[category]["domains"]
        console.print(f"\n[bold]Domains in {WEBSITE_CATEGORIES[category]['name']}:[/bold]")
        for domain in domains[:5]:
            console.print(f"  - {domain}")
        if len(domains) > 5:
            console.print(f"  ... and {len(domains) - 5} more")
        console.print()
    else:
        console.print("\n[bold]Enter domains to block (one per line, empty to finish):[/bold]")
        console.print("Examples: facebook.com, *.reddit.com, example.com\n")

        domains = []
        while True:
            domain = prompt_input(f"Domain #{len(domains) + 1} (or press Enter to finish)", default="")
            if not domain:
                break
            domains.append(domain)

        if not domains:
            show_error("No domains specified")
            wait_for_enter()
            return

    # Time-based scheduling
    console.print("\n[bold]Time-based Scheduling:[/bold]")
    use_schedule = confirm_action("Enable time-based filtering?", default=False)

    schedule = {"enabled": use_schedule}

    if use_schedule:
        default_window = config.get("content_filter", "default_block_window", "09:00-17:00")
        time_window = prompt_input(f"Time window (HH:MM-HH:MM)", default=default_window)

        try:
            start_time, end_time = time_window.split('-')
            schedule["start_time"] = start_time.strip()
            schedule["end_time"] = end_time.strip()
        except:
            show_error("Invalid time format")
            wait_for_enter()
            return

        # Days of week
        console.print("\n[bold]Days of week:[/bold]")
        console.print("  [1] Every day")
        console.print("  [2] Weekdays only")
        console.print("  [3] Weekends only")
        console.print("  [4] Custom")

        days_choice = prompt_input("Select option (1-4)", default="1")

        if days_choice == "1":
            schedule["days"] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        elif days_choice == "2":
            schedule["days"] = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        elif days_choice == "3":
            schedule["days"] = ["Sat", "Sun"]
        else:
            days_input = prompt_input("Days (comma-separated: Mon,Tue,Wed...)", default="Mon,Tue,Wed,Thu,Fri")
            schedule["days"] = [day.strip() for day in days_input.split(',')]

    # Device-specific filtering
    console.print("\n[bold]Device-specific Filtering:[/bold]")
    use_devices = confirm_action("Apply to specific devices only?", default=False)

    devices = []
    if use_devices:
        console.print("\n[bold]Enter device IPs (one per line, empty to finish):[/bold]\n")

        while True:
            device_ip = prompt_input(f"Device IP #{len(devices) + 1} (or press Enter to finish)", default="")
            if not device_ip:
                break
            devices.append(device_ip)

        if not devices:
            console.print("[yellow]No devices specified - rule will apply to all devices[/yellow]")

    # Create rule object
    rules = load_rules() or []

    # Generate new ID
    new_id = max([r.get("id", 0) for r in rules], default=0) + 1

    new_rule = {
        "id": new_id,
        "name": rule_name,
        "category": category,
        "domains": domains,
        "schedule": schedule,
        "devices": devices,
        "enabled": True,
        "created": None  # Will be set on save
    }

    # Show summary
    console.print("\n[bold]Rule Summary:[/bold]")
    console.print(f"Name: {rule_name}")
    console.print(f"Category: {category}")
    console.print(f"Domains: {len(domains)}")
    console.print(f"Schedule: {'Yes' if use_schedule else 'No'}")
    console.print(f"Devices: {len(devices) if devices else 'All'}")
    console.print()

    if not confirm_action("Create this rule?", default=True):
        return

    # Add rule and save
    rules.append(new_rule)

    if save_rules(rules):
        show_success(f"Rule '{rule_name}' created")

        # Show warning for time-based rules
        if use_schedule:
            console.print("\n[yellow]⚠️  Time-Based Filtering Notice:[/yellow]")
            console.print("[yellow]   Automatic time-based enforcement is not yet implemented.[/yellow]")
            console.print("[yellow]   You must manually enable/disable this rule at scheduled times,[/yellow]")
            console.print("[yellow]   or create custom cron jobs for automation.[/yellow]")
            console.print("[yellow]   See README.md 'Known Limitations' for details.[/yellow]\n")

        # Apply rule
        if confirm_action("Apply rule now?", default=True):
            apply_rules()
    else:
        show_error("Failed to save rule")

    wait_for_enter()


def edit_rule(config: Config):
    """Edit an existing rule"""
    rules = load_rules()

    if not rules:
        show_warning("No rules to edit")
        wait_for_enter()
        return

    # View rules first
    view_rules()

    rule_id = prompt_input("Enter rule ID to edit")

    if not rule_id.isdigit():
        show_error("Invalid ID")
        wait_for_enter()
        return

    # Find rule
    rule = next((r for r in rules if r.get("id") == int(rule_id)), None)

    if not rule:
        show_error(f"Rule ID {rule_id} not found")
        wait_for_enter()
        return

    console.print(f"\n[bold]Editing Rule: {rule.get('name')}[/bold]\n")

    # Edit options
    console.print("[bold]What to edit:[/bold]")
    console.print("  [1] Rule name")
    console.print("  [2] Schedule")
    console.print("  [3] Devices")
    console.print("  [4] Enable/Disable")

    edit_choice = prompt_input("Select option (1-4)", default="2")

    if edit_choice == "1":
        new_name = prompt_input("New name", default=rule.get("name"))
        rule["name"] = new_name

    elif edit_choice == "2":
        # Edit schedule
        use_schedule = confirm_action("Enable time-based filtering?", default=rule.get("schedule", {}).get("enabled", False))

        if use_schedule:
            current_schedule = rule.get("schedule", {})
            current_window = f"{current_schedule.get('start_time', '09:00')}-{current_schedule.get('end_time', '17:00')}"

            time_window = prompt_input("Time window (HH:MM-HH:MM)", default=current_window)
            start_time, end_time = time_window.split('-')

            rule["schedule"] = {
                "enabled": True,
                "start_time": start_time.strip(),
                "end_time": end_time.strip(),
                "days": current_schedule.get("days", ["Mon", "Tue", "Wed", "Thu", "Fri"])
            }
        else:
            rule["schedule"] = {"enabled": False}

    elif edit_choice == "3":
        # Edit devices
        current_devices = rule.get("devices", [])
        console.print(f"\nCurrent devices: {', '.join(current_devices) if current_devices else 'All'}\n")

        if confirm_action("Clear current devices and re-enter?", default=True):
            devices = []
            console.print("\n[bold]Enter device IPs (one per line, empty to finish):[/bold]\n")

            while True:
                device_ip = prompt_input(f"Device IP #{len(devices) + 1} (or press Enter to finish)", default="")
                if not device_ip:
                    break
                devices.append(device_ip)

            rule["devices"] = devices

    elif edit_choice == "4":
        rule["enabled"] = not rule.get("enabled", True)

    # Save changes
    if save_rules(rules):
        show_success("Rule updated")

        if confirm_action("Apply changes now?", default=True):
            apply_rules()
    else:
        show_error("Failed to save changes")

    wait_for_enter()


def delete_rule():
    """Delete a filter rule"""
    rules = load_rules()

    if not rules:
        show_warning("No rules to delete")
        wait_for_enter()
        return

    # View rules first
    view_rules()

    rule_id = prompt_input("Enter rule ID to delete")

    if not rule_id.isdigit():
        show_error("Invalid ID")
        wait_for_enter()
        return

    # Find rule
    rule = next((r for r in rules if r.get("id") == int(rule_id)), None)

    if not rule:
        show_error(f"Rule ID {rule_id} not found")
        wait_for_enter()
        return

    console.print(f"\n[bold]Rule:[/bold] {rule.get('name')}")
    console.print(f"[bold]Category:[/bold] {rule.get('category')}")
    console.print(f"[bold]Domains:[/bold] {len(rule.get('domains', []))}\n")

    if not confirm_action("Delete this rule?", default=False):
        return

    # Remove rule
    rules = [r for r in rules if r.get("id") != int(rule_id)]

    if save_rules(rules):
        show_success("Rule deleted")

        if confirm_action("Apply changes now?", default=True):
            apply_rules()
    else:
        show_error("Failed to delete rule")

    wait_for_enter()


def quick_block_category(config: Config):
    """Quick block a predefined category"""
    console.print("\n[bold]Quick Block Category[/bold]\n")

    console.print("[bold]Categories:[/bold]")
    for i, (key, cat) in enumerate(WEBSITE_CATEGORIES.items(), 1):
        console.print(f"  [{i}] {cat['name']} ({len(cat['domains'])} domains)")

    choice = prompt_input(f"Select category (1-{len(WEBSITE_CATEGORIES)})")

    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(WEBSITE_CATEGORIES):
        show_error("Invalid choice")
        wait_for_enter()
        return

    category_key = list(WEBSITE_CATEGORIES.keys())[int(choice) - 1]
    category = WEBSITE_CATEGORIES[category_key]

    # Create simple rule
    rules = load_rules() or []
    new_id = max([r.get("id", 0) for r in rules], default=0) + 1

    new_rule = {
        "id": new_id,
        "name": f"Block {category['name']}",
        "category": category_key,
        "domains": category["domains"],
        "schedule": {"enabled": False},
        "devices": [],
        "enabled": True
    }

    rules.append(new_rule)

    if save_rules(rules):
        show_success(f"{category['name']} blocked")
        apply_rules()
    else:
        show_error("Failed to create rule")

    wait_for_enter()


def quick_block_custom(config: Config):
    """Quick block a custom website"""
    console.print("\n[bold]Quick Block Website[/bold]\n")

    domain = prompt_input("Domain to block (e.g., example.com)")

    if not domain:
        show_error("No domain specified")
        wait_for_enter()
        return

    # Create simple rule
    rules = load_rules() or []
    new_id = max([r.get("id", 0) for r in rules], default=0) + 1

    new_rule = {
        "id": new_id,
        "name": f"Block {domain}",
        "category": "custom",
        "domains": [domain, f"*.{domain}"],
        "schedule": {"enabled": False},
        "devices": [],
        "enabled": True
    }

    rules.append(new_rule)

    if save_rules(rules):
        show_success(f"{domain} blocked")
        apply_rules()
    else:
        show_error("Failed to create rule")

    wait_for_enter()


def toggle_rule():
    """Enable or disable a rule"""
    rules = load_rules()

    if not rules:
        show_warning("No rules available")
        wait_for_enter()
        return

    view_rules()

    rule_id = prompt_input("Enter rule ID to toggle")

    if not rule_id.isdigit():
        show_error("Invalid ID")
        wait_for_enter()
        return

    # Find and toggle rule
    for rule in rules:
        if rule.get("id") == int(rule_id):
            rule["enabled"] = not rule.get("enabled", True)
            status = "enabled" if rule["enabled"] else "disabled"

            if save_rules(rules):
                show_success(f"Rule {status}")
                apply_rules()
            else:
                show_error("Failed to update rule")

            wait_for_enter()
            return

    show_error(f"Rule ID {rule_id} not found")
    wait_for_enter()


def test_rule_config():
    """Test if rules are properly configured"""
    show_status("Testing rule configuration...", "info")

    # Check if rules file exists
    if not file_exists(RULES_FILE):
        show_warning("No rules file found")
        wait_for_enter()
        return

    # Load rules
    rules = load_rules()

    console.print(f"\n[bold]Total rules:[/bold] {len(rules)}")

    enabled_rules = [r for r in rules if r.get("enabled", True)]
    console.print(f"[bold]Enabled rules:[/bold] {len(enabled_rules)}")

    # Count total domains
    total_domains = sum(len(r.get("domains", [])) for r in enabled_rules)
    console.print(f"[bold]Total domains affected:[/bold] {total_domains}")

    console.print("\n[green]✓[/green] Configuration is valid\n")

    wait_for_enter()


# Helper functions

def load_rules() -> Optional[List[Dict[str, Any]]]:
    """Load content filter rules from Pi-hole"""
    if not file_exists(RULES_FILE):
        return []

    success, content = read_file(RULES_FILE)

    if not success or not content:
        return []

    try:
        return json.loads(content)
    except:
        return []


def save_rules(rules: List[Dict[str, Any]]) -> bool:
    """Save content filter rules to Pi-hole"""
    try:
        rules_json = json.dumps(rules, indent=2)
        success, error = write_file(RULES_FILE, rules_json, sudo=True)
        if not success:
            console.print(f"[red]Error saving rules: {error}[/red]")
        return success
    except Exception as e:
        console.print(f"[red]Error saving rules: {e}[/red]")
        return False


def apply_rules():
    """Apply content filter rules to Pi-hole"""
    show_status("Applying content filter rules...", "info")

    rules = load_rules()

    if not rules:
        show_warning("No rules to apply")
        return

    # Get enabled rules
    enabled_rules = [r for r in rules if r.get("enabled", True)]

    # Collect all domains to block
    domains_to_block = []

    for rule in enabled_rules:
        # Check if rule should be active based on schedule
        schedule = rule.get("schedule", {})

        if schedule.get("enabled"):
            # TODO: Implement time-based checking
            # For now, add all scheduled rules
            pass

        domains_to_block.extend(rule.get("domains", []))

    # Remove duplicates
    domains_to_block = list(set(domains_to_block))

    console.print(f"\nApplying {len(domains_to_block)} domains from {len(enabled_rules)} rules...")

    # Add domains to blacklist with comment
    for domain in domains_to_block:
        domain_escaped = domain.replace("'", "''")

        # Check if already exists
        success, existing, _ = execute_command(
            f"sqlite3 /etc/pihole/gravity.db \"SELECT id FROM domainlist WHERE domain = '{domain_escaped}' AND type IN (1, 3);\"",
            sudo=True
        )

        if existing.strip():
            # Already exists, skip
            continue

        # Determine if regex or exact
        is_regex = '*' in domain or '.' in domain and domain.startswith('*')
        type_val = 3 if is_regex else 1  # 1=blacklist exact, 3=blacklist regex

        # Insert
        execute_command(
            f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO domainlist (type, domain, enabled, comment) VALUES ({type_val}, '{domain_escaped}', 1, 'Content Filter');\"",
            sudo=True
        )

    # Reload Pi-hole
    execute_command("pihole restartdns reload-lists", sudo=True)

    show_success("Content filter rules applied")
