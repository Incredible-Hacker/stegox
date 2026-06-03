"""Metadata steganography: hide, extract, and audit.

Supported targets:

- JPEG: EXIF, XMP, IPTC
- PNG: tEXt, zTXt, iTXt chunks
- MP3: ID3v2 tags
- OGG/FLAC: Vorbis comments
- MP4/MKV/MOV: container tags
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from stegox.core.constants import Strategy
from stegox.core.errors import UnsupportedFormatError
from stegox.core.result import HideResult

# A small registry of well-known fields. The audit detector inspects these
# and any user-provided field names.
JPEG_FIELDS: tuple[str, ...] = (
    "ImageDescription", "UserComment", "Artist", "Copyright",
    "XPComment", "XPAuthor", "XPKeywords", "XPSubject",
    "XPSubject", "XPTitle",
)
PNG_TEXT_KEYS: tuple[str, ...] = (
    "Comment", "Description", "Author", "Copyright", "Title", "Source",
    "Warning", "Disclaimer",
)
ID3_FIELDS: tuple[str, ...] = ("TIT2", "TPE1", "TALB", "COMM", "TXXX", "TSSE")


def list_fields() -> dict[str, tuple[str, ...]]:
    return {
        "jpeg": JPEG_FIELDS,
        "png": PNG_TEXT_KEYS,
        "mp3": ID3_FIELDS,
        "ogg": ("TITLE", "ARTIST", "COMMENT", "DESCRIPTION"),
        "flac": ("TITLE", "ARTIST", "COMMENT", "DESCRIPTION"),
        "mp4": ("©nam", "©ART", "©cmt", "desc"),
    }


def list_strategies():
    return [
        {"id": "metadata-field", "description": "Embed payload in a named metadata field.", "formats": ["jpeg", "png", "mp3", "ogg", "flac", "mp4"], "encrypted": False},
    ]


# ---------------------------------------------------------------------------
# JPEG (EXIF)
# ---------------------------------------------------------------------------


def embed_jpeg_exif(cover: Path, stego: Path, payload: bytes, *, field: str = "UserComment") -> HideResult:
    from PIL import Image

    if not _is_jpeg(cover):
        raise UnsupportedFormatError("not a JPEG file")
    img = Image.open(cover)
    exif = img.getexif()
    from PIL.ExifTags import TAGS  # type: ignore[attr-defined]

    # Resolve field name to tag id
    tag_id = None
    for k, v in TAGS.items():
        if v == field:
            tag_id = k
            break
    if tag_id is None:
        # Allow numeric IDs
        try:
            tag_id = int(field)
        except ValueError as exc:
            raise UnsupportedFormatError(f"unknown EXIF field: {field}") from exc
    encoded = base64.b64encode(payload).decode("ascii")
    exif[tag_id] = encoded
    img.save(stego, format="jpeg", exif=exif.tobytes())
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PASSWORD_EMBED,
                      capacity_bytes=len(encoded), payload_bytes=len(payload),
                      encrypted=False, sha256="")


def extract_jpeg_exif(stego: Path, *, field: str = "UserComment") -> bytes:
    from PIL import ExifTags, Image  # type: ignore[attr-defined]

    img = Image.open(stego)
    exif = img.getexif()
    tag_id = None
    for k, v in ExifTags.TAGS.items():
        if v == field:
            tag_id = k
            break
    if tag_id is None:
        try:
            tag_id = int(field)
        except ValueError as exc:
            raise UnsupportedFormatError(f"unknown EXIF field: {field}") from exc
    value = exif.get(tag_id)
    if not value:
        return b""
    if isinstance(value, bytes):
        return base64.b64decode(value.split(b"\x00", 1)[-1])
    return base64.b64decode(str(value))


# ---------------------------------------------------------------------------
# PNG text chunks
# ---------------------------------------------------------------------------


def embed_png_text(cover: Path, stego: Path, payload: bytes, *, key: str = "Comment") -> HideResult:
    from PIL import Image

    if not _is_png(cover):
        raise UnsupportedFormatError("not a PNG file")
    img = Image.open(cover)
    encoded = base64.b64encode(payload).decode("ascii")
    info = dict(img.info or {})
    info[key] = encoded
    img.save(stego, format="png", pnginfo=_make_pnginfo(info))
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PASSWORD_EMBED,
                      capacity_bytes=len(encoded), payload_bytes=len(payload),
                      encrypted=False, sha256="")


def extract_png_text(stego: Path, *, key: str = "Comment") -> bytes:
    from PIL import Image

    img = Image.open(stego)
    value = img.info.get(key)
    if not value:
        return b""
    return base64.b64decode(str(value))


def _make_pnginfo(info: dict[str, str]) -> Any:
    from PIL.PngImagePlugin import PngInfo  # type: ignore[attr-defined]

    pi = PngInfo()
    for k, v in info.items():
        pi.add_text(k, v)
    return pi


# ---------------------------------------------------------------------------
# MP3 / OGG / FLAC via mutagen
# ---------------------------------------------------------------------------


def embed_mutagen(cover: Path, stego: Path, payload: bytes, *, field: str) -> HideResult:
    from mutagen.flac import FLAC  # type: ignore[attr-defined]
    from mutagen.id3 import ID3, TXXX  # type: ignore[attr-defined]
    from mutagen.mp4 import MP4  # type: ignore[attr-defined]
    from mutagen.oggvorbis import OggVorbis  # type: ignore[attr-defined]

    encoded = base64.b64encode(payload).decode("ascii")
    suffix = cover.suffix.lower()
    if suffix == ".mp3":
        try:
            tags = ID3(cover)
        except Exception:
            tags = ID3()
        tags.add(TXXX(encoding=3, lang="eng", desc="stegox", text=[encoded]))
        tags.save(stego)
    elif suffix in (".flac", ".ogg"):
        audio = FLAC(cover) if suffix == ".flac" else OggVorbis(cover)
        audio[field.lower()] = [encoded]
        audio.save(stego)
    elif suffix == ".m4a" or suffix == ".mp4":
        audio = MP4(cover)
        key = next(iter(audio.tags.keys()), "©cmt") if audio.tags else "©cmt"
        audio.tags[key] = [encoded.encode("utf-8")]
        audio.save(stego)
    else:
        raise UnsupportedFormatError(f"unsupported container for metadata embed: {suffix}")
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PASSWORD_EMBED,
                      capacity_bytes=len(encoded), payload_bytes=len(payload),
                      encrypted=False, sha256="")


def extract_mutagen(stego: Path, *, field: str) -> bytes:
    from mutagen import File as MutagenFile  # type: ignore[attr-defined]
    from mutagen.id3 import ID3  # type: ignore[attr-defined]

    audio = MutagenFile(stego)
    if audio is None or audio.tags is None:
        return b""
    if isinstance(audio.tags, ID3):
        for frame in audio.tags.getall("TXXX"):
            for text in frame.text:
                try:
                    return base64.b64decode(text)
                except Exception:
                    continue
    else:
        for key in (field, field.lower(), field.upper(), "stegox", "comment"):
            values = audio.tags.get(key)
            if values:
                try:
                    return base64.b64decode(str(values[0]))
                except Exception:
                    continue
    return b""


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def audit_metadata(path: Path) -> dict[str, Any]:
    """Return a structured audit of all metadata fields in ``path``."""
    suffix = path.suffix.lower()
    out: dict[str, Any] = {"path": str(path), "format": suffix.lstrip("."), "fields": []}
    if suffix in (".jpg", ".jpeg"):
        out["fields"] = _audit_jpeg(path)
    elif suffix == ".png":
        out["fields"] = _audit_png(path)
    elif suffix in (".mp3", ".flac", ".ogg", ".m4a", ".mp4"):
        out["fields"] = _audit_mutagen(path)
    else:
        out["fields"] = []
    return out


def _audit_jpeg(path: Path) -> list[dict[str, Any]]:
    from PIL import Image

    img = Image.open(path)
    exif = img.getexif()
    fields: list[dict[str, Any]] = []
    from PIL.ExifTags import TAGS  # type: ignore[attr-defined]

    for tag_id, value in exif.items():
        name = TAGS.get(tag_id, str(tag_id))
        fields.append(_field_record(name, value))
    return fields


def _audit_png(path: Path) -> list[dict[str, Any]]:
    from PIL import Image

    img = Image.open(path)
    return [_field_record(k, v) for k, v in (img.info or {}).items()]


def _audit_mutagen(path: Path) -> list[dict[str, Any]]:
    from mutagen import File as MutagenFile  # type: ignore[attr-defined]

    audio = MutagenFile(path)
    if audio is None or audio.tags is None:
        return []
    out: list[dict[str, Any]] = []
    for key, value in audio.tags.items():
        out.append(_field_record(str(key), value))
    return out


def _field_record(name: str, value: Any) -> dict[str, Any]:
    text = str(value)
    return {
        "name": name,
        "length": len(text),
        "entropy": _shannon_entropy(text.encode("utf-8", errors="ignore")),
        "looks_base64": _looks_like_base64(text),
        "looks_hex": _looks_like_hex(text),
        "preview": text[:64],
    }


def _shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for b in data:
        counts[b] += 1
    total = len(data)
    import math

    return -sum((c / total) * math.log2(c / total) for c in counts if c)


_BASE64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r ")
_HEX_CHARS = set("0123456789abcdefABCDEF\n\r ")


def _looks_like_base64(text: str) -> bool:
    if len(text) < 32 or len(text) % 4 != 0:
        return False
    return all(c in _BASE64_CHARS for c in text)


def _looks_like_hex(text: str) -> bool:
    text = text.strip()
    if len(text) < 32 or len(text) % 2 != 0:
        return False
    return all(c in _HEX_CHARS for c in text)


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


def _is_jpeg(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(3) == b"\xff\xd8\xff"
    except OSError:
        return False


def _is_png(path: Path) -> bool:
    try:
        with path.open("rb") as fh:
            return fh.read(8) == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def embed_metadata(cover: Path, payload: bytes, *, field: str, stego: Path | None = None) -> HideResult:
    if stego is None:
        stego = cover.with_name(f"{cover.stem}.stegox{cover.suffix}")
    suffix = cover.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return embed_jpeg_exif(cover, stego, payload, field=field)
    if suffix == ".png":
        return embed_png_text(cover, stego, payload, key=field)
    if suffix in (".mp3", ".flac", ".ogg", ".m4a", ".mp4"):
        return embed_mutagen(cover, stego, payload, field=field)
    raise UnsupportedFormatError(f"unsupported metadata target: {suffix}")


def extract_metadata(stego: Path, *, field: str) -> bytes:
    suffix = stego.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return extract_jpeg_exif(stego, field=field)
    if suffix == ".png":
        return extract_png_text(stego, key=field)
    if suffix in (".mp3", ".flac", ".ogg", ".m4a", ".mp4"):
        return extract_mutagen(stego, field=field)
    raise UnsupportedFormatError(f"unsupported metadata target: {suffix}")
