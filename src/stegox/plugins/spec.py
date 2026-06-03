"""PluginSpec and related data classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    pass


@dataclass
class PluginSpec:
    """Descriptor returned by a plugin's register() callable."""

    name: str
    version: str
    author: str = ""
    license: str = "MIT"
    description: str = ""
    stability: str = "experimental"  # experimental | stable | deprecated
    permissions: tuple[str, ...] = ()  # network, subprocess, filesystem
    detectors: tuple[type, ...] = field(default_factory=tuple)
    embedders: tuple[type, ...] = field(default_factory=tuple)
    extractors: tuple[type, ...] = field(default_factory=tuple)
    formats: tuple[type, ...] = field(default_factory=tuple)
    report_renderers: tuple[type, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("PluginSpec.name is required")
        if not self.version:
            raise ValueError("PluginSpec.version is required")
        if self.stability not in {"experimental", "stable", "deprecated"}:
            raise ValueError(f"invalid stability: {self.stability}")
        for perm in self.permissions:
            if perm not in {"network", "subprocess", "filesystem"}:
                raise ValueError(f"unknown permission: {perm}")


__all__ = ["PluginSpec"]
