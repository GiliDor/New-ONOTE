#!/usr/bin/env python3
"""
Test to verify that undo/redo operations in white mode (EDIT mode) 
properly sync with the score setup dialog state.

This test demonstrates that after undo operations in white mode,
the setup dialog shows the correct undone state.
"""

import sys
import os
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

# Add the src directory to Python path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_undo_sync_with_setup():
    """Test that undo/redo in white mode syncs with setup dialog"""
    
    print("=== Testing Undo/Redo Sync Between White Mode and Setup Dialog ===")
    print()
    
    # Import after adding src to path
    from src.gui.music.main_window import MainWindow
    
    app = QApplication(sys.argv)
    
    # Create main window with document
    window = MainWindow()
    window.show()
    
    # Ensure we're in EDIT mode (white background)
    if hasattr(window, 'staff_view') and hasattr(window.staff_view, 'document'):
        document = window.staff_view.document
        if hasattr(document, 'layout'):
            document.layout.set_setup_mode(False)
            print("✅ Set to EDIT mode (white background)")
        
        # Test scenario: Start with initial state, add staves, undo, check setup dialog
        print()
        print("🔍 Testing Undo/Redo Sync:")
        print()
        
        # Step 1: Record initial state
        initial_staves = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
        print(f"1. Initial state: {initial_staves} staff(s)")
        
        # Step 2: Save state and add some staves (simulate setup changes)
        document._undo_context = "Test Setup Changes"
        document.save_state()
        print("2. Saved initial state for undo")
        
        # Simulate adding staves by creating setup changes
        from src.notation.model.staves import SingleStaff
        
        # Add a staff directly to the document
        new_staff = SingleStaff(
            instrument_name="Test Violin",
            instrument_id="test_violin", 
            clef="treble"
        )
        document.layout.ungrouped_staves.append(new_staff)
        
        # Add another staff
        new_staff2 = SingleStaff(
            instrument_name="Test Cello",
            instrument_id="test_cello",
            clef="bass"
        )
        document.layout.ungrouped_staves.append(new_staff2)
        
        current_staves = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
        print(f"3. After adding staves: {current_staves} staff(s)")
        
        # Update the display
        window.staff_view.update()
        
        # Step 3: Test undo operation
        print("4. Performing UNDO operation...")
        window.undo()
        
        # Check the state after undo
        undo_staves = len(document.layout.ungrouped_staves) + sum(len(section.staves) for section in document.layout.sections)
        print(f"5. After undo: {undo_staves} staff(s)")
        
        # Step 4: Open setup dialog and check if it reflects the undone state
        print("6. Opening setup dialog to check sync...")
        
        # Open the setup dialog
        window.show_score_setup()
        
        # Give time for the dialog to open and refresh
        QTimer.singleShot(100, lambda: check_setup_sync(window, undo_staves))
        
        # Run briefly to process events
        QTimer.singleShot(500, app.quit)
        app.exec()
        
    else:
        print("❌ ERROR: No document available for testing")
        return False

def check_setup_sync(window, expected_staves):
    """Check if the setup dialog shows the correct undone state"""
    print("7. Checking setup dialog state...")
    
    # Get the setup widget
    if hasattr(window, '_score_setup_widget') and window._score_setup_widget:
        setup_widget = window._score_setup_widget
        
        # Count staves in the setup widget
        staff_count = setup_widget.staff_list.topLevelItemCount()
        print(f"8. Setup dialog shows: {staff_count} staff(s)")
        
        # Check if the counts match
        if staff_count == expected_staves:
            print("✅ SUCCESS: Setup dialog properly reflects the undone state!")
            print(f"   Both document and setup dialog show {expected_staves} staff(s)")
        else:
            print("❌ ISSUE: Setup dialog doesn't reflect the undone state")
            print(f"   Document has {expected_staves} staff(s), setup dialog shows {staff_count}")
        
        # Also check the staff names if possible
        print("9. Staff details in setup dialog:")
        for i in range(staff_count):
            item = setup_widget.staff_list.topLevelItem(i)
            if item:
                staff_name = item.text(0)
                clef = item.text(2)
                print(f"   - {staff_name} ({clef})")
    
    else:
        print("❌ ERROR: Setup widget not available")

if __name__ == "__main__":
    test_undo_sync_with_setup() 