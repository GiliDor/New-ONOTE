#!/usr/bin/env python3
import os
import sys

sys.argv[0] = "ONOTE"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from src.gui.music.main import main

if __name__ == "__main__":
    main()


