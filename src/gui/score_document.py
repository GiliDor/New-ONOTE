from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton,
                           QLabel, QHBoxLayout, QCheckBox, QSpinBox, QGroupBox,
                           QToolBar, QSizePolicy)
from PyQt6.QtCore import Qt
from src.gui.music.staff_view import StaffView

class ScoreDocument(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Untitled Score")
        self.setMinimumSize(800, 600)
        
        # Initialize setup mode state
        self.setup_mode = False
        self.setup_background_color = "#fff0f0"  # Light pink for setup mode
        self.edit_background_color = "#ffffff"   # White for edit mode
        
        # Create central widget for staff view
        self.staff_view = StaffView()
        self.staff_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setCentralWidget(self.staff_view)
        
        # Set up window flags
        self.setWindowFlags(Qt.WindowType.Window)
        
    def enter_setup_mode(self):
        """Enter score setup mode"""
        print("Entering setup mode...")
        self.setup_mode = True
        self.staff_view.enter_setup_mode()
        
    def exit_setup_mode(self):
        """Exit score setup mode"""
        print("Exiting setup mode...")
        self.setup_mode = False
        self.staff_view.exit_setup_mode()
        
    def handle_staff_added(self, instrument_id: str, staff_type: str):
        """Add a new staff to the score"""
        self.staff_view.handle_staff_added(instrument_id, staff_type)
        
    def handle_staff_removed(self, staff_index: int):
        """Remove a staff from the score"""
        self.staff_view.handle_staff_removed(staff_index)
        
    def handle_staff_visibility(self, staff_index: int, is_visible: bool):
        """Handle staff visibility changes"""
        self.staff_view.handle_staff_visibility(staff_index, is_visible)
        
    def handle_staff_options(self, staff_index: int, options: dict):
        """Handle staff options changes"""
        self.staff_view.handle_staff_options(staff_index, options)
        
    def get_background_color(self):
        """Get the current background color based on mode"""
        return self.setup_background_color if self.setup_mode else self.edit_background_color
        
    def toggle_setup_mode(self):
        """Toggle between setup and edit modes"""
        self.setup_mode = not self.setup_mode
        self.layout.set_setup_mode(self.setup_mode)
        
    def is_in_setup_mode(self) -> bool:
        """Check if the score is in setup mode"""
        return self.setup_mode and self.layout.is_setup_mode 