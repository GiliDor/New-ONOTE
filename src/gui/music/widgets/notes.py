from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel

class NotesWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Notes", parent)
        
        # Create central widget
        central_widget = QWidget()
        self.setWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add placeholder content
        layout.addWidget(QLabel("Notes Widget"))
        layout.addStretch() 