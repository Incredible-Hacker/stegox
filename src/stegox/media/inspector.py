"""Media inspector.

A read-only inspection pass that returns basic dimensions, sample
rates, and container-level metadata. The inspector is used by the
``analyze`` operations and by metadata detectors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stegox.core.constants import MediaType
from stegox.core.errors import UnsupportedFormatError
from stegox.media.identifier import FileIdentifier


@dataclass(slots=True)
class InspectionReport:
    media_type: MediaType
    format_name: str
    width: int | None = None
    height: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    duration_seconds: float | None = None
    frame_count: int | None = None
    container_metadata: dict[str, Any] = field(default_factory=dict)


class MediaInspector:
    """Lightweight inspection across media types."""

    def __init__(self, identifier: FileIdentifier | None = None) -> None:
        self.identifier = identifier or FileIdentifier()

    def inspect(self, path: Path) -> InspectionReport:
        ident = self.identifier.identify(path)
        report = InspectionReport(media_type=ident.media_type, format_name=ident.format_name)
        try:
            if ident.media_type == MediaType.IMAGE:
                self._inspect_image(path, report)
            elif ident.media_type == MediaType.AUDIO:
                self._inspect_audio(path, ident.format_name, report)
            elif ident.media_type == MediaType.VIDEO:
                self._inspect_video(path, ident.format_name, report)
        except UnsupportedFormatError:
            raise
        except Exception as exc:
            report.container_metadata["inspector_error"] = str(exc)
        return report

    def _inspect_image(self, path: Path, report: InspectionReport) -> None:
        from PIL import Image

        with Image.open(path) as img:
            report.width, report.height = img.size
            report.container_metadata["mode"] = img.mode
            report.container_metadata["format"] = img.format

    def _inspect_audio(self, path: Path, fmt: str, report: InspectionReport) -> None:
        if fmt in {"wav", "flac"}:
            import soundfile

            with soundfile.SoundFile(path) as snd:
                report.channels = snd.channels
                report.sample_rate = snd.samplerate
                report.duration_seconds = float(len(snd)) / snd.samplerate
        elif fmt in {"mp3", "ogg"}:
            from mutagen import File as MutagenFile

            mf = MutagenFile(path)
            if mf is not None and mf.info is not None:
                report.sample_rate = getattr(mf.info, "sample_rate", None)
                report.channels = getattr(mf.info, "channels", None)
                report.duration_seconds = getattr(mf.info, "length", None)
        else:
            raise UnsupportedFormatError(f"unsupported audio format: {fmt}")

    def _inspect_video(self, path: Path, fmt: str, report: InspectionReport) -> None:
        import imageio.v3 as iio

        meta = iio.immeta(path, plugin="pyav")
        report.width = int(meta.get("size", [0, 0])[0]) if "size" in meta else None
        report.height = int(meta.get("size", [0, 0])[1]) if "size" in meta else None
        report.duration_seconds = float(meta.get("duration", 0.0) or 0.0)
        report.frame_count = int(meta.get("fps", 0) * report.duration_seconds) if report.duration_seconds else None
        report.container_metadata["container"] = fmt


__all__ = ["InspectionReport", "MediaInspector"]
