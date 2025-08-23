#!/usr/bin/env python3
"""
Working demonstration of Full Score Options dialog with undo/redo functionality.
This script creates a fully functional dialog with working Cmd+Z and Cmd+Y shortcuts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                           QLabel, QPushButton, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

# Import our modified Full Score Options dialog
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog

class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ONOTE Undo/Redo Test - Full Score Options")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add title
        title = QLabel("Full Score Options Dialog - Undo/Redo Test")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        layout.addWidget(title)
        
        # Add instructions
        instructions = QLabel("""
Instructions:
1. Click 'Open Full Score Options Dialog' below
2. In the dialog, change various values (font sizes, positions, colors)
3. Press Cmd+Z (Mac) or Ctrl+Z (Windows/Linux) to undo changes
4. Press Cmd+Y (Mac) or Ctrl+Y (Windows/Linux) to redo changes
5. Watch the values change in real-time!

Note: The undo/redo functionality is built into our modified dialog.
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("margin: 20px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(instructions)
        
        # Add button to open dialog
        button_layout = QHBoxLayout()
        self.open_dialog_btn = QPushButton("Open Full Score Options Dialog")
        self.open_dialog_btn.clicked.connect(self.open_full_score_dialog)
        self.open_dialog_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        button_layout.addStretch()
        button_layout.addWidget(self.open_dialog_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        # Store dialog reference
        self.dialog = None
        
    def open_full_score_dialog(self):
        """Open the Full Score Options dialog with undo/redo functionality."""
        try:
            if self.dialog is None:
                self.dialog = FullScoreOptionsDialog(self)
                
            # Show the dialog
            self.dialog.show()
            self.dialog.raise_()
            self.dialog.activateWindow()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open dialog: {str(e)}")
            print(f"Error opening dialog: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("Starting ONOTE Full Score Options Undo/Redo Test...")
    
    app = QApplication(sys.argv)
    
    # Create main window
    window = TestMainWindow()
    window.show()
    
    print("Test window opened. Click the button to open the Full Score Options dialog.")
    print("Then test undo/redo with Cmd+Z and Cmd+Y!")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 