# StegoX — Engineering Specification

**Status:** Draft v1.0
**License:** Open Source (recommend MIT or Apache-2.0)
**Architecture Type:** Backendless, Local-First, CLI-First Python Toolkit
**Document Purpose:** Production-ready engineering blueprint for implementing the StegoX project end-to-end.

> This document is a blueprint only. It does not contain source code. It is intended to be read by a coding agent or engineering team before any implementation begins.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Folder Structure](#3-folder-structure)
4. [Module Design](#4-module-design)
5. [Detector Design](#5-detector-design)
6. [Steganalysis Methodology](#6-steganalysis-methodology)
7. [Forensic Workflow](#7-forensic-workflow)
8. [Plugin Architecture](#8-plugin-architecture)
9. [CLI Specification](#9-cli-specification)
10. [Reporting Architecture](#10-reporting-architecture)
11. [Security Architecture](#11-security-architecture)
12. [Testing Strategy](#12-testing-strategy)
13. [Open-Source Governance](#13-open-source-governance)
14. [Release Strategy](#14-release-strategy)
15. [Development Roadmap](#15-development-roadmap)
16. [Future Enhancements](#16-future-enhancements)
17. [Appendix A — Detector Reference Matrix](#appendix-a--detector-reference-matrix)
18. [Appendix B — Glossary](#appendix-b--glossary)

---

## 1. Executive Summary

### 1.1 Vision
StegoX is a fully local, open-source, backendless engineering toolkit that unifies **steganography**, **steganalysis**, **digital forensics triage**, and **payload discovery** into a single, scriptable CLI platform. It is designed to be operated by humans (analysts, students, researchers, CTF players) and by automation (CI pipelines, DFIR triage scripts) with the same surface area.

### 1.2 Mission
Provide a defensible, auditable, and extensible toolkit that runs **entirely on the analyst's machine** without:
- Backend services
- Cloud dependencies
- Telemetry or outbound network calls
- Database servers
- External APIs

### 1.3 Target Users
- DFIR Analysts performing live incident triage
- Digital Forensics students learning artifact-level analysis
- Ethical Hackers performing red team / purple team exercises
- Security Researchers studying covert channels
- CTF Players solving steganography challenges
- Incident Responders auditing suspicious artifacts

### 1.4 Core Capability Matrix
Every supported media type must provide five operations:

| Operation | Description |
|---|---|
| **Hide** | Embed a payload into a cover medium |
| **Extract** | Recover an embedded payload from a medium |
| **Detect** | Run steganalysis heuristics against a medium |
| **Analyze** | Produce a deep forensic profile of a medium |
| **Report** | Render console / JSON / HTML reports |

### 1.5 Supported Media Types
- **Image:** PNG, BMP, JPEG, TIFF, WEBP
- **Audio:** WAV, MP3, FLAC, OGG
- **Video:** MP4, AVI, MKV, MOV
- **Text:** TXT, MD, (future: DOCX)
- **Metadata:** EXIF, XMP, IPTC, PNG text chunks, file-level metadata

### 1.6 Non-Goals
StegoX explicitly does **not**:
- Act as a covert exfiltration tool
- Provide ransomware or destructive capabilities
- Exfiltrate data over the network
- Phone home or phone home in obfuscated form
- Operate as a web service or expose any network listener

### 1.7 Guiding Principles
1. **Local-first** — no data leaves the host.
2. **Forensic defensibility** — every operation is reproducible and logged.
3. **Modularity** — every subsystem is a swappable component.
4. **Composability** — detectors and embedders can be chained.
5. **Open governance** — community contributions are reviewed against a published spec.
6. **Boring is better** — prefer stdlib and well-vetted dependencies.

### 1.8 Success Criteria
A successful StegoX v1.0 release:
- Installs via `pip install stegox` and `pipx install stegox` on Linux, macOS, Windows
- Provides a `stegox` CLI with stable subcommand contracts
- Ships a plugin protocol third parties can target
- Includes deterministic test fixtures and CI badges
- Publishes signed GitHub releases with SHA256 manifests
- Achieves >= 85% test coverage on the core engine
- Includes a public, versioned, and machine-readable CLI grammar

---

## 2. System Architecture

### 2.1 Architectural Style
StegoX follows a **layered, plugin-oriented, command-driven** architecture with strict **local execution boundaries**. There is no service tier, no message queue, no database, and no outbound network layer.

```
+---------------------------------------------------------------+
|                        CLI SURFACE                            |
|           (argparse / Typer, command dispatcher)              |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                    COMMAND / SUBCOMMAND LAYER                 |
|          (image, audio, video, text, metadata, detect)        |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                      OPERATION LAYER                          |
|         (hide, extract, detect, analyze, report)             |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                        CORE ENGINE                            |
|   (media I/O, plugin registry, crypto, detection pipeline,   |
|       report rendering, logging, config, error handling)     |
+---------------------------------------------------------------+
        |              |              |              |
        v              v              v              v
+-------------+ +-------------+ +-------------+ +-------------+
|  Image Mod. | |  Audio Mod. | |  Video Mod. | |  Text Mod.  |
+-------------+ +-------------+ +-------------+ +-------------+
        |              |              |              |
        v              v              v              v
+---------------------------------------------------------------+
|                   CODEC / FORMAT ABSTRACTIONS                 |
|         (PIL, OpenCV, soundfile, imageio, ffmpeg)             |
+---------------------------------------------------------------+
                              |
                              v
+---------------------------------------------------------------+
|                 LOCAL FILESYSTEM + USER STDOUT                |
+---------------------------------------------------------------+
```

### 2.2 Architectural Invariants
The architecture is bound by the following invariants:

1. **No outbound network** under any code path. Any violation is a critical bug.
2. **No persistent state** beyond the user's filesystem. The only "database" is the user's directory.
3. **Deterministic CLI** — same input + same plugin set = same output (modulo RNG keying, which is always password-derived).
4. **Side-effect-free core** — the core engine never writes to the filesystem directly; it returns a `Result` object that the CLI layer persists.
5. **Process isolation** — long-running detectors run in subprocesses to keep the main process responsive.

### 2.3 Major Subsystems
| Subsystem | Responsibility |
|---|---|
| `stegox.cli` | Argument parsing, subcommand dispatch, exit codes |
| `stegox.core` | Shared types, errors, result objects, configuration |
| `stegox.engine` | Orchestration of hide/extract/detect/analyze/report |
| `stegox.media` | Format-agnostic media abstractions |
| `stegox.modules` | Image, audio, video, text, metadata, crypto modules |
| `stegox.detectors` | Pluggable detector framework |
| `stegox.plugins` | Plugin discovery, registration, lifecycle |
| `stegox.reports` | Report rendering in console, JSON, HTML |
| `stegox.security` | Crypto primitives, secure key handling |
| `stegox.logging` | Structured logging, audit trail |
| `stegox.config` | Configuration loading, defaults |
| `stegox.utils` | Helpers (IO, hashing, file carving) |
| `stegox.tools` | Optional one-off utilities |

### 2.4 Dependency Strategy
- **Hard dependencies (locked to a floor version):**
  - `Pillow` (image I/O)
  - `numpy` (numerical operations)
  - `soundfile` (WAV/FLAC)
  - `imageio` and `imageio-ffmpeg` (video decoding)
  - `mutagen` (MP3/OGG metadata)
  - `cryptography` (AES-GCM, PBKDF2, scrypt)
  - `typer` and `rich` (CLI UX)
  - `pyyaml` (config)
  - `pluggy` (plugin system)
  - `pydantic` (config and result schemas)
- **Optional dependencies (declared as extras):**
  - `scipy` for advanced DSP detectors
  - `matplotlib` for plotting
  - `ffmpeg-python` for rich video pipeline
  - `stegano` for cross-validation
  - `zsteg`-equivalent routines (implemented natively, not a dependency)
- **Dev dependencies:** `pytest`, `pytest-cov`, `hypothesis`, `tox`, `ruff`, `mypy`, `pre-commit`.

### 2.5 Process Model
StegoX is a single-process Python application by default. The CLI is the entry point. A user can invoke a subcommand and the process exits when done. Long-running batch operations (e.g., directory scans) stream results via generators to keep memory bounded.

### 2.6 Data Flow (Hide)
```
Payload bytes
   -> compression (zlib or zstd)
   -> AES-256-GCM encrypt (key = KDF(password, salt, iters))
   -> framing (magic + version + salt + nonce + tag + length)
   -> embedder strategy (LSB, randomized LSB, echo, phase, etc.)
   -> cover medium mutated in memory
   -> output written to filesystem
   -> audit log emitted
```

### 2.7 Data Flow (Detect)
```
Target file
   -> file-type identification (signature + extension)
   -> metadata audit
   -> signature scan (magic bytes of known stego tools)
   -> entropy analysis (global + windowed)
   -> media-specific detectors (LSB, chi-square, RS, etc.)
   -> scoring engine (weighted evidence)
   -> risk classification
   -> report renderer (console / JSON / HTML)
```

### 2.8 Concurrency
- Use `concurrent.futures.ThreadPoolExecutor` for I/O-bound operations.
- Use `multiprocessing.Pool` only when a detector is CPU-bound and the user opts into parallel scan mode (`--jobs N`).
- All concurrency is opt-in; default mode is single-threaded and deterministic.

---

## 3. Folder Structure

### 3.1 Repository Layout
```
stegox/
├── LICENSE
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── requirements-extras.txt
├── tox.ini
├── .editorconfig
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── lint.yml
│   │   ├── security.yml
│   │   ├── release.yml
│   │   ├── docs.yml
│   │   └── dependency-review.yml
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── detector_request.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
├── docs/
│   ├── index.md
│   ├── architecture.md
│   ├── cli/
│   │   ├── index.md
│   │   ├── image.md
│   │   ├── audio.md
│   │   ├── video.md
│   │   ├── text.md
│   │   ├── metadata.md
│   │   └── detect.md
│   ├── detectors/
│   │   ├── index.md
│   │   ├── image.md
│   │   ├── audio.md
│   │   ├── video.md
│   │   └── text.md
│   ├── forensics/
│   │   ├── workflow.md
│   │   ├── reporting.md
│   │   └── case_workflow.md
│   ├── plugins/
│   │   ├── writing_a_plugin.md
│   │   └── plugin_api.md
│   ├── security/
│   │   ├── crypto.md
│   │   └── threat_model.md
│   ├── governance/
│   │   ├── contributing.md
│   │   ├── release.md
│   │   └── rfc_process.md
│   └── assets/
│       ├── diagrams/
│       │   ├── architecture.svg
│       │   ├── data_flow_hide.svg
│       │   ├── data_flow_detect.svg
│       │   └── plugin_lifecycle.svg
│       └── screenshots/
├── src/
│   └── stegox/
│       ├── __init__.py
│       ├── __main__.py
│       ├── py.typed
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── commands/
│       │   │   ├── __init__.py
│       │   │   ├── image.py
│       │   │   ├── audio.py
│       │   │   ├── video.py
│       │   │   ├── text.py
│       │   │   ├── metadata.py
│       │   │   ├── detect.py
│       │   │   ├── report.py
│       │   │   ├── plugin.py
│       │   │   ├── config.py
│       │   │   ├── version.py
│       │   │   └── doctor.py
│       │   ├── errors.py
│       │   ├── exitcodes.py
│       │   └── formatters/
│       │       ├── __init__.py
│       │       └── console.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── types.py
│       │   ├── errors.py
│       │   ├── result.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   ├── constants.py
│       │   └── paths.py
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── hide.py
│       │   ├── extract.py
│       │   ├── detect.py
│       │   ├── analyze.py
│       │   └── pipeline.py
│       ├── media/
│       │   ├── __init__.py
│       │   ├── registry.py
│       │   ├── identifier.py
│       │   ├── loader.py
│       │   ├── inspector.py
│       │   └── formats/
│       │       ├── __init__.py
│       │       ├── png.py
│       │       ├── bmp.py
│       │       ├── jpeg.py
│       │       ├── tiff.py
│       │       ├── webp.py
│       │       ├── wav.py
│       │       ├── mp3.py
│       │       ├── flac.py
│       │       ├── ogg.py
│       │       ├── mp4.py
│       │       ├── avi.py
│       │       ├── mkv.py
│       │       ├── mov.py
│       │       └── text.py
│       ├── modules/
│       │   ├── __init__.py
│       │   ├── image/
│       │   │   ├── __init__.py
│       │   │   ├── lsb.py
│       │   │   ├── randomized_lsb.py
│       │   │   ├── password_embed.py
│       │   │   ├── extract.py
│       │   │   └── dct.py
│       │   ├── audio/
│       │   │   ├── __init__.py
│       │   │   ├── pcm_lsb.py
│       │   │   ├── echo_hiding.py
│       │   │   ├── phase_coding.py
│       │   │   └── extract.py
│       │   ├── video/
│       │   │   ├── __init__.py
│       │   │   ├── frame_lsb.py
│       │   │   ├── motion_embed.py
│       │   │   └── extract.py
│       │   ├── text/
│       │   │   ├── __init__.py
│       │   │   ├── zero_width.py
│       │   │   ├── whitespace.py
│       │   │   ├── homoglyph.py
│       │   │   └── extract.py
│       │   └── metadata/
│       │       ├── __init__.py
│       │       ├── embed.py
│       │       ├── extract.py
│       │       ├── audit.py
│       │       └── exif.py
│       ├── detectors/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── scoring.py
│       │   ├── engine.py
│       │   ├── image/
│       │   │   ├── __init__.py
│       │   │   ├── lsb_distribution.py
│       │   │   ├── chi_square.py
│       │   │   ├── rs_analysis.py
│       │   │   ├── histogram.py
│       │   │   ├── entropy.py
│       │   │   └── dct_analysis.py
│       │   ├── audio/
│       │   │   ├── __init__.py
│       │   │   ├── spectrogram.py
│       │   │   ├── noise_floor.py
│       │   │   ├── entropy_window.py
│       │   │   ├── echo_pattern.py
│       │   │   └── bitplane.py
│       │   ├── video/
│       │   │   ├── __init__.py
│       │   │   ├── frame_diff.py
│       │   │   ├── temporal_entropy.py
│       │   │   ├── keyframe.py
│       │   │   └── frame_bitplane.py
│       │   ├── text/
│       │   │   ├── __init__.py
│       │   │   ├── zero_width_scan.py
│       │   │   ├── unicode_anomaly.py
│       │   │   └── whitespace_pattern.py
│       │   └── universal/
│       │       ├── __init__.py
│       │       ├── entropy.py
│       │       ├── signature.py
│       │       ├── base64_scan.py
│       │       ├── hex_blob.py
│       │       └── archive_scan.py
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── manager.py
│       │   ├── entrypoints.py
│       │   ├── spec.py
│       │   └── examples/
│       │       ├── __init__.py
│       │       └── hello_detector/
│       │           ├── __init__.py
│       │           ├── pyproject.toml
│       │           └── plugin.py
│       ├── reports/
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── console.py
│       │   ├── json.py
│       │   ├── html/
│       │   │   ├── __init__.py
│       │   │   ├── render.py
│       │   │   ├── template.py
│       │   │   ├── static/
│       │   │   │   ├── style.css
│       │   │   │   └── app.js
│       │   │   └── templates/
│       │   │       ├── base.html
│       │   │       ├── report.html
│       │   │       └── indicators.html
│       │   └── pdf.py
│       ├── security/
│       │   ├── __init__.py
│       ├── crypto.py
│       │   ├── kdf.py
│       │   ├── framing.py
│       │   └── shred.py
│       ├── forensics/
│       │   ├── __init__.py
│       │   ├── case.py
│       │   ├── chain_of_custody.py
│       │   ├── hashing.py
│       │   ├── timeline.py
│       │   └── workflow.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── io.py
│       │   ├── hashing.py
│       │   ├── bitio.py
│       │   ├── progress.py
│       │   └── magic.py
│       └── version.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── images/
│   │   ├── audio/
│   │   ├── video/
│   │   ├── text/
│   │   ├── embedded/
│   │   └── payloads/
│   ├── unit/
│   │   ├── core/
│   │   ├── engine/
│   │   ├── media/
│   │   ├── modules/
│   │   │   ├── image/
│   │   │   ├── audio/
│   │   │   ├── video/
│   │   │   ├── text/
│   │   │   └── metadata/
│   │   ├── detectors/
│   │   │   ├── image/
│   │   │   ├── audio/
│   │   │   ├── video/
│   │   │   ├── text/
│   │   │   └── universal/
│   │   ├── plugins/
│   │   ├── reports/
│   │   ├── security/
│   │   └── utils/
│   ├── integration/
│   │   ├── cli/
│   │   ├── pipelines/
│   │   └── end_to_end/
│   ├── property/
│   │   └── test_framing.py
│   ├── regression/
│   │   ├── ctfs/
│   │   └── corpora/
│   └── performance/
│       ├── bench_detect.py
│       └── bench_hide.py
├── tools/
│   ├── generate_fixtures.py
│   ├── update_magic.py
│   └── check_changelog.py
├── scripts/
│   ├── install_dev.sh
│   ├── run_tests.sh
│   └── build_wheel.sh
├── examples/
│   ├── hide_text_in_png.sh
│   ├── detect_image.sh
│   ├── batch_scan.sh
│   └── case_workflow.md
├── rfcs/
│   ├── 0001-record-process.md
│   ├── 0002-plugin-protocol-v1.md
│   ├── 0003-confidence-scoring.md
│   └── template.md
└── RELEASES.md
```

### 3.2 Directory Responsibilities
| Directory | Responsibility |
|---|---|
| `src/stegox/` | Source code root |
| `src/stegox/cli/` | CLI commands and dispatch |
| `src/stegox/core/` | Cross-cutting types, errors, config, logging |
| `src/stegox/engine/` | Orchestration of operations |
| `src/stegox/media/` | Format detection and loading |
| `src/stegox/modules/` | Per-medium embed/extract implementations |
| `src/stegox/detectors/` | Pluggable detector framework |
| `src/stegox/plugins/` | Plugin system machinery |
| `src/stegox/reports/` | Report rendering (console/JSON/HTML) |
| `src/stegox/security/` | Crypto, framing, secure I/O |
| `src/stegox/forensics/` | Case files, hashing, chain of custody |
| `src/stegox/utils/` | Generic utilities |
| `tests/` | Test suite, fixtures, regression corpus |
| `docs/` | User and developer documentation |
| `rfcs/` | Design proposals |
| `tools/` | Maintainer scripts |
| `scripts/` | Build and dev convenience scripts |
| `examples/` | End-user usage examples |

---

## 4. Module Design

### 4.1 Module Boundaries
Each module is a self-contained package under `stegox.modules.<medium>` with a stable public API. The engine layer is the only consumer that is allowed to call into multiple modules.

### 4.2 Image Module

#### 4.2.1 Hide Strategies
| Strategy ID | Description | Capacity | Robustness |
|---|---|---|---|
| `lsb` | Sequential LSB across all color channels | High | Low (detectable) |
| `lsb-rgb` | Sequential LSB across RGB only | High | Low |
| `randomized-lsb` | LSB with PRNG-driven pixel selection seeded by password | High | Medium |
| `password-embed` | Randomized LSB + AES-GCM framing | High | High |
| `dct-jpeg` | DCT coefficient manipulation (JPEG) | Medium | Medium |

#### 4.2.2 Extract Strategies
- `lsb-extract` — pulls sequential LSB
- `randomized-lsb-extract` — requires password to reconstruct PRNG sequence
- `password-extract` — combined KDF + decrypt + decompress
- `dct-extract` — recovers DCT-embedded payloads
- `signature-extract` — searches for known tool signatures (e.g., OpenStego, steghide markers)

#### 4.2.3 Supported Formats
| Format | Read | Write | Notes |
|---|---|---|---|
| PNG | yes | yes | Lossless, recommended |
| BMP | yes | yes | Lossless, no compression |
| JPEG | yes | yes | DCT-based path only |
| TIFF | yes | yes | Multi-page supported |
| WEBP | yes | yes | Lossless and lossy handled separately |

#### 4.2.4 Image Module Public API
- `embed_image(cover, payload, strategy, password=None) -> ImageResult`
- `extract_image(stego, strategy, password=None) -> bytes`
- `list_strategies() -> list[Strategy]`

### 4.3 Audio Module

#### 4.3.1 Hide Strategies
| Strategy ID | Description | Capacity | Robustness |
|---|---|---|---|
| `pcm-lsb` | LSB in PCM samples | High | Low |
| `pcm-lsb-rand` | Randomized sample order LSB | High | Medium |
| `echo-hiding` | Echo kernel modulation | Low | Medium |
| `phase-coding` | Phase spectrum embedding | Medium | Medium |
| `spread-spectrum` | Frequency-domain spread | Low | High |

#### 4.3.2 Extract Strategies
- `pcm-lsb-extract`
- `pcm-lsb-rand-extract` (requires password)
- `echo-extract` (parameterized by delay, decay)
- `phase-extract`
- `spread-spectrum-extract` (requires key)

#### 4.3.3 Supported Formats
| Format | Read | Write | Notes |
|---|---|---|---|
| WAV | yes | yes | Preferred for hiding |
| FLAC | yes | yes | Lossless |
| MP3 | yes | extract-only | Re-encoding destroys LSB |
| OGG | yes | extract-only | Vorbis lossy |

### 4.4 Video Module

#### 4.4.1 Hide Strategies
| Strategy ID | Description | Capacity | Robustness |
|---|---|---|---|
| `frame-lsb` | LSB across all keyframes | Very High | Low |
| `frame-lsb-rand` | Randomized frame/pixel selection | High | Medium |
| `motion-region` | Embed inside motion vector residuals | Medium | High |
| `keyframe-dct` | Embed in I-frame DCT coefficients | Medium | High |

#### 4.4.2 Extract Strategies
- `frame-lsb-extract`
- `frame-lsb-rand-extract` (requires password)
- `motion-region-extract`
- `keyframe-dct-extract`

#### 4.4.3 Supported Formats
| Format | Read | Write | Notes |
|---|---|---|---|
| MP4 | yes | yes | H.264/H.265 |
| AVI | yes | yes | Codec-dependent |
| MKV | yes | yes | Container flexible |
| MOV | yes | yes | Apple ecosystem |

### 4.5 Text Module

#### 4.5.1 Hide Strategies
| Strategy ID | Description | Capacity | Detectability |
|---|---|---|---|
| `zero-width` | ZWSP, ZWNJ, ZWJ, ZWS | High | Medium |
| `whitespace` | Trailing spaces and tabs | High | Low |
| `homoglyph` | Cyrillic/Greek look-alikes | High | High (renders oddly) |
| `homoglyph-advanced` | Confusable pairs with normalization map | High | Medium |

#### 4.5.2 Extract Strategies
- `zero-width-extract`
- `whitespace-extract`
- `homoglyph-extract` (requires normalization map)
- `universal-extract` (auto-detect and try all)

### 4.6 Metadata Module

#### 4.6.1 Hide Targets
- EXIF `ImageDescription`
- EXIF `UserComment`
- EXIF `Artist`
- EXIF `Copyright`
- XMP `dc:description`
- XMP `dc:creator`
- XMP `xmp:MetadataDate`
- IPTC `Caption`
- PNG `tEXt`, `zTXt`, `iTXt` chunks
- ID3v1 / ID3v2 tags (MP3)
- Vorbis comments (OGG, FLAC)
- MP4 iTunes metadata atoms
- Matroska tags

#### 4.6.2 Detect Targets
- Excessively long string fields
- High-entropy fields (likely encrypted)
- Base64-pattern matches
- Hex blob detection
- Embedded archive magic in fields
- Anomalous encoding

### 4.7 Crypto Module

#### 4.7.1 Algorithms
| Purpose | Algorithm | Parameters |
|---|---|---|
| Symmetric cipher | AES-256-GCM | 12-byte nonce, 16-byte tag |
| Key derivation | Argon2id (preferred) or scrypt (fallback) or PBKDF2-HMAC-SHA256 | tunable memory/iterations |
| Compression | zstd (preferred) or zlib | level 3 default |
| Random | `secrets` module | CSPRNG |

#### 4.7.2 Frame Format (Binary)
```
+---------+---------+--------+--------+--------+----------+-----------+----------+
| Magic   | Version | Flags  | Salt   | Nonce  | Tag Len  | Tag       | LengthLE |
| 4B      | 1B      | 1B     | 16B    | 12B    | 1B (16)  | 16B       | 8B       |
+---------+---------+--------+--------+--------+----------+-----------+----------+
| Ciphertext + LengthLE bytes                                                                       |
+----------------------------------------------------------------------------------------------------+
```

- **Magic:** `STGX` (chosen so it's printable and unlikely to collide with image/audio codecs)
- **Version:** `0x01` for v1 framing
- **Flags:** bitfield for compression algo, KDF algo, future expansion
- **LengthLE:** little-endian uint64 ciphertext length

#### 4.7.3 Tamper Detection
- AES-GCM authentication tag is checked before decryption
- On failure, the engine raises `IntegrityError`
- The CLI exits with code `EXIT_INTEGRITY` and never writes partial output

---

## 5. Detector Design

### 5.1 Detector Lifecycle
```
register -> discover -> instantiate -> configure -> run -> score -> persist result
```

### 5.2 Detector Base Class
Each detector must expose:

| Attribute | Description |
|---|---|
| `id` | Stable unique identifier |
| `name` | Human-readable name |
| `version` | Detector version |
| `media_type` | `image`, `audio`, `video`, `text`, `metadata`, `universal` |
| `formats` | List of supported file formats |
| `risk_if_missing` | Penalty if not runnable |
| `weight` | Default contribution to score |
| `requires` | List of optional dependencies |

Each detector must implement:

- `applicable(target: Target) -> bool`
- `run(target: Target, ctx: DetectionContext) -> DetectorResult`
- `explain() -> str` (returns a human-readable description)

### 5.3 Detection Context
A `DetectionContext` provides:
- The file as a streamable byte source
- A pre-computed file-level hash (sha256, sha1, md5)
- Format identification result
- A cancellation token
- Per-detector resource limits (time, memory)

### 5.4 Detector Result
A `DetectorResult` contains:
- `detector_id`
- `score` (0-100, contribution to suspicion)
- `confidence` (0-1, detector's own certainty)
- `indicators` (list of structured findings)
- `evidence_refs` (paths or byte offsets to evidence)
- `raw_metrics` (numeric dict for advanced users)
- `notes` (free text)

### 5.5 Universal Detection Engine
For every input file, run the following pipeline:

1. **File identification**
   - Magic byte scan
   - Extension vs content consistency check
   - Container walk (chunks, atoms, frames)
2. **Metadata audit**
   - All known metadata fields
   - High-entropy field detection
   - Anomalous field lengths
3. **Signature scan**
   - Search for known stego-tool markers
   - Search for common magic prefixes
4. **Entropy analysis**
   - Global Shannon entropy
   - Windowed entropy (sliding window)
   - Conditional entropy between channels
5. **Media-specific detection**
   - Run only detectors where `applicable(target) == True`
6. **Confidence scoring**
   - Weighted aggregation
7. **Forensic report**
   - Render to requested format

### 5.6 Detector Categories

#### 5.6.1 Image Detectors
| Detector | Method | Target |
|---|---|---|
| `image.lsb_distribution` | Compare LSB plane to expected random distribution | PNG, BMP, TIFF |
| `image.chi_square` | Chi-square test on pairs of LSB-substituted values | PNG, BMP, TIFF |
| `image.rs_analysis` | Regular-Singular groups analysis | PNG, BMP, TIFF |
| `image.histogram` | Histogram anomalies, "step" effects | PNG, BMP, JPEG, TIFF, WEBP |
| `image.entropy` | Per-channel entropy, joint entropy | All image formats |
| `image.dct_analysis` | DCT coefficient histogram anomalies | JPEG |

#### 5.6.2 Audio Detectors
| Detector | Method | Target |
|---|---|---|
| `audio.spectrogram` | Visualize spectrogram, flag suspicious bands | WAV, FLAC, MP3, OGG |
| `audio.noise_floor` | Analyze noise floor consistency | WAV, FLAC |
| `audio.entropy_window` | Sliding-window entropy | WAV, FLAC |
| `audio.echo_pattern` | Autocorrelation echo signature | WAV, FLAC |
| `audio.bitplane` | Bitplane statistics | WAV, FLAC |

#### 5.6.3 Video Detectors
| Detector | Method | Target |
|---|---|---|
| `video.frame_diff` | Inter-frame difference distribution | All video formats |
| `video.temporal_entropy` | Entropy over time | All video formats |
| `video.keyframe` | Keyframe bitplane statistics | All video formats |
| `video.frame_bitplane` | Per-frame bitplane statistics | All video formats |

#### 5.6.4 Text Detectors
| Detector | Method |
|---|---|
| `text.zero_width_scan` | Count zero-width characters per line |
| `text.unicode_anomaly` | Mix of scripts, confusables, RTL/LTR anomalies |
| `text.whitespace_pattern` | Trailing whitespace, tab/space ratios |

#### 5.6.5 Universal Detectors
| Detector | Method |
|---|---|
| `universal.entropy` | Global Shannon entropy, per-block entropy |
| `universal.signature` | Known stego tool markers |
| `universal.base64_scan` | Search for base64 streams |
| `universal.hex_blob` | Search for long hex blobs |
| `universal.archive_scan` | ZIP/PK/RAR/7z magic inside file |

---

## 6. Confidence Scoring System

### 6.1 Goals
- Produce a single 0-100 score per target.
- Be **defensible**: explain exactly which detectors contributed and by how much.
- Be **calibrated**: scores should map to real-world probability ranges.
- Be **stable**: small input perturbations should not wildly change the score.

### 6.2 Score Range
| Range | Classification |
|---|---|
| 0-30 | Low Suspicion |
| 31-60 | Medium Suspicion |
| 61-100 | High Suspicion |

### 6.3 Methodology
The total score is computed as a **weighted sum of detector contributions**, normalized and clamped.

```
raw_score   = Σ (detector.weight * detector.confidence * indicator_multiplier)
normalized  = clamp(raw_score / max_possible_raw_score * 100, 0, 100)
final_score = apply_recency_penalty(normalized)
```

### 6.4 Detector Weight Table (Default)
| Detector | Weight | Justification |
|---|---|---|
| `image.chi_square` | 1.0 | Strong signal for sequential LSB |
| `image.rs_analysis` | 1.0 | Strong signal for LSB family |
| `image.lsb_distribution` | 0.7 | Moderate signal, can false-positive |
| `image.histogram` | 0.5 | Weak signal, often normal |
| `image.entropy` | 0.4 | Weak signal, contextual |
| `image.dct_analysis` | 0.9 | Strong for JPEG-embedded payloads |
| `audio.spectrogram` | 0.6 | Visual heuristic |
| `audio.echo_pattern` | 0.9 | Strong when present |
| `audio.noise_floor` | 0.5 | Moderate |
| `audio.bitplane` | 0.7 | Moderate |
| `video.frame_diff` | 0.5 | Moderate |
| `video.temporal_entropy` | 0.5 | Moderate |
| `video.keyframe` | 0.6 | Moderate |
| `text.zero_width_scan` | 1.0 | Strong signal |
| `text.whitespace_pattern` | 0.6 | Moderate |
| `text.unicode_anomaly` | 0.8 | Strong when present |
| `universal.signature` | 1.0 | Definitive when matched |
| `universal.entropy` | 0.4 | Weak |
| `universal.base64_scan` | 0.6 | Moderate, contextual |
| `universal.hex_blob` | 0.5 | Moderate |
| `universal.archive_scan` | 0.9 | Strong when matched |

Weights are tunable in the configuration file.

### 6.5 Indicator Multiplier
A single detector can return multiple indicators. Each indicator has a sub-multiplier in the range `[0.0, 1.5]`. The detector's contribution is `weight * confidence * mean(indicator_multipliers)`.

### 6.6 Risk Classification
- **Low (0-30):** File likely benign. Routine scan only.
- **Medium (31-60):** File exhibits at least one suspicious pattern. Recommend manual review.
- **High (61-100):** Multiple strong indicators. Recommend escalation and secondary analysis.

### 6.7 Calibration Goals
- A truly empty file should score **near 0**.
- A clearly LSB-embedded payload in PNG should score **>= 70**.
- A clean JPEG should score **< 15**.
- A file with steghide metadata should be detected by signature detector with high confidence.

### 6.8 Scoring Engine API
- `ScoringEngine.evaluate(results: list[DetectorResult], config: ScoringConfig) -> ScoreReport`
- `ScoreReport` includes the final score, the per-detector contribution table, and a human-readable rationale.

---

## 7. Forensic Workflow

### 7.1 Case File Concept
StegoX supports the notion of a **case** for organizing output across multiple artifacts in an investigation. A case is a directory the user creates; StegoX does not store a database. The case directory layout is:

```
my_case/
├── manifest.yaml          # case metadata (analyst, hash, notes)
├── inputs/                # original evidence copies
├── work/                  # intermediate working files
├── reports/               # generated reports
├── logs/                  # audit logs
├── evidence.jsonl         # append-only evidence ledger
└── chain_of_custody.md    # signed custody log
```

### 7.2 Case Commands
- `stegox case init <path>`
- `stegox case add <file>`
- `stegox case scan`
- `stegox case report`
- `stegox case seal` (compute final manifest hash, sign with GPG if configured)

### 7.3 Hashing
For every evidence file, StegoX computes:
- MD5 (legacy compatibility)
- SHA1 (legacy compatibility)
- SHA256 (primary)
- SHA512 (optional)

### 7.4 Chain of Custody
- Every operation appends an entry to `evidence.jsonl`.
- Each entry includes: timestamp, operator, action, target, hash, parameters, exit code.
- The audit log is append-only. Rotation is manual.

### 7.5 Workflow
1. **Acquire** — copy file to case `inputs/`, hash it.
2. **Identify** — `stegox detect <file>` to determine media type and signatures.
3. **Triage** — `stegox detect --all <file>` to run universal + media-specific detectors.
4. **Deep analyze** — `stegox <media> analyze <file>`.
5. **Attempt extraction** — `stegox <media> extract <file> --strategy <id> --password <pw>`.
6. **Report** — render HTML or JSON report, attach to case.

### 7.6 Audit Log Format
- One JSON object per line
- ISO-8601 timestamps in UTC
- Stable field names: `ts`, `operator`, `cmd`, `args`, `target`, `sha256`, `result`, `exit_code`.

---

## 8. Plugin Architecture

### 8.1 Plugin Goals
- Allow third parties to add embedders, extractors, detectors, and report renderers.
- Allow third parties to add new media format handlers.
- Never require forking or rebuilding StegoX.

### 8.2 Plugin Protocol v1
A plugin is a Python package that declares a `stegox.plugin` entry point. The entry point must resolve to a callable that returns a `PluginSpec` object.

```toml
# pyproject.toml of a plugin package
[project]
name = "stegox-plugin-foo"
version = "0.1.0"

[project.entry-points."stegox.plugin"]
foo = "stegox_plugin_foo:register"
```

The `register()` callable returns a `PluginSpec` with:
- `name`
- `version`
- `detectors`: list of `Detector` subclasses
- `embedders`: list of `Embedder` subclasses
- `extractors`: list of `Extractor` subclasses
- `formats`: list of `FormatHandler` subclasses
- `report_renderers`: list of `ReportRenderer` subclasses

### 8.3 Discovery
- StegoX scans installed packages for the `stegox.plugin` entry point group.
- StegoX also scans `~/.config/stegox/plugins/` for drop-in plugins.
- Discovery is lazy: plugins are loaded only when a command is run.

### 8.4 Plugin Lifecycle Hooks
| Hook | When |
|---|---|
| `on_load(spec)` | When plugin is registered |
| `on_configure(config)` | When global config is loaded |
| `on_command(cmd)` | Before each command runs |
| `on_unload()` | On process exit |

### 8.5 Plugin Security
- Plugins run in the same process as StegoX by default.
- Plugins **must declare** the permissions they require (`network`, `subprocess`, `filesystem`).
- Plugins that request `network` cause StegoX to require a `--allow-network` flag.
- Plugins that do not declare `network` are forbidden from importing `urllib`, `http`, `socket`, `requests`, etc. The plugin loader performs a heuristic check.

### 8.6 Example Plugin
A complete, runnable example plugin lives at `src/stegox/plugins/examples/hello_detector/`. It registers a single `hello-detector` that flags files containing the string "stegox-demo".

### 8.7 Plugin Manifest
A plugin must ship a `MANIFEST.md` with:
- Plugin name and version
- Author
- License
- Detectors/embedders/extractors provided
- Required permissions
- Supported formats
- Stability status (`experimental`, `stable`, `deprecated`)

---

## 9. CLI Specification

### 9.1 CLI Framework
- Built on `typer` with `rich` for output.
- Provides auto-generated help text.
- Provides shell completions for bash, zsh, fish, and PowerShell.
- Provides machine-readable `--json` output globally.

### 9.2 Global Flags
| Flag | Description |
|---|---|
| `--config PATH` | Path to config file (default `~/.config/stegox/config.yaml`) |
| `--log-level LEVEL` | `debug`, `info`, `warning`, `error`, `critical` |
| `--log-file PATH` | Write logs to file in addition to console |
| `--json` | Emit machine-readable JSON |
| `--no-color` | Disable colored output |
| `--quiet` | Suppress non-error output |
| `--verbose` | Increase verbosity |
| `--version` | Show StegoX version |
| `--allow-network` | Permit plugins that request network |
| `--jobs N` | Parallel jobs (default 1) |
| `--no-cache` | Disable detector result cache |

### 9.3 Exit Codes
| Code | Meaning |
|---|---|
| 0 | Success, no findings |
| 1 | Generic failure |
| 2 | Usage error |
| 3 | File not found |
| 4 | Unsupported format |
| 5 | Integrity error (decryption failure) |
| 6 | Permission denied |
| 7 | Plugin error |
| 8 | Timeout |
| 9 | Cancelled by user |
| 10 | Detection completed with findings |
| 64-78 | Reserved (per `<sysexits.h>` style) |
| 100-127 | Plugin-defined |

### 9.4 Top-Level Commands
```
stegox --version
stegox --help
stegox doctor
stegox config show
stegox config set <key> <value>
stegox config get <key>
stegox plugin list
stegox plugin info <name>
stegox case init
stegox case add
stegox case scan
stegox case report
stegox case seal
stegox detect <file>
stegox image ...
stegox audio ...
stegox video ...
stegox text ...
stegox metadata ...
stegox report ...
stegox version
```

### 9.5 Image Command Tree
```
stegox image hide --cover <file> --payload <file> --out <file> --strategy <id> [--password <pw>]
stegox image extract --stego <file> --out <file> --strategy <id> [--password <pw>]
stegox image detect --target <file> [--detectors <id,id,...>]
stegox image analyze --target <file> [--out <dir>]
stegox image list-strategies
stegox image benchmark --strategy <id> --cover <file>
```

### 9.6 Audio Command Tree
```
stegox audio hide --cover <file> --payload <file> --out <file> --strategy <id> [--password <pw>]
stegox audio extract --stego <file> --out <file> --strategy <id> [--password <pw>]
stegox audio detect --target <file> [--detectors <id,id,...>]
stegox audio analyze --target <file> [--out <dir>]
stegox audio list-strategies
```

### 9.7 Video Command Tree
```
stegox video hide --cover <file> --payload <file> --out <file> --strategy <id> [--password <pw>]
stegox video extract --stego <file> --out <file> --strategy <id> [--password <pw>]
stegox video detect --target <file> [--detectors <id,id,...>]
stegox video analyze --target <file> [--out <dir>]
stegox video list-strategies
```

### 9.8 Text Command Tree
```
stegox text hide --cover <file> --payload <file> --out <file> --strategy <id>
stegox text extract --stego <file> --out <file> --strategy <id>
stegox text detect --target <file> [--detectors <id,id,...>]
stegox text analyze --target <file> [--out <dir>]
stegox text list-strategies
```

### 9.9 Metadata Command Tree
```
stegox metadata hide --cover <file> --payload <file> --out <file> --field <name>
stegox metadata extract --target <file> --field <name> [--out <file>]
stegox metadata detect --target <file> [--detectors <id,id,...>]
stegox metadata analyze --target <file>
stegox metadata list-fields
```

### 9.10 Detect Command Tree
```
stegox detect --target <file>
stegox detect --target <dir> [--recursive]
stegox detect --all <file>
stegox detect --list-detectors
stegox detect --detectors <id,id,...> --target <file>
```

### 9.11 Report Command Tree
```
stegox report render --input <json> --format <console|json|html> --out <file>
stegox report template list
stegox report template export <name> --out <file>
```

### 9.12 Doctor Command
```
stegox doctor
```
Checks:
- Python version
- Optional dependency presence
- Plugin loading
- File permissions for config directory
- Disk space

### 9.13 Output Conventions
- All non-error progress goes to **stderr**.
- All result data goes to **stdout**.
- This allows piping into `jq`, `grep`, etc.
- `--json` wraps stdout in a single JSON document.

### 9.14 Example Invocations
```bash
# Hide a payload in a PNG using password-protected LSB
stegox image hide --cover cat.png --payload secret.txt --out cat_stego.png \
    --strategy password-embed --password "correct horse"

# Extract with the same password
stegox image extract --stego cat_stego.png --out recovered.bin \
    --strategy password-embed --password "correct horse"

# Run all detectors
stegox detect --all suspicious.png

# Run specific detectors
stegox image detect --target suspicious.png --detectors image.chi_square,image.rs_analysis

# Generate an HTML report
stegox report render --input result.json --format html --out report.html
```

---

## 10. Reporting Architecture

### 10.1 Report Data Model
A report is a versioned JSON document with this structure:

```json
{
  "report_version": "1.0",
  "tool": {
    "name": "stegox",
    "version": "1.0.0",
    "commit": "abc1234"
  },
  "target": {
    "path": "/path/to/file",
    "sha256": "...",
    "size": 12345,
    "media_type": "image",
    "format": "png"
  },
  "scan": {
    "started_at": "2026-06-03T12:00:00Z",
    "finished_at": "2026-06-03T12:00:05Z",
    "duration_ms": 5000
  },
  "score": {
    "value": 72,
    "classification": "high",
    "rationale": "..."
  },
  "indicators": [
    {
      "id": "image.chi_square",
      "name": "Chi-Square Analysis",
      "verdict": "suspicious",
      "score": 0.85,
      "weight": 1.0,
      "metrics": { "...": "..." }
    }
  ],
  "evidence": [
    {
      "kind": "byte_range",
      "offset": 1024,
      "length": 256,
      "description": "High-entropy block in metadata section"
    }
  ],
  "recommendations": [
    "Run image.rs_analysis to confirm LSB embedding",
    "Attempt extraction with known steganography tools"
  ]
}
```

### 10.2 Console Renderer
- Uses `rich` for tables, panels, and color-coded verdicts.
- Sections: Header, Target, Score, Indicators, Evidence, Recommendations.
- Color rules:
  - Low = green
  - Medium = yellow
  - High = red

### 10.3 JSON Renderer
- Emits the report data model verbatim.
- Stable key ordering.
- UTF-8 encoded.
- Schema validated against `docs/report.schema.json`.

### 10.4 HTML Renderer
- Self-contained HTML with embedded CSS and JS.
- No CDN, no external resources.
- Dark and light themes.
- Print-friendly CSS for PDF export via browser.
- Interactive indicators (expand/collapse).
- Built on `Jinja2` templates committed in the repo.

### 10.5 PDF Renderer (Optional)
- HTML is the source of truth.
- PDF is produced via a local headless browser if the user has it installed.
- StegoX never installs a headless browser as a hard dependency.

### 10.6 Report Schemas
- JSON Schema files live under `docs/schemas/`.
- Schemas are versioned alongside the report model.
- Schema changes require an RFC.

### 10.7 Recommendations Engine
A small, rules-based engine that maps indicator patterns to recommended next steps. Example:

| Pattern | Recommendation |
|---|---|
| `image.chi_square` and `image.rs_analysis` both positive | "Run `stegox image extract --strategy password-embed`" |
| `universal.signature` matched `steghide` | "Try `steghide extract` with candidate passwords" |
| `audio.echo_pattern` positive | "Run `stegox audio extract --strategy echo-hiding`" |

---

## 11. Security Architecture

### 11.1 Threat Model
**In scope:**
- Tampering with cover files during analysis
- Accidental overwrite of evidence
- Memory disclosure of passwords or keys
- Supply chain attacks via dependencies
- Plugin supply chain attacks

**Out of scope:**
- Side-channel attacks on the host OS
- Hardware keyloggers
- Coercion of the operator

### 11.2 Password Handling
- Passwords are read from CLI args, environment variables, or `STDIN`.
- Passwords are never written to logs.
- Passwords are zeroized from memory after use.
- The CLI accepts `@password-file` syntax to read a password from a file.

### 11.3 Memory Hygiene
- Keys and plaintext payloads are stored in bytearrays and explicitly overwritten when no longer needed.
- `secrets.compare_digest` is used for all secret comparisons.

### 11.4 Filesystem Hygiene
- All writes go to explicit `--out` paths. StegoX never overwrites a file in place.
- A confirmation prompt is required when the output path exists (skippable via `--yes`).
- StegoX never follows symlinks during analysis by default (`--follow-symlinks` to override).

### 11.5 Dependency Security
- CI runs `pip-audit` and `safety` on every PR.
- Lockfiles are committed.
- `dependabot` is configured for weekly updates.
- Critical CVEs cause a hotfix release.

### 11.6 Code Security
- CI runs `bandit` and `semgrep` with conservative rule sets.
- Pre-commit hooks run `ruff`, `mypy`, and `bandit`.
- All unsafe deserialization paths are reviewed.

### 11.7 Audit Trail
- Every command invocation is logged.
- Logs include: timestamp, command, target SHA256, parameters (redacted).
- Logs are append-only.
- Logs are stored in `~/.local/state/stegox/logs/` by default.

### 11.8 Reporting Security
- Reports never embed raw passwords.
- Reports never embed raw payloads unless the user opts in via `--include-payload` (off by default).

---

## 12. Testing Strategy

### 12.1 Test Pyramid
- **Unit tests** — fast, isolated, no I/O.
- **Integration tests** — exercise modules with real fixture files.
- **Property-based tests** — Hypothesis-driven, for framing and crypto.
- **Regression tests** — CTF-style and corpus-driven.
- **Performance tests** — benchmark suite with thresholds.

### 12.2 Test Layout
Reflects source layout under `tests/unit/...` mirrored against `src/stegox/...`.

### 12.3 Fixture Strategy
- Generate fixtures via `tools/generate_fixtures.py` to keep repo small.
- Commit only minimal "golden" fixtures.
- Use `pytest` fixtures for lazy loading.
- Use a content-addressable fixture store.

### 12.4 Determinism
- All tests must be deterministic. RNG must be seeded.
- No tests rely on the wall clock.
- No tests rely on network or environment-specific paths.

### 12.5 Coverage Goals
- Core engine: >= 90%
- Detectors: >= 85%
- Crypto: 100% branch coverage
- CLI: >= 80% (snapshot tests on `--help`)

### 12.6 Property-Based Tests
- Framing round-trips
- Encrypt/decrypt round-trips for every embedder/extractor pair
- Detector score monotonicity
- Plugin spec validation

### 12.7 Regression Corpus
- A `corpus/` directory of public CTF challenges (with permission) is maintained.
- Each challenge is documented with: source URL, license, solution steps.

### 12.8 Performance Tests
- `bench_hide.py` measures MB/s for each embedder.
- `bench_detect.py` measures detector latency on standard fixtures.
- Results are tracked in CI with thresholds.

### 12.9 CI Test Stages
1. Lint (ruff, mypy, bandit, semgrep)
2. Unit tests on Linux, macOS, Windows
3. Integration tests
4. Property-based tests
5. Coverage report

### 12.10 Fuzzing
- A fuzz harness lives under `tests/fuzz/`.
- `atheris` is used for Python fuzzing.
- Critical entry points fuzzed: framing parser, file identifier, plugin loader.

---

## 13. Open-Source Governance

### 13.1 Licensing
- Default license: **MIT** for code, **CC-BY-4.0** for documentation.
- Dual-license options evaluated case by case.
- All third-party code must have a compatible license and be attributed.

### 13.2 Code of Conduct
- Adopts the Contributor Covenant v2.1.

### 13.3 Contribution Workflow
1. **Open or claim an issue** — describe the problem or proposal.
2. **Discuss the design** — maintainers and community weigh in.
3. **Write an RFC** (for non-trivial changes) under `rfcs/`.
4. **Submit a PR** — must pass CI and be reviewed by a code owner.
5. **Merge** — squash merge, with the RFC link in the commit body.

### 13.4 Coding Standards
- Python 3.10+ minimum, 3.12 recommended.
- PEP 8 + `ruff` defaults.
- Type hints everywhere; `mypy --strict` for `core/`, `engine/`, `security/`.
- Docstrings in Google style.
- No wildcard imports.
- No mutable default arguments.
- No bare `except:`.
- No `print` in library code.
- Public APIs must have a docstring and a type signature.

### 13.5 Branching Model
- `main` — always releasable.
- Feature branches — `feat/<short-name>`.
- Bugfix branches — `fix/<short-name>`.
- Release branches — `release/vX.Y.Z`.

### 13.6 Commit Message Style
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).
- Scope is the module name.
- Body explains the *why*.

### 13.7 Code Owners
- `CODEOWNERS` defines module-level ownership.
- Each module has at least one owner.
- Owners are responsible for reviewing PRs in their area.

### 13.8 Security Policy
- `SECURITY.md` defines how to report vulnerabilities.
- Critical issues are handled via private disclosure and a 90-day disclosure deadline.

### 13.9 Governance Roles
- **Maintainers** — merge rights, release authority.
- **Reviewers** — review rights, no merge.
- **Triagers** — issue triage rights only.
- **Contributors** — everyone else.

### 13.10 Voting and Disputes
- Maintainer decisions are documented in `MAINTAINERS.md`.
- Disputes go to public discussion first, then a maintainer vote.

---

## 14. Release Strategy

### 14.1 Versioning
- Semantic Versioning 2.0.
- Public API stability promises:
  - Major versions may break CLI flags and report schema.
  - Minor versions add features but preserve backward compatibility.
  - Patch versions are bug fixes only.

### 14.2 Release Cadence
- Minor releases every 8 weeks.
- Patch releases as needed for security and bug fixes.
- LTS branches maintained for 12 months.

### 14.3 Release Process
1. Cut a `release/vX.Y.Z` branch.
2. Update `CHANGELOG.md`.
3. Bump version in `pyproject.toml` and `src/stegox/version.py`.
4. Tag the commit.
5. GitHub Actions builds wheels for Linux, macOS, Windows.
6. Sign the wheels and tarball with a maintainer GPG key.
7. Generate SHA256 manifest.
8. Publish to PyPI.
9. Publish GitHub Release with notes.
10. Announce on discussion forum.

### 14.4 Distribution Artifacts
- Source tarball
- `manylinux` wheels for x86_64 and aarch64
- macOS wheels for x86_64 and arm64
- Windows wheels for x86_64
- Hashes and signatures
- SBOM (CycloneDX)

### 14.5 Release Channels
- **Stable** — `pip install stegox`
- **Pre-release** — `pip install --pre stegox`
- **Nightly** — `pip install stegox-nightly`

### 14.6 Deprecation Policy
- Deprecated features are marked in `CHANGELOG.md`.
- Deprecated features continue to work for at least one minor release.
- Deprecated features raise a `DeprecationWarning`.

---

## 15. Development Roadmap

### 15.1 Phase 0 — Foundations (Weeks 1-3)
- Repo scaffolding
- CI/CD skeleton
- Plugin protocol v1
- Crypto module and framing
- CLI dispatcher

### 15.2 Phase 1 — Image Module (Weeks 4-7)
- PNG/BMP hide/extract
- LSB distribution, chi-square, RS detectors
- JSON + console reports

### 15.3 Phase 2 — Audio Module (Weeks 8-10)
- WAV hide/extract
- Spectrogram and noise floor detectors
- HTML report

### 15.4 Phase 3 — Metadata Module (Weeks 11-12)
- EXIF/XMP/IPTC
- Metadata audit detectors
- Universal detectors

### 15.5 Phase 4 — Text Module (Weeks 13-14)
- Zero-width, whitespace, homoglyph
- Text detectors

### 15.6 Phase 5 — Video Module (Weeks 15-18)
- MP4/MKV
- Frame-based hide/extract
- Video detectors

### 15.7 Phase 6 — Forensics (Weeks 19-20)
- Case files
- Chain of custody
- Hashing and audit log

### 15.8 Phase 7 — Polish (Weeks 21-22)
- Performance benchmarks
- Documentation site
- Public 1.0 release

### 15.9 Phase 8 — Optional GUI (Post-1.0)
- Tauri/Electron/PySide6 desktop app
- Wraps the same Python engine via subprocess

---

## 16. Future Enhancements

### 16.1 Advanced Embedders
- Wet paper codes
- Matrix encoding
- F5-style JPEG embedding
- BCH-syndrome coding

### 16.2 Advanced Detectors
- Deep-learning based steganalysis (with a strict, opt-in, on-device model)
- Universal blind detection via SRM/PEV features
- Color-rich model detectors for palette images

### 16.3 Rich Media Support
- DOCX
- PDF
- EPUB
- SVG (text + image combo)

### 16.4 Network Capture Module
- Read-only PCAP parsing for covert channel analysis
- Strictly offline; no live capture

### 16.5 Mobile Companion
- A read-only iOS/Android viewer for reports (no execution)
- Reports are static, so the viewer is just a renderer

### 16.6 Distributed Scan Mode
- Optional peer-to-peer scan over LAN for large corpora
- Default off; opt-in with explicit consent prompt
- All peers must be operator-controlled

### 16.7 Tauri/Electron/PySide6 GUI
- A desktop GUI that wraps the CLI
- Reuses all Python engines via subprocess
- Local-only; no network

---

## Appendix A — Detector Reference Matrix

| Detector ID | Media | Formats | Default Weight | Confidence Range |
|---|---|---|---|---|
| image.lsb_distribution | image | png,bmp,tiff | 0.7 | 0.0-1.0 |
| image.chi_square | image | png,bmp,tiff | 1.0 | 0.0-1.0 |
| image.rs_analysis | image | png,bmp,tiff | 1.0 | 0.0-1.0 |
| image.histogram | image | png,bmp,jpeg,tiff,webp | 0.5 | 0.0-1.0 |
| image.entropy | image | all | 0.4 | 0.0-1.0 |
| image.dct_analysis | image | jpeg | 0.9 | 0.0-1.0 |
| audio.spectrogram | audio | wav,flac,mp3,ogg | 0.6 | 0.0-1.0 |
| audio.noise_floor | audio | wav,flac | 0.5 | 0.0-1.0 |
| audio.entropy_window | audio | wav,flac | 0.4 | 0.0-1.0 |
| audio.echo_pattern | audio | wav,flac | 0.9 | 0.0-1.0 |
| audio.bitplane | audio | wav,flac | 0.7 | 0.0-1.0 |
| video.frame_diff | video | all | 0.5 | 0.0-1.0 |
| video.temporal_entropy | video | all | 0.5 | 0.0-1.0 |
| video.keyframe | video | all | 0.6 | 0.0-1.0 |
| video.frame_bitplane | video | all | 0.6 | 0.0-1.0 |
| text.zero_width_scan | text | txt,md,docx | 1.0 | 0.0-1.0 |
| text.unicode_anomaly | text | txt,md,docx | 0.8 | 0.0-1.0 |
| text.whitespace_pattern | text | txt,md,docx | 0.6 | 0.0-1.0 |
| universal.entropy | any | any | 0.4 | 0.0-1.0 |
| universal.signature | any | any | 1.0 | 0.0-1.0 |
| universal.base64_scan | any | any | 0.6 | 0.0-1.0 |
| universal.hex_blob | any | any | 0.5 | 0.0-1.0 |
| universal.archive_scan | any | any | 0.9 | 0.0-1.0 |

---

## Appendix B — Glossary

| Term | Definition |
|---|---|
| **Cover** | The original, unaltered medium |
| **Stego** | The medium after embedding |
| **Payload** | The data being hidden |
| **Carrier** | Synonym for cover |
| **Steganalysis** | Detection of steganography |
| **LSB** | Least Significant Bit |
| **DCT** | Discrete Cosine Transform |
| **PRNG** | Pseudorandom Number Generator |
| **KDF** | Key Derivation Function |
| **AEAD** | Authenticated Encryption with Associated Data |
| **CSPRNG** | Cryptographically Secure Pseudorandom Number Generator |
| **DFIR** | Digital Forensics and Incident Response |
| **CTF** | Capture The Flag |
| **Shannon Entropy** | Information-theoretic entropy measure |
| **RS Analysis** | Regular-Singular groups analysis |
| **Chi-Square** | Statistical test for distribution similarity |
| **Chain of Custody** | Chronological record of evidence handling |

---

**End of Specification v1.0**
