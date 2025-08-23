#!/usr/bin/env python3
"""
Test script to debug form widget settings loading
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import QSettings
from gui.music.widgets.form_widget import FormWidget
from gui.music.score_document import ScoreDocument

def test_form_widget_debug():
    """Test form widget settings loading with debugging"""
    app = QApplication(sys.argv)
    
    # Set some test values in QSettings
    settings = QSettings()
    settings.setValue('notation/show_measure_numbers', True)
    settings.setValue('notation/barline_numbering', True)
    settings.setValue('notation/measure_numbers_font_color', '#FF0000')
    settings.setValue('notation/barline_numbers_font_color', '#00FF00')
    settings.setValue('notation/max_measures_per_system', 6)
    
    print("=== QSettings values ===")
    print(f"show_measure_numbers: {settings.value('notation/show_measure_numbers')}")
    print(f"barline_numbering: {settings.value('notation/barline_numbering')}")
    print(f"measure_numbers_font_color: {settings.value('notation/measure_numbers_font_color')}")
    print(f"barline_numbers_font_color: {settings.value('notation/barline_numbers_font_color')}")
    print(f"max_measures_per_system: {settings.value('notation/max_measures_per_system')}")
    
    # Create a document with some settings
    document = ScoreDocument()
    document.settings = {
        'notation/show_measure_numbers': True,
        'notation/barline_numbering': True,
        'notation/measure_numbers_font_color': '#FF0000',
        'notation/barline_numbers_font_color': '#00FF00',
        'notation/max_measures_per_system': 6
    }
    
    print("\n=== Document settings ===")
    print(f"Document settings: {document.settings}")
    
    # Create main window
    main_window = QMainWindow()
    main_window.document = document
    
    # Create form widget
    form_widget = FormWidget(main_window)
    form_widget.set_document(document)
    
    print("\n=== Form widget controls after initialization ===")
    print(f"show_measure_numbers.isChecked(): {form_widget.show_measure_numbers.isChecked()}")
    print(f"barline_numbering.isChecked(): {form_widget.barline_numbering.isChecked()}")
    print(f"max_measures_per_system.value(): {form_widget.max_measures_per_system.value()}")
    print(f"measure_numbers_color_value: {getattr(form_widget, 'measure_numbers_color_value', 'NOT SET')}")
    print(f"barline_numbers_color_value: {getattr(form_widget, 'barline_numbers_color_value', 'NOT SET')}")
    
    # Show the form widget
    form_widget.show()
    
    print("\n=== Form widget controls after show() ===")
    print(f"show_measure_numbers.isChecked(): {form_widget.show_measure_numbers.isChecked()}")
    print(f"barline_numbering.isChecked(): {form_widget.barline_numbering.isChecked()}")
    print(f"max_measures_per_system.value(): {form_widget.max_measures_per_system.value()}")
    print(f"measure_numbers_color_value: {getattr(form_widget, 'measure_numbers_color_value', 'NOT SET')}")
    print(f"barline_numbers_color_value: {getattr(form_widget, 'barline_numbers_color_value', 'NOT SET')}")
    
    # Create a simple window to show the form widget
    window = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(form_widget)
    
    close_button = QPushButton("Close")
    close_button.clicked.connect(window.close)
    layout.addWidget(close_button)
    
    window.setLayout(layout)
    window.setWindowTitle("Form Widget Debug Test")
    window.resize(800, 600)
    window.show()
    
    print("\n=== Test window shown ===")
    print("Check the form widget to see if settings are displayed correctly")
    
    return app.exec()

if __name__ == "__main__":
    test_form_widget_debug() 