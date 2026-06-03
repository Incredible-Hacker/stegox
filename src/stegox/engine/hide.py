"""Hide orchestration: dispatches to the correct module based on media type."""

from __future__ import annotations

from pathlib import Path

from stegox.core.errors import UnsupportedFormatError
from stegox.core.logging import get_logger
from stegox.core.result import HideResult
from stegox.media.identifier import FileIdentifier
from stegox.modules import audio, image, metadata, text, video

log = get_logger("engine.hide")


def hide(
    cover: Path,
    payload: bytes,
    *,
    strategy: str,
    password: str | None = None,
    stego: Path | None = None,
    media_type: str | None = None,
) -> HideResult:
    """Embed ``payload`` into ``cover`` using the requested strategy."""
    ident = FileIdentifier().identify(cover)
    fmt = media_type or ident.media_type.value
    log.info("hiding payload (%d bytes) into %s via %s", len(payload), cover.name, strategy)

    if fmt == "image":
        return image.embed_image(cover, payload, strategy, password=password, stego=stego)
    if fmt == "audio":
        return audio.embed_audio(cover, payload, strategy, password=password, stego=stego)
    if fmt == "video":
        return video.embed_video(cover, payload, strategy, password=password, stego=stego)
    if fmt == "text":
        return text.embed_text(cover, payload, strategy, stego=stego)
    if fmt == "metadata":
        field = strategy  # in metadata mode, "strategy" is the field name
        return metadata.embed_metadata(cover, payload, field=field, stego=stego)
    raise UnsupportedFormatError(f"unsupported media_type for hide: {fmt}")


__all__ = ["hide"]
