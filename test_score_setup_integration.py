#!/usr/bin/env python3
"""
Test script for score setup dialog integration with desktop window.
This script tests the complete workflow:
1. Desktop window starts in setup mode (pink page)
2. Score setup dialog opens and configures staves
3. Applying changes switches to edit mode (white page)
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


class ScoreSetupTestWindow(QMainWindow):
    """Test window to verify score setup integration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ONOTE Score Setup Integration Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Score Setup Integration Test")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Add description
        description = QLabel(
            "This test verifies the complete score setup workflow:\n"
            "1. Desktop window starts in setup mode (pink page)\n"
            "2. Score setup dialog opens and configures staves\n"
            "3. Applying changes switches to edit mode (white page)\n\n"
            "Click 'Launch Desktop Window' to test the integration."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add test buttons
        self.launch_btn = QPushButton("Launch Desktop Window")
        self.launch_btn.clicked.connect(self.launch_desktop_window)
        layout.addWidget(self.launch_btn)
        
        self.test_setup_btn = QPushButton("Test Score Setup Dialog")
        self.test_setup_btn.clicked.connect(self.test_score_setup_dialog)
        self.test_setup_btn.setEnabled(False)
        layout.addWidget(self.test_setup_btn)
        
        self.verify_mode_btn = QPushButton("Verify Mode Transition")
        self.verify_mode_btn.clicked.connect(self.verify_mode_transition)
        self.verify_mode_btn.setEnabled(False)
        layout.addWidget(self.verify_mode_btn)
        
        # Add log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)
        
        # Store desktop window reference
        self.desktop_window = None
        
        # Add status label
        self.status_label = QLabel("Ready to test")
        layout.addWidget(self.status_label)
        
    def log(self, message):
        """Add message to log area."""
        self.log_area.append(f"[{QTimer().remainingTime()}] {message}")
        
    def launch_desktop_window(self):
        """Launch the desktop window for testing."""
        try:
            self.log("Launching desktop window...")
            
            # Create desktop window
            self.desktop_window = DesktopWindow()
            
            # Connect signals
            self.desktop_window.page_mode_changed.connect(self.on_mode_changed)
            
            # Show window
            self.desktop_window.show()
            
            # Enable test buttons
            self.test_setup_btn.setEnabled(True)
            self.verify_mode_btn.setEnabled(True)
            
            self.log("✅ Desktop window launched successfully")
            self.log("📝 Window should start in setup mode (pink page)")
            self.status_label.setText("Desktop window launched - check for pink page")
            
        except Exception as e:
            self.log(f"❌ Error launching desktop window: {e}")
            self.status_label.setText("Error launching desktop window")
            
    def test_score_setup_dialog(self):
        """Test the score setup dialog integration."""
        if not self.desktop_window:
            self.log("❌ Desktop window not available")
            return
            
        try:
            self.log("Opening score setup dialog...")
            
            # Check initial mode
            if self.desktop_window.music_page:
                initial_mode = self.desktop_window.music_page.mode
                self.log(f"📝 Initial page mode: {initial_mode}")
                
                if initial_mode != "setup":
                    self.log("⚠️  Warning: Page not in setup mode initially")
                else:
                    self.log("✅ Page correctly in setup mode")
            
            # Open score setup dialog
            self.desktop_window.open_score_setup()
            
            self.log("✅ Score setup dialog opened")
            self.log("📝 Configure staves in the dialog, then click 'Apply'")
            self.status_label.setText("Score setup dialog opened - configure and apply")
            
        except Exception as e:
            self.log(f"❌ Error opening score setup dialog: {e}")
            self.status_label.setText("Error opening score setup dialog")
            
    def verify_mode_transition(self):
        """Verify the mode transition worked correctly."""
        if not self.desktop_window:
            self.log("❌ Desktop window not available")
            return
            
        try:
            self.log("Verifying mode transition...")
            
            if self.desktop_window.music_page:
                current_mode = self.desktop_window.music_page.mode
                self.log(f"📝 Current page mode: {current_mode}")
                
                if current_mode == "edit":
                    self.log("✅ Page correctly transitioned to edit mode")
                    self.log("📝 Page should now be white (not pink)")
                    self.status_label.setText("Mode transition successful - page should be white")
                else:
                    self.log("⚠️  Page still in setup mode - check if setup was applied")
                    self.status_label.setText("Page still in setup mode")
                    
                # Check staff view mode
                if self.desktop_window.music_page.staff_view:
                    staff_view_mode = getattr(self.desktop_window.music_page.staff_view, 'is_setup_mode', 'Unknown')
                    self.log(f"📝 Staff view setup mode: {staff_view_mode}")
                    
                    if staff_view_mode == False:
                        self.log("✅ Staff view correctly in edit mode")
                    else:
                        self.log("⚠️  Staff view still in setup mode")
            else:
                self.log("❌ Music page not available")
                
        except Exception as e:
            self.log(f"❌ Error verifying mode transition: {e}")
            self.status_label.setText("Error verifying mode transition")
            
    def on_mode_changed(self, mode):
        """Handle mode change signal."""
        self.log(f"🔄 Mode changed to: {mode}")
        if mode == "edit":
            self.log("✅ Successfully transitioned to edit mode")
            self.status_label.setText("Mode transition detected - edit mode active")


def main():
    """Main test function."""
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = ScoreSetupTestWindow()
    test_window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 