"""
Blocklist Manager Module

Sets up and manages blocklist profiles:
- Creates Light, Moderate, and Aggressive profiles
- Configures adlists.list with selected profile
- Updates Pi-hole gravity database
- Provides statistics on blocking coverage
"""

import subprocess
import shutil
from pathlib import Path
from rich.prompt import Prompt, Confirm
from rich.table import Table
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


def display_profile_info(console):
    """Display information about blocklist profiles"""
    console.print("\n[bold cyan]Blocklist Profile Options[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Profile", style="cyan", width=12)
    table.add_column("Domains", width=15)
    table.add_column("Description", width=50)

    table.add_row(
        "Light",
        "~100K",
        "Major ad networks only. Minimal breakage, basic protection."
    )
    table.add_row(
        "Moderate",
        "~300K",
        "Comprehensive ads + trackers. Recommended for most users. ⭐"
    )
    table.add_row(
        "Aggressive",
        "~1M+",
        "Maximum blocking. May break some sites. Requires active whitelisting."
    )

    console.print(table)
    console.print()


def get_profile_lists(profile_name):
    """Get blocklist URLs for a specific profile"""

    # Light profile - essential blocklists
    light_lists = [
        # StevenBlack's Unified Hosts
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
        # AdGuard DNS filter (sanitized)
        "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
        # EasyList
        "https://easylist.to/easylist/easylist.txt",
    ]

    # Moderate profile - light + additional tracking/malware protection
    moderate_lists = light_lists + [
        # EasyPrivacy
        "https://easylist.to/easylist/easyprivacy.txt",
        # Fanboy's Enhanced Tracking List
        "https://secure.fanboy.co.nz/enhancedstats.txt",
        # URLhaus - Malware URLs
        "https://urlhaus.abuse.ch/downloads/hostfile/",
        # Phishing Army
        "https://phishing.army/download/phishing_army_blocklist.txt",
        # AdGuard DNS filter (full)
        "https://raw.githubusercontent.com/AdguardTeam/AdGuardSDNSFilter/master/Filters/adguard_full.txt",
    ]

    # Aggressive profile - moderate + comprehensive blocking
    aggressive_lists = moderate_lists + [
        # OISD Big List
        "https://big.oisd.nl/",
        # 1Hosts (Pro)
        "https://o0.pages.dev/Pro/adblock.txt",
        # HaGeZi's Ultimate Aggressive
        "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/pro.txt",
        # Energized Ultimate
        "https://block.energized.pro/ultimate/formats/hosts.txt",
        # Anti-telemetry
        "https://raw.githubusercontent.com/crazy-max/WindowsSpyBlocker/master/data/hosts/spy.txt",
        # Social media tracking
        "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/social/hosts",
        # Cryptocurrency mining
        "https://raw.githubusercontent.com/Zelo72/rpi/master/pihole/blocklists/CoinMiner.txt",
    ]

    profiles = {
        "light": light_lists,
        "moderate": moderate_lists,
        "aggressive": aggressive_lists
    }

    return profiles.get(profile_name.lower(), moderate_lists)


def select_profile(console):
    """Prompt user to select a blocklist profile"""
    display_profile_info(console)

    console.print("[cyan]Which profile would you like to use?[/cyan]\n")
    console.print("  [1] Light")
    console.print("  [2] Moderate (recommended)")
    console.print("  [3] Aggressive\n")

    choice = Prompt.ask(
        "Select profile",
        choices=["1", "2", "3"],
        default="2"
    )

    profile_map = {
        "1": "light",
        "2": "moderate",
        "3": "aggressive"
    }

    profile = profile_map[choice]
    console.print(f"\n[green]Selected profile: {profile.upper()}[/green]")

    return profile


def backup_adlists(console):
    """Backup existing adlists.list"""
    adlists_file = Path("/etc/pihole/adlists.list")

    if adlists_file.exists():
        backup_file = Path("/etc/pihole/adlists.list.backup")
        console.print(f"  • Backing up existing adlists.list...")
        try:
            shutil.copy(adlists_file, backup_file)
            console.print(f"    Backup saved to {backup_file}")
            return True
        except Exception as e:
            console.print(f"[yellow]⚠ Backup failed: {e}[/yellow]")
            return False

    return True


def write_adlists(profile_name, console):
    """Write blocklist URLs to adlists.list"""
    console.print(f"\n[bold]Configuring {profile_name.upper()} Profile...[/bold]")

    adlists_file = Path("/etc/pihole/adlists.list")
    blocklists = get_profile_lists(profile_name)

    # Backup existing
    backup_adlists(console)

    # Write new adlists
    console.print(f"  • Writing {len(blocklists)} blocklists to adlists.list...")

    try:
        with open(adlists_file, 'w') as f:
            f.write(f"# Pi-hole Blocklist Profile: {profile_name.upper()}\n")
            f.write(f"# Generated by Pi-hole Network Manager\n")
            f.write(f"# Total lists: {len(blocklists)}\n\n")

            for url in blocklists:
                f.write(f"{url}\n")

        console.print(f"[green]✓ Blocklists configured[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Failed to write adlists.list: {e}[/red]")
        return False


def update_gravity(console):
    """Update Pi-hole gravity database"""
    console.print("\n[bold]Updating Gravity Database...[/bold]")
    console.print("[cyan]This downloads and processes all blocklists (may take 2-5 minutes)...[/cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Updating gravity...", total=None)

        success, stdout, stderr = run_command("pihole -g", check=False)

        progress.remove_task(task)

    if success:
        console.print("\n[green]✓ Gravity update completed successfully[/green]")
        return True
    else:
        console.print(f"\n[red]✗ Gravity update failed[/red]")
        console.print(f"[yellow]Error: {stderr}[/yellow]")
        return False


def get_blocking_stats(console):
    """Get statistics on blocking coverage"""
    console.print("\n[bold]Blocklist Statistics[/bold]\n")

    # Get domain count
    success, stdout, _ = run_command("pihole -g -l | tail -1", check=False)
    if success and "domains" in stdout.lower():
        # Extract number from output
        import re
        match = re.search(r'([\d,]+)\s+domains', stdout)
        if match:
            domain_count = match.group(1)
            console.print(f"  • Total domains blocked: [cyan]{domain_count}[/cyan]")

    # Get list count
    adlists_file = Path("/etc/pihole/adlists.list")
    if adlists_file.exists():
        with open(adlists_file, 'r') as f:
            lists = [line for line in f if line.strip() and not line.startswith('#')]
        console.print(f"  • Active blocklists: [cyan]{len(lists)}[/cyan]")

    # Get gravity database size
    gravity_db = Path("/etc/pihole/gravity.db")
    if gravity_db.exists():
        size_mb = gravity_db.stat().st_size / (1024 * 1024)
        console.print(f"  • Gravity database size: [cyan]{size_mb:.2f} MB[/cyan]")

    console.print()


def save_profile_metadata(profile_name, console):
    """Save profile metadata for future reference"""
    console.print("\n[bold]Saving Profile Configuration...[/bold]")

    metadata_file = Path("/etc/pihole/active_profile.txt")

    try:
        with open(metadata_file, 'w') as f:
            from datetime import datetime
            f.write(f"Profile: {profile_name}\n")
            f.write(f"Activated: {datetime.now().isoformat()}\n")
            f.write(f"Lists: {len(get_profile_lists(profile_name))}\n")

        console.print(f"  • Profile metadata saved to {metadata_file}")
        return True

    except Exception as e:
        console.print(f"[yellow]⚠ Failed to save metadata: {e}[/yellow]")
        return False


def display_next_steps(console, profile_name):
    """Display information about what to do next"""
    console.print("\n[bold cyan]═══ Blocklist Setup Complete ═══[/bold cyan]\n")

    console.print(f"[bold]Active Profile:[/bold] [green]{profile_name.upper()}[/green]\n")

    console.print("[bold]What's Next:[/bold]")
    console.print("  1. Configure your router to use Pi-hole as DNS server")
    console.print("  2. Test ad blocking by visiting ad-heavy websites")
    console.print("  3. Access Pi-hole web interface to view statistics")
    console.print("  4. Use the management tool to switch profiles or add custom lists")
    console.print()

    if profile_name == "aggressive":
        console.print("[yellow]⚠ Aggressive Profile Tips:[/yellow]")
        console.print("  • Some sites may break (e.g., shopping, news sites)")
        console.print("  • Use the whitelist feature to unblock specific domains")
        console.print("  • Monitor the query log to identify false positives")
        console.print()

    console.print("[cyan]Quick Commands:[/cyan]")
    console.print("  • View stats: [bold]pihole -c[/bold]")
    console.print("  • Whitelist domain: [bold]pihole -w domain.com[/bold]")
    console.print("  • Blacklist domain: [bold]pihole -b domain.com[/bold]")
    console.print("  • Update gravity: [bold]pihole -g[/bold]")
    console.print()


def run(config, console):
    """Main entry point for blocklist manager"""
    console.print("\n[bold cyan]═══ Blocklist Manager Module ═══[/bold cyan]\n")

    console.print("[cyan]This module sets up blocklist profiles for ad/tracker blocking.[/cyan]")
    console.print("[cyan]You can switch profiles later using the management tool.[/cyan]\n")

    # Check if Pi-hole is installed
    success, _, _ = run_command("which pihole", check=False)
    if not success:
        console.print("[red]✗ Pi-hole is not installed[/red]")
        console.print("[yellow]Please run the Pi-hole installation module first[/yellow]")
        return False

    # Step 1: Select profile
    profile_name = select_profile(console)

    # Confirm selection
    console.print(f"\n[bold yellow]Ready to configure {profile_name.upper()} profile[/bold yellow]")
    proceed = Confirm.ask("Proceed?", default=True)

    if not proceed:
        console.print("[yellow]Blocklist configuration cancelled[/yellow]")
        return False

    # Step 2: Write adlists
    if not write_adlists(profile_name, console):
        console.print("[red]Failed to configure blocklists[/red]")
        return False

    # Step 3: Update gravity
    if not update_gravity(console):
        console.print("[yellow]⚠ Blocklists configured but gravity update failed[/yellow]")
        console.print("[yellow]You can manually update with: pihole -g[/yellow]")
        # Don't fail - gravity can be updated later

    # Step 4: Get statistics
    get_blocking_stats(console)

    # Step 5: Save profile metadata
    save_profile_metadata(profile_name, console)
    config.update("blocklists", "active_profile", profile_name)

    # Step 6: Display next steps
    display_next_steps(console, profile_name)

    console.print("[bold green]✓ Blocklist setup completed successfully![/bold green]")

    return True
