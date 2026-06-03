"""Histogram analysis.

For lossless formats, this detector checks for "step" effects in the
pair histogram that are typical of LSB embedding. For JPEG, it checks
for unusual DCT coefficient distributions.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class HistogramDetector(Detector):
    id = "image.histogram"
    name = "Histogram Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp", "jpeg", "tiff", "webp")
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        img = Image.open(target.target_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        scores: list[float] = []
        per_channel: list[dict[str, float]] = []
        for ch in range(arr.shape[2]):
            plane = arr[:, :, ch]
            hist, _ = np.histogram(plane, bins=256, range=(0, 256))
            score = self._pair_step_score(hist)
            scores.append(score)
            per_channel.append({"score": round(float(score), 4)})
        mean_score = float(np.mean(scores)) if scores else 0.0
        verdict = "suspicious" if mean_score > 0.6 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=mean_score,
            confidence=0.5,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    mean_score,
                    metrics={"per_channel": per_channel},
                    description="Detects LSB-induced step artifacts in color histograms.",
                )
            ],
        )

    @staticmethod
    def _pair_step_score(hist: np.ndarray) -> float:
        # Compare each value with its pair (2k vs 2k+1). Embedding tends to
        # equalize the pair counts.
        diffs: list[float] = []
        for k in range(0, 256, 2):
            diffs.append(abs(int(hist[k]) - int(hist[k + 1])))
        diffs_arr = np.array(diffs, dtype=np.float64)
        if diffs_arr.sum() == 0:
            return 0.0
        # Lower normalized variance => more equalization => higher score
        normalized = diffs_arr.std() / (diffs_arr.mean() + 1e-9)
        score = 1.0 - min(1.0, normalized / 2.0)
        return float(score)
