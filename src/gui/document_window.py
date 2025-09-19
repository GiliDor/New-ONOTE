#!/usr/bin/env python3
"""
ONOTE Document Window
Independent window for each ONOTE document (score).
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QToolBar, QStatusBar, QSplitter,
    QApplication, QFileDialog, QMessageBox,
    QDockWidget, QLabel, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QCloseEvent

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.music.staff_view import StaffView
from src.gui.music.score_document import ScoreDocument
from src.gui.music.widgets.form_widget import FormWidget
from src.gui.dialogs.preferences_dialog import PreferencesDialog
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.music.score_setup_dialog import ScoreSetupDialog
from src import __version__


class DocumentWindow(QMainWindow):
    """
    Independent window for each ONOTE document.
    Each window contains its own staff view, form widget, and document.
    """
    
    # Signals
    document_modified = pyqtSignal(bool)
    document_saved = pyqtSignal(str)  # filename
    document_closed = pyqtSignal()
    
    def __init__(self, document: Optional[ScoreDocument] = None, app_manager=None, parent=None):
        super().__init__(parent)
        
        # Window properties
        self.setWindowTitle("ONOTE - Untitled")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Application manager reference
        self.app_manager = app_manager
        
        # Document management
        self.document = document or ScoreDocument()
        self.filename = None
        self.is_modified = False
        
        # UI components
        self.staff_view = None
        self.form_widget = None
        self.status_bar = None
        self.toolbar = None
        
        # Setup UI
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        self._setup_connections()
        
        # Update window title
        self._update_window_title()
        
        print(f"📄 DocumentWindow created - Version {__version__}")
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Staff view (left side) wrapped in a scroll area for scrollbars
        self.staff_view = StaffView()
        self.staff_view.set_document(self.document)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.staff_view)
        splitter.addWidget(scroll_area)
        
        # Form widget (right side)
        self.form_widget = FormWidget(self)
        self.form_widget.set_document(self.document)
        self.form_widget.setMaximumWidth(400)
        self.form_widget.setMinimumWidth(300)
        splitter.addWidget(self.form_widget)
        
        # Set splitter proportions (70% staff view, 30% form widget)
        splitter.setSizes([700, 300])
        
        # Connect staff view and form widget
        # Integration with temporal bridge is handled internally by FormWidget
    
    def _setup_menus(self):
        """Setup the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new score")
        new_action.triggered.connect(self.new_document)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an existing score")
        open_action.triggered.connect(self.open_document)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current score")
        save_action.triggered.connect(self.save_document)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.setStatusTip("Save the current score with a new name")
        save_as_action.triggered.connect(self.save_document_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Close action
        close_action = QAction("&Close", self)
        close_action.setShortcut(QKeySequence.StandardKey.Close)
        close_action.setStatusTip("Close this document")
        close_action.triggered.connect(self.close_document)
        file_menu.addAction(close_action)
        
        # Score menu
        score_menu = menubar.addMenu("&Score")
        
        # Score Setup action
        setup_action = QAction("&Score Setup", self)
        setup_action.setStatusTip("Open score setup dialog")
        setup_action.triggered.connect(self.open_score_setup)
        score_menu.addAction(setup_action)
        
        # Full Score Options action
        options_action = QAction("&Full Score Options", self)
        options_action.setStatusTip("Open full score options dialog")
        options_action.triggered.connect(self.open_full_score_options)
        score_menu.addAction(options_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo action
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        # Redo action
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.setStatusTip("Redo last action")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Preferences action
        preferences_action = QAction("&Preferences", self)
        preferences_action.setStatusTip("Open preferences dialog")
        preferences_action.triggered.connect(self.open_preferences)
        tools_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About ONOTE", self)
        about_action.setStatusTip("About ONOTE")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Setup the toolbar."""
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        
        # Add toolbar actions (will be connected to menu actions)
        # This can be expanded with icons and additional tools
    
    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status labels
        self.status_bar.addWidget(QLabel("Ready"))
    
    def _setup_connections(self):
        """Setup signal connections."""
        # Connect document modification signals
        if self.document:
            # self.document.modified_changed.connect(self._on_document_modified)
            pass
        
        # Connect staff view signals
        if self.staff_view:
            # Add any staff view specific connections here
            pass
    
    def _update_window_title(self):
        """Update the window title based on document state."""
        title = "ONOTE"
        
        if self.filename:
            title += f" - {os.path.basename(self.filename)}"
        else:
            title += " - Untitled"
        
        if self.is_modified:
            title += " *"
        
        self.setWindowTitle(title)
    
    def _on_document_modified(self, modified: bool):
        """Handle document modification state changes."""
        self.is_modified = modified
        self._update_window_title()
        self.document_modified.emit(modified)
    
    def new_document(self):
        """Create a new document in a new window."""
        if self.app_manager:
            # Create a new window via the application manager
            self.app_manager.create_new_window()
            print("📄 New document window created via ApplicationManager")
        else:
            # Fallback: create new document in current window
            if self.is_modified:
                reply = QMessageBox.question(
                    self, "Save Changes?",
                    "The current document has unsaved changes. Save before creating new?",
                    QMessageBox.StandardButton.Save | 
                    QMessageBox.StandardButton.Discard | 
                    QMessageBox.StandardButton.Cancel
                )
                
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_document():
                        return
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
            
            # Create new document
            self.document = ScoreDocument()
            self.filename = None
            self.is_modified = False
            
            # Update staff view and form widget
            self.staff_view.set_document(self.document)
            self.form_widget.set_document(self.document)
            
            self._update_window_title()
            self.status_bar.showMessage("New document created")
    
    def open_document(self):
        """Open an existing document."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "The current document has unsaved changes. Save before opening?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_document():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # Open file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Score", "", "ONOTE Files (*.onote);;All Files (*)"
        )
        
        if filename:
            try:
                # Load document
                self.document = ScoreDocument.load(filename)
                self.filename = filename
                self.is_modified = False
                
                # Update staff view and form widget
                self.staff_view.set_document(self.document)
                self.form_widget.set_document(self.document)
                
                self._update_window_title()
                self.status_bar.showMessage(f"Opened {os.path.basename(filename)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {str(e)}")
    
    def save_document(self) -> bool:
        """Save the current document."""
        if not self.filename:
            return self.save_document_as()
        
        try:
            self.document.save(self.filename)
            self.is_modified = False
            self._update_window_title()
            self.status_bar.showMessage(f"Saved {os.path.basename(self.filename)}")
            self.document_saved.emit(self.filename)
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file: {str(e)}")
            return False
    
    def save_document_as(self) -> bool:
        """Save the current document with a new name."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Score", "", "ONOTE Files (*.onote);;All Files (*)"
        )
        
        if filename:
            self.filename = filename
            return self.save_document()
        
        return False
    
    def close_document(self):
        """Close the current document."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "The document has unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_document():
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        # Close the window
        self.close()
    
    def open_score_setup(self):
        """Open the score setup dialog."""
        from src.gui.music.score_setup_dialog import ScoreSetupDialog
        # Create and show the dialog
        print(f"[DEBUG] DocumentWindow creating ScoreSetupDialog, parent type: {type(self)}")
        dialog = ScoreSetupDialog(self)
        if dialog.exec():
            # Dialog was accepted, update the document
            self.staff_view.apply_setup_changes()
            self.status_bar.showMessage("Score setup applied")
    
    def open_full_score_options(self):
        """Open the full score options dialog."""
        from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
        dialog = FullScoreOptionsDialog(self)
        
        # Set the document on the dialog so it can load current settings
        if hasattr(self, 'staff_view') and self.staff_view and self.staff_view.document:
            dialog.set_document(self.staff_view.document)
        
        if dialog.exec():
            # Dialog was accepted, update the view
            self.staff_view.update_view()
            self.status_bar.showMessage("Score options applied")
    
    def open_preferences(self):
        """Open the preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec()
    
    def undo(self):
        """Undo last action."""
        if self.document and hasattr(self.document, 'undo'):
            self.document.undo()
            self.status_bar.showMessage("Undo")
    
    def redo(self):
        """Redo last action."""
        if self.document and hasattr(self.document, 'redo'):
            self.document.redo()
            self.status_bar.showMessage("Redo")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About ONOTE",
            f"ONOTE - Object-Oriented Music Notation Software\n\n"
            f"Version {__version__}\n\n"
            f"A modern music notation editor with multi-window support."
        )
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        if self.is_modified:
            reply = QMessageBox.question(
                self, "Save Changes?",
                "The document has unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                if not self.save_document():
                    event.ignore()
                    return
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        
        # Emit close signal
        self.document_closed.emit()
        event.accept() 