"""Evidence hashing helpers."""

from __future__ import annotations

from pathlib import Path

from stegox.utils.hashing import FileHashes, hash_file


def evidence_hash(path: Path, *, with_sha512: bool = True) -> FileHashes:
    """Compute the canonical evidence hash for ``path``."""
    return hash_file(path, with_sha512=with_sha512)


__all__ = ["evidence_hash"]
