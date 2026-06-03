"""Result objects and adapters used by the engine layer.

The result types are thin dataclasses that modules and detectors return.
The CLI layer is responsible for serializing them into reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stegox.core.constants import MediaType
from stegox.core.types import FileHashes, ScoreReport

__all__ = [
    "AnalysisResult",
    "ExtractResult",
    "HideResult",
    "ScanResult",
]


@dataclass(frozen=True, slots=True)
class HideResult:
    """Outcome of a successful embed."""

    cover_path: Path
    stego_path: Path
    strategy: str
    capacity_bytes: int
    payload_bytes: int
    encrypted: bool
    sha256: str = ""


@dataclass(frozen=True, slots=True)
class ExtractResult:
    """Outcome of a successful extract."""

    stego_path: Path
    out_path: Path
    strategy: str
    payload_bytes: int
    decrypted: bool
    sha256: str = ""


@dataclass(slots=True)
class ScanResult:
    """Aggregated detection result for one target."""

    target_path: Path
    hashes: FileHashes
    media_type: MediaType
    format_name: str
    score: ScoreReport
    detector_results: list[Any] = field(default_factory=list)  # list[DetectorResult]
    duration_ms: float = 0.0


@dataclass(slots=True)
class AnalysisResult:
    """Deep analysis result for one target."""

    target_path: Path
    hashes: FileHashes
    media_type: MediaType
    format_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    score: ScoreReport | None = None
