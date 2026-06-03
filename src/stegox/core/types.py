"""Core data structures shared across modules, detectors, and reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from stegox.core.constants import MediaType, RiskClass


@dataclass(frozen=True, slots=True)
class FileHashes:
    """Cryptographic hashes of an evidence file.

    ``md5`` and ``sha1`` are included for legacy DFIR compatibility; ``sha256``
    is the primary identifier used in case files and reports.
    """

    md5: str
    sha1: str
    sha256: str
    sha512: str | None = None
    size: int = 0

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "md5": self.md5,
            "sha1": self.sha1,
            "sha256": self.sha256,
            "size": self.size,
        }
        if self.sha512 is not None:
            out["sha512"] = self.sha512
        return out


@dataclass(frozen=True, slots=True)
class DetectionContext:
    """Per-detection-call state passed to detectors.

    The context bundles the file location, precomputed hashes, the
    cancellation token, and resource limits.
    """

    target_path: Path
    hashes: FileHashes
    media_type: MediaType
    format_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    cancel_check: Callable[[], bool] | None = None
    max_seconds: float = 60.0


@dataclass(frozen=True, slots=True)
class Indicator:
    """A single, structured piece of evidence produced by a detector."""

    id: str
    name: str
    verdict: str  # "clean" | "suspicious" | "malicious"
    score: float  # 0.0 - 1.0 (detector's own certainty)
    weight: float = 1.0  # 0.0 - 1.5
    metrics: dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass(frozen=True, slots=True)
class DetectorResult:
    """The output of a single detector invocation."""

    detector_id: str
    detector_version: str
    score: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    indicators: list[Indicator] = field(default_factory=list)
    notes: str = ""
    error: str | None = None
    duration_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class HideResult:
    """The outcome of an embedder invocation."""

    cover_path: Path
    stego_path: Path
    strategy: str
    capacity_bytes: int
    payload_bytes: int
    encrypted: bool
    sha256: str


@dataclass(frozen=True, slots=True)
class MediaTarget:
    """A loaded, identified media file ready for processing."""

    path: Path
    media_type: MediaType
    format_name: str
    hashes: FileHashes
    metadata: dict[str, Any] = field(default_factory=dict)


class ScoreReport(BaseModel):
    """Aggregated detection verdict for a single target."""

    model_config = {"frozen": True}

    value: int = Field(ge=0, le=100)
    classification: RiskClass
    rationale: str
    detector_contributions: dict[str, float] = Field(default_factory=dict)
    raw_indicators: list[Indicator] = Field(default_factory=list)


# Late import to avoid runtime cost when not needed
from collections.abc import Callable  # noqa: E402
