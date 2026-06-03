#!/usr/bin/env bash
# Run every applicable detector against a target.
set -euo pipefail

TARGET="${1:?usage: detect_image.sh <file>}"
JSON_OUT="${2:-report.json}"
HTML_OUT="${3:-report.html}"

stegox detect --all "$TARGET" --json > "$JSON_OUT"
stegox report render --input "$JSON_OUT" --format html --out "$HTML_OUT"
echo "Wrote $JSON_OUT and $HTML_OUT"
