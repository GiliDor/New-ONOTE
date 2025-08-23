from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QFrame, QScrollArea, QWidget, QToolBar, QToolButton, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, pyqtSignal

class RhythmPatternDialog(QDialog):
    pattern_selected = pyqtSignal(str)  # Signal for pattern selection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Rhythm Pattern")
        self.setModal(False)  # Make modeless
        self.dialog_zoom = 1.0
        # --- Zoom controls bar ---
        zoom_toolbar = QToolBar()
        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("+")
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom * 1.2))
        zoom_toolbar.addWidget(zoom_in_btn)
        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("–")
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom / 1.2))
        zoom_toolbar.addWidget(zoom_out_btn)
        reset_btn = QToolButton()
        reset_btn.setText("100%")
        reset_btn.setToolTip("Reset Zoom")
        reset_btn.clicked.connect(lambda: self._set_dialog_zoom(1.0))
        zoom_toolbar.addWidget(reset_btn)
        zoom_menu = QMenu("In View", self)
        self.zoom_actions = []
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_dialog_zoom(v))
            zoom_menu.addAction(act)
            self.zoom_actions.append((act, value))
        zoom_tool_btn = QToolButton()
        zoom_tool_btn.setText("In View")
        zoom_tool_btn.setMenu(zoom_menu)
        zoom_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        zoom_toolbar.addWidget(zoom_tool_btn)
        # --- Main content in a scroll area for scalable zoom ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
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
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)
        self.content_layout.addWidget(scroll)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.content_layout.addWidget(close_btn)
        
        # Set dialog size
        self.resize(300, 400)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(zoom_toolbar)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        self.scroll_area.setWidget(self.content_widget)
        self._set_dialog_zoom(1.0)
        
    def handle_pattern_selection(self, pattern):
        self.pattern_selected.emit(pattern)
        self.close()

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01)

class SimpleRhythmDialog(QDialog):
    note_selected = pyqtSignal(str)  # Signal for note selection
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simple Rhythm Notation")
        self.setModal(False)  # Make modeless
        self.dialog_zoom = 1.0
        # --- Zoom controls bar ---
        zoom_toolbar = QToolBar()
        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("+")
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom * 1.2))
        zoom_toolbar.addWidget(zoom_in_btn)
        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("–")
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom / 1.2))
        zoom_toolbar.addWidget(zoom_out_btn)
        reset_btn = QToolButton()
        reset_btn.setText("100%")
        reset_btn.setToolTip("Reset Zoom")
        reset_btn.clicked.connect(lambda: self._set_dialog_zoom(1.0))
        zoom_toolbar.addWidget(reset_btn)
        zoom_menu = QMenu("In View", self)
        self.zoom_actions = []
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_dialog_zoom(v))
            zoom_menu.addAction(act)
            self.zoom_actions.append((act, value))
        zoom_tool_btn = QToolButton()
        zoom_tool_btn.setText("In View")
        zoom_tool_btn.setMenu(zoom_menu)
        zoom_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        zoom_toolbar.addWidget(zoom_tool_btn)
        # --- Main content in a scroll area for scalable zoom ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Create note buttons container
        notes_container = QFrame()
        notes_container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        notes_layout = QVBoxLayout(notes_container)
        
        # Add note duration buttons
        durations = [
            ("Whole Note", "𝅝"),
            ("Half Note", "𝅗𝅥"),
            ("Quarter Note", "♩"),
            ("Eighth Note", "♪"),
            ("Sixteenth Note", "♬"),
            ("Thirty-second Note", "𝅘𝅥𝅯"),
            ("Sixty-fourth Note", "𝅘𝅥𝅰")
        ]
        
        for name, symbol in durations:
            btn = QPushButton(f"{name} ({symbol})")
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
            btn.clicked.connect(lambda checked, s=symbol: self.handle_note_selection(s))
            notes_layout.addWidget(btn)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(notes_container)
        self.content_layout.addWidget(scroll)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        self.content_layout.addWidget(close_btn)
        
        # Set dialog size
        self.resize(300, 400)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(zoom_toolbar)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        self.scroll_area.setWidget(self.content_widget)
        self._set_dialog_zoom(1.0)
        
    def handle_note_selection(self, symbol):
        self.note_selected.emit(symbol)
        self.close()

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01) 