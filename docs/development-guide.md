# Development Guide

**Version**: 2.0
**Last Updated**: 2025-01-19
**Purpose**: Coding standards, patterns, and best practices for Pi-hole Network Manager development

---

## Table of Contents

1. [Overview](#overview)
2. [Python Standards](#python-standards)
3. [Local Execution Patterns](#local-execution-patterns)
4. [Pi-hole Interaction](#pi-hole-interaction)
5. [Core Module Usage](#core-module-usage)
6. [Management Module Patterns](#management-module-patterns)
7. [Testing Approaches](#testing-approaches)
8. [Error Handling](#error-handling)
9. [Configuration Management](#configuration-management)
10. [Best Practices](#best-practices)

---

## Overview

The Pi-hole Network Manager is a **Python 3.11+ application** that runs **directly on a Raspberry Pi** to manage Pi-hole instances. The system uses subprocess-based local execution with passwordless sudo for Pi-hole operations.

### Core Principles

1. **Local Execution** - Application runs on the same Pi as Pi-hole (no remote SSH for Pi-hole operations)
2. **Subprocess-Based** - All Pi operations via `execute_command()` from `core/local_executor.py`
3. **Passwordless Sudo** - Specific commands granted in `/etc/sudoers.d/pihole-manager`
4. **Rich TUI** - Use Rich library for consistent UI
5. **Configuration-Driven** - YAML configs for all settings
6. **Simple State** - Minimal setup state tracking (`setup_complete` flag only)
7. **Error Recovery** - Graceful degradation, clear error messages

### Architecture Overview

```
┌────────────────────────────────────────────────┐
│         Raspberry Pi (pihole.local)            │
│  ┌──────────────────────────────────────────┐ │
│  │   Pi-hole Network Manager (Python App)   │ │
│  │   Location: ~/pihole-network-manager   │ │
│  │                                            │ │
│  │   ┌────────────┐  ┌────────────────────┐ │ │
│  │   │  main.py   │  │  Management        │ │ │
│  │   │            │  │  Modules           │ │ │
│  │   └─────┬──────┘  └─────────┬──────────┘ │ │
│  │         │                   │             │ │
│  │         ▼                   ▼             │ │
│  │   ┌──────────────────────────────────┐   │ │
│  │   │   core/local_executor.py         │   │ │
│  │   │   - execute_command()            │   │ │
│  │   │   - query_database()             │   │ │
│  │   │   - read_file() / write_file()   │   │ │
│  │   └───────────┬──────────────────────┘   │ │
│  │               ▼                           │ │
│  │   ┌─────────────────┐  ┌──────────────┐ │ │
│  │   │   Pi-hole       │  │   System     │ │ │
│  │   │   (FTL, DNS)    │  │   Services   │ │ │
│  │   └─────────────────┘  └──────────────┘ │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

**Key Characteristics**:
- Single-component architecture (no client/server separation)
- Direct subprocess execution (no SSH overhead)
- Direct SQLite database access (faster than subprocess for queries)
- Passwordless sudo for specific Pi-hole commands only

---

## Python Standards

### Version and Dependencies

**Required**: Python 3.11+

**Core Dependencies** (`requirements.txt`):
```
rich>=13.0.0         # TUI
PyYAML>=6.0          # Configuration
cryptography>=41.0   # Router password encryption
requests>=2.31.0     # Router API calls
pandas>=2.0.0        # Data analysis
```

**Why These Versions**:
- Python 3.11+: Modern syntax, performance improvements
- Rich 13.0+: Latest TUI features
- PyYAML 6.0+: Security fixes
- cryptography 41.0+: Secure encryption for router passwords

**Removed Dependencies**:
- ~~paramiko~~ - No longer needed (no SSH for Pi-hole operations)

### Code Style

**PEP 8 Compliance** with project-specific conventions:

```python
# ✅ Good: Clear function names, type hints
def execute_pihole_command(
    command: str,
    use_sudo: bool = True,
    timeout: int = 30
) -> tuple[bool, str, str]:
    """Execute a Pi-hole command via subprocess.

    Args:
        command: Command to execute
        use_sudo: Whether to prefix with sudo
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    from core.local_executor import execute_command
    return execute_command(command, sudo=use_sudo, timeout=timeout)


# ❌ Bad: No type hints, unclear return
def exec_cmd(cmd, sudo=False):
    from core.local_executor import execute_command
    return execute_command(cmd, sudo=sudo)
```

**Naming Conventions**:
- Functions: `snake_case`, verb-based (`get_blocklists`, `rebuild_gravity`)
- Classes: `PascalCase`, noun-based (`Config`, `BlocklistManager`)
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_TIMEOUT`, `GRAVITY_DB_PATH`)
- Private: Prefix with `_` (`_validate_config`, `_internal_state`)

### Type Hints

**Always use type hints** for function signatures:

```python
from typing import Optional, Dict, List, Tuple

# ✅ Good: Clear types
def get_gravity_stats() -> Dict[str, int]:
    """Get gravity database statistics.

    Returns:
        Dictionary with 'total_domains', 'blocklists', etc.
    """
    pass

# ✅ Good: Optional return types
def find_device_by_mac(mac: str) -> Optional[Dict[str, str]]:
    """Find device by MAC address.

    Returns:
        Device info dict or None if not found
    """
    pass

# ❌ Bad: No type hints
def get_stats():
    pass
```

### Docstrings

**Google-style docstrings** for all public functions:

```python
def upload_blocklist_profile(
    profile_name: str,
    blocklists: List[str]
) -> bool:
    """Upload a blocklist profile to Pi-hole.

    This function uploads blocklists to the gravity database,
    replacing any existing profile with the same name.

    Args:
        profile_name: Name for the profile (e.g., 'aggressive')
        blocklists: List of blocklist URLs

    Returns:
        True if upload succeeded, False otherwise

    Raises:
        PermissionError: If user lacks sudo privileges
        DatabaseError: If gravity database is locked

    Example:
        >>> success = upload_blocklist_profile(
        ...     'moderate',
        ...     ['https://example.com/blocklist.txt']
        ... )
    """
    pass
```

---

## Local Execution Patterns

### Execute Command Pattern

**Basic Command Execution**:

```python
from core.local_executor import execute_command

# ✅ Good: Execute with explicit sudo control
# Non-sudo command
success, stdout, stderr = execute_command("pihole status", sudo=False)

# Sudo command (explicit)
success, stdout, stderr = execute_command("pihole restartdns", sudo=True, timeout=60)

# Check return value
if not success:
    from core.ui import show_error
    show_error(f"Command failed: {stderr}")
    return False
```

**Command Timeout Guidelines**:
- Quick queries: 10-30 seconds (`pihole status`, `cat /etc/pihole/setupVars.conf`)
- Database operations: 60-120 seconds (`pihole -g`, gravity database modifications)
- Service restarts: 30-60 seconds (`sudo systemctl restart pihole-FTL`)

**Why Local Execution?**:
- **Faster**: Direct subprocess execution vs SSH overhead
- **Simpler**: No connection management, key exchange, authentication
- **More Reliable**: No network dependency for Pi-hole operations
- **More Secure**: Fewer attack surfaces, no SSH for Pi-hole operations

### Database Query Patterns

**Direct SQLite Access** (preferred for queries):

```python
from core.local_executor import query_database, query_database_dict

# ✅ Best: Use query_database_dict for easier data handling
def get_blocklists() -> List[Dict[str, any]]:
    """Get all configured blocklists.

    Returns:
        List of dicts with keys: id, address, enabled, comment
    """
    query = "SELECT id, address, enabled, comment FROM adlist"
    results = query_database_dict("/etc/pihole/gravity.db", query)
    return results

# Usage
blocklists = get_blocklists()
for blocklist in blocklists:
    print(f"ID: {blocklist['id']}, URL: {blocklist['address']}")


# ✅ Good: Use query_database for raw tuples
def get_domain_count() -> Optional[int]:
    """Get total number of blocked domains."""
    query = "SELECT COUNT(*) FROM gravity"
    results = query_database("/etc/pihole/gravity.db", query)

    if results:
        return results[0][0]  # First row, first column
    return None


# ❌ Slower: Execute via subprocess (only when query_database won't work)
def get_count_slow() -> Optional[int]:
    """Get domain count via subprocess (slower)."""
    query = "SELECT COUNT(*) FROM gravity"
    command = f'sqlite3 /etc/pihole/gravity.db "{query}"'
    success, stdout, stderr = execute_command(command, sudo=True)

    if success:
        try:
            return int(stdout.strip())
        except ValueError:
            return None
    return None
```

**Performance Comparison**:
- `query_database()`: Direct SQLite connection (~10ms)
- `execute_command()` with sqlite3: Subprocess overhead (~50-100ms)

**Use `query_database()` for**:
- SELECT queries
- Complex JOINs
- Statistics gathering
- Frequent queries

**Use `execute_command()` for**:
- INSERT/UPDATE/DELETE (safer with error handling)
- Commands requiring specific sqlite3 flags
- Operations needing sudo for file permissions

### File Operations

**Read/Write Files**:

```python
from core.local_executor import read_file, write_file

# ✅ Good: Read configuration file
def get_pihole_config() -> Dict[str, str]:
    """Get Pi-hole configuration."""
    content = read_file("/etc/pihole/setupVars.conf")

    config = {}
    for line in content.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            config[key] = value

    return config

# ✅ Good: Write file with error handling
def save_profile(profile_name: str, content: str) -> bool:
    """Save blocklist profile."""
    path = f"/etc/pihole/profiles/{profile_name}.yaml"

    success = write_file(path, content, sudo=True)

    if not success:
        from core.ui import show_error
        show_error(f"Failed to write profile: {path}")
        return False

    return True
```

### Sudo Handling

**Passwordless Sudo Configuration**:

The application uses passwordless sudo for specific Pi-hole commands only. Configuration at `/etc/sudoers.d/pihole-manager`:

```bash
# Allow pihole-manager group to run specific commands without password
%pihole-manager ALL=(ALL) NOPASSWD: /usr/local/bin/pihole
%pihole-manager ALL=(ALL) NOPASSWD: /usr/bin/sqlite3 /etc/pihole/gravity.db*
%pihole-manager ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart pihole-FTL
%pihole-manager ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop pihole-FTL
%pihole-manager ALL=(ALL) NOPASSWD: /usr/bin/systemctl start pihole-FTL
```

**Explicit Sudo Control in Code**:

```python
from core.local_executor import execute_command

# ✅ Good: Explicit sudo awareness
def restart_pihole_service() -> bool:
    """Restart Pi-hole FTL service (requires sudo)."""
    from core.ui import show_status
    show_status("Restarting Pi-hole FTL service...", "info")

    # Explicitly use sudo
    success, stdout, stderr = execute_command(
        "systemctl restart pihole-FTL",
        sudo=True,
        timeout=60
    )

    if not success:
        from core.ui import show_error
        show_error(f"Restart failed: {stderr}")
        return False

    # Wait for service to stabilize
    import time
    time.sleep(5)

    # Verify service is active
    success, stdout, _ = execute_command("systemctl is-active pihole-FTL", sudo=False)
    return success and stdout.strip() == "active"


# ❌ Bad: Implicit sudo assumption
def restart_pihole_bad() -> bool:
    execute_command("systemctl restart pihole-FTL", sudo=False)  # Fails without sudo
    return True
```

---

## Pi-hole Interaction

### Pi-hole Commands

**Standard Commands**:

```python
from core.local_executor import execute_command
from core.ui import show_status, show_success, show_error
from typing import Dict, Optional

# ✅ Pattern: Pi-hole command wrapper
class PiHoleCommands:
    """Wrapper for common Pi-hole commands."""

    @staticmethod
    def status() -> Dict[str, bool]:
        """Get Pi-hole service status."""
        success, stdout, _ = execute_command("pihole status", sudo=False)
        return {
            "success": success,
            "enabled": "Enabled" in stdout,
            "ftl_running": "Active" in stdout
        }

    @staticmethod
    def rebuild_gravity(timeout: int = 300) -> bool:
        """Rebuild gravity database (requires sudo)."""
        show_status("Rebuilding gravity database...", "info")
        show_status("This may take several minutes...", "warning")

        success, stdout, stderr = execute_command(
            "pihole -g",
            sudo=True,
            timeout=timeout
        )

        if success:
            show_success("Gravity rebuild complete")
        else:
            show_error(f"Rebuild failed: {stderr}")

        return success

    @staticmethod
    def get_version() -> Optional[str]:
        """Get Pi-hole version."""
        success, stdout, _ = execute_command("pihole -v", sudo=False)
        if success:
            # Parse version from output
            for line in stdout.split('\n'):
                if "Pi-hole version" in line:
                    return line.split()[-1]
        return None

    @staticmethod
    def enable() -> bool:
        """Enable Pi-hole blocking."""
        success, _, stderr = execute_command("pihole enable", sudo=True)
        if not success:
            show_error(f"Failed to enable Pi-hole: {stderr}")
        return success

    @staticmethod
    def disable(duration: Optional[int] = None) -> bool:
        """Disable Pi-hole blocking.

        Args:
            duration: Optional duration in seconds (None = permanent)
        """
        if duration:
            command = f"pihole disable {duration}s"
        else:
            command = "pihole disable"

        success, _, stderr = execute_command(command, sudo=True)
        if not success:
            show_error(f"Failed to disable Pi-hole: {stderr}")
        return success
```

### Database Interaction

**Gravity Database Queries**:

```python
from core.local_executor import query_database, query_database_dict
from core.ui import show_error
from typing import List, Dict, Optional

# ✅ Good: Use query_database_dict for structured data
def get_adlists() -> List[Dict[str, any]]:
    """Get all configured blocklists.

    Returns:
        List of dicts with keys: id, address, enabled, comment
    """
    query = "SELECT id, address, enabled, comment FROM adlist"
    results = query_database_dict("/etc/pihole/gravity.db", query)
    return results if results else []


def get_blocklist_count() -> Optional[int]:
    """Get total number of blocked domains."""
    query = "SELECT COUNT(*) FROM gravity"
    results = query_database("/etc/pihole/gravity.db", query)

    if results:
        return results[0][0]
    return None


def get_whitelisted_domains() -> List[str]:
    """Get all whitelisted domains."""
    query = "SELECT domain FROM domainlist WHERE type = 0"
    results = query_database_dict("/etc/pihole/gravity.db", query)
    return [row['domain'] for row in results]


def get_blacklisted_domains() -> List[str]:
    """Get all blacklisted domains."""
    query = "SELECT domain FROM domainlist WHERE type = 1"
    results = query_database_dict("/etc/pihole/gravity.db", query)
    return [row['domain'] for row in results]
```

**Database Modifications** (Use with caution):

```python
from core.local_executor import execute_command
from core.ui import show_error, show_success

# ✅ Good: Safe database modification with backup
def add_blocklist(url: str, comment: str = "") -> bool:
    """Add blocklist to gravity database.

    WARNING: Always backup gravity.db before modifications.

    Args:
        url: Blocklist URL
        comment: Optional comment

    Returns:
        True if addition succeeded
    """
    # Backup first
    backup_cmd = "cp /etc/pihole/gravity.db /etc/pihole/gravity.db.backup"
    execute_command(backup_cmd, sudo=True)

    # Escape single quotes in SQL
    url_escaped = url.replace("'", "''")
    comment_escaped = comment.replace("'", "''")

    # Insert blocklist
    query = f"""
    INSERT INTO adlist (address, enabled, comment)
    VALUES ('{url_escaped}', 1, '{comment_escaped}');
    """
    command = f'sqlite3 /etc/pihole/gravity.db "{query}"'

    success, stdout, stderr = execute_command(command, sudo=True)

    if not success:
        # Restore backup on failure
        execute_command(
            "cp /etc/pihole/gravity.db.backup /etc/pihole/gravity.db",
            sudo=True
        )
        show_error(f"Failed to add blocklist: {stderr}")
        return False

    show_success("Blocklist added successfully")
    return True


def add_domain_to_whitelist(domain: str) -> bool:
    """Add domain to whitelist.

    Args:
        domain: Domain to whitelist

    Returns:
        True if addition succeeded
    """
    # Escape domain
    domain_escaped = domain.replace("'", "''")

    # type = 0 for whitelist (exact match)
    # type = 2 for regex whitelist
    query = f"""
    INSERT INTO domainlist (type, domain, enabled, comment)
    VALUES (0, '{domain_escaped}', 1, 'Added via manager');
    """
    command = f'sqlite3 /etc/pihole/gravity.db "{query}"'

    success, _, stderr = execute_command(command, sudo=True)

    if not success:
        show_error(f"Failed to add to whitelist: {stderr}")
        return False

    # IMPORTANT: Rebuild gravity after domain changes
    show_status("Rebuilding gravity database...", "info")
    return PiHoleCommands.rebuild_gravity()
```

**CRITICAL**: Always call `pihole -g` (gravity rebuild) after modifying the domainlist table.

---

## Core Module Usage

### local_executor (`core/local_executor.py`)

**Primary Execution Interface**:

```python
from core.local_executor import (
    execute_command,
    execute_streaming,
    query_database,
    query_database_dict,
    read_file,
    write_file,
    file_exists
)

# ✅ Pattern: Standard command execution
success, stdout, stderr = execute_command("pihole status", sudo=False, timeout=30)

# ✅ Pattern: Streaming output (for long-running commands)
for line in execute_streaming("pihole -g", sudo=True):
    print(line)  # Real-time output

# ✅ Pattern: Database query (returns list of tuples)
results = query_database("/etc/pihole/gravity.db", "SELECT * FROM adlist")

# ✅ Pattern: Database query (returns list of dicts - easier to use)
results = query_database_dict("/etc/pihole/gravity.db", "SELECT id, address FROM adlist")

# ✅ Pattern: File operations
content = read_file("/etc/pihole/setupVars.conf", sudo=True)
success = write_file("/etc/pihole/custom.conf", "CUSTOM=value", sudo=True)
exists = file_exists("/etc/pihole/gravity.db")
```

**Available Functions**:
- `execute_command(command, sudo=False, timeout=30)` - Execute command, return (success, stdout, stderr)
- `execute_streaming(command, sudo=False)` - Execute command, yield output lines in real-time
- `query_database(db_path, query)` - Execute SQLite query, return list of tuples
- `query_database_dict(db_path, query)` - Execute SQLite query, return list of dicts
- `read_file(path, sudo=False)` - Read file, return content string
- `write_file(path, content, sudo=False)` - Write file, return success boolean
- `file_exists(path)` - Check if file exists, return boolean

### Config (`core/config.py`)

**Configuration Loading**:

```python
from core.config import Config
from core.ui import show_error

# ✅ Pattern: Load and validate config
config = Config()

if not config.is_configured():
    show_error("Configuration not found. Run initial-setup.sh first.")
    return False

# Access configuration values
web_url = config.get('pihole', {}).get('web_url')
router_host = config.get('router', {}).get('host')

# Router password encryption/decryption
config.encrypt_router_password('password123')
password = config.decrypt_router_password()
```

**Configuration Structure** (`~/pihole-network-manager/config.yaml`):
```yaml
pihole:
  web_url: "http://pihole.local/admin"

router:  # Optional
  type: tplink_axe5400
  host: 192.168.1.1
  username: admin
  password_encrypted: "<base64>"
```

**Configuration Location**: `~/pihole-network-manager/config.yaml` (on the Pi)

### UI (`core/ui.py`)

**Console Output**:

```python
from core.ui import (
    show_menu,
    show_status,
    show_success,
    show_error,
    show_warning,
    show_table
)

# ✅ Pattern: Rich console for all output
show_status("Processing...", "info")
show_success("Operation successful")
show_warning("Slow connection detected")
show_error("Operation failed")

# Menu
choice = show_menu(
    "Main Menu",
    [
        "View Status",
        "Manage Blocklists",
        "Manage Devices",
        "Back"
    ],
    allow_back=True
)

# Tables
headers = ["ID", "Domain", "Status"]
data = [
    ["1", "example.com", "Blocked"],
    ["2", "test.com", "Allowed"]
]
show_table("Domains", headers, data)
```

**NEVER use `print()`**: Always use Rich console functions for consistent styling.

### State (`core/state.py`)

**Setup State Tracking**:

```python
from core.state import State
from core.ui import show_error

# ✅ Pattern: Check setup state
state = State()

if not state.is_setup_complete():
    show_error("Setup not complete. Run initial-setup.sh first.")
    return False

# Set setup complete (done by initial-setup.sh)
state.mark_setup_complete()
```

**State File Location**: `~/pihole-network-manager/state.json` (on the Pi)

**State Structure**:
```json
{
  "setup_complete": true
}
```

---

## Management Module Patterns

### Standard Module Structure

**Template for Management Modules**:

```python
"""
Module: management/<feature>.py
Purpose: <Brief description>
"""

from typing import Dict, List, Optional
from core.local_executor import execute_command, query_database_dict
from core.ui import show_menu, show_status, show_success, show_error, show_table
from core.config import Config


def run(config: Config) -> None:
    """Main entry point for <feature> management.

    Args:
        config: Application configuration
    """
    while True:
        choice = show_menu(
            "<Feature> Management",
            [
                "List items",
                "Add item",
                "Remove item",
                "Back to main menu"
            ],
            allow_back=True
        )

        if choice == 1:
            list_items()
        elif choice == 2:
            add_item()
        elif choice == 3:
            remove_item()
        elif choice is None:  # Back selected
            break


def list_items() -> None:
    """List all items."""
    items = _fetch_items()

    if not items:
        show_warning("No items found")
        return

    # Display using show_table
    headers = ["ID", "Name", "Status"]
    data = [[str(item['id']), item['name'], item['status']] for item in items]
    show_table("Items", headers, data)


def add_item() -> None:
    """Add a new item."""
    from rich.prompt import Prompt

    name = Prompt.ask("Item name")

    if not name:
        show_error("Name cannot be empty")
        return

    success = _create_item(name)

    if success:
        show_success("Item added successfully")
    else:
        show_error("Failed to add item")


def remove_item() -> None:
    """Remove an item."""
    from rich.prompt import Prompt, Confirm

    items = _fetch_items()

    if not items:
        show_warning("No items to remove")
        return

    # Show items
    list_items()

    item_id = Prompt.ask("Item ID to remove")

    if not Confirm.ask(f"Remove item {item_id}?"):
        show_status("Cancelled", "info")
        return

    success = _delete_item(item_id)

    if success:
        show_success("Item removed")
    else:
        show_error("Failed to remove item")


def _fetch_items() -> List[Dict]:
    """Fetch items from gravity database (private helper)."""
    query = "SELECT id, name, status FROM items"
    results = query_database_dict("/etc/pihole/gravity.db", query)
    return results if results else []


def _create_item(name: str) -> bool:
    """Create item in database (private helper)."""
    name_escaped = name.replace("'", "''")
    query = f"INSERT INTO items (name, status) VALUES ('{name_escaped}', 'active')"
    command = f'sqlite3 /etc/pihole/gravity.db "{query}"'
    success, _, _ = execute_command(command, sudo=True)
    return success


def _delete_item(item_id: str) -> bool:
    """Delete item from database (private helper)."""
    query = f"DELETE FROM items WHERE id = {item_id}"
    command = f'sqlite3 /etc/pihole/gravity.db "{query}"'
    success, _, _ = execute_command(command, sudo=True)
    return success
```

**Module Signature Change**:
```python
# OLD (removed in conversion):
# def run(ssh_client: SSHClient, config: Config) -> None:

# NEW (current):
def run(config: Config) -> None:
    """Main entry point for management module."""
```

### Module Examples

**Blocklist Management** (`management/blocklists.py`):
- `run(config)` - Main menu
- `switch_profile()` - Switch active profile
- `view_current_blocklists()` - View active lists
- `add_custom_blocklist()` - Add custom URL
- `rebuild_gravity()` - Trigger gravity rebuild

**Device Management** (`management/devices.py`):
- `run(config)` - Main menu
- `list_devices()` - List all network devices
- `add_device()` - Add device manually
- `remove_device()` - Remove device
- `block_device()` - Block device by MAC

---

## Testing Approaches

### Unit Testing

**Test Structure**:

```python
# tests/test_local_executor.py
import unittest
from unittest.mock import patch, MagicMock
from core.local_executor import execute_command, query_database

class TestLocalExecutor(unittest.TestCase):
    """Unit tests for local_executor."""

    @patch('subprocess.run')
    def test_execute_command_success(self, mock_run):
        """Test successful command execution."""
        # Arrange
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Act
        success, stdout, stderr = execute_command("test command", sudo=False)

        # Assert
        self.assertTrue(success)
        self.assertEqual(stdout, "output")
        self.assertEqual(stderr, "")
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_execute_command_with_sudo(self, mock_run):
        """Test command execution with sudo."""
        # Arrange
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Act
        execute_command("pihole status", sudo=True)

        # Assert
        # Verify sudo was added to command
        call_args = mock_run.call_args
        self.assertIn("sudo", call_args[0][0])

    @patch('sqlite3.connect')
    def test_query_database(self, mock_connect):
        """Test database query execution."""
        # Arrange
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [(1, "test")]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Act
        results = query_database("/etc/pihole/gravity.db", "SELECT * FROM test")

        # Assert
        self.assertEqual(results, [(1, "test")])
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")


if __name__ == '__main__':
    unittest.main()
```

### Integration Testing

**On-Pi Testing**:

```python
# tests/integration/test_pihole_commands.py
import unittest
from core.local_executor import execute_command, query_database
from management.blocklists import get_blocklist_count

class TestPiHoleIntegration(unittest.TestCase):
    """Integration tests to run on actual Pi."""

    def test_pihole_status(self):
        """Test Pi-hole status check."""
        success, stdout, _ = execute_command("pihole status", sudo=False)
        self.assertTrue(success)
        self.assertIn("Active", stdout)

    def test_gravity_database_access(self):
        """Test gravity database query."""
        count = get_blocklist_count()
        self.assertIsNotNone(count)
        self.assertGreater(count, 0)

    def test_sudo_permissions(self):
        """Test passwordless sudo is configured."""
        success, stdout, stderr = execute_command(
            "pihole -v",
            sudo=True,
            timeout=10
        )
        self.assertTrue(success, f"Sudo failed: {stderr}")


if __name__ == '__main__':
    unittest.main()
```

### Manual Testing

**Local Development**:
1. Test UI navigation in local environment
2. Test configuration loading
3. Test mock data handling
4. Test error handling paths

**On-Pi Testing**:
1. SSH to Pi: `ssh pi@pihole.local`
2. Activate venv: `source ~/.pihole-manager-venv/bin/activate`
3. Run application: `python3 ~/pihole-network-manager/main.py`
4. Test all management features
5. Verify no errors in logs: `tail -f /tmp/pihole-manager-*.log`

---

## Error Handling

### Exception Hierarchy

```python
# core/exceptions.py

class PiHoleManagerError(Exception):
    """Base exception for Pi-hole Manager."""
    pass


class ExecutionError(PiHoleManagerError):
    """Command execution failed."""
    pass


class DatabaseError(PiHoleManagerError):
    """Database operation failed."""
    pass


class PermissionError(PiHoleManagerError):
    """Permission denied (sudo required)."""
    pass


class ConfigurationError(PiHoleManagerError):
    """Configuration invalid or missing."""
    pass
```

### Error Handling Patterns

```python
from core.local_executor import execute_command
from core.ui import show_error, show_warning
from typing import Optional

# ✅ Good: Specific exception handling
def restart_pihole() -> bool:
    """Restart Pi-hole with comprehensive error handling."""
    try:
        success, stdout, stderr = execute_command(
            "systemctl restart pihole-FTL",
            sudo=True,
            timeout=60
        )

        if not success:
            show_error(f"Restart failed: {stderr}")
            return False

        return True

    except TimeoutError:
        show_error("Restart timed out after 60 seconds")
        show_warning("Pi-hole may still be restarting")
        return False

    except PermissionError:
        show_error("Permission denied - check sudoers configuration")
        show_warning("Run: sudo ~/pihole-network-manager/pi-setup/initial-setup.sh")
        return False

    except Exception as e:
        show_error(f"Unexpected error: {e}")
        return False


# ❌ Bad: Generic exception handling
def restart_bad() -> bool:
    try:
        execute_command("systemctl restart pihole-FTL", sudo=True)
        return True
    except Exception as e:
        print(f"Error: {e}")  # Not helpful, uses print()
        return False
```

---

## Configuration Management

### Configuration File Location

**Standard Path**: `~/pihole-network-manager/config.yaml` (on the Pi)

### Configuration Validation

```python
from core.config import Config
from core.ui import show_error

# ✅ Good: Validate configuration on load
def load_and_validate_config() -> Optional[Config]:
    """Load and validate configuration file."""
    config = Config()

    if not config.is_configured():
        show_error("Configuration not found")
        show_error("Run: sudo ~/pihole-network-manager/pi-setup/initial-setup.sh")
        return None

    # Validate web_url
    web_url = config.get('pihole', {}).get('web_url')
    if not web_url:
        show_error("Missing required config: pihole.web_url")
        return None

    return config
```

---

## Best Practices

### 1. Use Local Executor Functions

```python
# ✅ Good: Use local_executor
from core.local_executor import execute_command
success, stdout, stderr = execute_command("pihole status", sudo=False)

# ❌ Bad: Direct subprocess
import subprocess
result = subprocess.run(["pihole", "status"])
```

### 2. Use query_database for SELECT Queries

```python
# ✅ Good: Direct database access (faster)
from core.local_executor import query_database_dict
results = query_database_dict("/etc/pihole/gravity.db", "SELECT * FROM adlist")

# ❌ Slower: Via subprocess
success, stdout, _ = execute_command('sqlite3 /etc/pihole/gravity.db "SELECT * FROM adlist"', sudo=True)
```

### 3. Explicit Sudo Control

```python
# ✅ Good: Explicitly specify sudo requirement
execute_command("pihole restartdns", sudo=True)

# ❌ Bad: Forget sudo (will fail)
execute_command("pihole restartdns", sudo=False)
```

### 4. Timeout Appropriately

```python
# ✅ Good: Set timeout based on operation
execute_command("pihole status", sudo=False, timeout=10)  # Quick
execute_command("pihole -g", sudo=True, timeout=300)  # Slow

# ❌ Bad: No timeout or unrealistic timeout
execute_command("pihole -g", sudo=True, timeout=10)  # Too short
```

### 5. User Confirmation for Destructive Operations

```python
from rich.prompt import Confirm

# ✅ Good: Confirm before deletion
if not Confirm.ask(f"Delete device {device_name}?"):
    show_status("Cancelled", "info")
    return

# Proceed with deletion
```

### 6. Rich Console for All Output

```python
# ✅ Good: Use Rich UI functions
from core.ui import show_success
show_success("Operation complete")

# ❌ Bad: Use print()
print("Operation complete")  # No styling, inconsistent
```

### 7. Type Hints Everywhere

```python
# ✅ Good
from typing import List, Dict
def get_devices() -> List[Dict[str, str]]:
    pass

# ❌ Bad
def get_devices():
    pass
```

### 8. Docstrings for Public Functions

```python
# ✅ Good
def rebuild_gravity() -> bool:
    """Rebuild Pi-hole gravity database.

    Returns:
        True if rebuild succeeded
    """
    pass

# ❌ Bad
def rebuild_gravity():
    pass
```

### 9. Always Rebuild Gravity After Domain Changes

```python
# ✅ Good: Rebuild after modifying domainlist
def add_to_whitelist(domain: str) -> bool:
    # ... add domain to database ...

    # REQUIRED: Rebuild gravity
    return rebuild_gravity()

# ❌ Bad: Forget to rebuild (changes won't take effect)
def add_bad(domain: str) -> bool:
    # ... add domain to database ...
    return True  # Changes not applied!
```

### 10. Escape SQL Strings

```python
# ✅ Good: Escape single quotes
domain_escaped = domain.replace("'", "''")
query = f"INSERT INTO domainlist VALUES (1, '{domain_escaped}', 1)"

# ❌ Bad: No escaping (SQL injection risk)
query = f"INSERT INTO domainlist VALUES (1, '{domain}', 1)"
```

---

## Summary

**Key Takeaways**:

1. ✅ **Local Execution** - All Pi operations via subprocess, no SSH
2. ✅ **Direct Database Access** - Use `query_database()` for fast queries
3. ✅ **Passwordless Sudo** - Specific commands only via `/etc/sudoers.d/pihole-manager`
4. ✅ **Rich TUI** - Consistent UI with Rich library (never use `print()`)
5. ✅ **Type Hints** - All function signatures typed
6. ✅ **Error Handling** - Specific exceptions, helpful messages
7. ✅ **Configuration** - YAML-driven at `~/pihole-network-manager/config.yaml`
8. ✅ **Testing** - Unit tests (mocked subprocess) + Integration tests (on-Pi)
9. ✅ **Documentation** - Google-style docstrings
10. ✅ **Best Practices** - Explicit sudo, appropriate timeouts, SQL escaping, gravity rebuild

**Architecture Shift**:
- **Old**: Client application on local computer → SSH → Raspberry Pi
- **New**: Application runs directly on Raspberry Pi → subprocess → Pi-hole

**This guide ensures consistent, maintainable code for the local execution architecture.**
