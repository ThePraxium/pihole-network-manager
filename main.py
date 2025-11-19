#!/usr/bin/env python3
"""
Pi-hole Network Manager - Main Entry Point

Unified TUI application for Pi-hole setup and management.
Auto-creates virtual environment and installs dependencies if needed.
"""

import sys
import subprocess
from pathlib import Path
import os


def ensure_venv():
    """
    Ensure we're running in a virtual environment.
    If not, create one, install dependencies, and re-exec.
    """
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        venv_path = Path.home() / '.pihole-manager-venv'

        if not venv_path.exists():
            print("Creating virtual environment...")
            print(f"Location: {venv_path}")
            print()

            # Create virtual environment
            try:
                subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
                print("✓ Virtual environment created")
            except subprocess.CalledProcessError as e:
                print(f"✗ Failed to create virtual environment: {e}")
                sys.exit(1)

            # Install dependencies
            requirements_file = Path(__file__).parent / 'requirements.txt'

            if requirements_file.exists():
                print()
                print("Installing dependencies...")
                pip = venv_path / 'bin' / 'pip'

                try:
                    subprocess.run(
                        [str(pip), 'install', '--upgrade', 'pip'],
                        check=True,
                        capture_output=True
                    )
                    subprocess.run(
                        [str(pip), 'install', '-r', str(requirements_file)],
                        check=True
                    )
                    print("✓ Dependencies installed")
                except subprocess.CalledProcessError as e:
                    print(f"✗ Failed to install dependencies: {e}")
                    sys.exit(1)

        # Re-execute in virtual environment
        print()
        print("Launching in virtual environment...")
        print()

        python = venv_path / 'bin' / 'python'
        os.execv(str(python), [str(python)] + sys.argv)


# Ensure virtual environment before importing anything else
ensure_venv()


# Now safe to import our modules
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

from core.config import Config
from core.state import State
from core.ui import console, show_menu, show_success, show_error, show_warning, show_status
from core.logger import get_logger

# Import management modules
from management import blocklists, devices, lists, content_filter, stats
from management import router_control, maintenance, health


def show_banner():
    """Display application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        [bold magenta]Pi-hole Network Manager[/bold magenta]                        ║
║                                                           ║
║        Automated Setup & Management Tool                  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner)


def management_menu(config: Config):
    """
    Management submenu for daily Pi-hole operations

    Args:
        config: Configuration object
    """
    while True:
        console.clear()
        show_banner()

        console.print()
        console.print("[bold]Management Options:[/bold]")
        console.print()

        options = [
            "[1] Blocklist Management",
            "[2] Device Management",
            "[3] Whitelist/Blacklist",
            "[4] Content Filtering",
            "[5] Statistics & Monitoring",
            "[6] Router Control",
            "[7] Maintenance & Updates",
            "[8] Health & Diagnostics",
            "[0] Back to Main Menu"
        ]

        for option in options:
            console.print(f"  {option}")

        console.print()

        choice = Prompt.ask(
            "Select option",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"],
            default="0"
        )

        if choice == "1":
            blocklists.run(config)
        elif choice == "2":
            devices.run(config)
        elif choice == "3":
            lists.run(config)
        elif choice == "4":
            content_filter.run(config)
        elif choice == "5":
            stats.run(config)
        elif choice == "6":
            router_control.run(config)
        elif choice == "7":
            maintenance.run(config)
        elif choice == "8":
            health.run(config)
        elif choice == "0":
            break


def configuration_menu(config: Config):
    """
    Configuration submenu

    Args:
        config: Configuration object
    """
    while True:
        console.clear()
        show_banner()

        console.print()
        console.print("[bold]Configuration Options:[/bold]")
        console.print()

        options = [
            "[1] View Current Configuration",
            "[2] Edit Settings",
            "[0] Back to Main Menu"
        ]

        for option in options:
            console.print(f"  {option}")

        console.print()

        choice = Prompt.ask("Select option", choices=["1", "2", "0"], default="0")

        if choice == "1":
            view_configuration(config)
        elif choice == "2":
            edit_connection_settings(config)
        elif choice == "0":
            break


def view_configuration(config: Config):
    """Display current configuration"""
    console.clear()
    show_banner()

    console.print()
    console.print(Panel(
        "[bold]Current Configuration[/bold]",
        border_style="cyan"
    ))

    console.print()
    console.print(f"[bold]Pi-hole:[/bold]")
    console.print(f"  Web URL:  {config.get('pihole', 'web_url', 'Not configured')}")

    console.print()
    console.print(f"[bold]Router:[/bold]")
    if config.get('router', 'enabled'):
        console.print(f"  Enabled:  Yes")
        console.print(f"  Host:     {config.get('router', 'host')}")
        console.print(f"  User:     {config.get('router', 'user')}")
    else:
        console.print(f"  Enabled:  No")

    console.print()
    console.print(f"[bold]Config File:[/bold] {config.config_path}")

    console.print()
    Prompt.ask("Press Enter to continue")


def edit_connection_settings(config: Config):
    """Edit configuration settings"""
    console.print()
    console.print("[yellow]Configuration can be changed manually[/yellow]")
    console.print(f"[yellow]Edit: {config.config_path}[/yellow]")
    console.print()
    Prompt.ask("Press Enter to continue")


def main_menu():
    """Main application menu"""
    # Load configuration and state
    config = Config()
    state = State()

    # Check if initial setup has been completed
    if not state.is_setup_complete():
        console.clear()
        show_banner()
        console.print()
        show_error("Initial setup not complete!")
        console.print()
        console.print("[bold]Pi-hole Network Manager must be set up before use.[/bold]")
        console.print()
        console.print("Please run the initial setup script on your Raspberry Pi:")
        console.print()
        console.print("  [cyan]cd /opt/pihole-manager[/cyan]")
        console.print("  [cyan]sudo ./pi-setup/initial-setup.sh[/cyan]")
        console.print()
        console.print("After setup is complete, you can run this manager.")
        console.print()
        sys.exit(1)

    while True:
        console.clear()
        show_banner()

        console.print()
        console.print("[bold]Main Menu:[/bold]")
        console.print()

        options = [
            "[1] Pi-hole Management",
            "[2] Configuration",
            "[0] Exit"
        ]

        for option in options:
            console.print(f"  {option}")

        console.print()

        choice = Prompt.ask("Select option", choices=["1", "2", "0"], default="1")

        # Log menu selection
        logger = get_logger()
        if logger.is_active():
            menu_options = {
                "1": "Pi-hole Management",
                "2": "Configuration",
                "0": "Exit"
            }
            logger.log_menu("Main Menu", f"{choice} - {menu_options.get(choice, 'Unknown')}")

        if choice == "1":
            management_menu(config)
        elif choice == "2":
            configuration_menu(config)
        elif choice == "0":
            console.clear()
            console.print()
            console.print("[bold cyan]Thank you for using Pi-hole Network Manager![/bold cyan]")
            console.print()
            sys.exit(0)


if __name__ == "__main__":
    # Initialize logger for this session
    logger = get_logger()
    logger_started = logger.start()

    if logger_started:
        logger.log_separator("SESSION START")
        logger.log_status("info", "Pi-hole Network Manager started")

    try:
        main_menu()

        # Stop logger on normal exit
        if logger.is_active():
            logger.log_separator("SESSION END")
            logger.log_status("info", "Pi-hole Network Manager exited normally")
            logger.stop()

    except KeyboardInterrupt:
        console.print()
        console.print()
        console.print("[yellow]Interrupted by user[/yellow]")

        # Log interruption
        if logger.is_active():
            logger.log_status("warning", "Session interrupted by user (Ctrl+C)")
            logger.stop()

        sys.exit(0)

    except Exception as e:
        console.print()
        console.print(f"[red]Fatal error: {e}[/red]")
        import traceback
        console.print()
        console.print(traceback.format_exc())

        # Log fatal exception
        if logger.is_active():
            logger.log_exception(e, context="Fatal error in main()")
            logger.stop()

        sys.exit(1)
