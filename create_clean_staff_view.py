#!/usr/bin/env python3
"""
Create a clean working version of the problematic mousePressEvent method
"""

def create_clean_mouse_press_event():
    """Create a clean working mousePressEvent method"""
    
    # Read the current file
    with open('src/gui/music/staff_view.py', 'r') as f:
        lines = f.readlines()
    
    print("🔧 Creating clean mousePressEvent method...")
    
    # Find the start and end of the mousePressEvent method
    start_index = None
    end_index = None
    
    for i, line in enumerate(lines):
        if 'def mousePressEvent(self, event):' in line:
            start_index = i
        elif start_index is not None and line.strip().startswith('def ') and 'mousePressEvent' not in line:
            end_index = i
            break
    
    if start_index is None:
        print("❌ Could not find mousePressEvent method")
        return False
    
    if end_index is None:
        # Look for the end by finding super().mousePressEvent(event)
        for i in range(start_index + 1, len(lines)):
            if 'super().mousePressEvent(event)' in lines[i]:
                end_index = i + 2  # Include the line after super() call
                break
        
        if end_index is None:
            end_index = len(lines)
    
    print(f"Found mousePressEvent method from line {start_index + 1} to {end_index}")
    
    # Create the clean mousePressEvent method
    clean_method = '''    def mousePressEvent(self, event):
        """Handle mouse press events for barline creation and selection"""
        # CRITICAL: Ensure this widget has focus to receive key events
        self.setFocus()
        
        # Check for shift key modifier for multi-selection - define at top level
        shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        
        if event.button() == Qt.MouseButton.LeftButton:
            click_pos = event.position().toPoint()
            
            # Check if we're in a valid area for barline operations
            if self.is_position_valid_for_barline(click_pos.x(), click_pos.y()):
                # Try to find existing barline first
                existing_barline = self.find_barline_at_position(click_pos.x(), click_pos.y())
                
                if existing_barline:
                    # Select the existing barline
                    if shift_pressed:
                        # Shift-click: toggle selection of this barline (multi-select)
                        if hasattr(existing_barline, 'selected') and existing_barline.selected:
                            existing_barline.selected = False
                            print(f"SHIFT_CLICK: Deselected barline at measure {getattr(existing_barline, 'measure_number', 'unknown')}")
                        else:
                            existing_barline.selected = True
                            print(f"SHIFT_CLICK: Selected barline at measure {getattr(existing_barline, 'measure_number', 'unknown')}")
                        
                        # CRITICAL: Grab keyboard focus to ensure delete key works
                        try:
                            self.grabKeyboard()
                            self._keyboard_grabbed = True
                            print(f"SHIFT_CLICK: Added barline at measure {getattr(existing_barline, 'measure_number', 'unknown')} to selection, keyboard grabbed")
                        except Exception as e:
                            print(f"SHIFT_CLICK: Failed to grab keyboard: {e}")
                            self._keyboard_grabbed = False
                        
                        # Only emit signal for actual MeasureObjects, not graphical dashed barlines
                        if isinstance(existing_barline, MeasureObject):
                            # Emit selection signal for form widget
                            self.barline_selected.emit(existing_barline)
                        
                        # Update display to show selection changes
                        self.update()
                    else:
                        # Normal click: select only this barline (single select)
                        self.select_barline(existing_barline)
                else:
                    # No existing barline found
                    if not shift_pressed:
                        # Normal click: deselect all barlines first
                        self.deselect_all_barlines()
                    
                    # CRITICAL FIX: Only create barlines when form widget is active
                    # This prevents automatic barline creation on regular clicks that causes undo reversion
                    if not shift_pressed and self.is_form_widget_active():
                        new_barline = self.create_barline_at_position(click_pos.x(), click_pos.y())
                        if new_barline:
                            # Only emit signal for actual MeasureObjects, not graphical dashed barlines
                            if isinstance(new_barline, MeasureObject):
                                # Emit signal for form widget (if available)
                                self.barline_created.emit(new_barline)
                            # Update display
                            self.update()
                            print(f"BARLINE_CREATE: Created barline at x={click_pos.x()}")
                        else:
                            print(f"BARLINE_CREATE: Failed to create barline at x={click_pos.x()}")
                    elif not shift_pressed:
                        print(f"CLICK: Form widget not active, not creating barline at x={click_pos.x()}")
            else:
                # Click outside valid area
                if not shift_pressed:
                    # Normal click outside: deselect all barlines
                    self.deselect_all_barlines()
                # Shift-click outside: do nothing (preserve current selection)
        
        super().mousePressEvent(event)

'''
    
    # Replace the problematic method with the clean version
    new_lines = lines[:start_index] + [clean_method] + lines[end_index:]
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Created clean mousePressEvent method")
    return True

if __name__ == "__main__":
    try:
        if create_clean_mouse_press_event():
            print("✅ Successfully created clean mousePressEvent method!")
        else:
            print("❌ Failed to create clean mousePressEvent method")
    except Exception as e:
        print(f"❌ Error creating clean method: {e}")
        import traceback
        traceback.print_exc() 