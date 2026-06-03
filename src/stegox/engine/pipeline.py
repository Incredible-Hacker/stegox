"""End-to-end pipeline: hide + extract + detect.

Used by integration tests and by the example scripts to verify that
the toolkit functions correctly across modules.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stegox.core.logging import get_logger
from stegox.engine.detect import detect
from stegox.engine.extract import extract
from stegox.engine.hide import hide

log = get_logger("engine.pipeline")


@dataclass(slots=True)
class PipelineReport:
    cover_path: Path
    stego_path: Path
    payload_sha256: str
    extracted_sha256: str
    match: bool
    detection: dict[str, Any]


def run_pipeline(
    cover: Path,
    payload: bytes,
    *,
    media_type: str,
    strategy: str,
    password: str | None = None,
    out_dir: Path | None = None,
) -> PipelineReport:
    """Hide, extract, and detect in one shot. Used in tests and examples."""
    out_dir = out_dir or cover.parent
    stego = out_dir / f"{cover.stem}.stegox{cover.suffix}"
    hide(cover, payload, strategy=strategy, password=password, stego=stego, media_type=media_type)
    recovered = extract(stego, strategy=strategy, password=password, media_type=media_type)
    scan = detect(stego)
    payload_hash = hashlib.sha256(payload).hexdigest()
    extracted_hash = hashlib.sha256(recovered).hexdigest()
    return PipelineReport(
        cover_path=cover,
        stego_path=stego,
        payload_sha256=payload_hash,
        extracted_sha256=extracted_hash,
        match=(payload_hash == extracted_hash),
        detection={
            "score": scan.score.value,
            "classification": scan.score.classification.value,
            "rationale": scan.score.rationale,
        },
    )


__all__ = ["PipelineReport", "run_pipeline"]
