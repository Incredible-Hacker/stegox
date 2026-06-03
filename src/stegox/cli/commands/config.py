"""Config CLI subcommand."""

from __future__ import annotations

import json
import sys

import typer

from stegox.core.config import load_config, save_config

app = typer.Typer(help="View and edit StegoX configuration.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.command("show")
def show_cmd(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show the current configuration."""
    cfg = load_config()
    if json_output:
        _emit(cfg.model_dump())
    else:
        typer.echo(json.dumps(cfg.model_dump(), indent=2))


@app.command("get")
def get_cmd(key: str = typer.Argument(...)) -> None:
    """Get a single config value using dotted notation (e.g. ``scoring.low_threshold``)."""
    cfg = load_config()
    data = cfg.model_dump()
    cur: object = data
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            typer.echo(f"unknown key: {key}", err=True)
            raise typer.Exit(code=2)
    typer.echo(json.dumps(cur, indent=2, default=str))


@app.command("set")
def set_cmd(
    key: str = typer.Argument(...),
    value: str = typer.Argument(...),
) -> None:
    """Set a single config value."""
    cfg = load_config()
    data = cfg.model_dump()
    parts = key.split(".")
    cur = data
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = _coerce(value)

    new_cfg = type(cfg).model_validate(data)
    save_config(new_cfg)
    typer.echo(f"{key} = {value}")


def _coerce(value: str) -> object:
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


__all__ = ["app"]
