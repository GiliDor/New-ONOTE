#!/usr/bin/env python3
"""
Patch to add element selection to StaffView mousePressEvent
This will be applied manually to avoid the multiple occurrence issue
"""

ELEMENT_SELECTION_CODE = '''
        # ELEMENT SELECTION: Check for score elements first (works even when Form is closed)
        if event.button() == Qt.MouseButton.LeftButton:
            click_pos = event.position().toPoint()
            shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            
            # Try to select score elements (clefs, key signatures, etc.)
            selected_element = self.find_score_element_at_position(click_pos.x(), click_pos.y())
            if selected_element:
                if shift_pressed:
                    # Shift-click: toggle selection
                    if hasattr(selected_element, 'selected'):
                        selected_element.selected = not getattr(selected_element, 'selected', False)
                        print(f"SHIFT_CLICK: {'Selected' if selected_element.selected else 'Deselected'} {getattr(selected_element, 'element_type', 'element')}")
                else:
                    # Normal click: select only this element
                    self.deselect_all_elements()
                    if not hasattr(selected_element, 'selected'):
                        selected_element.selected = False
                    selected_element.selected = True
                    print(f"ELEMENT_SELECT: Selected {getattr(selected_element, 'element_type', type(selected_element).__name__)}")
                
                # Update display
                self.update()
                return
        
'''

print("Element selection code ready to be added to mousePressEvent")
print("Add this code after 'self.setFocus()' and before 'Track gesture start'")
