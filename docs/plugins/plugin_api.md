# Plugin API Reference

## `stegox.plugins.spec.PluginSpec`

Fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | str | yes | Unique plugin name |
| `version` | str | yes | SemVer version |
| `author` | str | no | Author name |
| `license` | str | no | License identifier (default MIT) |
| `description` | str | no | Short description |
| `stability` | str | no | `experimental` / `stable` / `deprecated` |
| `permissions` | tuple[str] | no | `network`, `subprocess`, `filesystem` |
| `detectors` | tuple[type] | no | Subclasses of `Detector` |
| `embedders` | tuple[type] | no | Custom embedder classes |
| `extractors` | tuple[type] | no | Custom extractor classes |
| `formats` | tuple[type] | no | Custom format handlers |
| `report_renderers` | tuple[type] | no | Custom report renderers |

## `stegox.detectors.base.Detector`

Required class attributes:

- `id` (str) — unique detector id
- `name` (str) — human-readable name
- `version` (str) — semver version
- `media_type` (MediaType)
- `formats` (tuple[str])

Methods to override:

- `run(target: DetectionContext) -> DetectorResult`
- `applicable(target) -> bool` (default checks format and media_type)

## `stegox.detectors.base.make_indicator`

```python
make_indicator(
    id: str,
    name: str,
    verdict: str,           # "clean" | "suspicious" | "malicious"
    score: float,           # 0.0 - 1.0
    weight: float = 1.0,    # 0.0 - 1.5
    metrics: dict = None,
    description: str = "",
)
```
