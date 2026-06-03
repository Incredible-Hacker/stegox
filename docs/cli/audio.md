# `stegox audio`

Hide, extract, detect, and analyze audio.

## Subcommands

- `audio hide`
- `audio extract`
- `audio detect`
- `audio analyze`
- `audio list-strategies`

## Examples

```bash
stegox audio hide \
    --cover song.wav --payload secret.bin --out song_stego.wav \
    --strategy pcm-lsb

stegox audio extract \
    --stego song_stego.wav --out recovered.bin \
    --strategy pcm-lsb --payload-bytes 1024
```

## Strategies

| ID | Description | Formats |
|---|---|---|
| `pcm-lsb` | Sequential LSB on PCM samples | WAV, FLAC |
| `pcm-lsb-rand` | PRNG-ordered LSB | WAV, FLAC |
| `echo-hiding` | Echo kernel modulation | WAV, FLAC |
| `phase-coding` | Phase spectrum embedding | WAV, FLAC |
