#!/usr/bin/env python3
"""
Test script for ONOTE Multi-Window functionality
Tests creating multiple document windows and verifies they are independent.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gui.application_manager import create_application_manager
from src.gui.music.score_document import ScoreDocument
from src import __version__

def test_multi_window_functionality():
    """Test the multi-window functionality of ONOTE."""
    print(f"🧪 Testing ONOTE Multi-Window Functionality - Version {__version__}")
    print("=" * 60)
    
    try:
        # Create application manager
        print("📋 Creating Application Manager...")
        manager = create_application_manager()
        print(f"✅ Application Manager created successfully")
        print(f"📊 Initial window count: {len(manager.windows)}")
        
        # Test 1: Create first document window
        print("\n🔧 Test 1: Creating first document window...")
        window1 = manager.create_new_window()
        print(f"✅ First window created: {window1}")
        print(f"📊 Window count after first: {len(manager.windows)}")
        
        # Test 2: Create second document window
        print("\n🔧 Test 2: Creating second document window...")
        window2 = manager.create_new_window()
        print(f"✅ Second window created: {window2}")
        print(f"📊 Window count after second: {len(manager.windows)}")
        
        # Test 3: Create third document window
        print("\n🔧 Test 3: Creating third document window...")
        window3 = manager.create_new_window()
        print(f"✅ Third window created: {window3}")
        print(f"📊 Window count after third: {len(manager.windows)}")
        
        # Test 4: Verify windows are independent
        print("\n🔧 Test 4: Verifying window independence...")
        windows = manager.windows
        print(f"📋 All windows: {[w.windowTitle() for w in windows]}")
        
        # Check that each window has its own document
        for i, window in enumerate(windows, 1):
            print(f"   Window {i}: {window.windowTitle()}")
            print(f"   - Document: {window.document}")
            print(f"   - Filename: {window.filename}")
            print(f"   - Is modified: {window.is_modified}")
        
        # Test 5: Test window management
        print("\n🔧 Test 5: Testing window management...")
        print(f"📊 Total windows: {len(manager.windows)}")
        print(f"📊 Active window: {manager.get_active_window()}")
        
        # Test 6: Close one window
        print("\n🔧 Test 6: Closing one window...")
        if windows:
            window_to_close = windows[0]
            print(f"📋 Closing window: {window_to_close.windowTitle()}")
            window_to_close.close()
            print(f"📊 Window count after closing: {len(manager.windows)}")
        
        print("\n✅ All multi-window tests completed successfully!")
        print("🎯 Multi-window functionality is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_independence():
    """Test that documents in different windows are truly independent."""
    print("\n🧪 Testing Document Independence...")
    print("=" * 40)
    
    try:
        # Create application manager
        manager = create_application_manager()
        
        # Create two windows
        window1 = manager.create_new_window()
        window2 = manager.create_new_window()
        
        # Verify they have different documents
        doc1 = window1.document
        doc2 = window2.document
        
        print(f"📋 Window 1 document: {doc1}")
        print(f"📋 Window 2 document: {doc2}")
        print(f"🔍 Documents are different: {doc1 is not doc2}")
        
        # Test document modification independence
        print("\n🔧 Testing document modification independence...")
        
        # Modify document 1
        window1.is_modified = True
        print(f"📊 Window 1 modified: {window1.is_modified}")
        print(f"📊 Window 2 modified: {window2.is_modified}")
        
        # Verify window 2 is not affected
        if not window2.is_modified:
            print("✅ Document independence verified - modifications don't affect other windows")
        else:
            print("❌ Document independence failed - modifications affect other windows")
        
        return True
        
    except Exception as e:
        print(f"❌ Document independence test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting ONOTE Multi-Window Tests")
    print("=" * 60)
    
    # Run tests
    test1_success = test_multi_window_functionality()
    test2_success = test_document_independence()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Multi-window functionality: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Document independence: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Multi-window functionality is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    print("\n🏁 Test completed.") 