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

# Import and run the main function
from src.main import main

if __name__ == "__main__":
    print("Starting ONOTE application...")
    main() 