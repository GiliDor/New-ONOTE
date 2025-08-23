#!/usr/bin/env python3
"""
Script to inject undo/redo functionality into the running ONOTE Full Score Options dialog.
This script monkey-patches the dialog to add undo/redo support.
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtCore import Qt
import copy

def find_full_score_options_dialog():
    """Find any open FullScoreOptionsDialog windows."""
    app = QApplication.instance()
    if not app:
        print("No QApplication instance found")
        return None
    
    for widget in app.allWidgets():
        if widget.__class__.__name__ == 'FullScoreOptionsDialog':
            print(f"Found FullScoreOptionsDialog: {widget}")
            return widget
    return None

def inject_undo_redo(dialog):
    """Inject undo/redo functionality into an existing dialog."""
    print(f"Injecting undo/redo into dialog {id(dialog)}")
    
    # Initialize undo/redo stacks if they don't exist
    if not hasattr(dialog, '_undo_stack'):
        dialog._undo_stack = []
    if not hasattr(dialog, '_redo_stack'):
        dialog._redo_stack = []
    if not hasattr(dialog, '_suppress_undo'):
        dialog._suppress_undo = False
    
    def get_current_state():
        """Get current state of all UI elements."""
        state = {}
        for attr_name in dir(dialog):
            attr = getattr(dialog, attr_name)
            if hasattr(attr, 'value') and callable(attr.value):
                try:
                    state[attr_name] = attr.value()
                except:
                    pass
            elif hasattr(attr, 'currentText') and callable(attr.currentText):
                try:
                    state[attr_name] = attr.currentText()
                except:
                    pass
        return state
    
    def set_state(state):
        """Restore UI elements to a saved state."""
        dialog._suppress_undo = True
        try:
            for attr_name, value in state.items():
                if hasattr(dialog, attr_name):
                    attr = getattr(dialog, attr_name)
                    if hasattr(attr, 'setValue') and callable(attr.setValue):
                        try:
                            attr.setValue(value)
                        except:
                            pass
                    elif hasattr(attr, 'setCurrentText') and callable(attr.setCurrentText):
                        try:
                            attr.setCurrentText(value)
                        except:
                            pass
        finally:
            dialog._suppress_undo = False
    
    def push_undo_state():
        """Push current state to undo stack."""
        if dialog._suppress_undo:
            return
        
        current_state = get_current_state()
        if not dialog._undo_stack or dialog._undo_stack[-1] != current_state:
            dialog._undo_stack.append(copy.deepcopy(current_state))
            dialog._redo_stack.clear()
            print(f"[INJECT] Pushed undo state, stack size: {len(dialog._undo_stack)}")
    
    def undo():
        """Perform undo operation."""
        print(f"[INJECT] Undo called, stack size: {len(dialog._undo_stack)}")
        if len(dialog._undo_stack) < 2:
            print("[INJECT] No undo states available")
            return
        
        current_state = dialog._undo_stack.pop()
        dialog._redo_stack.append(current_state)
        previous_state = dialog._undo_stack[-1]
        set_state(previous_state)
        print(f"[INJECT] Undo completed, undo stack: {len(dialog._undo_stack)}, redo stack: {len(dialog._redo_stack)}")
    
    def redo():
        """Perform redo operation."""
        print(f"[INJECT] Redo called, redo stack size: {len(dialog._redo_stack)}")
        if not dialog._redo_stack:
            print("[INJECT] No redo states available")
            return
        
        state = dialog._redo_stack.pop()
        dialog._undo_stack.append(state)
        set_state(state)
        print(f"[INJECT] Redo completed, undo stack: {len(dialog._undo_stack)}, redo stack: {len(dialog._redo_stack)}")
    
    # Inject methods into the dialog
    dialog._get_current_state = get_current_state
    dialog._set_state = set_state
    dialog._push_undo_state = push_undo_state
    dialog._undo = undo
    dialog._redo = redo
    
    # Create shortcuts
    import sys
    if sys.platform == 'darwin':
        undo_key = QKeySequence("Cmd+Z")
        redo_key = QKeySequence("Cmd+Y")
    else:
        undo_key = QKeySequence("Ctrl+Z")
        redo_key = QKeySequence("Ctrl+Y")
    
    dialog.undo_shortcut = QShortcut(undo_key, dialog)
    dialog.undo_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
    dialog.undo_shortcut.activated.connect(undo)
    
    dialog.redo_shortcut = QShortcut(redo_key, dialog)
    dialog.redo_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
    dialog.redo_shortcut.activated.connect(redo)
    
    print(f"[INJECT] Shortcuts created: Undo={undo_key.toString()}, Redo={redo_key.toString()}")
    
    # Connect to all value change signals to push undo states
    for attr_name in dir(dialog):
        attr = getattr(dialog, attr_name)
        if hasattr(attr, 'valueChanged'):
            try:
                attr.valueChanged.connect(push_undo_state)
                print(f"[INJECT] Connected {attr_name}.valueChanged")
            except:
                pass
        elif hasattr(attr, 'currentTextChanged'):
            try:
                attr.currentTextChanged.connect(push_undo_state)
                print(f"[INJECT] Connected {attr_name}.currentTextChanged")
            except:
                pass
    
    # Push initial state
    push_undo_state()
    print("[INJECT] Undo/Redo injection completed successfully!")

def main():
    print("ONOTE Undo/Redo Injector")
    print("Looking for FullScoreOptionsDialog...")
    
    while True:
        dialog = find_full_score_options_dialog()
        if dialog:
            if not hasattr(dialog, '_undo_injected'):
                inject_undo_redo(dialog)
                dialog._undo_injected = True
                print("Undo/Redo functionality injected! You can now use Cmd+Z and Cmd+Y in the dialog.")
                break
            else:
                print("Dialog already has undo/redo injected")
                break
        else:
            print("No FullScoreOptionsDialog found. Please open the Full Score Options dialog and try again.")
            time.sleep(2)

if __name__ == '__main__':
    main() 