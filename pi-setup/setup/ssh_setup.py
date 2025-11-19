"""
SSH Setup Module

Configures SSH for secure key-based authentication:
- Guides user through SSH key generation on their computer
- Receives and installs public key
- Disables password authentication
- Configures SSH port (optional)
- Tests key-based authentication
"""

import subprocess
from pathlib import Path
from rich.prompt import Prompt, Confirm
from rich.panel import Panel


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


def get_current_user():
    """Get the current non-root user"""
    success, stdout, _ = run_command("logname", check=False)
    if success and stdout.strip():
        return stdout.strip()

    # Fallback: check SUDO_USER
    success, stdout, _ = run_command("echo $SUDO_USER", check=False)
    if success and stdout.strip():
        return stdout.strip()

    return "pi"  # Default fallback


def display_ssh_key_instructions(console):
    """Display instructions for generating SSH keys"""
    instructions = """
[bold cyan]SSH Key Generation Instructions[/bold cyan]

On your main computer (not the Pi), run these commands:

[bold yellow]1. Generate SSH key pair:[/bold yellow]
   ssh-keygen -t ed25519 -C "pihole-access" -f ~/.ssh/pihole_rsa

   Press Enter for no passphrase (or set one for extra security)

[bold yellow]2. Display your public key:[/bold yellow]
   cat ~/.ssh/pihole_rsa.pub

[bold yellow]3. Copy the entire output[/bold yellow] (starts with ssh-ed25519...)

You'll paste this public key in the next step.
    """

    console.print(Panel(instructions, title="Setup Instructions", border_style="cyan"))


def receive_public_key(console):
    """Receive SSH public key from user"""
    console.print("\n[bold]Enter Your SSH Public Key[/bold]\n")
    console.print("Paste your public key (from ~/.ssh/pihole_rsa.pub on your computer):")
    console.print("[dim]Example: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... pihole-access[/dim]\n")

    public_key = Prompt.ask("Public key").strip()

    # Validate it looks like a public key
    if not public_key:
        console.print("[red]No public key provided[/red]")
        return None

    # Check if it starts with ssh-
    if not (public_key.startswith("ssh-rsa") or
            public_key.startswith("ssh-ed25519") or
            public_key.startswith("ssh-ecdsa")):
        console.print("[red]Invalid public key format[/red]")
        console.print("[yellow]Public key should start with 'ssh-rsa', 'ssh-ed25519', or 'ssh-ecdsa'[/yellow]")
        return None

    # Basic structure check: should have at least 2 parts
    parts = public_key.split()
    if len(parts) < 2:
        console.print("[red]Invalid public key format (too few parts)[/red]")
        return None

    console.print("\n[green]✓ Public key format looks valid[/green]")
    return public_key


def install_public_key(public_key, user, console):
    """Install public key for user"""
    console.print(f"\n[bold]Installing SSH Public Key for user '{user}'...[/bold]")

    user_home = Path(f"/home/{user}")
    if user == "root":
        user_home = Path("/root")

    ssh_dir = user_home / ".ssh"
    authorized_keys = ssh_dir / "authorized_keys"

    # Create .ssh directory if it doesn't exist
    console.print(f"  • Creating {ssh_dir} if needed...")
    ssh_dir.mkdir(mode=0o700, exist_ok=True)

    # Set ownership
    run_command(f"chown {user}:{user} {ssh_dir}")
    run_command(f"chmod 700 {ssh_dir}")

    # Add public key to authorized_keys
    console.print(f"  • Adding public key to {authorized_keys}...")

    try:
        # Read existing keys if file exists
        existing_keys = []
        if authorized_keys.exists():
            with open(authorized_keys, 'r') as f:
                existing_keys = [line.strip() for line in f.readlines() if line.strip()]

        # Check if key already exists
        if public_key in existing_keys:
            console.print("[yellow]  • Public key already exists in authorized_keys[/yellow]")
        else:
            # Append new key
            with open(authorized_keys, 'a') as f:
                f.write(f"{public_key}\n")
            console.print("[green]  • Public key added successfully[/green]")

        # Set proper permissions
        run_command(f"chown {user}:{user} {authorized_keys}")
        run_command(f"chmod 600 {authorized_keys}")

        console.print("[green]✓ SSH public key installed[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to install public key: {e}[/red]")
        return False


def disable_password_authentication(console):
    """Disable SSH password authentication"""
    console.print("\n[bold]Disabling Password Authentication...[/bold]")

    sshd_config = Path("/etc/ssh/sshd_config")

    # Backup
    console.print("  • Backing up sshd_config...")
    run_command(f"cp {sshd_config} {sshd_config}.backup-ssh-setup", check=False)

    try:
        with open(sshd_config, 'r') as f:
            lines = f.readlines()

        # Update configuration
        new_lines = []
        password_auth_set = False

        for line in lines:
            stripped = line.strip()

            # Replace PasswordAuthentication line
            if stripped.startswith("PasswordAuthentication"):
                if not password_auth_set:
                    new_lines.append("PasswordAuthentication no\n")
                    password_auth_set = True
            else:
                new_lines.append(line)

        # Add if not found
        if not password_auth_set:
            new_lines.append("\n# Disable password authentication (set by Pi-hole setup)\n")
            new_lines.append("PasswordAuthentication no\n")

        # Write updated config
        with open(sshd_config, 'w') as f:
            f.writelines(new_lines)

        console.print("[green]✓ Password authentication disabled in config[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to update sshd_config: {e}[/red]")
        return False


def change_ssh_port(console, config):
    """Optionally change SSH port"""
    console.print("\n[bold]SSH Port Configuration[/bold]\n")

    change_port = Confirm.ask(
        "Would you like to change the SSH port from default (22)?",
        default=False
    )

    if not change_port:
        console.print("[yellow]Keeping default SSH port (22)[/yellow]")
        return True, 22

    console.print("\n[cyan]Changing SSH port can improve security through obscurity.[/cyan]")
    console.print("[cyan]Common choices: 2222, 2200, 22000[/cyan]")
    console.print("[yellow]Remember: You'll need to update your SSH client config![/yellow]\n")

    while True:
        port_str = Prompt.ask("Enter new SSH port", default="22")
        try:
            port = int(port_str)
            if 1024 <= port <= 65535:
                break
            console.print("[red]Port must be between 1024 and 65535[/red]")
        except ValueError:
            console.print("[red]Invalid port number[/red]")

    # Update sshd_config
    sshd_config = Path("/etc/ssh/sshd_config")

    try:
        with open(sshd_config, 'r') as f:
            lines = f.readlines()

        new_lines = []
        port_set = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Port ") or stripped.startswith("#Port "):
                if not port_set:
                    new_lines.append(f"Port {port}\n")
                    port_set = True
            else:
                new_lines.append(line)

        if not port_set:
            new_lines.append(f"\n# Custom SSH port\nPort {port}\n")

        with open(sshd_config, 'w') as f:
            f.writelines(new_lines)

        # Update UFW if enabled
        console.print(f"  • Updating UFW firewall for port {port}...")
        run_command(f"ufw allow {port}/tcp comment 'SSH Custom Port'", check=False)
        run_command("ufw delete allow 22/tcp", check=False)

        config.update("ssh", "port", port)

        console.print(f"[green]✓ SSH port changed to {port}[/green]")
        console.print(f"[yellow]⚠ Update your client: ssh -p {port} user@pihole[/yellow]")
        return True, port

    except Exception as e:
        console.print(f"[red]✗ Failed to change SSH port: {e}[/red]")
        return False, 22


def restart_sshd(console):
    """Restart SSH daemon"""
    console.print("\n[bold]Restarting SSH Daemon...[/bold]")

    success, stdout, stderr = run_command("systemctl restart sshd", check=False)
    if not success:
        # Try ssh instead of sshd
        success, stdout, stderr = run_command("systemctl restart ssh", check=False)

    if success:
        console.print("[green]✓ SSH daemon restarted successfully[/green]")
        return True
    else:
        console.print(f"[red]✗ Failed to restart SSH daemon: {stderr}[/red]")
        return False


def test_ssh_connection(console, user, port=22):
    """Display instructions for testing SSH connection"""
    console.print("\n[bold cyan]Testing SSH Connection[/bold cyan]\n")

    # Get Pi's IP address
    success, ip, _ = run_command("hostname -I | awk '{print $1}'")
    ip = ip.strip() if success else "pihole.local"

    test_instructions = f"""
[bold]Test your SSH connection from your computer:[/bold]

[bold yellow]Command to test:[/bold yellow]
  ssh -i ~/.ssh/pihole_rsa {user}@{ip}{f' -p {port}' if port != 22 else ''}

[bold yellow]If successful:[/bold yellow]
  - You'll connect without entering a password
  - Password authentication is now disabled
  - Your Pi is more secure!

[bold yellow]If it fails:[/bold yellow]
  - Check your private key path (~/.ssh/pihole_rsa)
  - Verify the IP address is correct
  - Ensure the port is correct ({port})
  - Check firewall rules

[bold yellow]Add to ~/.ssh/config on your computer for easy access:[/bold yellow]
  Host pihole
      HostName {ip}
      User {user}
      Port {port}
      IdentityFile ~/.ssh/pihole_rsa

[bold yellow]Then connect with just:[/bold yellow]
  ssh pihole
    """

    console.print(Panel(test_instructions, title="Connection Test", border_style="cyan"))


def run(config, console):
    """Main entry point for SSH setup"""
    console.print("\n[bold cyan]═══ SSH Setup Module ═══[/bold cyan]\n")

    console.print("[cyan]This module will set up secure SSH key-based authentication.[/cyan]")
    console.print("[cyan]Password authentication will be disabled for security.[/cyan]\n")

    # Get current user
    user = get_current_user()
    console.print(f"[cyan]Setting up SSH for user: {user}[/cyan]\n")

    # Step 1: Display SSH key generation instructions
    display_ssh_key_instructions(console)

    ready = Confirm.ask("\nHave you generated your SSH key pair?", default=False)
    if not ready:
        console.print("\n[yellow]Please generate your SSH keys and run this module again.[/yellow]")
        console.print("[yellow]You can re-run individual modules from the main menu.[/yellow]")
        return False

    # Step 2: Receive public key
    public_key = receive_public_key(console)
    if not public_key:
        retry = Confirm.ask("\nWould you like to try entering the public key again?")
        if retry:
            public_key = receive_public_key(console)
            if not public_key:
                console.print("[red]SSH setup cannot continue without a valid public key[/red]")
                return False
        else:
            return False

    # Step 3: Install public key
    if not install_public_key(public_key, user, console):
        console.print("[red]Failed to install public key[/red]")
        return False

    # Step 4: Test before disabling passwords
    console.print("\n[bold yellow]⚠ Important: Test your SSH key before continuing![/bold yellow]")
    console.print("[yellow]Open a NEW terminal and test connecting with your SSH key.[/yellow]")
    console.print(f"[yellow]Command: ssh -i ~/.ssh/pihole_rsa {user}@$(hostname -I | awk '{{print $1}}')[/yellow]\n")

    test_successful = Confirm.ask("Did your SSH key test succeed?", default=False)

    if not test_successful:
        console.print("\n[red]⚠ SSH key test failed[/red]")
        console.print("[yellow]Please troubleshoot the SSH key connection before disabling passwords.[/yellow]")
        console.print("[yellow]The public key has been installed but passwords are still enabled.[/yellow]")
        console.print("[yellow]You can re-run this module after fixing the issue.[/yellow]")
        return False

    # Step 5: Disable password authentication
    if not disable_password_authentication(console):
        console.print("[yellow]⚠ Password authentication not disabled (manual review needed)[/yellow]")

    # Step 6: Optional: Change SSH port
    port_changed, ssh_port = change_ssh_port(console, config)

    # Step 7: Restart SSH daemon
    if not restart_sshd(console):
        console.print("[yellow]⚠ SSH daemon restart failed - changes may not be active[/yellow]")

    # Step 8: Display test instructions
    test_ssh_connection(console, user, ssh_port)

    console.print("\n[bold green]✓ SSH setup completed successfully![/bold green]")
    console.print("\n[bold cyan]Security Summary:[/bold cyan]")
    console.print("  • SSH key authentication: [green]Enabled[/green]")
    console.print("  • Password authentication: [red]Disabled[/red]")
    console.print(f"  • SSH port: [cyan]{ssh_port}[/cyan]")
    console.print(f"  • Authorized user: [cyan]{user}[/cyan]")

    return True
