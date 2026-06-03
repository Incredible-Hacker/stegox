"""Embedded archive detector.

Looks for ZIP, RAR, 7z, and other archive magic bytes that are not
expected at the start of common media files.
"""

from __future__ import annotations

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

ARCHIVE_MARKERS: tuple[bytes, ...] = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
    b"Rar!\x1a\x07\x00",
    b"7z\xbc\xaf\x27\x1c",
    b"\x1f\x8b\x08",  # gzip
    b"BZh",  # bzip2
)


class ArchiveScanDetector(Detector):
    id = "universal.archive_scan"
    name = "Embedded Archive Scan"
    version = "1.0.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.9

    def run(self, target: DetectionContext) -> DetectorResult:
        with target.target_path.open("rb") as fh:
            data = fh.read()
        indicators = []
        max_score = 0.0
        for marker in ARCHIVE_MARKERS:
            # Find all but exclude an archive at offset 0 if the file IS an archive
            start = 1 if target.format_name in {"zip", "rar", "7z"} else 0
            idx = data.find(marker, start)
            if idx >= 0:
                max_score = max(max_score, 1.0)
                indicators.append(
                    make_indicator(
                        "archive",
                        f"Archive marker {marker[:4].hex()}",
                        "suspicious",
                        1.0,
                        metrics={"offset": idx, "marker": marker.hex()},
                        description=f"Archive signature found at offset {idx}.",
                    )
                )
        if not indicators:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                notes="no archive signatures",
            )
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=max_score,
            confidence=0.9,
            indicators=indicators,
        )
