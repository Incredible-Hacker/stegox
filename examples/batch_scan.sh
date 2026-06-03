#!/usr/bin/env bash
# Batch scan a directory of suspicious files.
set -euo pipefail

DIR="${1:?usage: batch_scan.sh <directory>}"
OUT="${2:-reports}"

mkdir -p "$OUT"
shopt -s nullglob
for f in "$DIR"/*; do
    name=$(basename "$f")
    echo "[*] scanning $name"
    stegox detect --all "$f" --json > "$OUT/$name.json" || true
    stegox report render --input "$OUT/$name.json" --format html --out "$OUT/$name.html" || true
done
echo "Reports written to $OUT"
