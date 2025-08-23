#!/usr/bin/env python3
"""
Test script for Mac 2-finger zooming functionality in ONOTE Desktop Window.
This script tests the pinch gesture recognition and zoom behavior.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QTextEdit
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from src.gui.desktop_window import DesktopWindow
from src.gui.application_manager import ApplicationManager


class ZoomTestWindow(QMainWindow):
    """Test window to verify zoom functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ONOTE Mac Zoom Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("ONOTE Mac 2-Finger Zoom Test")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add instructions
        instructions = QTextEdit()
        instructions.setMaximumHeight(150)
        instructions.setPlainText("""
Mac 2-Finger Zoom Test Instructions:

1. Click 'Launch Desktop Window' to open the ONOTE desktop
2. Use two fingers on your Mac trackpad to pinch in/out on the music page
3. The page should zoom in/out smoothly with the pinch gesture
4. Zoom should be constrained between 30% and 300%
5. The status bar should show the current zoom percentage
6. The view should maintain proper centering during zoom

Expected Behavior:
- Pinch outward (spread fingers): Zoom in
- Pinch inward (bring fingers together): Zoom out
- Smooth zoom animation
- Zoom percentage displayed in status bar
- Page stays centered during zoom
- Zoom limits respected (30% - 300%)

Keyboard shortcuts also work:
- Ctrl++: Zoom in
- Ctrl+-: Zoom out  
- Ctrl+0: Reset zoom to 100%
        """)
        instructions.setReadOnly(True)
        layout.addWidget(instructions)
        
        # Add launch button
        launch_button = QPushButton("Launch Desktop Window")
        launch_button.setFont(QFont("Arial", 12))
        launch_button.clicked.connect(self.launch_desktop)
        layout.addWidget(launch_button)
        
        # Add status
        self.status_label = QLabel("Ready to test Mac 2-finger zooming")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # Store desktop window reference
        self.desktop_window = None
        
    def launch_desktop(self):
        """Launch the desktop window for testing."""
        try:
            # Create app manager
            app_manager = ApplicationManager()
            
            # Create desktop window
            self.desktop_window = DesktopWindow(app_manager)
            
            # Connect to signals for testing
            self.desktop_window.page_mode_changed.connect(self.on_mode_changed)
            
            # Update status
            self.status_label.setText("Desktop window launched! Test pinch gestures on the music page.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            
            print("✅ Desktop window launched successfully")
            print("📱 Test Mac 2-finger pinch gestures on the music page")
            print("🔍 Zoom should work smoothly between 30% and 300%")
            
        except Exception as e:
            self.status_label.setText(f"Error launching desktop: {str(e)}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            print(f"❌ Error launching desktop: {e}")
    
    def on_mode_changed(self, mode):
        """Handle mode changes."""
        print(f"🔄 Mode changed to: {mode}")


def test_zoom_functionality():
    """Test the zoom functionality."""
    print("🧪 Testing ONOTE Mac 2-Finger Zoom Functionality")
    print("=" * 60)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = ZoomTestWindow()
    test_window.show()
    
    print("✅ Test window created")
    print("📋 Instructions displayed in the test window")
    print("🚀 Click 'Launch Desktop Window' to begin testing")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    test_zoom_functionality() 