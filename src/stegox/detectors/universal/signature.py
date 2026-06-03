"""Known steganography tool signature detector."""

from __future__ import annotations

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator

# Common tool markers. Each entry is (id, name, signature_bytes, offset, tool_name)
SIGNATURES: tuple[tuple[str, str, bytes, int, str], ...] = (
    ("steg", "Steg header", b"STGX", 0, "stegox"),
    ("openstego", "OpenStego header", b"OPENSTEGO", 0, "openstego"),
    ("steghide", "Steghide magic", b"\x00\x00\x00\x18ftypsteg", 0, "steghide"),
    ("snow", "SNOW whitespace marker", b"Snow", 0, "snow"),
    ("wbstego", "WBstego header", b"\xfe\xfe\xfe\xfe", 0, "wbstego"),
)


class SignatureDetector(Detector):
    id = "universal.signature"
    name = "Known Steganography Signatures"
    version = "1.0.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 1.0

    def run(self, target: DetectionContext) -> DetectorResult:
        indicators = []
        max_score = 0.0
        with target.target_path.open("rb") as fh:
            data = fh.read()
        for sig_id, name, marker, offset, tool in SIGNATURES:
            idx = data.find(marker, offset)
            if idx >= 0:
                score = 1.0
                max_score = max(max_score, score)
                indicators.append(
                    make_indicator(
                        sig_id,
                        name,
                        "malicious",
                        score,
                        metrics={"offset": idx, "tool": tool},
                        description=f"Detected {tool} signature at offset {idx}.",
                    )
                )
        if not indicators:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                notes="no signatures matched",
            )
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=max_score,
            confidence=0.95,
            indicators=indicators,
        )
