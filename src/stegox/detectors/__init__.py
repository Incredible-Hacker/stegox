"""Detector framework.

Detectors are pluggable callables that inspect a target file and
return a :class:`stegox.core.types.DetectorResult`. The framework
provides:

- :class:`Detector` base class
- :class:`DetectorRegistry` (process-global)
- :class:`ScoringEngine` (weighted aggregation)
- :class:`DetectionEngine` (orchestration)
"""

from stegox.detectors.base import Detector, DetectorContext
from stegox.detectors.engine import DetectionEngine
from stegox.detectors.registry import DetectorRegistry, get_registry
from stegox.detectors.scoring import ScoringConfig, ScoringEngine

__all__ = [
    "DetectionEngine",
    "Detector",
    "DetectorContext",
    "DetectorRegistry",
    "ScoringConfig",
    "ScoringEngine",
    "get_registry",
]
