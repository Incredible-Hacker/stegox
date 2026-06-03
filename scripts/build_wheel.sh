#!/usr/bin/env bash
# Build sdist and wheels for StegoX.
set -euo pipefail

python -m pip install --upgrade build
python -m build
