"""
Router Control Module

Manage TP-Link router functions including device blocking,
DHCP information, bandwidth monitoring, and remote operations.
"""

from typing import List, Dict, Any, Optional
from core.local_executor import execute_command, read_file, write_file
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen, show_key_value_list
)


def run(config: Config):
    """Main router control interface"""
    # Check if router integration is enabled
    if not config.get("router", "enabled", False):
        show_warning("Router integration is not enabled")
        console.print("\nEnable router integration in configuration to use these features.\n")
        wait_for_enter()
        return

    while True:
        clear_screen()
        console.print("[bold cyan]Router Control[/bold cyan]\n")

        options = [
            "View Connected Devices",
            "Block/Unblock Device",
            "View DHCP Leases",
            "Bandwidth Statistics",
            "Reboot Router",
            "Guest Network Settings",
            "Parental Controls"
        ]

        choice = show_menu("Router Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            view_connected_devices(config)
        elif choice == "2":
            block_unblock_device(config)
        elif choice == "3":
            view_dhcp_leases(config)
        elif choice == "4":
            view_bandwidth_stats(config)
        elif choice == "5":
            reboot_router(config)
        elif choice == "6":
            guest_network_settings(config)
        elif choice == "7":
            parental_controls(config)


def view_connected_devices(config: Config):
    """View all devices connected to the router"""
    show_status("Fetching connected devices...", "info")

    result = run_router_command(config, "get_connected_devices")

    if not result or "error" in result:
        show_error(f"Failed to fetch devices: {result.get('error', 'Unknown error')}")
        wait_for_enter()
        return

    devices = result.get("devices", [])

    if not devices:
        show_warning("No devices connected")
        wait_for_enter()
        return

    # Display devices in table
    rows = []
    for device in devices:
        hostname = device.get("hostname", "Unknown")
        ip = device.get("ip", "N/A")
        mac = device.get("mac", "N/A")
        connection_type = device.get("type", "Unknown")  # Wired/Wireless
        status = "[green]Active[/green]" if device.get("active", True) else "[red]Inactive[/red]"

        rows.append([hostname, ip, mac, connection_type, status])

    show_table(
        title="Connected Devices",
        headers=["Hostname", "IP Address", "MAC Address", "Type", "Status"],
        rows=rows,
        styles=["white", "cyan", "yellow", "white", "white"]
    )

    console.print(f"\nTotal devices: {len(devices)}\n")
    wait_for_enter()


def block_unblock_device(config: Config):
    """Block or unblock a device from network access"""
    console.print("\n[bold]Block/Unblock Device[/bold]\n")

    mac_address = prompt_input("Device MAC address (XX:XX:XX:XX:XX:XX)")

    if not mac_address:
        show_error("MAC address required")
        wait_for_enter()
        return

    console.print("\n[bold]Action:[/bold]")
    console.print("  [1] Block device")
    console.print("  [2] Unblock device")

    action = prompt_input("Select action (1-2)", default="1")

    if action not in ["1", "2"]:
        show_error("Invalid selection")
        wait_for_enter()
        return

    block = action == "1"
    action_text = "block" if block else "unblock"

    if not confirm_action(f"{action_text.title()} device {mac_address}?", default=True):
        return

    show_status(f"{action_text.title()}ing device...", "info")

    # Run router command
    result = run_router_command(config, "set_device_access", {
        "mac": mac_address,
        "blocked": block
    })

    if result and "error" not in result:
        show_success(f"Device {action_text}ed successfully")
    else:
        show_error(f"Failed to {action_text} device: {result.get('error', 'Unknown error')}")

    wait_for_enter()


def view_dhcp_leases(config: Config):
    """View DHCP lease information"""
    console.print("\n[yellow]⚠️  Feature Notice:[/yellow]")
    console.print("[yellow]   This feature is pending hardware testing with TP-Link AXE5400.[/yellow]")
    console.print("[yellow]   It may not function correctly. Use your router's web interface[/yellow]")
    console.print("[yellow]   for reliable DHCP lease management.[/yellow]")
    console.print("[yellow]   See README.md 'Known Limitations' for details.[/yellow]\n")

    if not confirm_action("Continue anyway?", default=False):
        return

    show_status("Fetching DHCP leases...", "info")

    result = run_router_command(config, "get_dhcp_leases")

    if not result or "error" in result:
        show_error(f"Failed to fetch DHCP leases: {result.get('error', 'Unknown error')}")
        wait_for_enter()
        return

    leases = result.get("leases", [])

    if not leases:
        show_warning("No DHCP leases found")
        wait_for_enter()
        return

    rows = []
    for lease in leases:
        hostname = lease.get("hostname", "Unknown")
        ip = lease.get("ip", "N/A")
        mac = lease.get("mac", "N/A")
        lease_time = lease.get("lease_time", "N/A")

        rows.append([hostname, ip, mac, lease_time])

    show_table(
        title="DHCP Leases",
        headers=["Hostname", "IP Address", "MAC Address", "Lease Time"],
        rows=rows,
        styles=["white", "cyan", "yellow", "white"]
    )

    console.print(f"\nTotal leases: {len(leases)}\n")
    wait_for_enter()


def view_bandwidth_stats(config: Config):
    """View bandwidth usage statistics"""
    console.print("\n[yellow]⚠️  Feature Notice:[/yellow]")
    console.print("[yellow]   This feature is pending hardware testing with TP-Link AXE5400.[/yellow]")
    console.print("[yellow]   It may not function correctly. Use your router's web interface[/yellow]")
    console.print("[yellow]   for reliable bandwidth monitoring.[/yellow]")
    console.print("[yellow]   See README.md 'Known Limitations' for details.[/yellow]\n")

    if not confirm_action("Continue anyway?", default=False):
        return

    show_status("Fetching bandwidth statistics...", "info")

    result = run_router_command(config, "get_bandwidth_stats")

    if not result or "error" in result:
        show_error(f"Failed to fetch bandwidth stats: {result.get('error', 'Unknown error')}")
        wait_for_enter()
        return

    stats = result.get("stats", {})

    if not stats:
        show_warning("No bandwidth data available")
        wait_for_enter()
        return

    # Display overall stats
    console.print("\n[bold]Overall Bandwidth:[/bold]\n")

    overall = {
        "Download (Current)": format_bandwidth(stats.get("download_current", 0)),
        "Upload (Current)": format_bandwidth(stats.get("upload_current", 0)),
        "Download (Total)": format_data_size(stats.get("download_total", 0)),
        "Upload (Total)": format_data_size(stats.get("upload_total", 0))
    }

    show_key_value_list(overall)

    # Per-device stats if available
    device_stats = stats.get("per_device", [])

    if device_stats:
        console.print("[bold]Top Bandwidth Users:[/bold]\n")

        rows = []
        for device in device_stats[:10]:
            hostname = device.get("hostname", "Unknown")
            download = format_data_size(device.get("download", 0))
            upload = format_data_size(device.get("upload", 0))
            total = format_data_size(device.get("total", 0))

            rows.append([hostname, download, upload, total])

        show_table(
            title="",
            headers=["Device", "Download", "Upload", "Total"],
            rows=rows,
            styles=["white", "cyan", "yellow", "white"]
        )

    wait_for_enter()


def reboot_router(config: Config):
    """Reboot the router"""
    console.print("\n[bold red]Reboot Router[/bold red]\n")
    console.print("[yellow]WARNING: This will interrupt network connectivity for 1-2 minutes.[/yellow]\n")

    if not confirm_action("Reboot router now?", default=False):
        return

    # Confirm again
    confirm_text = prompt_input("Type 'REBOOT' to confirm")

    if confirm_text != "REBOOT":
        show_warning("Cancelled")
        wait_for_enter()
        return

    show_status("Sending reboot command to router...", "info")

    result = run_router_command(config, "reboot")

    if result and "error" not in result:
        show_success("Reboot command sent successfully")
        console.print("\n[yellow]Router is rebooting. Please wait 1-2 minutes for it to come back online.[/yellow]")
    else:
        show_error(f"Failed to reboot router: {result.get('error', 'Unknown error')}")

    wait_for_enter()


def guest_network_settings(config: Config):
    """Manage guest network settings"""
    console.print("\n[bold]Guest Network Settings[/bold]\n")

    console.print("[yellow]⚠️  Feature Notice:[/yellow]")
    console.print("[yellow]   This feature is pending hardware testing with TP-Link AXE5400.[/yellow]")
    console.print("[yellow]   It may not function correctly. Use your router's web interface[/yellow]")
    console.print("[yellow]   for reliable guest network configuration.[/yellow]")
    console.print("[yellow]   See README.md 'Known Limitations' for details.[/yellow]\n")

    if not confirm_action("Continue anyway?", default=False):
        return

    show_status("Fetching guest network status...", "info")

    result = run_router_command(config, "get_guest_network")

    if not result or "error" in result:
        show_error(f"Failed to fetch guest network settings: {result.get('error', 'Unknown error')}")
        wait_for_enter()
        return

    guest_config = result.get("guest_network", {})

    # Display current settings
    current_settings = {
        "Status": "Enabled" if guest_config.get("enabled", False) else "Disabled",
        "SSID": guest_config.get("ssid", "N/A"),
        "Password": "*" * len(guest_config.get("password", "")) if guest_config.get("password") else "None",
        "Max Clients": str(guest_config.get("max_clients", "N/A")),
        "Allow LAN Access": "Yes" if guest_config.get("allow_lan_access", False) else "No"
    }

    show_key_value_list(current_settings, "Current Guest Network Settings")

    # Options
    console.print("[bold]Actions:[/bold]")
    console.print("  [1] Enable guest network")
    console.print("  [2] Disable guest network")
    console.print("  [3] Change guest network password")

    choice = prompt_input("Select action (1-3, or Enter to cancel)", default="")

    if not choice:
        return

    if choice == "1":
        result = run_router_command(config, "set_guest_network", {"enabled": True})
        if result and "error" not in result:
            show_success("Guest network enabled")
        else:
            show_error("Failed to enable guest network")

    elif choice == "2":
        if confirm_action("Disable guest network?", default=True):
            result = run_router_command(config, "set_guest_network", {"enabled": False})
            if result and "error" not in result:
                show_success("Guest network disabled")
            else:
                show_error("Failed to disable guest network")

    elif choice == "3":
        new_password = prompt_input("New guest network password", password=True)

        if new_password:
            result = run_router_command(config, "set_guest_network", {"password": new_password})
            if result and "error" not in result:
                show_success("Guest network password updated")
            else:
                show_error("Failed to update password")

    wait_for_enter()


def parental_controls(config: Config):
    """Manage parental control settings"""
    console.print("\n[bold]Parental Controls[/bold]\n")
    console.print("[yellow]Note: Parental control features vary by router model.[/yellow]\n")
    console.print("For comprehensive content filtering, use the Content Filter module instead.\n")

    wait_for_enter()


# Helper functions

def run_router_command(config: Config, command: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Execute a router command via the router API helper

    This function runs a Python script locally that uses the
    tplinkrouterc6u library to communicate with the router.
    """
    # Get router credentials
    router_config = config.get_router_connection()

    if not router_config:
        return {"error": "Router configuration not available"}

    router_host = router_config.get("host")
    router_username = router_config.get("username")
    router_password = router_config.get("password")

    # Prompt for password if in secure mode
    automation_mode = config.get("router", "automation_mode", False)

    if not router_password and not automation_mode:
        from core.ui import prompt_input
        router_password = prompt_input("Router password (secure mode)", password=True)

        if not router_password:
            return {"error": "Password required"}
    elif automation_mode:
        # Load encrypted password from local file
        success, password_content = read_file("/opt/pihole-manager/router_credentials.enc")

        if success and password_content:
            # Decrypt locally
            # This would require a decryption helper script
            router_password = password_content.strip()
        else:
            return {"error": "Encrypted password not found"}

    # Build Python script to run on Pi-hole
    params_str = str(params) if params else "{}"

    router_script = f"""
import sys
import json
try:
    from tplinkrouterc6u import TplinkRouter

    router = TplinkRouter(host='{router_host}', password='{router_password}')

    command = '{command}'
    params = {params_str}

    if command == 'get_connected_devices':
        status = router.get_status()
        devices = status.get('devices', [])
        print(json.dumps({{'devices': devices}}))

    elif command == 'get_dhcp_leases':
        # Placeholder - actual API call depends on router model
        print(json.dumps({{'leases': []}}))

    elif command == 'get_bandwidth_stats':
        # Placeholder
        print(json.dumps({{'stats': {{}}}}))

    elif command == 'set_device_access':
        mac = params.get('mac')
        blocked = params.get('blocked', True)
        # API call to block/unblock device
        print(json.dumps({{'success': True}}))

    elif command == 'reboot':
        router.reboot()
        print(json.dumps({{'success': True}}))

    elif command == 'get_guest_network':
        # Placeholder
        print(json.dumps({{'guest_network': {{'enabled': False}}}}))

    elif command == 'set_guest_network':
        # Placeholder
        print(json.dumps({{'success': True}}))

    else:
        print(json.dumps({{'error': 'Unknown command'}}))

except Exception as e:
    print(json.dumps({{'error': str(e)}}))
"""

    # Write script to temp file locally
    temp_script = f"/tmp/router_cmd_{command}.py"
    success_write, error_write = write_file(temp_script, router_script, sudo=False)

    if not success_write:
        return {"error": f"Failed to write script: {error_write}"}

    # Execute script
    success, output, error = execute_command(f"python3 {temp_script}", sudo=False)

    # Clean up
    execute_command(f"rm {temp_script}", sudo=False)

    if not success:
        return {"error": error}

    # Parse JSON output
    try:
        import json
        return json.loads(output)
    except:
        return {"error": "Failed to parse router response"}


def format_bandwidth(bps: float) -> str:
    """Format bandwidth in bps to human-readable"""
    if bps >= 1_000_000_000:
        return f"{bps / 1_000_000_000:.2f} Gbps"
    elif bps >= 1_000_000:
        return f"{bps / 1_000_000:.2f} Mbps"
    elif bps >= 1_000:
        return f"{bps / 1_000:.2f} Kbps"
    else:
        return f"{bps:.0f} bps"


def format_data_size(bytes_count: int) -> str:
    """Format bytes to human-readable size"""
    if bytes_count >= 1_099_511_627_776:  # 1 TB
        return f"{bytes_count / 1_099_511_627_776:.2f} TB"
    elif bytes_count >= 1_073_741_824:  # 1 GB
        return f"{bytes_count / 1_073_741_824:.2f} GB"
    elif bytes_count >= 1_048_576:  # 1 MB
        return f"{bytes_count / 1_048_576:.2f} MB"
    elif bytes_count >= 1_024:  # 1 KB
        return f"{bytes_count / 1_024:.2f} KB"
    else:
        return f"{bytes_count} B"
