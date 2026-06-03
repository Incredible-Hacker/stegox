"""Encrypted payload framing.

Defines the on-the-wire container used by ``password-embed`` and other
strategy pipelines:

    +---------+---------+--------+--------+--------+----------+-----------+----------+
    | Magic   | Version | Flags  | Salt   | Nonce  | Tag Len  | Tag       | LengthLE |
    | 4B      | 1B      | 1B     | 16B    | 12B    | 1B (16)  | 16B       | 8B       |
    +---------+---------+--------+--------+--------+----------+-----------+----------+
    | Ciphertext + LengthLE bytes                                                       |
    +-----------------------------------------------------------------------------------+

The version is bumped only on breaking changes to the frame layout.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from enum import IntFlag
from typing import Final

from stegox.core.errors import IntegrityError
from stegox.security.crypto import NONCE_BYTES, TAG_BYTES, aead_decrypt, aead_encrypt
from stegox.security.kdf import SALT_BYTES, derive_key

FRAME_MAGIC: Final[bytes] = b"STGX"
FRAME_VERSION: Final[int] = 1

FLAG_COMPRESSION_ZLIB: Final[int] = 1 << 0
FLAG_COMPRESSION_ZSTD: Final[int] = 1 << 1
FLAG_KDF_ARGON2: Final[int] = 1 << 2
FLAG_KDF_SCRYPT: Final[int] = 1 << 3
FLAG_KDF_PBKDF2: Final[int] = 1 << 4

HEADER_FMT: Final[str] = ">4sBBBB"  # magic, version, flags, tag_len, kdf_marker
# Followed by: salt (16) | nonce (12) | tag (tag_len) | length_le (8) | ciphertext (length_le)


class _Compression(IntFlag):
    NONE = 0
    ZLIB = FLAG_COMPRESSION_ZLIB
    ZSTD = FLAG_COMPRESSION_ZSTD


class _KdfAlgo(IntFlag):
    ARGON2 = FLAG_KDF_ARGON2
    SCRYPT = FLAG_KDF_SCRYPT
    PBKDF2 = FLAG_KDF_PBKDF2


@dataclass(frozen=True, slots=True)
class EncryptedFrame:
    """Decoded frame representation."""

    version: int
    compression: int
    kdf: str
    salt: bytes
    nonce: bytes
    tag: bytes
    ciphertext: bytes


def _detect_compression(zstd_module: object | None) -> int:
    if zstd_module is not None:
        return FLAG_COMPRESSION_ZSTD
    return FLAG_COMPRESSION_ZLIB


def _compress(data: bytes, algo: int) -> bytes:
    if algo & FLAG_COMPRESSION_ZSTD:
        import zstd  # type: ignore[import-not-found]

        return zstd.ZstdCompressor().compress(data)
    return zlib.compress(data, level=6)


def _decompress(data: bytes, algo: int) -> bytes:
    if algo & FLAG_COMPRESSION_ZSTD:
        import zstd  # type: ignore[import-not-found]

        return zstd.ZstdDecompressor().decompress(data)
    return zlib.decompress(data)


def _kdf_flag_from_name(name: str) -> int:
    return {
        "argon2id": FLAG_KDF_ARGON2,
        "scrypt": FLAG_KDF_SCRYPT,
        "pbkdf2": FLAG_KDF_PBKDF2,
    }[name]


def _kdf_name_from_flag(flag: int) -> str:
    if flag & FLAG_KDF_ARGON2:
        return "argon2id"
    if flag & FLAG_KDF_SCRYPT:
        return "scrypt"
    if flag & FLAG_KDF_PBKDF2:
        return "pbkdf2"
    raise IntegrityError(f"unknown kdf flag 0x{flag:02x}")


def encrypt_payload(
    plaintext: bytes,
    *,
    password: bytes | None = None,
    key: bytes | None = None,
    compress: bool = True,
    kdf: str = "argon2id",
) -> bytes:
    """Build a self-describing encrypted frame.

    Either ``password`` or a pre-derived ``key`` must be provided. If
    ``password`` is given, a fresh salt is generated and KDF parameters
    are encoded in the frame.
    """
    if password is None and key is None:
        raise ValueError("either password or key is required")

    body = _compress(plaintext, FLAG_COMPRESSION_ZLIB) if compress else plaintext
    compression_flag = FLAG_COMPRESSION_ZLIB if compress else 0

    if password is not None:
        derived_key, params = derive_key(password, algo=kdf)
        kdf_flag = _kdf_flag_from_name(params.name)
        salt = params.salt
    else:
        assert key is not None
        derived_key = key
        kdf_flag = 0
        salt = b"\x00" * SALT_BYTES

    nonce, ct_with_tag = aead_encrypt(derived_key, body)
    tag = ct_with_tag[-TAG_BYTES:]
    ciphertext = ct_with_tag[:-TAG_BYTES]

    flags = compression_flag | kdf_flag
    header = struct.pack(HEADER_FMT, FRAME_MAGIC, FRAME_VERSION, flags, TAG_BYTES, 0)
    length = struct.pack(">Q", len(ciphertext))
    return header + salt + nonce + tag + length + ciphertext


def decrypt_payload(frame: bytes, *, password: bytes | None = None, key: bytes | None = None) -> bytes:
    """Reverse of :func:`encrypt_payload`. Raises :class:`IntegrityError`
    on tampering or wrong password.
    """
    if len(frame) < 4 + 1 + 1 + 1 + 1 + SALT_BYTES + NONCE_BYTES + TAG_BYTES + 8:
        raise IntegrityError("frame too short")
    magic, version, flags, tag_len, _kdf_marker = struct.unpack(HEADER_FMT, frame[:8])
    if magic != FRAME_MAGIC:
        raise IntegrityError("bad magic; not a stegox frame")
    if version != FRAME_VERSION:
        raise IntegrityError(f"unsupported frame version: {version}")
    if tag_len != TAG_BYTES:
        raise IntegrityError(f"unexpected tag length: {tag_len}")

    offset = 8
    salt = frame[offset : offset + SALT_BYTES]
    offset += SALT_BYTES
    nonce = frame[offset : offset + NONCE_BYTES]
    offset += NONCE_BYTES
    tag = frame[offset : offset + tag_len]
    offset += tag_len
    (length,) = struct.unpack(">Q", frame[offset : offset + 8])
    offset += 8
    ciphertext = frame[offset : offset + length]
    if len(ciphertext) != length:
        raise IntegrityError("truncated ciphertext")

    if key is not None:
        derived_key = key
    else:
        if password is None:
            raise ValueError("either password or key is required")
        kdf_name = _kdf_name_from_flag(flags)
        derived_key, _ = derive_key(password, algo=kdf_name, salt=salt)

    body = aead_decrypt(derived_key, nonce, ciphertext + tag)

    if flags & (FLAG_COMPRESSION_ZLIB | FLAG_COMPRESSION_ZSTD):
        body = _decompress(body, flags)

    return body


__all__ = [
    "FRAME_MAGIC",
    "FRAME_VERSION",
    "EncryptedFrame",
    "decrypt_payload",
    "encrypt_payload",
]
