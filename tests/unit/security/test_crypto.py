"""Tests for ``stegox.security``."""

from __future__ import annotations

import pytest

from stegox.core.errors import IntegrityError
from stegox.security.crypto import aead_decrypt, aead_encrypt
from stegox.security.framing import (
    FRAME_MAGIC,
    FRAME_VERSION,
    decrypt_payload,
    encrypt_payload,
)
from stegox.security.kdf import derive_key


def test_aead_round_trip() -> None:
    key = b"\x00" * 32
    nonce, ct = aead_encrypt(key, b"hello stegox")
    pt = aead_decrypt(key, nonce, ct)
    assert pt == b"hello stegox"


def test_aead_tamper_detection() -> None:
    key = b"\x01" * 32
    nonce, ct = aead_encrypt(key, b"hello")
    tampered = bytearray(ct)
    tampered[0] ^= 0xFF
    with pytest.raises(IntegrityError):
        aead_decrypt(key, nonce, bytes(tampered))


def test_framing_round_trip_with_password() -> None:
    payload = b"super secret payload"
    frame = encrypt_payload(payload, password=b"hunter2")
    assert frame.startswith(FRAME_MAGIC)
    assert frame[4] == FRAME_VERSION
    recovered = decrypt_payload(frame, password=b"hunter2")
    assert recovered == payload


def test_framing_wrong_password() -> None:
    frame = encrypt_payload(b"hello", password=b"correct")
    with pytest.raises(IntegrityError):
        decrypt_payload(frame, password=b"wrong")


def test_framing_short_frame() -> None:
    with pytest.raises(IntegrityError):
        decrypt_payload(b"STGX" + b"\x00" * 4)


def test_kdf_derive_key() -> None:
    key, params = derive_key(b"password", algo="pbkdf2")
    assert len(key) == 32
    assert params.name == "pbkdf2"
