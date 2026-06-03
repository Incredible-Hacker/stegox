# Architecture

StegoX follows a layered architecture with strict local-execution
boundaries. There is no service tier, no message queue, no database,
and no outbound network layer.

## Layers

1. **CLI surface** — `stegox.cli` parses arguments and dispatches commands.
2. **Command layer** — subcommands such as `image.hide` build engine calls.
3. **Engine** — `stegox.engine` orchestrates modules and detectors.
4. **Modules** — `stegox.modules.*` implement per-medium embed/extract.
5. **Detectors** — `stegox.detectors.*` are pluggable analysis callables.
6. **Reports** — `stegox.reports` renders results in console/JSON/HTML.
7. **Cross-cutting** — `stegox.security`, `stegox.forensics`,
   `stegox.plugins`, `stegox.core`.

## Architectural invariants

1. No outbound network under any code path.
2. No persistent state beyond the user's filesystem.
3. Deterministic CLI behavior.
4. Side-effect-free core; the engine owns filesystem writes.
5. Process isolation for long-running detectors.

## Data flow

### Hide

```
Payload -> compress -> AES-256-GCM -> frame -> embedder -> cover -> filesystem
```

### Detect

```
File -> identifier -> metadata audit -> universal detectors -> media detectors
     -> scoring engine -> risk classification -> report renderer
```

## Subsystems

- `stegox.core` — types, errors, config, logging
- `stegox.security` — crypto, framing, secure I/O
- `stegox.media` — format detection and adapters
- `stegox.modules` — embedders and extractors
- `stegox.detectors` — pluggable analysis framework
- `stegox.reports` — console/JSON/HTML rendering
- `stegox.forensics` — case management and chain of custody
- `stegox.plugins` — entry-point based extensibility
- `stegox.cli` — Typer-based command surface

## Dependency strategy

StegoX deliberately depends on a small set of widely-audited
libraries: `Pillow`, `numpy`, `soundfile`, `imageio`, `mutagen`,
`cryptography`, `typer`, `rich`, `pydantic`, `Jinja2`, `pluggy`.

Optional dependencies live under extras: `scipy` for advanced DSP,
`matplotlib` for plotting, `mkdocs`/`mkdocs-material` for the docs
site, and `atheris` for fuzzing.
