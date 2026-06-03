"""Cryptographic primitives used by StegoX.

This package exposes:

- :mod:`stegox.security.crypto` — AES-256-GCM AEAD wrapper.
- :mod:`stegox.security.kdf` — password-based key derivation.
- :mod:`stegox.security.framing` — encrypted payload framing.
- :mod:`stegox.security.shred` — best-effort file shredding.
"""

from stegox.security.crypto import aead_decrypt, aead_encrypt
from stegox.security.framing import (
    FRAME_MAGIC,
    FRAME_VERSION,
    decrypt_payload,
    encrypt_payload,
)
from stegox.security.kdf import derive_key
from stegox.security.shred import secure_delete

__all__ = [
    "FRAME_MAGIC",
    "FRAME_VERSION",
    "aead_decrypt",
    "aead_encrypt",
    "decrypt_payload",
    "derive_key",
    "encrypt_payload",
    "secure_delete",
]
