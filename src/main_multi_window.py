#!/usr/bin/env python3
"""
ONOTE Multi-Window Main Entry Point
Launches ONOTE with page-based desktop architecture.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.gui.application_manager import ApplicationManager, create_application_manager
from src import __version__


def main():
    """Main entry point for ONOTE multi-window version."""
    print("🎵 ONOTE Multi-Window Version Starting...")
    print(f"📝 Version: {__version__}")
    print("🖥️ Architecture: Page-Based Desktop")
    print()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ONOTE")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("ONOTE")
    app.setOrganizationDomain("onote.music")
    
    # Set high DPI scaling (handled automatically in PyQt6)
    # app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)  # Removed - not needed in PyQt6
    
    # Set high DPI pixmaps (handled automatically in PyQt6)
    # app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)  # Removed - not needed in PyQt6
    
    # Set application icon (if available)
    # icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
    # if icon_path.exists():
    #     app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create application manager
    manager = create_application_manager(app)
    
    print("✅ ONOTE Desktop initialized successfully")
    print("📄 Initial desktop window created")
    print("🎯 Ready for page-based music notation editing")
    print()
    
    # Start application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main()) 