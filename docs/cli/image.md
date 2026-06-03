# `stegox image`

Hide, extract, detect, and analyze images.

## Subcommands

- `image hide` — embed a payload
- `image extract` — recover a payload
- `image detect` — run image-specific detectors
- `image analyze` — deep analysis
- `image list-strategies` — list available strategies

## Examples

```bash
# Hide a payload using sequential LSB
stegox image hide \
    --cover cat.png --payload secret.txt --out cat_stego.png \
    --strategy lsb

# Hide with password-protected framing
stegox image hide \
    --cover cat.png --payload secret.txt --out cat_stego.png \
    --strategy password-embed --password "hunter2"

# Recover the payload
stegox image extract \
    --stego cat_stego.png --out recovered.bin \
    --strategy password-embed --password "hunter2"

# Run only chi-square and RS analysis
stegox image detect --target suspicious.png \
    --detectors image.chi_square,image.rs_analysis
```

## Strategies

| ID | Description | Formats |
|---|---|---|
| `lsb` | Sequential LSB across all channels | PNG, BMP, TIFF, WEBP |
| `lsb-rgb` | Sequential LSB across RGB only | PNG, BMP, TIFF, WEBP |
| `randomized-lsb` | PRNG-ordered LSB keyed by password | PNG, BMP, TIFF, WEBP |
| `password-embed` | Randomized LSB + AES-GCM framing | PNG, BMP, TIFF, WEBP |
| `dct-jpeg` | DCT coefficient embedding | JPEG |
