"""Bit packing and unpacking helpers for LSB embedders.

The bit ordering is **most-significant-bit first** to match the
convention used by most stego toolkits. The helpers operate on Python
``bytes`` and ``bytearray`` for clarity.
"""

from __future__ import annotations

from collections.abc import Iterator


class BitReader:
    """Iterate over the bits of a bytes-like object, MSB first."""

    __slots__ = ("_bit", "_byte", "_data", "_total")

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._byte = 0
        self._bit = 0
        self._total = len(data) * 8

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self._byte >= len(self._data):
            raise StopIteration
        bit = (self._data[self._byte] >> (7 - self._bit)) & 1
        self._bit += 1
        if self._bit == 8:
            self._bit = 0
            self._byte += 1
        return bit

    def __len__(self) -> int:  # pragma: no cover - trivial
        return self._total - self._byte * 8 - self._bit


class BitWriter:
    """Pack bits MSB-first into a bytearray."""

    __slots__ = ("_bit", "_buf", "_byte")

    def __init__(self) -> None:
        self._buf = bytearray()
        self._byte = 0
        self._bit = 0

    def write_bit(self, bit: int) -> None:
        if self._bit == 0:
            self._buf.append(0)
        if bit & 1:
            self._buf[-1] |= 1 << (7 - self._bit)
        self._bit += 1
        if self._bit == 8:
            self._bit = 0

    def write_bits(self, value: int, nbits: int) -> None:
        for i in range(nbits - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def value(self) -> bytes:
        return bytes(self._buf)

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._buf) * 8 + self._bit


def bits_to_bytes(bits: list[int]) -> bytes:
    """Pack a list/iterable of bits into bytes (MSB first).

    Trailing bits that do not complete a byte are padded with zeros.
    """
    w = BitWriter()
    for b in bits:
        w.write_bit(b)
    return w.value()


__all__ = ["BitReader", "BitWriter", "bits_to_bytes"]
