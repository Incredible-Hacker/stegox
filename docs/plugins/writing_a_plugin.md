# Writing a StegoX Plugin

StegoX plugins are regular Python packages that declare an entry
point in the `stegox.plugin` group.

## Minimal example

```python
# src/my_plugin/__init__.py
from stegox.detectors.base import Detector, make_indicator
from stegox.core.types import DetectionContext, DetectorResult
from stegox.core.constants import MediaType
from stegox.plugins.spec import PluginSpec

class MyDetector(Detector):
    id = "example.my"
    name = "My Detector"
    version = "0.1.0"
    media_type = MediaType.UNIVERSAL
    formats = ()
    weight = 0.5

    def run(self, target: DetectionContext) -> DetectorResult:
        with target.target_path.open("rb") as fh:
            head = fh.read(1024)
        if b"my-marker" in head:
            return DetectorResult(
                detector_id=self.id,
                detector_version=self.version,
                score=1.0,
                confidence=0.9,
                indicators=[make_indicator(
                    self.id, "My Marker", "suspicious", 1.0,
                    metrics={"offset": head.index(b"my-marker")},
                )],
            )
        return DetectorResult(
            detector_id=self.id,
            detector_version=self.version,
            score=0.0, confidence=0.0, indicators=[],
            notes="marker not present",
        )

def register() -> PluginSpec:
    return PluginSpec(
        name="my-plugin",
        version="0.1.0",
        author="Your Name",
        license="MIT",
        description="Example plugin",
        stability="experimental",
        permissions=(),
        detectors=(MyDetector,),
    )
```

```toml
# pyproject.toml
[project]
name = "stegox-plugin-my"
version = "0.1.0"
dependencies = ["stegox"]

[project.entry-points."stegox.plugin"]
my = "my_plugin:register"
```

Install with `pip install -e .` and the detector is auto-discovered.

## Permissions

If your plugin needs to make network calls, list `network` in
`permissions`. The plugin is only loaded if the user passes
`--allow-network`.
