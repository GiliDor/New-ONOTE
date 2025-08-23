from PyQt6.QtWidgets import (QMainWindow, QMenuBar, QMenu, 
                           QApplication, QWidget, QVBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from src.gui.score_document import ScoreDocument

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ONOTE")
        self.score_documents = []  # Keep track of all score documents
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Then setup the rest of the UI
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI"""
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Create initial score document
        self.new_score()
        
        # Show the window after UI setup
        self.show()
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        print("Creating menu bar...")
        # Create menu bar explicitly
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        print("Menu bar created")
        
        # Create menus in the correct order
        self.file_menu = QMenu("File", self)
        self.edit_menu = QMenu("Edit", self)
        self.score_menu = QMenu("Score", self)
        self.tools_menu = QMenu("Tools", self)
        self.help_menu = QMenu("Help", self)
        
        # Add menus to menu bar
        menubar.addMenu(self.file_menu)
        menubar.addMenu(self.edit_menu)
        menubar.addMenu(self.score_menu)
        menubar.addMenu(self.tools_menu)
        menubar.addMenu(self.help_menu)
        print("Menus created")
        
        # Add New action to File menu
        new_action = QAction("New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_score)
        self.file_menu.addAction(new_action)
        
        # Setup Score menu actions
        self.score_setup_action = QAction("Score Setup", self)
        self.score_setup_action.setShortcut("Ctrl+Alt+S")
        self.score_setup_action.triggered.connect(self.enter_score_setup_mode)
        
        # Add actions to Score menu
        self.score_menu.addAction(self.score_setup_action)
        self.score_menu.addSeparator()
        
        # Add additional Score menu actions
        self.full_score_options_action = QAction("Full Score Options", self)
        self.parts_options_action = QAction("Parts Options", self)
        self.add_title_action = QAction("Add Title, Header, Footer...", self)
        self.dynamic_parts_action = QAction("Dynamic Parts", self)
        
        self.score_menu.addAction(self.full_score_options_action)
        self.score_menu.addAction(self.parts_options_action)
        self.score_menu.addAction(self.add_title_action)
        self.score_menu.addAction(self.dynamic_parts_action)
        print("Menu actions added")
        
    def new_score(self):
        """Create a new score document"""
        score_doc = ScoreDocument(self)
        self.score_documents.append(score_doc)
        score_doc.show()
        
    def enter_score_setup_mode(self):
        """Enter score setup mode for the active score"""
        active_score = self.get_active_score()
        if active_score:
            active_score.enter_setup_mode()
            
    def exit_score_setup_mode(self):
        """Exit score setup mode for the active score"""
        active_score = self.get_active_score()
        if active_score:
            active_score.exit_setup_mode()
            
    def get_active_score(self):
        """Get the currently active score document"""
        active_window = QApplication.activeWindow()
        if isinstance(active_window, ScoreDocument):
            return active_window
        return None 