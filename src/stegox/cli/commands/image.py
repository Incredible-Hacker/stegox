"""Image CLI subcommand."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from stegox.core.errors import StegoXError
from stegox.core.logging import get_logger
from stegox.engine import extract as engine_extract
from stegox.engine import hide as engine_hide
from stegox.modules.image import list_strategies

app = typer.Typer(help="Image hide, extract, detect, and analyze.")
log = get_logger("cli.image")


def _read_password(value: str | None) -> str | None:
    if value is None:
        return None
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.exists():
            raise typer.BadParameter(f"password file not found: {path}")
        return path.read_text(encoding="utf-8").rstrip("\n")
    return value


def _emit_json(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.command("hide")
def hide_cmd(
    cover: Path = typer.Option(..., "--cover", help="Cover image."),
    payload: Path = typer.Option(..., "--payload", help="Payload file."),
    out: Path = typer.Option(..., "--out", help="Stego image output path."),
    strategy: str = typer.Option("lsb", "--strategy", help="Embed strategy id."),
    password: str | None = typer.Option(None, "--password", help="Password (or @file)."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON on stdout."),
) -> None:
    """Embed a payload into an image."""
    try:
        payload_bytes = payload.read_bytes()
        pw = _read_password(password)
        result = engine_hide(cover, payload_bytes, strategy=strategy, password=pw, stego=out, media_type="image")
        if json_output:
            _emit_json({
                "cover": str(result.cover_path),
                "stego": str(result.stego_path),
                "strategy": result.strategy,
                "capacity_bytes": result.capacity_bytes,
                "payload_bytes": result.payload_bytes,
                "encrypted": result.encrypted,
            })
        else:
            typer.echo(f"wrote {result.stego_path} ({result.payload_bytes} bytes, encrypted={result.encrypted})")
    except StegoXError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@app.command("extract")
def extract_cmd(
    stego: Path = typer.Option(..., "--stego", help="Stego image path."),
    out: Path = typer.Option(..., "--out", help="Output path for recovered payload."),
    strategy: str = typer.Option("lsb", "--strategy", help="Extract strategy id."),
    payload_bytes: int | None = typer.Option(None, "--payload-bytes", help="Payload size (for LSB extract)."),
    password: str | None = typer.Option(None, "--password", help="Password (or @file)."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON on stdout."),
) -> None:
    """Recover a payload from an image."""
    try:
        pw = _read_password(password)
        data = engine_extract(
            stego,
            strategy=strategy,
            password=pw,
            payload_bytes=payload_bytes,
            out=out,
            media_type="image",
        )
        if json_output:
            _emit_json({"recovered_bytes": len(data), "out": str(out)})
        else:
            typer.echo(f"wrote {len(data)} bytes to {out}")
    except StegoXError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@app.command("detect")
def detect_cmd(
    target: Path = typer.Option(..., "--target", help="Image to analyze."),
    detectors: str | None = typer.Option(None, "--detectors", help="Comma-separated detector ids."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
) -> None:
    """Run image detectors against a target."""
    from stegox.engine.detect import detect as engine_detect

    only = [d.strip() for d in detectors.split(",")] if detectors else None
    scan = engine_detect(target, only=only)
    if json_output:
        _emit_json(scan.score.model_dump())
    else:
        typer.echo(f"{target}: score={scan.score.value} ({scan.score.classification.value})")
        typer.echo(scan.score.rationale)


@app.command("list-strategies")
def list_strategies_cmd() -> None:
    """List available image strategies."""
    typer.echo(json.dumps(list_strategies(), indent=2))


@app.command("analyze")
def analyze_cmd(
    target: Path = typer.Option(..., "--target", help="Image to analyze."),
    json_output: bool = typer.Option(False, "--json", help="Emit JSON."),
) -> None:
    """Produce a deep analysis report for an image."""
    from stegox.engine.analyze import analyze
    from stegox.reports.model import build_report

    result = analyze(target)
    report = build_report(analysis=result)
    if json_output:
        _emit_json(report.model_dump())
    else:
        from stegox.reports.console import render_console
        typer.echo(render_console(report))


__all__ = ["app"]
