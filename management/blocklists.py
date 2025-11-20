"""
Blocklist Management Module

Manage Pi-hole blocklist sources and profiles.
Switch between Light/Moderate/Aggressive profiles or create custom lists.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.local_executor import execute_command, read_file, file_exists
from core.config import Config, get_project_root
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen
)


PROFILES_DIR = get_project_root() / "profiles"


def run(config: Config):
    """Main blocklist management interface"""
    while True:
        # clear_screen()  # Disabled to preserve scroll history
        console.print("[bold cyan]Blocklist Management[/bold cyan]\n")

        options = [
            "View Current Blocklists",
            "Switch Blocklist Profile",
            "Add Custom Blocklist",
            "Remove Blocklist",
            "Import Blocklist URLs from File",
            "Export Current Blocklists",
            "Update Gravity (Apply Changes)",
            "View Profile Details"
        ]

        choice = show_menu("Blocklist Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            view_current_blocklists()
        elif choice == "2":
            switch_profile(config)
        elif choice == "3":
            add_custom_blocklist()
        elif choice == "4":
            remove_blocklist()
        elif choice == "5":
            import_blocklists_from_file()
        elif choice == "6":
            export_blocklists()
        elif choice == "7":
            update_gravity()
        elif choice == "8":
            view_profile_details()


def view_current_blocklists():
    """Display currently configured blocklists"""
    show_status("Fetching current blocklists...", "info")

    # Query Pi-hole database for adlists
    success, output, error = execute_command(
        "sqlite3 /etc/pihole/gravity.db 'SELECT id, address, enabled, comment FROM adlist ORDER BY id;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch blocklists: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No blocklists configured")
        wait_for_enter()
        return

    # Parse output
    rows = []
    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 4:
            list_id, url, enabled, comment = parts[0], parts[1], parts[2], parts[3] if parts[3] else "No description"
            status = "[green]Enabled[/green]" if enabled == "1" else "[red]Disabled[/red]"

            # Truncate URL if too long
            display_url = url if len(url) <= 60 else url[:57] + "..."

            rows.append([list_id, display_url, status, comment[:30]])

    show_table(
        title="Current Blocklists",
        headers=["ID", "URL", "Status", "Comment"],
        rows=rows,
        styles=["cyan", "white", "white", "yellow"]
    )

    # Show summary
    total = len(rows)
    enabled = sum(1 for row in rows if "[green]" in row[2])
    console.print(f"\nTotal: {total} blocklists ({enabled} enabled, {total - enabled} disabled)\n")

    wait_for_enter()


def switch_profile(config: Config):
    """Switch to a different blocklist profile"""
    console.print("\n[bold]Available Profiles:[/bold]\n")

    profiles = {
        "1": ("light", "Light - ~100K domains (minimal breakage)"),
        "2": ("moderate", "Moderate - ~300K domains (recommended)"),
        "3": ("aggressive", "Aggressive - ~1M+ domains (may break sites)")
    }

    for key, (name, desc) in profiles.items():
        console.print(f"  [{key}] {desc}")

    console.print()
    choice = prompt_input("Select profile (1-3)", default="2")

    if choice not in profiles:
        show_error("Invalid profile selection")
        wait_for_enter()
        return

    profile_name, profile_desc = profiles[choice]

    # Show profile details
    profile_data = get_profile_data(profile_name)
    if not profile_data:
        show_error(f"Profile '{profile_name}' not found on Pi-hole")
        wait_for_enter()
        return

    console.print(f"\n[bold]Profile:[/bold] {profile_data.get('name', profile_name)}")
    console.print(f"[bold]Description:[/bold] {profile_data.get('description', 'N/A')}")
    console.print(f"[bold]Domains:[/bold] ~{profile_data.get('estimated_domains', 'Unknown')}")
    console.print(f"[bold]Lists:[/bold] {len(profile_data.get('blocklists', []))}")

    if profile_data.get('warnings'):
        console.print(f"\n[yellow]Warnings:[/yellow]")
        for warning in profile_data['warnings']:
            console.print(f"  - {warning}")

    console.print()

    if not confirm_action(f"Switch to {profile_name} profile?", default=True):
        return

    # Apply profile
    show_status(f"Applying {profile_name} profile...", "info")

    # Clear current adlists
    success, _, error = execute_command(
        "sqlite3 /etc/pihole/gravity.db 'DELETE FROM adlist;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to clear adlists: {error}")
        wait_for_enter()
        return

    # Insert new adlists
    blocklists = profile_data.get('blocklists', [])
    for blocklist in blocklists:
        url = blocklist.get('url', '')
        comment = blocklist.get('comment', '').replace("'", "''")  # Escape quotes

        execute_command(
            f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO adlist (address, enabled, comment) VALUES ('{url}', 1, '{comment}');\"",
            sudo=True
        )

    show_success(f"Profile '{profile_name}' applied successfully")
    console.print("\n[yellow]Run 'Update Gravity' to download and apply the blocklists[/yellow]")

    # Save preference
    config.set("preferences", "default_profile", profile_name)
    config.save()

    wait_for_enter()


def add_custom_blocklist():
    """Add a custom blocklist URL"""
    console.print("\n[bold]Add Custom Blocklist[/bold]\n")

    url = prompt_input("Blocklist URL")

    if not url.startswith("http://") and not url.startswith("https://"):
        show_error("URL must start with http:// or https://")
        wait_for_enter()
        return

    comment = prompt_input("Description/Comment (optional)", default="Custom blocklist")

    # Escape quotes
    comment = comment.replace("'", "''")
    url = url.replace("'", "''")

    # Insert into database
    show_status("Adding blocklist...", "info")

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO adlist (address, enabled, comment) VALUES ('{url}', 1, '{comment}');\"",
        sudo=True
    )

    if success:
        show_success("Blocklist added successfully")
        console.print("\n[yellow]Run 'Update Gravity' to download and apply the blocklist[/yellow]")
    else:
        show_error(f"Failed to add blocklist: {error}")

    wait_for_enter()


def remove_blocklist():
    """Remove a blocklist by ID"""
    # Show current lists
    view_current_blocklists()

    console.print("\n[bold]Remove Blocklist[/bold]\n")

    list_id = prompt_input("Enter blocklist ID to remove")

    if not list_id.isdigit():
        show_error("Invalid ID")
        wait_for_enter()
        return

    if not confirm_action(f"Remove blocklist ID {list_id}?", default=False):
        return

    # Delete from database
    show_status("Removing blocklist...", "info")

    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'DELETE FROM adlist WHERE id = {list_id};'",
        sudo=True
    )

    if success:
        show_success("Blocklist removed successfully")
        console.print("\n[yellow]Run 'Update Gravity' to apply changes[/yellow]")
    else:
        show_error(f"Failed to remove blocklist: {error}")

    wait_for_enter()


def import_blocklists_from_file():
    """Import blocklist URLs from a local file"""
    console.print("\n[bold]Import Blocklists from File[/bold]\n")
    console.print("File should contain one URL per line\n")

    local_file = prompt_input("Local file path")

    if not Path(local_file).exists():
        show_error(f"File not found: {local_file}")
        wait_for_enter()
        return

    # Read file
    try:
        with open(local_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        show_error(f"Failed to read file: {e}")
        wait_for_enter()
        return

    console.print(f"\nFound {len(urls)} URLs in file")

    if not confirm_action("Import these blocklists?", default=True):
        return

    # Import each URL
    show_status("Importing blocklists...", "info")

    imported = 0
    for url in urls:
        if not url.startswith("http://") and not url.startswith("https://"):
            console.print(f"[yellow]Skipping invalid URL: {url}[/yellow]")
            continue

        url_escaped = url.replace("'", "''")
        success, _, _ = execute_command(
            f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO adlist (address, enabled, comment) VALUES ('{url_escaped}', 1, 'Imported');\"",
            sudo=True
        )

        if success:
            imported += 1

    show_success(f"Imported {imported} of {len(urls)} blocklists")
    console.print("\n[yellow]Run 'Update Gravity' to download and apply the blocklists[/yellow]")

    wait_for_enter()


def export_blocklists():
    """Export current blocklists to a local file"""
    console.print("\n[bold]Export Blocklists[/bold]\n")

    local_file = prompt_input("Local file path to save", default="blocklists.txt")

    # Fetch blocklists
    show_status("Fetching blocklists...", "info")

    success, output, error = execute_command(
        "sqlite3 /etc/pihole/gravity.db 'SELECT address FROM adlist WHERE enabled = 1;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch blocklists: {error}")
        wait_for_enter()
        return

    urls = [line.strip() for line in output.strip().split('\n') if line.strip()]

    if not urls:
        show_warning("No enabled blocklists to export")
        wait_for_enter()
        return

    # Write to file
    try:
        with open(local_file, 'w') as f:
            f.write("# Pi-hole Blocklists Export\n")
            f.write(f"# Total: {len(urls)} lists\n\n")
            for url in urls:
                f.write(f"{url}\n")

        show_success(f"Exported {len(urls)} blocklists to {local_file}")
    except Exception as e:
        show_error(f"Failed to write file: {e}")

    wait_for_enter()


def update_gravity():
    """Run pihole -g to update gravity database"""
    console.print("\n[bold]Update Gravity[/bold]\n")
    console.print("This will download all configured blocklists and rebuild the gravity database.\n")
    console.print("[yellow]This may take several minutes depending on the number of lists.[/yellow]\n")

    if not confirm_action("Update gravity now?", default=True):
        return

    show_status("Updating gravity... (this may take a few minutes)", "info")

    # Run pihole -g
    success, output, error = execute_command("pihole -g", sudo=True)

    console.print("\n" + output)

    if success:
        show_success("Gravity updated successfully")

        # Show domain count
        success, count, _ = execute_command(
            "sqlite3 /etc/pihole/gravity.db 'SELECT COUNT(*) FROM gravity;'",
            sudo=True
        )

        if success and count.strip():
            console.print(f"\n[bold]Total domains blocked:[/bold] {count.strip()}")
    else:
        show_error("Gravity update failed")
        if error:
            console.print(f"\n[red]{error}[/red]")

    wait_for_enter()


def view_profile_details():
    """Display detailed information about profiles"""
    console.print("\n[bold]Profile Details[/bold]\n")

    profiles = ["light", "moderate", "aggressive"]

    for profile_name in profiles:
        profile_data = get_profile_data(profile_name)

        if not profile_data:
            continue

        console.print(f"\n[bold cyan]{profile_data.get('name', profile_name).upper()}[/bold cyan]")
        console.print(f"Description: {profile_data.get('description', 'N/A')}")
        console.print(f"Estimated Domains: ~{profile_data.get('estimated_domains', 'Unknown')}")
        console.print(f"Blocklists: {len(profile_data.get('blocklists', []))}")

        if profile_data.get('warnings'):
            console.print(f"Warnings: {', '.join(profile_data['warnings'])}")

        console.print()

    wait_for_enter()


def get_profile_data(profile_name: str) -> Optional[Dict[str, Any]]:
    """Load profile data from Pi-hole"""
    profile_path = f"{PROFILES_DIR}/{profile_name}.yaml"

    # Check if profile exists
    if not file_exists(profile_path):
        return None

    # Read profile file
    success, content = read_file(profile_path)
    if not success or not content:
        return None

    try:
        return yaml.safe_load(content)
    except Exception:
        return None
