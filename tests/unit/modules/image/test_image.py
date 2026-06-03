"""Image module tests."""

from __future__ import annotations

import pytest

from stegox.core.errors import CapacityError
from stegox.modules.image import (
    embed_image,
    embed_lsb,
    embed_password,
    embed_randomized_lsb,
    extract_image,
    extract_lsb,
    extract_password,
    list_strategies,
)


def test_list_strategies() -> None:
    items = list_strategies()
    assert any(item["id"] == "lsb" for item in items)
    assert any(item["id"] == "password-embed" for item in items)


def test_lsb_round_trip(sample_png, tmp_path) -> None:
    payload = b"hello stego"
    out = tmp_path / "out.png"
    embed_lsb(sample_png, out, payload)
    assert out.exists()
    recovered = extract_lsb(out, len(payload))
    assert recovered == payload


def test_password_round_trip(sample_png, tmp_path) -> None:
    payload = b"top secret"
    out = tmp_path / "out.png"
    embed_password(sample_png, out, payload, password="hunter2")
    assert out.exists()
    recovered = extract_password(out, password="hunter2")
    assert recovered == payload


def test_randomized_lsb_round_trip(sample_png, tmp_path) -> None:
    payload = b"random payload"
    out = tmp_path / "out.png"
    embed_randomized_lsb(sample_png, out, payload, password="abc")
    from stegox.modules.image import extract_randomized_lsb
    recovered = extract_randomized_lsb(out, len(payload), password="abc")
    assert recovered == payload


def test_capacity_error(sample_png, tmp_path) -> None:
    out = tmp_path / "out.png"
    huge = b"\x00" * (10 * 1024 * 1024)
    with pytest.raises(CapacityError):
        embed_lsb(sample_png, out, huge)


def test_embed_image_dispatch(sample_png, tmp_path) -> None:
    out = tmp_path / "out.png"
    result = embed_image(sample_png, b"x", strategy="lsb", stego=out)
    assert result.payload_bytes == 1
    recovered = extract_image(out, strategy="lsb", payload_bytes=1)
    assert recovered == b"x"
