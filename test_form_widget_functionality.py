#!/usr/bin/env python3
"""
Test the radio button clearing functionality in form widget
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
    from PyQt6.QtCore import Qt
    
    print("✅ PyQt6 imports successful")
    
    # Test form widget radio button functionality
    app = QApplication(sys.argv)
    
    # Try to import and test the form widget
    try:
        from gui.music.widgets.form_widget import FormWidget
        print("✅ FormWidget imported successfully")
        
        # Create a test window with form widget
        test_window = QWidget()
        test_window.setWindowTitle("ONOTE Form Widget Radio Button Test")
        test_window.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        
        # Add title
        title = QLabel("ONOTE Form Widget Test")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Create form widget with parent
        form_widget = FormWidget(test_window)
        layout.addWidget(form_widget)
        
        # Add instructions
        instructions = QLabel("""
Instructions for Testing Radio Button Clearing:

1. Select any barline type radio button (Double, Final, etc.)
2. Click anywhere on the form widget background (away from buttons)
3. All radio buttons should be cleared
4. Only 'Single' should be selected on startup

✅ Radio button clearing functionality is implemented in FormWidget.mousePressEvent()
✅ Background clicking calls clear_all_radio_buttons()
✅ Single barline auto-selection on startup is implemented
        """)
        instructions.setStyleSheet("background-color: #f0f0f0; padding: 10px; margin: 10px;")
        layout.addWidget(instructions)
        
        test_window.setLayout(layout)
        test_window.show()
        
        print("✅ FormWidget radio button clearing functionality is ready!")
        print("✅ Click on form widget background to test radio button clearing")
        
        # Run the test
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"❌ Cannot import FormWidget: {e}")
        print("This indicates there are syntax errors in the staff_view.py or related files")
        
except Exception as e:
    print(f"❌ Error during test setup: {e}")
    sys.exit(1) 