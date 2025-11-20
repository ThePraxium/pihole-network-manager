"""
Configuration Utility

Manages configuration file loading, saving, and validation.
Enhanced for unified setup and management workflow.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """Get the project root directory (where main.py lives)."""
    return Path(__file__).parent.parent


class Config:
    """Configuration manager for Pi-hole Network Manager"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to config file (default: <project-root>/config.yaml)
        """
        self.config_path = config_path or (get_project_root() / "config.yaml")
        self.config_dir = self.config_path.parent
        self.config = self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load configuration from file

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            return self.get_default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config if config else self.get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.get_default_config()

    def save(self):
        """Save configuration to file"""
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)

            # Set restrictive permissions
            self.config_path.chmod(0o600)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration

        Returns:
            Default configuration dictionary
        """
        return {
            "pihole": {
                "web_url": "http://localhost/admin"  # Local Pi-hole web interface
            },
            "preferences": {
                "show_tips": True,
                "confirm_actions": True
            }
        }

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def is_configured(self) -> bool:
        """
        Check if configuration is complete

        Returns:
            True if basic configuration is present
        """
        # For local execution, just check if we have a web URL configured
        web_url = self.get("pihole", "web_url")
        return bool(web_url)

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check Pi-hole configuration (minimal for local execution)
        if not self.get("pihole", "web_url"):
            errors.append("Pi-hole web URL is not configured")

        return len(errors) == 0, errors

    def __repr__(self) -> str:
        """String representation"""
        return f"Config(path={self.config_path})"


def create_default_config(config_path: Optional[Path] = None) -> Config:
    """
    Create and save default configuration

    Args:
        config_path: Path to save config file

    Returns:
        Config object
    """
    config = Config(config_path)
    config.save()
    return config
