# Detectors

StegoX ships a curated set of detectors across five media types plus a
universal pipeline. Every detector is a stateless callable that
returns a `DetectorResult`.

## Image

- `image.lsb_distribution` — LSB plane divergence from uniform 0.5
- `image.chi_square` — Westfeld-Pfitzmann chi-square on color pairs
- `image.rs_analysis` — Fridrich-Goljan-Du RS analysis
- `image.histogram` — LSB pair equalization heuristic
- `image.entropy` — Per-channel entropy variance
- `image.dct_analysis` — JPEG DCT coefficient proxy

## Audio

- `audio.spectrogram` — Mid/high band energy gap
- `audio.noise_floor` — High-band coefficient of variation
- `audio.entropy_window` — Sliding-window entropy spread
- `audio.echo_pattern` — Cepstral echo signature
- `audio.bitplane` — Per-block LSB uniformity

## Video

- `video.frame_diff` — Inter-frame difference variance
- `video.temporal_entropy` — Frame-level entropy variance
- `video.keyframe` — Keyframe LSB distribution
- `video.frame_bitplane` — Per-frame LSB deviation

## Text

- `text.zero_width_scan` — Counts zero-width characters
- `text.unicode_anomaly` — Confusables and mixed-script detection
- `text.whitespace_pattern` — Trailing space/tab counts

## Universal

- `universal.entropy` — Shannon entropy on the first 1 MiB
- `universal.signature` — Known stego tool signatures
- `universal.base64_scan` — Long base64-like strings
- `universal.hex_blob` — Long hex blobs
- `universal.archive_scan` — ZIP/RAR/7z magic inside non-archives
