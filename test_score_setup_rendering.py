#!/usr/bin/env python3
"""
Test script to verify that score setup dialog settings render on the page immediately.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer, pyqtSignal

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.desktop_window import DesktopWindow

class ScoreSetupTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Score Setup Rendering Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add test controls
        self.status_label = QLabel("Status: Ready to test")
        layout.addWidget(self.status_label)
        
        # Add test buttons
        launch_btn = QPushButton("Launch ONOTE")
        launch_btn.clicked.connect(self.launch_onote)
        layout.addWidget(launch_btn)
        
        test_setup_btn = QPushButton("Test Score Setup Dialog")
        test_setup_btn.clicked.connect(self.test_score_setup)
        layout.addWidget(test_setup_btn)
        
        # Add log area
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)
        
        # Store ONOTE window reference
        self.onote_window = None
        
    def log(self, message):
        """Add message to log area"""
        self.log_area.append(message)
        print(message)
        
    def launch_onote(self):
        """Launch ONOTE application"""
        try:
            self.log("🚀 Launching ONOTE...")
            self.onote_window = DesktopWindow()
            self.onote_window.show()
            self.log("✅ ONOTE launched successfully")
            self.status_label.setText("Status: ONOTE launched")
        except Exception as e:
            self.log(f"❌ Failed to launch ONOTE: {e}")
            self.status_label.setText("Status: Launch failed")
            
    def test_score_setup(self):
        """Test score setup dialog rendering"""
        if not self.onote_window:
            self.log("❌ ONOTE not launched - launch first")
            return
            
        try:
            self.log("🎵 Testing score setup dialog...")
            
            # Check if we're in setup mode
            if hasattr(self.onote_window, 'music_page') and self.onote_window.music_page:
                mode = getattr(self.onote_window.music_page, 'mode', 'unknown')
                self.log(f"📄 Current page mode: {mode}")
                
                if mode != 'setup':
                    self.log("🔄 Switching to setup mode...")
                    self.onote_window._enter_setup_mode()
                    
            # Open score setup dialog
            self.log("📋 Opening score setup dialog...")
            self.onote_window.open_score_setup()
            
            # Check if dialog was created
            if hasattr(self.onote_window, 'score_setup_dialog') and self.onote_window.score_setup_dialog:
                self.log("✅ Score setup dialog opened")
                
                # Test adding a staff
                dialog = self.onote_window.score_setup_dialog
                if hasattr(dialog, 'setup_widget'):
                    setup_widget = dialog.setup_widget
                    self.log("🎼 Testing staff addition...")
                    
                    # Add a treble clef staff
                    setup_widget.add_generic_staff("treble")
                    self.log("✅ Added treble clef staff")
                    
                    # Check if staff was added to the list
                    staff_count = setup_widget.staff_list.topLevelItemCount()
                    self.log(f"📊 Staff count in dialog: {staff_count}")
                    
                    # Check if the page was updated
                    if hasattr(self.onote_window, 'music_page') and self.onote_window.music_page:
                        if hasattr(self.onote_window.music_page, 'staff_view'):
                            staff_view = self.onote_window.music_page.staff_view
                            if hasattr(staff_view, 'document'):
                                doc = staff_view.document
                                if hasattr(doc, 'staves'):
                                    page_staff_count = len(doc.staves)
                                    self.log(f"📄 Staff count on page: {page_staff_count}")
                                    
                                    if page_staff_count > 0:
                                        self.log("✅ SUCCESS: Staff is rendering on the page!")
                                        self.status_label.setText("Status: SUCCESS - Staff rendering on page")
                                    else:
                                        self.log("❌ FAILED: Staff not rendering on page")
                                        self.status_label.setText("Status: FAILED - Staff not rendering")
                                else:
                                    self.log("⚠️ Document has no staves attribute")
                            else:
                                self.log("⚠️ Music page has no staff view")
                        else:
                            self.log("⚠️ Music page not found")
                    else:
                        self.log("⚠️ Music page not found")
                else:
                    self.log("❌ Dialog has no setup widget")
            else:
                self.log("❌ Score setup dialog not created")
                
        except Exception as e:
            self.log(f"❌ Test failed with error: {e}")
            self.status_label.setText("Status: Test failed")

def main():
    app = QApplication(sys.argv)
    window = ScoreSetupTestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 