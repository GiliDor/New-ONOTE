from PyQt6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel

class HarmonyWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Harmony", parent)
        
        # Create central widget
        central_widget = QWidget()
        self.setWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add placeholder content
        layout.addWidget(QLabel("Harmony Widget"))
        layout.addStretch()
        
        # Initialize document reference
        self.document = None
    
    def set_document(self, document):
        """Set the document to work with"""
        self.document = document
        print(f"HARMONY: Document set to {document}") 