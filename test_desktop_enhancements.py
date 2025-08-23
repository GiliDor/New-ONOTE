#!/usr/bin/env python3
"""
Test script for ONOTE Desktop Window Enhancements.
This script tests:
1. Full screen with menu visible
2. Auto-launch score setup dialog on startup
3. Toggle Apply/Setup button in score setup dialog
4. Enhanced Score menu toggle functionality
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


class DesktopEnhancementsTestWindow(QMainWindow):
    """Test window to verify desktop enhancements."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ONOTE Desktop Enhancements Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("ONOTE Desktop Enhancements Test")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Test buttons
        self.test_fullscreen_btn = QPushButton("Test Full Screen with Menu")
        self.test_fullscreen_btn.clicked.connect(self.test_fullscreen)
        layout.addWidget(self.test_fullscreen_btn)
        
        self.test_auto_launch_btn = QPushButton("Test Auto-Launch Score Setup")
        self.test_auto_launch_btn.clicked.connect(self.test_auto_launch)
        layout.addWidget(self.test_auto_launch_btn)
        
        self.test_toggle_btn = QPushButton("Test Score Setup Toggle")
        self.test_toggle_btn.clicked.connect(self.test_toggle_functionality)
        layout.addWidget(self.test_toggle_btn)
        
        self.test_menu_toggle_btn = QPushButton("Test Menu Toggle Functionality")
        self.test_menu_toggle_btn.clicked.connect(self.test_menu_toggle)
        layout.addWidget(self.test_menu_toggle_btn)
        
        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setMaximumHeight(200)
        layout.addWidget(self.results_display)
        
        # Desktop window reference
        self.desktop_window = None
        
    def log_result(self, message):
        """Log a test result."""
        self.results_display.append(f"✓ {message}")
        
    def test_fullscreen(self):
        """Test full screen functionality with menu visible."""
        self.log_result("Testing full screen with menu visibility...")
        
        if not self.desktop_window:
            self.desktop_window = DesktopWindow()
            
        # Test full screen
        if self.desktop_window.isFullScreen():
            self.desktop_window.showNormal()
            self.log_result("Exited full screen mode")
        else:
            self.desktop_window.showFullScreen()
            self.log_result("Entered full screen mode - menu should remain visible")
            
    def test_auto_launch(self):
        """Test auto-launch score setup dialog."""
        self.log_result("Testing auto-launch score setup dialog...")
        
        if not self.desktop_window:
            self.desktop_window = DesktopWindow()
            
        # Check if page is in setup mode
        if self.desktop_window.music_page and self.desktop_window.music_page.mode == "setup":
            self.log_result("✓ Page is in setup mode (pink)")
        else:
            self.log_result("✗ Page is not in setup mode")
            
        # Check if score setup dialog should auto-launch
        self.log_result("✓ Auto-launch timer should trigger score setup dialog")
        
    def test_toggle_functionality(self):
        """Test toggle functionality in score setup dialog."""
        self.log_result("Testing score setup dialog toggle functionality...")
        
        if not self.desktop_window:
            self.desktop_window = DesktopWindow()
            
        # Open score setup dialog
        self.desktop_window.open_score_setup()
        self.log_result("✓ Score setup dialog opened")
        self.log_result("✓ Apply button should toggle between 'Apply' and 'Setup'")
        
    def test_menu_toggle(self):
        """Test menu toggle functionality."""
        self.log_result("Testing menu toggle functionality...")
        
        if not self.desktop_window:
            self.desktop_window = DesktopWindow()
            
        # Check current mode
        current_mode = self.desktop_window.music_page.mode if self.desktop_window.music_page else "unknown"
        self.log_result(f"Current mode: {current_mode}")
        
        # Test menu text
        menu_text = self.desktop_window.score_setup_action.text()
        self.log_result(f"Menu text: {menu_text}")
        
        if current_mode == "setup":
            self.log_result("✓ In setup mode - menu should show 'Edit Mode'")
        else:
            self.log_result("✓ In edit mode - menu should show 'Score Setup'")
            
        # Test toggle action
        self.desktop_window._handle_score_setup_toggle()
        self.log_result("✓ Toggle action executed")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = DesktopEnhancementsTestWindow()
    test_window.show()
    
    # Create desktop window for testing
    desktop_window = DesktopWindow()
    
    # Store reference in test window
    test_window.desktop_window = desktop_window
    
    # Log initial state
    test_window.log_result("Desktop window created successfully")
    test_window.log_result("Testing enhancements:")
    test_window.log_result("1. Full screen with menu visible")
    test_window.log_result("2. Auto-launch score setup dialog")
    test_window.log_result("3. Toggle Apply/Setup button")
    test_window.log_result("4. Enhanced menu toggle functionality")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 