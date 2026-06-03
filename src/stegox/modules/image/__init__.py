"""Image steganography: LSB family and DCT embedders.

Strategies:

- :func:`embed_lsb` — sequential LSB across all channels.
- :func:`embed_randomized_lsb` — pixel order driven by a PRNG.
- :func:`embed_password` — randomized LSB with encrypted framing.
- :func:`embed_dct` — JPEG DCT coefficient modulation.
- :func:`extract_lsb` / :func:`extract_password` / :func:`extract_dct`.

Capacity: for a RGB image of WxH pixels, the theoretical LSB capacity
is ``W * H * 3`` bits minus the framing overhead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from stegox.core.constants import Strategy
from stegox.core.errors import CapacityError, IntegrityError, UnsupportedFormatError
from stegox.core.result import HideResult
from stegox.security.framing import decrypt_payload, encrypt_payload
from stegox.utils.bitio import BitReader, BitWriter

LOSSLESS_FORMATS: frozenset[str] = frozenset({"png", "bmp", "tiff", "webp"})


def list_strategies() -> list[dict[str, Any]]:
    """Return the public strategy catalogue for the image module."""
    return [
        {
            "id": Strategy.LSB,
            "description": "Sequential LSB across all color channels.",
            "formats": sorted(LOSSLESS_FORMATS),
            "encrypted": False,
        },
        {
            "id": Strategy.LSB_RGB,
            "description": "Sequential LSB across RGB only (skip alpha).",
            "formats": sorted(LOSSLESS_FORMATS),
            "encrypted": False,
        },
        {
            "id": Strategy.RANDOMIZED_LSB,
            "description": "Pixel order is driven by a PRNG seeded by the password.",
            "formats": sorted(LOSSLESS_FORMATS),
            "encrypted": False,
        },
        {
            "id": Strategy.PASSWORD_EMBED,
            "description": "Randomized LSB + AES-256-GCM framing with password.",
            "formats": sorted(LOSSLESS_FORMATS),
            "encrypted": True,
        },
        {
            "id": Strategy.DCT_JPEG,
            "description": "Embed in mid-frequency DCT coefficients (lossy).",
            "formats": ["jpeg"],
            "encrypted": False,
        },
    ]


# ---------------------------------------------------------------------------
# Capacity
# ---------------------------------------------------------------------------


def capacity_bytes(cover: Path, *, strategy: str = Strategy.LSB, channels: int = 3) -> int:
    """Return the maximum payload size in bytes for ``cover``."""
    if strategy == Strategy.DCT_JPEG:
        with Image.open(cover) as img:
            w, h = img.size
        # 1 bit per 8x8 block per coefficient slot; conservative
        return max(0, (w // 8) * (h // 8) // 8)
    with Image.open(cover) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
    eff_channels = min(channels, 3)
    return max(0, (w * h * eff_channels) // 8 - 64)


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def _load_rgb_array(cover: Path) -> np.ndarray:
    img = Image.open(cover)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return np.array(img, dtype=np.uint8)


def _lsb_pixels(width: int, height: int, order: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return flat (row, col) index arrays for LSB traversal."""
    if order is None:
        rows = np.repeat(np.arange(height), width)
        cols = np.tile(np.arange(width), height)
        return rows, cols
    return order[:, 0], order[:, 1]


def _write_lsb(cover: Path, stego: Path, payload: bytes, *, channels: tuple[int, ...] = (0, 1, 2),
               order: np.ndarray | None = None) -> None:
    arr = _load_rgb_array(cover)
    h, w, _ = arr.shape
    rows, cols = _lsb_pixels(w, h, order)
    bit_reader = BitReader(payload)
    bit_buffer: list[int] = []
    for r, c in zip(rows.tolist(), cols.tolist(), strict=False):
        for ch in channels:
            try:
                bit = next(bit_reader)
            except StopIteration:
                arr[r, c, ch] = (arr[r, c, ch] & 0xFE) | (bit_buffer.pop(0) if bit_buffer else 0)
                Image.fromarray(arr).save(stego, format=_format_from_ext(stego))
                return
            arr[r, c, ch] = (arr[r, c, ch] & 0xFE) | bit
    Image.fromarray(arr).save(stego, format=_format_from_ext(stego))


def _read_lsb(stego: Path, nbits: int, *, channels: tuple[int, ...] = (0, 1, 2),
              order: np.ndarray | None = None) -> bytes:
    img = Image.open(stego)
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.array(img, dtype=np.uint8)
    h, w, _ = arr.shape
    rows, cols = _lsb_pixels(w, h, order)
    writer = BitWriter()
    count = 0
    for r, c in zip(rows.tolist(), cols.tolist(), strict=False):
        for ch in channels:
            if count >= nbits:
                return writer.value()
            writer.write_bit(arr[r, c, ch] & 1)
            count += 1
    return writer.value()


def _format_from_ext(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    return {"jpg": "jpeg"}.get(ext, ext) or "png"


def _order_from_password(width: int, height: int, password: str) -> np.ndarray:
    """Derive a deterministic permutation of pixel positions from ``password``."""
    import hashlib

    seed = int.from_bytes(hashlib.sha256(password.encode("utf-8")).digest(), "big")
    rng = np.random.default_rng(seed)
    total = width * height
    perm = rng.permutation(total)
    rows = perm // width
    cols = perm % width
    return np.stack([rows, cols], axis=1)


def embed_lsb(cover: Path, stego: Path, payload: bytes) -> HideResult:
    """Embed ``payload`` using sequential LSB."""
    if _format_from_ext(cover) not in LOSSLESS_FORMATS:
        raise UnsupportedFormatError(f"LSB embed requires lossless format, got {_format_from_ext(cover)}")
    cap = capacity_bytes(cover, strategy=Strategy.LSB)
    if len(payload) > cap:
        raise CapacityError(f"payload {len(payload)} exceeds capacity {cap}")
    _write_lsb(cover, stego, payload)
    return HideResult(
        cover_path=cover,
        stego_path=stego,
        strategy=Strategy.LSB,
        capacity_bytes=cap,
        payload_bytes=len(payload),
        encrypted=False,
        sha256="",
    )


def embed_randomized_lsb(cover: Path, stego: Path, payload: bytes, password: str) -> HideResult:
    """Embed ``payload`` using PRNG-ordered LSB keyed by ``password``."""
    if _format_from_ext(cover) not in LOSSLESS_FORMATS:
        raise UnsupportedFormatError("randomized LSB requires lossless format")
    img = Image.open(cover)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    cap = capacity_bytes(cover, strategy=Strategy.RANDOMIZED_LSB)
    if len(payload) > cap:
        raise CapacityError(f"payload {len(payload)} exceeds capacity {cap}")
    order = _order_from_password(w, h, password)
    _write_lsb(cover, stego, payload, order=order)
    return HideResult(
        cover_path=cover,
        stego_path=stego,
        strategy=Strategy.RANDOMIZED_LSB,
        capacity_bytes=cap,
        payload_bytes=len(payload),
        encrypted=False,
        sha256="",
    )


def embed_password(cover: Path, stego: Path, payload: bytes, password: str) -> HideResult:
    """Embed ``payload`` using PRNG-ordered LSB with AES-GCM framing."""
    if _format_from_ext(cover) not in LOSSLESS_FORMATS:
        raise UnsupportedFormatError("password-embed requires lossless format")
    img = Image.open(cover)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    frame = encrypt_payload(payload, password=password.encode("utf-8"))
    cap = capacity_bytes(cover, strategy=Strategy.PASSWORD_EMBED)
    if len(frame) > cap:
        raise CapacityError(f"encrypted frame {len(frame)} exceeds capacity {cap}")
    order = _order_from_password(w, h, password)
    _write_lsb(cover, stego, frame, order=order)
    return HideResult(
        cover_path=cover,
        stego_path=stego,
        strategy=Strategy.PASSWORD_EMBED,
        capacity_bytes=cap,
        payload_bytes=len(frame),
        encrypted=True,
        sha256="",
    )


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------


def extract_lsb(stego: Path, payload_bytes: int) -> bytes:
    """Read ``payload_bytes`` from a sequential-LSB stego image."""
    nbits = payload_bytes * 8
    return _read_lsb(stego, nbits)


def extract_randomized_lsb(stego: Path, payload_bytes: int, password: str) -> bytes:
    """Read ``payload_bytes`` from a randomized-LSB stego image."""
    img = Image.open(stego)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    order = _order_from_password(w, h, password)
    return _read_lsb(stego, payload_bytes * 8, order=order)


def extract_password(stego: Path, password: str) -> bytes:
    """Read a password-encrypted frame and return the decrypted payload.

    The on-cover layout matches :func:`stegox.security.framing.encrypt_payload`:
    header (8) + salt (16) + nonce (12) + tag (16) + length_le (8) + ciphertext.
    """
    img = Image.open(stego)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    order = _order_from_password(w, h, password)
    # Read the full frame header (8) + salt (16) + nonce (12) + tag (16) + length (8) = 60 bytes
    prefix = _read_lsb(stego, 60 * 8, order=order)
    if len(prefix) < 60:
        raise IntegrityError("frame too short")
    # Length is the last 8 bytes of the prefix
    length = int.from_bytes(prefix[52:60], "big")
    ciphertext = _read_lsb(stego, (60 + length) * 8, order=order)[60:60 + length]
    frame = prefix + ciphertext
    return decrypt_payload(frame, password=password.encode("utf-8"))


# ---------------------------------------------------------------------------
# Dispatch helpers
# ---------------------------------------------------------------------------


def embed_image(cover: Path, payload: bytes, strategy: str, password: str | None = None,
                stego: Path | None = None) -> HideResult:
    """Dispatch an image embed to the appropriate strategy."""
    if stego is None:
        stego = cover.with_name(f"{cover.stem}.stegox{cover.suffix}")
    if strategy == Strategy.LSB:
        return embed_lsb(cover, stego, payload)
    if strategy == Strategy.LSB_RGB:
        return embed_lsb(cover, stego, payload)  # default uses RGB
    if strategy == Strategy.RANDOMIZED_LSB:
        if not password:
            raise ValueError("password required for randomized-lsb")
        return embed_randomized_lsb(cover, stego, payload, password)
    if strategy == Strategy.PASSWORD_EMBED:
        if not password:
            raise ValueError("password required for password-embed")
        return embed_password(cover, stego, payload, password)
    if strategy == Strategy.DCT_JPEG:
        return embed_dct(cover, stego, payload, password=password)
    raise UnsupportedFormatError(f"unknown strategy: {strategy}")


def extract_image(stego: Path, strategy: str, password: str | None = None,
                  payload_bytes: int | None = None) -> bytes:
    """Dispatch an image extract to the appropriate strategy."""
    if strategy == Strategy.LSB or strategy == Strategy.LSB_RGB:
        if payload_bytes is None:
            raise ValueError("payload_bytes is required for LSB extract")
        return extract_lsb(stego, payload_bytes)
    if strategy == Strategy.RANDOMIZED_LSB:
        if payload_bytes is None or not password:
            raise ValueError("payload_bytes and password required for randomized-lsb")
        return extract_randomized_lsb(stego, payload_bytes, password)
    if strategy == Strategy.PASSWORD_EMBED:
        if not password:
            raise ValueError("password required for password-embed")
        return extract_password(stego, password)
    if strategy == Strategy.DCT_JPEG:
        return extract_dct(stego, password=password)
    raise UnsupportedFormatError(f"unknown strategy: {strategy}")


# ---------------------------------------------------------------------------
# DCT (JPEG) embedder
# ---------------------------------------------------------------------------


def embed_dct(cover: Path, stego: Path, payload: bytes, *, password: str | None = None) -> HideResult:
    """Embed ``payload`` in the mid-frequency DCT coefficients of a JPEG."""
    try:
        from scipy.fft import dct, idct  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise UnsupportedFormatError("scipy is required for DCT embed") from exc
    if _format_from_ext(cover) != "jpeg":
        raise UnsupportedFormatError("DCT embed requires a JPEG cover")

    img = Image.open(cover).convert("L")
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape
    bits = list(BitReader(payload))
    bit_idx = 0
    block_size = 8
    for by in range(0, h - block_size + 1, block_size):
        for bx in range(0, w - block_size + 1, block_size):
            if bit_idx >= len(bits):
                break
            block = arr[by : by + 8, bx : bx + 8]
            d = dct(dct(block, axis=0, norm="ortho"), axis=1, norm="ortho")
            # Embed in coefficient (4, 4) and (4, 5)
            for (yy, xx) in ((4, 4), (4, 5)):
                if bit_idx >= len(bits):
                    break
                d[yy, xx] = (np.floor(d[yy, xx] / 2) * 2) + bits[bit_idx]
                bit_idx += 1
            new_block = idct(idct(d, axis=0, norm="ortho"), axis=1, norm="ortho")
            arr[by : by + 8, bx : bx + 8] = new_block
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out.save(stego, format="jpeg", quality=90)
    return HideResult(
        cover_path=cover,
        stego_path=stego,
        strategy=Strategy.DCT_JPEG,
        capacity_bytes=bit_idx // 8,
        payload_bytes=len(payload),
        encrypted=bool(password),
        sha256="",
    )


def extract_dct(stego: Path, *, password: str | None = None) -> bytes:
    """Recover a payload embedded by :func:`embed_dct`."""
    try:
        from scipy.fft import dct  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise UnsupportedFormatError("scipy is required for DCT extract") from exc
    img = Image.open(stego).convert("L")
    arr = np.array(img, dtype=np.float32)
    h, w = arr.shape
    writer = BitWriter()
    for by in range(0, h - 7, 8):
        for bx in range(0, w - 7, 8):
            block = arr[by : by + 8, bx : bx + 8]
            d = dct(dct(block, axis=0, norm="ortho"), axis=1, norm="ortho")
            writer.write_bit(int(abs(d[4, 4])) % 2)
            writer.write_bit(int(abs(d[4, 5])) % 2)
    return writer.value()
