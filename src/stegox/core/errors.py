"""StegoX error hierarchy.

All exceptions raised by StegoX inherit from :class:`StegoXError`. This
makes catching library errors straightforward for the CLI and for plugin
authors.
"""

from __future__ import annotations


class StegoXError(Exception):
    """Base class for all StegoX-originated errors.

    Subclasses should set ``exit_code`` to a value documented in
    :mod:`stegox.cli.exitcodes` so the CLI can map errors to exit codes.
    """

    exit_code: int = 1

    def __init__(self, message: str = "", *, context: dict[str, object] | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.context: dict[str, object] = context or {}


class CapacityError(StegoXError):
    """The cover medium cannot hold the requested payload."""

    exit_code: int = 4


class UnsupportedFormatError(StegoXError):
    """The input file is not a format supported by the requested operation."""

    exit_code: int = 4


class IntegrityError(StegoXError):
    """AEAD authentication failed or framing checksum mismatch."""

    exit_code: int = 5


class PluginError(StegoXError):
    """A plugin failed to load, register, or execute."""

    exit_code: int = 7


class TimeoutError_(StegoXError):  # noqa: N801, N818 - shadow stdlib intentionally
    """An operation exceeded its time budget."""

    exit_code: int = 8


class ConfigError(StegoXError):
    """A configuration value is invalid or missing."""

    exit_code: int = 2


__all__ = [
    "CapacityError",
    "ConfigError",
    "IntegrityError",
    "PluginError",
    "StegoXError",
    "TimeoutError_",
    "UnsupportedFormatError",
]
