"""Top-level detect command."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from stegox.detectors.registry import DetectorRegistry, register_builtin
from stegox.reports.model import build_report

app = typer.Typer(help="Run detectors against a target.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


def _ensure_registry() -> None:
    if not DetectorRegistry.ids():
        register_builtin()


@app.command("list-detectors")
def list_detectors() -> None:
    """List every registered detector."""
    _ensure_registry()
    rows = []
    for det in DetectorRegistry.all():
        rows.append({
            "id": det.id,
            "name": det.name,
            "media_type": det.media_type.value,
            "formats": list(det.formats),
            "weight": det.weight,
            "version": det.version,
        })
    typer.echo(json.dumps(rows, indent=2))


@app.command("all")
def all_cmd(
    target: Path = typer.Option(..., "--target"),
    detectors: str | None = typer.Option(None, "--detectors"),
    json_output: bool = typer.Option(False, "--json"),
    jobs: int = typer.Option(1, "--jobs"),
) -> None:
    """Run all applicable detectors against ``target``."""
    from stegox.engine.detect import detect as engine_detect
    only = [d.strip() for d in detectors.split(",")] if detectors else None
    scan = engine_detect(target, only=only, jobs=jobs)
    report = build_report(scan=scan)
    if json_output:
        _emit(report.model_dump())
    else:
        from stegox.reports.console import render_console
        typer.echo(render_console(report))


@app.callback()
def detect_callback() -> None:
    """Run a single detector or all detectors."""
    pass


def run(target: Path, *, only: list[str] | None = None, json_output: bool = False) -> None:
    """Programmatic entry point used by tests."""
    from stegox.engine.detect import detect as engine_detect
    scan = engine_detect(target, only=only)
    report = build_report(scan=scan)
    if json_output:
        _emit(report.model_dump())
    else:
        from stegox.reports.console import render_console
        typer.echo(render_console(report))


__all__ = ["app", "run"]
