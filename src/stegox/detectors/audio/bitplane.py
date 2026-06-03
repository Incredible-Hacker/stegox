"""Bitplane analysis for audio."""

from __future__ import annotations

import numpy as np
import soundfile

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class AudioBitplaneDetector(Detector):
    id = "audio.bitplane"
    name = "Audio Bitplane Statistics"
    version = "1.0.0"
    media_type = MediaType.AUDIO
    formats = ("wav", "flac")
    weight = 0.7

    def run(self, target: DetectionContext) -> DetectorResult:
        data, _ = soundfile.read(target.target_path, dtype="int16", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1).astype(np.int16)
        flat = data.flatten()
        lsb = flat & 1
        ones_ratio = float(lsb.mean())
        # Block-wise chi-square like test
        block = 4096
        deviations = []
        for i in range(0, len(flat) - block, block):
            chunk = flat[i : i + block]
            r = float((chunk & 1).mean())
            deviations.append(abs(r - 0.5))
        if deviations:
            std = float(np.std(deviations))
            mean = float(np.mean(deviations)) + 1e-9
            cv = std / mean
            score = max(0.0, 1.0 - min(1.0, cv))
        else:
            score = 0.0
        verdict = "suspicious" if (1.0 - score) > 0.6 or abs(ones_ratio - 0.5) > 0.05 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.6,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"ones_ratio": round(ones_ratio, 6)},
                    description="Uniform LSB across sample blocks is a strong LSB signal.",
                )
            ],
        )
