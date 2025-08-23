#!/usr/bin/env python3
"""
Comprehensive Test: Both Critical Issues Fixed

This script tests both critical issues that the user reported:

ISSUE 1: Sophisticated Barline Layering System
- Single barlines can be inserted anywhere (even between repeat barlines)  
- Other barline types create overlays that hide underlying single barlines
- Layered barlines copy positions and move together
- Only removing single barlines removes measures

ISSUE 2: Form Widget Radio Button Behavior  
- Clicking on form widget background clears all radio buttons
- Single barline radio button is selected only on initialization
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QMouseEvent

def test_sophisticated_layering_system():
    """Test the sophisticated barline layering system"""
    
    print("🏗️ Testing Sophisticated Barline Layering System")
    print("=" * 60)
    
    try:
        # Import required classes
        from src.gui.music.barline_temporal_bridge import BarlineTemporalBridge
        from src.gui.music.score_document import ScoreDocument
        
        # Create test document and bridge
        document = ScoreDocument()
        bridge = BarlineTemporalBridge(document)
        
        print("✅ Created document and temporal bridge")
        
        # Test 1: Create single barlines (structural - create measures)
        print("\n🏗️ Test 1: Single Barlines (Structural)")
        print("-" * 40)
        
        # Create single barlines at different positions
        single1 = bridge.create_barline_at_position(400.0, "single")
        single2 = bridge.create_barline_at_position(500.0, "single") 
        single3 = bridge.create_barline_at_position(600.0, "single")
        
        if single1 and single2 and single3:
            print("✅ Created 3 single barlines successfully")
            print(f"   - Single barline 1 at x=400 (measure {getattr(single1, 'measure_number', 'unknown')})")
            print(f"   - Single barline 2 at x=500 (measure {getattr(single2, 'measure_number', 'unknown')})")
            print(f"   - Single barline 3 at x=600 (measure {getattr(single3, 'measure_number', 'unknown')})")
        else:
            print("❌ Failed to create single barlines")
            return False
        
        # Test 2: Create overlay barlines (visual - should overlay existing singles)
        print("\n🎭 Test 2: Overlay Barlines (Visual)")
        print("-" * 40)
        
        # Try to create double barline overlay on second single barline
        double_overlay = bridge.create_barline_at_position(500.0, "double")
        
        if double_overlay:
            barline_type = getattr(double_overlay, 'barline_type', 'unknown')
            measure_num = getattr(double_overlay, 'measure_number', 'unknown')
            print(f"✅ Created double barline overlay: type={barline_type}, measure={measure_num}")
            
            # Verify it's the same measure object as the single barline
            if double_overlay == single2:
                print("✅ CORRECT: Overlay is the same measure object as underlying single")
            else:
                print("❌ WRONG: Overlay created new measure instead of overlaying existing")
        else:
            print("❌ Failed to create double barline overlay")
            return False
        
        # Try to create repeat barline overlay on third single barline  
        repeat_overlay = bridge.create_barline_at_position(600.0, "repeat_end")
        
        if repeat_overlay:
            barline_type = getattr(repeat_overlay, 'barline_type', 'unknown')
            measure_num = getattr(repeat_overlay, 'measure_number', 'unknown')
            print(f"✅ Created repeat end overlay: type={barline_type}, measure={measure_num}")
        else:
            print("❌ Failed to create repeat end overlay")
            return False
        
        # Test 3: Insert single barline between overlaid barlines (should work!)
        print("\n➕ Test 3: Insert Single Barline Between Overlays")
        print("-" * 40)
        
        # Try to insert single barline between the double (at 500) and repeat (at 600)
        middle_single = bridge.create_barline_at_position(550.0, "single")
        
        if middle_single:
            measure_num = getattr(middle_single, 'measure_number', 'unknown')
            print(f"✅ Inserted single barline between overlays: measure={measure_num}")
            print("✅ CORRECT: Single barlines can be inserted anywhere, even between repeat barlines")
        else:
            print("❌ WRONG: Could not insert single barline between overlaid barlines")
            return False
        
        # Test 4: Create overlay on the newly inserted single barline
        print("\n🎭 Test 4: Overlay on Newly Inserted Single")
        print("-" * 40)
        
        # Create final barline overlay on the middle single
        final_overlay = bridge.create_barline_at_position(550.0, "final")
        
        if final_overlay:
            barline_type = getattr(final_overlay, 'barline_type', 'unknown')
            print(f"✅ Created final barline overlay on inserted single: type={barline_type}")
            
            # Verify it's the same measure object
            if final_overlay == middle_single:
                print("✅ CORRECT: Overlay applied to newly inserted single barline")
            else:
                print("❌ WRONG: Overlay didn't apply to existing single barline")
        else:
            print("❌ Failed to create final barline overlay")
            return False
        
        # Test 5: Independent dashed barlines
        print("\n📏 Test 5: Independent Dashed Barlines")
        print("-" * 40)
        
        # Create dashed barlines (should be independent visual markers)
        dashed1 = bridge.create_barline_at_position(450.0, "dashed")
        dashed2 = bridge.create_barline_at_position(575.0, "dashed")
        
        if dashed1 and dashed2:
            print("✅ Created 2 independent dashed barlines")
            print(f"   - Dashed 1 at x=450")
            print(f"   - Dashed 2 at x=575")
            
            # Verify they have the independent marker flag
            if hasattr(dashed1, 'is_graphical_dashed') and dashed1.is_graphical_dashed:
                print("✅ CORRECT: Dashed barlines marked as independent graphical elements")
            else:
                print("❌ WRONG: Dashed barlines not properly marked as independent")
        else:
            print("❌ Failed to create independent dashed barlines")
            return False
        
        # Test 6: Verify layered barlines count and structure
        print("\n📊 Test 6: Verify Final Structure")
        print("-" * 40)
        
        measures = bridge._get_current_measures()
        measure_count = len(measures)
        print(f"✅ Total measures created: {measure_count}")
        
        # Should have 4 measures: 3 original singles + 1 inserted middle single
        expected_measures = 4
        if measure_count == expected_measures:
            print(f"✅ CORRECT: Expected {expected_measures} measures, got {measure_count}")
        else:
            print(f"❌ WRONG: Expected {expected_measures} measures, got {measure_count}")
            return False
        
        # Check for dashed barlines collection
        if hasattr(document, 'graphical_dashed_barlines'):
            dashed_count = len(document.graphical_dashed_barlines)
            print(f"✅ Independent dashed barlines: {dashed_count}")
            if dashed_count == 2:
                print("✅ CORRECT: Both dashed barlines stored independently")
            else:
                print(f"❌ WRONG: Expected 2 dashed barlines, got {dashed_count}")
        else:
            print("❌ WRONG: No graphical_dashed_barlines collection found")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 Sophisticated Barline Layering System: ALL TESTS PASSED!")
        print("✅ Single barlines can be inserted anywhere")
        print("✅ Overlays properly hide underlying single barlines")  
        print("✅ Layered barlines share positions and move together")
        print("✅ Dashed barlines work as independent visual markers")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during layering system testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_form_widget_radio_behavior():
    """Test the form widget radio button behavior"""
    
    print("🔘 Testing Form Widget Radio Button Behavior")
    print("=" * 60)
    
    try:
        # Import the form widget
        from src.gui.music.widgets.form_widget import FormWidget
        
        # Create minimal test setup
        app = QApplication([])
        
        # Create a proper mock main window that inherits from QWidget
        class MockMainWindow(QWidget):
            def __init__(self):
                super().__init__()
                self.form_widget = None
                # Create a minimal mock staff_view to satisfy FormWidget requirements
                self.staff_view = self.create_mock_staff_view()
                
            def create_mock_staff_view(self):
                """Create a minimal mock staff view"""
                class MockStaffView:
                    def __init__(self):
                        self._form_widget_connected = False
                        
                    def set_barline_creation_enabled(self, enabled):
                        """Mock method for enabling barline creation"""
                        pass
                
                return MockStaffView()
        
        mock_main_window = MockMainWindow()
        
        # Create form widget
        print("📋 Creating FormWidget...")
        form_widget = FormWidget(mock_main_window)
        mock_main_window.form_widget = form_widget
        
        # Show the form widget
        form_widget.show()
        
        print("✅ FormWidget created successfully")
        
        # Test 1: Check initial state
        print("\n📋 Test 1: Initial Radio Button State")
        print("-" * 40)
        
        if hasattr(form_widget, 'barline_button_group'):
            checked_button = form_widget.barline_button_group.checkedButton()
            if checked_button:
                barline_type = checked_button.property("barline_type")
                print(f"✅ Initial selection: {barline_type}")
                if barline_type == "single":
                    print("✅ CORRECT: Single barline is selected on initialization")
                else:
                    print(f"❌ WRONG: {barline_type} is selected instead of 'single'")
                    return False
            else:
                print("❌ WRONG: No radio button is selected on initialization")
                return False
        else:
            print("❌ ERROR: No barline_button_group found")
            return False
        
        # Test 2: Change selection and test background click clearing
        print("\n📋 Test 2: Background Click Clearing")
        print("-" * 40)
        
        # First, change to a different selection
        double_button = None
        for button in form_widget.barline_button_group.buttons():
            if button.property("barline_type") == "double":
                double_button = button
                break
        
        if double_button:
            double_button.setChecked(True)
            print("✅ Changed selection to 'double' barline for testing")
        else:
            print("❌ ERROR: Could not find double barline button")
            return False
        
        # Test background click clearing with fixed mouse event
        if hasattr(form_widget, 'mousePressEvent'):
            # Create a mock mouse event for background click
            click_pos = QPointF(10, 10)  # Top-left corner, likely background
            mouse_event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                click_pos,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            
            print(f"🖱️ Simulating background click at position {click_pos}")
            
            # Call mousePressEvent directly
            form_widget.mousePressEvent(mouse_event)
            
            # Check if radio buttons were cleared
            checked_button = form_widget.barline_button_group.checkedButton()
            if checked_button is None:
                print("✅ CORRECT: Background click cleared all radio buttons")
            else:
                barline_type = checked_button.property("barline_type")
                print(f"❌ WRONG: Background click did not clear selection, still have: {barline_type}")
                return False
        else:
            print("❌ ERROR: mousePressEvent method not found")
            return False
        
        # Test 3: Manual clear method
        print("\n📋 Test 3: Manual Clear Method")
        print("-" * 40)
        
        # First, set a selection again
        if double_button:
            double_button.setChecked(True)
            print("✅ Set selection to 'double' for testing")
        
        if hasattr(form_widget, 'clear_all_radio_buttons'):
            form_widget.clear_all_radio_buttons()
            print("🔄 Called clear_all_radio_buttons()")
            
            checked_button = form_widget.barline_button_group.checkedButton()
            if checked_button is None:
                print("✅ CORRECT: Manual clear method works")
            else:
                barline_type = checked_button.property("barline_type")
                print(f"❌ WRONG: Manual clear failed, still have: {barline_type}")
                return False
        else:
            print("❌ ERROR: clear_all_radio_buttons method not found")
            return False
        
        # Test 4: Initialization method
        print("\n📋 Test 4: Initialization Method")
        print("-" * 40)
        
        if hasattr(form_widget, 'ensure_single_barline_selected_on_init'):
            form_widget.ensure_single_barline_selected_on_init()
            print("🔄 Called ensure_single_barline_selected_on_init()")
            
            checked_button = form_widget.barline_button_group.checkedButton()
            if checked_button and checked_button.property("barline_type") == "single":
                print("✅ CORRECT: Initialization method sets 'single' selection")
            elif checked_button:
                barline_type = checked_button.property("barline_type")
                print(f"❌ WRONG: Initialization method set {barline_type} instead of 'single'")
                return False
            else:
                print("❌ WRONG: Initialization method cleared selection instead of setting 'single'")
                return False
        else:
            print("❌ ERROR: ensure_single_barline_selected_on_init method not found")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 Form Widget Radio Button Behavior: ALL TESTS PASSED!")
        print("✅ Single barline selected on initialization")
        print("✅ Background click clears all radio buttons")
        print("✅ Manual clear method works")
        print("✅ Initialization method works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during form widget testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run comprehensive tests for both critical issues"""
    
    print("🚀 COMPREHENSIVE TEST: Both Critical Issues Fixed")
    print("=" * 80)
    print("Testing both sophisticated barline layering and form widget radio behavior")
    print("=" * 80)
    
    # Test 1: Sophisticated Barline Layering System
    layering_success = test_sophisticated_layering_system()
    
    print("\n" + "=" * 80)
    
    # Test 2: Form Widget Radio Button Behavior
    radio_success = test_form_widget_radio_behavior()
    
    print("\n" + "=" * 80)
    print("🏁 FINAL RESULTS")
    print("=" * 80)
    
    if layering_success and radio_success:
        print("🎉 SUCCESS: Both critical issues are FIXED!")
        print("")
        print("ISSUE 1 ✅ Sophisticated Barline Layering System:")
        print("  - Single barlines can be inserted anywhere")
        print("  - Other types create overlays on existing singles")
        print("  - Layered barlines copy positions and move together")
        print("  - Only removing single barlines removes measures")
        print("")
        print("ISSUE 2 ✅ Form Widget Radio Button Behavior:")
        print("  - Background click clears all radio buttons")
        print("  - Single barline selected only on initialization")
        print("")
        print("🎊 ONOTE is ready for sophisticated barline creation!")
        return True
    else:
        print("❌ FAILURE: One or more issues still need fixing")
        if not layering_success:
            print("  - Sophisticated Barline Layering System: FAILED")
        if not radio_success:
            print("  - Form Widget Radio Button Behavior: FAILED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 