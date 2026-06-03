"""JSON report renderer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stegox.reports.model import Report


def render_json(report: Report, *, indent: int = 2) -> str:
    """Render ``report`` as a stable, sorted JSON document."""
    return report.model_dump_json(indent=indent, exclude_none=True)


def write_json(report: Report, path: Path) -> Path:
    """Write the JSON report to ``path``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(report), encoding="utf-8")
    return path


def parse_json(data: str | bytes) -> Report:
    """Parse a JSON document produced by :func:`render_json`."""
    if isinstance(data, bytes):
        data = data.decode("utf-8")
    obj: dict[str, Any] = json.loads(data)
    return Report.model_validate(obj)


__all__ = ["parse_json", "render_json", "write_json"]
