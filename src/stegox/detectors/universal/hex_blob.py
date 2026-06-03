"""Hex blob detector."""

from __future__ import annotations

import re

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

HEX_RE = re.compile(rb"(?:[0-9a-fA-F]{2}){32,}")


class HexBlobDetector(Detector):
    id = "universal.hex_blob"
    name = "Hex Blob Detector"
    version = "1.0.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        with target.target_path.open("rb") as fh:
            data = fh.read(2 << 20)
        matches = HEX_RE.findall(data)
        if not matches:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                notes="no hex blobs",
            )
        longest = max(matches, key=len)
        score = min(1.0, len(longest) / 1024.0)
        verdict = "suspicious" if score > 0.4 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.4,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"longest_length": len(longest), "count": len(matches)},
                    description="Long hex blobs can indicate encoded binary payloads.",
                )
            ],
        )
