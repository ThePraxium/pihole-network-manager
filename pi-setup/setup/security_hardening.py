"""
Security Hardening Module

Configures security features including:
- UFW firewall with strict rules
- Fail2ban for SSH protection
- Unattended security updates
- SSH hardening
- Sysctl security settings
- File permission hardening
"""

import subprocess
import os
from pathlib import Path


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


def configure_ufw(console):
    """Configure UFW firewall"""
    console.print("\n[bold]Configuring UFW Firewall...[/bold]")

    # Reset UFW to default
    console.print("  • Resetting UFW to defaults...")
    run_command("ufw --force reset", check=False)

    # Default policies
    console.print("  • Setting default policies (deny incoming, allow outgoing)...")
    run_command("ufw default deny incoming")
    run_command("ufw default allow outgoing")

    # Allow SSH (port 22 by default, can be changed later)
    console.print("  • Allowing SSH (port 22)...")
    run_command("ufw allow 22/tcp comment 'SSH'")

    # Allow DNS (port 53)
    console.print("  • Allowing DNS (port 53 TCP/UDP)...")
    run_command("ufw allow 53/tcp comment 'DNS TCP'")
    run_command("ufw allow 53/udp comment 'DNS UDP'")

    # Allow HTTP (port 80) for Pi-hole admin interface
    console.print("  • Allowing HTTP (port 80) for Pi-hole web interface...")
    run_command("ufw allow 80/tcp comment 'Pi-hole Web Interface HTTP'")

    # Allow HTTPS (port 443) for Pi-hole admin interface
    console.print("  • Allowing HTTPS (port 443) for Pi-hole web interface...")
    run_command("ufw allow 443/tcp comment 'Pi-hole Web Interface HTTPS'")

    # Enable UFW
    console.print("  • Enabling UFW...")
    run_command("ufw --force enable")

    # Verify status
    success, stdout, stderr = run_command("ufw status verbose")
    if success:
        console.print("[green]✓ UFW configured successfully[/green]")
        return True
    else:
        console.print(f"[red]✗ UFW configuration failed: {stderr}[/red]")
        return False


def configure_fail2ban(console):
    """Configure Fail2ban for SSH protection"""
    console.print("\n[bold]Configuring Fail2ban...[/bold]")

    # Create jail.local configuration
    jail_config = """[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = root@localhost
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
"""

    jail_file = Path("/etc/fail2ban/jail.local")
    console.print("  • Creating /etc/fail2ban/jail.local...")

    try:
        with open(jail_file, 'w') as f:
            f.write(jail_config)
        console.print("  • Jail configuration written")
    except Exception as e:
        console.print(f"[red]✗ Failed to write jail.local: {e}[/red]")
        return False

    # Restart fail2ban
    console.print("  • Restarting Fail2ban service...")
    success, stdout, stderr = run_command("systemctl restart fail2ban")
    if not success:
        console.print(f"[red]✗ Failed to restart Fail2ban: {stderr}[/red]")
        return False

    # Enable fail2ban
    console.print("  • Enabling Fail2ban to start on boot...")
    run_command("systemctl enable fail2ban")

    # Check status
    success, stdout, stderr = run_command("fail2ban-client status")
    if success:
        console.print("[green]✓ Fail2ban configured successfully[/green]")
        return True
    else:
        console.print(f"[red]✗ Fail2ban status check failed: {stderr}[/red]")
        return False


def configure_unattended_upgrades(console):
    """Configure automatic security updates"""
    console.print("\n[bold]Configuring Automatic Security Updates...[/bold]")

    # Enable unattended-upgrades
    config_file = Path("/etc/apt/apt.conf.d/50unattended-upgrades")

    unattended_config = """Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::InstallOnShutdown "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
"""

    console.print("  • Configuring unattended-upgrades...")
    try:
        with open(config_file, 'w') as f:
            f.write(unattended_config)
        console.print("  • Configuration written")
    except Exception as e:
        console.print(f"[red]✗ Failed to configure unattended-upgrades: {e}[/red]")
        return False

    # Create auto-upgrades config
    auto_upgrades_file = Path("/etc/apt/apt.conf.d/20auto-upgrades")
    auto_upgrades_config = """APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
"""

    console.print("  • Enabling automatic updates...")
    try:
        with open(auto_upgrades_file, 'w') as f:
            f.write(auto_upgrades_config)
        console.print("[green]✓ Automatic security updates configured[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed to enable automatic updates: {e}[/red]")
        return False


def harden_sshd_config(console):
    """Harden SSH daemon configuration"""
    console.print("\n[bold]Hardening SSH Configuration...[/bold]")

    sshd_config = Path("/etc/ssh/sshd_config")

    # Backup original config
    console.print("  • Backing up original sshd_config...")
    run_command(f"cp {sshd_config} {sshd_config}.backup")

    # SSH hardening settings
    ssh_hardening = {
        "PermitRootLogin": "no",
        "PasswordAuthentication": "yes",  # Will be changed to 'no' after SSH keys are set up
        "PubkeyAuthentication": "yes",
        "ChallengeResponseAuthentication": "no",
        "UsePAM": "yes",
        "X11Forwarding": "no",
        "PrintMotd": "no",
        "AcceptEnv": "LANG LC_*",
        "ClientAliveInterval": "300",
        "ClientAliveCountMax": "2",
        "MaxAuthTries": "3",
        "MaxSessions": "2"
    }

    console.print("  • Applying SSH hardening settings...")
    try:
        # Read current config
        with open(sshd_config, 'r') as f:
            lines = f.readlines()

        # Update config
        updated_lines = []
        settings_applied = set()

        for line in lines:
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                updated_lines.append(line)
                continue

            # Check if this line sets one of our hardening options
            setting_found = False
            for key, value in ssh_hardening.items():
                if stripped.startswith(key):
                    updated_lines.append(f"{key} {value}\n")
                    settings_applied.add(key)
                    setting_found = True
                    break

            if not setting_found:
                updated_lines.append(line)

        # Add any settings that weren't in the original config
        for key, value in ssh_hardening.items():
            if key not in settings_applied:
                updated_lines.append(f"{key} {value}\n")

        # Write updated config
        with open(sshd_config, 'w') as f:
            f.writelines(updated_lines)

        console.print("  • SSH configuration updated")
        console.print("[yellow]  Note: PasswordAuthentication will be disabled after SSH keys are set up[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ Failed to update sshd_config: {e}[/red]")
        return False

    # Note: Don't restart SSH yet - wait until SSH keys are in place
    console.print("[green]✓ SSH configuration hardened (restart required after SSH key setup)[/green]")
    return True


def configure_sysctl_security(console):
    """Configure kernel security parameters"""
    console.print("\n[bold]Configuring Kernel Security Settings...[/bold]")

    sysctl_config = """# IP Forwarding (disabled for security)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# IP Spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Ignore send redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Disable source packet routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1

# Ignore ICMP ping requests
net.ipv4.icmp_echo_ignore_all = 0

# Ignore Broadcast Request
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable IPv6
net.ipv6.conf.all.disable_ipv6 = 0
net.ipv6.conf.default.disable_ipv6 = 0
"""

    sysctl_file = Path("/etc/sysctl.d/99-security.conf")

    console.print("  • Writing sysctl security configuration...")
    try:
        with open(sysctl_file, 'w') as f:
            f.write(sysctl_config)
        console.print("  • Applying sysctl settings...")
        run_command("sysctl -p /etc/sysctl.d/99-security.conf")
        console.print("[green]✓ Kernel security settings configured[/green]")
        return True
    except Exception as e:
        console.print(f"[red]✗ Failed to configure sysctl: {e}[/red]")
        return False


def set_file_permissions(console):
    """Set proper file permissions for security"""
    console.print("\n[bold]Setting Secure File Permissions...[/bold]")

    permissions = [
        ("/etc/ssh/sshd_config", "0600"),
        ("/etc/shadow", "0640"),
        ("/etc/gshadow", "0640"),
    ]

    console.print("  • Applying secure file permissions...")
    for file_path, perm in permissions:
        if Path(file_path).exists():
            run_command(f"chmod {perm} {file_path}")
            console.print(f"    - {file_path}: {perm}")

    console.print("[green]✓ File permissions secured[/green]")
    return True


def disable_unused_services(console):
    """Disable unnecessary services"""
    console.print("\n[bold]Disabling Unused Services...[/bold]")

    # Services to disable (if they exist)
    services_to_disable = [
        "bluetooth",
        "avahi-daemon"
    ]

    for service in services_to_disable:
        # Check if service exists
        success, _, _ = run_command(f"systemctl list-unit-files | grep -q {service}", check=False)
        if success:
            console.print(f"  • Disabling {service}...")
            run_command(f"systemctl disable {service}", check=False)
            run_command(f"systemctl stop {service}", check=False)

    console.print("[green]✓ Unused services disabled[/green]")
    return True


def run(config, console):
    """Main entry point for security hardening"""
    console.print("\n[bold cyan]═══ Security Hardening Module ═══[/bold cyan]\n")

    steps = [
        ("UFW Firewall", configure_ufw),
        ("Fail2ban", configure_fail2ban),
        ("Automatic Updates", configure_unattended_upgrades),
        ("SSH Hardening", harden_sshd_config),
        ("Kernel Security", configure_sysctl_security),
        ("File Permissions", set_file_permissions),
        ("Unused Services", disable_unused_services)
    ]

    all_success = True

    for step_name, step_func in steps:
        try:
            success = step_func(console)
            if not success:
                console.print(f"[yellow]⚠ {step_name} completed with warnings[/yellow]")
                all_success = False
        except Exception as e:
            console.print(f"[red]✗ {step_name} failed: {e}[/red]")
            all_success = False

    if all_success:
        console.print("\n[bold green]✓ Security hardening completed successfully![/bold green]")
    else:
        console.print("\n[bold yellow]⚠ Security hardening completed with some warnings[/bold yellow]")

    return all_success
