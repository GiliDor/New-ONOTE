#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QColorDialog
from PyQt6.QtGui import QColor

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Color Picker Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create test buttons
        self.clef_color_btn = QPushButton("Test Clef Color")
        self.clef_color_btn.setStyleSheet("background-color: #000000; color: white;")
        self.clef_color_btn.clicked.connect(lambda: self.test_color_picker('clef'))
        layout.addWidget(self.clef_color_btn)
        
        self.time_sig_color_btn = QPushButton("Test Time Signature Color")
        self.time_sig_color_btn.setStyleSheet("background-color: #000000; color: white;")
        self.time_sig_color_btn.clicked.connect(lambda: self.test_color_picker('time_sig'))
        layout.addWidget(self.time_sig_color_btn)
        
        self.key_sig_color_btn = QPushButton("Test Key Signature Color")
        self.key_sig_color_btn.setStyleSheet("background-color: #000000; color: white;")
        self.key_sig_color_btn.clicked.connect(lambda: self.test_color_picker('key_sig'))
        layout.addWidget(self.key_sig_color_btn)
        
        # Store color values
        self.clef_color_value = '#000000'
        self.time_sig_color_value = '#000000'
        self.key_sig_color_value = '#000000'
        
    def test_color_picker(self, category):
        """Test color picker functionality"""
        print(f"TEST: Opening color picker for {category}")
        
        # Get current color
        current_color = QColor(getattr(self, f'{category}_color_value', '#000000'))
        print(f"TEST: Current color for {category}: {current_color.name()}")
        
        # Open color picker
        color = QColorDialog.getColor(current_color, self, f"Choose {category.replace('_', ' ').title()} Color")
        print(f"TEST: Color dialog returned: {color.name() if color.isValid() else 'Invalid'}")
        
        if color.isValid():
            # Update button appearance
            hex_color = color.name()
            print(f"TEST: Selected color for {category}: {hex_color}")
            
            # Choose contrasting text color
            text_color = "#FFFFFF" if self.is_dark_color(color) else "#000000"
            
            # Update the appropriate button
            if category == 'clef':
                self.clef_color_btn.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")
                self.clef_color_value = hex_color
            elif category == 'time_sig':
                self.time_sig_color_btn.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")
                self.time_sig_color_value = hex_color
            elif category == 'key_sig':
                self.key_sig_color_btn.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")
                self.key_sig_color_value = hex_color
            
            print(f"TEST: Updated {category}_color_value = {hex_color}")
        else:
            print(f"TEST: Color selection cancelled for {category}")
    
    def is_dark_color(self, color):
        """Determine if a color is dark (for choosing contrasting text color)"""
        # Use luminance formula to determine if color is dark
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 