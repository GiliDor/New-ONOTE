#!/usr/bin/env python3
"""
Comprehensive Test for ONOTE Specification Compliance

This test validates all the fixes made according to the detailed ONOTE specifications:
1. Initial state: Score starts with NO measures (only barline 0)
2. Measure renumbering: Consecutive numbering after deletion (Rule 2)
3. Form widget default: Single barline preselected
4. Measures per system enforcement: Constraint enforcement
5. Barline type restrictions: Only Single and Dashed can be created directly
6. UI restructuring: Proper organization of controls
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from src.gui.music.score_document import ScoreDocument
from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge
from src.gui.music.widgets.form_widget import FormWidget
from src.gui.dialogs.preferences_dialog import PreferencesDialog

def test_initial_state_compliance():
    """Test 1: Initial state - Score starts with NO measures (only barline 0)"""
    print("=" * 60)
    print("TEST 1: Initial State Compliance")
    print("=" * 60)
    
    # Create fresh document
    document = ScoreDocument()
    bridge = BarlineTemporalBridge(document)
    
    # Check initial state
    measures = bridge._get_current_measures()
    initial_count = len(measures)
    
    print(f"Initial measure count: {initial_count}")
    print(f"Expected: 0 (score starts empty)")
    
    if initial_count == 0:
        print("✅ PASS: Score starts with NO measures (ONOTE specification compliant)")
    else:
        print("❌ FAIL: Score should start with NO measures")
        return False
    
    return True

def test_measure_renumbering_compliance():
    """Test 2: Measure renumbering - Consecutive numbering after deletion (Rule 2)"""
    print("=" * 60)
    print("TEST 2: Measure Renumbering Compliance (Rule 2)")
    print("=" * 60)
    
    # Create document and bridge
    document = ScoreDocument()
    bridge = BarlineTemporalBridge(document)
    
    # Create multiple measures
    measure1 = bridge.create_barline_at_position(400.0, "single")
    measure2 = bridge.create_barline_at_position(500.0, "single")
    measure3 = bridge.create_barline_at_position(600.0, "single")
    
    print(f"Created 3 measures")
    measures = bridge._get_current_measures()
    print(f"Before deletion: {len(measures)} measures")
    for m in measures:
        print(f"  Measure #{getattr(m, 'measure_number', 'unknown')}")
    
    # Delete middle measure (should trigger renumbering)
    success = bridge.remove_barline(2)
    print(f"Deleted measure 2: {success}")
    
    # Check renumbering
    measures = bridge._get_current_measures()
    print(f"After deletion: {len(measures)} measures")
    
    # Verify consecutive numbering starting from 1
    expected_numbers = [1, 2]  # Should be renumbered consecutively
    actual_numbers = sorted([getattr(m, 'measure_number', 0) for m in measures])
    
    print(f"Expected numbering: {expected_numbers}")
    print(f"Actual numbering: {actual_numbers}")
    
    if actual_numbers == expected_numbers:
        print("✅ PASS: Measures renumbered consecutively (Rule 2 compliant)")
    else:
        print("❌ FAIL: Measures not renumbered consecutively")
        return False
    
    return True

def test_form_widget_default_compliance():
    """Test 3: Form widget default - Single barline preselected"""
    print("=" * 60)
    print("TEST 3: Form Widget Default Compliance")
    print("=" * 60)
    
    # Create Qt application for widget testing
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create document and form widget
    document = ScoreDocument()
    form_widget = FormWidget(None)
    form_widget.document = document
    
    # Check default selection
    selected_type = form_widget.get_selected_barline_type()
    print(f"Default selected barline type: {selected_type}")
    print(f"Expected: 'single'")
    
    if selected_type == "single":
        print("✅ PASS: Single barline preselected by default")
    else:
        print("❌ FAIL: Single barline should be preselected by default")
        return False
    
    return True

def test_measures_per_system_enforcement():
    """Test 4: Measures per system enforcement - Constraint enforcement"""
    print("=" * 60)
    print("TEST 4: Measures Per System Enforcement")
    print("=" * 60)
    
    # Create document and bridge
    document = ScoreDocument()
    bridge = BarlineTemporalBridge(document)
    
    # Set measures per system to 2 for testing
    bridge.measures_per_system = 2
    print(f"Set measures per system limit to: {bridge.measures_per_system}")
    
    # Create measures up to the limit
    measure1 = bridge.create_barline_at_position(400.0, "single")
    measure2 = bridge.create_barline_at_position(500.0, "single")
    
    measures = bridge._get_current_measures()
    print(f"Created {len(measures)} measures (at limit)")
    
    # Try to create one more (should be rejected)
    measure3 = bridge.create_barline_at_position(600.0, "single")
    
    measures_after = bridge._get_current_measures()
    print(f"After attempting to exceed limit: {len(measures_after)} measures")
    
    if len(measures_after) == 2 and measure3 is None:
        print("✅ PASS: Measures per system constraint enforced")
    else:
        print("❌ FAIL: Measures per system constraint not enforced")
        return False
    
    return True

def test_barline_type_restrictions():
    """Test 5: Barline type restrictions - Only Single and Dashed can be created directly"""
    print("=" * 60)
    print("TEST 5: Barline Type Restrictions")
    print("=" * 60)
    
    # Test with Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create document and form widget
    document = ScoreDocument()
    form_widget = FormWidget(None)
    form_widget.document = document
    
    # Test allowed types (single, dashed)
    print("Testing allowed barline types:")
    
    # Single should work
    form_widget.barline_button_group.buttons()[0].setChecked(True)  # Single
    result1 = form_widget.create_barline_at_position(400.0)
    print(f"  Single barline creation: {'✅ PASS' if result1 else '❌ FAIL'}")
    
    # Test restricted types (double, final, repeat_start, repeat_end, repeat_both)
    print("Testing restricted barline types:")
    restricted_types = ["double", "final", "repeat_start", "repeat_end", "repeat_both"]
    
    all_restricted = True
    for i, btn in enumerate(form_widget.barline_button_group.buttons()[1:], 1):  # Skip single
        barline_type = btn.property("barline_type")
        if barline_type == "dashed":
            continue  # Skip dashed, it's allowed
        
        if barline_type in restricted_types:
            btn.setChecked(True)
            result = form_widget.create_barline_at_position(500.0 + i * 50)
            if result is not None:
                print(f"  {barline_type} creation: ❌ FAIL (should be restricted)")
                all_restricted = False
            else:
                print(f"  {barline_type} creation: ✅ PASS (correctly restricted)")
    
    if all_restricted:
        print("✅ PASS: Barline type restrictions properly enforced")
    else:
        print("❌ FAIL: Some restricted barline types allowed direct creation")
        return False
    
    return True

def test_ui_restructuring_compliance():
    """Test 6: UI restructuring - Proper organization of controls"""
    print("=" * 60)
    print("TEST 6: UI Restructuring Compliance")
    print("=" * 60)
    
    # Test with Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create preferences dialog
    preferences = PreferencesDialog(None)
    
    # Check if Notation Setup tab exists
    notation_tab_found = False
    for i in range(preferences.tab_widget.count()):
        if preferences.tab_widget.tabText(i) == "Notation Setup":
            notation_tab_found = True
            break
    
    print(f"Notation Setup tab found: {'✅ PASS' if notation_tab_found else '❌ FAIL'}")
    
    # Check if measure numbers controls moved to Notation Setup
    has_measure_controls = (hasattr(preferences, 'show_measure_numbers') and 
                           hasattr(preferences, 'measure_numbers_frequency') and
                           hasattr(preferences, 'measure_numbers_font_color'))
    print(f"Measure number controls in Notation Setup: {'✅ PASS' if has_measure_controls else '❌ FAIL'}")
    
    # Check if barline controls added
    has_barline_controls = (hasattr(preferences, 'max_measures_per_system') and 
                           hasattr(preferences, 'barline_numbering') and
                           hasattr(preferences, 'barline_number_font_color'))
    print(f"Barline controls in Notation Setup: {'✅ PASS' if has_barline_controls else '❌ FAIL'}")
    
    # Check if font color controls added
    has_font_colors = (hasattr(preferences, 'staff_name_font_color') and 
                      hasattr(preferences, 'section_name_font_color') and
                      hasattr(preferences, 'measure_numbers_font_color') and
                      hasattr(preferences, 'barline_number_font_color'))
    print(f"Font color controls in Notation Setup: {'✅ PASS' if has_font_colors else '❌ FAIL'}")
    
    if notation_tab_found and has_measure_controls and has_barline_controls and has_font_colors:
        print("✅ PASS: UI restructuring properly implemented")
    else:
        print("❌ FAIL: UI restructuring incomplete")
        return False
    
    return True

def main():
    """Run all compliance tests"""
    print("ONOTE SPECIFICATION COMPLIANCE TEST SUITE")
    print("=" * 60)
    print("Testing all fixes according to detailed ONOTE specifications")
    print("=" * 60)
    
    tests = [
        test_initial_state_compliance,
        test_measure_renumbering_compliance,
        test_form_widget_default_compliance,
        test_measures_per_system_enforcement,
        test_barline_type_restrictions,
        test_ui_restructuring_compliance
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAIL: {test.__name__} - Exception: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - ONOTE specification compliance achieved!")
        return True
    else:
        print(f"⚠️  {failed} tests failed - specification compliance incomplete")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 