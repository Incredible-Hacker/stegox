"""Plugin CLI subcommand."""

from __future__ import annotations

import json
import sys

import typer

from stegox.plugins.manager import PluginManager

app = typer.Typer(help="Plugin discovery and information.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.command("list")
def list_cmd(json_output: bool = typer.Option(False, "--json")) -> None:
    """List loaded plugins."""
    pm = PluginManager()
    pm.discover()
    items = [
        {"name": p.name, "version": p.version, "origin": p.origin, "permissions": list(p.spec.permissions)}
        for p in pm.list()
    ]
    if json_output:
        _emit({"plugins": items})
    else:
        for p in items:
            typer.echo(f"{p['name']} v{p['version']} ({p['origin']})")


@app.command("info")
def info_cmd(
    name: str = typer.Argument(...),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show details for one plugin."""
    pm = PluginManager()
    pm.discover()
    for p in pm.list():
        if p.name == name:
            data = {
                "name": p.name,
                "version": p.version,
                "author": p.spec.author,
                "license": p.spec.license,
                "description": p.spec.description,
                "stability": p.spec.stability,
                "permissions": list(p.spec.permissions),
                "detectors": [d.__name__ for d in p.spec.detectors],
                "origin": p.origin,
            }
            if json_output:
                _emit(data)
            else:
                typer.echo(json.dumps(data, indent=2))
            return
    typer.echo(f"plugin not found: {name}", err=True)
    raise typer.Exit(code=1)


__all__ = ["app"]
