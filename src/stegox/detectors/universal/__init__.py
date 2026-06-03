"""Universal detectors that run on any media type."""

from stegox.detectors.universal.archive_scan import ArchiveScanDetector
from stegox.detectors.universal.base64_scan import Base64ScanDetector
from stegox.detectors.universal.entropy import EntropyDetector
from stegox.detectors.universal.hex_blob import HexBlobDetector
from stegox.detectors.universal.signature import SignatureDetector

__all__ = [
    "ArchiveScanDetector",
    "Base64ScanDetector",
    "EntropyDetector",
    "HexBlobDetector",
    "SignatureDetector",
]
