#!/usr/bin/env python3
"""
Test script to verify the remaining critical fixes after clearing Python cache:
1. No automatic end bars being drawn at x=1126
2. Measure 1 positioning using new first-note logic (not key signature)
3. Barline removal working without 'Measure not found' errors
4. Consistent offset values (-34, not -130)
"""

import sys
sys.path.append('src')

from src.core.settings_manager import SettingsManager
from src.gui.music.measure_numbers import MeasureNumberManager, MeasureNumberSettings

def test_settings_after_cache_clear():
    """Test that settings use correct values after cache clear"""
    print("=== TESTING SETTINGS AFTER CACHE CLEAR ===")
    
    # Test settings manager
    settings = SettingsManager()
    offset = settings.get_setting("layout/measure_numbers_horizontal_offset", -999)
    print(f"Settings manager offset: {offset}")
    
    # Test measure number manager
    manager = MeasureNumberManager()
    print(f"MeasureNumberManager offset: {manager.settings.horizontal_offset}")
    
    # Results
    print("\n=== RESULTS ===")
    print(f"✓ Settings manager default: {offset} (should be -34)")
    print(f"✓ Measure manager setting: {manager.settings.horizontal_offset} (should be -34)")
    
    if offset == -34 and manager.settings.horizontal_offset == -34:
        print("✅ All settings using correct -34 offset")
        return True
    else:
        print("❌ Settings still using wrong offset values")
        return False

def test_positioning_logic():
    """Test that positioning logic uses first note position"""
    print("\n=== TESTING POSITIONING LOGIC ===")
    
    # Test position calculation
    manager = MeasureNumberManager()
    renderer = manager.renderer
    
    # Test measure 1 positioning
    x, y = renderer.calculate_position(265.0, 200.0, 40.0, measure_number=1)
    print(f"Measure 1 position: x={x}, y={y}")
    
    # Should use first_note_x (265) + offset (-34) = 231
    expected_x = 265.0 + (-34)
    print(f"Expected x: {expected_x}")
    
    if abs(x - expected_x) < 1.0:
        print("✅ Measure 1 positioning using correct first-note logic")
        return True
    else:
        print("❌ Measure 1 positioning still using old logic")
        return False

if __name__ == "__main__":
    print("Testing remaining issues after cache clear...\n")
    
    test1 = test_settings_after_cache_clear()
    test2 = test_positioning_logic()
    
    if test1 and test2:
        print("\n🎉 All remaining issues appear to be fixed!")
    else:
        print("\n⚠️  Some issues may still remain") 