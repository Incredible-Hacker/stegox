"""Tests for the scoring engine."""

from __future__ import annotations

from stegox.core.types import DetectorResult, Indicator
from stegox.detectors.scoring import ScoringConfig, ScoringEngine


CFG = ScoringConfig(weights={"a": 1.0, "b": 0.5})


def _result(detector_id: str, score: float, confidence: float) -> DetectorResult:
    return DetectorResult(
        detector_id=detector_id,
        detector_version="0",
        score=score,
        confidence=confidence,
        indicators=[Indicator(id="x", name="x", verdict="suspicious", score=score, weight=1.0)],
    )


def test_empty_results() -> None:
    s = ScoringEngine(CFG)
    r = s.evaluate([])
    assert r.value == 0


def test_classification_bands() -> None:
    s = ScoringEngine(CFG)
    low = s.evaluate([_result("a", 0.0, 0.1)])
    high = s.evaluate([_result("a", 1.0, 1.0)])
    assert low.classification.value == "low"
    assert high.classification.value in {"medium", "high"}
