"""Hello detector example package."""

from stegox.plugins.examples.hello_detector.plugin import (
    PLUGIN_NAME,
    PLUGIN_VERSION,
    HelloDetector,
    register,
)

__all__ = ["PLUGIN_NAME", "PLUGIN_VERSION", "HelloDetector", "register"]
