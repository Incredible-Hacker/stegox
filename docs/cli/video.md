# `stegox video`

Hide, extract, detect, and analyze video.

## Subcommands

- `video hide`
- `video extract`
- `video detect`
- `video analyze`
- `video list-strategies`

## Strategies

| ID | Description | Formats |
|---|---|---|
| `frame-lsb` | LSB across keyframes | MP4, AVI, MKV, MOV |
| `frame-lsb-rand` | PRNG-ordered frame LSB | MP4, AVI, MKV, MOV |
| `motion-region` | Embed in high-motion regions | MP4, AVI, MKV, MOV |
| `keyframe-dct` | DCT embed in I-frames | MP4, AVI, MKV, MOV |
