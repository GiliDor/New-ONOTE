#!/usr/bin/env python3
"""
Script to reset cached settings that are causing inconsistent behavior
"""

import sys
sys.path.append('src')

from PyQt6.QtCore import QSettings
from src.core.settings_manager import SettingsManager

def reset_problematic_settings():
    """Reset cached settings that are causing issues"""
    print("=== RESETTING PROBLEMATIC CACHED SETTINGS ===")
    
    # Create QSettings instance to directly manipulate cached values
    settings = QSettings()
    
    # List of settings to reset
    problematic_keys = [
        "layout/measure_numbers_horizontal_offset",  # Currently cached as -59, should be -34
        "layout/measure_numbers_h_offset",           # Ensure consistency
    ]
    
    for key in problematic_keys:
        old_value = settings.value(key, "NOT_SET")
        print(f"Removing cached setting: {key} = {old_value}")
        settings.remove(key)
    
    # Sync changes
    settings.sync()
    print("Settings reset and synced")
    
    # Test that settings manager now uses defaults
    print("\n=== TESTING AFTER RESET ===")
    settings_manager = SettingsManager()
    
    test_keys = [
        "layout/measure_numbers_horizontal_offset",
        "layout/measure_numbers_h_offset"
    ]
    
    for key in test_keys:
        value = settings_manager.get_setting(key, "DEFAULT_NOT_FOUND")
        print(f"{key}: {value}")
    
    print("\n✅ Settings reset complete. The application should now use correct defaults.")

if __name__ == "__main__":
    reset_problematic_settings() 