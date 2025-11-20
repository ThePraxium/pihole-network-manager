"""
Maintenance and Updates Module

Manage Pi-hole updates, system maintenance tasks, service restarts,
and system resource monitoring.
"""

from typing import Dict, Any, Optional
from core.local_executor import execute_command, file_exists
from core.config import Config
from core.ui import (
    console, show_menu, show_table, show_status, show_error,
    show_success, show_warning, confirm_action, wait_for_enter,
    prompt_input, show_panel, clear_screen, show_key_value_list
)


def run(config: Config):
    """Main maintenance interface"""
    while True:
        # clear_screen()  # Disabled to preserve scroll history
        console.print("[bold cyan]Maintenance & Updates[/bold cyan]\n")

        options = [
            "Check for Updates",
            "Update Pi-hole",
            "Update System Packages",
            "Restart Pi-hole Services",
            "Restart System",
            "View System Resources",
            "Clean Old Logs",
            "Repair Pi-hole",
            "View Service Status"
        ]

        choice = show_menu("Maintenance Operations", options, allow_back=True)

        if choice == "9":
            break
        elif choice == "1":
            check_for_updates(config)
        elif choice == "2":
            update_pihole(config)
        elif choice == "3":
            update_system_packages(config)
        elif choice == "4":
            restart_pihole_services()
        elif choice == "5":
            restart_system()
        elif choice == "6":
            view_system_resources()
        elif choice == "7":
            clean_old_logs()
        elif choice == "8":
            repair_pihole()
        elif choice == "9":
            view_service_status()


def check_for_updates(config: Config):
    """Check for available updates"""
    show_status("Checking for Pi-hole updates...", "info")

    success, output, error = execute_command("pihole -v", sudo=False)

    if not success:
        show_error(f"Failed to check version: {error}")
        wait_for_enter()
        return

    console.print("\n[bold]Pi-hole Version Information:[/bold]\n")
    console.print(output)

    # Check for system updates
    console.print("\n[bold]Checking for system updates...[/bold]\n")

    success, update_output, _ = execute_command("apt-get update -qq && apt list --upgradable 2>/dev/null | grep -v 'Listing'", sudo=True)

    if success and update_output.strip():
        upgradable_count = len(update_output.strip().split('\n'))
        console.print(f"[yellow]{upgradable_count} system packages can be upgraded[/yellow]\n")

        if confirm_action("Show upgradable packages?", default=False):
            console.print(update_output)
    else:
        console.print("[green]System is up to date[/green]\n")

    wait_for_enter()


def update_pihole(config: Config):
    """Update Pi-hole to latest version"""
    console.print("\n[bold]Update Pi-hole[/bold]\n")

    if not confirm_action("Update Pi-hole now?", default=True):
        return

    show_status("Updating Pi-hole... (this may take several minutes)", "info")

    success, output, error = execute_command("pihole -up", sudo=True)

    console.print("\n" + output)

    if success:
        show_success("Pi-hole updated successfully")
    else:
        show_error("Pi-hole update failed")
        if error:
            console.print(f"\n[red]{error}[/red]")

    wait_for_enter()


def update_system_packages(config: Config):
    """Update system packages"""
    console.print("\n[bold]Update System Packages[/bold]\n")
    console.print("[yellow]This will update all system packages to their latest versions.[/yellow]\n")

    if not confirm_action("Update system packages now?", default=True):
        return

    show_status("Updating package list...", "info")

    execute_command("apt-get update -qq", sudo=True)

    show_status("Upgrading packages... (this may take several minutes)", "info")

    success, output, error = execute_command("apt-get upgrade -y", sudo=True)

    console.print("\n" + output)

    if success:
        show_success("System packages updated successfully")

        # Check if reboot is required
        if file_exists("/var/run/reboot-required"):
            show_warning("System reboot is recommended to apply updates")

            if confirm_action("Reboot now?", default=False):
                restart_system()
    else:
        show_error("System update failed")

    wait_for_enter()


def restart_pihole_services():
    """Restart Pi-hole services"""
    console.print("\n[bold]Restart Pi-hole Services[/bold]\n")

    if not confirm_action("Restart Pi-hole DNS service?", default=True):
        return

    show_status("Restarting Pi-hole DNS...", "info")

    success, output, error = execute_command("pihole restartdns", sudo=True)

    if success:
        show_success("Pi-hole DNS restarted successfully")
    else:
        show_error(f"Failed to restart: {error}")

    wait_for_enter()


def restart_system():
    """Restart the Pi-hole system"""
    console.print("\n[bold red]Restart System[/bold red]\n")
    console.print("[yellow]WARNING: This will reboot the Pi-hole server.[/yellow]\n")

    if not confirm_action("Restart system now?", default=False):
        return

    # Confirm again
    confirm_text = prompt_input("Type 'REBOOT' to confirm")

    if confirm_text != "REBOOT":
        show_warning("Cancelled")
        wait_for_enter()
        return

    show_status("Sending reboot command...", "info")

    execute_command("sudo reboot", sudo=False)

    show_success("Reboot command sent")
    console.print("\n[yellow]System is rebooting...[/yellow]\n")

    wait_for_enter()


def view_system_resources():
    """View system resource usage"""
    # clear_screen()  # Disabled to preserve scroll history
    console.print("[bold cyan]System Resources[/bold cyan]\n")

    show_status("Fetching system information...", "info")

    resources = {}

    # CPU usage
    success, cpu_output, _ = execute_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
    if success and cpu_output.strip():
        resources["CPU Usage"] = f"{cpu_output.strip()}%"

    # Memory usage
    success, mem_output, _ = execute_command("free -h | grep Mem | awk '{print $3 \"/\" $2 \" (\" int($3/$2 * 100) \"%)\"}'")
    if success and mem_output.strip():
        resources["Memory Usage"] = mem_output.strip()

    # Disk usage
    success, disk_output, _ = execute_command("df -h / | tail -1 | awk '{print $3 \"/\" $2 \" (\" $5 \")\"}'")
    if success and disk_output.strip():
        resources["Disk Usage"] = disk_output.strip()

    # Temperature (if available)
    success, temp_output, _ = execute_command("vcgencmd measure_temp 2>/dev/null | cut -d'=' -f2")
    if success and temp_output.strip():
        resources["CPU Temperature"] = temp_output.strip()

    # Uptime
    success, uptime_output, _ = execute_command("uptime -p")
    if success and uptime_output.strip():
        resources["Uptime"] = uptime_output.strip().replace("up ", "")

    # Load average
    success, load_output, _ = execute_command("cat /proc/loadavg | awk '{print $1, $2, $3}'")
    if success and load_output.strip():
        resources["Load Average"] = load_output.strip() + " (1m, 5m, 15m)"

    show_key_value_list(resources, "System Resources")

    # Process list
    console.print("[bold]Top Processes by CPU:[/bold]\n")

    success, ps_output, _ = execute_command("ps aux --sort=-%cpu | head -6 | tail -5 | awk '{print $11, $3\"%\"}'")

    if success and ps_output.strip():
        for line in ps_output.strip().split('\n'):
            console.print(f"  {line}")

    console.print()
    wait_for_enter()


def clean_old_logs():
    """Clean old log files"""
    console.print("\n[bold]Clean Old Logs[/bold]\n")

    # Check current log sizes
    show_status("Checking log sizes...", "info")

    success, size_output, _ = execute_command("du -sh /var/log/pihole* /var/log/pihole.log* 2>/dev/null | sort -h")

    if success and size_output.strip():
        console.print("\n[bold]Current Log Sizes:[/bold]\n")
        console.print(size_output)
        console.print()

    if not confirm_action("Clean old Pi-hole logs?", default=True):
        return

    show_status("Cleaning logs...", "info")

    # Flush Pi-hole logs
    success, _, error = execute_command("pihole flush", sudo=True)

    if success:
        show_success("Logs cleaned successfully")

        # Show new sizes
        success, new_size, _ = execute_command("du -sh /var/log/pihole.log 2>/dev/null")
        if success and new_size.strip():
            console.print(f"\nCurrent log size: {new_size.strip()}\n")
    else:
        show_error(f"Failed to clean logs: {error}")

    wait_for_enter()


def repair_pihole():
    """Run Pi-hole repair"""
    console.print("\n[bold]Repair Pi-hole[/bold]\n")
    console.print("This will attempt to repair Pi-hole installation issues.\n")

    if not confirm_action("Run Pi-hole repair?", default=True):
        return

    show_status("Running repair... (this may take several minutes)", "info")

    success, output, error = execute_command("pihole -r --reconfigure", sudo=True)

    console.print("\n" + output)

    if success:
        show_success("Pi-hole repair completed")
    else:
        show_error("Repair failed")
        if error:
            console.print(f"\n[red]{error}[/red]")

    wait_for_enter()


def view_service_status():
    """View status of Pi-hole related services"""
    # clear_screen()  # Disabled to preserve scroll history
    console.print("[bold cyan]Service Status[/bold cyan]\n")

    services = [
        ("pihole-FTL", "Pi-hole FTL (DNS/DHCP)"),
        ("lighttpd", "Web Interface"),
        ("ssh", "SSH Server")
    ]

    rows = []

    for service, description in services:
        # Check service status
        success, status_output, _ = execute_command(f"systemctl is-active {service}")

        status = status_output.strip()

        if status == "active":
            status_text = "[green]Running[/green]"
        elif status == "inactive":
            status_text = "[yellow]Stopped[/yellow]"
        else:
            status_text = "[red]Failed[/red]"

        # Get uptime
        success, uptime_output, _ = execute_command(f"systemctl show {service} --property=ActiveEnterTimestamp --value")

        uptime = uptime_output.strip() if uptime_output.strip() else "N/A"

        rows.append([service, description, status_text, uptime])

    show_table(
        title="Service Status",
        headers=["Service", "Description", "Status", "Started"],
        rows=rows,
        styles=["cyan", "white", "white", "yellow"]
    )

    console.print()
    wait_for_enter()
