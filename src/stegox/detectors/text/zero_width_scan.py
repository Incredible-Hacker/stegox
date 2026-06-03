"""Zero-width character scan for text."""

from __future__ import annotations

import re

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

ZW_RE = re.compile("[\u200b\u200c\u200d\ufeff]")


class ZeroWidthScanDetector(Detector):
    id = "text.zero_width_scan"
    name = "Zero-Width Character Scan"
    version = "1.0.0"
    media_type = MediaType.TEXT
    formats = ("txt", "md", "docx")
    weight = 1.0

    def run(self, target: DetectionContext) -> DetectorResult:
        text = target.target_path.read_text(encoding="utf-8", errors="ignore")
        matches = ZW_RE.findall(text)
        count = len(matches)
        # Score saturates around 50 zero-width characters
        score = min(1.0, count / 50.0)
        verdict = "suspicious" if count > 5 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.9,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"count": count},
                    description="Presence of zero-width characters is a strong steganalysis signal.",
                )
            ],
        )
