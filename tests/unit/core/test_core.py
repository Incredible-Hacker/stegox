"""Tests for ``stegox.core``."""

from __future__ import annotations

import json

import pytest

from stegox.core.config import Config, load_config
from stegox.core.constants import MediaType, RiskClass
from stegox.core.errors import (
    CapacityError,
    IntegrityError,
    StegoXError,
    UnsupportedFormatError,
)
from stegox.core.logging import configure_logging, get_logger
from stegox.core.paths import user_cache_dir, user_config_dir


def test_stegox_error_subclass_exit_codes() -> None:
    assert CapacityError("x").exit_code == 4
    assert UnsupportedFormatError("x").exit_code == 4
    assert IntegrityError("x").exit_code == 5


def test_config_default() -> None:
    cfg = Config()
    assert cfg.scoring.low_threshold == 30
    assert cfg.crypto.kdf == "argon2id"


def test_load_config_missing(tmp_path, monkeypatch) -> None:
    # Use a non-existent path to trigger defaults
    cfg = load_config(tmp_path / "nope.yaml")
    assert isinstance(cfg, Config)
    assert cfg.crypto.cipher == "aes-256-gcm"


def test_logger_redacts_passwords(capsys) -> None:
    configure_logging(level="info", quiet=False)
    log = get_logger("test")
    log.info("user password=hunter2 login")
    captured = capsys.readouterr()
    assert "hunter2" not in captured.err
    assert "REDACTED" in captured.err or "***" in captured.err


def test_paths_creates_dirs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg_config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg_cache"))
    cfg_dir = user_config_dir()
    cache_dir = user_cache_dir()
    assert cfg_dir.exists()
    assert cache_dir.exists()
