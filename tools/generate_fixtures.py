"""Generate fixture files for the StegoX test suite.

This script is invoked by maintainers; it is not part of the test
suite itself. It writes small, deterministic fixture files to
``tests/fixtures/``.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
IMG = FIX / "images"
AUD = FIX / "audio"
TXT = FIX / "text"
PAY = FIX / "payloads"


def make_png() -> None:
    IMG.mkdir(parents=True, exist_ok=True)
    arr = (np.random.default_rng(0).integers(0, 256, (128, 128, 3), dtype=np.uint8))
    Image.fromarray(arr).save(IMG / "sample.png")


def make_jpeg() -> None:
    arr = (np.random.default_rng(0).integers(0, 256, (128, 128, 3), dtype=np.uint8))
    Image.fromarray(arr).save(IMG / "sample.jpg", format="jpeg", quality=85)


def make_bmp() -> None:
    arr = (np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8))
    Image.fromarray(arr).save(IMG / "sample.bmp", format="bmp")


def make_tiff() -> None:
    arr = (np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8))
    Image.fromarray(arr).save(IMG / "sample.tiff", format="tiff")


def make_wav() -> None:
    AUD.mkdir(parents=True, exist_ok=True)
    sr = 16000
    samples = (np.random.default_rng(0).integers(-32768, 32767, sr, dtype=np.int16))
    with wave.open(str(AUD / "sample.wav"), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())


def make_text() -> None:
    TXT.mkdir(parents=True, exist_ok=True)
    (TXT / "sample.txt").write_text("The quick brown fox jumps over the lazy dog.\n", encoding="utf-8")
    (TXT / "sample.md").write_text("# Title\n\nA paragraph of text for analysis.\n", encoding="utf-8")


def make_payloads() -> None:
    PAY.mkdir(parents=True, exist_ok=True)
    (PAY / "small.txt").write_text("hello stegox\n", encoding="utf-8")
    (PAY / "binary.bin").write_bytes(bytes(range(256)) * 4)


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    make_png()
    make_jpeg()
    make_bmp()
    make_tiff()
    make_wav()
    make_text()
    make_payloads()
    print("fixtures written to", FIX)


if __name__ == "__main__":
    main()
