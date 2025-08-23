from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QPushButton, QDialogButtonBox, 
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont

class ZoomPresetsDialog(QDialog):
    """Simplified dialog for managing zoom presets with one spinner and 4 preset slots"""
    
    zoom_changed = pyqtSignal(float)  # Signal emitted when zoom is applied
    
    def __init__(self, parent=None, current_zoom=1.0):
        super().__init__(parent)
        self.setWindowTitle("Zoom Presets")
        self.setModal(True)
        self.setMinimumWidth(300)
        self.setMinimumHeight(250)
        
        self.current_zoom = current_zoom
        self.presets = [0.5, 0.75, 1.0, 1.25]  # Default presets: 50%, 75%, 100%, 125%
        
        # Load saved presets
        self.load_presets()
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the simplified UI with one spinner and 4 preset slots"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("Zoom Presets")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Current zoom display
        current_zoom_label = QLabel(f"Current Zoom: {int(self.current_zoom * 100)}%")
        current_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(current_zoom_label)
        
        # Single zoom spinner
        spinner_layout = QHBoxLayout()
        spinner_layout.addWidget(QLabel("Zoom:"))
        
        self.zoom_spinner = QSpinBox()
        self.zoom_spinner.setRange(25, 400)
        self.zoom_spinner.setValue(int(self.current_zoom * 100))
        self.zoom_spinner.setSuffix("%")
        self.zoom_spinner.setSingleStep(1)
        spinner_layout.addWidget(self.zoom_spinner)
        
        # Apply button for current spinner value
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_current_zoom)
        spinner_layout.addWidget(apply_button)
        
        layout.addLayout(spinner_layout)
        
        # Preset slots
        presets_group = QGroupBox("Preset Slots")
        presets_layout = QGridLayout(presets_group)
        
        self.preset_labels = []
        self.set_buttons = []
        
        for i in range(4):
            # Preset label showing current value
            preset_label = QLabel(f"Slot {i+1}: {int(self.presets[i] * 100)}%")
            preset_label.setMinimumWidth(80)
            self.preset_labels.append(preset_label)
            presets_layout.addWidget(preset_label, i, 0)
            
            # Set button to save current spinner value
            set_button = QPushButton("Set")
            set_button.clicked.connect(lambda checked, slot=i: self.set_preset(slot))
            self.set_buttons.append(set_button)
            presets_layout.addWidget(set_button, i, 1)
            
            # Apply button to use this preset
            apply_preset_button = QPushButton("Apply")
            apply_preset_button.clicked.connect(lambda checked, slot=i: self.apply_preset(slot))
            presets_layout.addWidget(apply_preset_button, i, 2)
        
        layout.addWidget(presets_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def apply_current_zoom(self):
        """Apply the current spinner value as zoom"""
        try:
            print("ZOOM_PRESETS: apply_current_zoom called")
            zoom_factor = self.zoom_spinner.value() / 100.0
            self.zoom_changed.emit(zoom_factor)
            print(f"ZOOM_PRESETS: Applied current zoom {int(zoom_factor * 100)}%")
        except Exception as e:
            print(f"ZOOM_PRESETS: Exception in apply_current_zoom: {e}")
        
    def set_preset(self, slot):
        """Set the preset slot to the current spinner value"""
        try:
            print(f"ZOOM_PRESETS: set_preset called for slot {slot}")
            zoom_factor = self.zoom_spinner.value() / 100.0
            self.presets[slot] = zoom_factor
            self.preset_labels[slot].setText(f"Slot {slot+1}: {int(zoom_factor * 100)}%")
            self.save_presets()
            print(f"ZOOM_PRESETS: Set slot {slot+1} to {int(zoom_factor * 100)}%")
        except Exception as e:
            print(f"ZOOM_PRESETS: Exception in set_preset: {e}")
        
    def apply_preset(self, slot):
        """Apply the preset from the specified slot"""
        try:
            print(f"ZOOM_PRESETS: apply_preset called for slot {slot}")
            zoom_factor = self.presets[slot]
            self.zoom_spinner.setValue(int(zoom_factor * 100))
            self.zoom_changed.emit(zoom_factor)
            print(f"ZOOM_PRESETS: Applied preset {slot+1}: {int(zoom_factor * 100)}%")
        except Exception as e:
            print(f"ZOOM_PRESETS: Exception in apply_preset: {e}")
        
    def load_presets(self):
        """Load saved presets from settings"""
        settings = QSettings("ONOTE", "ZoomPresets")
        for i in range(4):
            preset_value = settings.value(f"preset_{i}", self.presets[i])
            self.presets[i] = float(preset_value)
            
    def save_presets(self):
        """Save presets to settings"""
        settings = QSettings("ONOTE", "ZoomPresets")
        for i, preset in enumerate(self.presets):
            settings.setValue(f"preset_{i}", preset) 