#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
from PyQt6.QtCore import QSettings
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.music.staff_types import ScoreDocument, ScoreLayout

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Full Score Options Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create test buttons
        self.test_clef_btn = QPushButton("Test Clef Settings")
        self.test_clef_btn.clicked.connect(self.test_clef_settings)
        layout.addWidget(self.test_clef_btn)
        
        self.test_time_sig_btn = QPushButton("Test Time Signature Settings")
        self.test_time_sig_btn.clicked.connect(self.test_time_sig_settings)
        layout.addWidget(self.test_time_sig_btn)
        
        self.test_key_sig_btn = QPushButton("Test Key Signature Settings")
        self.test_key_sig_btn.clicked.connect(self.test_key_sig_settings)
        layout.addWidget(self.test_key_sig_btn)
        
        self.test_staff_name_btn = QPushButton("Test Staff Name Settings")
        self.test_staff_name_btn.clicked.connect(self.test_staff_name_settings)
        layout.addWidget(self.test_staff_name_btn)
        
        self.test_section_name_btn = QPushButton("Test Section Name Settings")
        self.test_section_name_btn.clicked.connect(self.test_section_name_settings)
        layout.addWidget(self.test_section_name_btn)
        
        self.test_save_load_btn = QPushButton("Test Save/Load Settings")
        self.test_save_load_btn.clicked.connect(self.test_save_load_settings)
        layout.addWidget(self.test_save_load_btn)
        
        self.test_defaults_btn = QPushButton("Test Set as Defaults")
        self.test_defaults_btn.clicked.connect(self.test_set_as_defaults)
        layout.addWidget(self.test_defaults_btn)
        
        # Create a mock document for testing
        self.document = ScoreDocument()
        self.document.layout = ScoreLayout()
        self.document.settings = {}
        
        # Set some initial settings
        self.document.settings.update({
            'notation/clef_font_size': 32,
            'notation/clef_vertical': 0,
            'notation/clef_horizontal': 20,
            'notation/clef_font_color': '#000000',
            'notation/time_sig_font_size': 24,
            'notation/time_sig_vertical': 0,
            'notation/time_sig_horizontal': 40,
            'notation/time_sig_spacing': 18,
            'notation/time_sig_font_color': '#000000',
            'notation/key_sig_font_size': 14,
            'notation/key_sig_vertical': 0,
            'notation/key_sig_horizontal': 75,
            'notation/key_sig_accidental_spacing': 12,
            'notation/key_sig_font_color': '#000000',
            'notation/staff_name_font_size': 10,
            'notation/staff_name_vertical': -8,
            'notation/staff_name_horizontal': -50,
            'notation/staff_name_font_color': '#000000',
            'notation/section_name_font_size': 12,
            'notation/section_name_vertical': -25,
            'notation/section_name_horizontal': -60,
            'notation/section_name_font_color': '#000000',
        })
        
        print("TEST: Created test document with initial settings")
        print(f"TEST: Document settings: {self.document.settings}")
    
    def test_clef_settings(self):
        """Test clef settings - font size, positioning, and color"""
        print("\n=== TESTING CLEF SETTINGS ===")
        
        # Create dialog
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Test font size change
        print("TEST: Testing clef font size change")
        original_size = dialog.clef_font_size.value()
        dialog.clef_font_size.setValue(40)
        new_size = dialog.clef_font_size.value()
        print(f"TEST: Clef font size changed from {original_size} to {new_size}")
        
        # Test vertical position change
        print("TEST: Testing clef vertical position change")
        original_vertical = dialog.clef_vertical.value()
        dialog.clef_vertical.setValue(5)
        new_vertical = dialog.clef_vertical.value()
        print(f"TEST: Clef vertical position changed from {original_vertical} to {new_vertical}")
        
        # Test horizontal position change
        print("TEST: Testing clef horizontal position change")
        original_horizontal = dialog.clef_horizontal.value()
        dialog.clef_horizontal.setValue(30)
        new_horizontal = dialog.clef_horizontal.value()
        print(f"TEST: Clef horizontal position changed from {original_horizontal} to {new_horizontal}")
        
        # Test color change
        print("TEST: Testing clef color change")
        original_color = getattr(dialog, 'clef_color_value', '#000000')
        print(f"TEST: Original clef color: {original_color}")
        
        # Simulate color selection
        setattr(dialog, 'clef_color_value', '#ff0000')
        dialog.clef_font_color.setStyleSheet("background-color: #ff0000; color: white;")
        new_color = getattr(dialog, 'clef_color_value', '#000000')
        print(f"TEST: New clef color: {new_color}")
        
        # Save settings
        dialog.save_settings()
        print(f"TEST: Saved settings to document: {self.document.settings}")
        
        # Verify settings were saved
        saved_color = self.document.settings.get('notation/clef_font_color', '#000000')
        print(f"TEST: Saved clef color in document: {saved_color}")
        
        dialog.close()
    
    def test_time_sig_settings(self):
        """Test time signature settings"""
        print("\n=== TESTING TIME SIGNATURE SETTINGS ===")
        
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Test font size change
        print("TEST: Testing time signature font size change")
        original_size = dialog.time_sig_font_size.value()
        dialog.time_sig_font_size.setValue(30)
        new_size = dialog.time_sig_font_size.value()
        print(f"TEST: Time signature font size changed from {original_size} to {new_size}")
        
        # Test color change
        print("TEST: Testing time signature color change")
        setattr(dialog, 'time_sig_color_value', '#00ff00')
        dialog.time_sig_font_color.setStyleSheet("background-color: #00ff00; color: black;")
        new_color = getattr(dialog, 'time_sig_color_value', '#000000')
        print(f"TEST: New time signature color: {new_color}")
            
        # Save settings
        dialog.save_settings()
        saved_color = self.document.settings.get('notation/time_sig_font_color', '#000000')
        print(f"TEST: Saved time signature color in document: {saved_color}")
        
        dialog.close()
    
    def test_key_sig_settings(self):
        """Test key signature settings"""
        print("\n=== TESTING KEY SIGNATURE SETTINGS ===")
        
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Test color change
        print("TEST: Testing key signature color change")
        setattr(dialog, 'key_sig_color_value', '#0000ff')
        dialog.key_sig_font_color.setStyleSheet("background-color: #0000ff; color: white;")
        new_color = getattr(dialog, 'key_sig_color_value', '#000000')
        print(f"TEST: New key signature color: {new_color}")
        
        # Save settings
        dialog.save_settings()
        saved_color = self.document.settings.get('notation/key_sig_font_color', '#000000')
        print(f"TEST: Saved key signature color in document: {saved_color}")
        
        dialog.close()
    
    def test_staff_name_settings(self):
        """Test staff name settings"""
        print("\n=== TESTING STAFF NAME SETTINGS ===")
        
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Test color change
        print("TEST: Testing staff name color change")
        setattr(dialog, 'staff_name_color_value', '#ff00ff')
        dialog.staff_name_font_color.setStyleSheet("background-color: #ff00ff; color: white;")
        new_color = getattr(dialog, 'staff_name_color_value', '#000000')
        print(f"TEST: New staff name color: {new_color}")
        
        # Save settings
        dialog.save_settings()
        saved_color = self.document.settings.get('notation/staff_name_font_color', '#000000')
        print(f"TEST: Saved staff name color in document: {saved_color}")
        
        dialog.close()
    
    def test_section_name_settings(self):
        """Test section name settings"""
        print("\n=== TESTING SECTION NAME SETTINGS ===")
        
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Test color change
        print("TEST: Testing section name color change")
        setattr(dialog, 'section_name_color_value', '#ffff00')
        dialog.section_name_font_color.setStyleSheet("background-color: #ffff00; color: black;")
        new_color = getattr(dialog, 'section_name_color_value', '#000000')
        print(f"TEST: New section name color: {new_color}")
        
        # Save settings
        dialog.save_settings()
        saved_color = self.document.settings.get('notation/section_name_font_color', '#000000')
        print(f"TEST: Saved section name color in document: {saved_color}")
        
        dialog.close()
    
    def test_save_load_settings(self):
        """Test saving and loading settings"""
        print("\n=== TESTING SAVE/LOAD SETTINGS ===")
        
        # Set some test settings
        test_settings = {
            'notation/clef_font_color': '#ff0000',
            'notation/time_sig_font_color': '#00ff00',
            'notation/key_sig_font_color': '#0000ff',
            'notation/staff_name_font_color': '#ff00ff',
            'notation/section_name_font_color': '#ffff00',
        }
        
        self.document.settings.update(test_settings)
        print(f"TEST: Set test settings: {test_settings}")
        
        # Create dialog and load settings
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        dialog.load_settings()
        
        # Check if settings were loaded correctly
        print("TEST: Checking loaded settings:")
        print(f"TEST: Clef color: {getattr(dialog, 'clef_color_value', 'NOT_SET')}")
        print(f"TEST: Time sig color: {getattr(dialog, 'time_sig_color_value', 'NOT_SET')}")
        print(f"TEST: Key sig color: {getattr(dialog, 'key_sig_color_value', 'NOT_SET')}")
        print(f"TEST: Staff name color: {getattr(dialog, 'staff_name_color_value', 'NOT_SET')}")
        print(f"TEST: Section name color: {getattr(dialog, 'section_name_color_value', 'NOT_SET')}")
        
        dialog.close()
    
    def test_set_as_defaults(self):
        """Test setting as defaults"""
        print("\n=== TESTING SET AS DEFAULTS ===")
        
        dialog = FullScoreOptionsDialog(self)
        dialog.document = self.document
        
        # Set some test values
        dialog.clef_font_size.setValue(40)
        dialog.time_sig_font_size.setValue(30)
        setattr(dialog, 'clef_color_value', '#ff0000')
        setattr(dialog, 'time_sig_color_value', '#00ff00')
    
        print("TEST: Set test values in dialog")
        print(f"TEST: Clef font size: {dialog.clef_font_size.value()}")
        print(f"TEST: Time sig font size: {dialog.time_sig_font_size.value()}")
        print(f"TEST: Clef color: {getattr(dialog, 'clef_color_value', 'NOT_SET')}")
        print(f"TEST: Time sig color: {getattr(dialog, 'time_sig_color_value', 'NOT_SET')}")
        
        # Save as defaults
        dialog.set_as_defaults()
        
        # Check if defaults were saved
        settings = QSettings("ONOTE", "Preferences")
        print("TEST: Checking saved defaults:")
        print(f"TEST: Clef font size default: {settings.value('notation/clef_font_size', 'NOT_SET')}")
        print(f"TEST: Time sig font size default: {settings.value('notation/time_sig_font_size', 'NOT_SET')}")
        print(f"TEST: Clef color default: {settings.value('notation/clef_font_color', 'NOT_SET')}")
        print(f"TEST: Time sig color default: {settings.value('notation/time_sig_font_color', 'NOT_SET')}")
        
        dialog.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec()) 