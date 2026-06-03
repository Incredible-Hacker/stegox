"""Structured logging with secret redaction and audit log support.

The logger emits human-readable text to stderr by default, with optional
JSON output. Sensitive fields (anything named like ``password``, ``token``,
``key``, or ``secret``) are redacted automatically.
"""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

REDACT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(?P<key>password|passphrase|token|api[_-]?key|secret)\s*[:=]\s*(?P<val>\S+)"),
)


class RedactingFormatter(logging.Formatter):
    """Log formatter that masks common secret field names."""

    REDACTED: ClassVar[str] = "***REDACTED***"

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        if not isinstance(message, str):
            message = str(message)
        for pattern in REDACT_PATTERNS:
            message = pattern.sub(lambda m: f"{m.group('key')}: {self.REDACTED}", message)
        return message


class JsonFormatter(logging.Formatter):
    """Log formatter that emits one JSON object per record."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        text = json.dumps(payload, ensure_ascii=False)
        for pattern in REDACT_PATTERNS:
            text = pattern.sub(lambda m: f"{m.group('key')}: ***", text)
        return text


_configured = False


def configure_logging(
    level: str = "info",
    log_file: Path | None = None,
    json_logs: bool = False,
    quiet: bool = False,
) -> None:
    """Configure the root ``stegox`` logger.

    Idempotent. Subsequent calls adjust the level and add or remove the
    file handler.
    """
    global _configured
    logger = logging.getLogger("stegox")
    if quiet:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(level.upper())

    # Reset handlers on every call to reflect the latest config
    for h in list(logger.handlers):
        logger.removeHandler(h)

    stream = logging.StreamHandler(stream=sys.stderr)
    if json_logs:
        stream.setFormatter(JsonFormatter())
    else:
        stream.setFormatter(
            RedactingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
    logger.addHandler(stream)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(RedactingFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(fh)

    if not _configured:
        logger.propagate = False
        _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a child logger of the ``stegox`` namespace."""
    return logging.getLogger(f"stegox.{name}")


__all__ = [
    "JsonFormatter",
    "RedactingFormatter",
    "configure_logging",
    "get_logger",
]
