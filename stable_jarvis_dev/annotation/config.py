"""
Configuration management for Zotero annotation system.

Supports multiple configuration sources with priority:
1. Environment variables: ZOTERO_LIBRARY_ID, ZOTERO_API_KEY, ZOTERO_LIBRARY_TYPE
2. Config file search: ./zotero.json → ./user_info/zotero.json → ~/.config/stable-jarvis-dev/zotero.json
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


class ConfigurationError(Exception):
    """Raised when no valid configuration can be found."""
    pass


@dataclass(frozen=True)
class ZoteroConfig:
    """Immutable Zotero API configuration."""
    library_id: str
    api_key: str
    library_type: str = "user"

    @classmethod
    def from_json(cls, path: Path | str) -> ZoteroConfig:
        """Load configuration from a JSON file."""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(
            library_id=str(data["library_id"]),
            api_key=data["api_key"],
            library_type=data.get("library_type", "user"),
        )

    @classmethod
    def from_env(cls) -> Optional[ZoteroConfig]:
        """
        Load configuration from environment variables.
        
        Required env vars:
            - ZOTERO_LIBRARY_ID
            - ZOTERO_API_KEY
        
        Optional env vars:
            - ZOTERO_LIBRARY_TYPE (default: "user")
        
        Returns:
            ZoteroConfig if all required env vars are set, None otherwise.
        """
        library_id = os.environ.get("ZOTERO_LIBRARY_ID")
        api_key = os.environ.get("ZOTERO_API_KEY")
        
        if library_id and api_key:
            return cls(
                library_id=library_id,
                api_key=api_key,
                library_type=os.environ.get("ZOTERO_LIBRARY_TYPE", "user"),
            )
        return None

    @classmethod
    def from_default(cls) -> ZoteroConfig:
        """
        Load configuration using priority-based discovery.
        
        Priority order:
        1. Environment variables (ZOTERO_LIBRARY_ID, ZOTERO_API_KEY)
        2. Config file search path
        
        Raises:
            ConfigurationError: If no valid configuration is found.
        """
        # Try environment variables first
        config = cls.from_env()
        if config:
            return config
        
        # Search for config file
        search_paths = _get_config_search_paths()
        for path in search_paths:
            if path.exists():
                return cls.from_json(path)
        
        # No config found - raise helpful error
        raise ConfigurationError(
            "Zotero configuration not found.\n\n"
            "Option 1: Set environment variables:\n"
            "  ZOTERO_LIBRARY_ID=your_library_id\n"
            "  ZOTERO_API_KEY=your_api_key\n"
            "  ZOTERO_LIBRARY_TYPE=user  (optional, default: user)\n\n"
            "Option 2: Create a config file at one of these locations:\n"
            + "\n".join(f"  - {p}" for p in search_paths)
            + "\n\nConfig file format (JSON):\n"
            '  {"library_id": "...", "api_key": "...", "library_type": "user"}'
        )


def _get_config_search_paths() -> List[Path]:
    """
    Get the list of paths to search for config files.
    
    Returns paths in priority order (first match wins):
    1. ./zotero.json (current working directory)
    2. ./user_info/zotero.json (relative to cwd)
    3. ~/.config/stable-jarvis-dev/zotero.json (user config dir)
    """
    cwd = Path.cwd()
    home = Path.home()
    
    return [
        cwd / "zotero.json",
        cwd / "user_info" / "zotero.json",
        home / ".config" / "stable-jarvis-dev" / "zotero.json",
    ]


def get_default_config() -> ZoteroConfig:
    """Convenience function to get the default Zotero configuration."""
    return ZoteroConfig.from_default()
