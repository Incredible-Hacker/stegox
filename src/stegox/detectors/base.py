"""Base classes for StegoX detectors.

A detector is a stateless object that, given a target, returns a
:class:`DetectorResult`. The framework provides a base class with
sensible defaults so plugin authors only override what they need.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult, Indicator


class Detector(ABC):
    """Abstract base class for all detectors.

    Subclasses must set class-level metadata and implement :meth:`run`.
    """

    id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    version: ClassVar[str] = "0.1.0"
    media_type: ClassVar[MediaType] = MediaType.UNIVERSAL
    formats: ClassVar[tuple[str, ...]] = ()
    weight: ClassVar[float] = 0.5
    requires: ClassVar[tuple[str, ...]] = ()

    def applicable(self, target: DetectionContext) -> bool:
        """Return True if this detector can process ``target``."""
        if self.formats and target.format_name not in self.formats:
            return False
        return not (
            self.media_type != MediaType.UNIVERSAL and target.media_type != self.media_type
        )

    @abstractmethod
    def run(self, target: DetectionContext) -> DetectorResult:
        """Inspect ``target`` and return a :class:`DetectorResult`."""

    def explain(self) -> str:
        """Return a short human-readable description of this detector."""
        return f"{self.name} ({self.id}) v{self.version}"


class DetectorContext(DetectionContext):
    """Backwards-compatible alias.

    The class shares its memory layout with :class:`DetectionContext`
    while exposing the more familiar ``DetectorContext`` name to
    plugin authors.
    """


def make_indicator(
    indicator_id: str,
    name: str,
    verdict: str,
    score: float,
    *,
    weight: float = 1.0,
    metrics: dict[str, Any] | None = None,
    description: str = "",
) -> Indicator:
    """Helper to build a single Indicator with defaults."""
    return Indicator(
        id=indicator_id,
        name=name,
        verdict=verdict,
        score=max(0.0, min(1.0, score)),
        weight=max(0.0, min(1.5, weight)),
        metrics=metrics or {},
        description=description,
    )


def empty_result(detector_id: str, version: str = "0.1.0") -> DetectorResult:
    """Convenience constructor for a clean DetectorResult."""
    return DetectorResult(
        detector_id=detector_id,
        detector_version=version,
        score=0.0,
        confidence=0.0,
        indicators=[],
        notes="not applicable",
    )


__all__ = ["Detector", "DetectorContext", "empty_result", "make_indicator"]
