#!/usr/bin/env python3
"""
Local Executor - Local Command Execution Module

Replaces SSH client for local execution on Raspberry Pi.
Provides functions for command execution, file operations, and database queries.
"""

import subprocess
import sqlite3
from pathlib import Path
from typing import Tuple, List, Optional, Any


def execute_command(
    command: str,
    sudo: bool = False,
    timeout: int = 30,
    shell: bool = True
) -> Tuple[bool, str, str]:
    """
    Execute command locally (replaces ssh_client.execute)

    Args:
        command: Command to execute
        sudo: Prepend 'sudo' to command
        timeout: Command timeout in seconds
        shell: Execute via shell (default True)

    Returns:
        Tuple of (success, stdout, stderr)

    Examples:
        >>> success, output, error = execute_command("pihole status", sudo=True)
        >>> success, output, error = execute_command("ls -la /etc/pihole")
    """
    if sudo:
        command = f"sudo {command}"

    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return (
            result.returncode == 0,
            result.stdout.strip(),
            result.stderr.strip()
        )

    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout} seconds")

    except Exception as e:
        return (False, "", f"Command execution failed: {str(e)}")


def execute_streaming(
    command: str,
    sudo: bool = False,
    timeout: int = 300
) -> Tuple[bool, List[str], str]:
    """
    Execute command with line-by-line streaming output

    Args:
        command: Command to execute
        sudo: Prepend 'sudo' to command
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, output_lines, stderr)

    Examples:
        >>> success, lines, error = execute_streaming("pihole -g", sudo=True)
        >>> for line in lines:
        ...     print(line)
    """
    if sudo:
        command = f"sudo {command}"

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output_lines = []
        for line in process.stdout:
            output_lines.append(line.rstrip())

        process.wait(timeout=timeout)
        stderr = process.stderr.read().strip()

        return (
            process.returncode == 0,
            output_lines,
            stderr
        )

    except subprocess.TimeoutExpired:
        process.kill()
        return (False, [], f"Command timed out after {timeout} seconds")

    except Exception as e:
        return (False, [], f"Streaming execution failed: {str(e)}")


def read_file(file_path: str, sudo: bool = False) -> Tuple[bool, str]:
    """
    Read file contents

    Args:
        file_path: Path to file
        sudo: Use sudo for reading

    Returns:
        Tuple of (success, content)

    Examples:
        >>> success, content = read_file("/etc/pihole/setupVars.conf")
        >>> success, content = read_file("/etc/pihole/pihole-FTL.conf", sudo=True)
    """
    path = Path(file_path)

    # Try direct read first
    if not sudo:
        try:
            if not path.exists():
                return (False, f"File not found: {file_path}")

            return (True, path.read_text())

        except PermissionError:
            # Fall back to sudo
            sudo = True

        except Exception as e:
            return (False, f"Failed to read file: {str(e)}")

    # Use sudo cat if needed
    if sudo:
        success, stdout, stderr = execute_command(f"cat {file_path}", sudo=True)
        if success:
            return (True, stdout)
        else:
            return (False, stderr or "Failed to read file with sudo")

    return (False, "Unknown error reading file")


def write_file(file_path: str, content: str, sudo: bool = False) -> Tuple[bool, str]:
    """
    Write content to file

    Args:
        file_path: Path to file
        content: Content to write
        sudo: Use sudo for writing

    Returns:
        Tuple of (success, error_message)

    Examples:
        >>> success, error = write_file("/tmp/test.txt", "Hello World")
        >>> success, error = write_file("/etc/pihole/custom.list", "domain.com", sudo=True)
    """
    path = Path(file_path)

    # Try direct write first
    if not sudo:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            return (True, "")

        except PermissionError:
            # Fall back to sudo
            sudo = True

        except Exception as e:
            return (False, f"Failed to write file: {str(e)}")

    # Use sudo tee if needed
    if sudo:
        # Use tee to write with sudo
        success, stdout, stderr = execute_command(
            f"tee {file_path} > /dev/null",
            sudo=True
        )

        if success:
            return (True, "")
        else:
            return (False, stderr or "Failed to write file with sudo")

    return (False, "Unknown error writing file")


def file_exists(file_path: str) -> bool:
    """
    Check if file exists

    Args:
        file_path: Path to check

    Returns:
        True if file exists

    Examples:
        >>> if file_exists("/etc/pihole/gravity.db"):
        ...     print("Database found")
    """
    return Path(file_path).exists()


def dir_exists(dir_path: str) -> bool:
    """
    Check if directory exists

    Args:
        dir_path: Directory path to check

    Returns:
        True if directory exists

    Examples:
        >>> if dir_exists("/etc/pihole"):
        ...     print("Pi-hole directory found")
    """
    path = Path(dir_path)
    return path.exists() and path.is_dir()


def query_database(
    db_path: str,
    query: str,
    params: Optional[Tuple] = None,
    fetch_all: bool = True
) -> Tuple[bool, Any, str]:
    """
    Execute SQLite query with direct database access

    Faster than subprocess sqlite3 commands.

    Args:
        db_path: Path to SQLite database
        query: SQL query to execute
        params: Optional query parameters (for prepared statements)
        fetch_all: Fetch all rows (True) or single row (False)

    Returns:
        Tuple of (success, results, error_message)
        - For SELECT: results = list of tuples (fetch_all=True) or single tuple (fetch_all=False)
        - For INSERT/UPDATE/DELETE: results = rows_affected

    Examples:
        >>> # Query blocklists
        >>> success, rows, error = query_database(
        ...     "/etc/pihole/gravity.db",
        ...     "SELECT * FROM adlist WHERE enabled = 1"
        ... )

        >>> # Insert domain with parameters
        >>> success, rows_affected, error = query_database(
        ...     "/etc/pihole/gravity.db",
        ...     "INSERT INTO domainlist (domain, type, enabled) VALUES (?, ?, ?)",
        ...     params=("example.com", 1, 1)
        ... )
    """
    if not file_exists(db_path):
        return (False, None, f"Database not found: {db_path}")

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Handle results based on query type
        query_type = query.strip().upper().split()[0]

        if query_type == "SELECT":
            # Fetch results
            if fetch_all:
                results = cursor.fetchall()
            else:
                results = cursor.fetchone()
        else:
            # INSERT/UPDATE/DELETE - commit and return rows affected
            conn.commit()
            results = cursor.rowcount

        # Close connection
        cursor.close()
        conn.close()

        return (True, results, "")

    except sqlite3.Error as e:
        return (False, None, f"Database error: {str(e)}")

    except Exception as e:
        return (False, None, f"Query failed: {str(e)}")


def query_database_dict(
    db_path: str,
    query: str,
    params: Optional[Tuple] = None
) -> Tuple[bool, List[dict], str]:
    """
    Execute SQLite query and return results as list of dictionaries

    More convenient than tuples for named column access.

    Args:
        db_path: Path to SQLite database
        query: SQL query to execute (SELECT only)
        params: Optional query parameters

    Returns:
        Tuple of (success, results_as_dicts, error_message)

    Examples:
        >>> success, rows, error = query_database_dict(
        ...     "/etc/pihole/gravity.db",
        ...     "SELECT id, domain, enabled FROM adlist"
        ... )
        >>> for row in rows:
        ...     print(f"Domain: {row['domain']}, Enabled: {row['enabled']}")
    """
    if not file_exists(db_path):
        return (False, [], f"Database not found: {db_path}")

    try:
        # Connect with Row factory for dict access
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Execute query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Convert rows to dicts
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]

        # Close connection
        cursor.close()
        conn.close()

        return (True, results, "")

    except sqlite3.Error as e:
        return (False, [], f"Database error: {str(e)}")

    except Exception as e:
        return (False, [], f"Query failed: {str(e)}")
