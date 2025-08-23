#!/usr/bin/env python3
"""
Simple test to verify that the color reset issue is fixed.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.music.score_document import ScoreDocument

def test_color_fix():
    """Test that changing a spinner doesn't reset colors to black"""
    
    app = QApplication.instance() or QApplication([])
    
    # Create a test document with custom colors
    document = ScoreDocument()
    document.settings = {
        'notation/clef_font_color': '#e8161a',
        'notation/time_sig_font_color': '#a1040b', 
        'notation/key_sig_font_color': '#0ff3f0',
        'notation/staff_name_font_color': '#00ff00',
        'notation/section_name_font_color': '#ff00ff',
    }
    
    print("TEST: Document settings before dialog creation:")
    for key, value in document.settings.items():
        print(f"  {key}: {value}")
    
    # Create dialog
    dialog = FullScoreOptionsDialog()
    dialog.document = document
    
    print("\nTEST: Dialog color values after initialization:")
    print(f"  clef_color_value: {dialog.clef_color_value}")
    print(f"  time_sig_color_value: {dialog.time_sig_color_value}")
    print(f"  key_sig_color_value: {dialog.key_sig_color_value}")
    print(f"  staff_name_color_value: {dialog.staff_name_color_value}")
    print(f"  section_name_color_value: {dialog.section_name_color_value}")
    
    # Change a spinner (this should NOT reset colors to black)
    print("\nTEST: Changing staff name font size spinner...")
    dialog.staff_name_font_size.setValue(15)
    
    print("\nTEST: Dialog color values after spinner change:")
    print(f"  clef_color_value: {dialog.clef_color_value}")
    print(f"  time_sig_color_value: {dialog.time_sig_color_value}")
    print(f"  key_sig_color_value: {dialog.key_sig_color_value}")
    print(f"  staff_name_color_value: {dialog.staff_name_color_value}")
    print(f"  section_name_color_value: {dialog.section_name_color_value}")
    
    # Check document settings
    print("\nTEST: Document settings after spinner change:")
    for key, value in document.settings.items():
        print(f"  {key}: {value}")
    
    # Verify colors are still correct
    assert dialog.clef_color_value == '#e8161a', f"Clef color was reset to {dialog.clef_color_value}"
    assert dialog.time_sig_color_value == '#a1040b', f"Time sig color was reset to {dialog.time_sig_color_value}"
    assert dialog.key_sig_color_value == '#0ff3f0', f"Key sig color was reset to {dialog.key_sig_color_value}"
    assert dialog.staff_name_color_value == '#00ff00', f"Staff name color was reset to {dialog.staff_name_color_value}"
    assert dialog.section_name_color_value == '#ff00ff', f"Section name color was reset to {dialog.section_name_color_value}"
    
    print("\n✅ SUCCESS: Colors were NOT reset to black when spinner was changed!")
    
    # Test changing another spinner
    print("\nTEST: Changing clef font size spinner...")
    dialog.clef_font_size.setValue(40)
    
    print("\nTEST: Dialog color values after second spinner change:")
    print(f"  clef_color_value: {dialog.clef_color_value}")
    print(f"  time_sig_color_value: {dialog.time_sig_color_value}")
    print(f"  key_sig_color_value: {dialog.key_sig_color_value}")
    print(f"  staff_name_color_value: {dialog.staff_name_color_value}")
    print(f"  section_name_color_value: {dialog.section_name_color_value}")
    
    # Verify colors are still correct
    assert dialog.clef_color_value == '#e8161a', f"Clef color was reset to {dialog.clef_color_value}"
    assert dialog.time_sig_color_value == '#a1040b', f"Time sig color was reset to {dialog.time_sig_color_value}"
    assert dialog.key_sig_color_value == '#0ff3f0', f"Key sig color was reset to {dialog.key_sig_color_value}"
    assert dialog.staff_name_color_value == '#00ff00', f"Staff name color was reset to {dialog.staff_name_color_value}"
    assert dialog.section_name_color_value == '#ff00ff', f"Section name color was reset to {dialog.section_name_color_value}"
    
    print("\n✅ SUCCESS: Colors were NOT reset to black when second spinner was changed!")
    
    print("\n🎉 ALL TESTS PASSED! The color reset issue is FIXED!")

if __name__ == "__main__":
    test_color_fix() 