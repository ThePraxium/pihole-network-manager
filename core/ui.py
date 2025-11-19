"""
UI Utility

Provides reusable UI components for the management tool using Rich library.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.layout import Layout
from rich.live import Live
from typing import List, Dict, Any, Optional

# Logger will be imported conditionally to avoid circular dependencies
try:
    from core.logger import get_logger
except ImportError:
    get_logger = None


console = Console()


def show_banner(title: str = "Pi-hole Network Manager"):
    """Display application banner"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        {title:^56}        ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def show_menu(title: str, options: List[str], allow_back: bool = True) -> str:
    """
    Display menu and get user selection

    Args:
        title: Menu title
        options: List of menu options
        allow_back: Show back/exit option

    Returns:
        Selected option number as string
    """
    console.print(f"\n[bold cyan]{title}[/bold cyan]\n")

    for i, option in enumerate(options, 1):
        console.print(f"  [{i}] {option}")

    if allow_back:
        console.print(f"  [9] {'Back' if title != 'Main Menu' else 'Exit'}")

    console.print()

    choices = [str(i) for i in range(1, len(options) + 1)]
    if allow_back:
        choices.append("9")

    return Prompt.ask("Select option", choices=choices)


def show_table(title: str, headers: List[str], rows: List[List[str]],
               styles: Optional[List[str]] = None):
    """
    Display formatted table

    Args:
        title: Table title
        headers: Column headers
        rows: Table rows
        styles: Optional column styles
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns
    for i, header in enumerate(headers):
        style = styles[i] if styles and i < len(styles) else "cyan"
        table.add_column(header, style=style)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)
    console.print()


def show_panel(content: str, title: str = "", border_style: str = "cyan"):
    """
    Display content in a panel

    Args:
        content: Panel content
        title: Panel title
        border_style: Border color
    """
    console.print(Panel(content, title=title, border_style=border_style))
    console.print()


def show_status(message: str, status: str = "info"):
    """
    Display status message

    Args:
        message: Status message
        status: Status type (info, success, warning, error)
    """
    # Log status message if logger is active
    logger = get_logger() if get_logger else None
    if logger and logger.is_active():
        logger.log_status(status, message)

    icons = {
        "info": ("[cyan]ℹ[/cyan]", ""),
        "success": ("[green]✓[/green]", "green"),
        "warning": ("[yellow]⚠[/yellow]", "yellow"),
        "error": ("[red]✗[/red]", "red")
    }

    icon, color = icons.get(status, icons["info"])
    text = f"[{color}]{message}[/{color}]" if color else message

    console.print(f"{icon} {text}")


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask for user confirmation

    Args:
        prompt: Confirmation prompt
        default: Default value

    Returns:
        True if confirmed, False otherwise
    """
    return Confirm.ask(prompt, default=default)


def prompt_input(prompt: str, default: str = "", password: bool = False) -> str:
    """
    Prompt for user input

    Args:
        prompt: Input prompt
        default: Default value
        password: Hide input (for passwords)

    Returns:
        User input
    """
    if default:
        return Prompt.ask(prompt, default=default, password=password)
    else:
        return Prompt.ask(prompt, password=password)


def show_progress(tasks: List[str], func, *args, **kwargs):
    """
    Show progress for multiple tasks

    Args:
        tasks: List of task descriptions
        func: Function to call for each task
        *args, **kwargs: Arguments to pass to function
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console
    ) as progress:

        for task_desc in tasks:
            task = progress.add_task(f"[cyan]{task_desc}...", total=None)
            func(*args, **kwargs)
            progress.update(task, completed=True)


def show_spinner(message: str):
    """
    Show spinner for long-running operation

    Args:
        message: Operation description

    Returns:
        Progress context manager
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    )


def clear_screen():
    """Clear terminal screen"""
    console.clear()


def print_divider(char: str = "─", length: int = 70, style: str = "cyan"):
    """
    Print horizontal divider

    Args:
        char: Character to use
        length: Divider length
        style: Text style
    """
    console.print(f"[{style}]{char * length}[/{style}]")


def show_key_value_list(data: Dict[str, Any], title: str = ""):
    """
    Display key-value pairs

    Args:
        data: Dictionary of key-value pairs
        title: Optional title
    """
    if title:
        console.print(f"\n[bold]{title}[/bold]\n")

    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")

    console.print()


def show_loading(message: str = "Loading..."):
    """
    Show loading message with spinner

    Args:
        message: Loading message
    """
    with console.status(f"[bold green]{message}"):
        pass


def paginate_output(content: str, page_size: int = 20):
    """
    Paginate long output

    Args:
        content: Content to paginate
        page_size: Lines per page
    """
    lines = content.split('\n')
    total_pages = (len(lines) + page_size - 1) // page_size

    for page in range(total_pages):
        start = page * page_size
        end = start + page_size
        page_lines = lines[start:end]

        for line in page_lines:
            console.print(line)

        if page < total_pages - 1:
            if not confirm_action(f"Page {page + 1}/{total_pages} - Continue?", default=True):
                break

            console.clear()


def show_error(error: str):
    """
    Display error message

    Args:
        error: Error message
    """
    # Log error message if logger is active
    logger = get_logger() if get_logger else None
    if logger and logger.is_active():
        logger.log_status("error", error)

    console.print(f"\n[bold red]Error:[/bold red] {error}\n")


def show_success(message: str):
    """
    Display success message

    Args:
        message: Success message
    """
    # Log success message if logger is active
    logger = get_logger() if get_logger else None
    if logger and logger.is_active():
        logger.log_status("success", message)

    console.print(f"\n[bold green]✓ {message}[/bold green]\n")


def show_warning(message: str):
    """
    Display warning message

    Args:
        message: Warning message
    """
    # Log warning message if logger is active
    logger = get_logger() if get_logger else None
    if logger and logger.is_active():
        logger.log_status("warning", message)

    console.print(f"\n[bold yellow]⚠ {message}[/bold yellow]\n")


def wait_for_enter(message: str = "Press Enter to continue..."):
    """
    Wait for user to press Enter

    Args:
        message: Prompt message
    """
    console.print()
    Prompt.ask(message, default="")
