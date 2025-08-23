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

class ImmediateRenderingFinalTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Immediate Rendering Final Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create test controls
        self.status_label = QLabel("Ready to test immediate rendering in setup mode")
        layout.addWidget(self.status_label)
        
        # Create test buttons
        test_btn = QPushButton("Test Immediate Rendering")
        test_btn.clicked.connect(self.test_immediate_rendering)
        layout.addWidget(test_btn)
        
        # Create log display
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        layout.addWidget(self.log_display)
        
        # Create desktop window
        self.desktop_window = DesktopWindow()
        self.desktop_window.show()
        
        # Position the test window
        self.move(100, 100)
        self.desktop_window.move(200, 100)
        
        self.log("Test window created")
        self.log("Desktop window created and shown")
        
    def log(self, message):
        """Add message to log display"""
        self.log_display.append(f"[TEST] {message}")
        print(f"[TEST] {message}")
        
    def test_immediate_rendering(self):
        """Test immediate rendering of staff additions in setup mode"""
        self.log("=== STARTING IMMEDIATE RENDERING TEST ===")
        
        # Check if we're in setup mode
        if hasattr(self.desktop_window, 'music_page') and hasattr(self.desktop_window.music_page, 'mode'):
            mode = self.desktop_window.music_page.mode
            self.log(f"Current mode: {mode}")
            
            if mode != 'setup':
                self.log("ERROR: Not in setup mode! Should be in setup mode (pink background)")
                return
        else:
            self.log("ERROR: Cannot determine current mode")
            return
            
        # Check if score setup dialog is open
        score_setup_dialog = None
        for child in self.desktop_window.findChildren(QWidget):
            if hasattr(child, 'windowTitle') and 'Score Setup' in child.windowTitle():
                score_setup_dialog = child
                break
                
        if not score_setup_dialog:
            self.log("ERROR: Score setup dialog not found!")
            return
            
        self.log("Found score setup dialog")
        
        # Find the score setup widget
        score_setup_widget = None
        for child in score_setup_dialog.findChildren(QWidget):
            if hasattr(child, 'staff_list'):
                score_setup_widget = child
                break
                
        if not score_setup_widget:
            self.log("ERROR: Score setup widget not found!")
            return
            
        self.log("Found score setup widget")
        
        # Check current staff count
        current_staff_count = score_setup_widget.staff_list.topLevelItemCount()
        self.log(f"Current staff count: {current_staff_count}")
        
        # Find an instrument to add
        instrument_tree = score_setup_widget.instrument_tree
        if instrument_tree.topLevelItemCount() == 0:
            self.log("ERROR: No instruments available in tree!")
            return
            
        # Get first instrument
        first_instrument = instrument_tree.topLevelItem(0)
        self.log(f"Found instrument: {first_instrument.text(0)}")
        
        # Add the instrument
        self.log("Adding instrument to staff list...")
        score_setup_widget.add_staff_from_item(first_instrument)
        
        # Check if staff was added
        new_staff_count = score_setup_widget.staff_list.topLevelItemCount()
        self.log(f"New staff count: {new_staff_count}")
        
        if new_staff_count > current_staff_count:
            self.log("SUCCESS: Staff was added to the list!")
            
            # Check if it rendered on the page
            self.log("Checking if staff rendered on the page...")
            
            # Wait a moment for rendering
            QTimer.singleShot(500, self.check_rendering)
        else:
            self.log("ERROR: Staff was not added to the list!")
            
    def check_rendering(self):
        """Check if the staff rendered on the page"""
        self.log("=== CHECKING RENDERING ===")
        
        # Check if the music page has the new staff
        if hasattr(self.desktop_window, 'music_page') and hasattr(self.desktop_window.music_page, 'document'):
            document = self.desktop_window.music_page.document
            
            if hasattr(document, 'staves'):
                staff_count = len(document.staves)
                self.log(f"Document has {staff_count} staves")
                
                # List the staves
                for i, staff in enumerate(document.staves):
                    staff_name = getattr(staff, 'name', f'Staff {i}')
                    self.log(f"  Staff {i}: {staff_name}")
                    
                if staff_count > 1:
                    self.log("SUCCESS: Multiple staves found in document - immediate rendering worked!")
                else:
                    self.log("WARNING: Only one staff found - immediate rendering may not have worked")
            else:
                self.log("ERROR: Document has no staves attribute")
        else:
            self.log("ERROR: Cannot access document")
            
        self.log("=== RENDERING CHECK COMPLETE ===")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = ImmediateRenderingFinalTestWindow()
    test_window.show()
    
    print("Test window created. Click 'Test Immediate Rendering' to test.")
    print("Make sure the score setup dialog is open and you're in setup mode (pink background).")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 