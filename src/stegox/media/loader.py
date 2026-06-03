"""High-level media loader.

The loader is the single entry point used by the engine layer. It
returns a :class:`MediaTarget` with hashes and lightweight metadata.
Heavy parsing is deferred to the per-format handler, but for the
common cases (PNG, BMP, TIFF, WAV) we eagerly read enough to compute
dimensions and sample rate.
"""

from __future__ import annotations

from pathlib import Path

from stegox.core.constants import MediaType
from stegox.core.types import MediaTarget  # re-export
from stegox.media.identifier import FileIdentifier
from stegox.utils.hashing import hash_file


class MediaLoader:
    """Identify, hash, and lightly inspect a media file."""

    def __init__(self, identifier: FileIdentifier | None = None) -> None:
        self.identifier = identifier or FileIdentifier()

    def load(self, path: Path) -> MediaTarget:
        ident = self.identifier.identify(path)
        hashes = hash_file(path)
        return MediaTarget(
            path=path,
            media_type=ident.media_type,
            format_name=ident.format_name,
            hashes=hashes,
            metadata={
                "identified_by_signature": ident.by_signature,
                "identified_by_extension": ident.by_extension,
            },
        )


__all__ = ["MediaLoader", "MediaTarget"]


def is_image(media_type: MediaType) -> bool:
    return media_type == MediaType.IMAGE


def is_audio(media_type: MediaType) -> bool:
    return media_type == MediaType.AUDIO


def is_video(media_type: MediaType) -> bool:
    return media_type == MediaType.VIDEO


def is_text(media_type: MediaType) -> bool:
    return media_type == MediaType.TEXT
