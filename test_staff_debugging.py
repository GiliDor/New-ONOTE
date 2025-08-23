#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from src.gui.music.main_window import MainWindow

def debug_staff_structure():
    app = QApplication(sys.argv)
    
    try:
        # Create main window and get document
        main_window = MainWindow()
        # Access document through staff_view
        document = main_window.staff_view.document
        
        print("=== STAFF STRUCTURE DEBUG ===")
        print(f"Total staves in document: {len(document.staves)}")
        print()
        
        # List all staves
        for i, staff in enumerate(document.staves):
            print(f"Staff {i+1}: {staff.instrument_name}")
            print(f"  - Type: {getattr(staff, 'staff_type', 'Unknown')}")
            print(f"  - Y Position: {getattr(staff, 'y_position', 'Unknown')}")
            print(f"  - Clef: {getattr(staff, 'clef', 'Unknown')}")
            print()
        
        print("=== SECTIONS DEBUG ===")
        if hasattr(document, 'sections') and document.sections:
            print(f"Total sections: {len(document.sections)}")
            for i, section in enumerate(document.sections):
                print(f"Section {i+1}: {section.name}")
                print(f"  - Staff count: {len(section.staves)}")
                for j, staff in enumerate(section.staves):
                    print(f"    Staff {j+1}: {staff.instrument_name}")
                print()
        else:
            print("No sections found - using ungrouped staves")
        
        print("=== RENDERING ORDER DEBUG ===")
        # Check what the renderer sees
        if hasattr(document, 'sections') and document.sections:
            rendering_staves = []
            for section in document.sections:
                rendering_staves.extend(section.staves)
        else:
            rendering_staves = document.staves
        
        print(f"Staves that will be rendered: {len(rendering_staves)}")
        for i, staff in enumerate(rendering_staves):
            print(f"  {i+1}. {staff.instrument_name} (y_pos: {getattr(staff, 'y_position', 'Unknown')})")
        
        # Check if any staff is missing
        document_staff_names = [staff.instrument_name for staff in document.staves]
        rendering_staff_names = [staff.instrument_name for staff in rendering_staves]
        
        missing_from_rendering = set(document_staff_names) - set(rendering_staff_names)
        if missing_from_rendering:
            print(f"\n❌ MISSING FROM RENDERING: {missing_from_rendering}")
        else:
            print(f"\n✅ All staves are included in rendering")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_staff_structure() 