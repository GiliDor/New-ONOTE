from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                           QComboBox, QLineEdit, QSpinBox, QPushButton,
                           QFormLayout)
from PyQt6.QtCore import Qt

class StaffDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Staff Options")
        self.setModal(True)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Create form layout for staff options
        form_layout = QFormLayout()
        
        # Staff type selection
        self.staff_type = QComboBox()
        self.staff_type.addItems(["Single Staff", "Grand Staff", "Full Score"])
        self.staff_type.currentTextChanged.connect(self.on_staff_type_changed)
        form_layout.addRow("Staff Type:", self.staff_type)
        
        # Staff count for full score
        self.staff_count = QSpinBox()
        self.staff_count.setRange(1, 10)
        self.staff_count.setValue(1)
        self.staff_count.setEnabled(False)  # Only enabled for Full Score
        form_layout.addRow("Number of Staves:", self.staff_count)
        
        # Name edit
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Abbreviation edit
        self.abbr_edit = QLineEdit()
        form_layout.addRow("Abbreviation:", self.abbr_edit)
        
        layout.addLayout(form_layout)
        
        # Add OK and Cancel buttons
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def on_staff_type_changed(self, staff_type):
        """Handle staff type change"""
        self.staff_count.setEnabled(staff_type == "Full Score")
        
    def get_settings(self):
        """Get the current settings"""
        staff_type = self.staff_type.currentText().lower().replace(" ", "_")
        if staff_type == "full_score":
            staff_type = f"full_{self.staff_count.value()}"
            
        return {
            "staff_type": staff_type,
            "name": self.name_edit.text(),
            "abbr": self.abbr_edit.text()
        } 