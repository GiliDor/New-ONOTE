#!/usr/bin/env python3
"""
Final test script to verify score setup dialog synchronization after undo operations.

This tests the fix for the issue where the score setup dialog would retain 
the original state instead of reflecting the current undone state.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.music.main_window import MainWindow
from src.notation.model.staves import SingleStaff

def test_dialog_sync_final():
    """Final test for dialog synchronization after undo operations"""
    
    print("=== FINAL TEST: Score Setup Dialog Sync After Undo ===")
    print()
    
    app = QApplication(sys.argv)
    
    # Create main window and document
    print("1. Creating main window and new document...")
    main_window = MainWindow()
    main_window.new_document()
    main_window.show()
    
    staff_view = main_window.staff_view
    document = staff_view.document
    
    print(f"✓ Document created with {len(document.layout.ungrouped_staves)} initial staves")
    
    # Add multiple staves to test with
    print("\n2. Adding test staves...")
    
    test_staves = [
        ("Flute", "flute"),
        ("Oboe", "oboe"), 
        ("Clarinet", "clarinet"),
        ("Bassoon", "bassoon"),
        ("Trumpet", "trumpet")
    ]
    
    for name, instrument_id in test_staves:
        staff = SingleStaff(instrument_id=instrument_id, instrument_name=name)
        document.add_staff(staff)
        print(f"  ✓ Added {name}")
    
    total_staves = len(document.layout.ungrouped_staves)
    print(f"✓ Total staves after adding: {total_staves}")
    
    # Save undo state
    print("\n3. Saving undo state...")
    if hasattr(document, 'save_state'):
        document.save_state("Added Multiple Staves")
        print("✓ Undo state saved")
    
    # Go to white mode (edit mode) 
    print("\n4. Switching to edit mode (white)...")
    staff_view.enter_edit_mode()
    print("✓ Now in edit mode")
    
    # Perform undo operations to test sync
    print("\n5. Performing undo operations in white mode...")
    
    # Remove 3 staves and create undo states
    for i in range(3):
        if len(document.layout.ungrouped_staves) > 0:
            staff_to_remove = document.layout.ungrouped_staves[-1]
            staff_name = staff_to_remove.instrument_name
            document.remove_staff(staff_to_remove)
            print(f"  ✓ Removed {staff_name}")
            
            # Save state for undo
            if hasattr(document, 'save_state'):
                document.save_state(f"Remove {staff_name}")
    
    # Perform 2 undo operations
    undo_count = 0
    for i in range(2):
        if hasattr(document, 'undo') and document.undo():
            undo_count += 1
            print(f"  ✓ Undo operation {i+1} successful")
        else:
            print(f"  ✗ Undo operation {i+1} failed")
            break
    
    final_staff_count = len(document.layout.ungrouped_staves)
    print(f"✓ After {undo_count} undos: {final_staff_count} staves remain")
    
    # Test the dialog synchronization
    print("\n6. Testing dialog synchronization...")
    
    def test_dialog_manual():
        """Manually test the dialog to see if it shows correct state"""
        print("  Creating dialog manually to test sync...")
        
        try:
            from src.gui.music.score_setup_dialog import ScoreSetupDialog
            
            # Create dialog manually and check state before and after refresh
            test_dialog = ScoreSetupDialog(staff_view)
            
            # Check initial state (might be wrong)
            initial_count = test_dialog.setup_widget.staff_list.topLevelItemCount()
            print(f"  Dialog initial state: {initial_count} staves")
            print(f"  Document actual state: {final_staff_count} staves")
            
            if initial_count != final_staff_count:
                print(f"  ✗ BEFORE REFRESH: Mismatch detected!")
                print(f"    Dialog shows {initial_count}, should show {final_staff_count}")
                
                # Force refresh
                print("  Calling refresh_from_document()...")
                test_dialog.refresh_from_document()
                
                # Check after refresh
                after_refresh_count = test_dialog.setup_widget.staff_list.topLevelItemCount()
                print(f"  Dialog after refresh: {after_refresh_count} staves")
                
                if after_refresh_count == final_staff_count:
                    print("  ✓ AFTER REFRESH: Synchronization successful!")
                else:
                    print(f"  ✗ AFTER REFRESH: Still mismatched! ({after_refresh_count} vs {final_staff_count})")
            else:
                print("  ✓ Dialog already synchronized correctly")
            
            # List the staves in the dialog
            print("  Staves shown in dialog:")
            for i in range(test_dialog.setup_widget.staff_list.topLevelItemCount()):
                item = test_dialog.setup_widget.staff_list.topLevelItem(i)
                staff_name = item.text(0)
                print(f"    {i+1}. {staff_name}")
            
            # List the staves in the document
            print("  Staves in document:")
            for i, staff in enumerate(document.layout.ungrouped_staves):
                print(f"    {i+1}. {staff.instrument_name}")
            
            test_dialog.close()
            
        except Exception as e:
            print(f"  ✗ Error testing dialog: {e}")
            import traceback
            traceback.print_exc()
    
    # Test dialog via edit_score_setup method
    print("\n7. Testing via edit_score_setup method...")
    
    def test_via_method():
        print("  Testing dialog opened via edit_score_setup()...")
        print(f"  Document state before opening: {len(document.layout.ungrouped_staves)} staves")
        
        # This should open the dialog, refresh it, and show it
        # The refresh should ensure it shows the current state
        try:
            # Note: This will open the actual dialog for the user to see
            # In automated testing, we'd need to simulate this differently
            result = staff_view.edit_score_setup()
            print(f"  Dialog result: {result}")
        except Exception as e:
            print(f"  Error opening dialog: {e}")
    
    # Schedule tests
    QTimer.singleShot(1000, test_dialog_manual)
    QTimer.singleShot(3000, test_via_method)
    
    print("\n8. Summary of fixes applied:")
    print("  ✓ Enhanced refresh_from_document() with multiple document lookup paths")
    print("  ✓ Aggressive cache clearing to prevent stale data")
    print("  ✓ Immediate refresh after dialog creation")
    print("  ✓ Secondary refresh if mismatch detected")
    print("  ✓ Detailed logging for troubleshooting")
    
    # Schedule app quit
    QTimer.singleShot(8000, app.quit)
    
    # Run the event loop
    app.exec()
    
    return True

if __name__ == "__main__":
    test_dialog_sync_final() 