"""Noise floor analysis for audio.

A natural recording has a relatively flat noise floor at the highest
frequencies. LSB embedding perturbs the floor.
"""

from __future__ import annotations

import numpy as np
import soundfile

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class NoiseFloorDetector(Detector):
    id = "audio.noise_floor"
    name = "Noise Floor Analysis"
    version = "1.0.0"
    media_type = MediaType.AUDIO
    formats = ("wav", "flac")
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        data, sr = soundfile.read(target.target_path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        n = min(len(data), 1 << 16)
        data = data[:n]
        spec = np.abs(np.fft.rfft(data))
        freqs = np.fft.rfftfreq(n, 1.0 / sr)
        # Look at top 10% of spectrum
        cutoff = int(len(freqs) * 0.9)
        top = spec[cutoff:]
        if top.size == 0:
            score = 0.0
        else:
            std = float(np.std(top))
            mean = float(np.mean(top)) + 1e-9
            cv = std / mean
            score = min(1.0, cv * 4.0)  # rough heuristic
        verdict = "suspicious" if score > 0.6 else "clean"
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
                    metrics={"top_band_cv": round(score, 4)},
                    description="High coefficient of variation in the high band is suspicious.",
                )
            ],
        )
