"""Sliding-window entropy for audio."""

from __future__ import annotations

import numpy as np
import soundfile

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _entropy(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    _, counts = np.unique(samples, return_counts=True)
    p = counts / counts.sum()
    return float(-(p * np.log2(p + 1e-12)).sum())


class EntropyWindowDetector(Detector):
    id = "audio.entropy_window"
    name = "Entropy Window Scan"
    version = "1.0.0"
    media_type = MediaType.AUDIO
    formats = ("wav", "flac")
    weight = 0.4

    def run(self, target: DetectionContext) -> DetectorResult:
        data, sr = soundfile.read(target.target_path, dtype="int16", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1).astype(np.int16)
        window = sr  # 1 second
        if len(data) < window * 2:
            score = 0.0
        else:
            entropies = []
            for start in range(0, len(data) - window, window):
                entropies.append(_entropy(data[start : start + window]))
            entropies_arr = np.array(entropies)
            spread = float(entropies_arr.std())
            score = min(1.0, spread / 0.5)
        verdict = "suspicious" if score > 0.7 else "clean"
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
                    metrics={"entropy_spread": round(score, 4)},
                    description="Large entropy spread across windows suggests embedded noise.",
                )
            ],
        )
