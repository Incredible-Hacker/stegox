"""Console report renderer.

Uses the ``rich`` library to produce color-coded tables and panels.
Falls back to plain text when ``rich`` is unavailable.
"""

from __future__ import annotations

import io
from typing import TextIO

from stegox.reports.model import Report

_COLOR_MAP = {
    "low": "green",
    "medium": "yellow",
    "high": "red",
}


def render_console(report: Report, out: TextIO | None = None) -> str:
    """Render ``report`` to ``out`` (defaults to a StringIO). Returns the text."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
    except ImportError:
        return _render_plain(report)

    buf = out if out is not None else io.StringIO()
    console = Console(file=buf, force_terminal=False, color_system="standard", width=100)
    color = _COLOR_MAP.get(report.score.classification.value, "white")

    console.print(Panel.fit(f"[bold cyan]StegoX {report.tool.version}[/] - Forensic Report",
                            border_style="cyan"))
    console.print(f"[bold]Target:[/] {report.target.path}")
    console.print(f"[bold]Format:[/] {report.target.format}  [bold]Media:[/] {report.target.media_type}")
    console.print(f"[bold]SHA256:[/] {report.target.sha256}")
    console.print(f"[bold]Size:[/] {report.target.size} bytes")
    console.print()

    score_text = f"Score: [bold {color}]{report.score.value}/100[/] - {report.score.classification.value.upper()}"
    console.print(Panel(score_text, border_style=color))
    console.print(f"[dim]Rationale:[/] {report.score.rationale}")
    console.print()

    if report.indicators:
        table = Table(title="Indicators", show_lines=False)
        table.add_column("Detector", style="cyan")
        table.add_column("Indicator", style="magenta")
        table.add_column("Verdict")
        table.add_column("Score", justify="right")
        for ind in report.indicators:
            verdict_color = _COLOR_MAP.get(
                "high" if ind.verdict == "malicious" else ("medium" if ind.verdict == "suspicious" else "low"),
                "white",
            )
            table.add_row(
                ind.detector_id,
                ind.name,
                f"[{verdict_color}]{ind.verdict}[/]",
                f"{ind.score:.2f}",
            )
        console.print(table)
        console.print()

    if report.detector_results:
        dtable = Table(title="Detector Results", show_lines=False)
        dtable.add_column("Detector", style="cyan")
        dtable.add_column("Score", justify="right")
        dtable.add_column("Confidence", justify="right")
        dtable.add_column("Duration (ms)", justify="right")
        dtable.add_column("Notes")
        for r in report.detector_results:
            dtable.add_row(
                r["id"],
                f"{r['score']:.2f}",
                f"{r['confidence']:.2f}",
                f"{r['duration_ms']:.1f}",
                r.get("notes") or r.get("error") or "",
            )
        console.print(dtable)
        console.print()

    if report.evidence:
        etable = Table(title="Evidence", show_lines=False)
        etable.add_column("Kind")
        etable.add_column("Offset", justify="right")
        etable.add_column("Length", justify="right")
        etable.add_column("Description")
        for ev in report.evidence:
            etable.add_row(ev.kind, str(ev.offset), str(ev.length), ev.description[:80])
        console.print(etable)
        console.print()

    if report.recommendations:
        for rec in report.recommendations:
            console.print(f"[bold]•[/] {rec.text}")
        console.print()

    if isinstance(buf, io.StringIO):
        return buf.getvalue()
    return ""


def _render_plain(report: Report) -> str:
    """Fallback renderer used when rich is not available."""
    lines: list[str] = []
    lines.append(f"StegoX {report.tool.version} - Forensic Report")
    lines.append("=" * 40)
    lines.append(f"Target: {report.target.path}")
    lines.append(f"Format: {report.target.format}  Media: {report.target.media_type}")
    lines.append(f"SHA256: {report.target.sha256}")
    lines.append(f"Score: {report.score.value}/100 - {report.score.classification.value.upper()}")
    lines.append(f"Rationale: {report.score.rationale}")
    lines.append("")
    if report.indicators:
        lines.append("Indicators:")
        for ind in report.indicators:
            lines.append(f"  - [{ind.detector_id}] {ind.name}: {ind.verdict} ({ind.score:.2f})")
    return "\n".join(lines) + "\n"


__all__ = ["render_console"]
