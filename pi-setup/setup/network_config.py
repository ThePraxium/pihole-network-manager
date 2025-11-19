"""
Network Configuration Module

Configures network settings including:
- Static IP address configuration
- Gateway and DNS settings
- Network interface validation
- Connectivity testing
- /etc/hosts configuration
"""

import subprocess
import socket
from pathlib import Path
from rich.prompt import Prompt, Confirm


def run_command(cmd, check=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def get_current_ip():
    """Get current IP address"""
    success, stdout, _ = run_command("hostname -I | awk '{print $1}'")
    if success:
        return stdout.strip()
    return None


def get_current_gateway():
    """Get current gateway"""
    success, stdout, _ = run_command("ip route | grep default | awk '{print $3}'")
    if success:
        return stdout.strip()
    return None


def get_network_interface():
    """Get primary network interface"""
    # Try to get the interface connected to the default route
    success, stdout, _ = run_command("ip route | grep default | awk '{print $5}'")
    if success and stdout.strip():
        return stdout.strip()

    # Fallback: get first non-loopback interface
    success, stdout, _ = run_command("ip -o link show | awk -F': ' '{print $2}' | grep -v lo | head -1")
    if success:
        return stdout.strip()

    return "eth0"  # Default fallback


def validate_ip_address(ip):
    """Validate IP address format"""
    try:
        socket.inet_aton(ip)
        parts = ip.split('.')
        if len(parts) == 4 and all(0 <= int(p) <= 255 for p in parts):
            return True
    except (socket.error, ValueError):
        pass
    return False


def prompt_network_settings(console, config):
    """Prompt user for network settings"""
    console.print("\n[bold]Network Configuration[/bold]\n")

    # Show current settings
    current_ip = get_current_ip()
    current_gateway = get_current_gateway()
    current_interface = get_network_interface()

    console.print(f"[cyan]Current Settings:[/cyan]")
    console.print(f"  • IP Address: {current_ip}")
    console.print(f"  • Gateway: {current_gateway}")
    console.print(f"  • Interface: {current_interface}")
    console.print()

    # Ask if user wants to configure static IP
    use_static = Confirm.ask(
        "Would you like to configure a static IP address?",
        default=True
    )

    if not use_static:
        console.print("[yellow]Skipping static IP configuration - will use DHCP[/yellow]")
        return None

    # Get static IP
    while True:
        static_ip = Prompt.ask(
            "Enter static IP address for Pi-hole",
            default=current_ip if current_ip else "192.168.1.100"
        )
        if validate_ip_address(static_ip):
            break
        console.print("[red]Invalid IP address format. Please try again.[/red]")

    # Get gateway
    while True:
        gateway = Prompt.ask(
            "Enter gateway IP address",
            default=current_gateway if current_gateway else "192.168.1.1"
        )
        if validate_ip_address(gateway):
            break
        console.print("[red]Invalid gateway address. Please try again.[/red]")

    # Get DNS servers
    dns_input = Prompt.ask(
        "Enter DNS servers (comma-separated)",
        default="1.1.1.1,8.8.8.8"
    )
    dns_servers = [dns.strip() for dns in dns_input.split(',')]

    # Validate DNS servers
    valid_dns = []
    for dns in dns_servers:
        if validate_ip_address(dns):
            valid_dns.append(dns)
        else:
            console.print(f"[yellow]Warning: Skipping invalid DNS server: {dns}[/yellow]")

    if not valid_dns:
        console.print("[yellow]No valid DNS servers provided. Using defaults: 1.1.1.1, 8.8.8.8[/yellow]")
        valid_dns = ["1.1.1.1", "8.8.8.8"]

    # Get subnet mask
    subnet_mask = Prompt.ask(
        "Enter subnet mask",
        default="255.255.255.0"
    )

    # Confirm settings
    console.print("\n[bold cyan]Network Configuration Summary:[/bold cyan]")
    console.print(f"  • Static IP: {static_ip}")
    console.print(f"  • Gateway: {gateway}")
    console.print(f"  • DNS Servers: {', '.join(valid_dns)}")
    console.print(f"  • Subnet Mask: {subnet_mask}")
    console.print(f"  • Interface: {current_interface}")
    console.print()

    confirm = Confirm.ask("Apply these settings?", default=True)

    if not confirm:
        console.print("[yellow]Network configuration cancelled[/yellow]")
        return None

    return {
        "static_ip": static_ip,
        "gateway": gateway,
        "dns_servers": valid_dns,
        "subnet_mask": subnet_mask,
        "interface": current_interface
    }


def configure_static_ip_dhcpcd(settings, console):
    """Configure static IP using dhcpcd.conf"""
    console.print("\n[bold]Configuring Static IP Address...[/bold]")

    dhcpcd_conf = Path("/etc/dhcpcd.conf")

    # Backup original config
    console.print("  • Backing up original dhcpcd.conf...")
    run_command(f"cp {dhcpcd_conf} {dhcpcd_conf}.backup")

    # Read existing config
    try:
        with open(dhcpcd_conf, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        console.print(f"[red]✗ Failed to read dhcpcd.conf: {e}[/red]")
        return False

    # Remove any existing static configuration for this interface
    console.print("  • Removing old static IP configuration...")
    new_lines = []
    skip_until_blank = False

    for line in lines:
        if f"interface {settings['interface']}" in line:
            skip_until_blank = True
            continue
        if skip_until_blank:
            if line.strip() == "" or not line.startswith(" "):
                skip_until_blank = False
            else:
                continue
        new_lines.append(line)

    # Add new static configuration
    console.print("  • Adding new static IP configuration...")
    static_config = f"""
# Static IP configuration for Pi-hole
interface {settings['interface']}
static ip_address={settings['static_ip']}/24
static routers={settings['gateway']}
static domain_name_servers={' '.join(settings['dns_servers'])}
"""

    new_lines.append(static_config)

    # Write updated config
    try:
        with open(dhcpcd_conf, 'w') as f:
            f.writelines(new_lines)
        console.print("  • Configuration written to /etc/dhcpcd.conf")
    except Exception as e:
        console.print(f"[red]✗ Failed to write dhcpcd.conf: {e}[/red]")
        return False

    console.print("[green]✓ Static IP configured[/green]")
    console.print("[yellow]  Note: Changes will take effect after reboot or network restart[/yellow]")

    return True


def configure_static_ip_networkmanager(settings, console):
    """Configure static IP using NetworkManager (alternative method)"""
    console.print("\n[bold]Configuring Static IP via NetworkManager...[/bold]")

    interface = settings['interface']
    static_ip = settings['static_ip']
    gateway = settings['gateway']
    dns_servers = ','.join(settings['dns_servers'])

    # Get connection name
    success, stdout, _ = run_command(f"nmcli -t -f NAME,DEVICE connection show | grep {interface} | cut -d: -f1")
    connection_name = stdout.strip() if success else interface

    if not connection_name:
        connection_name = interface

    console.print(f"  • Modifying connection: {connection_name}")

    # Configure static IP
    commands = [
        f"nmcli connection modify '{connection_name}' ipv4.method manual",
        f"nmcli connection modify '{connection_name}' ipv4.addresses {static_ip}/24",
        f"nmcli connection modify '{connection_name}' ipv4.gateway {gateway}",
        f"nmcli connection modify '{connection_name}' ipv4.dns '{dns_servers}'",
        f"nmcli connection down '{connection_name}'",
        f"nmcli connection up '{connection_name}'"
    ]

    for cmd in commands:
        success, stdout, stderr = run_command(cmd, check=False)
        if not success:
            console.print(f"[yellow]Warning: {cmd} failed: {stderr}[/yellow]")

    console.print("[green]✓ NetworkManager configuration applied[/green]")
    return True


def update_hosts_file(console, config):
    """Update /etc/hosts with Pi-hole hostname"""
    console.print("\n[bold]Updating /etc/hosts...[/bold]")

    hosts_file = Path("/etc/hosts")
    hostname = config.config.get("pihole", {}).get("hostname", "pihole")
    static_ip = config.config.get("pihole", {}).get("static_ip", "")

    if not static_ip:
        console.print("[yellow]No static IP configured, skipping /etc/hosts update[/yellow]")
        return True

    # Backup
    run_command(f"cp {hosts_file} {hosts_file}.backup")

    try:
        with open(hosts_file, 'r') as f:
            lines = f.readlines()

        # Add Pi-hole entry
        new_lines = []
        pihole_entry_added = False

        for line in lines:
            # Skip existing pihole entries
            if hostname in line and not line.strip().startswith('#'):
                continue
            new_lines.append(line)

        # Add new entry
        new_lines.append(f"{static_ip}    {hostname}\n")

        with open(hosts_file, 'w') as f:
            f.writelines(new_lines)

        console.print(f"  • Added entry: {static_ip}    {hostname}")
        console.print("[green]✓ /etc/hosts updated[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to update /etc/hosts: {e}[/red]")
        return False


def test_connectivity(console):
    """Test network connectivity"""
    console.print("\n[bold]Testing Network Connectivity...[/bold]")

    tests = [
        ("Gateway", "ping -c 2 -W 2 $(ip route | grep default | awk '{print $3}')"),
        ("DNS (1.1.1.1)", "ping -c 2 -W 2 1.1.1.1"),
        ("Internet (google.com)", "ping -c 2 -W 2 google.com")
    ]

    all_passed = True

    for test_name, command in tests:
        success, stdout, stderr = run_command(command, check=False)
        if success:
            console.print(f"  [green]✓[/green] {test_name}: OK")
        else:
            console.print(f"  [red]✗[/red] {test_name}: Failed")
            all_passed = False

    if all_passed:
        console.print("[green]✓ All connectivity tests passed[/green]")
    else:
        console.print("[yellow]⚠ Some connectivity tests failed[/yellow]")

    return all_passed


def run(config, console):
    """Main entry point for network configuration"""
    console.print("\n[bold cyan]═══ Network Configuration Module ═══[/bold cyan]\n")

    # Prompt for network settings
    settings = prompt_network_settings(console, config)

    if settings is None:
        console.print("[yellow]Network configuration skipped[/yellow]")
        return True  # Not a failure, user chose to skip

    # Save to config
    config.update("pihole", "static_ip", settings["static_ip"])
    config.update("pihole", "gateway", settings["gateway"])
    config.update("pihole", "dns_servers", settings["dns_servers"])

    # Check which network management system is in use
    success, _, _ = run_command("which nmcli", check=False)
    use_networkmanager = success

    success, _, _ = run_command("which dhcpcd", check=False)
    use_dhcpcd = success

    if use_dhcpcd:
        console.print("[cyan]Detected dhcpcd - using dhcpcd.conf for configuration[/cyan]")
        if not configure_static_ip_dhcpcd(settings, console):
            return False
    elif use_networkmanager:
        console.print("[cyan]Detected NetworkManager - using nmcli for configuration[/cyan]")
        if not configure_static_ip_networkmanager(settings, console):
            return False
    else:
        console.print("[red]✗ No supported network manager found (dhcpcd or NetworkManager)[/red]")
        return False

    # Update /etc/hosts
    update_hosts_file(console, config)

    # Test connectivity
    test_connectivity(console)

    console.print("\n[bold green]✓ Network configuration completed![/bold green]")
    console.print("[yellow]⚠ Note: A reboot may be required for changes to take full effect[/yellow]")

    reboot_now = Confirm.ask("\nWould you like to reboot now?", default=False)
    if reboot_now:
        console.print("[cyan]Rebooting in 5 seconds...[/cyan]")
        run_command("sleep 5 && reboot", check=False)

    return True
