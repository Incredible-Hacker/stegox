"""Analyze orchestration: produce a deep forensic profile of a target."""

from __future__ import annotations

from pathlib import Path

from stegox.core.result import AnalysisResult
from stegox.engine.detect import _ensure_registry, detect
from stegox.media.inspector import MediaInspector


def analyze(target: Path) -> AnalysisResult:
    """Inspect, hash, and detect on ``target``."""
    _ensure_registry()
    inspector = MediaInspector()
    report = inspector.inspect(target)
    scan = detect(target)
    return AnalysisResult(
        target_path=target,
        hashes=scan.hashes,
        media_type=scan.media_type,
        format_name=scan.format_name,
        metadata={
            "width": report.width,
            "height": report.height,
            "sample_rate": report.sample_rate,
            "channels": report.channels,
            "duration_seconds": report.duration_seconds,
            "frame_count": report.frame_count,
            "container_metadata": report.container_metadata,
        },
        metrics={"score": scan.score.value, "classification": scan.score.classification.value},
        score=scan.score,
    )


__all__ = ["analyze"]
