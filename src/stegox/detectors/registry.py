"""Detector registry.

A process-global lookup table that maps ``detector_id`` strings to
:class:`Detector` instances. Built-in detectors are registered when the
respective submodules are imported. Plugins can register additional
detectors via the entry point system.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from stegox.detectors.base import Detector


class DetectorRegistry:
    """Mutable registry of detectors keyed by ``Detector.id``."""

    _items: dict[str, Detector] = {}  # noqa: RUF012 - class-level mutable state is intentional

    @classmethod
    def register(cls, detector: Detector, *, replace: bool = False) -> None:
        if not detector.id:
            raise ValueError("detector.id must be non-empty")
        if not replace and detector.id in cls._items:
            raise ValueError(f"detector already registered: {detector.id}")
        cls._items[detector.id] = detector

    @classmethod
    def unregister(cls, detector_id: str) -> None:
        cls._items.pop(detector_id, None)

    @classmethod
    def get(cls, detector_id: str) -> Detector | None:
        return cls._items.get(detector_id)

    @classmethod
    def all(cls) -> list[Detector]:
        return list(cls._items.values())

    @classmethod
    def ids(cls) -> list[str]:
        return list(cls._items.keys())

    @classmethod
    def filter(cls, *, media_type: str | None = None,
               formats: Iterable[str] | None = None) -> list[Detector]:
        out: list[Detector] = []
        fmt_set = set(formats) if formats else None
        for det in cls._items.values():
            if media_type and det.media_type.value != media_type and det.media_type.value != "universal":
                continue
            if fmt_set is not None and det.formats and not (set(det.formats) & fmt_set):
                continue
            out.append(det)
        return out

    @classmethod
    def clear(cls) -> None:
        cls._items.clear()

    def __iter__(self) -> Iterator[Detector]:  # pragma: no cover
        return iter(self._items.values())


def get_registry() -> DetectorRegistry:
    """Return the singleton registry (class acts as singleton)."""
    return DetectorRegistry


def register_builtin() -> None:
    """Register the detectors shipped with StegoX."""
    from stegox.detectors.audio import (
        AudioBitplaneDetector,
        EchoPatternDetector,
        EntropyWindowDetector,
        NoiseFloorDetector,
        SpectrogramDetector,
    )
    from stegox.detectors.image import (
        ChiSquareDetector,
        DCTAnalysisDetector,
        EntropyImageDetector,
        HistogramDetector,
        LsbDistributionDetector,
        RSAnalysisDetector,
    )
    from stegox.detectors.text import (
        UnicodeAnomalyDetector,
        WhitespacePatternDetector,
        ZeroWidthScanDetector,
    )
    from stegox.detectors.universal import (
        ArchiveScanDetector,
        Base64ScanDetector,
        EntropyDetector,
        HexBlobDetector,
        SignatureDetector,
    )
    from stegox.detectors.video import (
        FrameBitplaneDetector,
        FrameDiffDetector,
        KeyframeDetector,
        TemporalEntropyDetector,
    )

    for cls in (
        LsbDistributionDetector,
        ChiSquareDetector,
        RSAnalysisDetector,
        HistogramDetector,
        EntropyImageDetector,
        DCTAnalysisDetector,
        SpectrogramDetector,
        NoiseFloorDetector,
        EntropyWindowDetector,
        EchoPatternDetector,
        AudioBitplaneDetector,
        FrameDiffDetector,
        TemporalEntropyDetector,
        KeyframeDetector,
        FrameBitplaneDetector,
        ZeroWidthScanDetector,
        UnicodeAnomalyDetector,
        WhitespacePatternDetector,
        EntropyDetector,
        SignatureDetector,
        Base64ScanDetector,
        HexBlobDetector,
        ArchiveScanDetector,
    ):
        DetectorRegistry.register(cls())


__all__ = ["DetectorRegistry", "get_registry", "register_builtin"]
