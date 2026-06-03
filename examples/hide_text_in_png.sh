#!/usr/bin/env bash
# Hide a payload in a PNG using password-protected LSB.
set -euo pipefail

COVER="${1:-cover.png}"
PAYLOAD="${2:-secret.txt}"
OUT="${3:-cover_stego.png}"
PASSWORD="${4:-correct horse battery staple}"

stegox image hide \
    --cover "$COVER" \
    --payload "$PAYLOAD" \
    --out "$OUT" \
    --strategy password-embed \
    --password "$PASSWORD"
