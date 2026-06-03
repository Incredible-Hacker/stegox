"""Case CLI subcommand."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from stegox.forensics.case import init_case, load_case
from stegox.forensics.chain_of_custody import ChainOfCustody

app = typer.Typer(help="DFIR case management.")


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, indent=2, default=str))
    sys.stdout.write("\n")


@app.command("init")
def init_cmd(
    path: Path = typer.Argument(..., help="Case directory to create."),
    operator: str = typer.Option("analyst", "--operator"),
    description: str = typer.Option("", "--description"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Initialize a new case directory."""
    case = init_case(path, operator=operator, description=description)
    if json_output:
        _emit({"case_root": str(case.root), "manifest": case.manifest})
    else:
        typer.echo(f"case initialized at {case.root}")


@app.command("add")
def add_cmd(
    path: Path = typer.Argument(..., help="Existing case directory."),
    file: Path = typer.Option(..., "--file"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Add a file to a case (copies into inputs/)."""
    case = load_case(path)
    case_file = case.add_file(file)
    case.save()
    if json_output:
        _emit({"file": case_file.path, "sha256": case_file.sha256})
    else:
        typer.echo(f"added {case_file.path} ({case_file.sha256})")


@app.command("scan")
def scan_cmd(
    path: Path = typer.Argument(..., help="Case directory."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Run detection on every file in inputs/."""
    from stegox.engine.detect import detect as engine_detect
    from stegox.reports.model import build_report

    case = load_case(path)
    reports = []
    for case_file in case.files:
        target = path / case_file.path
        scan = engine_detect(target)
        report = build_report(scan=scan)
        out = path / "reports" / f"{target.name}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report.model_dump(), indent=2, default=str), encoding="utf-8")
        reports.append(str(out))
    if json_output:
        _emit({"reports": reports})
    else:
        for r in reports:
            typer.echo(r)


@app.command("report")
def report_cmd(
    path: Path = typer.Argument(..., help="Case directory."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show a summary of the case."""
    case = load_case(path)
    summary = {
        "case_root": str(case.root),
        "manifest": case.manifest,
        "file_count": len(case.files),
        "files": [
            {"path": f.path, "sha256": f.sha256, "size": f.size} for f in case.files
        ],
    }
    if json_output:
        _emit(summary)
    else:
        typer.echo(json.dumps(summary, indent=2))


@app.command("seal")
def seal_cmd(
    path: Path = typer.Argument(..., help="Case directory."),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Compute a final manifest hash and append a custody event."""
    import hashlib

    case = load_case(path)
    h = hashlib.sha256()
    for case_file in case.files:
        h.update(case_file.sha256.encode("utf-8"))
    final = h.hexdigest()
    custody = ChainOfCustody(path / "logs" / "custody.jsonl")
    custody.append(
        ChainOfCustody.now_event(
            operator=case.manifest.get("case", {}).get("operator", "unknown"),
            action="seal",
            target="manifest",
            sha256=final,
            args={"files": len(case.files)},
        )
    )
    if json_output:
        _emit({"seal_sha256": final})
    else:
        typer.echo(f"sealed: {final}")


__all__ = ["app"]
