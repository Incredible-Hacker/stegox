"""Shared utility functions for StegoX.

This package contains:

- :mod:`stegox.utils.io` — safe filesystem helpers
- :mod:`stegox.utils.hashing` — multi-algorithm file hashing
- :mod:`stegox.utils.bitio` — bit packing/unpacking helpers
- :mod:`stegox.utils.progress` — progress reporting
- :mod:`stegox.utils.magic` — magic-byte file identification
"""

from stegox.utils.hashing import FileHashes, hash_file
from stegox.utils.io import atomic_write, read_bytes, safe_open
from stegox.utils.magic import MAGIC_SIGNATURES, identify_format

__all__ = [
    "MAGIC_SIGNATURES",
    "FileHashes",
    "atomic_write",
    "hash_file",
    "identify_format",
    "read_bytes",
    "safe_open",
]
