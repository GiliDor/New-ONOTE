#!/bin/bash
set -euo pipefail
ROOT="/Users/gilidor/Projects/New-ONOTE"
PY="$ROOT/venv/bin/python"
export PYTHONPATH="$ROOT/src"
exec "$PY" "$ROOT/run.py" "$@"
