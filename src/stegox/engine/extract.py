"""Extract orchestration."""

from __future__ import annotations

from pathlib import Path

from stegox.core.errors import UnsupportedFormatError
from stegox.core.logging import get_logger
from stegox.media.identifier import FileIdentifier
from stegox.modules import audio, image, metadata, text, video

log = get_logger("engine.extract")


def extract(
    stego: Path,
    *,
    strategy: str,
    password: str | None = None,
    payload_bytes: int | None = None,
    out: Path | None = None,
    media_type: str | None = None,
) -> bytes:
    """Recover a hidden payload from ``stego``."""
    ident = FileIdentifier().identify(stego)
    fmt = media_type or ident.media_type.value
    log.info("extracting payload from %s via %s", stego.name, strategy)

    if fmt == "image":
        data = image.extract_image(stego, strategy, password=password, payload_bytes=payload_bytes)
    elif fmt == "audio":
        data = audio.extract_audio(stego, strategy, password=password, payload_bytes=payload_bytes)
    elif fmt == "video":
        data = video.extract_video(stego, strategy, password=password, payload_bytes=payload_bytes)
    elif fmt == "text":
        data = text.extract_text(stego, strategy)
    elif fmt == "metadata":
        field = strategy
        data = metadata.extract_metadata(stego, field=field)
    else:
        raise UnsupportedFormatError(f"unsupported media_type for extract: {fmt}")

    if out is not None:
        out.write_bytes(data)
        log.info("wrote %d bytes to %s", len(data), out)
    return data


__all__ = ["extract"]
