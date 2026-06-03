"""Text steganography: zero-width, whitespace, homoglyph encodings."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from pathlib import Path

from stegox.core.constants import Strategy
from stegox.core.errors import CapacityError, UnsupportedFormatError
from stegox.core.result import HideResult
from stegox.utils.bitio import BitReader, BitWriter

# Zero-width characters used as the symbol alphabet
ZW_CHARS: tuple[str, ...] = ("\u200b", "\u200c", "\u200d", "\ufeff")
# Whitespace symbols: ' ' (00) and '\t' (01)
WS_CHARS: tuple[str, ...] = (" ", "\t")
# Latin-to-homoglyph mapping
HOMOGLYPHS: dict[str, str] = {
    "a": "\u0430",  # Cyrillic a
    "e": "\u0435",  # Cyrillic e
    "o": "\u043e",  # Cyrillic o
    "p": "\u0440",  # Cyrillic p
    "c": "\u0441",  # Cyrillic c
    "x": "\u0445",  # Cyrillic x
    "y": "\u0443",  # Cyrillic y
    "i": "\u0456",  # Cyrillic i
}


def list_strategies():
    return [
        {"id": Strategy.ZERO_WIDTH, "description": "Encode payload in zero-width characters.", "formats": ["txt", "md"], "encrypted": False},
        {"id": Strategy.WHITESPACE, "description": "Trailing space and tab encoding.", "formats": ["txt", "md"], "encrypted": False},
        {"id": Strategy.HOMOGLYPH, "description": "Substitute characters with confusable Unicode look-alikes.", "formats": ["txt", "md"], "encrypted": False},
        {"id": Strategy.HOMOGLYPH_ADVANCED, "description": "Extended confusable mapping (placeholder).", "formats": ["txt", "md"], "encrypted": False},
    ]


def _bits_per_symbol(strategy: str) -> int:
    if strategy == Strategy.ZERO_WIDTH:
        return 2  # 4 symbols
    if strategy == Strategy.WHITESPACE:
        return 1  # 2 symbols
    if strategy in (Strategy.HOMOGLYPH, Strategy.HOMOGLYPH_ADVANCED):
        return 1
    raise UnsupportedFormatError(strategy)


def capacity(cover_text: str, strategy: str) -> int:
    """Return the maximum payload in bytes given a cover of length ``cover_text``."""
    bits_per_sym = _bits_per_symbol(strategy)
    if strategy == Strategy.HOMOGLYPH:
        # Each character is one symbol; we only have 8 confusables
        return max(0, sum(1 for c in cover_text if c.lower() in HOMOGLYPHS) // 8)
    if strategy in (Strategy.HOMOGLYPH_ADVANCED,):
        return max(0, len(cover_text) // 8)
    return max(0, (len(cover_text) * bits_per_sym) // 8 - 8)


# ---------------------------------------------------------------------------
# Zero-width
# ---------------------------------------------------------------------------


def embed_zero_width(cover: Path, stego: Path, payload: bytes) -> HideResult:
    text = cover.read_text(encoding="utf-8")
    bits = list(BitReader(payload))
    out_chars: list[str] = []
    bit_idx = 0
    for ch in text:
        out_chars.append(ch)
        if bit_idx + 2 > len(bits):
            continue
        symbol = (bits[bit_idx] << 1) | bits[bit_idx + 1]
        out_chars.append(ZW_CHARS[symbol])
        bit_idx += 2
    if bit_idx < len(bits):
        raise CapacityError("cover too small for payload")
    stego.write_text("".join(out_chars), encoding="utf-8")
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.ZERO_WIDTH,
                      capacity_bytes=len(payload), payload_bytes=len(payload), encrypted=False, sha256="")


def extract_zero_width(stego: Path) -> bytes:
    text = stego.read_text(encoding="utf-8")
    bits: list[int] = []
    for ch in text:
        if ch in ZW_CHARS:
            idx = ZW_CHARS.index(ch)
            bits.append((idx >> 1) & 1)
            bits.append(idx & 1)
    return _bits_to_bytes(bits)


# ---------------------------------------------------------------------------
# Whitespace
# ---------------------------------------------------------------------------


def embed_whitespace(cover: Path, stego: Path, payload: bytes) -> HideResult:
    text = cover.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    bits = list(BitReader(payload))
    out_lines: list[str] = []
    bit_idx = 0
    for line in lines:
        if bit_idx >= len(bits):
            out_lines.append(line)
            continue
        stripped = line.rstrip("\n")
        suffix = "\n" if line.endswith("\n") else ""
        if bit_idx < len(bits):
            stripped += WS_CHARS[bits[bit_idx]]
            bit_idx += 1
        out_lines.append(stripped + suffix)
    if bit_idx < len(bits):
        raise CapacityError("cover too small for payload")
    stego.write_text("".join(out_lines), encoding="utf-8")
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.WHITESPACE,
                      capacity_bytes=len(payload), payload_bytes=len(payload), encrypted=False, sha256="")


def extract_whitespace(stego: Path) -> bytes:
    text = stego.read_text(encoding="utf-8")
    bits: list[int] = []
    for line in text.splitlines():
        trailing = line[len(line.rstrip()) :]
        for ch in trailing:
            bits.append(WS_CHARS.index(ch) if ch in WS_CHARS else 0)
    return _bits_to_bytes(bits)


# ---------------------------------------------------------------------------
# Homoglyph
# ---------------------------------------------------------------------------


def embed_homoglyph(cover: Path, stego: Path, payload: bytes) -> HideResult:
    text = cover.read_text(encoding="utf-8")
    bits = list(BitReader(payload))
    bit_idx = 0
    out_chars: list[str] = []
    for ch in text:
        lower = ch.lower()
        if lower in HOMOGLYPHS and bit_idx < len(bits):
            mapped = HOMOGLYPHS[lower]
            out_chars.append(mapped if ch.islower() else mapped.upper())
            bit_idx += 1
        else:
            out_chars.append(ch)
    if bit_idx < len(bits):
        raise CapacityError("cover too small for payload")
    stego.write_text("".join(out_chars), encoding="utf-8")
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.HOMOGLYPH,
                      capacity_bytes=bit_idx // 8, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_homoglyph(stego: Path) -> bytes:
    text = stego.read_text(encoding="utf-8")
    bits: list[int] = []
    reverse = dict.fromkeys(HOMOGLYPHS.values(), 1)  # any homoglyph = bit 1
    for ch in text:
        nfd = unicodedata.normalize("NFKD", ch)
        bits.append(1 if any(c in reverse for c in nfd) else 0)
    return _bits_to_bytes(bits)


# ---------------------------------------------------------------------------
# Dispatch helpers
# ---------------------------------------------------------------------------


def _bits_to_bytes(bits: Iterable[int]) -> bytes:
    writer = BitWriter()
    for b in bits:
        writer.write_bit(b)
    return writer.value()


def embed_text(cover: Path, payload: bytes, strategy: str, stego: Path | None = None) -> HideResult:
    if stego is None:
        stego = cover.with_name(f"{cover.stem}.stegox{cover.suffix}")
    if strategy == Strategy.ZERO_WIDTH:
        return embed_zero_width(cover, stego, payload)
    if strategy == Strategy.WHITESPACE:
        return embed_whitespace(cover, stego, payload)
    if strategy in (Strategy.HOMOGLYPH, Strategy.HOMOGLYPH_ADVANCED):
        return embed_homoglyph(cover, stego, payload)
    raise UnsupportedFormatError(f"unknown text strategy: {strategy}")


def extract_text(stego: Path, strategy: str) -> bytes:
    if strategy == Strategy.ZERO_WIDTH:
        return extract_zero_width(stego)
    if strategy == Strategy.WHITESPACE:
        return extract_whitespace(stego)
    if strategy in (Strategy.HOMOGLYPH, Strategy.HOMOGLYPH_ADVANCED):
        return extract_homoglyph(stego)
    raise UnsupportedFormatError(f"unknown text strategy: {strategy}")
