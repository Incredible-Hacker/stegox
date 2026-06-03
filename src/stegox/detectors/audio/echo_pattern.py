"""Echo pattern detector.

Looks for periodic autocorrelation peaks in the cepstrum, which is
the signature of echo-hiding embedding.
"""

from __future__ import annotations

import numpy as np
import soundfile

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


class EchoPatternDetector(Detector):
    id = "audio.echo_pattern"
    name = "Echo Pattern Detection"
    version = "1.0.0"
    media_type = MediaType.AUDIO
    formats = ("wav", "flac")
    weight = 0.9

    def run(self, target: DetectionContext) -> DetectorResult:
        data, sr = soundfile.read(target.target_path, dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        # Compute real cepstrum via FFT log magnitude IFFT
        n = 1 << 14
        if len(data) < n:
            score = 0.0
        else:
            seg = data[:n]
            mag = np.abs(np.fft.rfft(seg * np.hanning(n)))
            log_mag = np.log(mag + 1e-9)
            cep = np.fft.irfft(log_mag)
            # Look for peaks in the 5-30 ms range
            low = int(0.005 * sr)
            high = int(0.030 * sr)
            peak = float(np.max(np.abs(cep[low:high]))) if high > low else 0.0
            score = min(1.0, peak * 8.0)
        verdict = "suspicious" if score > 0.5 else "clean"
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
                    metrics={"cepstral_peak": round(score, 4)},
                    description="Periodic autocorrelation peak in 5-30 ms range is the echo signature.",
                )
            ],
        )
