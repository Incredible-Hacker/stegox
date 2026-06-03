"""StegoX version.

Version is sourced dynamically from VCS tags via ``hatch-vcs``.
For source-checkout builds without tags, a development fallback is used.
"""

from __future__ import annotations

__all__ = ["VERSION", "__version__"]

try:  # pragma: no cover - exercised by hatch-vcs
    from stegox._version import __version__  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - dev fallback
    __version__ = "0.1.0.dev0"

VERSION: tuple[int, int, int] = tuple(int(p) for p in __version__.split(".")[:3] if p.isdigit())  # type: ignore[assignment]
