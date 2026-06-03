"""Progress reporting helpers.

StegoX avoids third-party progress bars; this module provides a tiny
TUI-friendly spinner and percentage reporter that writes to stderr.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass, field

SPINNER_FRAMES: tuple[str, ...] = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


@dataclass
class ProgressBar:
    """Minimal progress reporter for long operations."""

    total: int
    label: str = ""
    stream=sys.stderr
    _start: float = field(default_factory=time.monotonic, init=False)
    _last: float = 0.0

    def __enter__(self) -> ProgressBar:
        self._start = time.monotonic()
        self._render(0)
        return self

    def __exit__(self, *exc: object) -> None:
        self._render(self.total)
        self.stream.write("\n")

    def update(self, value: int) -> None:
        now = time.monotonic()
        if now - self._last < 0.1 and value != self.total:
            return
        self._last = now
        self._render(value)

    def _render(self, value: int) -> None:
        pct = (value / self.total) * 100 if self.total else 100.0
        bar_len = 24
        filled = int(bar_len * value / self.total) if self.total else bar_len
        bar = "█" * filled + "·" * (bar_len - filled)
        elapsed = time.monotonic() - self._start
        self.stream.write(f"\r{self.label} |{bar}| {pct:5.1f}% {elapsed:5.1f}s")
        self.stream.flush()


def spinner(label: str, is_done: Callable[[], bool], *, interval: float = 0.1) -> None:
    """Display a spinner until ``is_done()`` returns True.

    Intended for use in a background thread or polling loop.
    """
    i = 0
    while not is_done():
        frame = SPINNER_FRAMES[i % len(SPINNER_FRAMES)]
        sys.stderr.write(f"\r{frame} {label}")
        sys.stderr.flush()
        time.sleep(interval)
        i += 1
    sys.stderr.write(f"\r✓ {label}\n")
    sys.stderr.flush()


__all__ = ["ProgressBar", "spinner"]
