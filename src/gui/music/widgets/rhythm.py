from PyQt6.QtWidgets import (QDockWidget, QWidget, QVBoxLayout, QLabel, QHBoxLayout,
                           QPushButton, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal

class RhythmWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Rhythm", parent)
        
        # Create central widget
        central_widget = QWidget()
        self.setWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add placeholder content
        layout.addWidget(QLabel("Rhythm Widget"))
        layout.addStretch()

class RhythmPatternWidget(QWidget):
    pattern_selected = pyqtSignal(str)  # Signal for pattern selection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create scroll area for patterns
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create container for patterns
        container = QWidget()
        patterns_layout = QVBoxLayout(container)
        
        # Add pattern buttons
        patterns = [
            "4/4 Basic", "3/4 Basic", "6/8 Basic",
            "Syncopated", "Triplet", "Dotted",
            "Complex", "Mixed", "Custom"
        ]
        
        for pattern in patterns:
            btn = QPushButton(pattern)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            btn.clicked.connect(lambda checked, p=pattern: self.handle_pattern_selection(p))
            patterns_layout.addWidget(btn)
        
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
    def handle_pattern_selection(self, pattern):
        self.pattern_selected.emit(pattern)

class SimpleRhythmWidget(QWidget):
    note_selected = pyqtSignal(str)  # Signal for note selection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(2)  # Minimal spacing between containers
        
        # Create horizontal layout for notes and rests
        notes_rests_layout = QHBoxLayout()
        notes_rests_layout.setSpacing(2)  # Minimal spacing between columns
        
        # Create notes container
        notes_container = QFrame()
        notes_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        notes_layout = QVBoxLayout(notes_container)
        notes_layout.setSpacing(2)  # Minimal spacing between rows
        
        # Add note duration buttons with Bravura Text symbols
        durations = [
            ("Whole Note", "\uE1D2", "\uE4E3"),  # Whole note and whole rest
            ("Half Note", "\uE1D3", "\uE4E4"),   # Half note and half rest
            ("Quarter Note", "\uE1D5", "\uE4E5"), # Quarter note and quarter rest
            ("Eighth Note", "\uE1D7", "\uE4E6"),  # Eighth note and eighth rest
            ("Sixteenth Note", "\uE1D9", "\uE4E7"), # Sixteenth note and sixteenth rest
            ("Thirty-second Note", "\uE1DB", "\uE4E8"), # Thirty-second note and rest
            ("Sixty-fourth Note", "\uE1DD", "\uE4E9")  # Sixty-fourth note and rest
        ]
        
        # Create two columns for notes and rests
        for name, note_symbol, rest_symbol in durations:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(2)  # Minimal spacing between buttons
            
            # Note button with Bravura Text font
            note_btn = QPushButton(note_symbol)
            note_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 4px;
                    text-align: center;
                    font-family: "Bravura Text";
                    font-size: 20px;
                    min-width: 30px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            note_btn.clicked.connect(lambda checked, s=note_symbol: self.handle_note_selection(s))
            row_layout.addWidget(note_btn)
            
            # Rest button with Bravura Text font
            rest_btn = QPushButton(rest_symbol)
            rest_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    padding: 4px;
                    text-align: center;
                    font-family: "Bravura Text";
                    font-size: 20px;
                    min-width: 30px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            rest_btn.clicked.connect(lambda checked, s=rest_symbol: self.handle_note_selection(s))
            row_layout.addWidget(rest_btn)
            
            notes_layout.addLayout(row_layout)
        
        notes_rests_layout.addWidget(notes_container)
        layout.addLayout(notes_rests_layout)
        
        # Create modifiers container
        modifiers_container = QFrame()
        modifiers_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        modifiers_layout = QHBoxLayout(modifiers_container)
        modifiers_layout.setSpacing(2)  # Minimal spacing between buttons
        
        # Add Dot button with Bravura Text font
        dot_btn = QPushButton("Dot (·)")  # Single dot
        dot_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
                text-align: center;
                font-family: "Bravura Text";
                font-size: 20px;
                min-width: 30px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        dot_btn.clicked.connect(lambda checked: self.handle_note_selection("\u1D16D"))
        modifiers_layout.addWidget(dot_btn)
        
        # Add Double Dot button with Bravura Text font
        double_dot_btn = QPushButton("Double Dot (··)")  # Double dot
        double_dot_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
                text-align: center;
                font-family: "Bravura Text";
                font-size: 20px;
                min-width: 30px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        double_dot_btn.clicked.connect(lambda checked: self.handle_note_selection("\u1D16D\u1D16D"))
        modifiers_layout.addWidget(double_dot_btn)
        
        # Add Tie button with Bravura Text font
        tie_btn = QPushButton("Tie (⌢)")  # Tie
        tie_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 4px;
                text-align: center;
                font-family: "Bravura Text";
                font-size: 20px;
                min-width: 30px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        tie_btn.clicked.connect(lambda checked: self.handle_note_selection("\u1D175"))
        modifiers_layout.addWidget(tie_btn)
        
        layout.addWidget(modifiers_container)
        
    def handle_note_selection(self, symbol):
        self.note_selected.emit(symbol) 