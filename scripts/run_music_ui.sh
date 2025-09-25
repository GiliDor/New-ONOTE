#!/bin/bash
# activate venv if it exists
source "$(git rev-parse --show-toplevel)/venv/bin/activate" 2>/dev/null
# use python3 (works with or without the venv on macOS)
python3 -m src.gui.music.main "$@"
