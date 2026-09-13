#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
python scripts/verify_manifest.py
python -m unittest discover -s tests -v
