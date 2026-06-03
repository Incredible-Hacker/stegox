"""Tests for ``stegox.utils``."""

from __future__ import annotations

from stegox.utils.bitio import BitReader, BitWriter
from stegox.utils.hashing import hash_file
from stegox.utils.io import atomic_write, read_bytes
from stegox.utils.magic import identify_format


def test_bit_round_trip() -> None:
    payload = bytes(range(256))
    reader = BitReader(payload)
    writer = BitWriter()
    for _ in range(len(payload) * 8):
        writer.write_bit(next(reader))
    assert writer.value() == payload


def test_atomic_write(tmp_path) -> None:
    p = tmp_path / "x.bin"
    atomic_write(p, b"hello")
    assert p.read_bytes() == b"hello"


def test_read_bytes(tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_bytes(b"abc")
    assert read_bytes(p) == b"abc"


def test_hash_file(tmp_path) -> None:
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello stegox")
    h = hash_file(p)
    assert len(h.sha256) == 64
    assert h.size == len("hello stegox")


def test_identify_format(tmp_path) -> None:
    p = tmp_path / "x.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
    fmt, media = identify_format(p) or ("unknown", "universal")
    assert fmt == "png"
    assert media == "image"
