"""File-type identification.

Combines magic-byte matching with extension hints to produce a
``MediaTarget``. The identifier is intentionally permissive: it never
raises on a missing signature and falls back to ``"unknown"``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from stegox.core.constants import MediaType
from stegox.utils.magic import identify_format


@dataclass(frozen=True, slots=True)
class IdentificationResult:
    format_name: str
    media_type: MediaType
    by_signature: bool
    by_extension: bool


_EXT_TO_MEDIA: dict[str, tuple[str, str]] = {
    ".png": ("png", MediaType.IMAGE),
    ".bmp": ("bmp", MediaType.IMAGE),
    ".jpg": ("jpeg", MediaType.IMAGE),
    ".jpeg": ("jpeg", MediaType.IMAGE),
    ".tif": ("tiff", MediaType.IMAGE),
    ".tiff": ("tiff", MediaType.IMAGE),
    ".webp": ("webp", MediaType.IMAGE),
    ".gif": ("gif", MediaType.IMAGE),
    ".wav": ("wav", MediaType.AUDIO),
    ".flac": ("flac", MediaType.AUDIO),
    ".mp3": ("mp3", MediaType.AUDIO),
    ".ogg": ("ogg", MediaType.AUDIO),
    ".mp4": ("mp4", MediaType.VIDEO),
    ".m4v": ("mp4", MediaType.VIDEO),
    ".avi": ("avi", MediaType.VIDEO),
    ".mkv": ("mkv", MediaType.VIDEO),
    ".mov": ("mov", MediaType.VIDEO),
    ".webm": ("webm", MediaType.VIDEO),
    ".txt": ("txt", MediaType.TEXT),
    ".md": ("md", MediaType.TEXT),
    ".markdown": ("md", MediaType.TEXT),
    ".docx": ("docx", MediaType.TEXT),
}


class FileIdentifier:
    """Identify ``path`` using both magic bytes and extension."""

    def identify(self, path: Path) -> IdentificationResult:
        sig = identify_format(path)
        ext = _EXT_TO_MEDIA.get(path.suffix.lower())
        by_sig = sig is not None
        by_ext = ext is not None

        if by_sig and by_ext:
            fmt, media = sig  # type: ignore[misc]
            # Magic bytes are authoritative when both agree on media
            return IdentificationResult(
                format_name=fmt, media_type=MediaType(media), by_signature=True, by_extension=True
            )
        if by_sig:
            fmt, media = sig  # type: ignore[misc]
            return IdentificationResult(
                format_name=fmt,
                media_type=MediaType(media),
                by_signature=True,
                by_extension=False,
            )
        if by_ext:
            fmt, media = ext  # type: ignore[misc]
            return IdentificationResult(
                format_name=fmt,
                media_type=media,
                by_signature=False,
                by_extension=True,
            )
        return IdentificationResult(
            format_name="unknown",
            media_type=MediaType.UNIVERSAL,
            by_signature=False,
            by_extension=False,
        )


__all__ = ["FileIdentifier", "IdentificationResult"]
