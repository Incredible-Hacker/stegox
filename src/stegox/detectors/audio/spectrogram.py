"""Spectrogram-based detector.

Computes a magnitude spectrogram and looks for high-frequency energy
that is inconsistent with the noise floor.
"""

from __future__ import annotations

import numpy as np
import soundfile

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class SpectrogramDetector(Detector):
    id = "audio.spectrogram"
    name = "Spectrogram Analysis"
    version = "1.0.0"
    media_type = MediaType.AUDIO
    formats = ("wav", "flac", "ogg", "mp3")
    weight = 0.6

    def run(self, target: DetectionContext) -> DetectorResult:
        data, sr = soundfile.read(target.target_path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        spec = np.abs(np.fft.rfft(data, n=min(len(data), 1 << 14)))
        spec_db = 20 * np.log10(spec + 1e-9)
        # Compare mid band (4-12 kHz) energy to upper band (>14 kHz)
        freqs = np.fft.rfftfreq(min(len(data), 1 << 14), 1.0 / sr)
        mid = spec_db[(freqs > 4_000) & (freqs <= 12_000)]
        high = spec_db[freqs > 14_000]
        if mid.size == 0 or high.size == 0:
            score = 0.0
        else:
            mid_mean = float(mid.mean())
            high_mean = float(high.mean())
            gap = mid_mean - high_mean
            # For natural music, gap is large. For spectrogram messages,
            # high band is boosted, so the gap shrinks.
            score = max(0.0, 1.0 - min(1.0, gap / 20.0))
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
                    metrics={"mid_db": round(mid_mean, 2) if mid.size else None,
                             "high_db": round(high_mean, 2) if high.size else None},
                    description="Compares mid- and high-band spectrogram energy.",
                )
            ],
        )
