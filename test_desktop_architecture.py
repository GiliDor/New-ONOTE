#!/usr/bin/env python3
"""
Test script to verify the new page-based desktop architecture.
Tests the DesktopWindow and MusicPage functionality.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.application_manager import ApplicationManager


def test_desktop_architecture():
    """Test the new page-based desktop architecture."""
    print("🧪 Testing ONOTE Page-Based Desktop Architecture")
    print("=" * 60)
    
    # Create application manager
    manager = ApplicationManager(QApplication.instance() or QApplication(sys.argv))
    
    # Test 1: Create initial desktop window
    print("📄 Test 1: Creating initial desktop window...")
    window1 = manager.create_new_window()
    assert window1 is not None, "Failed to create initial desktop window"
    print("✅ Initial desktop window created successfully")
    
    # Test 2: Verify window properties
    print("📄 Test 2: Verifying window properties...")
    assert window1.music_page is not None, "Music page not created"
    assert window1.graphics_view is not None, "Graphics view not created"
    assert window1.graphics_scene is not None, "Graphics scene not created"
    assert window1.form_widget is not None, "Form widget not created"
    print("✅ Window properties verified")
    
    # Test 3: Test page mode switching
    print("📄 Test 3: Testing page mode switching...")
    window1.page_mode_changed.emit("setup")
    assert window1.music_page.mode == "setup", "Page mode not switched to setup"
    print("✅ Page mode switched to setup")
    
    window1.page_mode_changed.emit("edit")
    assert window1.music_page.mode == "edit", "Page mode not switched to edit"
    print("✅ Page mode switched to edit")
    
    # Test 4: Test zoom functionality
    print("📄 Test 4: Testing zoom functionality...")
    original_zoom = window1.page_zoom_level
    window1.zoom_in()
    assert window1.page_zoom_level > original_zoom, "Zoom in failed"
    print("✅ Zoom in working")
    
    zoom_after_in = window1.page_zoom_level
    window1.zoom_out()
    assert window1.page_zoom_level < zoom_after_in, "Zoom out failed"
    print("✅ Zoom out working")
    
    # Test 5: Create second window
    print("📄 Test 5: Creating second desktop window...")
    window2 = manager.create_new_window()
    assert window2 is not None, "Failed to create second desktop window"
    assert len(manager.windows) == 2, "Window count incorrect"
    print("✅ Second desktop window created successfully")
    
    # Test 6: Verify window independence
    print("📄 Test 6: Verifying window independence...")
    assert window1 != window2, "Windows should be different instances"
    assert window1.document != window2.document, "Documents should be different instances"
    print("✅ Window independence verified")
    
    # Test 7: Test window management
    print("📄 Test 7: Testing window management...")
    active_window = manager.get_active_window()
    assert active_window == window2, "Active window should be the last created"
    print("✅ Window management working")
    
    # Test 8: Test window closing
    print("📄 Test 8: Testing window closing...")
    initial_count = len(manager.windows)
    window2.close()
    time.sleep(0.1)  # Give time for close event to process
    assert len(manager.windows) == initial_count - 1, "Window not properly closed"
    print("✅ Window closing working")
    
    print("\n🎉 All desktop architecture tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_desktop_architecture()
        if success:
            print("\n✅ Desktop architecture test completed successfully!")
        else:
            print("\n❌ Desktop architecture test failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        sys.exit(1) 