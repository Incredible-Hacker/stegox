"""AEAD wrapper around AES-256-GCM.

This module is intentionally thin. Callers must supply a 32-byte key
(typically obtained from :mod:`stegox.security.kdf`) and a 12-byte nonce.
The 16-byte authentication tag is appended to the ciphertext and is
validated on decryption; any tampering raises :class:`IntegrityError`.
"""

from __future__ import annotations

import os
from typing import Final

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from stegox.core.errors import IntegrityError

NONCE_BYTES: Final[int] = 12
KEY_BYTES: Final[int] = 32
TAG_BYTES: Final[int] = 16


def aead_encrypt(key: bytes, plaintext: bytes, *, aad: bytes | None = None) -> tuple[bytes, bytes]:
    """Encrypt ``plaintext`` with AES-256-GCM.

    Returns ``(nonce, ciphertext_with_tag)``. The nonce is freshly
    generated from the OS CSPRNG and must be persisted alongside the
    ciphertext.
    """
    if len(key) != KEY_BYTES:
        raise ValueError(f"key must be {KEY_BYTES} bytes, got {len(key)}")
    nonce = os.urandom(NONCE_BYTES)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ct


def aead_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, *, aad: bytes | None = None) -> bytes:
    """Decrypt and verify ``ciphertext`` using AES-256-GCM.

    Raises :class:`IntegrityError` if the authentication tag is invalid
    or the nonce is the wrong size.
    """
    if len(key) != KEY_BYTES:
        raise ValueError(f"key must be {KEY_BYTES} bytes, got {len(key)}")
    if len(nonce) != NONCE_BYTES:
        raise IntegrityError(f"nonce must be {NONCE_BYTES} bytes, got {len(nonce)}")
    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, aad)
    except Exception as exc:  # cryptography raises InvalidTag
        raise IntegrityError("authentication failed: data may be tampered") from exc


__all__ = ["KEY_BYTES", "NONCE_BYTES", "TAG_BYTES", "aead_decrypt", "aead_encrypt"]
