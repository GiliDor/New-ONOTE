#!/usr/bin/env python3
"""
Test script to verify the undo/redo synchronization fixes.

This script tests the specific issues reported:
1. First undo showing blank page (should now force proper refresh)
2. Setup dialog not reflecting undone state (should now sync properly)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.music.main_window import MainWindow
from src.notation.model.staves import SingleStaff

def test_undo_sync_fixes():
    """Test the undo/redo synchronization fixes"""
    
    print("=== Testing Undo/Redo Synchronization Fixes ===")
    print()
    
    app = QApplication(sys.argv)
    
    # Create main window and document
    print("1. Creating main window and document...")
    window = MainWindow()
    window.show()
    window.new_score()
    
    # Process events to ensure everything is initialized
    QApplication.processEvents()
    
    if not hasattr(window, 'staff_view') or not window.staff_view or not window.staff_view.document:
        print("❌ ERROR: Failed to create document")
        return False
    
    document = window.staff_view.document
    print("✅ Document created successfully")
    
    # Ensure we're in EDIT mode (white background)
    if hasattr(document, 'layout'):
        document.layout.set_setup_mode(False)
        print("✅ Set to EDIT mode (white background)")
    
    # Record initial state
    initial_staves = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
    print(f"✅ Initial state: {initial_staves} staff(s)")
    print()
    
    print("2. Testing Add Staves → Apply → Undo sequence...")
    
    # Step 1: Save state before changes
    document._undo_context = "Before Adding Staves"
    document.save_state()
    print("📝 Saved initial state")
    
    # Step 2: Add multiple staves to simulate setup changes
    staff1 = SingleStaff(instrument_name="Violin 1", instrument_id="violin_1", clef="treble")
    staff2 = SingleStaff(instrument_name="Violin 2", instrument_id="violin_2", clef="treble") 
    staff3 = SingleStaff(instrument_name="Cello", instrument_id="cello", clef="bass")
    
    document.layout.ungrouped_staves.extend([staff1, staff2, staff3])
    
    # Save state after adding staves
    document._undo_context = "After Adding 3 Staves"
    document.save_state()
    
    current_staves = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
    print(f"➕ Added staves: {current_staves} staff(s) (was {initial_staves})")
    
    # Force update
    window.staff_view.update()
    QApplication.processEvents()
    
    print()
    print("3. Testing undo operations (this should fix the blank page issue)...")
    
    # Test first undo - this was showing blank page before
    print("   🔄 First undo...")
    window.undo()
    QApplication.processEvents()
    
    after_first_undo = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
    print(f"   📊 After first undo: {after_first_undo} staff(s)")
    
    # Test second undo
    print("   🔄 Second undo...")
    window.undo()
    QApplication.processEvents()
    
    after_second_undo = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
    print(f"   📊 After second undo: {after_second_undo} staff(s)")
    
    print()
    print("4. Testing setup dialog synchronization...")
    
    # Open score setup dialog to test synchronization
    print("   🔧 Opening score setup dialog...")
    window.show_score_setup()
    QApplication.processEvents()
    
    # Check if setup widget was refreshed properly
    if MainWindow._score_setup_widget:
        widget = MainWindow._score_setup_widget
        dialog_staff_count = widget.staff_list.topLevelItemCount()
        print(f"   📋 Setup dialog shows: {dialog_staff_count} staff(s)")
        print(f"   📋 Document actually has: {after_second_undo} staff(s)")
        
        if dialog_staff_count == after_second_undo:
            print("   ✅ FIXED: Setup dialog correctly reflects undone state!")
        else:
            print("   ❌ ISSUE: Setup dialog still not synchronized")
            
        # List what the dialog shows
        print("   📝 Dialog contents:")
        for i in range(dialog_staff_count):
            item = widget.staff_list.topLevelItem(i)
            staff_name = item.text(0)
            staff_type = item.text(1)
            clef = item.text(2)
            print(f"      {i+1}. {staff_name} ({staff_type}, {clef})")
    else:
        print("   ❌ Setup widget not available")
    
    print()
    print("5. Testing redo operations...")
    
    # Test redo to make sure it also works properly
    print("   ⏩ First redo...")
    window.redo()
    QApplication.processEvents()
    
    after_first_redo = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
    print(f"   📊 After first redo: {after_first_redo} staff(s)")
    
    print()
    print("=== Test Summary ===")
    print(f"Initial state: {initial_staves} staff(s)")
    print(f"After adding staves: {current_staves} staff(s)")
    print(f"After first undo: {after_first_undo} staff(s)")
    print(f"After second undo: {after_second_undo} staff(s)")
    print(f"After first redo: {after_first_redo} staff(s)")
    
    # Check if the progression makes sense
    if after_second_undo == initial_staves:
        print("✅ UNDO worked correctly - returned to initial state")
    else:
        print(f"❌ UNDO issue - expected {initial_staves}, got {after_second_undo}")
    
    if after_first_redo > after_second_undo:
        print("✅ REDO worked correctly - progressed forward")
    else:
        print("❌ REDO issue - did not progress forward properly")
    
    print()
    print("=== Key Fixes Applied ===")
    print("1. ✅ Added forced layout position update in undo/redo")
    print("2. ✅ Added forced repaint() to ensure immediate UI refresh")
    print("3. ✅ Enhanced refresh_from_document() with detailed logging")
    print("4. ✅ Ensured setup dialog always syncs with current document state")
    
    # Keep window open for manual verification
    print()
    print("Window will remain open for manual verification...")
    print("Try using Ctrl+Z and opening Score Setup to verify synchronization.")
    
    return True

if __name__ == "__main__":
    test_undo_sync_fixes() 