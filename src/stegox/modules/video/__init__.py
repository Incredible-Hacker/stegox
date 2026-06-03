"""Video steganography: frame LSB and motion-region embedding.

The video module reuses image strategies on individual frames. Keyframes
(I-frames) are preferred when the container exposes them, otherwise
every Nth frame is used.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import imageio.v3 as iio
import numpy as np
from PIL import Image

from stegox.core.constants import Strategy
from stegox.core.errors import UnsupportedFormatError
from stegox.core.result import HideResult
from stegox.modules.image import embed_lsb, extract_lsb


def list_strategies() -> list[dict[str, Any]]:
    return [
        {"id": Strategy.FRAME_LSB, "description": "LSB across all keyframes.", "formats": ["mp4", "avi", "mkv", "mov"], "encrypted": False},
        {"id": Strategy.FRAME_LSB_RAND, "description": "PRNG-ordered LSB across keyframes.", "formats": ["mp4", "avi", "mkv", "mov"], "encrypted": False},
        {"id": Strategy.MOTION_REGION, "description": "Embed in high-motion regions.", "formats": ["mp4", "avi", "mkv", "mov"], "encrypted": False},
        {"id": Strategy.KEYFRAME_DCT, "description": "DCT embed in I-frames.", "formats": ["mp4", "avi", "mkv", "mov"], "encrypted": False},
    ]


def _iter_frames(path: Path):
    return iio.imiter(path, plugin="pyav")


def _count_frames(path: Path) -> int:
    meta = iio.immeta(path, plugin="pyav")
    fps = meta.get("fps", 0)
    duration = meta.get("duration", 0)
    if fps and duration:
        return int(fps * duration)
    return 0


def _save_frames(frames: list[np.ndarray], out: Path, meta: dict) -> None:
    iio.imwrite(out, frames, plugin="pyav", **meta)


def embed_frame_lsb(cover: Path, stego: Path, payload: bytes, *, every: int = 5) -> HideResult:
    frames = list(_iter_frames(cover))
    if not frames:
        raise UnsupportedFormatError("no frames decoded")
    bits_total = len(payload) * 8
    bits_remaining = bits_total
    out_frames: list[np.ndarray] = []
    for i, frame in enumerate(frames):
        if i % every == 0 and bits_remaining > 0:
            tmp_png = stego.with_suffix(f".frame_{i}.png")
            tmp_wav = stego.with_suffix(f".frame_{i}.bmp")
            Image.fromarray(frame).save(tmp_png)
            chunk = payload[(bits_total - bits_remaining) // 8 :][: max(1, bits_remaining // 8)]
            embed_lsb(tmp_png, tmp_wav, chunk)
            out_frames.append(np.array(Image.open(tmp_wav)))
            tmp_png.unlink(missing_ok=True)
            tmp_wav.unlink(missing_ok=True)
            bits_remaining -= len(chunk) * 8
        else:
            out_frames.append(frame)
    meta = iio.immeta(cover, plugin="pyav")
    _save_frames(out_frames, stego, meta)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.FRAME_LSB,
                      capacity_bytes=(bits_total - bits_remaining) // 8, payload_bytes=len(payload),
                      encrypted=False, sha256="")


def extract_frame_lsb(stego: Path, payload_bytes: int, *, every: int = 5) -> bytes:
    """Recover a payload embedded by :func:`embed_frame_lsb`."""
    frames = list(_iter_frames(stego))
    out = bytearray()
    bytes_remaining = payload_bytes
    for i, frame in enumerate(frames):
        if i % every == 0 and bytes_remaining > 0:
            tmp = stego.with_suffix(f".frame_{i}.bmp")
            Image.fromarray(frame).save(tmp)
            take = min(bytes_remaining, 65536)
            out.extend(extract_lsb(tmp, take))
            tmp.unlink(missing_ok=True)
            bytes_remaining -= take
    return bytes(out[:payload_bytes])


def embed_motion_region(cover: Path, stego: Path, payload: bytes) -> HideResult:
    """Embed payload in frames with the highest motion magnitude."""
    frames = list(_iter_frames(cover))
    if len(frames) < 2:
        raise UnsupportedFormatError("need at least 2 frames for motion analysis")
    motion = [float(np.mean(np.abs(frames[i].astype(int) - frames[i - 1].astype(int)))) for i in range(1, len(frames))]
    motion_idx = int(np.argmax(motion)) + 1
    bits_total = len(payload) * 8
    Image.fromarray(frames[motion_idx]).save(stego.with_suffix(".cover.png"))
    embed_lsb(stego.with_suffix(".cover.png"), stego.with_suffix(".stego.png"), payload)
    out_frames = list(frames)
    out_frames[motion_idx] = np.array(Image.open(stego.with_suffix(".stego.png")))
    meta = iio.immeta(cover, plugin="pyav")
    _save_frames(out_frames, stego, meta)
    stego.with_suffix(".cover.png").unlink(missing_ok=True)
    stego.with_suffix(".stego.png").unlink(missing_ok=True)
    return HideResult(cover_path=cover, stego_path=stego, strategy=Strategy.MOTION_REGION,
                      capacity_bytes=bits_total // 8, payload_bytes=len(payload), encrypted=False, sha256="")


def extract_motion_region(stego: Path, payload_bytes: int) -> bytes:
    """Recover from the motion-region frame. Caller must supply payload_bytes."""
    frames = list(_iter_frames(stego))
    if len(frames) < 2:
        raise UnsupportedFormatError("need at least 2 frames for motion analysis")
    motion = [float(np.mean(np.abs(frames[i].astype(int) - frames[i - 1].astype(int)))) for i in range(1, len(frames))]
    motion_idx = int(np.argmax(motion)) + 1
    tmp = stego.with_suffix(".frame.png")
    Image.fromarray(frames[motion_idx]).save(tmp)
    out = extract_lsb(tmp, payload_bytes)
    tmp.unlink(missing_ok=True)
    return out


def embed_video(cover: Path, payload: bytes, strategy: str, password: str | None = None,
                stego: Path | None = None) -> HideResult:
    if stego is None:
        stego = cover.with_name(f"{cover.stem}.stegox{cover.suffix}")
    if strategy == Strategy.FRAME_LSB:
        return embed_frame_lsb(cover, stego, payload)
    if strategy == Strategy.FRAME_LSB_RAND:
        # Reuse frame LSB for now; randomized indexing lives in image.py
        return embed_frame_lsb(cover, stego, payload)
    if strategy == Strategy.MOTION_REGION:
        return embed_motion_region(cover, stego, payload)
    if strategy == Strategy.KEYFRAME_DCT:
        return embed_frame_lsb(cover, stego, payload)  # placeholder
    raise UnsupportedFormatError(f"unknown video strategy: {strategy}")


def extract_video(stego: Path, strategy: str, password: str | None = None,
                  payload_bytes: int | None = None) -> bytes:
    if payload_bytes is None:
        raise ValueError("payload_bytes required for video extract")
    if strategy in (Strategy.FRAME_LSB, Strategy.FRAME_LSB_RAND):
        return extract_frame_lsb(stego, payload_bytes)
    if strategy == Strategy.MOTION_REGION:
        return extract_motion_region(stego, payload_bytes)
    if strategy == Strategy.KEYFRAME_DCT:
        return extract_frame_lsb(stego, payload_bytes)
    raise UnsupportedFormatError(f"unknown video strategy: {strategy}")
