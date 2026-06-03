"""Filesystem layout helpers.

Centralizes the directory structure used for config, state, cache, and
case files so plugins and CLI commands can locate them consistently.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

APP_NAME: Final[str] = "stegox"
APP_AUTHOR: Final[str] = "StegoX"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def user_config_dir() -> Path:
    """Return the per-user config directory.

    Respects ``XDG_CONFIG_HOME`` on Linux, ``XDG_CONFIG_HOME`` falls back
    to ``~/.config``; on macOS uses ``~/Library/Application Support``;
    on Windows uses ``%APPDATA%``.
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return _ensure_dir(Path(base) / APP_NAME)
    if os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        return _ensure_dir(Path.home() / "Library" / "Application Support" / APP_NAME)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return _ensure_dir(Path(base) / APP_NAME)


def user_state_dir() -> Path:
    """Return the per-user state directory (logs, audit)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return _ensure_dir(Path(base) / APP_NAME)
    if os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        return _ensure_dir(Path.home() / "Library" / "Application Support" / APP_NAME)
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return _ensure_dir(Path(base) / APP_NAME)


def user_cache_dir() -> Path:
    """Return the per-user cache directory (detector result cache)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return _ensure_dir(Path(base) / APP_NAME / "Cache")
    if os.uname().sysname == "Darwin":  # type: ignore[attr-defined]
        return _ensure_dir(Path.home() / "Library" / "Caches" / APP_NAME)
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return _ensure_dir(Path(base) / APP_NAME)


def user_plugin_dir() -> Path:
    """Return the drop-in plugin directory."""
    return _ensure_dir(user_config_dir() / "plugins")


def default_config_path() -> Path:
    """Return the default path of the user config file."""
    return user_config_dir() / "config.yaml"


__all__ = [
    "default_config_path",
    "user_cache_dir",
    "user_config_dir",
    "user_plugin_dir",
    "user_state_dir",
]
