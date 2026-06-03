"""Version CLI subcommand."""

from __future__ import annotations

import json
import sys

import typer

from stegox import __version__

app = typer.Typer(help="Version information.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.callback()
def version_callback() -> None:
    pass


@app.command("show")
def show(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show the StegoX version."""
    if json_output:
        _emit({"version": __version__})
    else:
        typer.echo(f"stegox {__version__}")


__all__ = ["app"]
