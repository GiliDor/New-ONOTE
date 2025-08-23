#!/usr/bin/env python3
"""
Comprehensive test script to verify undo/redo synchronization fixes.

This script tests the specific issues reported:
1. First undo showing blank page (should now force proper refresh)
2. Setup dialog not reflecting undone state (should now sync properly)
3. UI synchronization between document state and dialog state
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.music.main_window import MainWindow
from src.notation.model.staves import SingleStaff

def test_comprehensive_undo_sync():
    """Test the comprehensive undo/redo synchronization fixes"""
    
    print("=== Comprehensive Undo/Redo Synchronization Test ===")
    print()
    
    app = QApplication(sys.argv)
    
    # Create main window and document
    print("1. Creating main window and document...")
    main_window = MainWindow()
    main_window.show()
    
    # Create initial document with multiple staves
    print("2. Setting up document with multiple staves...")
    
    if hasattr(main_window, 'staff_view') and main_window.staff_view:
        document = main_window.staff_view.document
        
        # Add multiple staves to test undo behavior
        staff1 = SingleStaff('violin', 'Violin I')
        staff2 = SingleStaff('violin2', 'Violin II') 
        staff3 = SingleStaff('viola', 'Viola')
        staff4 = SingleStaff('cello', 'Cello')
        
        # Add staves to document layout
        if hasattr(document, 'layout'):
            document.layout.ungrouped_staves.extend([staff1, staff2, staff3, staff4])
            print(f"   Added {len(document.layout.ungrouped_staves)} staves to document")
        
        # Force UI update
        main_window.staff_view.update()
        main_window.staff_view.repaint()
        
    print("3. Testing undo/redo synchronization...")
    
    def test_undo_operations():
        """Test multiple undo operations"""
        print("\n--- Testing Undo Operations ---")
        
        # Perform multiple undos
        for i in range(4):
            print(f"\nUndo #{i+1}:")
            main_window.undo()
            
            # Check document state
            if hasattr(main_window, 'staff_view') and main_window.staff_view:
                doc = main_window.staff_view.document
                if hasattr(doc, 'layout'):
                    staff_count = len(doc.layout.ungrouped_staves)
                    section_count = len(doc.layout.sections) if hasattr(doc.layout, 'sections') else 0
                    print(f"   Document now has {staff_count} ungrouped staves, {section_count} sections")
            
            # Short delay to let UI update
            app.processEvents()
            
        print("\n--- Testing Setup Dialog Sync ---")
        
        # Open setup dialog to test sync
        print("Opening setup dialog to check sync...")
        main_window.show_score_setup()
        
        # Check if setup widget reflects current document state
        if MainWindow._score_setup_widget:
            staff_list_count = MainWindow._score_setup_widget.staff_list.topLevelItemCount()
            print(f"Setup dialog shows {staff_list_count} staves")
            
            # Force refresh and check again
            MainWindow._score_setup_widget.refresh_from_document()
            updated_count = MainWindow._score_setup_widget.staff_list.topLevelItemCount()
            print(f"After forced refresh: {updated_count} staves")
        
    def test_redo_operations():
        """Test redo operations"""
        print("\n--- Testing Redo Operations ---")
        
        # Perform multiple redos
        for i in range(2):
            print(f"\nRedo #{i+1}:")
            main_window.redo()
            
            # Check document state
            if hasattr(main_window, 'staff_view') and main_window.staff_view:
                doc = main_window.staff_view.document
                if hasattr(doc, 'layout'):
                    staff_count = len(doc.layout.ungrouped_staves)
                    section_count = len(doc.layout.sections) if hasattr(doc.layout, 'sections') else 0
                    print(f"   Document now has {staff_count} ungrouped staves, {section_count} sections")
            
            # Short delay to let UI update
            app.processEvents()
        
        # Check setup dialog sync after redo
        if MainWindow._score_setup_widget:
            staff_list_count = MainWindow._score_setup_widget.staff_list.topLevelItemCount()
            print(f"Setup dialog shows {staff_list_count} staves after redo")
    
    # Schedule tests to run after UI is ready
    QTimer.singleShot(500, test_undo_operations)
    QTimer.singleShot(3000, test_redo_operations)
    QTimer.singleShot(5000, app.quit)
    
    print("4. Starting application and running tests...")
    print("   (Tests will run automatically)")
    
    # Run the application
    app.exec()
    
    print("\n=== Test Complete ===")
    print("Check the output above to verify:")
    print("1. Undo operations work correctly (no blank pages)")
    print("2. Setup dialog syncs with document state")
    print("3. Redo operations work correctly")
    print("4. UI consistently reflects document state")

if __name__ == '__main__':
    test_comprehensive_undo_sync() 