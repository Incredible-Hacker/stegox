"""Frame difference analysis for video."""

from __future__ import annotations

import imageio.v3 as iio
import numpy as np

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class FrameDiffDetector(Detector):
    id = "video.frame_diff"
    name = "Frame Difference Analysis"
    version = "1.0.0"
    media_type = MediaType.VIDEO
    formats = ("mp4", "avi", "mkv", "mov")
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        frames = []
        for i, frame in enumerate(iio.imiter(target.target_path, plugin="pyav")):
            frames.append(frame.astype(np.int16))
            if i >= 60:
                break
        if len(frames) < 2:
            return DetectorResult(
                detector_id=self.id, detector_version=self.version, score=0.0, confidence=0.0, indicators=[]
            )
        diffs = [float(np.mean(np.abs(frames[i] - frames[i - 1]))) for i in range(1, len(frames))]
        arr = np.array(diffs)
        cv = float(arr.std() / (arr.mean() + 1e-9))
        # High coefficient of variation in frame differences is suspicious
        score = min(1.0, max(0.0, cv - 0.3) * 2.0)
        verdict = "suspicious" if score > 0.5 else "clean"
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
                    metrics={"diff_cv": round(cv, 4), "frames": len(frames)},
                    description="High variance in inter-frame differences can indicate frame-level embedding.",
                )
            ],
        )
