"""Audio steganography: PCM LSB, echo hiding, phase coding."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import soundfile

from stegox.core.constants import Strategy
from stegox.core.errors import CapacityError, UnsupportedFormatError
from stegox.core.result import HideResult
from stegox.utils.bitio import BitReader, BitWriter
from stegox.utils.io import atomic_write

LOSSLESS_FORMATS: frozenset[str] = frozenset({"wav", "flac"})


def list_strategies():
    return [
        {"id": Strategy.PCM_LSB, "description": "Sequential LSB on PCM samples.", "formats": sorted(LOSSLESS_FORMATS), "encrypted": False},
        {"id": Strategy.PCM_LSB_RAND, "description": "PRNG-ordered LSB on PCM samples.", "formats": sorted(LOSSLESS_FORMATS), "encrypted": False},
        {"id": Strategy.ECHO_HIDING, "description": "Echo kernel modulation.", "formats": sorted(LOSSLESS_FORMATS), "encrypted": False},
        {"id": Strategy.PHASE_CODING, "description": "Phase spectrum embedding.", "formats": sorted(LOSSLESS_FORMATS), "encrypted": False},
    ]


def _read_pcm(cover: Path) -> tuple[np.ndarray, int]:
    data, sr = soundfile.read(cover, dtype="int16", always_2d=False)
    return data, sr


def _write_pcm(stego: Path, data: np.ndarray, sr: int) -> None:
    atomic_write(stego, b"")  # ensure parent exists
    soundfile.write(stego, data, sr, subtype="PCM_16")


def capacity_bytes(cover: Path) -> int:
    data, _ = _read_pcm(cover)
    n = data.size
    if data.dtype == np.int16:
        return max(0, n // 8 - 64)
    return max(0, n // 8 - 64)


# ---------------------------------------------------------------------------
# PCM LSB
# ---------------------------------------------------------------------------


def embed_pcm_lsb(cover: Path, stego: Path, payload: bytes) -> HideResult:
    data, sr = _read_pcm(cover)
    cap = capacity_bytes(cover)
    if len(payload) > cap:
        raise CapacityError(f"payload {len(payload)} > capacity {cap}")
    flat = data.flatten()
    bits = BitReader(payload)
    out = flat.copy()
    for i in range(len(out)):
        try:
            bit = next(bits)
        except StopIteration:
            break
        out[i] = (out[i] & ~np.int16(1)) | np.int16(bit)
    out = out.reshape(data.shape)
    _write_pcm(stego, out, sr)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PCM_LSB,
                      capacity_bytes=cap, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_pcm_lsb(stego: Path, nbits: int) -> bytes:
    data, _ = _read_pcm(stego)
    flat = data.flatten()
    writer = BitWriter()
    for i in range(min(len(flat), (nbits + 7) // 8 * 8)):
        writer.write_bit(int(flat[i]) & 1)
        if writer.__len__() >= nbits:
            break
    return writer.value()


def embed_pcm_lsb_rand(cover: Path, stego: Path, payload: bytes, password: str) -> HideResult:
    import hashlib
    data, sr = _read_pcm(cover)
    cap = capacity_bytes(cover)
    if len(payload) > cap:
        raise CapacityError(f"payload {len(payload)} > capacity {cap}")
    flat = data.flatten()
    seed = int.from_bytes(hashlib.sha256(password.encode()).digest(), "big")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(flat))
    bits = BitReader(payload)
    out = flat.copy()
    for idx in perm:
        try:
            bit = next(bits)
        except StopIteration:
            break
        out[idx] = (out[idx] & ~np.int16(1)) | np.int16(bit)
    out = out.reshape(data.shape)
    _write_pcm(stego, out, sr)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PCM_LSB_RAND,
                      capacity_bytes=cap, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_pcm_lsb_rand(stego: Path, nbits: int, password: str) -> bytes:
    import hashlib
    data, _ = _read_pcm(stego)
    flat = data.flatten()
    seed = int.from_bytes(hashlib.sha256(password.encode()).digest(), "big")
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(flat))
    writer = BitWriter()
    for count, idx in enumerate(perm):
        if count >= nbits:
            break
        writer.write_bit(int(flat[idx]) & 1)
    return writer.value()


# ---------------------------------------------------------------------------
# Echo hiding
# ---------------------------------------------------------------------------


def embed_echo(cover: Path, stego: Path, payload: bytes, *, delay: int = 200, decay: float = 0.5) -> HideResult:
    data, sr = _read_pcm(cover)
    flat = data.astype(np.float32) / 32768.0
    out = flat.copy()
    bit_idx = 0
    bits = list(BitReader(payload))
    segment = sr // 10  # 100 ms per bit
    pos = 0
    while pos + segment < len(out) and bit_idx < len(bits):
        bit = bits[bit_idx]
        bit_idx += 1
        for i in range(pos + delay, min(pos + segment, len(out))):
            out[i] += decay * (out[i - delay] if i - delay >= 0 else 0.0) * (1 if bit else 0)
        pos += segment
    out = np.clip(out * 32768.0, -32768, 32767).astype(np.int16).reshape(data.shape)
    _write_pcm(stego, out, sr)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.ECHO_HIDING,
                      capacity_bytes=bit_idx, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_echo(stego: Path, nbits: int, *, delay: int = 200) -> bytes:
    data, sr = _read_pcm(stego)
    flat = data.astype(np.float32) / 32768.0
    writer = BitWriter()
    segment = sr // 10
    pos = 0
    while pos + segment < len(flat) and writer.__len__() < nbits:
        seg = flat[pos : pos + segment]
        if len(seg) <= delay:
            break
        ref = seg[:-delay]
        delayed = seg[delay:]
        corr = np.corrcoef(ref, delayed)[0, 1] if ref.std() and delayed.std() else 0.0
        writer.write_bit(1 if corr > 0.3 else 0)
        pos += segment
    return writer.value()


# ---------------------------------------------------------------------------
# Phase coding
# ---------------------------------------------------------------------------


def embed_phase(cover: Path, stego: Path, payload: bytes) -> HideResult:
    data, sr = _read_pcm(cover)
    flat = data.astype(np.float32) / 32768.0
    spectrum = np.fft.rfft(flat)
    magnitude = np.abs(spectrum)
    phase = np.angle(spectrum)
    bits = list(BitReader(payload))
    n = min(len(phase) - 1, len(bits))
    # Embed bit by setting a phase difference of pi (0) or 0 (1)
    for i in range(1, n + 1):
        phase[i] = 0.0 if bits[i - 1] else math.pi
    new_spectrum = magnitude * np.exp(1j * phase)
    out = np.fft.irfft(new_spectrum, n=len(flat))
    out = np.clip(out * 32768.0, -32768, 32767).astype(np.int16).reshape(data.shape)
    _write_pcm(stego, out, sr)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.PHASE_CODING,
                      capacity_bytes=n, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_phase(stego: Path, nbits: int) -> bytes:
    data, _sr = _read_pcm(stego)
    flat = data.astype(np.float32) / 32768.0
    spectrum = np.fft.rfft(flat)
    phase = np.angle(spectrum)
    writer = BitWriter()
    for i in range(1, min(len(phase), nbits + 1)):
        # Map to bit by looking at |phase|
        p = abs(phase[i]) % math.pi
        writer.write_bit(0 if p > math.pi / 2 else 1)
    return writer.value()


# ---------------------------------------------------------------------------
# Dispatch helpers
# ---------------------------------------------------------------------------


def embed_audio(cover: Path, payload: bytes, strategy: str, password: str | None = None,
                stego: Path | None = None, **kwargs) -> HideResult:
    if stego is None:
        stego = cover.with_name(f"{cover.stem}.stegox{cover.suffix}")
    if strategy == Strategy.PCM_LSB:
        return embed_pcm_lsb(cover, stego, payload)
    if strategy == Strategy.PCM_LSB_RAND:
        if not password:
            raise ValueError("password required for pcm-lsb-rand")
        return embed_pcm_lsb_rand(cover, stego, payload, password)
    if strategy == Strategy.ECHO_HIDING:
        return embed_echo(cover, stego, payload, **{"delay": kwargs.get("delay", 200), "decay": kwargs.get("decay", 0.5)})
    if strategy == Strategy.PHASE_CODING:
        return embed_phase(cover, stego, payload)
    raise UnsupportedFormatError(f"unknown audio strategy: {strategy}")


def extract_audio(stego: Path, strategy: str, password: str | None = None,
                  payload_bytes: int | None = None, **kwargs) -> bytes:
    if payload_bytes is None:
        raise ValueError("payload_bytes required for audio extract")
    nbits = payload_bytes * 8
    if strategy == Strategy.PCM_LSB:
        return extract_pcm_lsb(stego, nbits)
    if strategy == Strategy.PCM_LSB_RAND:
        if not password:
            raise ValueError("password required for pcm-lsb-rand")
        return extract_pcm_lsb_rand(stego, nbits, password)
    if strategy == Strategy.ECHO_HIDING:
        return extract_echo(stego, nbits, delay=kwargs.get("delay", 200))
    if strategy == Strategy.PHASE_CODING:
        return extract_phase(stego, nbits)
    raise UnsupportedFormatError(f"unknown audio strategy: {strategy}")
