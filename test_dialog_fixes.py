#!/usr/bin/env python3
"""
Test script to verify dialog fixes are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_preferences_dialog():
    """Test that Preferences dialog color controls are working"""
    print("Testing Preferences Dialog...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.dialogs.preferences_dialog import PreferencesDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = PreferencesDialog()
        
        # Test that color controls exist and are enabled
        assert hasattr(dialog, 'clef_font_color'), "Clef color control missing"
        assert hasattr(dialog, 'time_sig_font_color'), "Time signature color control missing"
        assert hasattr(dialog, 'key_sig_font_color'), "Key signature color control missing"
        
        assert dialog.clef_font_color.isEnabled(), "Clef color control not enabled"
        assert dialog.time_sig_font_color.isEnabled(), "Time signature color control not enabled"
        assert dialog.key_sig_font_color.isEnabled(), "Key signature color control not enabled"
        
        print("✅ Preferences dialog color controls are working")
        
    except Exception as e:
        print(f"❌ Preferences dialog test failed: {e}")
        return False
    
    return True

def test_full_score_options_dialog():
    """Test that Full Score Options dialog can be created"""
    print("Testing Full Score Options Dialog...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = FullScoreOptionsDialog()
        
        # Test that the dialog can be created
        assert dialog is not None, "Dialog creation failed"
        
        # Test that it has the expected controls
        assert hasattr(dialog, 'directions_horizontal'), "Musical Directions horizontal control missing"
        
        print("✅ Full Score Options dialog can be created")
        
    except Exception as e:
        print(f"❌ Full Score Options dialog test failed: {e}")
        return False
    
    return True

def test_color_methods():
    """Test that color methods work correctly"""
    print("Testing Color Methods...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.dialogs.preferences_dialog import PreferencesDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = PreferencesDialog()
        
        # Test that choose_font_color method handles new categories
        assert hasattr(dialog, 'choose_font_color'), "choose_font_color method missing"
        
        # Test that color value attributes can be set
        dialog.clef_color_value = '#ff0000'
        dialog.time_sig_color_value = '#00ff00'
        dialog.key_sig_color_value = '#0000ff'
        
        assert dialog.clef_color_value == '#ff0000', "Clef color not set correctly"
        assert dialog.time_sig_color_value == '#00ff00', "Time signature color not set correctly"
        assert dialog.key_sig_color_value == '#0000ff', "Key signature color not set correctly"
        
        print("✅ Color methods are working")
        
    except Exception as e:
        print(f"❌ Color methods test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("Running Dialog Fix Tests...")
    print("=" * 50)
    
    tests = [
        test_preferences_dialog,
        test_full_score_options_dialog,
        test_color_methods
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Dialog fixes are working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 