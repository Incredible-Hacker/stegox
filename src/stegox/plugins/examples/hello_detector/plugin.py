"""Hello detector example plugin.

This plugin is the canonical example referenced by the docs. It
flags any file that contains the bytes ``b"stegox-demo"`` near the
start. It is intentionally trivial so plugin authors can copy the
shape.
"""

from __future__ import annotations

from stegox.core.constants import MediaType
from stegox.core.types import DetectionContext, DetectorResult
from stegox.detectors.base import Detector, make_indicator
from stegox.plugins.spec import PluginSpec

PLUGIN_NAME = "hello-detector"
PLUGIN_VERSION = "0.1.0"


class HelloDetector(Detector):
    id = "example.hello"
    name = "Hello Detector (Example)"
    version = PLUGIN_VERSION
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.3

    def run(self, target: DetectionContext) -> DetectorResult:
        try:
            with target.target_path.open("rb") as fh:
                head = fh.read(64 * 1024)
        except OSError:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=0.0,
                confidence=0.0,
                indicators=[],
                notes="unable to read",
            )
        if b"stegox-demo" in head:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=1.0,
                confidence=0.9,
                indicators=[
                    make_indicator(
                        "hello",
                        "Demo marker found",
                        "suspicious",
                        1.0,
                        metrics={"offset": head.index(b"stegox-demo")},
                        description="The file contains the example marker 'stegox-demo'.",
                    )
                ],
            )
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=0.0,
            confidence=0.0,
            indicators=[],
            notes="marker not present",
        )


def register() -> PluginSpec:
    """Return the plugin spec; called by the plugin manager."""
    return PluginSpec(
        name=PLUGIN_NAME,
        version=PLUGIN_VERSION,
        author="StegoX Contributors",
        license="MIT",
        description="Example detector used in tests and documentation.",
        stability="experimental",
        permissions=(),
        detectors=(HelloDetector,),
    )


__all__ = ["PLUGIN_NAME", "PLUGIN_VERSION", "HelloDetector", "register"]
