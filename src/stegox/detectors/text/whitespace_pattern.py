"""Whitespace pattern analysis for text."""

from __future__ import annotations

import re

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

TRAILING_RE = re.compile(r"[ \t]+(?=\n|$)")


class WhitespacePatternDetector(Detector):
    id = "text.whitespace_pattern"
    name = "Whitespace Pattern Analysis"
    version = "1.0.0"
    media_type = MediaType.TEXT
    formats = ("txt", "md", "docx")
    weight = 0.6

    def run(self, target: DetectionContext) -> DetectorResult:
        text = target.target_path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        if not lines:
            return DetectorResult(
                detector_id=self.id, detector_version=self.version, score=0.0, confidence=0.0, indicators=[]
            )
        trailing_counts = [len(TRAILING_RE.findall(line)) for line in lines]
        nonzero = [c for c in trailing_counts if c > 0]
        if not nonzero:
            score = 0.0
            total_trailing = 0
        else:
            total_trailing = sum(trailing_counts)
            # Score saturates around 100 trailing characters
            score = min(1.0, total_trailing / 100.0)
        verdict = "suspicious" if total_trailing > 20 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.5,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"trailing_total": total_trailing, "lines": len(lines)},
                    description="Many trailing spaces or tabs suggest whitespace encoding.",
                )
            ],
        )
