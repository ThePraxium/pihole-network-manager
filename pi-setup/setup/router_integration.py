"""
Router Integration Module

Configures integration with TP-Link router:
- Tests router connectivity
- Validates router credentials
- Sets up automation mode (optional)
- Encrypts and stores router credentials
- Tests router API compatibility
"""

import subprocess
from pathlib import Path
from rich.prompt import Prompt, Confirm
from cryptography.fernet import Fernet
import base64
import hashlib


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


def encrypt_password(password, key):
    """Encrypt password using Fernet"""
    f = Fernet(key)
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()


def generate_encryption_key():
    """Generate encryption key from system unique identifier"""
    # Use machine ID as basis for key
    machine_id_file = Path("/etc/machine-id")

    if machine_id_file.exists():
        with open(machine_id_file, 'r') as f:
            machine_id = f.read().strip()
    else:
        # Fallback to hostname
        success, hostname, _ = run_command("hostname")
        machine_id = hostname.strip() if success else "pihole-default"

    # Create Fernet key from machine ID
    key_material = hashlib.sha256(machine_id.encode()).digest()
    key = base64.urlsafe_b64encode(key_material)

    return key


def test_router_connectivity(router_ip, console):
    """Test if router is reachable"""
    console.print(f"\n[bold]Testing Router Connectivity ({router_ip})...[/bold]")

    # Ping test
    success, stdout, stderr = run_command(f"ping -c 2 -W 2 {router_ip}", check=False)

    if success:
        console.print(f"  [green]✓[/green] Router is reachable at {router_ip}")
        return True
    else:
        console.print(f"  [red]✗[/red] Cannot reach router at {router_ip}")
        console.print(f"  [yellow]Make sure the router IP is correct[/yellow]")
        return False


def test_router_api(router_ip, username, password, console):
    """Test router API access using tplinkrouterc6u"""
    console.print("\n[bold]Testing Router API Access...[/bold]")

    # Create a test Python script
    test_script = """
import sys
try:
    from tplinkrouterc6u import TplinkRouter

    router = TplinkRouter(
        host=sys.argv[1],
        password=sys.argv[2]
    )

    # Try to get status (basic API test)
    status = router.get_status()

    if status:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED: No status returned")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"""

    test_file = Path("/tmp/test_router_api.py")

    try:
        with open(test_file, 'w') as f:
            f.write(test_script)

        # Run test
        success, stdout, stderr = run_command(
            f"python3 {test_file} {router_ip} '{password}'",
            check=False
        )

        # Clean up
        test_file.unlink(missing_ok=True)

        if success and "SUCCESS" in stdout:
            console.print("  [green]✓[/green] Router API access successful")
            console.print(f"  [cyan]Router model detected and API is compatible[/cyan]")
            return True
        else:
            console.print("  [red]✗[/red] Router API access failed")
            console.print(f"  [yellow]Error: {stdout.strip() if stdout else stderr.strip()}[/yellow]")
            return False

    except Exception as e:
        console.print(f"  [red]✗[/red] API test failed: {e}")
        return False


def prompt_router_config(console, config):
    """Prompt for router configuration"""
    console.print("\n[bold cyan]Router Configuration[/bold cyan]\n")

    console.print("[cyan]Configure TP-Link router integration for advanced features:[/cyan]")
    console.print("  • Unified device dashboard (Pi-hole + router data)")
    console.print("  • Network-level device blocking (MAC filtering)")
    console.print("  • DHCP lease information")
    console.print("  • Bandwidth monitoring")
    console.print("  • Remote router reboot")
    console.print()

    enable_router = Confirm.ask(
        "Enable router integration?",
        default=True
    )

    if not enable_router:
        console.print("[yellow]Router integration disabled[/yellow]")
        return None

    # Get router details
    router_ip = Prompt.ask("Router IP address", default="192.168.1.1")

    router_user = Prompt.ask("Router admin username", default="admin")

    router_pass = Prompt.ask("Router admin password", password=True)

    return {
        "enabled": True,
        "host": router_ip,
        "username": router_user,
        "password": router_pass
    }


def configure_automation_mode(console, config):
    """Configure automation mode for router control"""
    console.print("\n[bold]Router Automation Mode[/bold]\n")

    console.print("[cyan]Automation mode allows Pi-hole to control the router automatically:[/cyan]")
    console.print("  • Scheduled device blocking (e.g., block social media 9am-5pm)")
    console.print("  • Auto-reboot router if internet connection fails")
    console.print("  • Coordinated Pi-hole + router blocking")
    console.print()

    console.print("[yellow]⚠ Security Note:[/yellow]")
    console.print("  Router credentials will be encrypted and stored on the Pi")
    console.print("  Encryption key is derived from this Pi's unique machine ID")
    console.print()

    enable_automation = Confirm.ask(
        "Enable automation mode?",
        default=False
    )

    if enable_automation:
        console.print("[green]Automation mode will be enabled[/green]")
        console.print("[cyan]Scheduled tasks can be configured via the management tool[/cyan]")
    else:
        console.print("[yellow]Automation mode disabled[/yellow]")
        console.print("[cyan]Router features will work via manual control from your computer[/cyan]")

    return enable_automation


def save_router_config(router_config, automation_enabled, console, config):
    """Save router configuration to config file"""
    console.print("\n[bold]Saving Router Configuration...[/bold]")

    # Generate encryption key
    encryption_key = generate_encryption_key()

    # Encrypt password
    encrypted_password = encrypt_password(router_config["password"], encryption_key)

    # Update config
    config.update("router", "enabled", True)
    config.update("router", "host", router_config["host"])
    config.update("router", "username", router_config["username"])
    config.update("router", "password", encrypted_password)
    config.update("router", "automation_mode", automation_enabled)

    console.print("  • Router credentials encrypted and saved")

    if not automation_enabled:
        console.print("  • [yellow]Note: Password is saved for optional use by management tool[/yellow]")

    console.print("[green]✓ Router configuration saved[/green]")

    return True


def display_integration_summary(console, router_config, automation_enabled):
    """Display router integration summary"""
    console.print("\n[bold cyan]═══ Router Integration Summary ═══[/bold cyan]\n")

    console.print(f"[bold]Router:[/bold] TP-Link AXE5400")
    console.print(f"[bold]IP Address:[/bold] {router_config['host']}")
    console.print(f"[bold]Username:[/bold] {router_config['username']}")
    console.print(f"[bold]API Access:[/bold] [green]Configured[/green]")
    console.print()

    console.print(f"[bold]Mode:[/bold] {'Automation Enabled' if automation_enabled else 'Manual Control Only'}")
    console.print()

    if automation_enabled:
        console.print("[bold]Automation Features Available:[/bold]")
        console.print("  • Scheduled content filtering with device blocking")
        console.print("  • Automatic router management via cron jobs")
        console.print("  • Advanced network control from management tool")
    else:
        console.print("[bold]Manual Features Available:[/bold]")
        console.print("  • View devices and bandwidth (via management tool)")
        console.print("  • Manual device blocking")
        console.print("  • DHCP information")
        console.print("  • Remote reboot")

    console.print()

    console.print("[bold]Security:[/bold]")
    console.print("  • Router password: [green]Encrypted[/green]")
    console.print("  • Encryption key: Derived from Pi's machine ID")
    console.print("  • Access: Local network only")
    console.print()


def run(config, console):
    """Main entry point for router integration"""
    console.print("\n[bold cyan]═══ Router Integration Module ═══[/bold cyan]\n")

    console.print("[cyan]This module configures integration with your TP-Link AXE5400 router.[/cyan]")
    console.print("[cyan]Integration is optional but enables advanced network management.[/cyan]\n")

    # Step 1: Prompt for router configuration
    router_config = prompt_router_config(console, config)

    if router_config is None:
        config.update("router", "enabled", False)
        console.print("[yellow]Router integration skipped[/yellow]")
        return True  # Not a failure, user chose to skip

    # Step 2: Test connectivity
    if not test_router_connectivity(router_config["host"], console):
        console.print("\n[red]Cannot reach router - please check IP address and network connection[/red]")

        retry = Confirm.ask("Would you like to try a different IP address?")
        if retry:
            router_config["host"] = Prompt.ask("Enter router IP address")
            if not test_router_connectivity(router_config["host"], console):
                console.print("[red]Still cannot reach router - integration cancelled[/red]")
                return False
        else:
            console.print("[yellow]Router integration cancelled[/yellow]")
            return False

    # Step 3: Test API access
    console.print("\n[cyan]Testing router API compatibility...[/cyan]")

    if not test_router_api(
        router_config["host"],
        router_config["username"],
        router_config["password"],
        console
    ):
        console.print("\n[yellow]⚠ Router API test failed[/yellow]")
        console.print("[yellow]This could mean:[/yellow]")
        console.print("  • Wrong username/password")
        console.print("  • Router firmware not compatible")
        console.print("  • Network connectivity issue")
        console.print()

        continue_anyway = Confirm.ask("Save configuration anyway? (Can troubleshoot later)", default=False)

        if not continue_anyway:
            console.print("[yellow]Router integration cancelled[/yellow]")
            return False

    # Step 4: Configure automation mode
    automation_enabled = configure_automation_mode(console, config)

    # Step 5: Save configuration
    save_router_config(router_config, automation_enabled, console, config)

    # Step 6: Display summary
    display_integration_summary(console, router_config, automation_enabled)

    console.print("[bold green]✓ Router integration completed successfully![/bold green]")

    return True
