#!/usr/bin/env python3
"""
Runtime patch to inject undo/redo functionality into the Full Score Options dialog
of the running ONOTE application.

This script finds the running dialog and monkey-patches it to add undo/redo support.
"""

import sys
import os
import time
import copy
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt

def find_full_score_options_dialog():
    """Find the Full Score Options dialog in the running application."""
    app = QApplication.instance()
    if not app:
        print("ERROR: No QApplication instance found. Make sure ONOTE is running.")
        return None
    
    # Look for FullScoreOptionsDialog
    for widget in app.allWidgets():
        class_name = widget.__class__.__name__
        if 'FullScoreOptions' in class_name or 'ScoreOptions' in class_name:
            print(f"Found dialog: {class_name} at {widget}")
            return widget
    
    print("ERROR: No Full Score Options dialog found. Make sure the dialog is open.")
    return None

def get_dialog_state(dialog):
    """Extract the current state of all controls in the dialog."""
    state = {}
    
    # Find all spinboxes, checkboxes, color buttons, etc.
    from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
    
    for widget in dialog.findChildren(QSpinBox):
        if hasattr(widget, 'objectName') and widget.objectName():
            state[widget.objectName()] = widget.value()
    
    for widget in dialog.findChildren(QDoubleSpinBox):
        if hasattr(widget, 'objectName') and widget.objectName():
            state[widget.objectName()] = widget.value()
    
    for widget in dialog.findChildren(QCheckBox):
        if hasattr(widget, 'objectName') and widget.objectName():
            state[widget.objectName()] = widget.isChecked()
    
    for widget in dialog.findChildren(QComboBox):
        if hasattr(widget, 'objectName') and widget.objectName():
            state[widget.objectName()] = widget.currentIndex()
    
    print(f"PATCH: Captured state with {len(state)} controls")
    return state

def set_dialog_state(dialog, state):
    """Restore the dialog to a previous state."""
    from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
    
    restored_count = 0
    
    for widget in dialog.findChildren(QSpinBox):
        if hasattr(widget, 'objectName') and widget.objectName() in state:
            widget.setValue(state[widget.objectName()])
            restored_count += 1
    
    for widget in dialog.findChildren(QDoubleSpinBox):
        if hasattr(widget, 'objectName') and widget.objectName() in state:
            widget.setValue(state[widget.objectName()])
            restored_count += 1
    
    for widget in dialog.findChildren(QCheckBox):
        if hasattr(widget, 'objectName') and widget.objectName() in state:
            widget.setChecked(state[widget.objectName()])
            restored_count += 1
    
    for widget in dialog.findChildren(QComboBox):
        if hasattr(widget, 'objectName') and widget.objectName() in state:
            widget.setCurrentIndex(state[widget.objectName()])
            restored_count += 1
    
    print(f"PATCH: Restored {restored_count} controls")

def patch_dialog_with_undo_redo(dialog):
    """Add undo/redo functionality to the dialog."""
    
    # Initialize undo/redo stacks
    dialog._patch_undo_stack = []
    dialog._patch_redo_stack = []
    dialog._patch_suppress_undo = False
    
    # Capture initial state
    initial_state = get_dialog_state(dialog)
    dialog._patch_undo_stack.append(copy.deepcopy(initial_state))
    print(f"PATCH: Initial state captured with {len(initial_state)} controls")
    
    def push_undo_state():
        """Push current state to undo stack."""
        if dialog._patch_suppress_undo:
            return
        
        current_state = get_dialog_state(dialog)
        
        # Only push if different from last state
        if not dialog._patch_undo_stack or dialog._patch_undo_stack[-1] != current_state:
            dialog._patch_undo_stack.append(copy.deepcopy(current_state))
            dialog._patch_redo_stack.clear()  # Clear redo on new action
            print(f"PATCH: Pushed undo state, stack size: {len(dialog._patch_undo_stack)}")
    
    def undo():
        """Undo last action."""
        print("PATCH: Undo called")
        if len(dialog._patch_undo_stack) < 2:
            print("PATCH: No undo states available")
            return
        
        # Move current state to redo stack
        current_state = dialog._patch_undo_stack.pop()
        dialog._patch_redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = dialog._patch_undo_stack[-1]
        dialog._patch_suppress_undo = True
        set_dialog_state(dialog, previous_state)
        dialog._patch_suppress_undo = False
        
        print(f"PATCH: Undo completed. Undo stack: {len(dialog._patch_undo_stack)}, Redo stack: {len(dialog._patch_redo_stack)}")
    
    def redo():
        """Redo last undone action."""
        print("PATCH: Redo called")
        if not dialog._patch_redo_stack:
            print("PATCH: No redo states available")
            return
        
        # Move state from redo to undo stack
        state = dialog._patch_redo_stack.pop()
        dialog._patch_undo_stack.append(state)
        
        # Restore state
        dialog._patch_suppress_undo = True
        set_dialog_state(dialog, state)
        dialog._patch_suppress_undo = False
        
        print(f"PATCH: Redo completed. Undo stack: {len(dialog._patch_undo_stack)}, Redo stack: {len(dialog._patch_redo_stack)}")
    
    # Create shortcuts
    import sys
    if sys.platform == 'darwin':
        undo_sequence = QKeySequence("Cmd+Z")
        redo_sequence = QKeySequence("Cmd+Y")
    else:
        undo_sequence = QKeySequence("Ctrl+Z")
        redo_sequence = QKeySequence("Ctrl+Y")
    
    # Create and connect shortcuts
    undo_shortcut = QShortcut(undo_sequence, dialog)
    undo_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
    undo_shortcut.activated.connect(undo)
    
    redo_shortcut = QShortcut(redo_sequence, dialog)
    redo_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
    redo_shortcut.activated.connect(redo)
    
    # Connect to all value-changing signals to track changes
    from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox
    
    connected_count = 0
    for widget in dialog.findChildren(QSpinBox):
        widget.valueChanged.connect(push_undo_state)
        connected_count += 1
    
    for widget in dialog.findChildren(QDoubleSpinBox):
        widget.valueChanged.connect(push_undo_state)
        connected_count += 1
    
    for widget in dialog.findChildren(QCheckBox):
        widget.toggled.connect(push_undo_state)
        connected_count += 1
    
    for widget in dialog.findChildren(QComboBox):
        widget.currentIndexChanged.connect(push_undo_state)
        connected_count += 1
    
    print(f"PATCH: Connected to {connected_count} widgets for change tracking")
    print(f"PATCH: Undo/Redo shortcuts created: {undo_sequence.toString()}, {redo_sequence.toString()}")
    print("PATCH: Undo/Redo functionality successfully injected!")
    
    # Store references to prevent garbage collection
    dialog._patch_undo_shortcut = undo_shortcut
    dialog._patch_redo_shortcut = redo_shortcut
    dialog._patch_push_undo_state = push_undo_state

def main():
    """Main function to inject undo/redo into running dialog."""
    print("PATCH: Looking for Full Score Options dialog...")
    
    dialog = find_full_score_options_dialog()
    if not dialog:
        print("PATCH: Failed to find dialog. Please ensure:")
        print("  1. ONOTE application is running")
        print("  2. Full Score Options dialog is open")
        print("  3. You're using the correct version with Full Score Options")
        return False
    
    print(f"PATCH: Found dialog: {dialog.__class__.__name__}")
    
    # Check if already patched
    if hasattr(dialog, '_patch_undo_stack'):
        print("PATCH: Dialog already patched with undo/redo functionality")
        return True
    
    # Apply the patch
    patch_dialog_with_undo_redo(dialog)
    
    print("\nPATCH: SUCCESS! Undo/Redo functionality added to the dialog.")
    print("  - Press Cmd+Z (Mac) or Ctrl+Z (Windows/Linux) to undo")
    print("  - Press Cmd+Y (Mac) or Ctrl+Y (Windows/Linux) to redo")
    print("  - Change some values in the dialog and test the shortcuts")
    
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1) 