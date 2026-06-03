"""Confidence scoring engine.

The scoring engine is deterministic: given a list of
:class:`DetectorResult` and a :class:`ScoringConfig`, it returns a
:class:`ScoreReport` with a 0-100 score and a risk classification.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from stegox.core.constants import RiskClass
from stegox.core.types import DetectorResult, Indicator, ScoreReport


@dataclass(frozen=True, slots=True)
class ScoringConfig:
    weights: dict[str, float]
    low_threshold: int = 30
    high_threshold: int = 60


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _classify(value: int, low: int, high: int) -> RiskClass:
    if value <= low:
        return RiskClass.LOW
    if value <= high:
        return RiskClass.MEDIUM
    return RiskClass.HIGH


class ScoringEngine:
    """Stateless scorer."""

    def __init__(self, config: ScoringConfig) -> None:
        self.config = config

    def evaluate(self, results: Iterable[DetectorResult]) -> ScoreReport:
        contributions: dict[str, float] = {}
        raw_indicators: list[Indicator] = []
        total_raw = 0.0
        total_possible = 0.0
        for res in results:
            weight = self.config.weights.get(res.detector_id, 0.0)
            if weight <= 0.0:
                continue
            total_possible += weight * 1.0 * 1.0  # max indicator multiplier is 1.5
            confidence = _clamp(res.confidence, 0.0, 1.0)
            multiplier = self._indicator_multiplier(res.indicators)
            contribution = weight * confidence * multiplier
            total_raw += contribution
            contributions[res.detector_id] = round(contribution, 4)
            raw_indicators.extend(res.indicators)
        if total_possible <= 0.0:
            value = 0
            rationale = "no applicable detectors"
        else:
            normalized = (total_raw / total_possible) * 100.0
            value = round(_clamp(normalized, 0.0, 100.0))
            rationale = self._build_rationale(contributions, value)
        return ScoreReport(
            value=value,
            classification=_classify(value, self.config.low_threshold, self.config.high_threshold),
            rationale=rationale,
            detector_contributions=contributions,
            raw_indicators=raw_indicators,
        )

    @staticmethod
    def _indicator_multiplier(indicators: list[Indicator]) -> float:
        if not indicators:
            return 0.0
        return sum(i.weight for i in indicators) / len(indicators)

    @staticmethod
    def _build_rationale(contributions: dict[str, float], value: int) -> str:
        if not contributions:
            return "no contributions"
        top = sorted(contributions.items(), key=lambda kv: kv[1], reverse=True)[:3]
        names = ", ".join(f"{name}={score:.2f}" for name, score in top)
        return f"score={value} from top contributors: {names}"


__all__ = ["ScoringConfig", "ScoringEngine"]
