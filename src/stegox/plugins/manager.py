"""Plugin manager: discovers and registers plugins.

Two discovery mechanisms are supported:

1. Python entry points in the ``stegox.plugin`` group.
2. Drop-in modules in ``~/.config/stegox/plugins/``.

Each plugin's ``register()`` callable must return a
:class:`PluginSpec`. Detectors declared by the spec are added to the
:class:`DetectorRegistry`.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import sys
from collections.abc import Iterable
from dataclasses import dataclass

from stegox.core.config import Config
from stegox.core.logging import get_logger
from stegox.core.paths import user_plugin_dir
from stegox.detectors.registry import DetectorRegistry
from stegox.plugins.spec import PluginSpec

log = get_logger("plugins.manager")

ENTRY_POINT_GROUP = "stegox.plugin"


@dataclass(slots=True)
class LoadedPlugin:
    name: str
    version: str
    spec: PluginSpec
    origin: str  # "entry_point" or "drop_in"


class PluginManager:
    """Discover, load, and unload plugins."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self._loaded: dict[str, LoadedPlugin] = {}

    def discover(self) -> list[LoadedPlugin]:
        """Discover and load all plugins. Returns the list of loaded plugins."""
        for plugin in self._iter_entry_points():
            self._register(plugin)
        for plugin in self._iter_drop_in():
            self._register(plugin)
        return list(self._loaded.values())

    def _register(self, plugin: LoadedPlugin) -> None:
        if plugin.name in self._loaded:
            return
        if "network" in plugin.spec.permissions and not self.config.plugins_allow_network:
            log.warning(
                "plugin %s requests network permission but --allow-network is not set; skipping",
                plugin.name,
            )
            return
        for detector_cls in plugin.spec.detectors:
            try:
                instance = detector_cls()
            except Exception as exc:
                log.error("plugin %s detector %s failed to instantiate: %s", plugin.name, detector_cls, exc)
                continue
            try:
                DetectorRegistry.register(instance)
            except ValueError as exc:
                log.warning("plugin detector %s not registered: %s", instance.id, exc)
        self._loaded[plugin.name] = plugin
        log.info("loaded plugin %s v%s from %s", plugin.name, plugin.version, plugin.origin)

    def _iter_entry_points(self) -> Iterable[LoadedPlugin]:
        try:
            eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
        except Exception as exc:
            log.warning("entry point discovery failed: %s", exc)
            return
        for ep in eps:
            try:
                register = ep.load()
                spec_obj = register()
                if not isinstance(spec_obj, PluginSpec):
                    raise TypeError(f"{ep.name} register() did not return PluginSpec")
                yield LoadedPlugin(name=spec_obj.name, version=spec_obj.version, spec=spec_obj, origin=f"entry_point:{ep.name}")
            except Exception as exc:
                log.error("failed to load plugin %s: %s", ep.name, exc)

    def _iter_drop_in(self) -> Iterable[LoadedPlugin]:
        drop_dir = user_plugin_dir()
        if not drop_dir.exists():
            return
        for path in sorted(drop_dir.glob("*.py")):
            try:
                spec = importlib.util.spec_from_file_location(f"stegox_drop_in_{path.stem}", path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                if not hasattr(module, "register"):
                    log.warning("drop-in %s has no register()", path.name)
                    continue
                spec_obj = module.register()
                if not isinstance(spec_obj, PluginSpec):
                    raise TypeError(f"{path.name} register() did not return PluginSpec")
                yield LoadedPlugin(
                    name=spec_obj.name,
                    version=spec_obj.version,
                    spec=spec_obj,
                    origin=f"drop_in:{path.name}",
                )
            except Exception as exc:
                log.error("drop-in plugin %s failed: %s", path.name, exc)

    def unload(self, name: str) -> None:
        plugin = self._loaded.pop(name, None)
        if not plugin:
            return
        for det_cls in plugin.spec.detectors:
            try:
                instance = det_cls()
            except Exception:
                continue
            DetectorRegistry.unregister(instance.id)
        log.info("unloaded plugin %s", name)

    def list(self) -> list[LoadedPlugin]:
        return list(self._loaded.values())


__all__ = ["ENTRY_POINT_GROUP", "LoadedPlugin", "PluginManager"]
