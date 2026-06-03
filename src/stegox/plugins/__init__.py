"""Plugin system for StegoX.

Plugins are discovered via Python entry points in the
``stegox.plugin`` group and via the drop-in directory at
``~/.config/stegox/plugins``. The system uses ``pluggy`` for hook
implementations and adds a StegoX-specific spec on top.
"""

from stegox.plugins.manager import PluginManager
from stegox.plugins.spec import PluginSpec

__all__ = ["PluginManager", "PluginSpec"]
