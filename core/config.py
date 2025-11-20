"""
Configuration Utility

Manages configuration file loading, saving, and validation.
Enhanced for unified setup and management workflow.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import base64
import hashlib


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
            "router": {
                "enabled": False,
                "host": "192.168.1.1",
                "username": "admin",
                "password": "",  # Encrypted
                "automation_mode": False
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


    def get_router_connection(self) -> Optional[Dict[str, Any]]:
        """
        Get router connection parameters

        Returns:
            Dictionary with host, username, password or None if disabled
        """
        if not self.get("router", "enabled", False):
            return None

        return {
            "host": self.get("router", "host"),
            "username": self.get("router", "username"),
            "password": self.get("router", "password")
        }

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

        # Check router configuration if enabled
        if self.get("router", "enabled"):
            if not self.get("router", "host"):
                errors.append("Router host is not configured")

            if not self.get("router", "username"):
                errors.append("Router username is not configured")

        return len(errors) == 0, errors


    def encrypt_password(self, password: str) -> str:
        """
        Encrypt password for storage

        Args:
            password: Plain text password

        Returns:
            Encrypted password
        """
        key = self._get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(password.encode())
        return encrypted.decode()

    def decrypt_password(self, encrypted_password: str) -> str:
        """
        Decrypt password

        Args:
            encrypted_password: Encrypted password

        Returns:
            Plain text password
        """
        if not encrypted_password:
            return ""

        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            decrypted = f.decrypt(encrypted_password.encode())
            return decrypted.decode()
        except Exception:
            return encrypted_password  # Return as-is if not encrypted

    def _get_encryption_key(self) -> bytes:
        """
        Generate encryption key from user-specific data

        Returns:
            Encryption key
        """
        # Use home directory path as basis for key
        home_path = str(Path.home())
        key_material = hashlib.sha256(home_path.encode()).digest()
        return base64.urlsafe_b64encode(key_material)


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
