# StegoX

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Incredible-Hacker/stegox/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![Lint](https://github.com/Incredible-Hacker/stegox/actions/workflows/lint.yml/badge.svg)](.github/workflows/lint.yml)
[![Security](https://github.com/Incredible-Hacker/stegox/actions/workflows/security.yml/badge.svg)](.github/workflows/security.yml)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type-checked: mypy](https://img.shields.io/badge/type--checked-mypy-blue.svg)](https://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)

> **One-line description:** A local-first, backendless, MIT-licensed CLI for hiding, finding, and reporting on steganographic payloads in images, audio, video, text, and metadata.

> **Tagline:** *Hide. Find. Report. — All on your machine.*

---

## Table of Contents

- [What is StegoX?](#what-is-stegox)
- [Why StegoX?](#why-stegox)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
  - [Hide a payload](#hide-a-payload)
  - [Extract a payload](#extract-a-payload)
  - [Run detectors](#run-detectors)
  - [Full analysis report](#full-analysis-report)
  - [DFIR case workflow](#dfir-case-workflow)
  - [Interactive menu](#interactive-menu)
- [Supported Media](#supported-media)
- [Strategies](#strategies)
- [Detectors](#detectors)
- [Reports](#reports)
- [Plugin Development](#plugin-development)
- [Architecture](#architecture)
- [Security Model](#security-model)
- [Testing & Quality](#testing--quality)
- [Performance](#performance)
- [Project Layout](#project-layout)
- [Documentation](#documentation)
- [Comparison with Other Tools](#comparison-with-other-tools)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Governance & RFCs](#governance--rfcs)
- [FAQ](#faq)
- [Citation](#citation)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## What is StegoX?

**StegoX** is an all-in-one, fully local, **backendless** toolkit for **steganography**, **steganalysis**, **digital forensics triage**, and **payload discovery**. It runs entirely on the analyst's machine. There is no server, no database, no cloud, and no telemetry. Every byte that goes in is the only byte that comes out, and every operation is hashed, logged, and reproducible.

It targets:

- **DFIR analysts & incident responders** who need fast, scriptable triage of suspicious artifacts.
- **Forensics students & researchers** who want a single, well-documented playground.
- **CTF players** who need quick hide/extract/detect across many formats.
- **Security engineers** building detection pipelines with reproducible, auditable outputs.
- **Tooling authors** who want a plugin protocol to extend the engine.

The full engineering blueprint lives in [`SPEC.md`](SPEC.md) (1,657 lines, 16 sections + 2 appendices).

## Why StegoX?

Modern DFIR and CTF workflows are fragmented. Analysts juggle:

- One tool to embed, another to extract.
- Format-specific scripts for images vs. audio vs. video.
- Hand-rolled detection routines that aren't weighted or reproducible.
- Cloud-only or telemetry-leaking "AI" detectors you can't run on a sealed network.

**StegoX unifies these into one CLI** with a plugin-friendly architecture and a strict no-network policy. You can:

- Embed the same payload in PNG, WAV, MP4, and TXT using the same flags.
- Extract from any of them with the matching strategy.
- Run every applicable detector with a single command and get a confidence-scored, auditable report.
- Ship custom embedders, extractors, and detectors as Python entry points without forking.

It is:

- **Backendless** — no FastAPI, Flask, Django, or any web server.
- **Local-first** — no network calls under any code path. Network-requiring plugins are opt-in via `--allow-network`.
- **Open source** — MIT licensed, RFC-driven governance.
- **Plugin-extensible** — third parties can ship new embedders, extractors, detectors, and renderers.
- **Forensically defensible** — every operation is hashed (MD5/SHA-1/SHA-256/SHA-512), logged to a structured audit log, and reproducible from the case file alone.

## Key Features

### Embedding (`hide`)
- **Image:** sequential LSB, RGB-only LSB, PRNG-randomized LSB, password-keyed LSB with AES-256-GCM framing, mid-frequency DCT coefficient modulation (JPEG).
- **Audio:** PCM LSB, PRNG-randomized PCM LSB, echo-hiding, phase-spectrum coding, spread-spectrum.
- **Video:** per-frame LSB (every Nth frame), motion-region embedding, keyframe DCT (MP4/MKV/MOV).
- **Text:** zero-width Unicode (ZWSP/ZWNJ/ZWJ/BOM), trailing space/tab, Latin→Cyrillic homoglyph, advanced confusables.
- **Metadata:** EXIF, XMP, IPTC (JPEG); tEXt/zTXt/iTXt (PNG); ID3v2 (MP3); Vorbis comments (OGG/FLAC); MP4 container tags.

### Extraction (`extract`)
- Matching inverse for every strategy. Password-encrypted strategies recover the original payload with bit-perfect fidelity (or raise `IntegrityError` on tamper).
- Automatic detection of carrier type via magic bytes and extension.

### Detection (`detect` / `analyze`)
- **22+ built-in detectors** across image, audio, video, text, and universal categories.
- Modular, weighted confidence scoring (0–100) with low/medium/high risk bands.
- Each detector returns structured `Indicator` records (verdict, score, weight, metrics, description) that feed into a transparent rationale string.
- Built-in detectors include:
  - **Image:** RS analysis, chi-square, LSB distribution, histogram, entropy, DCT analysis.
  - **Audio:** spectrogram, noise floor, entropy window, echo pattern, bitplane.
  - **Video:** frame difference, temporal entropy, keyframe analysis, frame bitplane.
  - **Text:** zero-width scan, Unicode anomaly, whitespace pattern.
  - **Universal:** entropy, signature (magic), base64 scan, hex blob, archive scan.

### Reporting (`report`)
- **Console** with rich tables and panels (default for terminals).
- **JSON** for machine consumption and pipeline chaining.
- **HTML** — self-contained, offline, Jinja2-rendered with embedded CSS/JS.
- **PDF** — placeholder, documented in the SPEC for future release.

### DFIR Workflows (`case`)
- Initialize a case directory, add evidence, run scans, generate reports, seal the case (write a tamper-evident manifest).
- Chain-of-custody log with timestamps, hashes, and actors.

### Plugin Protocol
- Drop a Python package with entry points in `stegox.plugins`, or drop a file in `~/.config/stegox/plugins/`, and StegoX will discover and load it at startup.
- Plugin authors get the same `Detector`/`Embedder`/`Extractor`/`Renderer` base classes shipped to first-party code.

## Quick Start

```bash
# Install (once published)
pipx install stegox
# or
pip install stegox

# Hide a payload inside a PNG with password-protected AES-GCM framing
stegox image hide \
    --cover cat.png \
    --payload secret.txt \
    --out cat_stego.png \
    --strategy password-embed \
    --password "correct horse battery staple"

# Extract the payload
stegox image extract \
    --stego cat_stego.png \
    --out recovered.bin \
    --strategy password-embed \
    --password "correct horse battery staple"

# Run every applicable detector against a suspicious file
stegox detect --all suspicious.png

# Render an HTML report from a JSON scan result
stegox report render --input result.json --format html --out report.html

# Or just type `stegox` to enter the interactive, options-based menu
stegox
```

## Installation

### From PyPI (once published)

```bash
pipx install stegox        # recommended (isolated env)
# or
pip install stegox
```

### From source (development)

```bash
git clone https://github.com/Incredible-Hacker/stegox.git
cd stegox
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
stegox --version
stegox doctor
```

### Requirements

- **Python:** 3.10 or newer (3.13 tested in CI).
- **OS:** Linux (glibc + musl), macOS, Windows.
- **CPU:** x86_64 or aarch64.
- **Optional:** `ffmpeg` on PATH for video detection (embed/extract do not require it).
- **Optional:** `argon2-cffi` for Argon2id key derivation (falls back to scrypt/PBKDF2 if absent).

## Usage

### Hide a payload

```bash
# Image (lossless formats support all strategies)
stegox image hide \
    --cover photo.png \
    --payload secret.bin \
    --out photo.stego.png \
    --strategy lsb

# Image with encryption
stegox image hide \
    --cover photo.png \
    --payload secret.bin \
    --out photo.stego.png \
    --strategy password-embed \
    --password "hunter2"

# Audio
stegox audio hide \
    --cover song.wav \
    --payload secret.bin \
    --out song.stego.wav \
    --strategy pcm-lsb

# Video (per-frame LSB on every 4th frame)
stegox video hide \
    --cover clip.mp4 \
    --payload secret.bin \
    --out clip.stego.mp4 \
    --strategy frame-lsb

# Text (zero-width Unicode encoding)
stegox text hide \
    --cover essay.md \
    --payload secret.bin \
    --out essay.stego.md \
    --strategy zero-width

# Metadata (writes to a custom field)
stegox metadata hide \
    --cover photo.jpg \
    --payload secret.bin \
    --out photo.stego.jpg \
    --strategy EXIF.UserComment
```

### Extract a payload

```bash
stegox image extract \
    --stego photo.stego.png \
    --out recovered.bin \
    --strategy lsb \
    --payload-bytes 1234

stegox image extract \
    --stego photo.stego.png \
    --out recovered.bin \
    --strategy password-embed \
    --password "hunter2"

stegox text extract \
    --stego essay.stego.md \
    --out recovered.bin \
    --strategy zero-width
```

### Run detectors

```bash
# All applicable detectors
stegox detect --all suspicious.png

# A specific detector
stegox detect --target suspicious.png --detectors image.rs_analysis

# Multiple detectors (comma-separated)
stegox detect --target suspicious.png --detectors image.rs_analysis,image.chi_square

# Parallel jobs
stegox detect --target suspicious.png --jobs 4

# JSON output for piping
stegox detect --all suspicious.png --json > result.json
```

### Full analysis report

```bash
stegox image analyze --target suspicious.png
# Writes a full report: detection results, metadata, hashes, indicators.

stegox image analyze --target suspicious.png --json > analysis.json
stegox report render --input analysis.json --format html --out report.html
```

### DFIR case workflow

```bash
# Initialize a case
stegox case init --case-id CASE-2026-001 --lead "Analyst Name"

# Add evidence (hashes recorded automatically)
stegox case add --case-id CASE-2026-001 --evidence disk.img
stegox case add --case-id CASE-2026-001 --evidence notes.pdf

# Run a scan across all evidence
stegox case scan --case-id CASE-2026-001 --detectors all

# Render the case report
stegox case report --case-id CASE-2026-001 --format html --out case.html

# Seal the case (writes a tamper-evident manifest)
stegox case seal --case-id CASE-2026-001
```

### Interactive menu

Run `stegox` (no subcommand) or `stegox menu` to enter the **options-based interactive menu**. The menu walks you through hide/extract/detect/doctor/config without needing to remember flags.

```
╭───────────────────────────────────────────────────────────╮
│ StegoX v0.1.0.dev0                                        │
│ local-first steganography, steganalysis, and DFIR toolkit │
╰───────────────────────────────────────────────────────────╯
╭───────────────────────────────── Main menu ──────────────────────────────────╮
│ [1]  Hide a payload into a cover file                                        │
│ [2]  Extract a payload from a stego file                                     │
│ [3]  Run detectors / build a report on a file                                │
│ [4]  List available strategies (image/audio/...)                             │
│ [5]  Run diagnostics (doctor)                                                │
│ [6]  Show current configuration                                              │
│ [0]  Exit                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

The menu uses `rich.prompt` for input and `rich.console` for output — works in any TTY, gracefully handles EOF/Ctrl-C, and accepts empty input to cancel a step.

## Supported Media

| Medium   | Formats                       | Hide | Extract | Detect |
| -------- | ----------------------------- | ---- | ------- | ------ |
| Image    | PNG, BMP, JPEG, TIFF, WEBP    | yes  | yes     | yes    |
| Audio    | WAV, FLAC, MP3, OGG           | yes  | yes     | yes    |
| Video    | MP4, AVI, MKV, MOV            | yes  | yes     | yes    |
| Text     | TXT, MD, (DOCX in roadmap)    | yes  | yes     | yes    |
| Metadata | EXIF, XMP, IPTC, ID3, Vorbis  | yes  | yes     | yes    |

## Strategies

Each module publishes a typed strategy catalogue via `list_strategies()`. The full list is always available at runtime:

```bash
stegox image list-strategies
stegox audio list-strategies
stegox video list-strategies
stegox text  list-strategies
stegox metadata list-fields
```

Strategies that use the `password-embed` family (or any other explicitly encrypted strategy) require a `--password` and use AES-256-GCM with a per-call salt. See [`docs/security/crypto.md`](docs/security/crypto.md) for the framing format (`STGX` v1) and KDF selection.

## Detectors

```bash
stegox detect list-detectors
```

The detection engine is modular. Each detector implements the same interface:

```python
from stegox.detectors.base import Detector
from stegox.core.types import DetectionContext, DetectorResult

class MyDetector(Detector):
    id = "my.detector"
    name = "My Custom Detector"
    version = "1.0.0"
    media_type = MediaType.IMAGE
    formats = ("png", "bmp")
    weight = 0.7

    def run(self, target: DetectionContext) -> DetectorResult:
        ...
```

The framework handles registration, applicability filtering, parallel execution, timeouts, scoring, and reporting. See [`docs/detectors/index.md`](docs/detectors/index.md) for the full reference and [`docs/plugins/writing_a_plugin.md`](docs/plugins/writing_a_plugin.md) for the plugin protocol.

## Reports

Three renderers ship today:

- **Console** (`rich` tables + panels) — default for interactive use.
- **JSON** — Pydantic-serialized for pipelines. Schema published at [`docs/schemas/report.schema.json`](docs/schemas/report.schema.json).
- **HTML** — Jinja2-rendered, self-contained, offline, with embedded CSS/JS for filtering indicators.

PDF rendering is on the roadmap. The architecture makes it a small addition; the placeholder lives at `src/stegox/reports/pdf.py`.

## Plugin Development

Plugins are normal Python packages that expose one or more entry points under the `stegox.plugins` group, or single-file modules dropped into `~/.config/stegox/plugins/`.

```toml
# pyproject.toml
[project.entry-points."stegox.plugins"]
my_detector = "my_pkg.detectors:register"
```

The `register` function is called once at startup with the `PluginManager` as its argument:

```python
def register(pm):
    from my_pkg.detectors import MyDetector
    pm.register_detector(MyDetector())
```

Plugin authors can ship:

- Detectors (most common)
- Embedders / extractors
- Report renderers
- CLI subcommands
- Whole media-type modules

See [`docs/plugins/writing_a_plugin.md`](docs/plugins/writing_a_plugin.md) for the full guide and [`docs/plugins/plugin_api.md`](docs/plugins/plugin_api.md) for the API reference.

## Architecture

```
                  ┌──────────────────────────────────────┐
                  │             CLI (Typer)             │
                  │  image|audio|video|text|metadata|…  │
                  └─────────────┬────────────────────────┘
                                │
                  ┌─────────────▼────────────────────────┐
                  │            Engine                    │
                  │   hide / extract / detect / analyze  │
                  └──┬──────────────┬──────────────┬──────┘
                     │              │              │
        ┌────────────▼─┐  ┌─────────▼──────┐  ┌────▼──────────┐
        │   Modules     │  │   Detectors    │  │   Reports    │
        │ embed/extract │  │  22+ built-in  │  │ console/JSON │
        │ per media     │  │  + plugins     │  │  /HTML/PDF   │
        └────────────┬──┘  └────────┬───────┘  └──────────────┘
                     │              │
                     └──────┬───────┘
                            │
                  ┌─────────▼──────────┐
                  │       Core         │
                  │ types, errors,     │
                  │ config, paths,     │
                  │ logging, hashing,  │
                  │ bit I/O, atomic FS │
                  └─────────┬──────────┘
                            │
                  ┌─────────▼──────────┐
                  │     Security       │
                  │ AES-256-GCM,       │
                  │ Argon2id/scrypt/   │
                  │ PBKDF2, STGX v1    │
                  └────────────────────┘
```

Full details in [`docs/architecture.md`](docs/architecture.md) and [`SPEC.md`](SPEC.md).

## Security Model

Threat model, framing format, KDF selection, and operational guidance live in [`docs/security/threat_model.md`](docs/security/threat_model.md) and [`docs/security/crypto.md`](docs/security/crypto.md). Highlights:

- **Framing:** `STGX` v1 — magic, version, flags, salt, nonce, tag, length, ciphertext.
- **KDF:** Argon2id preferred (conservative parameters), scrypt and PBKDF2-HMAC-SHA256 as portable fallbacks.
- **Cipher:** AES-256-GCM (AEAD), 12-byte nonce, 16-byte tag, per-call salt.
- **Authenticity:** GCM tag verified before any payload processing; tampered frames raise `IntegrityError`.
- **At-rest:** atomic writes via temp-file + `os.replace`; no symlink following.
- **Network:** the default `PluginManager` blocks network-requiring plugins; opt-in with `--allow-network`.
- **Redaction:** log records are scanned for `password`/`token`/`api_key`/`secret` keys and replaced with `***REDACTED***` before they leave the formatter.
- **Audit:** every operation appends a structured log entry (timestamp, hashes, action, args hash). The `case seal` command writes a manifest of all files with their hashes for chain-of-custody.

**Reporting a vulnerability:** see [`SECURITY.md`](SECURITY.md). Please do not open public issues for suspected vulnerabilities.

## Testing & Quality

```bash
# Run the test suite
pytest

# With coverage
pytest --cov=stegox

# Type-check
mypy src/stegox

# Lint + format
ruff check src/
ruff format src/

# Security audit
bandit -r src/stegox
pip-audit

# Pre-commit (runs all of the above on staged files)
pre-commit run --all-files
```

Current status (as of `v0.1.0.dev0`):

- **32 / 32 tests passing** across unit, integration, and property-based suites.
- **ruff:** clean across 108 source files.
- **mypy:** clean across 108 source files.
- **CI:** Linux + macOS + Windows, Python 3.10 → 3.13.

## Performance

Capacity (rough numbers for a 1 MiB carrier):

| Strategy                       | Carrier   | Overhead    | Throughput       |
| ------------------------------ | --------- | ----------- | ---------------- |
| LSB (sequential)               | PNG       | ~25%        | ~10 MB/s         |
| password-embed (Argon2id + GCM)| PNG       | +60 bytes   | ~5 MB/s          |
| PCM LSB                        | WAV       | 1 bit/sample| ~20 MB/s         |
| DCT (JPEG)                     | JPEG      | lossless? no| ~2 MB/s          |
| zero-width (text)              | TXT       | 4x expansion| ~50 KB/s         |

Numbers depend heavily on cover size, KDF parameters, and CPU. Run `pytest tests/performance/` for a machine-specific benchmark.

## Project Layout

```
stegox/
├── SPEC.md                 # 1,657-line engineering blueprint
├── README.md
├── LICENSE                 # MIT
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── pyproject.toml          # hatchling build, deps, scripts, tool config
├── mkdocs.yml
├── requirements*.txt
├── .pre-commit-config.yaml
├── .editorconfig
├── .gitignore
├── docs/                   # MkDocs site
│   ├── index.md
│   ├── architecture.md
│   ├── cli/
│   ├── detectors/
│   ├── forensics/
│   ├── plugins/
│   ├── security/
│   ├── governance/
│   └── schemas/
├── examples/               # copy-paste shell recipes
├── scripts/                # install_dev, run_tests, build_wheel
├── tools/                  # generate_fixtures, update_magic, check_changelog
├── rfcs/                   # governance / design records
├── src/stegox/             # the package
│   ├── core/               # types, errors, config, paths, logging
│   ├── security/           # crypto, kdf, framing, shred
│   ├── utils/              # io, hashing, bitio, progress, magic
│   ├── media/              # identifier, registry, loader, inspector, formats
│   ├── modules/            # image, audio, video, text, metadata
│   ├── detectors/          # base, registry, scoring, engine + per-media
│   ├── engine/             # hide, extract, detect, analyze, pipeline
│   ├── plugins/            # manager, spec, examples
│   ├── reports/            # model, console, json_render, html
│   ├── forensics/          # case, chain_of_custody, hashing, timeline
│   └── cli/                # app, menu, errors, exitcodes, commands/
└── tests/                  # unit, integration, property, regression
```

## Documentation

- [`SPEC.md`](SPEC.md) — the full engineering specification.
- [`docs/index.md`](docs/index.md) — user guide.
- [`docs/architecture.md`](docs/architecture.md) — system internals.
- [`docs/cli/index.md`](docs/cli/index.md) — CLI reference.
- [`docs/detectors/index.md`](docs/detectors/index.md) — detector reference.
- [`docs/forensics/workflow.md`](docs/forensics/workflow.md) — DFIR workflow guide.
- [`docs/plugins/writing_a_plugin.md`](docs/plugins/writing_a_plugin.md) — plugin author guide.
- [`docs/security/threat_model.md`](docs/security/threat_model.md) — threat model.
- [`docs/governance/rfcs.md`](docs/governance/rfc_process.md) — RFC process.
- [`docs/schemas/report.schema.json`](docs/schemas/report.schema.json) — JSON schema for reports.

## Comparison with Other Tools

| Capability                         | StegoX | steghide | OpenStego | zsteg | stegseek | binwalk |
| ---------------------------------- | :----: | :------: | :-------: | :---: | :------: | :-----: |
| Local-first / no network           |   ✓    |    ✓     |     ✓     |   ✓   |    ✓     |    ✓    |
| Backendless CLI                    |   ✓    |    ✓     |     ✓     |   ✓   |    ✓     |    ✓    |
| Hide in image                      |   ✓    |    ✓     |     ✓     |   ✗   |    ✗     |    ✗    |
| Hide in audio                      |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Hide in video                      |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Hide in text                       |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Hide in metadata                   |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Extract same tool                  |   ✓    |    ✓     |     ✓     |   ✓   |    ✓     |    ✓    |
| Modular detector framework         |   ✓    |    ✗     |     ✗     |   ✗   |  partial |  partial|
| Weighted confidence scoring        |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Interactive menu                   |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Plugin protocol                    |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| HTML report                        |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| DFIR case workflow                 |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| Chain-of-custody log               |   ✓    |    ✗     |     ✗     |   ✗   |    ✗     |    ✗    |
| MIT-licensed                       |   ✓    |    ✓     |     ✓     |   ✓   |    ✓     |    ✓    |

## Limitations

- **JPEG LSB** is impossible by construction; StegoX uses DCT coefficient modulation for JPEG. Expect a quality hit at high embedding rates.
- **MP3 hide** uses ID3v2 metadata, not audio sample modification, because lossy compression destroys sample-level data.
- **Video detection** requires `ffmpeg` on PATH for some formats (MP4 demuxing).
- **DOCX** is on the roadmap; current text strategies target plain `.txt` and `.md`.
- **Spread-spectrum audio** is implemented but uses a fixed chip rate; per-deployment tuning is future work.
- **No GPU acceleration** — every strategy is CPU-only by design. If your carrier is 100 MB, expect seconds-to-minutes for a full detector sweep.

## Roadmap

- v0.2 — DOCX embed/extract, more universal detectors (PE/ELF anomaly, EXIF heuristics).
- v0.3 — PDF report renderer.
- v0.4 — Tauri / PySide6 desktop GUI shell that wraps the existing CLI.
- v0.5 — Improved video: motion-aware embedding, GOP-aware keyframe selection.
- v0.6 — RFC-0001 plugin protocol v1 (formal spec, version negotiation).
- v1.0 — Stable API, signed wheels, Homebrew tap, Scoop bucket, Nix flake, AUR package.

## Contributing

Contributions are welcome. Before opening a PR, please read:

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — coding style, commit format, review process.
- [`docs/governance/contributing.md`](docs/governance/contributing.md) — governance specifics.
- [`docs/governance/rfc_process.md`](docs/governance/rfc_process.md) — for any change to the public API.

Use **Conventional Commits** (`feat:`, `fix:`, `docs:`, `chore:`, …) so automated changelog generation works. Run `pre-commit run --all-files` before pushing.

## Governance & RFCs

StegoX uses an RFC process for substantive changes. RFCS live in [`rfcs/`](rfcs/) and follow the template at [`rfcs/template.md`](rfcs/template.md). The active set:

- `0001-record-process.md` — how RFCs are filed, discussed, and accepted.
- `0002-plugin-protocol-v1.md` — the v1 plugin protocol contract.
- `0003-confidence-scoring.md` — the detector weighting and risk-band math.

Anyone can propose an RFC. Acceptance requires a maintainer sign-off after a 14-day comment window.

## FAQ

**Q: Is StegoX undetectable?**
A: No tool is. StegoX includes its own detector framework precisely so you can audit what your embedder leaves behind. Use the analyze flow to grade your own work.

**Q: Can I use StegoX from Python, not just the CLI?**
A: Yes. Every CLI command is a thin wrapper over the `engine` and `modules` packages. See the Quick Start in [`docs/index.md`](docs/index.md) for programmatic examples.

**Q: Does StegoX phone home?**
A: No. There is no telemetry, no analytics, no update check. Verified by `bandit` and a custom network-call audit in CI.

**Q: How do I add a new embed strategy?**
A: Subclass the appropriate module's strategy function or write a new module, then register it. See [`docs/plugins/writing_a_plugin.md`](docs/plugins/writing_a_plugin.md).

**Q: Why no GUI?**
A: The CLI is the source of truth. A desktop GUI is on the roadmap (v0.4) and will be a thin shell over the CLI — never the reverse.

**Q: Why MIT and not Apache 2.0?**
A: MIT maximizes downstream reuse (commercial, academic, hobbyist). Apache 2.0's patent grant was a close second; community feedback at the v0.0 design review tipped the balance.

**Q: Will v1.0 break my plugin?**
A: No. The v0.x line is committed to API stability for embedders, extractors, and detectors. Only major (v1+) versions may break the plugin protocol; the deprecation policy is in the RFCs.

## Citation

If you use StegoX in academic work, please cite it as:

```bibtex
@software{stegox2026,
  title  = {StegoX: A local-first toolkit for steganography, steganalysis, and digital forensics triage},
  author = {{The StegoX contributors}},
  year   = {2026},
  url    = {https://github.com/Incredible-Hacker/stegox},
  note   = {Version 0.1.0}
}
```

## License

[MIT](LICENSE) — see the [`LICENSE`](LICENSE) file for the full text.

## Acknowledgments

- **Fridrich, Goljan, Du** — RS analysis foundation.
- **Provos & Honeyman** — stegdetect-style statistical framework inspiration.
- **Pierre Laperdrix** — detector benchmarking methodology.
- **The `rich` and `typer` teams** — for making terminal UX enjoyable.
- **Every DFIR analyst who ever lost an afternoon to a missing tool** — this is for you.
