"""LSB distribution analysis.

Compares the LSB plane of an image to the expected distribution under
the null hypothesis (uniform). A high divergence suggests sequential
LSB embedding.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class LsbDistributionDetector(Detector):
    id = "image.lsb_distribution"
    name = "LSB Distribution Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp", "tiff", "webp")
    weight = 0.7

    def run(self, target: DetectionContext) -> DetectorResult:
        img = Image.open(target.target_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        lsb = arr & 1
        ones = float(lsb.sum())
        total = float(lsb.size)
        observed_ratio = ones / total
        expected_ratio = 0.5
        deviation = abs(observed_ratio - expected_ratio)
        # Convert to a 0..1 score; saturation around 0.05 deviation
        score = min(1.0, deviation / 0.05)
        confidence = 0.6
        verdict = "suspicious" if score > 0.4 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=confidence,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={
                        "ones_ratio": round(observed_ratio, 6),
                        "deviation": round(deviation, 6),
                        "total_bits": int(total),
                    },
                    description="LSB plane divergence from uniform 0.5 ratio.",
                )
            ],
        )
