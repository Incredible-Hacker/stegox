"""Report CLI subcommand."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="Render reports from JSON results.")


@app.command("render")
def render_cmd(
    input: Path = typer.Option(..., "--input", help="Input JSON file."),
    fmt: str = typer.Option("console", "--format", help="console|json|html"),
    output: Path = typer.Option(..., "--out"),
) -> None:
    """Render a report file in the requested format."""
    from stegox.reports.console import render_console
    from stegox.reports.html import write_html
    from stegox.reports.json_render import parse_json

    report = parse_json(input.read_text(encoding="utf-8"))
    if fmt == "console":
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_console(report), encoding="utf-8")
    elif fmt == "json":
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    elif fmt == "html":
        write_html(report, output)
    else:
        typer.echo(f"unknown format: {fmt}", err=True)
        raise typer.Exit(code=2)


@app.command("template")
def template_cmd(
    action: str = typer.Argument("list"),
    name: str = typer.Argument("", help="Template name (for export)."),
    out: Path = typer.Option(Path("template.html"), "--out"),
) -> None:
    """List or export report templates."""
    if action == "list":
        typer.echo("- report.html")
    elif action == "export":
        from importlib import resources

        template = resources.files("stegox.reports.html.templates").joinpath("report.html")
        out.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
        typer.echo(f"exported to {out}")
    else:
        typer.echo(f"unknown action: {action}", err=True)
        raise typer.Exit(code=2)


__all__ = ["app"]
