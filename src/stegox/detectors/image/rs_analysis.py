"""Regular-Singular (RS) analysis.

Implementation of Fridrich, Goljan, Du's RS-analysis for LSB
embedding. The detector estimates the embedding rate by measuring
discriminant statistics on the LSB plane.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _discrimination(arr: np.ndarray) -> float:
    """Sum of absolute differences between horizontally adjacent pixels."""
    if arr.ndim == 3:
        d = np.abs(arr[:, 1:, :] - arr[:, :-1, :]).sum()
    else:
        d = np.abs(arr[:, 1:] - arr[:, :-1]).sum()
    return float(d)


def _flip_lsb(group: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = group.copy()
    return out ^ (mask & 1)


def _regular(group: np.ndarray, mask: np.ndarray) -> np.ndarray:
    flipped = _flip_lsb(group, mask)
    return _discrimination(flipped) > _discrimination(group)


def _singular(group: np.ndarray, mask: np.ndarray) -> np.ndarray:
    flipped = _flip_lsb(group, mask)
    return _discrimination(flipped) < _discrimination(group)


def _unusable(group: np.ndarray, mask: np.ndarray) -> np.ndarray:
    flipped = _flip_lsb(group, mask)
    return _discrimination(flipped) == _discrimination(group)


class RSAnalysisDetector(Detector):
    id = "image.rs_analysis"
    name = "RS Analysis"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp", "tiff")
    weight = 1.0

    def run(self, target: DetectionContext) -> DetectorResult:
        img = Image.open(target.target_path)
        if img.mode != "RGB":
            img = img.convert("RGB")
        arr = np.array(img, dtype=np.uint8)
        _, w, _ = arr.shape
        # Work on channel 0 for speed; the indicator is a single number
        plane = arr[:, :, 0]
        groups = [plane[:, i : i + 4] for i in range(0, w - 4, 4)]
        mask = np.array([1, 0, 1, 0], dtype=np.uint8)
        r_count = s_count = u_count = 0
        total = 0
        for g in groups:
            if g.shape[1] < 2:
                continue
            if _regular(g, mask):
                r_count += 1
            elif _singular(g, mask):
                s_count += 1
            else:
                u_count += 1
            total += 1
        if total == 0:
            return DetectorResult(detector_id=self.id, detector_version=self.version, score=0.0, confidence=0.0, indicators=[])
        rs_ratio = (r_count - s_count) / max(1, total)
        score = min(1.0, abs(rs_ratio) / 2.0)
        verdict = "suspicious" if score > 0.3 else "clean"
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
                    metrics={"rs_ratio": round(rs_ratio, 6), "groups": int(total)},
                    description="Higher RS ratio indicates higher LSB embedding rate.",
                )
            ],
        )
