from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QComboBox, QDialog, QLabel,
                           QDialogButtonBox)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal

class StaffTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Staff Type")
        self.setModal(True)
        self.setMinimumWidth(200)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Staff type selection
        self.staff_type_combo = QComboBox()
        self.staff_type_combo.addItems(["Single Staff", "Grand Staff"])
        layout.addWidget(self.staff_type_combo)
        
        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_staff_type(self):
        return self.staff_type_combo.currentText()

class SectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Section")
        self.setModal(True)
        self.setMinimumWidth(300)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Section management buttons
        self.new_section_btn = QPushButton("New Section")
        self.add_to_section_btn = QPushButton("Add to Section")
        self.remove_from_section_btn = QPushButton("Remove from Section")
        
        layout.addWidget(self.new_section_btn)
        layout.addWidget(self.add_to_section_btn)
        layout.addWidget(self.remove_from_section_btn)
        
        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect signals
        self.new_section_btn.clicked.connect(self.on_new_section)
        self.add_to_section_btn.clicked.connect(self.on_add_to_section)
        self.remove_from_section_btn.clicked.connect(self.on_remove_from_section)
        
    def on_new_section(self):
        """Handle new section creation"""
        if hasattr(self.parent(), 'on_new_section'):
            self.parent().on_new_section()
            
    def on_add_to_section(self):
        """Handle adding to section"""
        if hasattr(self.parent(), 'on_add_to_section'):
            self.parent().on_add_to_section()
            
    def on_remove_from_section(self):
        """Handle removing from section"""
        if hasattr(self.parent(), 'on_remove_from_section'):
            self.parent().on_remove_from_section()

class AddStavesToolbar(QWidget):
    # Define signals
    staff_type_changed = pyqtSignal(str)
    new_section = pyqtSignal()
    add_to_section = pyqtSignal()
    remove_from_section = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the UI components"""
        layout = QHBoxLayout(self)
        
        # Staff Type Combo
        self.staff_type_combo = QComboBox()
        self.staff_type_combo.addItems(["Single Staff", "Grand Staff"])
        self.staff_type_combo.currentTextChanged.connect(self.staff_type_changed.emit)
        layout.addWidget(QLabel("Staff Type:"))
        layout.addWidget(self.staff_type_combo)
        
        # Section Buttons
        self.new_section_btn = QPushButton("New Section")
        self.new_section_btn.clicked.connect(self.new_section.emit)
        layout.addWidget(self.new_section_btn)
        
        self.add_to_section_btn = QPushButton("Add to Section")
        self.add_to_section_btn.clicked.connect(self.add_to_section.emit)
        layout.addWidget(self.add_to_section_btn)
        
        self.remove_from_section_btn = QPushButton("Remove from Section")
        self.remove_from_section_btn.clicked.connect(self.remove_from_section.emit)
        layout.addWidget(self.remove_from_section_btn)
        
        layout.addStretch()
        
    def update_with_staff_data(self, staff_data):
        """Update the toolbar with the selected staff data"""
        if staff_data.get('staff_type'):
            staff_type = staff_data['staff_type'].replace('_', ' ').title()
            index = self.staff_type_combo.findText(staff_type)
            if index >= 0:
                self.staff_type_combo.setCurrentIndex(index)
        
    def show_staff_type_dialog(self):
        """Show the staff type dialog"""
        dialog = StaffTypeDialog(self)
        # Position dialog under the Added Staves area
        if hasattr(self.parent(), 'staff_list'):
            staff_list = self.parent().staff_list
            pos = staff_list.mapToGlobal(QPoint(0, staff_list.height()))
            dialog.move(pos)
        dialog.exec()
        
    def show_section_dialog(self):
        """Show the section dialog"""
        dialog = SectionDialog(self)
        # Position dialog under the Added Staves area
        if hasattr(self.parent(), 'staff_list'):
            staff_list = self.parent().staff_list
            pos = staff_list.mapToGlobal(QPoint(0, staff_list.height()))
            dialog.move(pos)
        dialog.exec() 