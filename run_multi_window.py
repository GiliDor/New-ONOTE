#!/usr/bin/env python3
"""
ONOTE Page-Based Desktop Launcher
Simple launcher for the new page-based desktop ONOTE version
"""

import sys
import os
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Set environment variables
os.environ["PYTHONNAME"] = "ONOTE"
os.environ["PYTHONAPPLICATION"] = "ONOTE"
os.environ["PYTHON_APP_NAME"] = "ONOTE"
os.environ["PYTHON_APP_DISPLAY_NAME"] = "ONOTE Page-Based Desktop"
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

if __name__ == "__main__":
    print("🎵 Launching ONOTE Page-Based Desktop...")
    print("📝 Version: 2.0.0 with Page-Based Desktop Architecture")
    print("🖥️ Features: Resizable desktop, floating music page, independent zoom")
    print()
    
    try:
        from src.main_multi_window import main
        sys.exit(main())
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you're running from the ONOTE project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Launch error: {e}")
        sys.exit(1) 