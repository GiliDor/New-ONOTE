#!/usr/bin/env python3
"""
Fix the select_barline method with correct indentation
"""

def fix_select_barline_method():
    """Fix the select_barline method"""
    
    # Read the current file
    with open('src/gui/music/staff_view.py', 'r') as f:
        lines = f.readlines()
    
    print("🔧 Fixing select_barline method...")
    
    # Find the start and end of the select_barline method
    start_index = None
    end_index = None
    
    for i, line in enumerate(lines):
        if 'def select_barline(self, barline):' in line:
            start_index = i
        elif start_index is not None and line.strip().startswith('def ') and 'select_barline' not in line:
            end_index = i
            break
    
    if start_index is None:
        print("❌ Could not find select_barline method")
        return False
    
    if end_index is None:
        end_index = len(lines)
    
    print(f"Found select_barline method from line {start_index + 1} to {end_index}")
    
    # Create the clean select_barline method
    clean_method = '''    def select_barline(self, barline):
        """Select a barline and highlight it in orange"""
        if not barline:
            return
                
        # Deselect all other barlines first
        self.deselect_all_barlines()
        
        # Select the clicked barline
        barline.selected = True
        
        # CRITICAL: Grab keyboard focus to ensure delete key works
        # This ensures delete key works even when cursor moves away from barlines
        try:
            self.grabKeyboard()
            self._keyboard_grabbed = True
            print("BARLINE_SELECT: Grabbed keyboard focus")
        except Exception as e:
            print(f"BARLINE_SELECT: Failed to grab keyboard: {e}")
            self._keyboard_grabbed = False
        
        # Set focus to this widget as primary handler
        self.setFocus()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Only emit signal for actual MeasureObjects, not graphical dashed barlines
        if isinstance(barline, MeasureObject):
            # Emit selection signal for form widget
            self.barline_selected.emit(barline)
        
        # Update display to show orange highlighting
        self.update()
        
        print(f"BARLINE_SELECT: Selected barline at measure {getattr(barline, 'measure_number', 'unknown')}, global filter installed: {self._keyboard_grabbed}")

'''
    
    # Replace the problematic method with the clean version
    new_lines = lines[:start_index] + [clean_method] + lines[end_index:]
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed select_barline method")
    return True

if __name__ == "__main__":
    try:
        if fix_select_barline_method():
            print("✅ Successfully fixed select_barline method!")
        else:
            print("❌ Failed to fix select_barline method")
    except Exception as e:
        print(f"❌ Error fixing method: {e}")
        import traceback
        traceback.print_exc() 