#!/usr/bin/env python3
"""
Test script to demonstrate immediate score updates in Full Score Options dialog
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QTimer
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog


class MockStaffView:
    """Mock staff view for testing"""
    def __init__(self):
        self.update_count = 0
        self.repaint_count = 0
        self.document = MockDocument()
    
    def update(self):
        self.update_count += 1
        print(f"MOCK_STAFF_VIEW: Update called (count: {self.update_count})")
    
    def repaint(self):
        self.repaint_count += 1
        print(f"MOCK_STAFF_VIEW: Repaint called (count: {self.repaint_count})")


class MockDocument:
    """Mock document for testing"""
    def __init__(self):
        self.settings = {}
        self.modified = False
    
    def set_modified(self, modified):
        self.modified = modified
        print(f"MOCK_DOCUMENT: Set modified to {modified}")


class TestMainWindow(QMainWindow):
    """Test main window with mock staff view"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Full Score Options Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create mock staff view
        self.staff_view = MockStaffView()
        
        # Create central widget with a button to open dialog
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Add button to open Full Score Options dialog
        self.open_dialog_button = QPushButton("Open Full Score Options Dialog")
        self.open_dialog_button.clicked.connect(self.open_full_score_options)
        layout.addWidget(self.open_dialog_button)
        
        # Add status label
        from PyQt6.QtWidgets import QLabel
        self.status_label = QLabel("Ready - Click button to open dialog and test immediate updates")
        layout.addWidget(self.status_label)
        
        print("TEST_WINDOW: Created with mock staff view")
    
    def open_full_score_options(self):
        """Open the Full Score Options dialog"""
        print("\\nTEST_WINDOW: Opening Full Score Options dialog...")
        
        # Create and show dialog
        dialog = FullScoreOptionsDialog(parent=self)
        
        # Update status
        self.status_label.setText("Dialog opened - Try changing parameters in the Notation Setup tab to see immediate updates")
        
        # Show dialog
        result = dialog.exec()
        
        # Update status based on result
        if result == dialog.DialogCode.Accepted:
            self.status_label.setText(f"Dialog accepted - Staff view updated {self.staff_view.update_count} times, repainted {self.staff_view.repaint_count} times")
        else:
            self.status_label.setText(f"Dialog cancelled - Staff view updated {self.staff_view.update_count} times, repainted {self.staff_view.repaint_count} times")
        
        print(f"TEST_WINDOW: Dialog closed with result: {result}")
        print(f"TEST_WINDOW: Final counts - Updates: {self.staff_view.update_count}, Repaints: {self.staff_view.repaint_count}")


def main():
    """Main test function"""
    print("=== Full Score Options Immediate Update Test ===")
    print("This test demonstrates that parameter changes in the Full Score Options")
    print("dialog immediately update the score through the staff view.")
    print("")
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = TestMainWindow()
    window.show()
    
    print("TEST: Window created and shown")
    print("TEST: Click 'Open Full Score Options Dialog' to test immediate updates")
    print("TEST: In the dialog, go to 'Notation Setup' tab and change any parameter")
    print("TEST: You should see immediate update messages in the console")
    print("")
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 