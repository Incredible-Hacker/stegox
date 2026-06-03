"""File hashing utilities.

All hashes are computed in a single pass over the file using a
``hashlib`` constructor. ``FileHashes`` is the legacy DFIR-friendly
shape used across the codebase.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

CHUNK_SIZE: Final[int] = 1024 * 1024


@dataclass(frozen=True, slots=True)
class FileHashes:
    """Multi-algorithm file fingerprints."""

    md5: str
    sha1: str
    sha256: str
    sha512: str | None = None
    size: int = 0

    def to_dict(self) -> dict[str, str | int | None]:
        out: dict[str, str | int | None] = {
            "md5": self.md5,
            "sha1": self.sha1,
            "sha256": self.sha256,
            "size": self.size,
        }
        if self.sha512 is not None:
            out["sha512"] = self.sha512
        return out


def _digest(path: Path, algorithms: Iterable[str], with_size: bool = True) -> dict[str, str]:
    hashers = {name: hashlib.new(name) for name in algorithms}
    size = 0
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break
            size += len(chunk)
            for h in hashers.values():
                h.update(chunk)
    result = {name: h.hexdigest() for name, h in hashers.items()}
    if with_size:
        result["__size__"] = str(size)
    return result


def hash_file(path: Path, *, with_sha512: bool = False) -> FileHashes:
    """Compute MD5, SHA1, SHA256 (and optionally SHA512) for ``path``."""
    algorithms = ("md5", "sha1", "sha256")
    if with_sha512:
        algorithms = ("md5", "sha1", "sha256", "sha512")
    digests = _digest(path, algorithms)
    size = int(digests.pop("__size__", "0"))
    return FileHashes(
        md5=digests["md5"],
        sha1=digests["sha1"],
        sha256=digests["sha256"],
        sha512=digests.get("sha512"),
        size=size,
    )


__all__ = ["CHUNK_SIZE", "FileHashes", "hash_file"]
