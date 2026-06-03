#!/usr/bin/env bash
# Run the StegoX test suite.
set -euo pipefail

pytest tests/ -n auto --cov=stegox --cov-report=term-missing
