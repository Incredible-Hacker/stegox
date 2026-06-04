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


def _clean_result(detector_id: str, confidence: float = 0.9) -> DetectorResult:
    """A 'clean' verdict (score=0) with the given confidence — used to
    prove that confidence alone does not inflate the score."""
    return DetectorResult(
        detector_id=detector_id,
        detector_version="0",
        score=0.0,
        confidence=confidence,
        indicators=[
            Indicator(id="x", name="x", verdict="clean", score=0.0, weight=1.0),
        ],
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


def test_clean_with_high_confidence_stays_low() -> None:
    """Regression: a clean file (score=0) reported with high confidence
    must NOT push the aggregate score above 0. The previous formula used
    ``confidence`` as the verdict and produced a 32/100 false positive on
    a plain text fixture.
    """
    s = ScoringEngine(CFG)
    r = s.evaluate([_clean_result("a", confidence=0.9), _clean_result("b", confidence=0.7)])
    assert r.value == 0
    assert r.classification.value == "low"


def test_indicator_score_drives_contribution() -> None:
    """Even with high confidence, a low-score indicator must keep the
    detector's contribution near zero."""
    s = ScoringEngine(CFG)
    r = DetectorResult(
        detector_id="a",
        detector_version="0",
        score=0.05,
        confidence=0.95,
        indicators=[Indicator(id="x", name="x", verdict="clean", score=0.05, weight=1.0)],
    )
    report = s.evaluate([r])
    assert report.value < 5


def test_indicator_weights_combine_correctly() -> None:
    """Two indicators, one strong and one weak, should produce a
    weighted-average indicator score."""
    s = ScoringEngine(CFG)
    res = DetectorResult(
        detector_id="a",
        detector_version="0",
        score=0.5,
        confidence=1.0,
        indicators=[
            Indicator(id="x", name="x", verdict="suspicious", score=1.0, weight=1.0),
            Indicator(id="y", name="y", verdict="clean", score=0.0, weight=1.0),
        ],
    )
    report = s.evaluate([res])
    # indicator_score = (1*1 + 0*1) / 2 = 0.5
    # contribution     = 1.0 * 0.5 * 1.0 * 0.5 = 0.25
    # value            = 0.25 / 1.0 * 100 = 25
    assert 20 <= report.value <= 30
    assert report.detector_contributions["a"] == round(0.25, 4)
