#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog

def test_undo_redo():
    app = QApplication(sys.argv)
    
    # Create a dummy parent window
    from PyQt6.QtWidgets import QMainWindow
    parent = QMainWindow()
    
    # Create the dialog
    dialog = FullScoreOptionsDialog(parent)
    dialog.show()
    
    print("Test completed. Check if you see the debug messages above.")
    print("Now test the undo/redo shortcuts in the dialog.")
    
    app.exec()

if __name__ == '__main__':
    test_undo_redo() 