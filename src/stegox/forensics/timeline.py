"""Timeline helpers.

The timeline orders chain-of-custody events for inclusion in a case
report.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from stegox.forensics.chain_of_custody import ChainOfCustody


@dataclass(slots=True)
class TimelineEvent:
    ts: datetime
    action: str
    target: str
    sha256: str
    operator: str


class Timeline:
    """Ordered list of timeline events."""

    def __init__(self, events: list[TimelineEvent] | None = None) -> None:
        self.events = events or []

    @classmethod
    def from_custody(cls, custody: ChainOfCustody) -> Timeline:
        events: list[TimelineEvent] = []
        for ev in custody.read():
            ts = datetime.fromisoformat(ev.ts)
            events.append(TimelineEvent(
                ts=ts, action=ev.action, target=ev.target,
                sha256=ev.sha256, operator=ev.operator,
            ))
        events.sort(key=lambda e: e.ts)
        return cls(events=events)


__all__ = ["Timeline", "TimelineEvent"]
