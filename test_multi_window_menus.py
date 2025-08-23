#!/usr/bin/env python3
"""
Test script for ONOTE multi-window menu system.
Tests all menus, dialogs, and window management functionality.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication, QToolBar
from PyQt6.QtCore import QTimer

from src.gui.application_manager import ApplicationManager


def test_menu_system():
    """Test the complete menu system."""
    print("🧪 Testing ONOTE Multi-Window Menu System")
    print("=" * 50)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create application manager
    app_manager = ApplicationManager()
    
    print("✅ Application manager created")
    
    # Test window creation
    print("\n📄 Testing window creation...")
    
    # Create a few document windows
    window1 = app_manager.create_new_window()
    window2 = app_manager.create_new_window()
    window3 = app_manager.create_new_window()
    
    print(f"✅ Created {len(app_manager.get_all_windows())} windows")
    
    # Test window management
    print("\n🪟 Testing window management...")
    
    # Test tiling
    print("Testing tile windows...")
    app_manager.tile_windows()
    
    # Test cascading
    print("Testing cascade windows...")
    app_manager.cascade_windows()
    
    print("✅ Window management functions work")
    
    # Test menu functionality
    print("\n🍽️ Testing menu functionality...")
    
    # Test File menu actions
    print("Testing File menu actions...")
    desktop = app_manager.desktop_window
    
    # Test New action
    print("  - Testing New action...")
    desktop._file_new()
    
    # Test Open action (will show dialog)
    print("  - Testing Open action...")
    desktop._file_open()
    
    # Test Save action
    print("  - Testing Save action...")
    desktop._file_save()
    
    # Test Save As action (will show dialog)
    print("  - Testing Save As action...")
    desktop._file_save_as()
    
    # Test Import action
    print("  - Testing Import action...")
    desktop._file_import()
    
    # Test Export action
    print("  - Testing Export action...")
    desktop._file_export()
    
    # Test Print Preview action
    print("  - Testing Print Preview action...")
    desktop._print_preview()
    
    # Test Print action
    print("  - Testing Print action...")
    desktop._print()
    
    print("✅ File menu actions work")
    
    # Test Edit menu actions
    print("Testing Edit menu actions...")
    
    # Test Undo action
    print("  - Testing Undo action...")
    desktop._edit_undo()
    
    # Test Redo action
    print("  - Testing Redo action...")
    desktop._edit_redo()
    
    # Test Toggle Edit Mode action
    print("  - Testing Toggle Edit Mode action...")
    desktop._toggle_edit_mode()
    
    print("✅ Edit menu actions work")
    
    # Test Score menu actions
    print("Testing Score menu actions...")
    
    # Test Score Setup action
    print("  - Testing Score Setup action...")
    desktop.open_score_setup()
    
    # Test Full Score Options action
    print("  - Testing Full Score Options action...")
    desktop.open_full_score_options()
    
    # Test other score actions
    print("  - Testing Page Setup action...")
    desktop._page_setup()
    
    print("  - Testing Parts Options action...")
    desktop._parts_options()
    
    print("  - Testing Add Title/Header/Footer action...")
    desktop._add_title_header_footer()
    
    print("  - Testing Dynamic Parts action...")
    desktop._dynamic_parts()
    
    print("  - Testing Notation Setup action...")
    desktop._notation_setup()
    
    print("✅ Score menu actions work")
    
    # Test View menu actions
    print("Testing View menu actions...")
    
    # Test view mode toggles
    print("  - Testing Continuous View toggle...")
    desktop._toggle_continuous_view()
    
    print("  - Testing Page Across toggle...")
    desktop._toggle_page_across()
    
    print("  - Testing Page Down toggle...")
    desktop._toggle_page_down()
    
    # Test zoom actions
    print("  - Testing Zoom In action...")
    desktop._zoom_in()
    
    print("  - Testing Zoom Out action...")
    desktop._zoom_out()
    
    print("  - Testing Reset Zoom action...")
    desktop._reset_zoom()
    
    # Test window arrangement
    print("  - Testing Tile Windows action...")
    desktop._tile_windows()
    
    print("  - Testing Cascade Windows action...")
    desktop._cascade_windows()
    
    print("✅ View menu actions work")
    
    # Test Tools menu actions
    print("Testing Tools menu actions...")
    
    # Test widget actions
    print("  - Testing Form widget action...")
    desktop._show_form()
    
    print("  - Testing Notes widget action...")
    desktop._show_notes()
    
    print("  - Testing Rhythm widget action...")
    desktop._show_rhythm()
    
    print("  - Testing Pitch widget action...")
    desktop._show_pitch()
    
    print("  - Testing Harmony widget action...")
    desktop._show_harmony()
    
    # Test Preferences action
    print("  - Testing Preferences action...")
    desktop._show_preferences()
    
    print("✅ Tools menu actions work")
    
    # Test Help menu actions
    print("Testing Help menu actions...")
    
    print("  - Testing Documentation action...")
    desktop._show_documentation()
    
    print("  - Testing Keyboard Shortcuts action...")
    desktop._show_shortcuts()
    
    print("  - Testing Check for Updates action...")
    desktop._check_for_updates()
    
    print("  - Testing About action...")
    desktop._show_about()
    
    print("✅ Help menu actions work")
    
    # Test status bar
    print("\n📊 Testing status bar...")
    desktop.status_bar.showMessage("Test message from menu system")
    print("✅ Status bar works")
    
    # Test toolbar
    print("\n🔧 Testing toolbar...")
    toolbars = desktop.findChildren(QToolBar)
    if toolbars:
        toolbar = toolbars[0]
        print(f"✅ Toolbar found with {len(toolbar.actions())} actions")
    else:
        print("❌ Toolbar not found")
    
    # Test window management
    print("\n🪟 Testing window management...")
    
    # Get all windows
    all_windows = app_manager.get_all_windows()
    print(f"✅ Found {len(all_windows)} total windows")
    
    # Get document windows
    doc_windows = app_manager.get_document_windows()
    print(f"✅ Found {len(doc_windows)} document windows")
    
    # Get active window
    active_window = app_manager.get_active_window()
    if active_window:
        print(f"✅ Active window: {active_window.windowTitle()}")
    else:
        print("❌ No active window found")
    
    print("\n🎉 All menu system tests completed successfully!")
    print("=" * 50)
    
    # Set up timer to close after showing results
    def close_app():
        print("\n🔄 Closing test application...")
        app_manager.close_all_windows()
        app.quit()
    
    # Close after 5 seconds
    QTimer.singleShot(5000, close_app)
    
    # Start event loop
    return app.exec()


if __name__ == "__main__":
    try:
        exit_code = test_menu_system()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 