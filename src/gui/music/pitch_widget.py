from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QComboBox, QGridLayout,
                           QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

class PianoKey(QPushButton):
    def __init__(self, note_name, solfege_name, is_black=False, parent=None):
        super().__init__(parent)
        self.note_name = note_name
        self.solfege_name = solfege_name
        self.is_black = is_black
        
        # Set button properties
        if is_black:
            self.setFixedSize(40, 90)  # Slightly longer height for black keys
            self.setStyleSheet("""
                QPushButton {
                    background-color: black;
                    color: white;
                    border: 1px solid #333;
                    border-radius: 0 0 3px 3px;
                    text-align: center;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #333;
                }
                QPushButton:pressed {
                    background-color: #444;
                }
            """)
        else:
            self.setFixedSize(40, 150)  # Full height for white keys
            self.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                    border-radius: 0 0 3px 3px;
                    text-align: center;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
            """)
        
        # Set text with both note name and solfège
        if is_black:
            # For black keys, show sharp note on top and flat note underneath
            alt_note = self.get_alternative_note_name(note_name)
            self.setText(f"{note_name}\n{alt_note}")
        else:
            # For white keys, show only the letter name
            self.setText(note_name)
    
    def get_alternative_note_name(self, note_name):
        """Get the alternative note name for black keys"""
        alternatives = {
            "C#": "Db",
            "D#": "Eb",
            "F#": "Gb",
            "G#": "Ab",
            "A#": "Bb"
        }
        return alternatives.get(note_name, "")

class PitchWidget(QWidget):
    note_selected = pyqtSignal(str)  # Signal emitted when a note is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pitch Input")
        self.setMinimumSize(600, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Piano keyboard container
        piano_frame = QFrame()
        piano_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        piano_layout = QVBoxLayout(piano_frame)
        piano_layout.setSpacing(0)  # No spacing between rows
        
        # Single row for all keys
        keys_layout = QHBoxLayout()
        keys_layout.setSpacing(0)
        keys_layout.setContentsMargins(0, 0, 0, 0)
        keys_layout.setObjectName("keys_layout")  # Set the object name for finding it later
        
        # Create piano keys
        self.piano_keys = []
        
        # Define notes and their solfège names
        self.notes = [
            ("C", "Do"), ("C#", "Do♯"), ("D", "Re"), ("D#", "Re♯"),
            ("E", "Mi"), ("F", "Fa"), ("F#", "Fa♯"), ("G", "Sol"),
            ("G#", "Sol♯"), ("A", "La"), ("A#", "La♯"), ("B", "Si")
        ]
        
        # Create the piano keys
        self.create_piano_keys(keys_layout)
        
        # Add layout to piano frame
        piano_layout.addLayout(keys_layout)
        layout.addWidget(piano_frame)
        
        # Pitch modifiers section
        modifiers_frame = QFrame()
        modifiers_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        modifiers_layout = QHBoxLayout(modifiers_frame)
        
        # Accidentals
        accidentals_group = QVBoxLayout()
        accidentals_label = QLabel("Accidentals:")
        accidentals_layout = QHBoxLayout()
        
        for accidental in ["♮", "♯", "𝄪", "♭", "𝄫"]:
            btn = QPushButton(accidental)
            btn.setStyleSheet("font-size: 16px;")  # Increased font size
            btn.clicked.connect(lambda checked, a=accidental: self.handle_accidental_selection(a))
            accidentals_layout.addWidget(btn)
        
        accidentals_group.addWidget(accidentals_label)
        accidentals_group.addLayout(accidentals_layout)
        modifiers_layout.addLayout(accidentals_group)
        
        # Octave displacement
        octave_group = QVBoxLayout()
        octave_label = QLabel("Octave Displacement:")
        octave_layout = QHBoxLayout()
        
        for octave in ["8va", "8vb", "16va", "16vb"]:
            btn = QPushButton(octave)
            btn.setStyleSheet("font-size: 16px;")  # Increased font size
            btn.clicked.connect(lambda checked, o=octave: self.handle_octave_selection(o))
            octave_layout.addWidget(btn)
        
        octave_group.addWidget(octave_label)
        octave_group.addLayout(octave_layout)
        modifiers_layout.addLayout(octave_group)
        
        layout.addWidget(modifiers_frame)
        
        # MIDI input indicator
        midi_frame = QFrame()
        midi_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        midi_layout = QHBoxLayout(midi_frame)
        
        midi_label = QLabel("MIDI Input:")
        self.midi_status = QLabel("Not Connected")
        self.midi_status.setStyleSheet("color: red;")
        
        midi_layout.addWidget(midi_label)
        midi_layout.addWidget(self.midi_status)
        midi_layout.addStretch()
        
        layout.addWidget(midi_frame)
        
    def create_piano_keys(self, keys_layout):
        """Create and add piano keys to the layout"""
        # Clear existing keys
        for key in self.piano_keys:
            key.setParent(None)
        self.piano_keys.clear()
        
        # Constants for key widths
        KEY_WIDTH = 40  # Both black and white keys are 40px wide
        
        # Create all keys in a single row
        for note, solfege in self.notes:
            if "#" in note:
                # Create a container widget for black key to control its position
                container = QWidget()
                container.setFixedSize(40, 150)  # Same size as white keys
                container_layout = QVBoxLayout(container)
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(0)
                
                # Create and add the black key
                key = PianoKey(note, solfege, is_black=True)
                key.clicked.connect(lambda checked, n=note: self.handle_note_selection(n))
                container_layout.addWidget(key)
                
                # Add a spacer at the bottom to push the key to the top
                spacer = QWidget()
                spacer.setFixedHeight(60)  # 150 - 90 = 60px spacer
                container_layout.addWidget(spacer)
                
                # Add the container to the main layout
                keys_layout.addWidget(container)
                self.piano_keys.append(key)
            else:
                key = PianoKey(note, solfege, is_black=False)
                key.clicked.connect(lambda checked, n=note: self.handle_note_selection(n))
                keys_layout.addWidget(key)
                self.piano_keys.append(key)
    
    def handle_note_selection(self, note):
        """Handle note selection"""
        self.note_selected.emit(note)
        
    def handle_accidental_selection(self, accidental):
        """Handle accidental selection"""
        # TODO: Implement accidental handling
        print(f"Accidental selected: {accidental}")
        
    def handle_octave_selection(self, octave):
        """Handle octave displacement selection"""
        # TODO: Implement octave displacement handling
        print(f"Octave selected: {octave}")
        
    def update_midi_status(self, connected):
        """Update MIDI connection status"""
        if connected:
            self.midi_status.setText("Connected")
            self.midi_status.setStyleSheet("color: green;")
        else:
            self.midi_status.setText("Not Connected")
            self.midi_status.setStyleSheet("color: red;") 