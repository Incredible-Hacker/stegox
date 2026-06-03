"""Report data model and builder.

Reports are Pydantic models so they can be validated, serialized, and
documented with a stable JSON schema.
"""

from __future__ import annotations

import getpass
import os
import socket
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from stegox.core.constants import RiskClass
from stegox.core.result import AnalysisResult, ScanResult
from stegox.version import __version__


class TargetInfo(BaseModel):
    path: str
    sha256: str
    md5: str
    sha1: str
    size: int
    media_type: str
    format: str


class ScoreInfo(BaseModel):
    value: int = Field(ge=0, le=100)
    classification: RiskClass
    rationale: str
    detector_contributions: dict[str, float] = Field(default_factory=dict)


class EvidenceInfo(BaseModel):
    kind: str
    offset: int
    length: int
    description: str = ""


class ToolInfo(BaseModel):
    name: str = "stegox"
    version: str
    commit: str = "unknown"
    operator: str = ""
    host: str = ""


class ScanWindow(BaseModel):
    started_at: str
    finished_at: str
    duration_ms: float


class IndicatorInfo(BaseModel):
    id: str
    detector_id: str
    name: str
    verdict: str
    score: float
    weight: float = 1.0
    metrics: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


class RecommendationInfo(BaseModel):
    text: str
    rationale: str = ""


class Report(BaseModel):
    """A complete forensic report for a single target."""

    report_version: str = "1.0"
    tool: ToolInfo
    target: TargetInfo
    scan: ScanWindow
    score: ScoreInfo
    indicators: list[IndicatorInfo] = Field(default_factory=list)
    evidence: list[EvidenceInfo] = Field(default_factory=list)
    recommendations: list[RecommendationInfo] = Field(default_factory=list)
    detector_results: list[dict[str, Any]] = Field(default_factory=list)


class ReportBuilder:
    """Helper that accumulates scan output into a :class:`Report`."""

    def __init__(self) -> None:
        self.report = Report(
            tool=ToolInfo(
                version=__version__,
                operator=_safe_operator(),
                host=_safe_host(),
            ),
            target=TargetInfo(path="", sha256="", md5="", sha1="", size=0, media_type="", format=""),
            scan=ScanWindow(started_at="", finished_at="", duration_ms=0.0),
            score=ScoreInfo(value=0, classification=RiskClass.LOW, rationale=""),
        )

    def with_scan(self, scan: ScanResult) -> ReportBuilder:
        self.report.target = TargetInfo(
            path=str(scan.target_path),
            sha256=scan.hashes.sha256,
            md5=scan.hashes.md5,
            sha1=scan.hashes.sha1,
            size=scan.hashes.size,
            media_type=scan.media_type.value,
            format=scan.format_name,
        )
        self.report.score = ScoreInfo(
            value=scan.score.value,
            classification=scan.score.classification,
            rationale=scan.score.rationale,
            detector_contributions=scan.score.detector_contributions,
        )
        now = datetime.now(tz=timezone.utc).isoformat()
        self.report.scan = ScanWindow(
            started_at=now,
            finished_at=now,
            duration_ms=scan.duration_ms,
        )
        for r in scan.detector_results:
            self.report.detector_results.append(
                {
                    "id": r.detector_id,
                    "version": r.detector_version,
                    "score": r.score,
                    "confidence": r.confidence,
                    "notes": r.notes,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
            )
            for ind in r.indicators:
                self.report.indicators.append(
                    IndicatorInfo(
                        id=ind.id,
                        detector_id=r.detector_id,
                        name=ind.name,
                        verdict=ind.verdict,
                        score=ind.score,
                        weight=ind.weight,
                        metrics=ind.metrics,
                        description=ind.description,
                    )
                )
        return self

    def with_analysis(self, analysis: AnalysisResult) -> ReportBuilder:
        self.report.target = TargetInfo(
            path=str(analysis.target_path),
            sha256=analysis.hashes.sha256,
            md5=analysis.hashes.md5,
            sha1=analysis.hashes.sha1,
            size=analysis.hashes.size,
            media_type=analysis.media_type.value,
            format=analysis.format_name,
        )
        if analysis.score is not None:
            self.report.score = ScoreInfo(
                value=analysis.score.value,
                classification=analysis.score.classification,
                rationale=analysis.score.rationale,
                detector_contributions=analysis.score.detector_contributions,
            )
        self.report.evidence.append(
            EvidenceInfo(
                kind="metadata",
                offset=0,
                length=0,
                description=str(analysis.metadata),
            )
        )
        return self

    def add_recommendation(self, text: str, rationale: str = "") -> ReportBuilder:
        self.report.recommendations.append(RecommendationInfo(text=text, rationale=rationale))
        return self

    def build(self) -> Report:
        return self.report


def build_report(scan: ScanResult | None = None, analysis: AnalysisResult | None = None) -> Report:
    builder = ReportBuilder()
    if scan is not None:
        builder.with_scan(scan)
    if analysis is not None:
        builder.with_analysis(analysis)
    builder.add_recommendation("Review the report and follow organizational DFIR policy.")
    return builder.build()


def _safe_operator() -> str:
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", os.environ.get("USERNAME", "unknown"))


def _safe_host() -> str:
    try:
        return socket.gethostname()
    except Exception:
        return "unknown"


__all__ = ["IndicatorInfo", "RecommendationInfo", "Report", "ReportBuilder", "build_report"]
