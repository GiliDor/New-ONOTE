#!/usr/bin/env python3
"""
Test script to verify the final remaining critical fixes:
1. Barline removal working consistently (no "Measure not found" errors)
2. No automatic end bars at x=1126 vs user barlines at x=1136 
3. Measure 1 positioning relative to first note position (265px) not key signature (225px)
4. Settings manager defaulting to -34 offset instead of -130
"""

import sys
sys.path.append('src')

from src.core.settings_manager import SettingsManager
from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge
from src.gui.music.measure_numbers import MeasureNumberSettings, MeasureNumberRenderer
from src.gui.music.score_document import ScoreDocument

def test_settings_manager_defaults():
    """Test that settings manager uses correct defaults"""
    print("=== TESTING SETTINGS MANAGER DEFAULTS ===")
    
    settings = SettingsManager()
    
    # Test horizontal offset default
    h_offset = settings.get_setting("layout/measure_numbers_h_offset", None)
    print(f"Settings manager horizontal offset: {h_offset}")
    
    # Test from default settings
    defaults = settings._get_default_settings()
    default_h_offset = defaults.get("layout/measure_numbers_h_offset", "NOT_FOUND")
    print(f"Default settings horizontal offset: {default_h_offset}")
    
    # Check frequency default
    frequency = settings.get_setting("layout/measure_numbers_frequency", None)
    print(f"Settings manager frequency: {frequency}")
    
    success = (default_h_offset == -34 and 
              defaults.get("layout/measure_numbers_frequency") == "Every Measure")
    print(f"✅ Settings defaults: {'PASS' if success else 'FAIL'}")
    return success

def test_measure_number_positioning():
    """Test that measure 1 uses note position, not key signature"""
    print("\\n=== TESTING MEASURE NUMBER POSITIONING ===")
    
    # Create mock settings with -34 offset
    settings = MeasureNumberSettings()
    settings.horizontal_offset = -34
    settings.position = MeasureNumberSettings().position  # Beginning
    
    renderer = MeasureNumberRenderer(settings)
    
    # Test measure 1 positioning (should use 265px + offset = 231px)
    measure_x = 265.0  # First note position
    measure_width = 174.2
    staff_y = 40
    
    x, y = renderer.calculate_position(measure_x, measure_width, staff_y, measure_number=1)
    print(f"Measure 1 position: x={x} (expected ~231), y={y}")
    
    # Test measure 2 positioning (should use barline position + offset)
    measure_2_x = 439.2  # Second measure start (barline position)
    x2, y2 = renderer.calculate_position(measure_2_x, measure_width, staff_y, measure_number=2)
    print(f"Measure 2 position: x={x2} (expected ~473), y={y2}")
    
    # Verify: Measure 1 should be at 231px (265 + (-34)), not 95px (225 + (-130))
    expected_m1_x = 265.0 + (-34)  # 231px
    expected_m2_x = 439.2 + 34    # 473.2px
    
    success = (abs(x - expected_m1_x) < 1.0 and abs(x2 - expected_m2_x) < 1.0)
    print(f"✅ Measure positioning: {'PASS' if success else 'FAIL'}")
    return success

def test_barline_positioning_consistency():
    """Test that all barlines use consistent x=1136 positioning"""
    print("\\n=== TESTING BARLINE POSITIONING CONSISTENCY ===")
    
    # Create a mock document and temporal bridge
    document = ScoreDocument()
    document.measures = {}
    
    bridge = BarlineTemporalBridge(document)
    
    # Check END_BARLINE_X constant
    end_x = bridge.END_BARLINE_X
    print(f"Temporal bridge END_BARLINE_X: {end_x}")
    
    # Create a measure and check its positioning
    bridge.create_initial_measure()
    
    measures = bridge._get_current_measures()
    if measures:
        measure = measures[0]
        measure_end_x = getattr(measure, 'end_x', 'unknown')
        print(f"Created measure end_x: {measure_end_x}")
        
        success = (end_x == 1136.0 and measure_end_x == 1136.0)
    else:
        print("No measures created")
        success = False
    
    print(f"✅ Barline positioning: {'PASS' if success else 'FAIL'}")
    return success

def test_barline_removal():
    """Test that barline removal works without 'Measure not found' errors"""
    print("\\n=== TESTING BARLINE REMOVAL ===")
    
    document = ScoreDocument()
    document.measures = {}
    
    bridge = BarlineTemporalBridge(document)
    
    # Create multiple measures
    bridge.create_initial_measure()  # Measure 1
    bridge.create_barline_at_position(500.0)  # Should create measure 2
    bridge.create_barline_at_position(750.0)  # Should create measure 3
    
    initial_count = len(bridge._get_current_measures())
    print(f"Created {initial_count} measures")
    
    # Try to remove measure 2
    try:
        success = bridge.remove_barline(2)
        remaining_count = len(bridge._get_current_measures())
        print(f"Removal success: {success}, remaining measures: {remaining_count}")
        
        # Check that measure numbers are sequential
        measures = bridge._get_current_measures()
        measure_nums = [getattr(m, 'measure_number', 'unknown') for m in measures]
        print(f"Remaining measure numbers: {measure_nums}")
        
        # Should have 2 measures numbered 1 and 2 (renumbered)
        expected_success = (success == True and remaining_count == 2 and 
                          set(measure_nums) == {1, 2})
        
    except Exception as e:
        print(f"Barline removal failed with error: {e}")
        expected_success = False
    
    print(f"✅ Barline removal: {'PASS' if expected_success else 'FAIL'}")
    return expected_success

def main():
    """Run all tests"""
    print("Testing final remaining fixes for ONOTE barline system\\n")
    
    results = []
    results.append(test_settings_manager_defaults())
    results.append(test_measure_number_positioning())
    results.append(test_barline_positioning_consistency())
    results.append(test_barline_removal())
    
    print(f"\\n=== FINAL RESULTS ===")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 ALL FIXES WORKING CORRECTLY!")
    else:
        print("❌ Some fixes still need work")
        
    return all(results)

if __name__ == "__main__":
    main() 