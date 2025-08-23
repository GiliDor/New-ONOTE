#!/usr/bin/env python3
"""
Test script to verify immediate rendering of staff additions in setup mode.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.desktop_window import DesktopWindow

class ImmediateRenderingFinalFixTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Immediate Rendering Final Fix Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create status label
        self.status_label = QLabel("Testing immediate rendering in setup mode...")
        layout.addWidget(self.status_label)
        
        # Create log text area
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Create test button
        self.test_button = QPushButton("Test Immediate Rendering")
        self.test_button.clicked.connect(self.test_immediate_rendering)
        layout.addWidget(self.test_button)
        
        # Create desktop window
        self.desktop_window = DesktopWindow()
        self.desktop_window.show()
        
        # Set up timer to check for immediate rendering
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_rendering)
        self.test_step = 0
        
    def test_immediate_rendering(self):
        """Test that staff additions immediately render in setup mode."""
        self.log_text.append("=== STARTING IMMEDIATE RENDERING TEST ===")
        self.log_text.append("1. Desktop window should be in setup mode (pink background)")
        self.log_text.append("2. Score setup dialog should be open")
        self.log_text.append("3. Adding staves should immediately show on pink background")
        self.log_text.append("4. No need to click Apply - changes should be live")
        
        # Start the test sequence
        self.test_step = 0
        self.timer.start(2000)  # Check every 2 seconds
        
    def check_rendering(self):
        """Check if immediate rendering is working."""
        self.test_step += 1
        
        if self.test_step == 1:
            self.log_text.append("\n=== STEP 1: Checking setup mode ===")
            if hasattr(self.desktop_window, 'music_page') and self.desktop_window.music_page:
                mode = getattr(self.desktop_window.music_page, 'mode', 'unknown')
                self.log_text.append(f"Current mode: {mode}")
                if mode == 'setup':
                    self.log_text.append("✅ Setup mode active (pink background)")
                else:
                    self.log_text.append("❌ Not in setup mode")
                    
        elif self.test_step == 2:
            self.log_text.append("\n=== STEP 2: Checking score setup dialog ===")
            # Look for score setup dialog
            dialogs = self.desktop_window.findChildren(type(self.desktop_window))
            score_setup_dialog = None
            for dialog in dialogs:
                if hasattr(dialog, 'windowTitle') and 'Score Setup' in dialog.windowTitle():
                    score_setup_dialog = dialog
                    break
            
            if score_setup_dialog:
                self.log_text.append("✅ Score setup dialog found")
                self.log_text.append("Now try adding staves - they should appear immediately on pink background")
            else:
                self.log_text.append("❌ Score setup dialog not found")
                
        elif self.test_step == 3:
            self.log_text.append("\n=== STEP 3: Testing immediate rendering ===")
            self.log_text.append("If you added staves and they appeared immediately on pink background:")
            self.log_text.append("✅ IMMEDIATE RENDERING IS WORKING!")
            self.log_text.append("If staves only appeared after clicking Apply:")
            self.log_text.append("❌ IMMEDIATE RENDERING IS NOT WORKING")
            
        elif self.test_step == 4:
            self.log_text.append("\n=== TEST COMPLETE ===")
            self.log_text.append("Expected behavior:")
            self.log_text.append("- Pink background in setup mode")
            self.log_text.append("- Staff additions show immediately")
            self.log_text.append("- No need to click Apply for live preview")
            self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImmediateRenderingFinalFixTestWindow()
    window.show()
    sys.exit(app.exec()) 