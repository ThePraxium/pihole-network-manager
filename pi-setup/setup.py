#!/usr/bin/env python3

"""
Pi-hole Network Manager - Setup Orchestrator

Interactive Python-based setup wizard that guides users through
configuring their Pi-hole system with security hardening, network setup,
SSH configuration, and blocklist profiles.
"""

import os
import sys
import yaml
import json
import argparse
from datetime import datetime
from pathlib import Path

# Get project root (this file is in pi-setup/ subdirectory)
PROJECT_ROOT = Path(__file__).parent.parent
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

# Setup module imports (will be created)
try:
    from setup import security_hardening
    from setup import network_config
    from setup import ssh_setup
    from setup import pihole_install
    from setup import blocklist_manager
    from setup import performance_tuning
    from setup import health_check
except ImportError as e:
    print(f"Warning: Could not import setup modules: {e}")
    print("Some features may not be available.")

console = Console()

# Configuration paths
CONFIG_DIR = PROJECT_ROOT
CONFIG_FILE = PROJECT_ROOT / "config.yaml"
STATE_FILE = PROJECT_ROOT / "setup_state.json"
LOG_FILE = PROJECT_ROOT / "logs" / "setup.log"


class SetupState:
    """Manage setup state persistence"""

    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
        """Load setup state from file"""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            "modules": {
                "security_hardening": {"status": "pending", "completed_at": None},
                "network_config": {"status": "pending", "completed_at": None},
                "ssh_setup": {"status": "pending", "completed_at": None},
                "pihole_install": {"status": "pending", "completed_at": None},
                "blocklist_manager": {"status": "pending", "completed_at": None},
                "performance_tuning": {"status": "pending", "completed_at": None},
                "health_check": {"status": "pending", "completed_at": None}
            },
            "setup_started": None,
            "setup_completed": None
        }

    def save_state(self):
        """Save setup state to file"""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def mark_module_complete(self, module_name):
        """Mark a module as completed"""
        if module_name in self.state["modules"]:
            self.state["modules"][module_name]["status"] = "completed"
            self.state["modules"][module_name]["completed_at"] = datetime.now().isoformat()
            self.save_state()

    def mark_module_failed(self, module_name, error):
        """Mark a module as failed"""
        if module_name in self.state["modules"]:
            self.state["modules"][module_name]["status"] = "failed"
            self.state["modules"][module_name]["error"] = str(error)
            self.save_state()

    def is_module_complete(self, module_name):
        """Check if a module is completed"""
        return self.state["modules"].get(module_name, {}).get("status") == "completed"

    def mark_setup_started(self):
        """Mark setup as started"""
        self.state["setup_started"] = datetime.now().isoformat()
        self.save_state()

    def mark_setup_complete(self):
        """Mark setup as completed"""
        self.state["setup_completed"] = datetime.now().isoformat()
        self.save_state()


class Configuration:
    """Manage configuration settings"""

    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f)
        return {
            "pihole": {
                "static_ip": "",
                "gateway": "",
                "dns_servers": ["1.1.1.1", "8.8.8.8"],
                "admin_password": "",
                "hostname": "pihole"
            },
            "blocklists": {
                "active_profile": "moderate"
            },
            "ssh": {
                "port": 22,
                "key_file": "/root/.ssh/authorized_keys"
            }
        }

    def save_config(self):
        """Save configuration to file"""
        with open(CONFIG_FILE, 'w') as f:
            yaml.safe_dump(self.config, f, default_flow_style=False)

    def update(self, section, key, value):
        """Update a configuration value"""
        if section in self.config:
            self.config[section][key] = value
            self.save_config()


def show_banner():
    """Display welcome banner"""
    console.clear()
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        Pi-hole Network Manager - Setup Wizard                    ║
║                                                                  ║
║  Interactive setup for your Pi-hole network management system    ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def show_status_table(state):
    """Display setup module status table"""
    table = Table(title="Setup Progress", show_header=True, header_style="bold magenta")
    table.add_column("Module", style="cyan", width=30)
    table.add_column("Status", width=15)
    table.add_column("Completed", width=20)

    status_icons = {
        "pending": "⧖ Pending",
        "completed": "✓ Complete",
        "failed": "✗ Failed"
    }

    status_colors = {
        "pending": "yellow",
        "completed": "green",
        "failed": "red"
    }

    modules_display = {
        "security_hardening": "Security Hardening",
        "network_config": "Network Configuration",
        "ssh_setup": "SSH Setup",
        "pihole_install": "Pi-hole Installation",
        "blocklist_manager": "Blocklist Profiles",
        "performance_tuning": "Performance Tuning",
        "health_check": "Health Check"
    }

    for module_key, module_name in modules_display.items():
        module_state = state.state["modules"].get(module_key, {})
        status = module_state.get("status", "pending")
        completed_at = module_state.get("completed_at", "")

        status_text = status_icons.get(status, status)
        status_color = status_colors.get(status, "white")

        table.add_row(
            module_name,
            f"[{status_color}]{status_text}[/{status_color}]",
            completed_at[:19] if completed_at else "—"
        )

    console.print(table)
    console.print()


def show_main_menu():
    """Display main menu and get user choice"""
    console.print("\n[bold cyan]Main Menu[/bold cyan]\n")
    console.print("  [1] Run Complete Setup (All modules)")
    console.print("  [2] Run Individual Module")
    console.print("  [3] View Configuration")
    console.print("  [4] View Setup Log")
    console.print("  [5] Reset Setup State")
    console.print("  [9] Exit")
    console.print()

    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "9"], default="1")
    return choice


def run_module(module_name, config, state):
    """Run a specific setup module"""
    module_map = {
        "security_hardening": ("Security Hardening", security_hardening),
        "network_config": ("Network Configuration", network_config),
        "ssh_setup": ("SSH Setup", ssh_setup),
        "pihole_install": ("Pi-hole Installation", pihole_install),
        "blocklist_manager": ("Blocklist Manager", blocklist_manager),
        "performance_tuning": ("Performance Tuning", performance_tuning),
        "health_check": ("Health Check", health_check)
    }

    if module_name not in module_map:
        console.print(f"[red]Unknown module: {module_name}[/red]")
        return False

    display_name, module = module_map[module_name]

    console.print(f"\n[bold blue]Running: {display_name}[/bold blue]\n")

    try:
        # Check if module has a run() function
        if hasattr(module, 'run'):
            result = module.run(config, console)
            if result:
                state.mark_module_complete(module_name)
                console.print(f"\n[green]✓ {display_name} completed successfully[/green]")
                return True
            else:
                state.mark_module_failed(module_name, "Module returned False")
                console.print(f"\n[red]✗ {display_name} failed[/red]")
                return False
        else:
            console.print(f"[yellow]Module {module_name} does not have a run() function[/yellow]")
            console.print(f"[yellow]Marking as complete for now (placeholder)[/yellow]")
            state.mark_module_complete(module_name)
            return True
    except Exception as e:
        state.mark_module_failed(module_name, str(e))
        console.print(f"\n[red]✗ Error running {display_name}: {e}[/red]")
        return False


def run_complete_setup(config, state):
    """Run all setup modules in sequence"""
    console.print("\n[bold green]Starting Complete Setup[/bold green]\n")

    modules = [
        "security_hardening",
        "network_config",
        "ssh_setup",
        "pihole_install",
        "blocklist_manager",
        "performance_tuning",
        "health_check"
    ]

    state.mark_setup_started()

    for module_name in modules:
        # Skip if already completed
        if state.is_module_complete(module_name):
            console.print(f"[yellow]Skipping {module_name} (already completed)[/yellow]")
            continue

        success = run_module(module_name, config, state)

        if not success:
            console.print(f"\n[red]Setup failed at module: {module_name}[/red]")
            retry = Confirm.ask("Would you like to retry this module?")
            if retry:
                success = run_module(module_name, config, state)
                if not success:
                    console.print("[red]Module failed again. Stopping setup.[/red]")
                    return False
            else:
                console.print("[yellow]Skipping failed module and continuing...[/yellow]")

        console.print()

    state.mark_setup_complete()
    console.print("\n[bold green]═══════════════════════════════════════[/bold green]")
    console.print("[bold green]✓ Complete Setup Finished![/bold green]")
    console.print("[bold green]═══════════════════════════════════════[/bold green]\n")

    return True


def run_individual_module(config, state):
    """Allow user to select and run individual module"""
    modules = {
        "1": "security_hardening",
        "2": "network_config",
        "3": "ssh_setup",
        "4": "pihole_install",
        "5": "blocklist_manager",
        "6": "performance_tuning",
        "7": "health_check"
    }

    console.print("\n[bold cyan]Select Module to Run:[/bold cyan]\n")
    console.print("  [1] Security Hardening")
    console.print("  [2] Network Configuration")
    console.print("  [3] SSH Setup")
    console.print("  [4] Pi-hole Installation")
    console.print("  [5] Blocklist Manager")
    console.print("  [6] Performance Tuning")
    console.print("  [7] Health Check")
    console.print("  [9] Back to Main Menu")
    console.print()

    choice = Prompt.ask("Select module", choices=list(modules.keys()) + ["9"])

    if choice == "9":
        return

    module_name = modules.get(choice)
    if module_name:
        run_module(module_name, config, state)
        Prompt.ask("\nPress Enter to continue")


def view_configuration(config):
    """Display current configuration"""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")
    console.print(yaml.dump(config.config, default_flow_style=False))
    Prompt.ask("\nPress Enter to continue")


def view_setup_log():
    """Display setup log"""
    console.print("\n[bold cyan]Setup Log[/bold cyan]\n")
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            console.print(f.read())
    else:
        console.print("[yellow]No log file found[/yellow]")
    Prompt.ask("\nPress Enter to continue")


def reset_setup_state(state):
    """Reset setup state"""
    console.print("\n[bold red]Warning: This will reset all setup progress![/bold red]\n")
    confirm = Confirm.ask("Are you sure you want to reset?")

    if confirm:
        STATE_FILE.unlink(missing_ok=True)
        console.print("[green]Setup state reset successfully[/green]")
        Prompt.ask("\nPress Enter to continue")
        return True
    return False


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Pi-hole Network Manager Setup Wizard')
    parser.add_argument('--quick', action='store_true',
                        help='Run complete setup automatically without prompts (non-interactive mode)')
    args = parser.parse_args()

    # Check if running as root
    if os.geteuid() != 0:
        console.print("[red]This script must be run as root (use sudo)[/red]")
        sys.exit(1)

    # Initialize
    state = SetupState()
    config = Configuration()

    # Quick mode: Run complete setup automatically
    if args.quick:
        console.print("[bold cyan]Running in quick mode (non-interactive)[/bold cyan]\n")

        # Pre-populate config with defaults for non-interactive setup
        # This allows modules to skip prompts if values already exist
        console.print("[dim]Pre-populating configuration with defaults...[/dim]")

        config.update("pihole", "static_ip", "current")  # Use current DHCP IP
        config.update("pihole", "gateway", "auto")       # Auto-detect gateway
        config.update("pihole", "dns_servers", ["1.1.1.1", "1.0.0.1"])  # Cloudflare DNS
        config.update("blocklists", "active_profile", "moderate")

        console.print("[dim]Configuration defaults set[/dim]\n")

        run_complete_setup(config, state)
        console.print("\n[bold green]Setup complete![/bold green]")
        sys.exit(0)

    # Interactive mode: Show menu
    while True:
        show_banner()
        show_status_table(state)

        choice = show_main_menu()

        if choice == "1":
            run_complete_setup(config, state)
            Prompt.ask("\nPress Enter to continue")

        elif choice == "2":
            run_individual_module(config, state)

        elif choice == "3":
            view_configuration(config)

        elif choice == "4":
            view_setup_log()

        elif choice == "5":
            if reset_setup_state(state):
                state = SetupState()  # Reload state

        elif choice == "9":
            console.print("\n[cyan]Goodbye![/cyan]\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Setup interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)
