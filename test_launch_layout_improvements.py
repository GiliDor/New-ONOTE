#!/usr/bin/env python3
"""
Test script to verify the launch layout improvements:
1. Window launches just short of full screen with menu accessible
2. Page positioned on left side of desktop
3. Score setup dialog positioned on right side
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction

from gui.desktop_window import DesktopWindow

class LaunchLayoutTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launch Layout Improvements Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("ONOTE Launch Layout Improvements Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Test description
        description = QLabel(
            "This test verifies:\n"
            "1. Window launches just short of full screen (menu accessible)\n"
            "2. Music page positioned on left side of desktop\n"
            "3. Score setup dialog positioned on right side\n"
            "4. Proper dialog closing when switching modes"
        )
        description.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(description)
        
        # Test buttons
        test_button = QPushButton("Launch ONOTE Desktop Window")
        test_button.clicked.connect(self.launch_desktop_window)
        layout.addWidget(test_button)
        
        # Results area
        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setMaximumHeight(200)
        layout.addWidget(self.results)
        
        # Status
        self.status = QLabel("Ready to test")
        layout.addWidget(self.status)
        
        # Store desktop window reference
        self.desktop_window = None
        
    def launch_desktop_window(self):
        """Launch the desktop window and run tests."""
        self.results.clear()
        self.status.setText("Launching desktop window...")
        
        # Create desktop window
        self.desktop_window = DesktopWindow()
        
        # Run tests after window is shown
        QTimer.singleShot(1000, self.run_tests)
        
    def run_tests(self):
        """Run the layout tests."""
        if not self.desktop_window:
            self.results.append("❌ Desktop window not created")
            return
            
        self.results.append("=== Launch Layout Improvements Test ===\n")
        
        # Test 1: Window size (just short of full screen)
        self.test_window_size()
        
        # Test 2: Page positioning (left side)
        self.test_page_positioning()
        
        # Test 3: Dialog positioning (right side)
        self.test_dialog_positioning()
        
        # Test 4: Dialog closing functionality
        self.test_dialog_closing()
        
        self.status.setText("Tests completed - check results above")
        
    def test_window_size(self):
        """Test that window launches just short of full screen."""
        self.results.append("1. Testing window size...")
        
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Get window geometry
        window_geometry = self.desktop_window.geometry()
        
        # Check window size
        expected_height = screen_geometry.height() - 50  # Should be 50px less than screen height
        actual_height = window_geometry.height()
        
        if abs(actual_height - expected_height) <= 10:  # Allow 10px tolerance
            self.results.append("✅ Window size correct - just short of full screen")
            self.results.append(f"   Screen height: {screen_geometry.height()}px")
            self.results.append(f"   Window height: {actual_height}px")
            self.results.append(f"   Menu space: {screen_geometry.height() - actual_height}px")
        else:
            self.results.append("❌ Window size incorrect")
            self.results.append(f"   Expected: ~{expected_height}px, Got: {actual_height}px")
            
    def test_page_positioning(self):
        """Test that page is positioned on the left side."""
        self.results.append("\n2. Testing page positioning...")
        
        if not self.desktop_window.music_page:
            self.results.append("❌ Music page not found")
            return
            
        page_pos = self.desktop_window.music_page.pos()
        window_width = self.desktop_window.geometry().width()
        
        # Page should be on left side (x < window_width/2)
        if page_pos.x() < window_width / 2:
            self.results.append("✅ Page positioned on left side")
            self.results.append(f"   Page X position: {page_pos.x()}px")
            self.results.append(f"   Window width: {window_width}px")
        else:
            self.results.append("❌ Page not positioned on left side")
            self.results.append(f"   Page X position: {page_pos.x()}px")
            
    def test_dialog_positioning(self):
        """Test that dialog is positioned on the right side."""
        self.results.append("\n3. Testing dialog positioning...")
        
        # Trigger dialog opening
        if hasattr(self.desktop_window, 'open_score_setup'):
            # Store original dialog reference
            original_dialog = self.desktop_window.score_setup_dialog
            
            # Open dialog
            self.desktop_window.open_score_setup()
            
            # Check if dialog was positioned correctly
            if self.desktop_window.score_setup_dialog:
                dialog_geometry = self.desktop_window.score_setup_dialog.geometry()
                window_geometry = self.desktop_window.geometry()
                
                # Dialog should be on right side
                dialog_center_x = dialog_geometry.x() + dialog_geometry.width() / 2
                window_center_x = window_geometry.width() / 2
                
                if dialog_center_x > window_center_x:
                    self.results.append("✅ Dialog positioned on right side")
                    self.results.append(f"   Dialog center X: {dialog_center_x}px")
                    self.results.append(f"   Window center X: {window_center_x}px")
                else:
                    self.results.append("❌ Dialog not positioned on right side")
                    self.results.append(f"   Dialog center X: {dialog_center_x}px")
                    self.results.append(f"   Window center X: {window_center_x}px")
            else:
                self.results.append("❌ Dialog not created")
        else:
            self.results.append("❌ open_score_setup method not found")
            
    def test_dialog_closing(self):
        """Test that dialog closes when switching modes."""
        self.results.append("\n4. Testing dialog closing functionality...")
        
        if hasattr(self.desktop_window, '_handle_score_setup_toggle'):
            # Check if dialog closing logic exists
            method_source = self.desktop_window._handle_score_setup_toggle.__code__.co_code
            if b'close' in method_source or b'isVisible' in method_source:
                self.results.append("✅ Dialog closing logic implemented")
            else:
                self.results.append("❌ Dialog closing logic not found")
        else:
            self.results.append("❌ _handle_score_setup_toggle method not found")
            
        self.results.append("\n=== Test Summary ===")
        self.results.append("All tests completed. Check individual results above.")
        self.results.append("Manual verification: Launch ONOTE and verify:")
        self.results.append("- Menu bar is accessible at top")
        self.results.append("- Page appears on left side")
        self.results.append("- Score setup dialog appears on right side")
        self.results.append("- Dialog closes when switching to edit mode")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = LaunchLayoutTest()
    test_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 