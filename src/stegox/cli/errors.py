"""CLI error mapping."""

from __future__ import annotations

import sys
import traceback

import typer

from stegox.cli.exitcodes import (
    EXIT_GENERIC,
    EXIT_INTEGRITY,
    EXIT_NOENT,
    EXIT_PERMISSION,
    EXIT_PLUGIN,
    EXIT_TIMEOUT,
    EXIT_UNSUPPORTED,
    EXIT_USAGE,
)
from stegox.core.errors import (
    CapacityError,
    ConfigError,
    IntegrityError,
    PluginError,
    StegoXError,
    TimeoutError_,
    UnsupportedFormatError,
)


def map_error(exc: BaseException) -> int:
    if isinstance(exc, CapacityError):
        return EXIT_UNSUPPORTED
    if isinstance(exc, UnsupportedFormatError):
        return EXIT_UNSUPPORTED
    if isinstance(exc, IntegrityError):
        return EXIT_INTEGRITY
    if isinstance(exc, PluginError):
        return EXIT_PLUGIN
    if isinstance(exc, TimeoutError_):
        return EXIT_TIMEOUT
    if isinstance(exc, ConfigError):
        return EXIT_USAGE
    if isinstance(exc, FileNotFoundError):
        return EXIT_NOENT
    if isinstance(exc, PermissionError):
        return EXIT_PERMISSION
    if isinstance(exc, StegoXError):
        return getattr(exc, "exit_code", EXIT_GENERIC)
    return EXIT_GENERIC


def handle(exc: BaseException) -> int:
    code = map_error(exc)
    typer.echo(f"error: {exc}", err=True)
    if "--debug" in sys.argv:
        traceback.print_exc()
    return code


__all__ = ["handle", "map_error"]
