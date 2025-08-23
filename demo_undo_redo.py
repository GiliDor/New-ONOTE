#!/usr/bin/env python3
"""
Complete demonstration of Full Score Options dialog with working undo/redo functionality.

This creates a standalone version of the dialog that proves our undo/redo implementation works.
You can then apply the same pattern to the main application.
"""

import sys
import os
import copy
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                           QLabel, QPushButton, QHBoxLayout, QMessageBox,
                           QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
                           QTabWidget, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut

class SimplifiedFullScoreOptionsDialog(QMainWindow):
    """Simplified version of Full Score Options dialog with working undo/redo."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Full Score Options - Undo/Redo Demo")
        self.setGeometry(100, 100, 600, 500)
        
        # Initialize undo/redo system
        self._undo_stack = []
        self._redo_stack = []
        self._suppress_undo = False
        
        self.setup_ui()
        self.setup_undo_redo()
        
        # Capture initial state
        initial_state = self._get_current_state()
        self._undo_stack.append(copy.deepcopy(initial_state))
        print(f"DEMO: Initial state captured with {len(initial_state)} controls")
    
    def setup_ui(self):
        """Create the UI with various controls."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Instructions
        instructions = QLabel("Demo Full Score Options with Undo/Redo\n\n"
                            "1. Change values below\n"
                            "2. Press Cmd+Z (Mac) or Ctrl+Z to undo\n"
                            "3. Press Cmd+Y (Mac) or Ctrl+Y to redo\n"
                            "4. Watch the terminal for debug messages")
        instructions.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(instructions)
        
        # Create tabs
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Staff Names tab
        staff_tab = self.create_staff_names_tab()
        tab_widget.addTab(staff_tab, "Staff Names")
        
        # Layout tab
        layout_tab = self.create_layout_tab()
        tab_widget.addTab(layout_tab, "Layout")
        
        # Manual undo/redo buttons for testing
        button_layout = QHBoxLayout()
        
        self.undo_button = QPushButton("Manual Undo (Test)")
        self.undo_button.clicked.connect(self._undo)
        button_layout.addWidget(self.undo_button)
        
        self.redo_button = QPushButton("Manual Redo (Test)")
        self.redo_button.clicked.connect(self._redo)
        button_layout.addWidget(self.redo_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Status
        self.status_label = QLabel("Ready - Try changing values and using Ctrl+Z/Ctrl+Y or manual buttons")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e8f4f8;")
        layout.addWidget(self.status_label)
    
    def create_staff_names_tab(self):
        """Create the staff names tab with font controls."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Font size group
        font_group = QGroupBox("Font Sizes")
        font_layout = QFormLayout(font_group)
        
        # Staff name font size
        self.staff_name_font_size = QSpinBox()
        self.staff_name_font_size.setObjectName("staff_name_font_size")
        self.staff_name_font_size.setRange(8, 72)
        self.staff_name_font_size.setValue(17)
        self.staff_name_font_size.valueChanged.connect(self._push_undo_state)
        font_layout.addRow("Staff Name Font Size:", self.staff_name_font_size)
        
        # Section name font size
        self.section_name_font_size = QSpinBox()
        self.section_name_font_size.setObjectName("section_name_font_size")
        self.section_name_font_size.setRange(8, 72)
        self.section_name_font_size.setValue(20)
        self.section_name_font_size.valueChanged.connect(self._push_undo_state)
        font_layout.addRow("Section Name Font Size:", self.section_name_font_size)
        
        layout.addWidget(font_group)
        
        # Visibility group
        visibility_group = QGroupBox("Visibility")
        visibility_layout = QFormLayout(visibility_group)
        
        self.show_staff_names = QCheckBox()
        self.show_staff_names.setObjectName("show_staff_names")
        self.show_staff_names.setChecked(True)
        self.show_staff_names.toggled.connect(self._push_undo_state)
        visibility_layout.addRow("Show Staff Names:", self.show_staff_names)
        
        self.show_section_names = QCheckBox()
        self.show_section_names.setObjectName("show_section_names")
        self.show_section_names.setChecked(True)
        self.show_section_names.toggled.connect(self._push_undo_state)
        visibility_layout.addRow("Show Section Names:", self.show_section_names)
        
        layout.addWidget(visibility_group)
        layout.addStretch()
        
        return widget
    
    def create_layout_tab(self):
        """Create the layout tab with positioning controls."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Position group
        position_group = QGroupBox("Positions")
        position_layout = QFormLayout(position_group)
        
        # Vertical position
        self.staff_name_v_pos = QDoubleSpinBox()
        self.staff_name_v_pos.setObjectName("staff_name_v_pos")
        self.staff_name_v_pos.setRange(-100.0, 100.0)
        self.staff_name_v_pos.setValue(0.0)
        self.staff_name_v_pos.setSuffix(" px")
        self.staff_name_v_pos.valueChanged.connect(self._push_undo_state)
        position_layout.addRow("Staff Name Vertical Position:", self.staff_name_v_pos)
        
        # Style combo
        self.name_style = QComboBox()
        self.name_style.setObjectName("name_style")
        self.name_style.addItems(["Normal", "Bold", "Italic", "Bold Italic"])
        self.name_style.currentIndexChanged.connect(self._push_undo_state)
        position_layout.addRow("Name Style:", self.name_style)
        
        layout.addWidget(position_group)
        layout.addStretch()
        
        return widget
    
    def setup_undo_redo(self):
        """Set up undo/redo shortcuts using keyPressEvent."""
        # Store the key sequences for reference
        self.undo_sequence = QKeySequence.StandardKey.Undo
        self.redo_sequence = QKeySequence.StandardKey.Redo
        
        print(f"DEMO: Shortcuts will use keyPressEvent - Undo: {QKeySequence(self.undo_sequence).toString()}, Redo: {QKeySequence(self.redo_sequence).toString()}")
    
    def keyPressEvent(self, event):
        """Handle key press events for undo/redo."""
        print(f"DEMO: Key press event - key: {event.key()}, modifiers: {event.modifiers()}")
        
        # Check for undo (Ctrl+Z or Cmd+Z) - be more explicit about the key
        if event.key() == Qt.Key.Key_Z and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):  # Not Shift+Z
                print("DEMO: Undo shortcut detected via keyPressEvent (Ctrl+Z)")
                self._undo()
                event.accept()
                return
        
        # Check for redo (Ctrl+Shift+Z or Ctrl+Y)
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if (event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                print("DEMO: Redo shortcut detected via keyPressEvent (Ctrl+Shift+Z)")
                self._redo()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Y:
                print("DEMO: Redo shortcut detected via keyPressEvent (Ctrl+Y)")
                self._redo()
                event.accept()
                return
        
        # Also try to install an event filter to catch events at the application level
        if not hasattr(self, '_event_filter_installed'):
            QApplication.instance().installEventFilter(self)
            self._event_filter_installed = True
            print("DEMO: Installed application-level event filter for Ctrl+Z")
        
        # Let the parent handle other keys
        super().keyPressEvent(event)
    
    def eventFilter(self, obj, event):
        """Application-level event filter to catch Ctrl+Z before other widgets."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Z and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    print("DEMO: Undo shortcut detected via eventFilter (Ctrl+Z)")
                    self._undo()
                    return True  # Consume the event
        return super().eventFilter(obj, event)
    
    def _get_current_state(self):
        """Get current state of all controls."""
        state = {}
        
        # Get all controls by their object names
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox)):
            if hasattr(widget, 'objectName') and widget.objectName():
                name = widget.objectName()
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    state[name] = widget.value()
                elif isinstance(widget, QCheckBox):
                    state[name] = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    state[name] = widget.currentIndex()
        
        return state
    
    def _set_state(self, state):
        """Restore controls to a previous state."""
        restored_count = 0
        
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox)):
            if hasattr(widget, 'objectName') and widget.objectName() in state:
                name = widget.objectName()
                value = state[name]
                
                if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                    widget.setValue(value)
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(value)
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(value)
                
                restored_count += 1
        
        print(f"DEMO: Restored {restored_count} controls")
        return restored_count
    
    def _push_undo_state(self):
        """Push current state to undo stack."""
        if self._suppress_undo:
            print("DEMO: Undo state push suppressed")
            return
        
        current_state = self._get_current_state()
        
        # Only push if different from last state
        if not self._undo_stack or self._undo_stack[-1] != current_state:
            self._undo_stack.append(copy.deepcopy(current_state))
            self._redo_stack.clear()  # Clear redo on new action
            print(f"DEMO: Pushed undo state, stack size: {len(self._undo_stack)}")
            self.status_label.setText(f"State saved - Undo stack: {len(self._undo_stack)} states")
        else:
            print("DEMO: State unchanged, not pushed")
    
    def _undo(self):
        """Undo last action."""
        print("DEMO: Undo called")
        if len(self._undo_stack) < 2:
            print("DEMO: No undo states available")
            self.status_label.setText("No undo states available")
            return
        
        # Move current state to redo stack
        current_state = self._undo_stack.pop()
        self._redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self._undo_stack[-1]
        self._suppress_undo = True
        restored_count = self._set_state(previous_state)
        self._suppress_undo = False
        
        print(f"DEMO: Undo completed - restored {restored_count} controls")
        print(f"DEMO: Undo stack: {len(self._undo_stack)}, Redo stack: {len(self._redo_stack)}")
        self.status_label.setText(f"Undo successful - restored {restored_count} controls (Undo: {len(self._undo_stack)}, Redo: {len(self._redo_stack)})")
    
    def _redo(self):
        """Redo last undone action."""
        print("DEMO: Redo called")
        if not self._redo_stack:
            print("DEMO: No redo states available")
            self.status_label.setText("No redo states available")
            return
        
        # Move state from redo to undo stack
        state = self._redo_stack.pop()
        self._undo_stack.append(state)
        
        # Restore state
        self._suppress_undo = True
        restored_count = self._set_state(state)
        self._suppress_undo = False
        
        print(f"DEMO: Redo completed - restored {restored_count} controls")
        print(f"DEMO: Undo stack: {len(self._undo_stack)}, Redo stack: {len(self._redo_stack)}")
        self.status_label.setText(f"Redo successful - restored {restored_count} controls (Undo: {len(self._undo_stack)}, Redo: {len(self._redo_stack)})")

def main():
    """Run the demo application."""
    app = QApplication(sys.argv)
    
    dialog = SimplifiedFullScoreOptionsDialog()
    dialog.show()
    
    print("DEMO: Application started")
    print("DEMO: Try changing values and using Cmd+Z/Cmd+Y (or Ctrl+Z/Ctrl+Y)")
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 