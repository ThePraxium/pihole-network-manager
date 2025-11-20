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
        venv_path = Path(__file__).parent / '.venv'

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

        # Check if venv was created with wrong ownership (via sudo)
        if venv_path.exists() and os.geteuid() != 0:
            venv_owner = venv_path.stat().st_uid
            current_user = os.geteuid()

            if venv_owner == 0 and current_user != 0:
                print()
                print("⚠ Warning: Virtual environment was created with sudo")
                print(f"  To fix permissions, run:")
                print(f"  sudo chown -R $USER:$USER {venv_path}")
                print()

        # Re-execute in virtual environment
        print()
        print("Launching in virtual environment...")
        print()

        python = venv_path / 'bin' / 'python'
        os.execv(str(python), [str(python)] + sys.argv)


def ensure_directories():
    """
    Ensure required project subdirectories exist.
    Creates data/, logs/, and profiles/ if they don't exist.
    """
    project_root = Path(__file__).parent
    required_dirs = [
        project_root / "data",
        project_root / "logs",
        project_root / "profiles"
    ]

    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)


# Ensure virtual environment before importing anything else
ensure_venv()

# Ensure required directories exist
ensure_directories()


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
from management import maintenance, health


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
        # console.clear()  # Disabled to preserve scroll history
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
            "[6] Maintenance & Updates",
            "[7] Health & Diagnostics",
            "[0] Back to Main Menu"
        ]

        for option in options:
            console.print(f"  {option}")

        console.print()

        choice = Prompt.ask(
            "Select option",
            choices=["1", "2", "3", "4", "5", "6", "7", "0"],
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
            maintenance.run(config)
        elif choice == "7":
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
        # console.clear()  # Disabled to preserve scroll history
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
    # console.clear()  # Disabled to preserve scroll history
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


def migrate_setup_state():
    """
    Migrate setup_state.json to state.json if needed.
    This bridges the gap between the setup wizard and the main app.
    """
    project_root = Path(__file__).parent
    setup_state_file = project_root / "setup_state.json"
    state_file = project_root / "state.json"

    # If state.json already exists, nothing to do
    if state_file.exists():
        return

    # If setup_state.json exists and setup completed, create state.json
    if setup_state_file.exists():
        import json
        try:
            with open(setup_state_file, 'r') as f:
                setup_state = json.load(f)

            # Check if health_check completed (last step)
            if setup_state.get('modules', {}).get('health_check', {}).get('status') == 'completed':
                # Create state.json with setup_complete flag
                completed_at = setup_state.get('modules', {}).get('health_check', {}).get('completed_at')
                state_data = {
                    "setup": {
                        "setup_complete": True
                    },
                    "timestamps": {
                        "setup_complete": completed_at
                    },
                    "metadata": {
                        "created_at": setup_state.get('setup_started'),
                        "last_updated": completed_at
                    }
                }

                with open(state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)

                print(f"✓ Migrated setup state to {state_file}")
        except Exception as e:
            print(f"Warning: Could not migrate setup state: {e}")


def main_menu():
    """Main application menu"""
    # Migrate setup state if needed
    migrate_setup_state()

    # Load configuration and state
    config = Config()
    state = State()

    # Check if initial setup has been completed
    if not state.is_setup_complete():
        # console.clear()  # Disabled to preserve scroll history
        show_banner()
        console.print()
        show_warning("Initial setup not complete!")
        console.print()
        console.print("[bold]Pi-hole Network Manager must be set up before use.[/bold]")
        console.print()

        # Get actual project root dynamically
        project_root = Path(__file__).parent
        setup_script = project_root / "pi-setup" / "initial-setup.sh"

        console.print("Would you like to run the initial setup now?")
        console.print()
        console.print("  [cyan]Option 1:[/cyan] Run setup automatically (recommended)")
        console.print("  [cyan]Option 2:[/cyan] Run setup manually")
        console.print()

        choice = Prompt.ask("Select option", choices=["1", "2"], default="1")

        if choice == "1":
            console.print()
            console.print("[bold cyan]Running initial setup...[/bold cyan]")
            console.print()
            console.print("[dim]Note: This will require sudo privileges[/dim]")
            console.print()

            import subprocess
            result = subprocess.run(
                ["sudo", str(setup_script)],
                cwd=str(project_root)
            )

            if result.returncode == 0:
                console.print()
                show_success("Setup completed successfully!")
                console.print()
                console.print("Please run this application again:")
                console.print(f"  [cyan]python3 {project_root}/main.py[/cyan]")
                console.print()
            else:
                console.print()
                show_error("Setup failed or was cancelled")
                console.print()

            sys.exit(0)
        else:
            console.print()
            console.print("To run setup manually:")
            console.print()
            console.print(f"  [cyan]cd {project_root}[/cyan]")
            console.print(f"  [cyan]sudo ./pi-setup/initial-setup.sh[/cyan]")
            console.print()
            console.print("After setup is complete, run this application again:")
            console.print(f"  [cyan]python3 {project_root}/main.py[/cyan]")
            console.print()
            sys.exit(1)

    while True:
        # console.clear()  # Disabled to preserve scroll history
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
            # console.clear()  # Disabled to preserve scroll history
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
