"""Verify that CHANGELOG.md has an "Unreleased" section."""

from __future__ import annotations

import sys
from pathlib import Path

CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def main() -> int:
    if not CHANGELOG.exists():
        print("CHANGELOG.md missing", file=sys.stderr)
        return 1
    text = CHANGELOG.read_text(encoding="utf-8")
    if "## [Unreleased]" not in text:
        print("CHANGELOG.md missing [Unreleased] section", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
