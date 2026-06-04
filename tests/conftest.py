"""Shared pytest fixtures for StegoX."""

from __future__ import annotations

import wave
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def tmp_workdir(tmp_path: Path) -> Path:
    """A clean working directory for each test."""
    d = tmp_path / "work"
    d.mkdir()
    return d


@pytest.fixture
def sample_png(tmp_path: Path) -> Path:
    """Create a 64x64 RGB PNG with random pixel data."""
    arr = (np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8))
    path = tmp_path / "sample.png"
    Image.fromarray(arr).save(path)
    return path


@pytest.fixture
def sample_jpeg(tmp_path: Path) -> Path:
    """Create a 64x64 JPEG."""
    arr = (np.random.default_rng(0).integers(0, 256, (64, 64, 3), dtype=np.uint8))
    path = tmp_path / "sample.jpg"
    Image.fromarray(arr).save(path, format="jpeg", quality=85)
    return path


@pytest.fixture
def sample_bmp(tmp_path: Path) -> Path:
    arr = (np.random.default_rng(0).integers(0, 256, (32, 32, 3), dtype=np.uint8))
    path = tmp_path / "sample.bmp"
    Image.fromarray(arr).save(path, format="bmp")
    return path


@pytest.fixture
def sample_tiff(tmp_path: Path) -> Path:
    arr = (np.random.default_rng(0).integers(0, 256, (32, 32, 3), dtype=np.uint8))
    path = tmp_path / "sample.tiff"
    Image.fromarray(arr).save(path, format="tiff")
    return path


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    """Create a 1-second 16-bit mono WAV with random samples."""
    sr = 16000
    samples = (np.random.default_rng(0).integers(-32768, 32767, sr, dtype=np.int16))
    path = tmp_path / "sample.wav"
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return path


@pytest.fixture
def sample_txt(tmp_path: Path) -> Path:
    path = tmp_path / "sample.txt"
    path.write_text("The quick brown fox jumps over the lazy dog.\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_md(tmp_path: Path) -> Path:
    path = tmp_path / "sample.md"
    path.write_text("# Title\n\nA paragraph of text for analysis.\n", encoding="utf-8")
    return path


@pytest.fixture
def sample_payload() -> bytes:
    """A small deterministic payload."""
    return b"StegoX payload marker: " + b"X" * 64


@pytest.fixture
def registry_setup() -> Iterator[None]:
    """Ensure the built-in detectors are registered before the test."""
    from stegox.detectors.registry import DetectorRegistry, register_builtin

    if not DetectorRegistry.ids():
        register_builtin()
    return
