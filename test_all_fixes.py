#!/usr/bin/env python3
"""
Test script to verify all dialog communication and settings isolation fixes.

This script tests:
1. Full Score Options "Set as Defaults" functionality
2. Full Score Options "Reset to Defaults" functionality  
3. Parameter isolation between different notation elements
4. File persistence of document-specific settings
5. Proper precedence: document settings override preferences
"""

import sys
import os
import tempfile
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.dialogs.preferences_dialog import PreferencesDialog
from src.gui.music.score_document import ScoreDocument

def test_1_set_as_defaults():
    """Test 1: Verify 'Set as Defaults' properly transfers ALL settings"""
    print("\n=== TEST 1: Set as Defaults Communication ===")
    
    # Create Full Score Options dialog with test values
    fso_dialog = FullScoreOptionsDialog()
    
    # Set unique test values for all notation elements
    fso_dialog.staff_name_font_size.setValue(15)
    fso_dialog.staff_name_vertical.setValue(-10)
    fso_dialog.staff_name_horizontal.setValue(5)
    fso_dialog.staff_name_color_value = '#ff0000'
    
    fso_dialog.section_name_font_size.setValue(18)
    fso_dialog.section_name_vertical.setValue(-5)
    fso_dialog.section_name_horizontal.setValue(10)
    fso_dialog.section_name_color_value = '#00ff00'
    
    fso_dialog.clef_font_size.setValue(35)
    fso_dialog.clef_vertical.setValue(3)
    fso_dialog.clef_horizontal.setValue(25)
    fso_dialog.clef_color_value = '#0000ff'
    
    fso_dialog.time_sig_font_size.setValue(28)
    fso_dialog.time_sig_vertical.setValue(-2)
    fso_dialog.time_sig_horizontal.setValue(45)
    fso_dialog.time_sig_spacing.setValue(20)
    fso_dialog.time_sig_color_value = '#ffff00'
    
    fso_dialog.key_sig_font_size.setValue(16)
    fso_dialog.key_sig_vertical.setValue(1)
    fso_dialog.key_sig_horizontal.setValue(80)
    fso_dialog.key_sig_accidental_spacing.setValue(15)
    fso_dialog.key_sig_color_value = '#ff00ff'
    
    fso_dialog.directions_font_size.setValue(12)
    fso_dialog.directions_vertical.setValue(2)
    fso_dialog.directions_horizontal.setValue(3)
    
    # Save as defaults
    fso_dialog.set_as_defaults()
    
    # Verify all settings were saved to QSettings
    settings = QSettings("ONOTE", "Preferences")
    
    # Test all staff name settings
    assert settings.value("notation/staff_name_font_size", type=int) == 15, "Staff name font size not saved"
    assert settings.value("notation/staff_name_vertical", type=int) == -10, "Staff name vertical not saved"
    assert settings.value("notation/staff_name_horizontal", type=int) == 5, "Staff name horizontal not saved"
    assert settings.value("notation/staff_name_font_color") == '#ff0000', "Staff name color not saved"
    
    # Test all section name settings
    assert settings.value("notation/section_name_font_size", type=int) == 18, "Section name font size not saved"
    assert settings.value("notation/section_name_vertical", type=int) == -5, "Section name vertical not saved"
    assert settings.value("notation/section_name_horizontal", type=int) == 10, "Section name horizontal not saved"
    assert settings.value("notation/section_name_font_color") == '#00ff00', "Section name color not saved"
    
    # Test all clef settings
    assert settings.value("notation/clef_font_size", type=int) == 35, "Clef font size not saved"
    assert settings.value("notation/clef_vertical", type=int) == 3, "Clef vertical not saved"
    assert settings.value("notation/clef_horizontal", type=int) == 25, "Clef horizontal not saved"
    assert settings.value("notation/clef_font_color") == '#0000ff', "Clef color not saved"
    
    # Test all time signature settings
    assert settings.value("notation/time_sig_font_size", type=int) == 28, "Time sig font size not saved"
    assert settings.value("notation/time_sig_vertical", type=int) == -2, "Time sig vertical not saved"
    assert settings.value("notation/time_sig_horizontal", type=int) == 45, "Time sig horizontal not saved"
    assert settings.value("notation/time_sig_spacing", type=int) == 20, "Time sig spacing not saved"
    assert settings.value("notation/time_sig_font_color") == '#ffff00', "Time sig color not saved"
    
    # Test all key signature settings
    assert settings.value("notation/key_sig_font_size", type=int) == 16, "Key sig font size not saved"
    assert settings.value("notation/key_sig_vertical", type=int) == 1, "Key sig vertical not saved"
    assert settings.value("notation/key_sig_horizontal", type=int) == 80, "Key sig horizontal not saved"
    assert settings.value("notation/key_sig_accidental_spacing", type=int) == 15, "Key sig spacing not saved"
    assert settings.value("notation/key_sig_font_color") == '#ff00ff', "Key sig color not saved"
    
    # Test musical directions settings
    assert settings.value("notation/directions_font_size", type=int) == 12, "Directions font size not saved"
    assert settings.value("notation/directions_vertical", type=int) == 2, "Directions vertical not saved"
    assert settings.value("notation/directions_horizontal", type=int) == 3, "Directions horizontal not saved"
    
    print("✓ Set as Defaults: ALL settings properly transferred to Preferences")
    return True

def test_2_reset_to_defaults():
    """Test 2: Verify 'Reset to Defaults' loads from Preferences instead of constants"""
    print("\n=== TEST 2: Reset to Defaults Functionality ===")
    
    # Create Full Score Options dialog
    fso_dialog = FullScoreOptionsDialog()
    
    # Set non-default values
    fso_dialog.staff_name_font_size.setValue(99)
    fso_dialog.clef_color_value = '#999999'
    
    # Reset to defaults (should load from QSettings, not constants)
    fso_dialog.reset_to_defaults()
    
    # Should match the values we saved in test 1
    assert fso_dialog.staff_name_font_size.value() == 15, f"Reset didn't load from Preferences: {fso_dialog.staff_name_font_size.value()}"
    assert getattr(fso_dialog, 'staff_name_color_value', '#000000') == '#ff0000', "Reset didn't load color from Preferences"
    
    print("✓ Reset to Defaults: Properly loads from Preferences instead of constants")
    return True

def test_3_parameter_isolation():
    """Test 3: Verify all notation elements are completely independent"""
    print("\n=== TEST 3: Parameter Isolation ===")
    
    # Create Full Score Options dialog
    fso_dialog = FullScoreOptionsDialog()
    
    # Test changing one parameter doesn't affect others
    original_clef_size = fso_dialog.clef_font_size.value()
    original_time_sig_size = fso_dialog.time_sig_font_size.value()
    original_key_sig_size = fso_dialog.key_sig_font_size.value()
    
    # Change staff name settings
    fso_dialog.staff_name_font_size.setValue(50)
    fso_dialog.staff_name_color_value = '#abcdef'
    
    # Verify other elements unchanged
    assert fso_dialog.clef_font_size.value() == original_clef_size, "Clef affected by staff name change"
    assert fso_dialog.time_sig_font_size.value() == original_time_sig_size, "Time sig affected by staff name change"
    assert fso_dialog.key_sig_font_size.value() == original_key_sig_size, "Key sig affected by staff name change"
    
    # Change clef settings
    fso_dialog.clef_horizontal.setValue(100)
    fso_dialog.clef_color_value = '#fedcba'
    
    # Verify other elements still unchanged
    assert fso_dialog.staff_name_font_size.value() == 50, "Staff name affected by clef change"
    assert fso_dialog.time_sig_font_size.value() == original_time_sig_size, "Time sig affected by clef change"
    
    print("✓ Parameter Isolation: Each notation element is completely independent")
    return True

def test_4_file_persistence():
    """Test 4: Verify score files save/load their settings independently of Preferences"""
    print("\n=== TEST 4: File Persistence ===")
    
    # Create a document with specific settings
    document = ScoreDocument()
    document.settings = {
        'notation/staff_name_font_size': 999,
        'notation/staff_name_font_color': '#123456',
        'notation/clef_font_size': 888,
        'notation/clef_font_color': '#654321',
        'notation/time_sig_horizontal': 777,
        'notation/key_sig_vertical': 666,
    }
    
    # Serialize to dict (simulating file save)
    saved_data = document.to_dict()
    
    # Verify settings are included
    assert 'settings' in saved_data, "Settings not included in save data"
    assert saved_data['settings']['notation/staff_name_font_size'] == 999, "Staff name font size not saved"
    assert saved_data['settings']['notation/staff_name_font_color'] == '#123456', "Staff name color not saved"
    
    # Create new document from saved data (simulating file load)
    loaded_document = ScoreDocument.from_dict(saved_data)
    
    # Verify settings are restored
    assert loaded_document.settings['notation/staff_name_font_size'] == 999, "Staff name font size not restored"
    assert loaded_document.settings['notation/staff_name_font_color'] == '#123456', "Staff name color not restored"
    assert loaded_document.settings['notation/clef_font_size'] == 888, "Clef font size not restored"
    assert loaded_document.settings['notation/clef_font_color'] == '#654321', "Clef color not restored"
    
    print("✓ File Persistence: Document settings properly saved and loaded independently")
    return True

def test_5_document_precedence():
    """Test 5: Verify document settings override preferences"""
    print("\n=== TEST 5: Document Settings Precedence ===")
    
    # Set preferences values
    settings = QSettings("ONOTE", "Preferences")
    settings.setValue("notation/staff_name_font_size", 100)
    settings.setValue("notation/clef_font_color", "#aaaaaa")
    
    # Create document with different values
    document = ScoreDocument()
    document.settings = {
        'notation/staff_name_font_size': 200,  # Should override preference
        'notation/clef_font_color': '#bbbbbb',  # Should override preference
    }
    
    # Create Full Score Options dialog with this document
    fso_dialog = FullScoreOptionsDialog()
    fso_dialog.set_document(document)
    fso_dialog.load_current_settings()
    
    # Should use document values, not preferences
    assert fso_dialog.staff_name_font_size.value() == 200, f"Document precedence failed for font size: {fso_dialog.staff_name_font_size.value()}"
    assert getattr(fso_dialog, 'clef_color_value', '#000000') == '#bbbbbb', f"Document precedence failed for color: {getattr(fso_dialog, 'clef_color_value', '#000000')}"
    
    print("✓ Document Precedence: Document settings properly override preferences")
    return True

def main():
    """Run all tests"""
    print("🔧 Testing ONOTE Dialog Communication and Settings Isolation Fixes")
    print("=" * 70)
    
    # Initialize Qt application for testing
    app = QApplication(sys.argv)
    
    try:
        # Run all tests
        test_1_set_as_defaults()
        test_2_reset_to_defaults()
        test_3_parameter_isolation()
        test_4_file_persistence()
        test_5_document_precedence()
        
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED! All fixes are working correctly:")
        print("   ✓ Set as Defaults transfers ALL settings properly")
        print("   ✓ Reset to Defaults loads from Preferences (not constants)")
        print("   ✓ All notation elements are completely isolated")
        print("   ✓ Score files save/load settings independently")
        print("   ✓ Document settings properly override preferences")
        print("\n🚀 The rebuilt application has all fixes applied!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        app.quit()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 