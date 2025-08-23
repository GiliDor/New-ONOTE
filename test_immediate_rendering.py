#!/usr/bin/env python3
"""
Test script to verify immediate rendering of staff changes in setup mode.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.desktop_window import DesktopWindow

class ImmediateRenderingTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Immediate Rendering Test")
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
        test_btn = QPushButton("Test Immediate Rendering")
        test_btn.clicked.connect(self.test_immediate_rendering)
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
                    
                    # Check staff count in dialog
                    dialog = self.desktop_window.score_setup_dialog
                    if hasattr(dialog, 'setup_widget') and hasattr(dialog.setup_widget, 'staff_list'):
                        staff_count = dialog.setup_widget.staff_list.topLevelItemCount()
                        self.log(f"Staff count in dialog: {staff_count}")
                        
                        # Check staff count on page
                        if hasattr(self.desktop_window.music_page, 'staff_view'):
                            staff_view = self.desktop_window.music_page.staff_view
                            if hasattr(staff_view, 'document') and hasattr(staff_view.document, 'staves'):
                                page_staff_count = len(staff_view.document.staves)
                                self.log(f"Staff count on page: {page_staff_count}")
                else:
                    self.log("Score setup dialog is not visible")
            else:
                self.log("No score setup dialog reference")
                
    def test_immediate_rendering(self):
        """Test immediate rendering of staff changes."""
        self.log("=== TESTING IMMEDIATE RENDERING ===")
        
        # Open score setup dialog
        self.log("Opening score setup dialog...")
        self.desktop_window.open_score_setup()
        
        # Wait a moment then test adding a staff
        QTimer.singleShot(2000, self.test_add_staff)
        
    def test_add_staff(self):
        """Test adding a staff and see if it renders immediately."""
        self.log("=== TESTING ADD STAFF ===")
        
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            
            # Check initial staff count
            initial_count = dialog.setup_widget.staff_list.topLevelItemCount()
            self.log(f"Initial staff count: {initial_count}")
            
            # Add a treble clef staff
            self.log("Adding treble clef staff...")
            dialog.setup_widget.add_generic_staff("treble")
            
            # Wait and check if staff was added
            QTimer.singleShot(1000, self.check_staff_added)
        else:
            self.log("ERROR: No score setup dialog available")
            
    def check_staff_added(self):
        """Check if staff was added and rendered."""
        self.log("=== CHECKING STAFF ADDED ===")
        
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            
            # Check staff count in dialog
            dialog_count = dialog.setup_widget.staff_list.topLevelItemCount()
            self.log(f"Staff count in dialog: {dialog_count}")
            
            # Check staff count on page
            if hasattr(self.desktop_window.music_page, 'staff_view'):
                staff_view = self.desktop_window.music_page.staff_view
                if hasattr(staff_view, 'document') and hasattr(staff_view.document, 'staves'):
                    page_staff_count = len(staff_view.document.staves)
                    self.log(f"Staff count on page: {page_staff_count}")
                    
                    if page_staff_count > 0:
                        self.log("SUCCESS: Staff was immediately rendered on page!")
                    else:
                        self.log("FAILURE: Staff was not rendered on page")
                        
            # Test adding another staff
            QTimer.singleShot(1000, self.test_add_second_staff)
            
    def test_add_second_staff(self):
        """Test adding a second staff."""
        self.log("=== TESTING ADD SECOND STAFF ===")
        
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            
            # Add a bass clef staff
            self.log("Adding bass clef staff...")
            dialog.setup_widget.add_generic_staff("bass")
            
            # Wait and check final state
            QTimer.singleShot(1000, self.check_final_state)
            
    def check_final_state(self):
        """Check final state after adding multiple staves."""
        self.log("=== CHECKING FINAL STATE ===")
        
        if hasattr(self.desktop_window, 'score_setup_dialog') and self.desktop_window.score_setup_dialog:
            dialog = self.desktop_window.score_setup_dialog
            
            # Check staff count in dialog
            dialog_count = dialog.setup_widget.staff_list.topLevelItemCount()
            self.log(f"Final staff count in dialog: {dialog_count}")
            
            # Check staff count on page
            if hasattr(self.desktop_window.music_page, 'staff_view'):
                staff_view = self.desktop_window.music_page.staff_view
                if hasattr(staff_view, 'document') and hasattr(staff_view.document, 'staves'):
                    page_staff_count = len(staff_view.document.staves)
                    self.log(f"Final staff count on page: {page_staff_count}")
                    
                    if page_staff_count == dialog_count:
                        self.log("SUCCESS: All staves are immediately rendered on page!")
                    else:
                        self.log(f"FAILURE: Only {page_staff_count}/{dialog_count} staves rendered on page")
                        
        self.log("=== TEST COMPLETED ===")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = ImmediateRenderingTestWindow()
    test_window.show()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 