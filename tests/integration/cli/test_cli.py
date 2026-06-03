"""End-to-end CLI tests using typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from stegox.cli.app import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "stegox" in result.stdout


def test_image_hide_extract(tmp_path: Path) -> None:
    # Create a cover
    from PIL import Image
    import numpy as np

    cover = tmp_path / "cover.png"
    arr = (np.random.default_rng(0).integers(0, 256, (128, 128, 3), dtype=np.uint8))
    Image.fromarray(arr).save(cover)
    payload = tmp_path / "payload.txt"
    payload.write_text("hello stegox")
    out = tmp_path / "stego.png"
    result = runner.invoke(app, [
        "image", "hide",
        "--cover", str(cover),
        "--payload", str(payload),
        "--out", str(out),
        "--strategy", "lsb",
    ])
    assert result.exit_code == 0
    assert out.exists()


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor", "run"])
    assert result.exit_code == 0
    assert "python_version" in result.stdout
