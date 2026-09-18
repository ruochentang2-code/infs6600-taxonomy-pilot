#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
python src/pipeline.py demo
python src/pipeline.py replay
