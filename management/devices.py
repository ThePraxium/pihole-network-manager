"""
Device Management Module

View and manage network devices, configure per-device DNS settings,
view device query history and apply device-specific rules.
"""

import json
from typing import List, Dict, Any, Optional
from core.local_executor import execute_command
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen, show_key_value_list
)


def run(config: Config):
    """Main device management interface"""
    while True:
        clear_screen()
        console.print("[bold cyan]Device Management[/bold cyan]\n")

        options = [
            "View All Devices",
            "View Device Details",
            "Set Device DNS Override",
            "View Device Query History",
            "Add Device Alias/Name",
            "Search for Device",
            "Export Device List"
        ]

        choice = show_menu("Device Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            view_all_devices()
        elif choice == "2":
            view_device_details()
        elif choice == "3":
            set_device_dns_override()
        elif choice == "4":
            view_device_query_history()
        elif choice == "5":
            add_device_alias()
        elif choice == "6":
            search_device()
        elif choice == "7":
            export_device_list()


def view_all_devices():
    """Display all known network devices"""
    show_status("Fetching device information...", "info")

    # Get devices from FTL database (Pi-hole's network table)
    success, output, error = execute_command(
        "sqlite3 /etc/pihole/pihole-FTL.db 'SELECT DISTINCT ip, hwaddr, name FROM network ORDER BY ip;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch devices: {error}")
        wait_for_enter()
        return

    devices = []
    if output.strip():
        for line in output.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 3:
                ip, mac, name = parts[0], parts[1], parts[2] if parts[2] else "Unknown"
                devices.append([ip, mac, name])

    # Get additional devices from DHCP leases if available
    success, leases_output, _ = execute_command("cat /etc/pihole/dhcp.leases 2>/dev/null || echo ''")

    if success and leases_output.strip():
        for line in leases_output.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                # DHCP lease format: timestamp MAC IP hostname
                mac, ip, hostname = parts[1], parts[2], parts[3] if len(parts) > 3 else "Unknown"

                # Check if device already in list
                if not any(d[0] == ip for d in devices):
                    devices.append([ip, mac, hostname])

    if not devices:
        show_warning("No devices found")
        console.print("\n[yellow]Devices appear after they make DNS queries to Pi-hole[/yellow]")
        wait_for_enter()
        return

    # Sort by IP
    devices.sort(key=lambda x: tuple(int(part) for part in x[0].split('.')))

    show_table(
        title="Network Devices",
        headers=["IP Address", "MAC Address", "Device Name/Hostname"],
        rows=devices,
        styles=["cyan", "yellow", "white"]
    )

    console.print(f"\nTotal devices: {len(devices)}\n")
    wait_for_enter()


def view_device_details():
    """Display detailed information about a specific device"""
    device_ip = prompt_input("Enter device IP address")

    show_status(f"Fetching details for {device_ip}...", "info")

    # Get device info from network table
    success, output, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT ip, hwaddr, name, firstSeen, lastQuery, numQueries FROM network WHERE ip = '{device_ip}';\"",
        sudo=True
    )

    if not success or not output.strip():
        show_error(f"Device {device_ip} not found")
        wait_for_enter()
        return

    # Parse device info
    parts = output.strip().split('|')
    if len(parts) < 6:
        show_error("Invalid device data")
        wait_for_enter()
        return

    ip, mac, name, first_seen, last_query, num_queries = parts

    # Convert timestamps
    from datetime import datetime
    try:
        first_seen_dt = datetime.fromtimestamp(int(first_seen)).strftime("%Y-%m-%d %H:%M:%S") if first_seen else "Unknown"
        last_query_dt = datetime.fromtimestamp(int(last_query)).strftime("%Y-%m-%d %H:%M:%S") if last_query else "Never"
    except:
        first_seen_dt = "Unknown"
        last_query_dt = "Unknown"

    device_info = {
        "IP Address": ip,
        "MAC Address": mac,
        "Hostname": name if name else "Unknown",
        "First Seen": first_seen_dt,
        "Last Query": last_query_dt,
        "Total Queries": num_queries
    }

    console.print()
    show_key_value_list(device_info, f"Device Details: {ip}")

    # Get recent queries
    console.print("[bold]Recent Queries (Last 10):[/bold]\n")

    success, queries, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT timestamp, domain, status FROM queries WHERE client = '{device_ip}' ORDER BY timestamp DESC LIMIT 10;\"",
        sudo=True
    )

    if success and queries.strip():
        query_rows = []
        for line in queries.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 3:
                timestamp, domain, status = parts[0], parts[1], parts[2]

                try:
                    ts_dt = datetime.fromtimestamp(int(timestamp)).strftime("%H:%M:%S")
                except:
                    ts_dt = timestamp

                # Status codes: 1=blocked, 2=allowed, 3=cached, etc.
                status_map = {
                    "1": "[red]Blocked[/red]",
                    "2": "[green]Allowed[/green]",
                    "3": "[yellow]Cached[/yellow]",
                }
                status_text = status_map.get(status, f"Status {status}")

                query_rows.append([ts_dt, domain[:50], status_text])

        show_table(
            title="",
            headers=["Time", "Domain", "Status"],
            rows=query_rows,
            styles=["cyan", "white", "white"]
        )
    else:
        console.print("No recent queries\n")

    wait_for_enter()


def set_device_dns_override():
    """Configure custom DNS settings for a specific device"""
    console.print("\n[bold]Set Device DNS Override[/bold]\n")
    console.print("This feature requires dnsmasq configuration and router support.\n")

    device_ip = prompt_input("Device IP address")
    device_name = prompt_input("Device name/hostname (for reference)")

    console.print("\n[bold]DNS Options:[/bold]")
    console.print("  [1] Use Pi-hole (default)")
    console.print("  [2] Use specific DNS server")
    console.print("  [3] Bypass Pi-hole (direct to router/ISP)")

    dns_choice = prompt_input("Select option (1-3)", default="1")

    if dns_choice == "2":
        dns_server = prompt_input("DNS server IP address", default="1.1.1.1")
    elif dns_choice == "3":
        dns_server = "bypass"
    else:
        dns_server = "pihole"

    # Create dnsmasq config entry
    if dns_server == "bypass":
        # This would require router configuration
        show_warning("Bypass mode requires router-level configuration")
        console.print("\nYou need to configure your router to set specific DNS for this device.")
        console.print(f"Set device {device_ip} ({device_name}) to use your router's DNS.")
    elif dns_server == "pihole":
        show_status("Device will use Pi-hole (default behavior)")
    else:
        # Add dnsmasq config
        config_line = f"dhcp-option=tag:{device_ip.replace('.', '_')},6,{dns_server}"

        show_status("Configuring device-specific DNS...", "info")

        # Add to dnsmasq custom config
        success, _, error = execute_command(
            f"echo '# DNS override for {device_name} ({device_ip})' | sudo tee -a /etc/dnsmasq.d/04-custom-dns.conf",
            sudo=False
        )

        success, _, error = execute_command(
            f"echo '{config_line}' | sudo tee -a /etc/dnsmasq.d/04-custom-dns.conf",
            sudo=False
        )

        if success:
            # Restart dnsmasq
            execute_command("sudo systemctl restart dnsmasq")
            show_success(f"DNS override configured for {device_ip}")
            console.print(f"\nDevice will now use DNS server: {dns_server}")
        else:
            show_error("Failed to configure DNS override")

    wait_for_enter()


def view_device_query_history():
    """View comprehensive query history for a device"""
    device_ip = prompt_input("Enter device IP address")

    console.print("\n[bold]Query History Options:[/bold]")
    console.print("  [1] Last 24 hours")
    console.print("  [2] Last 7 days")
    console.print("  [3] All time")
    console.print("  [4] Custom time range")

    time_choice = prompt_input("Select option (1-4)", default="1")

    # Calculate time filter
    import time
    now = int(time.time())

    if time_choice == "1":
        time_filter = f"timestamp > {now - 86400}"
    elif time_choice == "2":
        time_filter = f"timestamp > {now - 604800}"
    elif time_choice == "3":
        time_filter = "1=1"
    else:
        hours = prompt_input("Hours to look back", default="24")
        time_filter = f"timestamp > {now - (int(hours) * 3600)}"

    show_status("Fetching query history...", "info")

    # Get query stats
    success, stats, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT COUNT(*), SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) FROM queries WHERE client = '{device_ip}' AND {time_filter};\"",
        sudo=True
    )

    if success and stats.strip():
        parts = stats.strip().split('|')
        total_queries = parts[0] if len(parts) > 0 else "0"
        blocked_queries = parts[1] if len(parts) > 1 else "0"

        console.print(f"\n[bold]Total Queries:[/bold] {total_queries}")
        console.print(f"[bold]Blocked:[/bold] {blocked_queries}")
        console.print(f"[bold]Allowed:[/bold] {int(total_queries) - int(blocked_queries)}")

    # Get top domains
    console.print("\n[bold]Top Queried Domains:[/bold]\n")

    success, top_domains, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT domain, COUNT(*) as count FROM queries WHERE client = '{device_ip}' AND {time_filter} GROUP BY domain ORDER BY count DESC LIMIT 20;\"",
        sudo=True
    )

    if success and top_domains.strip():
        domain_rows = []
        for line in top_domains.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 2:
                domain, count = parts[0], parts[1]
                domain_rows.append([domain[:60], count])

        show_table(
            title="",
            headers=["Domain", "Queries"],
            rows=domain_rows,
            styles=["white", "cyan"]
        )
    else:
        console.print("No queries found\n")

    wait_for_enter()


def add_device_alias():
    """Add or update a device alias/friendly name"""
    console.print("\n[bold]Add Device Alias[/bold]\n")

    device_ip = prompt_input("Device IP address")
    device_name = prompt_input("Friendly name/alias")

    show_status("Setting device name...", "info")

    # Update network table
    success, _, error = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"UPDATE network SET name = '{device_name}' WHERE ip = '{device_ip}';\"",
        sudo=True
    )

    if success:
        show_success(f"Device {device_ip} named as '{device_name}'")

        # Also add to /etc/hosts for local DNS resolution
        if confirm_action("Add to /etc/hosts for local DNS?", default=True):
            # Remove existing entry if present
            execute_command(f"sudo sed -i '/{device_ip}/d' /etc/hosts")

            # Add new entry
            execute_command(f"echo '{device_ip}    {device_name}' | sudo tee -a /etc/hosts > /dev/null")

            show_success(f"Added to /etc/hosts: {device_name} resolves to {device_ip}")
    else:
        show_error(f"Failed to set device name: {error}")

    wait_for_enter()


def search_device():
    """Search for devices by IP, MAC, or name"""
    console.print("\n[bold]Search Devices[/bold]\n")

    search_term = prompt_input("Enter IP, MAC, or name to search")

    show_status("Searching...", "info")

    # Search in network table
    success, output, _ = execute_command(
        f"sqlite3 /etc/pihole/pihole-FTL.db \"SELECT ip, hwaddr, name FROM network WHERE ip LIKE '%{search_term}%' OR hwaddr LIKE '%{search_term}%' OR name LIKE '%{search_term}%';\"",
        sudo=True
    )

    if not success or not output.strip():
        show_warning(f"No devices found matching '{search_term}'")
        wait_for_enter()
        return

    results = []
    for line in output.strip().split('\n'):
        parts = line.split('|')
        if len(parts) >= 3:
            ip, mac, name = parts[0], parts[1], parts[2] if parts[2] else "Unknown"
            results.append([ip, mac, name])

    show_table(
        title=f"Search Results for '{search_term}'",
        headers=["IP Address", "MAC Address", "Device Name"],
        rows=results,
        styles=["cyan", "yellow", "white"]
    )

    console.print(f"\nFound {len(results)} device(s)\n")
    wait_for_enter()


def export_device_list():
    """Export device list to CSV"""
    console.print("\n[bold]Export Device List[/bold]\n")

    local_file = prompt_input("Local file path to save", default="devices.csv")

    show_status("Fetching device list...", "info")

    # Get all devices
    success, output, error = execute_command(
        "sqlite3 /etc/pihole/pihole-FTL.db 'SELECT ip, hwaddr, name, firstSeen, lastQuery, numQueries FROM network ORDER BY ip;'",
        sudo=True
    )

    if not success:
        show_error(f"Failed to fetch devices: {error}")
        wait_for_enter()
        return

    if not output.strip():
        show_warning("No devices to export")
        wait_for_enter()
        return

    # Write to CSV
    try:
        with open(local_file, 'w') as f:
            f.write("IP Address,MAC Address,Name,First Seen,Last Query,Total Queries\n")

            for line in output.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 6:
                    ip, mac, name, first_seen, last_query, num_queries = parts
                    f.write(f"{ip},{mac},{name},{first_seen},{last_query},{num_queries}\n")

        show_success(f"Device list exported to {local_file}")
    except Exception as e:
        show_error(f"Failed to write file: {e}")

    wait_for_enter()
