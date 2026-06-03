"""Password-based key derivation.

Default policy: Argon2id with conservative parameters. scrypt and
PBKDF2-HMAC-SHA256 are supported as portable fallbacks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from stegox.security.crypto import KEY_BYTES

SALT_BYTES = 16


@dataclass(frozen=True, slots=True)
class KDFParams:
    """Resolved KDF parameters."""

    name: str
    salt: bytes
    time_cost: int
    memory_cost: int
    parallelism: int


def _derive_argon2id(password: bytes, salt: bytes, t: int, m: int, p: int) -> bytes:
    try:
        import argon2.low_level as _al  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "argon2-cffi is required for Argon2id; install 'argon2-cffi' or "
            "use kdf='scrypt' or kdf='pbkdf2'."
        ) from exc
    hash_fn = getattr(_al, "hash_secret_raw", None) or getattr(_al, "hash_raw", None)
    if hash_fn is None:  # pragma: no cover - extreme old version
        raise RuntimeError(
            "argon2-cffi is too old; upgrade or use kdf='scrypt' or kdf='pbkdf2'."
        )
    # Newer API uses kwarg 'secret'; older API used 'password'.
    try:
        return hash_fn(  # type: ignore[call-arg]
            secret=password, salt=salt, time_cost=t, memory_cost=m,
            parallelism=p, hash_len=KEY_BYTES, type=_al.Type.ID,
        )
    except TypeError:
        return hash_fn(  # type: ignore[call-arg]
            password=password, salt=salt, time_cost=t, memory_cost=m,
            parallelism=p, hash_len=KEY_BYTES, type=_al.Type.ID,
        )


def _derive_scrypt(password: bytes, salt: bytes, n: int, r: int, p: int) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_BYTES, n=n, r=r, p=p)
    return kdf.derive(password)


def _derive_pbkdf2(password: bytes, salt: bytes, iters: int) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=KEY_BYTES, salt=salt, iterations=iters)
    return kdf.derive(password)


def derive_key(
    password: bytes,
    *,
    algo: str = "argon2id",
    salt: bytes | None = None,
    time_cost: int = 3,
    memory_cost: int = 64 * 1024,
    parallelism: int = 1,
) -> tuple[bytes, KDFParams]:
    """Derive a 32-byte key from ``password`` using the requested KDF.

    Returns ``(key, params)`` so callers can persist the salt and
    parameter set alongside the ciphertext.
    """
    salt_bytes = salt if salt is not None else os.urandom(SALT_BYTES)
    if len(salt_bytes) != SALT_BYTES:
        raise ValueError(f"salt must be {SALT_BYTES} bytes")
    algo_norm = algo.lower()
    if algo_norm == "argon2id":
        key = _derive_argon2id(password, salt_bytes, time_cost, memory_cost, parallelism)
    elif algo_norm == "scrypt":
        # Approximate Argon2 memory into scrypt N
        n = max(2**15, memory_cost * 2)
        key = _derive_scrypt(password, salt_bytes, n=n, r=8, p=parallelism)
    elif algo_norm == "pbkdf2":
        iters = max(100_000, time_cost * 100_000)
        key = _derive_pbkdf2(password, salt_bytes, iters)
    else:
        raise ValueError(f"unknown kdf: {algo!r}")
    return key, KDFParams(
        name=algo_norm,
        salt=salt_bytes,
        time_cost=time_cost,
        memory_cost=memory_cost,
        parallelism=parallelism,
    )


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time byte comparison wrapper around ``hmac.compare_digest``."""
    import hmac
    return hmac.compare_digest(a, b)


__all__ = [
    "SALT_BYTES",
    "KDFParams",
    "constant_time_compare",
    "derive_key",
]
