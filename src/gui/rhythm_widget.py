from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFrame, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

class RhythmWidget(QWidget):
    note_selected = pyqtSignal(str)  # Signal to emit when a note is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Rhythm Input")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Create tab widget for notes and rests
        tab_widget = QTabWidget()
        
        # Notes tab
        notes_tab = QWidget()
        notes_layout = QHBoxLayout(notes_tab)
        
        # Create note buttons
        self.note_buttons = {}
        note_types = {
            'whole': '𝅝',      # Whole note
            'half': '𝅗𝅥',      # Half note
            'quarter': '♩',     # Quarter note
            'eighth': '♪',      # Eighth note
            'sixteenth': '♬',   # Sixteenth note
            'thirty_second': '𝅘𝅥𝅯'  # Thirty-second note
        }
        
        for note_type, symbol in note_types.items():
            btn = QPushButton(symbol)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    padding: 10px;
                    min-width: 50px;
                    min-height: 50px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(lambda checked, n=note_type: self.note_selected.emit(n))
            notes_layout.addWidget(btn)
            self.note_buttons[note_type] = btn
        
        # Rests tab
        rests_tab = QWidget()
        rests_layout = QHBoxLayout(rests_tab)
        
        # Create rest buttons
        self.rest_buttons = {}
        rest_types = {
            'whole_rest': '𝄻',      # Whole rest
            'half_rest': '𝄼',       # Half rest
            'quarter_rest': '𝄽',    # Quarter rest
            'eighth_rest': '𝄾',     # Eighth rest
            'sixteenth_rest': '𝄿',  # Sixteenth rest
            'thirty_second_rest': '𝅀'  # Thirty-second rest
        }
        
        for rest_type, symbol in rest_types.items():
            btn = QPushButton(symbol)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    padding: 10px;
                    min-width: 50px;
                    min-height: 50px;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(lambda checked, r=rest_type: self.note_selected.emit(r))
            rests_layout.addWidget(btn)
            self.rest_buttons[rest_type] = btn
        
        # Add tabs to tab widget
        tab_widget.addTab(notes_tab, "Notes")
        tab_widget.addTab(rests_tab, "Rests")
        
        layout.addWidget(tab_widget)
        
        # Preview area
        self.preview_frame = QFrame()
        self.preview_frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.preview_frame.setMinimumHeight(100)
        self.preview_frame.setStyleSheet("background-color: white;")
        layout.addWidget(self.preview_frame)
        
        # Set fixed size for the widget
        self.setFixedSize(400, 200)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        # Add any custom painting here if needed 