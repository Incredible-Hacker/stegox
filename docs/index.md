# StegoX

> Local-first steganography, steganalysis, and digital forensics toolkit.

StegoX is a backendless, single-binary Python toolkit that unifies five
operations across every supported media type:

- **Hide** — embed payloads in image, audio, video, text, or metadata.
- **Extract** — recover hidden payloads with optional password protection.
- **Detect** — run a pluggable, weighted detector pipeline.
- **Analyze** — produce a deep forensic profile.
- **Report** — render console, JSON, or self-contained HTML reports.

## Why StegoX?

DFIR analysts, CTF players, and security researchers deserve a single
toolkit that:

- **Runs entirely on the analyst's machine** — no servers, no cloud, no telemetry.
- **Has a stable, scriptable CLI** — composable with standard Unix tools.
- **Supports plugins** — extend detection, embedders, and report renderers.
- **Is forensically defensible** — every operation is hashed, logged, and reproducible.

## Quick start

```bash
pip install stegox
stegox image hide --cover cat.png --payload secret.txt --out cat_stego.png \
    --strategy password-embed --password "correct horse battery staple"
stegox image extract --stego cat_stego.png --out recovered.bin \
    --strategy password-embed --password "correct horse battery staple"
stegox detect --all suspicious.png
stegox report render --input result.json --format html --out report.html
```

## Project layout

The full project specification lives in [`SPEC.md`](SPEC.md). The high-level
component map is:

```
CLI  ->  Engine  ->  Modules + Detectors  ->  Reports
            |
            v
        Security, Forensics, Plugins
```

## Modules

- [Image](cli/image.md): PNG, BMP, JPEG, TIFF, WEBP
- [Audio](cli/audio.md): WAV, FLAC, MP3, OGG
- [Video](cli/video.md): MP4, AVI, MKV, MOV
- [Text](cli/text.md): TXT, MD
- [Metadata](cli/metadata.md): EXIF, XMP, IPTC, ID3, Vorbis, MP4 atoms

## Contributing

See [CONTRIBUTING.md](https://github.com/Incredible-Hacker/stegox/blob/main/CONTRIBUTING.md)
and the [RFC process](rfcs/0001-record-process.md).

## License

MIT — see [LICENSE](https://github.com/Incredible-Hacker/stegox/blob/main/LICENSE).
