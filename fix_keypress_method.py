#!/usr/bin/env python3
"""
Fix the keyPressEvent method with correct indentation
"""

def fix_keypress_method():
    """Fix the keyPressEvent method"""
    
    # Read the current file
    with open('src/gui/music/staff_view.py', 'r') as f:
        lines = f.readlines()
    
    print("🔧 Fixing keyPressEvent method...")
    
    # Find the start and end of the keyPressEvent method
    start_index = None
    end_index = None
    
    for i, line in enumerate(lines):
        if 'def keyPressEvent(self, event):' in line:
            start_index = i
        elif start_index is not None and line.strip().startswith('def ') and 'keyPressEvent' not in line:
            end_index = i
            break
    
    if start_index is None:
        print("❌ Could not find keyPressEvent method")
        return False
    
    if end_index is None:
        # Look for the end by finding super().keyPressEvent(event)
        for i in range(start_index + 1, len(lines)):
            if 'super().keyPressEvent(event)' in lines[i]:
                end_index = i + 2  # Include the line after super() call
                break
        
        if end_index is None:
            end_index = len(lines)
    
    print(f"Found keyPressEvent method from line {start_index + 1} to {end_index}")
    
    # Create the clean keyPressEvent method
    clean_method = '''    def keyPressEvent(self, event):
        """Handle key press events"""
        print(f"KEYPRESS: Received key event: {event.key()}, focus: {self.hasFocus()}, keyboard grabbed: {getattr(self, '_keyboard_grabbed', False)}")
        
        # Handle both Delete and Backspace keys (Mac "delete" key is actually Backspace in Qt)
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Get all selected barlines
            selected_barlines = self.get_selected_barlines()
            print(f"KEYPRESS_DELETE: Found {len(selected_barlines)} selected barlines")
            
            if selected_barlines:
                # Save state for undo BEFORE deletion
                form_widget = self.get_form_widget()
                if form_widget and hasattr(form_widget, 'save_state'):
                    if len(selected_barlines) == 1:
                        form_widget.save_state(f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}")
                    else:
                        form_widget.save_state(f"Delete {len(selected_barlines)} barlines")
                
                # Remove each barline immediately
                successfully_deleted = 0
                for barline in selected_barlines:
                    # Check if barline can be removed
                    can_remove = True
                    if hasattr(self, 'measure_manager') and self.measure_manager:
                        can_remove = self.measure_manager.can_remove_barline(barline)
                        if not can_remove:
                            print(f"KEYPRESS_DELETE: Cannot remove barline at measure {getattr(barline, 'measure_number', 'unknown')} - it's the initial end bar")
                            continue
                    
                    # Deselect the barline before removal
                    if hasattr(barline, 'selected'):
                        barline.selected = False
                    
                    # Remove the barline
                    if self._remove_barline_direct(barline):
                        successfully_deleted += 1
                        # Emit removal signal
                        if isinstance(barline, MeasureObject):
                            self.barline_removed.emit(barline)
                        print(f"BARLINE_DELETE: Deleted barline at measure {getattr(barline, 'measure_number', 'unknown')}")
                    else:
                        print(f"BARLINE_DELETE: Failed to delete barline at measure {getattr(barline, 'measure_number', 'unknown')}")
                
                # Release keyboard grab since barlines are now deleted
                if hasattr(self, '_keyboard_grabbed') and self._keyboard_grabbed:
                    try:
                        self.releaseKeyboard()
                        self._keyboard_grabbed = False
                        print("KEYPRESS_DELETE: Released keyboard grab after deletion")
                    except Exception as e:
                        print(f"KEYPRESS_DELETE: Failed to release keyboard: {e}")
                        self._keyboard_grabbed = False
                
                # Update display
                self.update()
                
                print(f"BARLINE_DELETE: Successfully deleted {successfully_deleted} barline(s) out of {len(selected_barlines)} selected")
                
                # Accept the event to prevent further propagation
                event.accept()
                return
            else:
                print("BARLINE_DELETE: No barlines selected for deletion")
        
        # Call parent implementation for other keys
        super().keyPressEvent(event)

'''
    
    # Replace the problematic method with the clean version
    new_lines = lines[:start_index] + [clean_method] + lines[end_index:]
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed keyPressEvent method")
    return True

if __name__ == "__main__":
    try:
        if fix_keypress_method():
            print("✅ Successfully fixed keyPressEvent method!")
        else:
            print("❌ Failed to fix keyPressEvent method")
    except Exception as e:
        print(f"❌ Error fixing method: {e}")
        import traceback
        traceback.print_exc() 