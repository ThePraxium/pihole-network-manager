"""
Whitelist/Blacklist Management Module

Manage exact and regex-based domain whitelists and blacklists.
Import/export lists and manage exceptions to blocklists.
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from core.local_executor import execute_command
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen
)


def run(config: Config):
    """Main whitelist/blacklist management interface"""
    while True:
        # clear_screen()  # Disabled to preserve scroll history
        console.print("[bold cyan]Whitelist / Blacklist Management[/bold cyan]\n")

        options = [
            "View Whitelist (Exact)",
            "View Whitelist (Regex)",
            "View Blacklist (Exact)",
            "View Blacklist (Regex)",
            "Add to Whitelist",
            "Add to Blacklist",
            "Remove from Lists",
            "Import List from File",
            "Export Lists",
            "Clear List"
        ]

        choice = show_menu("List Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            view_list("whitelist", exact=True)
        elif choice == "2":
            view_list("whitelist", exact=False)
        elif choice == "3":
            view_list("blacklist", exact=True)
        elif choice == "4":
            view_list("blacklist", exact=False)
        elif choice == "5":
            add_to_list("whitelist")
        elif choice == "6":
            add_to_list("blacklist")
        elif choice == "7":
            remove_from_list()
        elif choice == "8":
            import_list_from_file()
        elif choice == "9":
            export_lists()
        elif choice == "10":
            clear_list()


def view_list(list_type: str, exact: bool = True):
    """View whitelist or blacklist entries"""
    list_name = f"{list_type} ({'Exact' if exact else 'Regex'})"
    show_status(f"Fetching {list_name}...", "info")

    # Determine table name
    if list_type == "whitelist":
        table = "domainlist"
        type_filter = "type = 0" if exact else "type = 2"
    else:  # blacklist
        table = "domainlist"
        type_filter = "type = 1" if exact else "type = 3"

    # Query database
    success, output, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'SELECT id, domain, enabled, comment FROM {table} WHERE {type_filter} ORDER BY domain;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch {list_name}: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning(f"{list_name} is empty")
        wait_for_enter()
        return

    # Parse entries
    rows = []
    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 4:
            entry_id, domain, enabled, comment = parts[0], parts[1], parts[2], parts[3] if parts[3] else ""
            status = "[green]Enabled[/green]" if enabled == "1" else "[red]Disabled[/red]"

            rows.append([entry_id, domain[:60], status, comment[:30]])

    show_table(
        title=list_name,
        headers=["ID", "Domain/Pattern", "Status", "Comment"],
        rows=rows,
        styles=["cyan", "white", "white", "yellow"]
    )

    total = len(rows)
    enabled_count = sum(1 for row in rows if "[green]" in row[2])
    console.print(f"\nTotal: {total} entries ({enabled_count} enabled, {total - enabled_count} disabled)\n")

    wait_for_enter()


def add_to_list(list_type: str):
    """Add domain to whitelist or blacklist"""
    console.print(f"\n[bold]Add to {list_type.title()}[/bold]\n")

    console.print("[bold]Entry Type:[/bold]")
    console.print("  [1] Exact domain (e.g., example.com)")
    console.print("  [2] Regex pattern (e.g., .*\\.example\\.com)")

    entry_type = prompt_input("Select type (1-2)", default="1")
    is_regex = entry_type == "2"

    # Get domain/pattern
    if is_regex:
        console.print("\n[yellow]Regex Tips:[/yellow]")
        console.print("  - Use .* for wildcard")
        console.print("  - Escape dots: \\.")
        console.print("  - Example: .*\\.ads\\.example\\.com")
        pattern = prompt_input("Regex pattern")

        # Validate regex
        try:
            re.compile(pattern)
        except re.error as e:
            show_error(f"Invalid regex: {e}")
            wait_for_enter()
            return

        domain = pattern
    else:
        domain = prompt_input("Domain name (e.g., example.com)")

        # Basic domain validation
        if not domain or ' ' in domain:
            show_error("Invalid domain name")
            wait_for_enter()
            return

    comment = prompt_input("Comment (optional)", default="")

    # Determine type value
    # type: 0=whitelist exact, 1=blacklist exact, 2=whitelist regex, 3=blacklist regex
    if list_type == "whitelist":
        type_val = 2 if is_regex else 0
    else:
        type_val = 3 if is_regex else 1

    # Escape quotes
    domain = domain.replace("'", "''")
    comment = comment.replace("'", "''")

    show_status(f"Adding to {list_type}...", "info")

    # Insert into database
    success, _, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO domainlist (type, domain, enabled, comment) VALUES ({type_val}, '{domain}', 1, '{comment}');\"",
        sudo=True
    )

    if success:
        show_success(f"Added '{domain}' to {list_type}")

        # Reload lists
        console.print("\n[yellow]Reloading Pi-hole...[/yellow]")
        execute_command("pihole restartdns reload-lists", sudo=True)
        show_success("Lists reloaded")
    else:
        show_error(f"Failed to add entry: {error}")

    wait_for_enter()


def remove_from_list():
    """Remove entry from any list"""
    console.print("\n[bold]Remove from List[/bold]\n")

    entry_id = prompt_input("Entry ID to remove")

    if not entry_id.isdigit():
        show_error("Invalid ID")
        wait_for_enter()
        return

    # Get entry details
    success, output, _ = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'SELECT domain, type FROM domainlist WHERE id = {entry_id};'",
        sudo=True
    )

    if not success or not output.strip():
        show_error(f"Entry ID {entry_id} not found")
        wait_for_enter()
        return

    parts = output.strip().split('|')
    domain = parts[0] if len(parts) > 0 else "Unknown"
    entry_type = parts[1] if len(parts) > 1 else "Unknown"

    # Map type to list name
    type_map = {
        "0": "Whitelist (Exact)",
        "1": "Blacklist (Exact)",
        "2": "Whitelist (Regex)",
        "3": "Blacklist (Regex)"
    }
    list_name = type_map.get(entry_type, "Unknown")

    console.print(f"\n[bold]Entry:[/bold] {domain}")
    console.print(f"[bold]List:[/bold] {list_name}\n")

    if not confirm_action(f"Remove this entry?", default=False):
        return

    show_status("Removing entry...", "info")

    # Delete from database
    success, _, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'DELETE FROM domainlist WHERE id = {entry_id};'",
        sudo=True
    )

    if success:
        show_success("Entry removed")

        # Reload lists
        console.print("\n[yellow]Reloading Pi-hole...[/yellow]")
        execute_command("pihole restartdns reload-lists", sudo=True)
        show_success("Lists reloaded")
    else:
        show_error(f"Failed to remove entry: {error}")

    wait_for_enter()


def import_list_from_file():
    """Import domains from a local file"""
    console.print("\n[bold]Import List from File[/bold]\n")
    console.print("File should contain one domain per line\n")

    local_file = prompt_input("Local file path")

    if not Path(local_file).exists():
        show_error(f"File not found: {local_file}")
        wait_for_enter()
        return

    # Read file
    try:
        with open(local_file, 'r') as f:
            domains = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        show_error(f"Failed to read file: {e}")
        wait_for_enter()
        return

    console.print(f"\nFound {len(domains)} domains in file\n")

    # Select list type
    console.print("[bold]Add to:[/bold]")
    console.print("  [1] Whitelist (Exact)")
    console.print("  [2] Blacklist (Exact)")
    console.print("  [3] Whitelist (Regex)")
    console.print("  [4] Blacklist (Regex)")

    list_choice = prompt_input("Select list (1-4)", default="1")

    type_map = {
        "1": 0,  # whitelist exact
        "2": 1,  # blacklist exact
        "3": 2,  # whitelist regex
        "4": 3   # blacklist regex
    }

    type_val = type_map.get(list_choice, 0)

    comment = prompt_input("Comment for all entries (optional)", default="Imported")
    comment = comment.replace("'", "''")

    if not confirm_action(f"Import {len(domains)} domains?", default=True):
        return

    show_status("Importing domains...", "info")

    imported = 0
    for domain in domains:
        domain_escaped = domain.replace("'", "''")

        success, _, _ = execute_command(
            f"sqlite3 /etc/pihole/gravity.db \"INSERT INTO domainlist (type, domain, enabled, comment) VALUES ({type_val}, '{domain_escaped}', 1, '{comment}');\"",
            sudo=True
        )

        if success:
            imported += 1

    show_success(f"Imported {imported} of {len(domains)} domains")

    # Reload lists
    if imported > 0:
        console.print("\n[yellow]Reloading Pi-hole...[/yellow]")
        execute_command("pihole restartdns reload-lists", sudo=True)
        show_success("Lists reloaded")

    wait_for_enter()


def export_lists():
    """Export whitelist and blacklist to files"""
    console.print("\n[bold]Export Lists[/bold]\n")

    console.print("[bold]Select lists to export:[/bold]")
    console.print("  [1] Whitelist (Exact)")
    console.print("  [2] Blacklist (Exact)")
    console.print("  [3] Whitelist (Regex)")
    console.print("  [4] Blacklist (Regex)")
    console.print("  [5] All Lists")

    export_choice = prompt_input("Select option (1-5)", default="5")

    # Map choices to type values
    export_types = []
    if export_choice == "1":
        export_types = [(0, "whitelist_exact.txt")]
    elif export_choice == "2":
        export_types = [(1, "blacklist_exact.txt")]
    elif export_choice == "3":
        export_types = [(2, "whitelist_regex.txt")]
    elif export_choice == "4":
        export_types = [(3, "blacklist_regex.txt")]
    else:
        export_types = [
            (0, "whitelist_exact.txt"),
            (1, "blacklist_exact.txt"),
            (2, "whitelist_regex.txt"),
            (3, "blacklist_regex.txt")
        ]

    show_status("Exporting lists...", "info")

    for type_val, filename in export_types:
        # Fetch list
        success, output, _ = execute_command(
            f"sqlite3 /etc/pihole/gravity.db 'SELECT domain FROM domainlist WHERE type = {type_val} AND enabled = 1;'",
            sudo=True
        )

        if not success or not output.strip():
            console.print(f"[yellow]Skipping {filename} (empty)[/yellow]")
            continue

        domains = output.strip().split('\n')

        # Write to file
        try:
            with open(filename, 'w') as f:
                f.write(f"# Pi-hole List Export - Type {type_val}\n")
                f.write(f"# Total: {len(domains)} entries\n\n")
                for domain in domains:
                    f.write(f"{domain}\n")

            console.print(f"[green]✓[/green] Exported {len(domains)} entries to {filename}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to write {filename}: {e}")

    console.print()
    wait_for_enter()


def clear_list():
    """Clear entire whitelist or blacklist"""
    console.print("\n[bold red]Clear List[/bold red]\n")
    console.print("[yellow]WARNING: This will remove all entries from the selected list![/yellow]\n")

    console.print("[bold]Select list to clear:[/bold]")
    console.print("  [1] Whitelist (Exact)")
    console.print("  [2] Blacklist (Exact)")
    console.print("  [3] Whitelist (Regex)")
    console.print("  [4] Blacklist (Regex)")

    list_choice = prompt_input("Select list (1-4)")

    type_map = {
        "1": (0, "Whitelist (Exact)"),
        "2": (1, "Blacklist (Exact)"),
        "3": (2, "Whitelist (Regex)"),
        "4": (3, "Blacklist (Regex)")
    }

    if list_choice not in type_map:
        show_error("Invalid selection")
        wait_for_enter()
        return

    type_val, list_name = type_map[list_choice]

    # Count entries
    success, count_output, _ = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'SELECT COUNT(*) FROM domainlist WHERE type = {type_val};'",
        sudo=True
    )

    entry_count = count_output.strip() if success else "?"

    console.print(f"\n[bold]List:[/bold] {list_name}")
    console.print(f"[bold]Entries:[/bold] {entry_count}\n")

    if not confirm_action(f"Clear {list_name}? This cannot be undone!", default=False):
        return

    # Confirm again
    confirm_text = prompt_input(f"Type 'DELETE' to confirm")

    if confirm_text != "DELETE":
        show_warning("Cancelled")
        wait_for_enter()
        return

    show_status(f"Clearing {list_name}...", "info")

    # Delete all entries
    success, _, error = execute_command(
        f"sqlite3 /etc/pihole/gravity.db 'DELETE FROM domainlist WHERE type = {type_val};'",
        sudo=True
    )

    if success:
        show_success(f"{list_name} cleared")

        # Reload lists
        console.print("\n[yellow]Reloading Pi-hole...[/yellow]")
        execute_command("pihole restartdns reload-lists", sudo=True)
        show_success("Lists reloaded")
    else:
        show_error(f"Failed to clear list: {error}")

    wait_for_enter()
