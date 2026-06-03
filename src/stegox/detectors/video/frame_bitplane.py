"""Per-frame bitplane analysis."""

from __future__ import annotations

import imageio.v3 as iio
import numpy as np

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class FrameBitplaneDetector(Detector):
    id = "video.frame_bitplane"
    name = "Per-Frame Bitplane Analysis"
    version = "1.0.0"
    media_type = MediaType.VIDEO
    formats = ("mp4", "avi", "mkv", "mov")
    weight = 0.6

    def run(self, target: DetectionContext) -> DetectorResult:
        scores = []
        for i, frame in enumerate(iio.imiter(target.target_path, plugin="pyav")):
            lsb = frame & 1
            r = float(lsb.mean())
            scores.append(min(1.0, abs(r - 0.5) / 0.05))
            if i >= 30:
                break
        if not scores:
            return DetectorResult(
                detector_id=self.id, detector_version=self.version, score=0.0, confidence=0.0, indicators=[]
            )
        mean_score = float(np.mean(scores))
        verdict = "suspicious" if mean_score > 0.4 else "clean"
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
                    metrics={"mean_score": round(mean_score, 4), "frames": len(scores)},
                    description="Mean LSB deviation across sampled frames.",
                )
            ],
        )
