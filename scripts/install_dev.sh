#!/usr/bin/env bash
# Install StegoX in editable mode with dev dependencies.
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,extras]"
pre-commit install
