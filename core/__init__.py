"""
Core utilities for Pi-hole Network Manager.

This package provides shared functionality used by both setup and management modules:
- Configuration management
- SSH client with password and key-based authentication
- Setup state tracking
- UI components (Rich-based terminal interface)
"""

__all__ = ['Config', 'SSHClient', 'State', 'console', 'show_menu', 'show_table', 'show_status']
