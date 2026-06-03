"""Cross-cutting types, errors, configuration, and logging."""

from stegox.core.constants import MediaType, RiskClass, Strategy
from stegox.core.errors import (
    CapacityError,
    IntegrityError,
    PluginError,
    StegoXError,
    UnsupportedFormatError,
)
from stegox.core.result import HideResult
from stegox.core.types import (
    DetectionContext,
    DetectorResult,
    FileHashes,
    Indicator,
    MediaTarget,
    ScoreReport,
)

__all__ = [
    "CapacityError",
    "DetectionContext",
    "DetectorResult",
    "FileHashes",
    "HideResult",
    "Indicator",
    "IntegrityError",
    "MediaTarget",
    "MediaType",
    "PluginError",
    "RiskClass",
    "ScoreReport",
    "StegoXError",
    "Strategy",
    "UnsupportedFormatError",
]
