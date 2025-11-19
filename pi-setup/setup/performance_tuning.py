"""
Performance Tuning Module

Optimizes system performance for Pi-hole:
- Configure swap for SD card longevity
- Set up log rotation to prevent disk fill
- Optimize Pi-hole FTL settings
- Configure DNS cache settings
- Set up tmpfs for frequently written files
"""

import subprocess
from pathlib import Path
from rich.prompt import Confirm


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


def configure_swap(console):
    """Configure swap to reduce SD card wear"""
    console.print("\n[bold]Configuring Swap Settings...[/bold]")

    # Reduce swappiness (how aggressively system uses swap)
    console.print("  • Reducing swappiness to minimize SD card writes...")

    sysctl_swap = """# Reduce swap usage to extend SD card life
vm.swappiness=10
vm.vfs_cache_pressure=50
"""

    sysctl_file = Path("/etc/sysctl.d/90-swap.conf")

    try:
        with open(sysctl_file, 'w') as f:
            f.write(sysctl_swap)

        # Apply immediately
        run_command("sysctl vm.swappiness=10")
        run_command("sysctl vm.vfs_cache_pressure=50")

        console.print("    - Swappiness: 10 (default 60)")
        console.print("    - Cache pressure: 50 (default 100)")
        console.print("[green]✓ Swap configured for SD card longevity[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to configure swap: {e}[/red]")
        return False


def configure_log_rotation(console):
    """Set up aggressive log rotation"""
    console.print("\n[bold]Configuring Log Rotation...[/bold]")

    # Pi-hole specific log rotation
    pihole_logrotate = """/var/log/pihole.log {
    daily
    rotate 7
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
    postrotate
        /usr/bin/killall -HUP pihole-FTL
    endscript
}

/var/log/pihole-FTL.log {
    daily
    rotate 3
    missingok
    notifempty
    compress
    delaycompress
}
"""

    logrotate_file = Path("/etc/logrotate.d/pihole")

    try:
        with open(logrotate_file, 'w') as f:
            f.write(pihole_logrotate)

        console.print("  • Pi-hole logs: Daily rotation, keep 7 days")
        console.print("  • FTL logs: Daily rotation, keep 3 days")
        console.print("[green]✓ Log rotation configured[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to configure log rotation: {e}[/red]")
        return False


def optimize_ftl_config(console):
    """Optimize Pi-hole FTL configuration"""
    console.print("\n[bold]Optimizing Pi-hole FTL Settings...[/bold]")

    ftl_config = """# Pi-hole FTL Configuration - Performance Optimized

# DNS Cache Settings
CACHE_SIZE=10000

# Database Settings
MAXDBDAYS=30
DBINTERVAL=1.0

# Privacy Settings
PRIVACYLEVEL=0

# Query Logging
QUERY_LOGGING=true

# Rate Limiting (prevent DNS amplification attacks)
RATE_LIMIT=1000/60

# DNSSEC
DNSSEC=false

# Conditional Forwarding (set to false initially, can enable later)
CONDITIONAL_FORWARDING=false

# Blocking Mode
BLOCKING_MODE=NULL

# Reply when blocked
REPLY_WHEN_BLOCKED=IP

# Performance
RESOLVE_IPV6=yes
RESOLVE_IPV4=yes

# Refresh blocklist
REFRESH_HOSTNAMES=IPV4
"""

    ftl_config_file = Path("/etc/pihole/pihole-FTL.conf")

    try:
        # Backup existing if it exists
        if ftl_config_file.exists():
            run_command(f"cp {ftl_config_file} {ftl_config_file}.backup", check=False)

        with open(ftl_config_file, 'w') as f:
            f.write(ftl_config)

        console.print("  • Cache size: 10,000 entries")
        console.print("  • Database retention: 30 days")
        console.print("  • Rate limiting: 1000 queries/minute per client")
        console.print("[green]✓ FTL configuration optimized[/green]")

        # Restart FTL to apply changes
        console.print("  • Restarting Pi-hole FTL service...")
        success, _, _ = run_command("systemctl restart pihole-FTL", check=False)
        if success:
            console.print("    Service restarted successfully")
        else:
            console.print("    [yellow]Service restart may have failed (check manually)[/yellow]")

        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to optimize FTL config: {e}[/red]")
        return False


def configure_tmpfs(console):
    """Configure tmpfs for frequently written files"""
    console.print("\n[bold]Configuring tmpfs for Log Files...[/bold]")

    console.print("[cyan]tmpfs stores files in RAM instead of SD card[/cyan]")
    console.print("[cyan]This reduces SD card wear for frequently written files[/cyan]\n")

    enable_tmpfs = Confirm.ask(
        "Enable tmpfs for Pi-hole logs? (Logs will be lost on reboot)",
        default=False
    )

    if not enable_tmpfs:
        console.print("[yellow]Skipping tmpfs configuration[/yellow]")
        return True

    # Add tmpfs mounts to fstab
    fstab_entries = """
# tmpfs for Pi-hole logs (reduce SD card wear)
tmpfs    /var/log    tmpfs    defaults,noatime,nosuid,mode=0755,size=100m    0 0
"""

    fstab_file = Path("/etc/fstab")

    try:
        # Backup fstab
        run_command(f"cp {fstab_file} {fstab_file}.backup", check=False)

        # Check if already configured
        with open(fstab_file, 'r') as f:
            content = f.read()

        if 'tmpfs    /var/log' in content:
            console.print("[yellow]tmpfs already configured in /etc/fstab[/yellow]")
        else:
            # Append tmpfs entries
            with open(fstab_file, 'a') as f:
                f.write(fstab_entries)

            console.print("  • Added tmpfs mount for /var/log")
            console.print("[green]✓ tmpfs configured[/green]")
            console.print("[yellow]⚠ Reboot required for tmpfs to take effect[/yellow]")

        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to configure tmpfs: {e}[/red]")
        return False


def optimize_dns_cache(console):
    """Optimize dnsmasq cache settings"""
    console.print("\n[bold]Optimizing DNS Cache Settings...[/bold]")

    dnsmasq_config = """# Custom dnsmasq configuration for performance

# Cache size (number of DNS entries)
cache-size=10000

# Negative caching TTL (cache NXDOMAIN responses)
neg-ttl=3600

# Min cache TTL (minimum time to cache entries)
min-cache-ttl=300

# Max cache TTL
max-cache-ttl=86400

# Local domain cache TTL
local-ttl=60
"""

    dnsmasq_file = Path("/etc/dnsmasq.d/99-custom-cache.conf")

    try:
        with open(dnsmasq_file, 'w') as f:
            f.write(dnsmasq_config)

        console.print("  • DNS cache size: 10,000 entries")
        console.print("  • Minimum cache TTL: 5 minutes")
        console.print("  • Maximum cache TTL: 24 hours")
        console.print("[green]✓ DNS cache optimized[/green]")

        # Restart dnsmasq
        console.print("  • Restarting DNS service...")
        run_command("systemctl restart pihole-FTL", check=False)

        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to optimize DNS cache: {e}[/red]")
        return False


def cleanup_temp_files(console):
    """Clean up temporary files and caches"""
    console.print("\n[bold]Cleaning Up Temporary Files...[/bold]")

    commands = [
        ("APT cache", "apt-get clean"),
        ("Old logs", "journalctl --vacuum-time=7d"),
        ("Temp files", "rm -rf /tmp/*"),
    ]

    for name, cmd in commands:
        console.print(f"  • Cleaning {name}...")
        run_command(cmd, check=False)

    console.print("[green]✓ Temporary files cleaned[/green]")
    return True


def display_performance_summary(console):
    """Display performance optimization summary"""
    console.print("\n[bold cyan]═══ Performance Optimization Summary ═══[/bold cyan]\n")

    console.print("[bold]Optimizations Applied:[/bold]")
    console.print("  [green]✓[/green] Swap reduced to minimize SD card writes")
    console.print("  [green]✓[/green] Aggressive log rotation configured")
    console.print("  [green]✓[/green] Pi-hole FTL optimized (cache, rate limiting)")
    console.print("  [green]✓[/green] DNS cache settings tuned")
    console.print("  [green]✓[/green] Temporary files cleaned")
    console.print()

    console.print("[bold]Performance Benefits:[/bold]")
    console.print("  • Extended SD card lifespan")
    console.print("  • Faster DNS resolution (larger cache)")
    console.print("  • Reduced disk space usage")
    console.print("  • Protection against DNS amplification attacks")
    console.print()

    console.print("[bold]Monitoring Commands:[/bold]")
    console.print("  • Check disk usage: [cyan]df -h[/cyan]")
    console.print("  • Check memory: [cyan]free -h[/cyan]")
    console.print("  • Check Pi-hole stats: [cyan]pihole -c[/cyan]")
    console.print("  • Check system load: [cyan]htop[/cyan]")
    console.print()


def run(config, console):
    """Main entry point for performance tuning"""
    console.print("\n[bold cyan]═══ Performance Tuning Module ═══[/bold cyan]\n")

    console.print("[cyan]This module optimizes your Pi-hole for performance and longevity.[/cyan]")
    console.print("[cyan]Optimizations focus on reducing SD card wear and improving DNS speed.[/cyan]\n")

    steps = [
        ("Swap Configuration", configure_swap),
        ("Log Rotation", configure_log_rotation),
        ("FTL Optimization", optimize_ftl_config),
        ("DNS Cache", optimize_dns_cache),
        ("tmpfs (optional)", configure_tmpfs),
        ("Cleanup", cleanup_temp_files),
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

    # Display summary
    display_performance_summary(console)

    if all_success:
        console.print("[bold green]✓ Performance tuning completed successfully![/bold green]")
    else:
        console.print("[bold yellow]⚠ Performance tuning completed with some warnings[/bold yellow]")

    return all_success
