#!/usr/bin/env python3
"""
Test script to verify score setup dialog toggle functionality.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.desktop_window import DesktopWindow

class ScoreSetupToggleTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Score Setup Toggle Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add test controls
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Add test buttons
        test_btn = QPushButton("Test Score Setup Dialog")
        test_btn.clicked.connect(self.test_score_setup_dialog)
        layout.addWidget(test_btn)
        
        # Create desktop window
        self.desktop_window = DesktopWindow()
        self.desktop_window.setGeometry(200, 200, 1200, 800)
        self.desktop_window.show()
        
        # Log initial state
        self.log("Desktop window created and shown")
        self.log(f"Initial music page mode: {getattr(self.desktop_window.music_page, 'mode', 'unknown')}")
        
        # Set up timer to check state
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_state)
        self.timer.start(1000)  # Check every second
        
    def log(self, message):
        """Add message to log."""
        self.log_text.append(f"[{QTimer().remainingTime()}] {message}")
        print(message)
        
    def check_state(self):
        """Check current state of desktop window."""
        if hasattr(self.desktop_window, 'music_page') and self.desktop_window.music_page:
            mode = getattr(self.desktop_window.music_page, 'mode', 'unknown')
            self.log(f"Current mode: {mode}")
            
            # Check if score setup dialog is open
            if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
                if self.desktop_window.score_setup_dialog.isVisible():
                    self.log("Score setup dialog is visible")
                    
                    # Check button text
                    apply_btn = self.desktop_window.score_setup_dialog.apply_btn
                    if apply_btn:
                        self.log(f"Apply button text: '{apply_btn.text()}'")
                else:
                    self.log("Score setup dialog is not visible")
            else:
                self.log("No score setup dialog reference")
                
    def test_score_setup_dialog(self):
        """Test the score setup dialog functionality."""
        self.log("=== TESTING SCORE SETUP DIALOG ===")
        
        # Open score setup dialog
        self.log("Opening score setup dialog...")
        self.desktop_window.open_score_setup()
        
        # Wait a moment then test toggle
        QTimer.singleShot(2000, self.test_toggle_functionality)
        
    def test_toggle_functionality(self):
        """Test the toggle functionality."""
        self.log("=== TESTING TOGGLE FUNCTIONALITY ===")
        
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            
            # Test initial state
            self.log(f"Initial button text: '{dialog.apply_btn.text()}'")
            
            # Test toggle to edit mode
            self.log("Clicking Apply button to switch to edit mode...")
            dialog.toggle_apply_setup()
            
            # Wait and check state
            QTimer.singleShot(1000, self.check_edit_mode)
        else:
            self.log("ERROR: No score setup dialog available")
            
    def check_edit_mode(self):
        """Check if we're in edit mode."""
        self.log("=== CHECKING EDIT MODE ===")
        
        if hasattr(self.desktop_window, 'music_page') and self.desktop_window.music_page:
            mode = getattr(self.desktop_window.music_page, 'mode', 'unknown')
            self.log(f"Music page mode: {mode}")
            
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            self.log(f"Apply button text: '{dialog.apply_btn.text()}'")
            
            # Test toggle back to setup mode
            self.log("Clicking Setup button to switch back to setup mode...")
            dialog.toggle_apply_setup()
            
            # Wait and check final state
            QTimer.singleShot(1000, self.check_final_state)
            
    def check_final_state(self):
        """Check final state after toggle."""
        self.log("=== CHECKING FINAL STATE ===")
        
        if hasattr(self.desktop_window, 'music_page') and self.desktop_window.music_page:
            mode = getattr(self.desktop_window.music_page, 'mode', 'unknown')
            self.log(f"Final music page mode: {mode}")
            
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            self.log(f"Final apply button text: '{dialog.apply_btn.text()}'")
            
        self.log("=== TEST COMPLETED ===")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = ScoreSetupToggleTestWindow()
    test_window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 