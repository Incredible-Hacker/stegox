"""Safe filesystem helpers."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from stegox.core.errors import StegoXError


def read_bytes(path: Path) -> bytes:
    """Read the entire file at ``path`` as bytes.

    Raises :class:`StegoXError` with exit_code 3 on missing file and
    exit_code 1 on other I/O errors.
    """
    try:
        with path.open("rb") as fh:
            return fh.read()
    except FileNotFoundError as exc:
        raise StegoXError(f"file not found: {path}", context={"path": str(path)}) from exc
    except OSError as exc:
        raise StegoXError(f"read error: {exc}", context={"path": str(path)}) from exc


def atomic_write(path: Path, data: bytes) -> Path:
    """Write ``data`` to ``path`` atomically.

    Writes to a temporary file in the same directory, fsyncs, and
    renames. This prevents leaving partial files on disk if the
    process is interrupted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{os.urandom(4).hex()}.tmp")
    try:
        with tmp.open("wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        Path(tmp).replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise
    return path


@contextmanager
def safe_open(path: Path, mode: str = "rb") -> Iterator[BinaryIO]:
    """Open ``path`` and ensure it is closed even on error."""
    fh = path.open(mode)  # type: ignore[assignment]
    try:
        yield fh  # type: ignore[misc]
    finally:
        fh.close()


__all__ = ["atomic_write", "read_bytes", "safe_open"]
