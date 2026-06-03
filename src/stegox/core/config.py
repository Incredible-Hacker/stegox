"""Configuration loading and defaults.

The configuration is a Pydantic model that can be loaded from a YAML
file. Sensible defaults ensure ``stegox`` works out of the box.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from stegox.core.errors import ConfigError
from stegox.core.paths import default_config_path

DEFAULT_DETECTOR_WEIGHTS: dict[str, float] = {
    "image.lsb_distribution": 0.7,
    "image.chi_square": 1.0,
    "image.rs_analysis": 1.0,
    "image.histogram": 0.5,
    "image.entropy": 0.4,
    "image.dct_analysis": 0.9,
    "audio.spectrogram": 0.6,
    "audio.noise_floor": 0.5,
    "audio.entropy_window": 0.4,
    "audio.echo_pattern": 0.9,
    "audio.bitplane": 0.7,
    "video.frame_diff": 0.5,
    "video.temporal_entropy": 0.5,
    "video.keyframe": 0.6,
    "video.frame_bitplane": 0.6,
    "text.zero_width_scan": 1.0,
    "text.unicode_anomaly": 0.8,
    "text.whitespace_pattern": 0.6,
    "universal.entropy": 0.4,
    "universal.signature": 1.0,
    "universal.base64_scan": 0.6,
    "universal.hex_blob": 0.5,
    "universal.archive_scan": 0.9,
}


class ScoringConfig(BaseModel):
    """Detector weights and thresholds."""

    weights: dict[str, float] = Field(default_factory=lambda: dict(DEFAULT_DETECTOR_WEIGHTS))
    low_threshold: int = 30
    high_threshold: int = 60
    recency_window_days: int = 30


class CryptoConfig(BaseModel):
    """Crypto policy."""

    kdf: str = "argon2id"  # or "scrypt", "pbkdf2"
    kdf_time_cost: int = 3
    kdf_memory_cost: int = 64 * 1024  # 64 MiB
    kdf_parallelism: int = 1
    cipher: str = "aes-256-gcm"


class LoggingConfig(BaseModel):
    """Logging policy."""

    level: str = "info"
    file: Path | None = None
    redact_passwords: bool = True
    json_logs: bool = False


class Config(BaseModel):
    """Top-level user configuration."""

    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    crypto: CryptoConfig = Field(default_factory=CryptoConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    plugins_allow_network: bool = False
    default_output_format: str = "console"
    detector_timeout_seconds: float = 60.0


def load_config(path: Path | None = None) -> Config:
    """Load configuration from ``path`` or the default location.

    Missing files return :class:`Config` with built-in defaults; malformed
    files raise :class:`ConfigError`.
    """
    config_path = path or default_config_path()
    if not config_path.exists():
        return Config()
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            data: dict[str, Any] = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {config_path}: {exc}") from exc
    try:
        return Config.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError or similar
        raise ConfigError(f"Invalid configuration in {config_path}: {exc}") from exc


def save_config(config: Config, path: Path | None = None) -> Path:
    """Persist ``config`` to ``path`` (or default location)."""
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(config.model_dump(mode="json"), fh, sort_keys=False)
    return config_path


__all__ = [
    "DEFAULT_DETECTOR_WEIGHTS",
    "Config",
    "CryptoConfig",
    "LoggingConfig",
    "ScoringConfig",
    "load_config",
    "save_config",
]
