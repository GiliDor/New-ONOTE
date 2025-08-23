#!/usr/bin/env python3
"""
Test Dynamic Proportional Barline Positioning System

This test verifies that the barline positioning system responds dynamically
to window resizing and page dimension changes, ensuring proportional scaling
rather than fixed positioning.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from gui.music.main_window import MainWindow
from gui.music.staff_view import StaffView
from gui.music.score_document import ScoreDocument
from gui.music.barline_temporal_bridge import BarlineTemporalBridge

class DynamicProportionalTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Proportional Barline System Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create test controls
        controls_layout = QHBoxLayout()
        
        # Test buttons
        self.resize_btn = QPushButton("Resize Window (800x600)")
        self.resize_btn.clicked.connect(self.resize_small)
        controls_layout.addWidget(self.resize_btn)
        
        self.resize_large_btn = QPushButton("Resize Window (1400x1000)")
        self.resize_large_btn.clicked.connect(self.resize_large)
        controls_layout.addWidget(self.resize_large_btn)
        
        self.create_barlines_btn = QPushButton("Create Test Barlines")
        self.create_barlines_btn.clicked.connect(self.create_test_barlines)
        controls_layout.addWidget(self.create_barlines_btn)
        
        self.refresh_btn = QPushButton("Force Layout Refresh")
        self.refresh_btn.clicked.connect(self.force_refresh)
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)
        
        # Status label
        self.status_label = QLabel("Ready - Create a score and test dynamic resizing")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
        
        # Create main window for testing
        self.main_window = MainWindow()
        self.main_window.new_score()
        
        # Get the staff view and temporal bridge
        self.staff_view = self.main_window.staff_view
        self.temporal_bridge = self.staff_view.temporal_bridge
        
        # Add the staff view to our layout
        layout.addWidget(self.staff_view)
        
        # Test timer for delayed operations
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self.run_delayed_tests)
        
        self.update_status("Test window created. Click 'Create Test Barlines' to start testing.")
    
    def resize_small(self):
        """Resize window to small size"""
        self.resize(800, 600)
        self.update_status("Resized to 800x600 - check if barlines adjust proportionally")
    
    def resize_large(self):
        """Resize window to large size"""
        self.resize(1400, 1000)
        self.update_status("Resized to 1400x1000 - check if barlines adjust proportionally")
    
    def create_test_barlines(self):
        """Create test barlines to verify dynamic positioning"""
        try:
            # Ensure we're in edit mode
            if self.staff_view.is_setup_mode:
                self.staff_view.enter_edit_mode()
            
            # Create several test barlines
            test_positions = [400, 600, 800, 1000]
            
            for i, x_pos in enumerate(test_positions):
                # Create barline at position
                self.staff_view.create_barline_at_position(x_pos, 50)  # x, y
                self.update_status(f"Created barline {i+1} at x={x_pos}")
            
            self.update_status(f"Created {len(test_positions)} test barlines. Now try resizing the window.")
            
        except Exception as e:
            self.update_status(f"Error creating test barlines: {e}")
    
    def force_refresh(self):
        """Force layout refresh to test dynamic system"""
        try:
            if self.temporal_bridge:
                self.temporal_bridge._force_layout_refresh()
                self.update_status("Forced layout refresh - check if barlines repositioned correctly")
            else:
                self.update_status("No temporal bridge available")
        except Exception as e:
            self.update_status(f"Error in force refresh: {e}")
    
    def run_delayed_tests(self):
        """Run tests after a delay to ensure UI is ready"""
        self.test_timer.stop()
        
        # Test the dynamic system
        try:
            # Get current page width
            page_width = self.temporal_bridge._get_dynamic_page_width()
            right_margin = self.temporal_bridge._get_dynamic_right_margin()
            end_barline_x = self.temporal_bridge.get_current_end_barline_x()
            
            self.update_status(f"Dynamic system test: page_width={page_width}, right_margin={right_margin}, end_barline_x={end_barline_x}")
            
        except Exception as e:
            self.update_status(f"Error in delayed tests: {e}")
    
    def update_status(self, message):
        """Update status message"""
        self.status_label.setText(message)
        print(f"TEST: {message}")

def main():
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = DynamicProportionalTest()
    test_window.show()
    
    # Start delayed tests
    test_window.test_timer.start(1000)  # 1 second delay
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 