from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QLabel, QFrame, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class PitchWidget(QDockWidget):
    note_selected = pyqtSignal(str)  # Signal for note selection
    modifier_selected = pyqtSignal(str)  # Signal for modifier selection
    
    def __init__(self, parent=None):
        super().__init__("Pitch", parent)
        
        # Create central widget
        central_widget = QWidget()
        self.setWidget(central_widget)
        
        # Create main layout
        layout = QVBoxLayout(central_widget)
        
        # Create container for piano keys
        piano_container = QFrame()
        piano_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        piano_layout = QGridLayout(piano_container)
        
        # Define white and black keys
        white_keys = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        black_keys = ['C#', 'D#', '', 'F#', 'G#', 'A#', '']
        
        # Add white keys (bottom row)
        for i, key in enumerate(white_keys):
            btn = QPushButton(key)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 0 0 3px 3px;
                    padding: 20px 10px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.handle_note_selection(k))
            piano_layout.addWidget(btn, 1, i)
        
        # Add black keys (top row)
        for i, key in enumerate(black_keys):
            if key:  # Only add if there's a black key
                btn = QPushButton(key)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: black;
                        color: white;
                        border: 1px solid #333;
                        border-radius: 0 0 3px 3px;
                        padding: 10px 5px;
                        min-width: 30px;
                        margin-left: -15px;
                        margin-right: -15px;
                        z-index: 1;
                    }
                    QPushButton:hover {
                        background-color: #333;
                    }
                """)
                btn.clicked.connect(lambda checked, k=key: self.handle_note_selection(k))
                piano_layout.addWidget(btn, 0, i)
        
        layout.addWidget(piano_container)
        
        # Add octave controls
        octave_container = QFrame()
        octave_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        octave_layout = QHBoxLayout(octave_container)
        
        # Octave down button
        octave_down = QPushButton("Octave ↓")
        octave_down.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        octave_down.clicked.connect(lambda: self.handle_octave_change(-1))
        octave_layout.addWidget(octave_down)
        
        # Current octave display
        self.octave_label = QLabel("4")
        self.octave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.octave_label.setStyleSheet("""
            QLabel {
                padding: 5px 10px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        octave_layout.addWidget(self.octave_label)
        
        # Octave up button
        octave_up = QPushButton("Octave ↑")
        octave_up.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        octave_up.clicked.connect(lambda: self.handle_octave_change(1))
        octave_layout.addWidget(octave_up)
        layout.addWidget(octave_container)
        
        # Add note name display
        self.note_display = QLabel("Selected Note: None")
        self.note_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.note_display.setStyleSheet("""
            QLabel {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
        layout.addWidget(self.note_display)
        
        # Initialize state
        self.current_octave = 4
        self.current_note = None
        self.current_modifier = None
        self.document = None
    
    def set_document(self, document):
        """Set the document to work with"""
        self.document = document
        print(f"PITCH: Document set to {document}")
        
    def handle_note_selection(self, note):
        """Handle note selection"""
        self.current_note = note
        self.update_note_display()
        self.note_selected.emit(note)
        
    def handle_octave_change(self, direction):
        """Handle octave change"""
        self.current_octave += direction
        self.octave_label.setText(str(self.current_octave))
        self.update_note_display()
        
    def update_note_display(self):
        """Update the note display with current state"""
        if self.current_note:
            note_text = f"Selected Note: {self.current_note}"
            if self.current_modifier:
                note_text += f" {self.current_modifier}"
            note_text += f" {self.current_octave}"
            self.note_display.setText(note_text)
        else:
            self.note_display.setText("Selected Note: None") 