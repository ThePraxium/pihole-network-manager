"""
Setup State Management

Tracks the progress of setup workflow to enable resumable setup.
Persists state to JSON file in config directory.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


# For local Pi execution, store state on the Pi itself
DEFAULT_STATE_FILE = Path("/opt/pihole-manager/state.json")


class State:
    """Setup state tracker"""

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize state tracker

        Args:
            state_file: Path to state file (default: ~/.config/pihole-manager/state.json)
        """
        self.state_file = state_file or DEFAULT_STATE_FILE
        self.state = self.load()

    def load(self) -> Dict[str, Any]:
        """
        Load state from file

        Returns:
            State dictionary
        """
        if not self.state_file.exists():
            return self.get_default_state()

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
                return state if state else self.get_default_state()
        except Exception as e:
            print(f"Error loading state: {e}")
            return self.get_default_state()

    def save(self):
        """Save state to file"""
        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)

            # Set restrictive permissions
            self.state_file.chmod(0o600)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False

    def get_default_state(self) -> Dict[str, Any]:
        """
        Get default state

        Returns:
            Default state dictionary
        """
        return {
            "setup": {
                "setup_complete": False  # Only track if initial setup is done
            },
            "timestamps": {},
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": None
            }
        }

    def is_complete(self, step: str) -> bool:
        """
        Check if a setup step is complete

        Args:
            step: Step name (info_gathered, ssh_keys_generated, etc.)

        Returns:
            True if step is complete, False otherwise
        """
        return self.state.get("setup", {}).get(step, False)

    def mark_complete(self, step: str):
        """
        Mark a setup step as complete

        Args:
            step: Step name to mark as complete
        """
        if "setup" not in self.state:
            self.state["setup"] = {}

        self.state["setup"][step] = True

        # Update timestamp
        if "timestamps" not in self.state:
            self.state["timestamps"] = {}

        self.state["timestamps"][step] = datetime.now().isoformat()
        self.state["metadata"]["last_updated"] = datetime.now().isoformat()

        self.save()

        # Log the state change if logger is available
        try:
            from core.logger import get_logger
            logger = get_logger()
            if logger.is_active():
                logger.log_state("mark_complete", step, True)
        except:
            pass  # Logger not available or not initialized

    def mark_incomplete(self, step: str):
        """
        Mark a setup step as incomplete

        Args:
            step: Step name to mark as incomplete
        """
        if "setup" not in self.state:
            self.state["setup"] = {}

        self.state["setup"][step] = False
        self.save()

    def reset_all(self):
        """Reset all setup steps"""
        self.state = self.get_default_state()
        self.save()

    def reset_step(self, step: str):
        """
        Reset a specific setup step to allow re-execution.

        Clears the step's completion status and removes its timestamp.
        Use this when you need to retry a specific step (e.g., file transfer failed).

        Args:
            step: Step name to reset (info_gathered, ssh_keys_generated, files_transferred, etc.)
        """
        if "setup" not in self.state:
            self.state["setup"] = {}

        self.state["setup"][step] = False

        # Remove timestamp if it exists
        if "timestamps" in self.state and step in self.state["timestamps"]:
            del self.state["timestamps"][step]

        self.state["metadata"]["last_updated"] = datetime.now().isoformat()
        self.save()

        # Log the reset action if logger is available
        try:
            from core.logger import get_logger
            logger = get_logger()
            if logger.is_active():
                logger.log_state("reset", step, False)
        except:
            pass  # Logger not available or not initialized


    def is_setup_complete(self) -> bool:
        """
        Check if entire setup is complete

        Returns:
            True if setup is complete
        """
        return self.is_complete("setup_complete")

    def get_progress_percent(self) -> int:
        """
        Get setup progress percentage

        Returns:
            Progress percentage (0-100)
        """
        return 100 if self.is_complete("setup_complete") else 0

    def get_next_step(self) -> Optional[str]:
        """
        Get the next incomplete setup step

        Returns:
            Next step name or None if all complete
        """
        if not self.is_complete("setup_complete"):
            return "Run initial setup (pi-setup/setup.py)"
        return None

    def get_summary(self) -> Dict[str, Any]:
        """
        Get state summary

        Returns:
            Dictionary with progress information
        """
        return {
            "progress_percent": self.get_progress_percent(),
            "next_step": self.get_next_step(),
            "is_complete": self.is_setup_complete(),
            "steps": {
                "setup_complete": self.is_complete("setup_complete")
            },
            "last_updated": self.state.get("metadata", {}).get("last_updated")
        }

    def __repr__(self) -> str:
        """String representation"""
        return f"State(file={self.state_file}, progress={self.get_progress_percent()}%)"
