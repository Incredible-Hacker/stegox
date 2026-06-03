"""Temporal entropy analysis for video."""

from __future__ import annotations

import imageio.v3 as iio
import numpy as np

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _entropy(arr: np.ndarray) -> float:
    _, counts = np.unique(arr, return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log2(p + 1e-12)).sum())


class TemporalEntropyDetector(Detector):
    id = "video.temporal_entropy"
    name = "Temporal Entropy Analysis"
    version = "1.0.0"
    media_type = MediaType.VIDEO
    formats = ("mp4", "avi", "mkv", "mov")
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        ents = []
        for i, frame in enumerate(iio.imiter(target.target_path, plugin="pyav")):
            ents.append(_entropy(frame.flatten()[::97]))  # subsample for speed
            if i >= 30:
                break
        if len(ents) < 2:
            score = 0.0
        else:
            arr = np.array(ents)
            std = float(arr.std())
            mean = float(arr.mean()) + 1e-9
            cv = std / mean
            score = min(1.0, cv * 2.0)
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
                    metrics={"entropy_cv": round(score, 4)},
                    description="Temporal entropy variance is a weak video steganalysis signal.",
                )
            ],
        )
