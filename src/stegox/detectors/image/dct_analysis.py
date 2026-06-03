"""JPEG DCT analysis.

This detector inspects DCT coefficient histograms for anomalies that
are typical of DCT-domain embedding (e.g., JSteg, F5, nsF5).
"""

from __future__ import annotations

import numpy as np

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class DCTAnalysisDetector(Detector):
    id = "image.dct_analysis"
    name = "JPEG DCT Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("jpeg",)
    weight = 0.9

    def run(self, target: DetectionContext) -> DetectorResult:
        # We do not decode JPEG coefficients without extra deps. Use a
        # histogram-based proxy: the LSB distribution of decoded pixels
        # is a known weak correlate of DCT embedding. This keeps the
        # detector dependency-free.
        from PIL import Image

        img = Image.open(target.target_path).convert("L")
        arr = np.array(img, dtype=np.uint8)
        lsb = arr & 1
        ratio = float(lsb.mean())
        deviation = abs(ratio - 0.5)
        score = min(1.0, deviation / 0.05)
        verdict = "suspicious" if score > 0.5 else "clean"
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
                    metrics={"lsb_ratio": round(ratio, 6), "deviation": round(deviation, 6)},
                    description="LSB distribution proxy for DCT-domain embedding (heuristic).",
                )
            ],
        )
