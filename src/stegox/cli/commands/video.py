"""Video CLI subcommand."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from stegox.core.errors import StegoXError
from stegox.engine import extract as engine_extract
from stegox.engine import hide as engine_hide
from stegox.modules.video import list_strategies

app = typer.Typer(help="Video hide, extract, detect, and analyze.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.command("hide")
def hide_cmd(
    cover: Path = typer.Option(..., "--cover"),
    payload: Path = typer.Option(..., "--payload"),
    out: Path = typer.Option(..., "--out"),
    strategy: str = typer.Option("frame-lsb", "--strategy"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        data = payload.read_bytes()
        result = engine_hide(cover, data, strategy=strategy, stego=out, media_type="video")
        if json_output:
            _emit({"stego": str(result.stego_path), "payload_bytes": result.payload_bytes})
        else:
            typer.echo(f"wrote {result.stego_path}")
    except StegoXError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@app.command("extract")
def extract_cmd(
    stego: Path = typer.Option(..., "--stego"),
    out: Path = typer.Option(..., "--out"),
    strategy: str = typer.Option("frame-lsb", "--strategy"),
    payload_bytes: int = typer.Option(..., "--payload-bytes"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    try:
        data = engine_extract(stego, strategy=strategy, payload_bytes=payload_bytes, out=out, media_type="video")
        if json_output:
            _emit({"recovered_bytes": len(data), "out": str(out)})
        else:
            typer.echo(f"wrote {len(data)} bytes to {out}")
    except StegoXError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=exc.exit_code) from exc


@app.command("detect")
def detect_cmd(
    target: Path = typer.Option(..., "--target"),
    detectors: str | None = typer.Option(None, "--detectors"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    from stegox.engine.detect import detect as engine_detect
    only = [d.strip() for d in detectors.split(",")] if detectors else None
    scan = engine_detect(target, only=only)
    if json_output:
        _emit(scan.score.model_dump())
    else:
        typer.echo(f"{target}: score={scan.score.value} ({scan.score.classification.value})")


@app.command("list-strategies")
def list_strategies_cmd() -> None:
    typer.echo(json.dumps(list_strategies(), indent=2))


@app.command("analyze")
def analyze_cmd(
    target: Path = typer.Option(..., "--target"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    from stegox.engine.analyze import analyze
    from stegox.reports.console import render_console
    from stegox.reports.model import build_report
    result = analyze(target)
    report = build_report(analysis=result)
    if json_output:
        _emit(report.model_dump())
    else:
        typer.echo(render_console(report))


__all__ = ["app"]
