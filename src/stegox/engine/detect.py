"""Detect orchestration: run all applicable detectors and score."""

from __future__ import annotations

from pathlib import Path

from stegox.core.constants import RiskClass
from stegox.core.logging import get_logger
from stegox.core.result import ScanResult
from stegox.core.types import ScoreReport
from stegox.detectors.engine import DetectionEngine
from stegox.detectors.registry import DetectorRegistry, register_builtin

log = get_logger("engine.detect")


def _ensure_registry() -> None:
    if not DetectorRegistry.ids():
        register_builtin()


def detect(target: Path, *, only: list[str] | None = None, jobs: int = 1) -> ScanResult:
    """Run the full detector pipeline against ``target``."""
    _ensure_registry()
    engine = DetectionEngine()
    out = engine.run(target, only=only, jobs=jobs)
    classification = RiskClass(out.score_classification)
    score = ScoreReport(
        value=out.score_value,
        classification=classification,
        rationale=out.rationale,
        detector_contributions={r.detector_id: r.score for r in out.detector_results},
        raw_indicators=[i for r in out.detector_results for i in r.indicators],
    )
    return ScanResult(
        target_path=target,
        hashes=out.context.hashes,
        media_type=out.context.media_type,
        format_name=out.context.format_name,
        score=score,
        detector_results=out.detector_results,
        duration_ms=sum(r.duration_ms for r in out.detector_results),
    )


__all__ = ["detect"]
