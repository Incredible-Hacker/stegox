"""Best-effort secure file deletion.

This module overwrites a file with random bytes (and a final zero
pattern) before unlinking it. It is a defense-in-depth measure for
analysts working with sensitive intermediate files.

Note: on flash storage and copy-on-write filesystems, overwriting is
not guaranteed to erase the underlying blocks. Treat this as a
best-effort measure, not a guarantee.
"""

from __future__ import annotations

import os
from pathlib import Path

PASSES: int = 3


def _overwrite_with_random(path: Path, length: int) -> None:
    block = 1024 * 1024
    with path.open("r+b", buffering=0) as fh:
        remaining = length
        while remaining > 0:
            chunk = os.urandom(min(block, remaining))
            fh.write(chunk)
            remaining -= len(chunk)
        fh.flush()
        os.fsync(fh.fileno())


def _zero_fill(path: Path, length: int) -> None:
    block = 1024 * 1024
    zeros = b"\x00" * min(block, length)
    with path.open("r+b", buffering=0) as fh:
        remaining = length
        while remaining > 0:
            to_write = zeros[: min(len(zeros), remaining)]
            fh.write(to_write)
            remaining -= len(to_write)
        fh.flush()
        os.fsync(fh.fileno())


def secure_delete(path: Path, *, passes: int = PASSES) -> None:
    """Overwrite ``path`` with random bytes and unlink it.

    The file is renamed to a temporary name first to make recovery
    harder on journaled filesystems. Missing files are not an error.
    """
    if not path.exists() or not path.is_file():
        return
    size = path.stat().st_size
    parent = path.parent
    tmp = parent / f".{path.name}.{os.getpid()}.{os.urandom(4).hex()}"
    try:
        path.rename(tmp)
    except OSError:
        tmp = path
    for _ in range(max(1, passes)):
        _overwrite_with_random(tmp, size)
    _zero_fill(tmp, size)
    try:
        tmp.unlink()
    finally:
        if tmp.exists():
            tmp.unlink()


__all__ = ["secure_delete"]
