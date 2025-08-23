from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel

class FormDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Form", parent)
        
        # Create central widget
        central_widget = QWidget()
        self.setWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add placeholder content
        layout.addWidget(QLabel("Form Widget"))
        layout.addStretch() 