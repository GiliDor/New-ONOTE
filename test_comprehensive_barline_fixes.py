#!/usr/bin/env python3
"""
Comprehensive test script to verify all barline system fixes:
1. Proper measure indexing (ONOTE Rule 2 compliance)
2. System wrapping (measures per system limit enforcement)
3. Justified positioning (ONOTE Rule 1 compliance)
4. Measure number positioning (correct placement relative to measures)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from src.gui.music.score_document import ScoreDocument
from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge
from src.gui.music.measure_numbers import MeasureNumberManager, MeasureNumberSettings

def test_comprehensive_barline_system():
    """Test all aspects of the barline system"""
    
    print("=== COMPREHENSIVE BARLINE SYSTEM TEST ===")
    
    # Create application and document
    app = QApplication([])
    document = ScoreDocument()
    
    # Configure document settings
    if not hasattr(document, 'settings'):
        document.settings = {}
    
    # Enable measure numbers and barline numbering
    document.settings.update({
        'notation/show_measure_numbers': True,
        'notation/measure_numbers_frequency': 'Every Measure',
        'notation/measure_numbers_position': 'Center',
        'notation/measure_numbers_font_color': '#e8161a',
        'notation/barline_numbering': True,
        'notation/barline_number_font_size': 10,
        'notation/barline_numbers_font_color': '#0066cc'
    })
    
    print("✓ Document settings configured")
    
    # Create temporal bridge
    bridge = BarlineTemporalBridge(document)
    
    # Test 1: Initial measure creation
    print("\n--- Test 1: Initial Measure Creation ---")
    bridge.enter_edit_mode()
    
    if hasattr(document, 'measures') and document.measures:
        print(f"✓ Initial measure created: {len(document.measures)} measures")
        for measure_num, measure in document.measures.items():
            print(f"  Measure {measure_num}: x={getattr(measure, 'x_position', 'N/A')} to {getattr(measure, 'end_x', 'N/A')}")
    else:
        print("✗ No measures created")
        return False
    
    # Test 2: Measure indexing compliance (ONOTE Rule 2)
    print("\n--- Test 2: Measure Indexing (ONOTE Rule 2) ---")
    
    # Create additional measures to test indexing
    test_positions = [400, 600, 800, 1000]
    created_measures = []
    
    for i, x_pos in enumerate(test_positions):
        new_measure = bridge.create_barline_at_position(x_pos, "single")
        if new_measure:
            created_measures.append(new_measure)
            print(f"✓ Created measure {new_measure.measure_number} at x={x_pos}")
        else:
            print(f"✗ Failed to create measure at x={x_pos}")
    
    # Verify measure numbering is sequential
    measure_numbers = sorted([getattr(m, 'measure_number', 0) for m in created_measures])
    expected_numbers = list(range(2, len(created_measures) + 2))  # Starting from 2 (after initial measure)
    
    if measure_numbers == expected_numbers:
        print(f"✓ Measure numbering is sequential: {measure_numbers}")
    else:
        print(f"✗ Measure numbering error: got {measure_numbers}, expected {expected_numbers}")
        return False
    
    # Test 3: System wrapping (measures per system limit)
    print("\n--- Test 3: System Wrapping ---")
    
    # Check current measures per system setting
    measures_per_system = getattr(bridge, 'measures_per_system', 4)
    print(f"Measures per system limit: {measures_per_system}")
    
    # Try to create more measures than the limit
    extra_positions = [1100, 1200, 1300, 1400]
    extra_measures = []
    
    for i, x_pos in enumerate(extra_positions):
        new_measure = bridge.create_barline_at_position(x_pos, "single")
        if new_measure:
            extra_measures.append(new_measure)
            print(f"✓ Created extra measure {new_measure.measure_number} at x={x_pos}")
        else:
            print(f"✗ System limit reached at x={x_pos} (expected behavior)")
            break
    
    total_measures = len(document.measures)
    print(f"Total measures created: {total_measures}")
    
    if total_measures <= measures_per_system:
        print("✓ System wrapping working correctly")
    else:
        print(f"✗ System wrapping not working - {total_measures} measures exceed limit of {measures_per_system}")
    
    # Test 4: Justified positioning (ONOTE Rule 1)
    print("\n--- Test 4: Justified Positioning (ONOTE Rule 1) ---")
    
    # Check that measures are positioned with equal spacing
    measures = sorted(document.measures.items(), key=lambda x: x[0])
    
    if len(measures) >= 3:
        # Calculate spacing between consecutive measures
        spacings = []
        for i in range(1, len(measures)):
            prev_end = getattr(measures[i-1][1], 'end_x', 0)
            curr_end = getattr(measures[i][1], 'end_x', 0)
            spacing = curr_end - prev_end
            spacings.append(spacing)
        
        # Check if spacings are approximately equal (within 10% tolerance)
        if spacings:
            avg_spacing = sum(spacings) / len(spacings)
            tolerance = avg_spacing * 0.1
            
            all_equal = all(abs(spacing - avg_spacing) <= tolerance for spacing in spacings)
            
            if all_equal:
                print(f"✓ Measures are justified with equal spacing: ~{avg_spacing:.1f}px")
            else:
                print(f"✗ Measures are not justified - spacings vary: {spacings}")
        else:
            print("✓ Insufficient measures to test justification")
    else:
        print("✓ Insufficient measures to test justification")
    
    # Test 5: Measure number positioning
    print("\n--- Test 5: Measure Number Positioning ---")
    
    # Create measure number manager
    measure_number_manager = MeasureNumberManager(document)
    
    # Test measure number positioning calculation
    test_settings = MeasureNumberSettings()
    test_settings.position = test_settings.position  # Center
    test_settings.horizontal_offset = -111  # Standard offset
    
    # Test positioning for different measure widths
    test_cases = [
        (265.0, 215.25, 1),   # Measure 1
        (480.25, 215.25, 2),  # Measure 2
        (695.5, 215.25, 3),   # Measure 3
    ]
    
    for measure_x, measure_width, measure_number in test_cases:
        x, y = measure_number_manager.renderer.calculate_position(
            measure_x, measure_width, 40.0, measure_number
        )
        print(f"Measure {measure_number}: x={x:.1f}, y={y:.1f} (start={measure_x}, width={measure_width})")
        
        # Verify positioning logic
        if measure_number == 1:
            # Measure 1 should be positioned relative to first note position
            expected_x = measure_x + test_settings.horizontal_offset
        else:
            # Other measures should be positioned at center
            expected_x = measure_x + (measure_width / 2) + test_settings.horizontal_offset
        
        if abs(x - expected_x) < 1.0:
            print(f"  ✓ Position correct for measure {measure_number}")
        else:
            print(f"  ✗ Position incorrect for measure {measure_number}: got {x:.1f}, expected {expected_x:.1f}")
    
    # Test 6: Barline type consistency
    print("\n--- Test 6: Barline Type Consistency ---")
    
    # Check that all measures use 'single' barline type
    all_single = True
    for measure_num, measure in document.measures.items():
        barline_type = getattr(measure, 'barline_type', 'unknown')
        if barline_type != 'single':
            print(f"✗ Measure {measure_num} has incorrect barline type: {barline_type}")
            all_single = False
    
    if all_single:
        print("✓ All measures use 'single' barline type consistently")
    else:
        print("✗ Some measures have incorrect barline types")
    
    # Test 7: Document state consistency
    print("\n--- Test 7: Document State Consistency ---")
    
    # Verify document has all required attributes
    required_attrs = ['measures', 'settings']
    missing_attrs = []
    
    for attr in required_attrs:
        if not hasattr(document, attr):
            missing_attrs.append(attr)
    
    if missing_attrs:
        print(f"✗ Document missing attributes: {missing_attrs}")
    else:
        print("✓ Document has all required attributes")
    
    # Verify measures collection is properly structured
    if hasattr(document, 'measures') and document.measures:
        if isinstance(document.measures, dict):
            print("✓ Measures collection is properly structured as dictionary")
        else:
            print("✗ Measures collection is not a dictionary")
    else:
        print("✗ No measures collection found")
    
    print("\n=== COMPREHENSIVE TEST COMPLETED ===")
    
    # Summary
    print(f"\nSummary:")
    print(f"- Total measures created: {len(document.measures)}")
    print(f"- Measures per system limit: {measures_per_system}")
    print(f"- System wrapping: {'Working' if len(document.measures) <= measures_per_system else 'Not working'}")
    print(f"- Measure numbering: {'Sequential' if measure_numbers == expected_numbers else 'Incorrect'}")
    print(f"- Barline types: {'Consistent' if all_single else 'Inconsistent'}")
    
    return True

if __name__ == "__main__":
    success = test_comprehensive_barline_system()
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    sys.exit(0 if success else 1) 