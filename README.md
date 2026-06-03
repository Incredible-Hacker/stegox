# StegoX

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/stegox/stegox/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**StegoX** is an all-in-one, fully local, backendless toolkit for **steganography**, **steganalysis**, **digital forensics triage**, and **payload discovery**. It runs entirely on the analyst's machine. There is no server, no database, no cloud, and no telemetry.

## Why StegoX?

Modern DFIR and CTF workflows require a single tool that can:

- **Hide** payloads in images, audio, video, text, and metadata.
- **Extract** payloads from steganographic carriers.
- **Detect** covert channels using a modular, weighted detector framework.
- **Analyze** artifacts with reproducible, auditable reports.
- **Report** findings as console tables, JSON, or self-contained HTML.

StegoX is that tool. It is:

- **Backendless** — no FastAPI, Flask, Django, or any web server.
- **Local-first** — no network calls under any code path.
- **Open source** — MIT licensed, RFC-driven governance.
- **Plugin-extensible** — third parties can ship new embedders, extractors, detectors, and renderers.
- **Forensically defensible** — every operation is hashed, logged, and reproducible.

## Quick Start

```bash
# Install (once published)
pipx install stegox
# or
pip install stegox

# Hide a payload inside a PNG
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

# Run every detector against a suspicious file
stegox detect --all suspicious.png

# Render an HTML report
stegox report render --input result.json --format html --out report.html
```

## Supported Media

| Medium | Formats | Hide | Extract | Detect |
|---|---|---|---|---|
| Image | PNG, BMP, JPEG, TIFF, WEBP | yes | yes | yes |
| Audio | WAV, FLAC, MP3, OGG | yes | yes | yes |
| Video | MP4, AVI, MKV, MOV | yes | yes | yes |
| Text | TXT, MD, (DOCX future) | yes | yes | yes |
| Metadata | EXIF, XMP, IPTC, ID3, Vorbis | yes | yes | yes |

## CLI Overview

```
stegox image <hide|extract|detect|analyze|list-strategies>
stegox audio <hide|extract|detect|analyze|list-strategies>
stegox video <hide|extract|detect|analyze|list-strategies>
stegox text  <hide|extract|detect|analyze|list-strategies>
stegox metadata <hide|extract|detect|analyze|list-fields>
stegox detect --all <file>
stegox case <init|add|scan|report|seal>
stegox plugin <list|info>
stegox config <show|get|set>
stegox report render --input <json> --format <console|json|html> --out <file>
stegox doctor
stegox --version
```

## Documentation

- [Specification](SPEC.md) — the full engineering blueprint
- [User Guide](docs/index.md) — installation, usage, recipes
- [Architecture](docs/architecture.md) — system internals
- [CLI Reference](docs/cli/index.md)
- [Detector Reference](docs/detectors/index.md)
- [Plugin Author Guide](docs/plugins/writing_a_plugin.md)
- [Security & Threat Model](docs/security/crypto.md)

## Project Status

StegoX is in active development. The first stable release (v1.0) targets the following:

- Image, audio, video, text, metadata modules
- Universal + media-specific detectors
- Console, JSON, and HTML reports
- Stable plugin protocol v1
- CI on Linux, macOS, and Windows
- Packaged wheels for x86_64 and aarch64

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [RFC process](rfcs/0001-record-process.md) before opening a PR.

## License

MIT — see [LICENSE](LICENSE).
