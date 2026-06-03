"""Global Shannon entropy detector."""

from __future__ import annotations

import math
from collections import Counter

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator


def _shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values() if c)


class EntropyDetector(Detector):
    id = "universal.entropy"
    name = "Shannon Entropy"
    version = "1.0.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.4

    def run(self, target: DetectionContext) -> DetectorResult:
        with target.target_path.open("rb") as fh:
            data = fh.read(1 << 20)  # 1 MiB
        h = _shannon_entropy(data)
        # High entropy (close to 8) is a weak signal. Use it sparingly.
        score = max(0.0, (h - 7.5) / 0.5) if h > 7.5 else 0.0
        verdict = "suspicious" if score > 0.5 else "clean"
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=score,
            confidence=0.3,
            indicators=[
                make_indicator(
                    self.id,
                    self.name,
                    verdict,
                    score,
                    metrics={"entropy": round(h, 4)},
                    description="High Shannon entropy is consistent with encrypted or compressed payloads.",
                )
            ],
        )
