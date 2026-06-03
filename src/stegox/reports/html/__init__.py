"""HTML report renderer.

Produces a self-contained HTML file with embedded CSS and JS so reports
work fully offline.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from stegox.reports.model import Report

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_html(report: Report) -> str:
    """Render ``report`` as a self-contained HTML string."""
    env = _env()
    template = env.get_template("report.html")
    return template.render(
        report=report,
        report_json=report.model_dump_json(exclude_none=True, indent=2),
    )


def write_html(report: Report, path: Path) -> Path:
    """Write the HTML report to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(report), encoding="utf-8")
    return path


__all__ = ["render_html", "write_html"]
