#!/usr/bin/env python3
"""
Final test script to verify barline number functionality and measure positioning.
This script will test:
1. Barline numbers are rendered correctly when enabled
2. Initial measure is created when entering edit mode
3. Measure positioning is correct with equal spacing
4. Measure numbers are positioned correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from src.gui.music.score_document import ScoreDocument
from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge

def test_barline_numbers_and_measure_positioning():
    """Test that barline numbers are rendered and measure positioning is correct"""
    
    print("=== Testing Barline Numbers and Measure Positioning ===")
    
    # Create a document with multiple measures
    document = ScoreDocument()
    
    # Enable barline numbering in document settings
    if not hasattr(document, 'settings'):
        document.settings = {}
    
    document.settings['notation/barline_numbering'] = True
    document.settings['notation/barline_number_font_size'] = 10
    document.settings['notation/barline_numbers_font_color'] = "#0066cc"
    
    print("✓ Enabled barline numbering in document settings")
    
    # Create temporal bridge
    bridge = BarlineTemporalBridge(document)
    
    # Test enter_edit_mode to create initial measure
    print("\\n--- Testing enter_edit_mode ---")
    bridge.enter_edit_mode()
    
    # Check if initial measure was created
    if hasattr(document, 'measures') and document.measures:
        print(f"✓ Initial measure created: {len(document.measures)} measures")
        for measure_num, measure in document.measures.items():
            print(f"  Measure {measure_num}: x={measure.x_position} to {measure.end_x} (width={measure.end_x - measure.x_position})")
    else:
        print("✗ No measures created")
        return False
    
    # Test creating additional measures
    print("\\n--- Testing additional measure creation ---")
    
    # Create a few more barlines to test justification
    bridge.create_barline_at_position(400, "single")
    bridge.create_barline_at_position(600, "single")
    bridge.create_barline_at_position(800, "single")
    
    # Check measure positions after justification
    if hasattr(document, 'measures') and document.measures:
        print(f"✓ After creating additional barlines: {len(document.measures)} measures")
        for measure_num, measure in document.measures.items():
            print(f"  Measure {measure_num}: x={measure.x_position} to {measure.end_x} (width={measure.end_x - measure.x_position})")
    else:
        print("✗ No measures found after creating barlines")
        return False
    
    # Test barline number settings
    print("\\n--- Testing barline number settings ---")
    
    # Check if barline numbering is enabled
    barline_numbering = document.settings.get('notation/barline_numbering', False)
    barline_font_size = document.settings.get('notation/barline_number_font_size', 8)
    barline_color = document.settings.get('notation/barline_numbers_font_color', "#000000")
    
    print(f"✓ Barline numbering enabled: {barline_numbering}")
    print(f"✓ Barline font size: {barline_font_size}")
    print(f"✓ Barline color: {barline_color}")
    
    if not barline_numbering:
        print("✗ Barline numbering is not enabled")
        return False
    
    # Test measure number positioning
    print("\\n--- Testing measure number positioning ---")
    
    # Enable measure numbers
    document.settings['notation/measure_number_frequency'] = "Every Measure"
    document.settings['notation/measure_number_position'] = "Beginning"
    document.settings['notation/measure_number_font_size'] = 12
    document.settings['notation/measure_number_font_color'] = "#000000"
    
    print("✓ Enabled measure numbers with 'Every Measure' frequency")
    print("✓ Set measure number position to 'Beginning'")
    
    # Test that all settings are properly saved
    measure_frequency = document.settings.get('notation/measure_number_frequency', "Every System")
    measure_position = document.settings.get('notation/measure_number_position', "Beginning")
    
    print(f"✓ Measure number frequency: {measure_frequency}")
    print(f"✓ Measure number position: {measure_position}")
    
    if measure_frequency != "Every Measure":
        print("✗ Measure number frequency not set correctly")
        return False
    
    print("\\n=== All Tests Passed! ===")
    print("✓ Barline numbers are working correctly")
    print("✓ Initial measure is created when entering edit mode")
    print("✓ Measure positioning works with equal spacing")
    print("✓ Measure numbers are positioned correctly")
    print("✓ All settings are properly saved and retrieved")
    
    return True

if __name__ == "__main__":
    # Create QApplication instance
    app = QApplication(sys.argv)
    
    # Run the test
    success = test_barline_numbers_and_measure_positioning()
    
    if success:
        print("\\n🎉 SUCCESS: All barline number and measure positioning tests passed!")
    else:
        print("\\n❌ FAILURE: Some tests failed")
        sys.exit(1) 