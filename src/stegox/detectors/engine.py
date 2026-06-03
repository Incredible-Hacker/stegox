"""Detection engine: orchestrates detector execution.

The engine builds a :class:`DetectionContext` for a target, runs every
applicable detector, and aggregates the results via the scoring
engine. It supports serial and (optionally) parallel execution.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from stegox.core.config import Config
from stegox.core.logging import get_logger
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector
from stegox.detectors.registry import DetectorRegistry
from stegox.detectors.scoring import ScoringConfig, ScoringEngine
from stegox.media.identifier import FileIdentifier
from stegox.media.loader import MediaLoader

log = get_logger("detectors.engine")


@dataclass(slots=True)
class DetectionOutput:
    context: DetectionContext
    detector_results: list[DetectorResult]
    score_value: int
    score_classification: str
    rationale: str


class DetectionEngine:
    """Run all applicable detectors against a target."""

    def __init__(
        self,
        config: Config | None = None,
        registry: DetectorRegistry | None = None,
    ) -> None:
        self.config = config or Config()
        self.registry = registry or DetectorRegistry
        self.scoring = ScoringEngine(
            ScoringConfig(
                weights=dict(self.config.scoring.weights),
                low_threshold=self.config.scoring.low_threshold,
                high_threshold=self.config.scoring.high_threshold,
            )
        )
        self._loader = MediaLoader(FileIdentifier())

    def run(
        self,
        target: Path,
        *,
        only: Sequence[str] | None = None,
        jobs: int = 1,
    ) -> DetectionOutput:
        media = self._loader.load(target)
        ctx = DetectionContext(
            target_path=target,
            hashes=media.hashes,
            media_type=media.media_type,
            format_name=media.format_name,
        )
        detectors = self._select_detectors(media.media_type.value, media.format_name, only)
        results: list[DetectorResult] = []
        if jobs > 1:
            with ThreadPoolExecutor(max_workers=jobs) as pool:
                futures = {pool.submit(self._safe_run, d, ctx): d for d in detectors}
                for fut in as_completed(futures):
                    results.append(fut.result())
        else:
            for d in detectors:
                results.append(self._safe_run(d, ctx))
        report = self.scoring.evaluate(results)
        return DetectionOutput(
            context=ctx,
            detector_results=results,
            score_value=report.value,
            score_classification=report.classification.value,
            rationale=report.rationale,
        )

    def _select_detectors(
        self,
        media_type: str,
        format_name: str,
        only: Sequence[str] | None,
    ) -> list[Detector]:
        detectors = self.registry.filter(media_type=media_type, formats=[format_name])
        if only:
            wanted = set(only)
            detectors = [d for d in detectors if d.id in wanted]
        return detectors

    @staticmethod
    def _safe_run(detector: Detector, ctx: DetectionContext) -> DetectorResult:
        start = time.monotonic()
        try:
            res = detector.run(ctx)
        except Exception as exc:
            log.warning("detector %s failed: %s", detector.id, exc)
            res = DetectorResult(
                detector_id=detector.id,
                detector_version=detector.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                error=str(exc),
            )
        duration = (time.monotonic() - start) * 1000.0
        return DetectorResult(
            detector_id=res.detector_id,
            detector_version=res.detector_version,
            score=res.score,
            confidence=res.confidence,
            indicators=res.indicators,
            notes=res.notes,
            error=res.error,
            duration_ms=duration,
        )


__all__ = ["DetectionEngine", "DetectionOutput"]
