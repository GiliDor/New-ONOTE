#!/usr/bin/env python
"""
Test script for the notation model integration with the application.

This script demonstrates how to use the NotationService to create 
and manipulate scores, and how they integrate with the existing 
application structure.
"""

import sys
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.gui.music.score_document import ScoreDocument
from src.notation.service import notation_service
from src.notation.model import Score, Section, SingleStaff, GrandStaff

def test_document_creation():
    """Test creating different document types via the NotationService"""
    # Create a piano score
    piano_doc = notation_service.create_piano_document("Piano Score", "Composer")
    print(f"Created piano document: {piano_doc.title} by {piano_doc.composer}")
    print(f"Number of ungrouped staves: {len(piano_doc.layout.ungrouped_staves)}")
    print(f"Number of sections: {len(piano_doc.layout.sections)}")
    
    # Create a string quartet score
    quartet_doc = notation_service.create_string_quartet_document("String Quartet", "Composer")
    print(f"\nCreated string quartet document: {quartet_doc.title} by {quartet_doc.composer}")
    print(f"Number of ungrouped staves: {len(quartet_doc.layout.ungrouped_staves)}")
    print(f"Number of sections: {len(quartet_doc.layout.sections)}")
    print(f"Section map: {quartet_doc.section_map}")
    
    # Test the round-trip conversion
    piano_score = notation_service.load_document(piano_doc)
    print(f"\nRound-trip conversion for piano score:")
    print(f"Number of ungrouped staves: {len(piano_score.ungrouped_staves)}")
    print(f"Number of sections: {len(piano_score.sections)}")
    
    quartet_score = notation_service.load_document(quartet_doc)
    print(f"\nRound-trip conversion for string quartet:")
    print(f"Number of ungrouped staves: {len(quartet_score.ungrouped_staves)}")
    print(f"Number of sections: {len(quartet_score.sections)}")
    print(f"First section name: {quartet_score.sections[0].name if quartet_score.sections else 'No sections'}")
    print(f"Staves in first section: {len(quartet_score.sections[0].staves) if quartet_score.sections else 0}")

def launch_gui_with_test_document():
    """Launch the GUI with a test document"""
    from src.gui.music.main_window import MainWindow
    
    app = QApplication(sys.argv)
    
    # Open the main window
    window = MainWindow()
    
    # Create a score using the notation service
    notation_service.create_string_quartet_document("Test String Quartet", "ONOTE Test")
    
    # Apply the score to the window
    window.score_document = notation_service.current_document
    window.staff_view.set_document(window.score_document)
    
    # Show the window
    window.show()
    
    # Set a timer to print some diagnostic info after the window loads
    def print_info():
        print(f"Window title: {window.windowTitle()}")
        print(f"Document title: {window.score_document.title}")
        print(f"Number of ungrouped staves: {len(window.score_document.layout.ungrouped_staves)}")
        print(f"Number of sections: {len(window.score_document.layout.sections)}")
        print(f"Section map: {window.score_document.section_map}")
    
    QTimer.singleShot(1000, print_info)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    # Run the document creation test
    print("===== Testing Document Creation =====")
    test_document_creation()
    
    # Run the GUI test
    print("\n===== Testing GUI Integration =====")
    launch_gui_with_test_document() 