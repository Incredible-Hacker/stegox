"""Format handler registry.

A :class:`FormatHandler` is a small adapter object that knows how to
read and (optionally) write a specific file format. The registry is a
process-global lookup keyed by format name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from stegox.core.constants import MediaType


@dataclass(frozen=True, slots=True)
class FormatHandler:
    """Metadata describing a single format handler."""

    name: str
    media_type: MediaType
    read: bool
    write: bool
    extensions: tuple[str, ...]


class FormatRegistry:
    """In-memory registry of known formats."""

    _handlers: ClassVar[dict[str, FormatHandler]] = {}

    @classmethod
    def register(cls, handler: FormatHandler) -> None:
        cls._handlers[handler.name] = handler

    @classmethod
    def get(cls, name: str) -> FormatHandler | None:
        return cls._handlers.get(name)

    @classmethod
    def all(cls) -> list[FormatHandler]:
        return list(cls._handlers.values())

    @classmethod
    def for_media(cls, media_type: MediaType) -> list[FormatHandler]:
        return [h for h in cls._handlers.values() if h.media_type == media_type]


def _bootstrap_registry() -> None:
    """Populate the registry with built-in handlers."""
    if FormatRegistry._handlers:
        return
    for fmt, media, exts in [
        ("png", MediaType.IMAGE, (".png",)),
        ("bmp", MediaType.IMAGE, (".bmp",)),
        ("jpeg", MediaType.IMAGE, (".jpg", ".jpeg")),
        ("tiff", MediaType.IMAGE, (".tif", ".tiff")),
        ("webp", MediaType.IMAGE, (".webp",)),
        ("wav", MediaType.AUDIO, (".wav",)),
        ("flac", MediaType.AUDIO, (".flac",)),
        ("mp3", MediaType.AUDIO, (".mp3",)),
        ("ogg", MediaType.AUDIO, (".ogg",)),
        ("mp4", MediaType.VIDEO, (".mp4", ".m4v")),
        ("avi", MediaType.VIDEO, (".avi",)),
        ("mkv", MediaType.VIDEO, (".mkv",)),
        ("mov", MediaType.VIDEO, (".mov",)),
        ("txt", MediaType.TEXT, (".txt",)),
        ("md", MediaType.TEXT, (".md", ".markdown")),
        ("docx", MediaType.TEXT, (".docx",)),
    ]:
        FormatRegistry.register(
            FormatHandler(
                name=fmt,
                media_type=media,
                read=True,
                write=fmt != "mp3" and fmt != "ogg",  # lossy formats: extract only
                extensions=exts,
            )
        )


_bootstrap_registry()


__all__ = ["FormatHandler", "FormatRegistry"]


def __getattr__(name: str) -> Any:  # pragma: no cover - lazy bootstrap
    if name in {"FormatRegistry"}:
        _bootstrap_registry()
        return FormatRegistry
    raise AttributeError(name)
