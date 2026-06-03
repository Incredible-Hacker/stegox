"""Base64 string detector.

Scans for long Base64-like strings inside a file, which can indicate
that an encoded payload has been appended to or embedded in a cover.
"""

from __future__ import annotations

import base64
import re

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

B64_RE = re.compile(rb"[A-Za-z0-9+/]{64,}={0,2}")


class Base64ScanDetector(Detector):
    id = "universal.base64_scan"
    name = "Base64 String Scan"
    version = "1.0.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.6

    def run(self, target: DetectionContext) -> DetectorResult:
        with target.target_path.open("rb") as fh:
            data = fh.read(2 << 20)
        matches = B64_RE.findall(data)
        if not matches:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                notes="no base64-like strings",
            )
        longest = max(matches, key=len)
        score = min(1.0, len(longest) / 4096.0)
        # Verify a sample decodes
        valid = False
        try:
            base64.b64decode(longest[:256] + b"==")
            valid = True
        except Exception:
            valid = False
        if not valid:
            score *= 0.5
        verdict = "suspicious" if score > 0.4 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.6,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"longest_length": len(longest), "count": len(matches), "valid_decode": valid},
                    description="Long Base64-like strings can indicate embedded encoded payloads.",
                )
            ],
        )
