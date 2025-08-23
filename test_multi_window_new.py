#!/usr/bin/env python3
"""
Test script to verify multi-window ONOTE functionality.
Tests that "New" action creates a new window, not just a new document.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.gui.application_manager import ApplicationManager


def test_multi_window_new():
    """Test that New action creates a new window."""
    print("🧪 Testing multi-window ONOTE - New action")
    
    # Create application manager
    manager = ApplicationManager(QApplication.instance() or QApplication(sys.argv))
    
    # Create initial window
    window1 = manager.create_new_window()
    print(f"✅ Created initial window: {window1}")
    
    # Wait a moment
    time.sleep(1)
    
    # Test New action - should create a new window
    print("🔄 Testing New action...")
    manager.new_document()
    
    # Wait for window creation
    time.sleep(1)
    
    # Check window count
    window_count = manager.get_window_count()
    print(f"📊 Window count after New action: {window_count}")
    
    if window_count == 2:
        print("✅ SUCCESS: New action created a new window!")
        
        # Get the new window
        windows = manager.get_windows()
        window2 = windows[-1] if len(windows) > 1 else None
        
        if window2 and window2 != window1:
            print(f"✅ SUCCESS: New window is different from original: {window2}")
        else:
            print("❌ FAILED: New window is same as original")
    else:
        print(f"❌ FAILED: Expected 2 windows, got {window_count}")
    
    # Clean up
    print("🧹 Cleaning up...")
    manager.close_all_windows()
    
    print("✅ Multi-window New action test completed!")


if __name__ == "__main__":
    test_multi_window_new() 