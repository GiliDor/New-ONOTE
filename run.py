#!/usr/bin/env python3
import os
import sys

# Set process name for macOS dock/Activity Monitor
sys.argv[0] = "ONOTE"

# Set environment variables
os.environ['PYTHONNAME'] = 'ONOTE'
os.environ['PYTHONAPPLICATION'] = 'ONOTE'
os.environ['PYTHON_APP_NAME'] = 'ONOTE'
os.environ['PYTHON_APP_DISPLAY_NAME'] = 'ONOTE'
os.environ['PYTHONUNBUFFERED'] = '1'

# Additional macOS process name setting
if sys.platform == 'darwin':
    try:
        import ctypes
        if hasattr(ctypes.pythonapi, 'Py_SetProgramName'):
            name = 'ONOTE'.encode('utf-8')
            ctypes.pythonapi.Py_SetProgramName(name)
    except ImportError:
        pass

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the main function with robust path handling
try:
    # Primary: new entry under music package
    from src.gui.music.main import main
except ModuleNotFoundError:
    try:
        # Secondary: older location
        from src.main import main
    except ModuleNotFoundError:
        # Fallback: add src/ directly and import package path
        src_path = os.path.join(project_root, 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        try:
            from gui.music.main import main
        except ModuleNotFoundError:
            from music.main import main

if __name__ == "__main__":
    print("Starting ONOTE application...")
    main() 