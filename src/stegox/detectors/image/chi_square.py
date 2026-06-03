"""Chi-square analysis on LSB-substituted pairs.

The classic Westfeld-Pfitzmann chi-square test counts pairs of colors
(2k, 2k+1) across color channels and compares the observed count to
the expected count. Sequential LSB embedding drives the count toward
equality, lowering the chi-square statistic.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
from PIL import Image

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _expected_count(observed_pair: int) -> float:
    return (observed_pair + observed_pair + 1) / 2.0


class ChiSquareDetector(Detector):
    id = "image.chi_square"
    name = "Chi-Square Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp", "tiff")
    weight = 1.0

    def run(self, target: DetectionContext) -> DetectorResult:
        img = Image.open(target.target_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        chi_stats: list[float] = []
        for ch in range(arr.shape[2]):
            flat = arr[:, :, ch].flatten()
            counts = Counter(int(v) for v in flat.tolist())
            chi = self._chi_square_one_channel(counts)
            chi_stats.append(chi)
        mean_chi = float(np.mean(chi_stats)) if chi_stats else 0.0
        score = self._chi_to_score(mean_chi)
        verdict = "suspicious" if score > 0.5 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.7,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"mean_chi": round(mean_chi, 4), "per_channel": [round(x, 4) for x in chi_stats]},
                    description="Lower chi-square values indicate LSB embedding.",
                )
            ],
        )

    @staticmethod
    def _chi_square_one_channel(counts: Counter) -> float:
        total = 0.0
        chi = 0.0
        for k in range(0, 256, 2):
            obs_pair = counts.get(k, 0) + counts.get(k + 1, 0)
            exp_pair = _expected_count(obs_pair)
            total += obs_pair
            if exp_pair == 0:
                continue
            chi += (counts.get(k, 0) - exp_pair) ** 2 / exp_pair
            chi += (counts.get(k + 1, 0) - exp_pair) ** 2 / exp_pair
        return chi

    @staticmethod
    def _chi_to_score(chi: float) -> float:
        # The test reports 0 for strong embedding and very large for natural images.
        if chi <= 0:
            return 1.0
        # Empirically, natural images yield chi > 100; embedded images often < 30
        score = 1.0 - (min(chi, 200.0) / 200.0)
        return float(max(0.0, min(1.0, score)))
