"""Chain-of-custody helpers.

A chain-of-custody log is an append-only JSON-Lines file. The
:class:`ChainOfCustody` helper writes entries atomically.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CustodyEvent:
    ts: str
    operator: str
    action: str
    target: str
    sha256: str
    args: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 0


class ChainOfCustody:
    """Append-only custody log."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def append(self, event: CustodyEvent) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), ensure_ascii=False))
            fh.write("\n")

    def read(self) -> list[CustodyEvent]:
        events: list[CustodyEvent] = []
        if not self.path.exists():
            return events
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            events.append(CustodyEvent(**data))
        return events

    @staticmethod
    def now_event(operator: str, action: str, target: str, sha256: str,
                  *, args: dict[str, Any] | None = None, exit_code: int = 0) -> CustodyEvent:
        return CustodyEvent(
            ts=datetime.now(tz=timezone.utc).isoformat(),
            operator=operator,
            action=action,
            target=target,
            sha256=sha256,
            args=args or {},
            exit_code=exit_code,
        )


__all__ = ["ChainOfCustody", "CustodyEvent"]
