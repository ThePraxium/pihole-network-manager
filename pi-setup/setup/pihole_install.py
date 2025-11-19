"""
Pi-hole Installation Module

Installs and configures Pi-hole:
- Downloads official Pi-hole installer
- Runs unattended installation
- Sets admin password
- Configures upstream DNS servers
- Verifies installation
- Initial configuration
"""

import subprocess
import secrets
import string
from pathlib import Path
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn


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


def generate_strong_password(length=16):
    """Generate a strong random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def prompt_admin_password(console):
    """Prompt for Pi-hole admin password"""
    console.print("\n[bold]Pi-hole Admin Password[/bold]\n")
    console.print("  [1] Generate random password (recommended)")
    console.print("  [2] Set custom password\n")

    choice = Prompt.ask(
        "Password option",
        choices=["1", "2"],
        default="1"
    )

    if choice == "1":
        password = generate_strong_password()
        console.print(f"\n[green]Generated password: {password}[/green]")
        console.print("[yellow]⚠ Save this password - you'll need it to access the web interface![/yellow]\n")
    else:
        while True:
            password = Prompt.ask("Enter admin password", password=True)
            if len(password) >= 8:
                password_confirm = Prompt.ask("Confirm password", password=True)
                if password == password_confirm:
                    break
                console.print("[red]Passwords don't match. Try again.[/red]")
            else:
                console.print("[red]Password must be at least 8 characters[/red]")

    return password


def select_upstream_dns(console):
    """Select upstream DNS servers"""
    console.print("\n[bold]Upstream DNS Server Selection[/bold]\n")
    console.print("When Pi-hole needs to resolve a domain (not blocked), which DNS should it use?\n")

    console.print("  [1] Cloudflare (1.1.1.1, 1.0.0.1) - Privacy-focused, fast")
    console.print("  [2] Google (8.8.8.8, 8.8.4.4) - Reliable, widely used")
    console.print("  [3] Quad9 (9.9.9.9, 149.112.112.112) - Security-focused, blocks malware")
    console.print("  [4] OpenDNS (208.67.222.222, 208.67.220.220) - Cisco-owned, filtering options")
    console.print("  [5] Both Cloudflare + Google (redundancy)")
    console.print("  [6] Custom DNS servers")

    choice = Prompt.ask("Select DNS provider", choices=["1", "2", "3", "4", "5", "6"], default="1")

    dns_map = {
        "1": ["1.1.1.1", "1.0.0.1"],
        "2": ["8.8.8.8", "8.8.4.4"],
        "3": ["9.9.9.9", "149.112.112.112"],
        "4": ["208.67.222.222", "208.67.220.220"],
        "5": ["1.1.1.1", "8.8.8.8"]
    }

    if choice == "6":
        dns_input = Prompt.ask("Enter DNS servers (comma-separated)", default="1.1.1.1,8.8.8.8")
        dns_servers = [dns.strip() for dns in dns_input.split(',')]
    else:
        dns_servers = dns_map[choice]

    console.print(f"\n[green]Selected DNS servers: {', '.join(dns_servers)}[/green]")
    return dns_servers


def create_setupvars_conf(console, config, admin_password, dns_servers):
    """Create setupVars.conf for unattended installation"""
    console.print("\n[bold]Creating Pi-hole Configuration...[/bold]")

    # Get network settings from config
    static_ip = config.config.get("pihole", {}).get("static_ip", "")
    gateway = config.config.get("pihole", {}).get("gateway", "")

    if not static_ip:
        # Fallback: get current IP
        success, ip_output, _ = run_command("hostname -I | awk '{print $1}'")
        static_ip = ip_output.strip() if success else "192.168.1.100"

    if not gateway:
        # Fallback: get current gateway
        success, gw_output, _ = run_command("ip route | grep default | awk '{print $3}'")
        gateway = gw_output.strip() if success else "192.168.1.1"

    # Get interface
    success, iface_output, _ = run_command("ip route | grep default | awk '{print $5}'")
    interface = iface_output.strip() if success else "eth0"

    # Create setupVars.conf content
    setupvars_content = f"""# Pi-hole Setup Variables
PIHOLE_INTERFACE={interface}
PIHOLE_DNS_1={dns_servers[0] if len(dns_servers) > 0 else '1.1.1.1'}
PIHOLE_DNS_2={dns_servers[1] if len(dns_servers) > 1 else '8.8.8.8'}
QUERY_LOGGING=true
INSTALL_WEB_SERVER=true
INSTALL_WEB_INTERFACE=true
LIGHTTPD_ENABLED=true
CACHE_SIZE=10000
DNS_FQDN_REQUIRED=true
DNS_BOGUS_PRIV=true
DNSMASQ_LISTENING=local
WEBPASSWORD={admin_password}
BLOCKING_ENABLED=true
"""

    setupvars_path = Path("/etc/pihole/setupVars.conf")

    # Ensure directory exists
    setupvars_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(setupvars_path, 'w') as f:
            f.write(setupvars_content)
        console.print("  • Configuration file created at /etc/pihole/setupVars.conf")
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed to create setupVars.conf: {e}[/red]")
        return False


def download_installer(console):
    """Download Pi-hole installer"""
    console.print("\n[bold]Downloading Pi-hole Installer...[/bold]")

    installer_path = Path("/tmp/pihole_install.sh")

    # Download installer
    success, stdout, stderr = run_command(
        f"curl -sSL https://install.pi-hole.net -o {installer_path}",
        check=False
    )

    if not success or not installer_path.exists():
        console.print(f"[red]✗ Failed to download installer: {stderr}[/red]")
        return None

    # Make executable
    run_command(f"chmod +x {installer_path}")

    console.print(f"[green]✓ Installer downloaded to {installer_path}[/green]")
    return installer_path


def run_pihole_installer(installer_path, console):
    """Run Pi-hole installer in unattended mode"""
    console.print("\n[bold]Running Pi-hole Installer...[/bold]")
    console.print("[cyan]This may take 5-10 minutes...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Installing Pi-hole...", total=None)

        # Run installer with unattended flag
        success, stdout, stderr = run_command(
            f"{installer_path} --unattended",
            check=False
        )

        progress.remove_task(task)

    if success:
        console.print("\n[green]✓ Pi-hole installation completed successfully![/green]")
        return True
    else:
        console.print(f"\n[red]✗ Pi-hole installation failed[/red]")
        console.print(f"[red]Error output:[/red]\n{stderr}")
        return False


def set_web_password(password, console):
    """Set Pi-hole web interface password"""
    console.print("\n[bold]Setting Web Interface Password...[/bold]")

    # Pi-hole has a command to set password
    success, stdout, stderr = run_command(
        f"pihole -a -p {password}",
        check=False
    )

    if success:
        console.print("[green]✓ Web interface password set[/green]")
        return True
    else:
        console.print(f"[yellow]⚠ Password may already be set via setupVars.conf[/yellow]")
        return True  # Not a critical failure


def verify_installation(console):
    """Verify Pi-hole is installed and running"""
    console.print("\n[bold]Verifying Pi-hole Installation...[/bold]")

    checks = [
        ("Pi-hole FTL service", "systemctl is-active pihole-FTL"),
        ("Pi-hole command", "which pihole"),
        ("Web interface", "systemctl is-active lighttpd"),
        ("DNS port (53)", "netstat -tuln | grep ':53 '")
    ]

    all_passed = True

    for check_name, command in checks:
        success, stdout, stderr = run_command(command, check=False)
        if success:
            console.print(f"  [green]✓[/green] {check_name}: OK")
        else:
            console.print(f"  [red]✗[/red] {check_name}: Failed")
            all_passed = False

    if all_passed:
        console.print("\n[green]✓ All verification checks passed![/green]")
    else:
        console.print("\n[yellow]⚠ Some verification checks failed[/yellow]")

    return all_passed


def display_access_info(console, config):
    """Display Pi-hole access information"""
    console.print("\n[bold cyan]═══ Pi-hole Access Information ═══[/bold cyan]\n")

    # Get IP address
    success, ip_output, _ = run_command("hostname -I | awk '{print $1}'")
    ip_address = ip_output.strip() if success else config.config.get("pihole", {}).get("static_ip", "unknown")

    admin_password = config.config.get("pihole", {}).get("admin_password", "[check setupVars.conf]")

    console.print(f"[bold]Web Interface:[/bold]")
    console.print(f"  • URL: [cyan]http://{ip_address}/admin[/cyan]")
    console.print(f"  • Password: [yellow]{admin_password}[/yellow]")
    console.print()

    console.print(f"[bold]DNS Server:[/bold]")
    console.print(f"  • IP: [cyan]{ip_address}[/cyan]")
    console.print(f"  • Port: [cyan]53[/cyan]")
    console.print()

    console.print(f"[bold]Next Steps:[/bold]")
    console.print("  1. Configure your router to use Pi-hole as DNS server")
    console.print(f"     → Set Primary DNS to: {ip_address}")
    console.print("  2. Access the web interface and explore the dashboard")
    console.print("  3. Continue with blocklist profile setup in the next module")
    console.print()


def run(config, console):
    """Main entry point for Pi-hole installation"""
    console.print("\n[bold cyan]═══ Pi-hole Installation Module ═══[/bold cyan]\n")

    console.print("[cyan]This module will install Pi-hole, the network-wide ad blocker.[/cyan]")
    console.print("[cyan]Installation takes approximately 5-10 minutes.[/cyan]\n")

    # Check if Pi-hole is already installed
    success, _, _ = run_command("which pihole", check=False)
    if success:
        console.print("[yellow]⚠ Pi-hole appears to be already installed[/yellow]")
        reinstall = Confirm.ask("Would you like to reinstall/reconfigure?", default=False)
        if not reinstall:
            console.print("[yellow]Skipping Pi-hole installation[/yellow]")
            return True

    # Step 1: Prompt for admin password
    admin_password = prompt_admin_password(console)
    config.update("pihole", "admin_password", admin_password)

    # Step 2: Select upstream DNS
    dns_servers = select_upstream_dns(console)
    config.update("pihole", "dns_servers", dns_servers)

    # Step 3: Create setupVars.conf
    if not create_setupvars_conf(console, config, admin_password, dns_servers):
        console.print("[red]Setup configuration failed[/red]")
        return False

    # Step 4: Download installer
    installer_path = download_installer(console)
    if not installer_path:
        console.print("[red]Failed to download Pi-hole installer[/red]")
        return False

    # Confirm before installation
    console.print("\n[bold yellow]Ready to install Pi-hole[/bold yellow]")
    proceed = Confirm.ask("Proceed with installation?", default=True)

    if not proceed:
        console.print("[yellow]Installation cancelled[/yellow]")
        return False

    # Step 5: Run installer
    if not run_pihole_installer(installer_path, console):
        console.print("[red]Pi-hole installation failed[/red]")
        return False

    # Step 6: Set web password (redundant but ensures it's set)
    set_web_password(admin_password, console)

    # Step 7: Verify installation
    if not verify_installation(console):
        console.print("[yellow]⚠ Pi-hole installed but some checks failed[/yellow]")
        console.print("[yellow]You may need to troubleshoot manually[/yellow]")

    # Step 8: Display access information
    display_access_info(console, config)

    console.print("\n[bold green]✓ Pi-hole installation completed successfully![/bold green]")

    return True
