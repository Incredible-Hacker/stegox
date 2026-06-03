"""Magic-byte file identification.

A small, dependency-free signature database used to disambiguate file
formats when the extension is missing or misleading. The table is
intentionally conservative; new entries are added in their own commits
so false-positive behavior is easy to audit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# (offset, signature_bytes, format_name, media_type)
_SIGNATURES: tuple[tuple[int, bytes, str, str], ...] = (
    (0, b"\x89PNG\r\n\x1a\n", "png", "image"),
    (0, b"BM", "bmp", "image"),
    (0, b"\xff\xd8\xff", "jpeg", "image"),
    (0, b"GIF87a", "gif", "image"),
    (0, b"GIF89a", "gif", "image"),
    (0, b"RIFF", "riff", "container"),  # needs subtype
    (0, b"II*\x00", "tiff", "image"),
    (0, b"MM\x00*", "tiff", "image"),
    (0, b"RIFF", "webp", "image"),  # overridden by RIFF+WEBP subtype below
    (0, b"fLaC", "flac", "audio"),
    (0, b"OggS", "ogg", "audio"),
    (0, b"ID3", "mp3", "audio"),
    (0, b"\xff\xfb", "mp3", "audio"),
    (0, b"RIFF", "wav", "audio"),  # overridden by RIFF+WAVE subtype
    (0, b"\x1aE\xdf\xa3", "mkv", "video"),  # also WebM
    (4, b"ftyp", "mp4", "video"),
    (0, b"<?xml", "xml", "text"),
    (0, b"PK\x03\x04", "zip", "archive"),
    (0, b"7z\xbc\xaf\x27\x1c", "7z", "archive"),
    (0, b"Rar!\x1a\x07\x00", "rar", "archive"),
)


@dataclass(frozen=True, slots=True)
class MagicSignature:
    offset: int
    signature: bytes
    format: str
    media_type: str


MAGIC_SIGNATURES: tuple[MagicSignature, ...] = tuple(
    MagicSignature(off, sig, fmt, media) for off, sig, fmt, media in _SIGNATURES
)


def identify_format(path: Path) -> tuple[str, str] | None:
    """Return ``(format, media_type)`` for ``path`` based on magic bytes.

    Returns ``None`` if no signature matches.
    """
    try:
        with path.open("rb") as fh:
            head = fh.read(64)
    except OSError:
        return None

    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image"
    if head.startswith(b"BM"):
        return "bmp", "image"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpeg", "image"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "gif", "image"
    if head.startswith(b"II*\x00") or head.startswith(b"MM\x00*"):
        return "tiff", "image"
    if head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WEBP":
        return "webp", "image"
    if head.startswith(b"RIFF") and len(head) >= 12 and head[8:12] == b"WAVE":
        return "wav", "audio"
    if head.startswith(b"fLaC"):
        return "flac", "audio"
    if head.startswith(b"OggS"):
        return "ogg", "audio"
    if head.startswith(b"ID3") or head.startswith(b"\xff\xfb"):
        return "mp3", "audio"
    if head.startswith(b"\x1aE\xdf\xa3"):
        # Could be MKV or WebM; we report mkv and let codecs further classify
        return "mkv", "video"
    if len(head) >= 8 and head[4:8] == b"ftyp":
        return "mp4", "video"
    if head.startswith(b"<?xml"):
        return "xml", "text"
    if head.startswith(b"PK\x03\x04"):
        return "zip", "archive"
    if head.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "7z", "archive"
    if head.startswith(b"Rar!\x1a\x07\x00"):
        return "rar", "archive"
    return None


__all__ = ["MAGIC_SIGNATURES", "MagicSignature", "identify_format"]
