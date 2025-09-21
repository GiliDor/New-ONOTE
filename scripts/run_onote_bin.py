#!/usr/bin/env python3
import os
import sys
import subprocess


def main() -> int:
    project_root = "/Users/gilidor/Projects/New-ONOTE"
    binary_path = os.path.join(project_root, "ONOTE", "ONOTE")

    if not os.path.exists(binary_path) or not os.access(binary_path, os.X_OK):
        sys.stderr.write(f"ERROR: Packaged ONOTE binary not found or not executable at: {binary_path}\n")
        return 1

    # Forward any args to the packaged binary
    args = [binary_path] + sys.argv[1:]

    try:
        completed = subprocess.run(args, check=False)
        return completed.returncode
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

import os
import subprocess
import sys

BIN = "/Users/gilidor/Projects/New-ONOTE/ONOTE/ONOTE"

if not os.path.exists(BIN):
    print(f"Executable not found: {BIN}")
    sys.exit(1)

subprocess.Popen([BIN], cwd=os.path.dirname(BIN))


