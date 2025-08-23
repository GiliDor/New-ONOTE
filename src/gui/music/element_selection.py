"""
Element Selection System for ONOTE Score View

This module handles the selection of musical elements in the score view,
including clefs, key signatures, time signatures, staff names, section names,
barlines, and other score elements. It provides visual feedback and enables
property editing through the notation setup preferences.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QFont
from PyQt6.QtWidgets import QApplication
from typing import Dict, List, Optional, Tuple, Any
import math


class SelectableElement:
    """Represents a selectable musical element in the score"""
    
    def __init__(self, element_type: str, element_id: str, bounds: QRectF, 
                 staff_ref=None, properties: Dict[str, Any] = None):
        self.element_type = element_type  # 'clef', 'key_signature', 'time_signature', 'staff_name', etc.
        self.element_id = element_id      # Unique identifier
        self.bounds = bounds              # QRectF defining the clickable area
        self.staff_ref = staff_ref        # Reference to the staff object
        self.properties = properties or {}  # Element-specific properties
        self.is_selected = False
        self.hover_color = QColor(100, 150, 255, 100)  # Light blue
        self.selection_color = QColor(50, 100, 200, 150)  # Darker blue
        
    def contains_point(self, point: QPointF) -> bool:
        """Check if a point is within this element's bounds"""
        return self.bounds.contains(point)
        
    def get_center(self) -> QPointF:
        """Get the center point of this element"""
        return self.bounds.center()
        
    def render_selection_highlight(self, painter: QPainter):
        """Render the selection highlight for this element"""
        if self.is_selected:
            painter.save()
            
            # Draw selection rectangle with rounded corners
            pen = QPen(self.selection_color.darker(150), 2)
            brush = QBrush(self.selection_color)
            painter.setPen(pen)
            painter.setBrush(brush)
            
            # Expand bounds slightly for better visual feedback
            expanded_bounds = self.bounds.adjusted(-3, -3, 3, 3)
            painter.drawRoundedRect(expanded_bounds, 3, 3)
            
            painter.restore()


class ScoreElementSelection(QObject):
    """
    Manages selection of musical elements in the score view.
    
    Handles multiple selection types:
    - Single element selection
    - Multiple element selection (Ctrl+click)
    - Range selection (Shift+click for sequential elements)
    - Selection by type (all clefs, all key signatures, etc.)
    """
    
    # Signals
    selection_changed = pyqtSignal(list)  # List of selected elements
    element_double_clicked = pyqtSignal(object)  # Element that was double-clicked
    properties_request = pyqtSignal(object)  # Request to show properties for element
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.elements: Dict[str, SelectableElement] = {}
        self.selected_elements: List[str] = []  # List of selected element IDs
        self.hover_element_id: Optional[str] = None
        self.selection_mode = "single"  # "single", "multiple", "range"
        self.last_selected_id: Optional[str] = None
        
        # Element type colors for different visual feedback
        self.type_colors = {
            'clef': QColor(255, 100, 100, 120),           # Light red
            'key_signature': QColor(100, 255, 100, 120),   # Light green
            'time_signature': QColor(100, 100, 255, 120),  # Light blue
            'staff_name': QColor(255, 255, 100, 120),      # Light yellow
            'section_name': QColor(255, 150, 255, 120),    # Light magenta
            'barline': QColor(150, 150, 150, 120),         # Light gray
            'measure': QColor(200, 200, 255, 80),          # Very light blue
            'bracket': QColor(255, 200, 150, 120),         # Light orange
            'brace': QColor(150, 255, 200, 120),           # Light cyan
        }
        
    def clear_all_elements(self):
        """Clear all registered elements"""
        self.elements.clear()
        self.selected_elements.clear()
        self.hover_element_id = None
        self.last_selected_id = None
        
    def register_element(self, element: SelectableElement):
        """Register a new selectable element"""
        self.elements[element.element_id] = element
        
    def unregister_element(self, element_id: str):
        """Unregister an element"""
        if element_id in self.elements:
            del self.elements[element_id]
        if element_id in self.selected_elements:
            self.selected_elements.remove(element_id)
        if self.hover_element_id == element_id:
            self.hover_element_id = None
        if self.last_selected_id == element_id:
            self.last_selected_id = None
            
    def find_element_at_point(self, point: QPointF) -> Optional[SelectableElement]:
        """Find the topmost element at the given point"""
        # Check elements in reverse order (topmost first)
        # Prioritize smaller elements over larger ones for better selection
        candidates = []
        
        for element in self.elements.values():
            if element.contains_point(point):
                candidates.append(element)
                
        if not candidates:
            return None
            
        # Sort by area (smaller first) to prioritize precise elements
        candidates.sort(key=lambda e: e.bounds.width() * e.bounds.height())
        return candidates[0]
        
    def handle_mouse_press(self, point: QPointF, modifiers) -> bool:
        """
        Handle mouse press for element selection.
        Returns True if an element was selected, False otherwise.
        """
        element = self.find_element_at_point(point)
        
        if not element:
            # Click on empty area - clear selection unless Ctrl is held
            if not (modifiers & QApplication.instance().keyboardModifiers()):
                self.clear_selection()
            return False
            
        # Determine selection mode based on modifiers
        ctrl_held = bool(modifiers & QApplication.instance().keyboardModifiers())
        shift_held = bool(modifiers & QApplication.instance().keyboardModifiers())
        
        if shift_held and self.last_selected_id:
            # Range selection - select all elements between last and current
            self._select_range(self.last_selected_id, element.element_id)
        elif ctrl_held:
            # Toggle selection of this element
            self._toggle_element_selection(element.element_id)
        else:
            # Single selection - clear others and select this one
            self._select_single_element(element.element_id)
            
        self.last_selected_id = element.element_id
        self._emit_selection_changed()
        return True
        
    def handle_mouse_double_click(self, point: QPointF) -> bool:
        """
        Handle double-click for element property editing.
        Returns True if an element was double-clicked, False otherwise.
        """
        element = self.find_element_at_point(point)
        if element:
            self.element_double_clicked.emit(element)
            self.properties_request.emit(element)
            return True
        return False
        
    def handle_mouse_move(self, point: QPointF):
        """Handle mouse movement for hover effects"""
        old_hover = self.hover_element_id
        element = self.find_element_at_point(point)
        
        self.hover_element_id = element.element_id if element else None
        
        # Only emit update if hover changed
        if old_hover != self.hover_element_id:
            # Could emit a hover changed signal here if needed
            pass
            
    def _select_single_element(self, element_id: str):
        """Select a single element, clearing all others"""
        self.clear_selection()
        if element_id in self.elements:
            self.selected_elements.append(element_id)
            self.elements[element_id].is_selected = True
            
    def _toggle_element_selection(self, element_id: str):
        """Toggle selection of an element"""
        if element_id in self.selected_elements:
            self.selected_elements.remove(element_id)
            self.elements[element_id].is_selected = False
        else:
            self.selected_elements.append(element_id)
            self.elements[element_id].is_selected = True
            
    def _select_range(self, start_id: str, end_id: str):
        """Select a range of elements (implementation depends on element ordering)"""
        # For now, just select both elements
        # This could be enhanced to select elements in between based on their type and position
        if start_id in self.elements and end_id in self.elements:
            if start_id not in self.selected_elements:
                self.selected_elements.append(start_id)
                self.elements[start_id].is_selected = True
            if end_id not in self.selected_elements:
                self.selected_elements.append(end_id)
                self.elements[end_id].is_selected = True
                
    def clear_selection(self):
        """Clear all selections"""
        for element_id in self.selected_elements:
            if element_id in self.elements:
                self.elements[element_id].is_selected = False
        self.selected_elements.clear()
        
    def select_all_of_type(self, element_type: str):
        """Select all elements of a specific type"""
        self.clear_selection()
        for element in self.elements.values():
            if element.element_type == element_type:
                self.selected_elements.append(element.element_id)
                element.is_selected = True
        self._emit_selection_changed()
        
    def get_selected_elements(self) -> List[SelectableElement]:
        """Get all currently selected elements"""
        return [self.elements[eid] for eid in self.selected_elements if eid in self.elements]
        
    def get_selected_by_type(self, element_type: str) -> List[SelectableElement]:
        """Get all selected elements of a specific type"""
        return [elem for elem in self.get_selected_elements() if elem.element_type == element_type]
        
    def is_element_selected(self, element_id: str) -> bool:
        """Check if an element is selected"""
        return element_id in self.selected_elements
        
    def render_all_selections(self, painter: QPainter):
        """Render selection highlights for all selected elements"""
        painter.save()
        
        # Render hover effect first (below selection)
        if self.hover_element_id and self.hover_element_id in self.elements:
            hover_element = self.elements[self.hover_element_id]
            if not hover_element.is_selected:  # Don't show hover on selected elements
                # Draw subtle hover highlight
                hover_color = self.type_colors.get(hover_element.element_type, QColor(200, 200, 200, 80))
                painter.fillRect(hover_element.bounds.adjusted(-2, -2, 2, 2), hover_color)
        
        # Render selection highlights
        for element in self.get_selected_elements():
            element.render_selection_highlight(painter)
            
        painter.restore()
        
    def _emit_selection_changed(self):
        """Emit the selection changed signal"""
        selected_elements = self.get_selected_elements()
        self.selection_changed.emit(selected_elements)
        
    def get_selection_info(self) -> Dict[str, Any]:
        """Get detailed information about the current selection"""
        selected = self.get_selected_elements()
        
        info = {
            'count': len(selected),
            'types': {},
            'elements': selected
        }
        
        # Count by type
        for element in selected:
            element_type = element.element_type
            if element_type not in info['types']:
                info['types'][element_type] = 0
            info['types'][element_type] += 1
            
        return info
        
    def create_clef_element(self, staff_ref, x: float, y: float, width: float = 30, height: float = 40) -> SelectableElement:
        """Create a selectable clef element"""
        element_id = f"clef_{id(staff_ref)}_{staff_ref.instrument_name}"
        bounds = QRectF(x - width/2, y - height/2, width, height)
        
        properties = {
            'clef_type': getattr(staff_ref, 'clef', 'treble'),
            'staff_name': staff_ref.instrument_name,
            'position': {'x': x, 'y': y}
        }
        
        element = SelectableElement('clef', element_id, bounds, staff_ref, properties)
        self.register_element(element)
        return element
        
    def create_key_signature_element(self, staff_ref, x: float, y: float, width: float = 40, height: float = 30) -> SelectableElement:
        """Create a selectable key signature element"""
        element_id = f"key_sig_{id(staff_ref)}_{staff_ref.instrument_name}"
        bounds = QRectF(x, y - height/2, width, height)
        
        properties = {
            'key': getattr(staff_ref, 'key', 'C major'),
            'staff_name': staff_ref.instrument_name,
            'position': {'x': x, 'y': y}
        }
        
        element = SelectableElement('key_signature', element_id, bounds, staff_ref, properties)
        self.register_element(element)
        return element
        
    def create_time_signature_element(self, staff_ref, x: float, y: float, width: float = 25, height: float = 40) -> SelectableElement:
        """Create a selectable time signature element"""
        element_id = f"time_sig_{id(staff_ref)}_{staff_ref.instrument_name}"
        bounds = QRectF(x, y - height/2, width, height)
        
        properties = {
            'time_signature': getattr(staff_ref, 'time_signature', '4/4'),
            'staff_name': staff_ref.instrument_name,
            'position': {'x': x, 'y': y}
        }
        
        element = SelectableElement('time_signature', element_id, bounds, staff_ref, properties)
        self.register_element(element)
        return element
        
    def create_staff_name_element(self, staff_ref, x: float, y: float, text: str, width: float, height: float = 20) -> SelectableElement:
        """Create a selectable staff name element"""
        element_id = f"staff_name_{id(staff_ref)}_{staff_ref.instrument_name}"
        bounds = QRectF(x, y - height/2, width, height)
        
        properties = {
            'text': text,
            'staff_name': staff_ref.instrument_name,
            'position': {'x': x, 'y': y},
            'font_size': 10  # Default font size
        }
        
        element = SelectableElement('staff_name', element_id, bounds, staff_ref, properties)
        self.register_element(element)
        return element
        
    def create_section_name_element(self, section_ref, x: float, y: float, text: str, width: float, height: float = 25) -> SelectableElement:
        """Create a selectable section name element"""
        element_id = f"section_name_{id(section_ref)}_{section_ref.name}"
        bounds = QRectF(x, y - height/2, width, height)
        
        properties = {
            'text': text,
            'section_name': section_ref.name,
            'position': {'x': x, 'y': y},
            'font_size': 12  # Default font size
        }
        
        element = SelectableElement('section_name', element_id, bounds, section_ref, properties)
        self.register_element(element)
        return element
        
    def create_barline_element(self, x: float, y_top: float, y_bottom: float, barline_type: str = 'single') -> SelectableElement:
        """Create a selectable barline element"""
        element_id = f"barline_{x}_{y_top}_{y_bottom}"
        width = 8  # Clickable width for barlines
        height = y_bottom - y_top
        bounds = QRectF(x - width/2, y_top, width, height)
        
        properties = {
            'barline_type': barline_type,
            'position': {'x': x, 'y_top': y_top, 'y_bottom': y_bottom}
        }
        
        element = SelectableElement('barline', element_id, bounds, None, properties)
        self.register_element(element)
        return element 