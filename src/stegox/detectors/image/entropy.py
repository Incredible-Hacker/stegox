"""Per-channel entropy analysis for images."""

from __future__ import annotations

import numpy as np
from PIL import Image

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _shannon_entropy(data: np.ndarray) -> float:
    if data.size == 0:
        return 0.0
    _, counts = np.unique(data, return_counts=True)
    probs = counts / counts.sum()
    return float(-(probs * np.log2(probs + 1e-12)).sum())


class EntropyImageDetector(Detector):
    id = "image.entropy"
    name = "Image Entropy Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp", "jpeg", "tiff", "webp")
    weight = 0.4

    def run(self, target: DetectionContext) -> DetectorResult:
        img = Image.open(target.target_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        per_channel = []
        for ch in range(arr.shape[2]):
            plane = arr[:, :, ch]
            h = _shannon_entropy(plane)
            per_channel.append(round(h, 4))
        joint = _shannon_entropy(arr.flatten())
        # Heuristic: entropy very close to 8 across channels with low variance
        # is suspicious.
        max_h = max(per_channel) if per_channel else 0.0
        variance = float(np.var(per_channel))
        score = 0.0
        if max_h > 7.95 and variance < 0.05:
            score = 0.6
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
                    metrics={"per_channel": per_channel, "joint": round(joint, 4)},
                    description="Very high per-channel entropy with low variance is a weak signal.",
                )
            ],
        )
