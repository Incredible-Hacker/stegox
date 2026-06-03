"""Keyframe bitplane analysis for video.

Examines every I-frame (default: every 5th frame) and checks the LSB
plane for uniformity.
"""

from __future__ import annotations

import imageio.v3 as iio
import numpy as np

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class KeyframeDetector(Detector):
    id = "video.keyframe"
    name = "Keyframe Bitplane Analysis"
    version = "1.0.0"
    media_type = MediaType.VIDEO
    formats = ("mp4", "avi", "mkv", "mov")
    weight = 0.6

    def run(self, target: DetectionContext) -> DetectorResult:
        ratios = []
        for i, frame in enumerate(iio.imiter(target.target_path, plugin="pyav")):
            if i % 5 != 0:
                continue
            lsb = frame & 1
            ratios.append(float(lsb.mean()))
            if len(ratios) >= 12:
                break
        if not ratios:
            score = 0.0
        else:
            arr = np.array(ratios)
            mean_dev = float(np.mean(np.abs(arr - 0.5)))
            score = min(1.0, mean_dev / 0.05)
        verdict = "suspicious" if score > 0.4 else "clean"
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
                    metrics={"keyframe_lsb_deviation": round(score, 4)},
                    description="LSB deviation from 0.5 across keyframes is a weak steganalysis signal.",
                )
            ],
        )
