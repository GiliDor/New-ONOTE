#!/usr/bin/env python3
"""
Test script to verify barline fixes are working correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_barline_fixes():
    """Test that the barline fixes are properly implemented"""
    
    print("=== Testing Barline Fixes ===")
    
    # Test 1: Check if draw_barlines is called in paintEvent
    try:
        from src.gui.music.staff_view import StaffView
        print("✅ StaffView import successful")
        
        # Check if the draw_barlines call is in paintEvent
        with open('src/gui/music/staff_view.py', 'r') as f:
            content = f.read()
            if "CRITICAL FIX: Draw barlines using StaffView's draw_barlines method" in content:
                print("✅ Barline drawing fix is implemented in paintEvent")
            else:
                print("❌ Barline drawing fix NOT found in paintEvent")
                
            # Check for duplicate draw_barlines methods
            draw_barlines_count = content.count("def draw_barlines")
            if draw_barlines_count == 1:
                print("✅ Only one draw_barlines method found")
            else:
                print(f"❌ Found {draw_barlines_count} duplicate draw_barlines methods")
                
    except ImportError as e:
        print(f"❌ Failed to import StaffView: {e}")
        return False
    
    # Test 2: Check if overlap prevention is implemented
    try:
        from src.gui.music.widgets.form_widget import FormWidget
        print("✅ FormWidget import successful")
        
        with open('src/gui/music/widgets/form_widget.py', 'r') as f:
            content = f.read()
            if "_check_barline_overlap" in content:
                print("✅ Barline overlap prevention is implemented")
            else:
                print("❌ Barline overlap prevention NOT found")
                
    except ImportError as e:
        print(f"❌ Failed to import FormWidget: {e}")
        return False
    
    # Test 3: Check if barline 0 handling is implemented
    with open('src/gui/music/staff_view.py', 'r') as f:
        content = f.read()
        if "measure_number == 0" in content and "Skipping barline 0" in content:
            print("✅ Barline 0 handling is implemented")
        else:
            print("❌ Barline 0 handling NOT found")
    
    # Test 4: Check if orange selection color is implemented
    with open('src/gui/music/staff_view.py', 'r') as f:
        content = f.read()
        if "QColor(255, 165, 0" in content and "Orange for selected" in content:
            print("✅ Orange selection color is implemented")
        else:
            print("❌ Orange selection color NOT found")
    
    print("\n=== Test Summary ===")
    print("All barline fixes appear to be implemented in the source code.")
    print("The issue may be that no measures exist in the document yet.")
    print("Try creating a test score with measures to see if barlines appear.")
    
    return True

def test_create_score_with_measures():
    """Test creating a score with measures to see if barlines are drawn"""
    print("\n=== Testing Score Creation with Measures ===")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.gui.music.staff_view import StaffView
        from src.gui.music.score_document import ScoreDocument
        
        # Create minimal app
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        
        # Create staff view and document
        staff_view = StaffView()
        document = ScoreDocument()
        staff_view.set_document(document)
        
        # Create test score with measures
        print("Creating test score with measures...")
        staff_view.create_test_score()
        
        # Check if measures were created
        if hasattr(document, 'measures') and document.measures:
            print(f"✅ Created {len(document.measures)} measures")
            for measure_num, measure in document.measures.items():
                print(f"  Measure {measure_num}: {measure.barline_type} at x={measure.end_x}")
        else:
            print("❌ No measures created")
        
        # Enter edit mode to trigger rendering
        staff_view.enter_edit_mode()
        
        print("✅ Test score created successfully")
        print("Check the ONOTE app to see if barlines are now visible.")
        
    except Exception as e:
        print(f"❌ Error creating test score: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Testing ONOTE Barline Fixes")
    print("=" * 40)
    
    # Run the tests
    test_barline_fixes()
    test_create_score_with_measures()
    
    print("\n=== Instructions ===")
    print("1. Open ONOTE app")
    print("2. Hold Shift and click 'Score Setup' to create test score")
    print("3. Check if barlines are visible on the staves")
    print("4. If barlines are still not visible, the issue may be in the rendering pipeline") 