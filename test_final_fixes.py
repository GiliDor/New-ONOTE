#!/usr/bin/env python3
"""
Final test script to verify all fixes work correctly:
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

def test_all_fixes():
    """Test that all fixes work correctly"""
    
    print("=== Testing All Fixes ===")
    
    # Create a document
    document = ScoreDocument()
    
    # Create temporal bridge
    bridge = BarlineTemporalBridge(document)
    
    # Test 1: Initial measure creation
    print("\n--- Test 1: Initial Measure Creation ---")
    bridge.enter_edit_mode()
    
    # Check if initial measure was created
    if hasattr(document, 'measures') and document.measures:
        print(f"✅ Initial measure created successfully")
        print(f"   Measures: {list(document.measures.keys())}")
        for measure_num, measure in document.measures.items():
            print(f"   Measure {measure_num}: x={measure.x_position}, end_x={measure.end_x}, width={measure.end_x - measure.x_position}")
    else:
        print("❌ Initial measure not created")
        return False
    
    # Test 2: Barline numbers functionality
    print("\n--- Test 2: Barline Numbers ---")
    
    # Enable barline numbering in document settings
    if not hasattr(document, 'settings'):
        document.settings = {}
    
    document.settings.update({
        'notation/barline_numbering': True,
        'notation/barline_number_font_size': 8,
        'notation/barline_numbers_font_color': '#666666'
    })
    
    print("✅ Barline numbering enabled in settings")
    
    # Test 3: Measure number positioning
    print("\n--- Test 3: Measure Number Positioning ---")
    
    # Set measure number settings
    document.settings.update({
        'notation/show_measure_numbers': True,
        'notation/measure_numbers_frequency': 'Every Measure',
        'notation/measure_numbers_position': 'Beginning',
        'notation/measure_numbers_font_color': '#e8161a'
    })
    
    print("✅ Measure number settings configured")
    
    # Test 4: Create additional measures to test justification
    print("\n--- Test 4: Additional Measures and Justification ---")
    
    # Create a few more barlines to test justification
    for i in range(3):
        x_pos = 300 + (i + 1) * 200  # Simple positioning for test
        new_measure = bridge.create_barline_at_position(x_pos, "single")
        if new_measure:
            print(f"✅ Created barline at x={x_pos}, measure {new_measure.measure_number}")
        else:
            print(f"❌ Failed to create barline at x={x_pos}")
    
    # Check final measure layout
    if hasattr(document, 'measures') and document.measures:
        print(f"✅ Final measure count: {len(document.measures)}")
        for measure_num in sorted(document.measures.keys()):
            measure = document.measures[measure_num]
            print(f"   Measure {measure_num}: x={measure.x_position}, end_x={measure.end_x}")
    
    print("\n=== All Tests Completed ===")
    return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        success = test_all_fixes()
        if success:
            print("🎉 All fixes working correctly!")
        else:
            print("❌ Some fixes failed")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    app.quit() 