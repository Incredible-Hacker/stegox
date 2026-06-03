"""Media abstraction layer.

This package groups everything related to identifying, loading, and
inspecting media files. Per-format handlers live in
:mod:`stegox.media.formats`.
"""

from stegox.media.identifier import FileIdentifier, IdentificationResult
from stegox.media.inspector import MediaInspector
from stegox.media.loader import MediaLoader
from stegox.media.registry import FormatHandler, FormatRegistry

__all__ = [
    "FileIdentifier",
    "FormatHandler",
    "FormatRegistry",
    "IdentificationResult",
    "MediaInspector",
    "MediaLoader",
]
