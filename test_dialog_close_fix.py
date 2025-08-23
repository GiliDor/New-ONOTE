#!/usr/bin/env python3
"""
Test script to verify that the Score menu toggle properly closes the score setup dialog
when switching from setup to edit mode.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction

from gui.desktop_window import DesktopWindow

class DialogCloseTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Close Fix Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Test description
        description = QLabel("""
        <h2>Dialog Close Fix Test</h2>
        <p>This test verifies that the Score menu toggle properly closes the score setup dialog 
        when switching from setup to edit mode.</p>
        
        <h3>Test Steps:</h3>
        <ol>
            <li>Launch ONOTE Desktop (should auto-open score setup dialog)</li>
            <li>Verify dialog is open and page is in setup mode (pink)</li>
            <li>Click "Score Setup" menu item (should show "Edit Mode")</li>
            <li>Verify dialog closes and page switches to edit mode (white)</li>
            <li>Click "Edit Mode" menu item (should show "Score Setup")</li>
            <li>Verify dialog opens again and page switches to setup mode</li>
        </ol>
        
        <h3>Expected Behavior:</h3>
        <ul>
            <li>✅ Dialog closes when switching from setup to edit mode</li>
            <li>✅ Page color changes from pink to white</li>
            <li>✅ Menu text updates correctly</li>
            <li>✅ Dialog reopens when switching back to setup mode</li>
        </ul>
        """)
        layout.addWidget(description)
        
        # Launch button
        launch_btn = QPushButton("Launch ONOTE Desktop")
        launch_btn.clicked.connect(self.launch_desktop)
        layout.addWidget(launch_btn)
        
        # Status display
        self.status_display = QTextEdit()
        self.status_display.setMaximumHeight(200)
        layout.addWidget(self.status_display)
        
        # Store desktop window reference
        self.desktop_window = None
        
    def launch_desktop(self):
        """Launch the ONOTE Desktop window."""
        try:
            self.desktop_window = DesktopWindow()
            self.desktop_window.show()
            
            # Connect to signals to monitor state changes
            self.desktop_window.page_mode_changed.connect(self.on_mode_changed)
            
            # Monitor dialog state
            QTimer.singleShot(1000, self.check_initial_state)
            
            self.log_status("✅ ONOTE Desktop launched successfully")
            self.log_status("📋 Auto-launching score setup dialog in 500ms...")
            
        except Exception as e:
            self.log_status(f"❌ Error launching desktop: {e}")
    
    def check_initial_state(self):
        """Check the initial state after launch."""
        if not self.desktop_window:
            return
            
        try:
            # Check if we're in setup mode
            if self.desktop_window.music_page and self.desktop_window.music_page.mode == "setup":
                self.log_status("✅ Initial state: Setup mode (pink page)")
                
                # Check if dialog is open
                if self.desktop_window.score_setup_dialog and self.desktop_window.score_setup_dialog.isVisible():
                    self.log_status("✅ Score setup dialog is open")
                else:
                    self.log_status("⚠️ Score setup dialog not detected (may have closed)")
                    
            else:
                self.log_status("❌ Initial state: Not in setup mode")
                
        except Exception as e:
            self.log_status(f"❌ Error checking initial state: {e}")
    
    def on_mode_changed(self, mode):
        """Handle page mode changes."""
        self.log_status(f"🔄 Page mode changed to: {mode}")
        
        if mode == "edit":
            # Check if dialog was closed
            if not self.desktop_window.score_setup_dialog or not self.desktop_window.score_setup_dialog.isVisible():
                self.log_status("✅ Dialog properly closed when switching to edit mode")
            else:
                self.log_status("❌ Dialog still open when switching to edit mode")
                
        elif mode == "setup":
            # Check if dialog is open
            if self.desktop_window.score_setup_dialog and self.desktop_window.score_setup_dialog.isVisible():
                self.log_status("✅ Dialog opened when switching to setup mode")
            else:
                self.log_status("⚠️ Dialog not detected when switching to setup mode")
    
    def log_status(self, message):
        """Log a status message."""
        self.status_display.append(f"[{QTimer.singleShot(0, lambda: None)}] {message}")
        print(message)

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = DialogCloseTest()
    test_window.show()
    
    print("=" * 60)
    print("DIALOG CLOSE FIX TEST")
    print("=" * 60)
    print("This test verifies that the Score menu toggle properly closes")
    print("the score setup dialog when switching from setup to edit mode.")
    print()
    print("Manual Test Steps:")
    print("1. Click 'Launch ONOTE Desktop'")
    print("2. Wait for score setup dialog to auto-open")
    print("3. Click 'Score Setup' menu item (should show 'Edit Mode')")
    print("4. Verify dialog closes and page turns white")
    print("5. Click 'Edit Mode' menu item (should show 'Score Setup')")
    print("6. Verify dialog opens and page turns pink")
    print()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 