"""Unicode anomaly detection for text."""

from __future__ import annotations

import unicodedata

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

# Confusable characters common in homoglyph encoding
CONFUSABLES = {
    "\u0430", "\u0435", "\u043e", "\u0440", "\u0441", "\u0445", "\u0443",
    "\u0456", "\u0458", "\u04bb", "\u0501", "\u051b", "\u051d",
}


class UnicodeAnomalyDetector(Detector):
    id = "text.unicode_anomaly"
    name = "Unicode Anomaly Detection"
    version = "1.0.0"
    media_type = MediaType.TEXT
    formats = ("txt", "md", "docx")
    weight = 0.8

    def run(self, target: DetectionContext) -> DetectorResult:
        text = target.target_path.read_text(encoding="utf-8", errors="ignore")
        total = len(text)
        if total == 0:
            return DetectorResult(
                detector_id=self.id, detector_version=self.version, score=0.0, confidence=0.0, indicators=[]
            )
        confusable = sum(1 for ch in text if ch in CONFUSABLES)
        mixed_scripts = 0
        scripts: set[str] = set()
        for ch in text:
            if not ch.isalpha():
                continue
            try:
                name = unicodedata.name(ch, "")
            except ValueError:
                continue
            if name:
                scripts.add(name.split()[0])
            if len(scripts) > 1:
                mixed_scripts += 1
                break
        ratio = confusable / total
        score = min(1.0, ratio * 10.0)
        if mixed_scripts:
            score = max(score, 0.6)
        verdict = "suspicious" if score > 0.4 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.7,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"confusable_ratio": round(ratio, 6), "mixed_scripts": mixed_scripts},
                    description="High density of confusable characters or mixed scripts suggests homoglyph encoding.",
                )
            ],
        )
