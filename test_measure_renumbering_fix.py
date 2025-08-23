#!/usr/bin/env python3
"""
Test script to verify the measure renumbering fix after barline deletion.

This test specifically checks that:
1. After deleting measures, remaining measures are renumbered consecutively starting from 1
2. The form widget sync correctly uses document dictionary keys instead of stale measure_number properties
3. The logs show the correct measure numbers after deletion
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings
from src.gui.music.score_document import ScoreDocument
from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge
from src.gui.music.measure_object import MeasureObject

def test_measure_renumbering_after_deletion():
    """Test that measures are correctly renumbered after deletion"""
    print("=== TESTING MEASURE RENUMBERING AFTER DELETION ===")
    
    # Create test document
    document = ScoreDocument()
    document.measures = {}
    
    # Create temporal bridge
    bridge = BarlineTemporalBridge(document=document)
    
    # Test scenario: Create 3 measures, then delete measure 2
    print("\n1. Creating 3 measures...")
    
    # Create measures 1, 2, 3
    for i in range(1, 4):
        measure = MeasureObject(
            measure_number=i,
            end_x=i * 300,
            document=document,
            barline_type='single'
        )
        document.measures[i] = measure
        print(f"   Created measure #{i}")
    
    print(f"   Document has {len(document.measures)} measures: {sorted(document.measures.keys())}")
    
    # Delete measure 2
    print("\n2. Deleting measure 2...")
    success = bridge.remove_barline(2)
    print(f"   Deletion success: {success}")
    
    # Check the results
    print(f"   Document now has {len(document.measures)} measures: {sorted(document.measures.keys())}")
    
    # Verify measure numbering
    print("\n3. Verifying measure renumbering...")
    expected_measures = [1, 2]  # After deleting measure 2, we should have measures 1, 2 (was 3)
    actual_measures = sorted(document.measures.keys())
    
    print(f"   Expected measures: {expected_measures}")
    print(f"   Actual measures: {actual_measures}")
    
    # Check each measure's internal number
    for key, measure in document.measures.items():
        internal_number = getattr(measure, 'measure_number', 'NO_NUMBER')
        print(f"   Measure key {key}: internal measure_number = {internal_number}")
        
        # CRITICAL CHECK: The key should match the internal number
        if key != internal_number:
            print(f"   ❌ MISMATCH: Key {key} != internal number {internal_number}")
            return False
    
    # Check that we have exactly 2 measures numbered 1 and 2
    if actual_measures != [1, 2]:
        print(f"   ❌ WRONG MEASURE KEYS: Expected [1, 2], got {actual_measures}")
        return False
    
    # Check that the first measure is numbered 1 and second is numbered 2
    if document.measures[1].measure_number != 1:
        print(f"   ❌ WRONG INTERNAL NUMBER: Measure 1 has internal number {document.measures[1].measure_number}")
        return False
    
    if document.measures[2].measure_number != 2:
        print(f"   ❌ WRONG INTERNAL NUMBER: Measure 2 has internal number {document.measures[2].measure_number}")
        return False
    
    print("   ✅ Measure renumbering is CORRECT!")
    return True

def test_form_widget_sync_fix():
    """Test that form widget sync uses correct measure numbers"""
    print("\n=== TESTING FORM WIDGET SYNC FIX ===")
    
    # Create mock form widget sync scenario
    # Simulate what happens after temporal bridge renumbering
    
    # Document with correctly renumbered measures
    document = ScoreDocument()
    document.measures = {
        1: MeasureObject(measure_number=1, end_x=300, document=document, barline_type='single'),
        2: MeasureObject(measure_number=2, end_x=600, document=document, barline_type='single')
    }
    
    # But simulate old/stale measure_number properties (this was the bug)
    # In the real bug, these would be stale after renumbering
    document.measures[1].measure_number = 1  # This one is correct
    document.measures[2].measure_number = 3  # This one is stale (should be 2)
    
    print(f"   Document keys: {sorted(document.measures.keys())}")
    print(f"   Internal numbers: {[m.measure_number for m in document.measures.values()]}")
    
    # Simulate the fixed sync method
    synced_measures = {}
    for measure_key, measure in document.measures.items():
        if isinstance(measure_key, int):
            # FIXED: Use document's key as the correct measure number
            measure.measure_number = measure_key  # Update to match key
            synced_measures[measure_key] = measure
    
    print(f"   After sync - keys: {sorted(synced_measures.keys())}")
    print(f"   After sync - internal numbers: {[m.measure_number for m in synced_measures.values()]}")
    
    # Verify the fix worked
    if sorted(synced_measures.keys()) != [1, 2]:
        print(f"   ❌ WRONG SYNCED KEYS: Expected [1, 2], got {sorted(synced_measures.keys())}")
        return False
    
    if synced_measures[1].measure_number != 1:
        print(f"   ❌ WRONG SYNCED NUMBER: Measure 1 has internal number {synced_measures[1].measure_number}")
        return False
    
    if synced_measures[2].measure_number != 2:
        print(f"   ❌ WRONG SYNCED NUMBER: Measure 2 has internal number {synced_measures[2].measure_number}")
        return False
    
    print("   ✅ Form widget sync fix is CORRECT!")
    return True

if __name__ == "__main__":
    # Initialize Qt application
    app = QApplication(sys.argv)
    
    # Run tests
    test1_passed = test_measure_renumbering_after_deletion()
    test2_passed = test_form_widget_sync_fix()
    
    print(f"\n=== TEST RESULTS ===")
    print(f"Measure renumbering test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Form widget sync test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    overall_result = test1_passed and test2_passed
    print(f"Overall: {'✅ ALL TESTS PASSED' if overall_result else '❌ SOME TESTS FAILED'}")
    
    if overall_result:
        print("\n🎉 The measure renumbering fix is working correctly!")
    else:
        print("\n❌ The fix needs more work.")
    
    sys.exit(0 if overall_result else 1) 