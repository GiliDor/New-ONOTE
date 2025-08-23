from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QComboBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal

class RhythmPalette(QWidget):
    pattern_selected = pyqtSignal(str)  # Signal emitted when a pattern is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rhythm Pattern Generator")
        self.setMinimumSize(300, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Add title label
        title_label = QLabel("Rhythm Palette")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f0f0;
                border-bottom: 1px solid #ccc;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Ratio selector
        ratio_label = QLabel("Ratio:")
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["1:1", "2:1", "3:1"])
        self.ratio_combo.currentTextChanged.connect(self.update_patterns)
        
        # Size selector
        size_label = QLabel("Size:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["w", "h", "q"])  # whole, half, quarter
        self.size_combo.currentTextChanged.connect(self.update_patterns)
        
        controls_layout.addWidget(ratio_label)
        controls_layout.addWidget(self.ratio_combo)
        controls_layout.addWidget(size_label)
        controls_layout.addWidget(self.size_combo)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Pattern grid
        self.pattern_grid = QGridLayout()
        layout.addLayout(self.pattern_grid)
        
        # Initialize patterns
        self.update_patterns()
        
    def update_patterns(self):
        """Update the pattern grid based on current settings"""
        # Clear existing patterns
        for i in reversed(range(self.pattern_grid.count())): 
            self.pattern_grid.itemAt(i).widget().setParent(None)
        
        # Get current settings
        ratio = self.ratio_combo.currentText()
        size = self.size_combo.currentText()
        
        # Create pattern buttons (placeholder for now)
        # This will be replaced with actual pattern generation later
        patterns = [
            "Pattern 1", "Pattern 2", "Pattern 3",
            "Pattern 4", "Pattern 5", "Pattern 6",
            "Pattern 7", "Pattern 8", "Pattern 9"
        ]
        
        # Add patterns to grid
        for i, pattern in enumerate(patterns):
            btn = QPushButton(pattern)
            btn.clicked.connect(lambda checked, p=pattern: self.pattern_selected.emit(p))
            self.pattern_grid.addWidget(btn, i // 3, i % 3)
            
    def get_current_settings(self):
        """Get current pattern settings"""
        return {
            'ratio': self.ratio_combo.currentText(),
            'size': self.size_combo.currentText()
        } 