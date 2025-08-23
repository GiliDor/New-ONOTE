from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QComboBox, QGridLayout,
                           QSpinBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPen, QColor

class StaffDialog(QDialog):
    staff_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Staff Settings")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Staff type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Staff Type:"))
        self.staff_type = QComboBox()
        self.staff_type.addItems(["Single Staff", "Grand Staff", "Full Score"])
        self.staff_type.currentTextChanged.connect(self.on_staff_type_changed)
        type_layout.addWidget(self.staff_type)
        layout.addLayout(type_layout)
        
        # Staff count for full score
        self.count_layout = QHBoxLayout()
        self.count_layout.addWidget(QLabel("Number of Staves:"))
        self.staff_count = QSpinBox()
        self.staff_count.setRange(1, 32)
        self.staff_count.setValue(4)
        self.staff_count.setEnabled(False)  # Initially disabled
        self.count_layout.addWidget(self.staff_count)
        layout.addLayout(self.count_layout)
        
        # Staff spacing
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Staff Spacing:"))
        self.staff_spacing = QSpinBox()
        self.staff_spacing.setRange(30, 100)  # Range in pixels
        self.staff_spacing.setValue(40)  # Default spacing
        self.staff_spacing.setSuffix(" px")
        spacing_layout.addWidget(self.staff_spacing)
        layout.addLayout(spacing_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def on_staff_type_changed(self, staff_type):
        """Handle staff type selection change"""
        self.staff_count.setEnabled(staff_type == "Full Score")
        
    def get_settings(self):
        """Get the current settings"""
        staff_type = self.staff_type.currentText()
        if staff_type == "Single Staff":
            return {
                'staff_type': 'single',
                'staff_spacing': self.staff_spacing.value()
            }
        elif staff_type == "Grand Staff":
            return {
                'staff_type': 'grand',
                'staff_spacing': self.staff_spacing.value()
            }
        else:  # Full Score
            return {
                'staff_type': f'full_{self.staff_count.value()}',
                'staff_spacing': self.staff_spacing.value()
            }

class ClefDialog(QDialog):
    clef_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clef Selection")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Clef selector
        clef_layout = QHBoxLayout()
        clef_layout.addWidget(QLabel("Clef:"))
        self.clef_combo = QComboBox()
        self.clef_combo.addItems([
            "Treble (G)", "Bass (F)", "Alto (C)", 
            "Tenor (C)", "Soprano (C)", "Mezzo-soprano (C)"
        ])
        clef_layout.addWidget(self.clef_combo)
        layout.addLayout(clef_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_settings(self):
        return {
            'clef': self.clef_combo.currentText()
        }

class KeyDialog(QDialog):
    key_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Key Selection")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        
        # Staff selector
        staff_layout = QHBoxLayout()
        staff_layout.addWidget(QLabel("Staff:"))
        self.staff_combo = QComboBox()
        self.staff_combo.addItems(["Staff 1", "Staff 2"])
        staff_layout.addWidget(self.staff_combo)
        layout.addLayout(staff_layout)
        
        # Key signature selector
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Key Signature:"))
        self.key_combo = QComboBox()
        self.key_combo.addItems([
            "C major / A minor (no sharps/flats)",
            "G major / E minor (1 sharp)",
            "D major / B minor (2 sharps)",
            "A major / F♯ minor (3 sharps)",
            "E major / C♯ minor (4 sharps)",
            "B major / G♯ minor (5 sharps)",
            "F♯ major / D♯ minor (6 sharps)",
            "C♯ major / A♯ minor (7 sharps)",
            "F major / D minor (1 flat)",
            "B♭ major / G minor (2 flats)",
            "E♭ major / C minor (3 flats)",
            "A♭ major / F minor (4 flats)",
            "D♭ major / B♭ minor (5 flats)",
            "G♭ major / E♭ minor (6 flats)",
            "C♭ major / A♭ minor (7 flats)"
        ])
        key_layout.addWidget(self.key_combo)
        layout.addLayout(key_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def get_settings(self):
        return {
            'staff': self.staff_combo.currentIndex(),
            'key': self.key_combo.currentText()
        } 