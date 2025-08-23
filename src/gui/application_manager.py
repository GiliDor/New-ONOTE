#!/usr/bin/env python3
"""
ONOTE Application Manager
Manages multiple document windows in a multi-window architecture.
"""

import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QRect, QPoint
from PyQt6.QtGui import QScreen

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.desktop_window import DesktopWindow
from src.gui.document_window import DocumentWindow
from src import __version__


class ApplicationManager(QObject):
    """
    Manages the ONOTE application with multiple document windows.
    Handles window creation, positioning, and coordination.
    """
    
    # Signals
    window_created = pyqtSignal(object)  # window
    window_closed = pyqtSignal(object)   # window
    document_opened = pyqtSignal(str)    # filename
    application_exiting = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Window management
        self.windows: List[QMainWindow] = []
        self.desktop_window: Optional[DesktopWindow] = None
        
        # Window positioning
        self.window_offset = 30
        self.current_offset = 0
        
        # Application settings
        self.settings = {}
        
        # Create desktop window
        self._create_desktop_window()
        
        print(f"🎵 ONOTE Application Manager initialized - Version {__version__}")
        
    def _create_desktop_window(self):
        """Create the main desktop window."""
        self.desktop_window = DesktopWindow(app_manager=self)
        self.windows.append(self.desktop_window)
        
        # Connect signals
        self.desktop_window.document_saved.connect(self._on_document_saved)
        self.desktop_window.document_closed.connect(self._on_document_closed)
        
        print("🖥️ Desktop window created")
        
    def create_new_window(self) -> DesktopWindow:
        """Create a new document window (as a DesktopWindow)."""
        # Calculate position for new window
        position = self._calculate_window_position()
        
        # Create new window as DesktopWindow
        new_window = DesktopWindow(app_manager=self)
        new_window.move(position)
        
        # Add to window list
        self.windows.append(new_window)
        
        # Connect signals
        new_window.document_saved.connect(self._on_document_saved)
        new_window.document_closed.connect(self._on_document_closed)
        
        # Show window
        new_window.show()
        new_window.raise_()
        new_window.activateWindow()
        
        # Update open files menu in all windows
        self._update_open_files_menus()
        
        # Emit signal
        self.window_created.emit(new_window)
        
        print(f"📄 New document window created at {position}")
        return new_window
        
    def open_document(self, filename: str) -> Optional[DocumentWindow]:
        """Open a document in a new window."""
        if not os.path.exists(filename):
            QMessageBox.warning(None, "File Not Found", f"Could not find file: {filename}")
            return None
            
        # Create new window
        new_window = self.create_new_window()
        
        # Load document
        try:
            new_window.load_document(filename)
            self.document_opened.emit(filename)
            print(f"📄 Document opened: {filename}")
            return new_window
        except Exception as e:
            QMessageBox.warning(new_window, "Open Error", f"Could not open file: {str(e)}")
            new_window.close()
            return None
            
    def _calculate_window_position(self) -> QPoint:
        """Calculate position for new window."""
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Calculate position with offset
        x = screen_geometry.x() + 100 + self.current_offset
        y = screen_geometry.y() + 100 + self.current_offset
        
        # Update offset for next window
        self.current_offset += self.window_offset
        
        # Reset offset if it gets too large
        if self.current_offset > 200:
            self.current_offset = 0
            
        return QPoint(x, y)
        
    def tile_windows(self):
        """Tile all document windows."""
        if len(self.windows) <= 1:
            return
            
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Calculate tile dimensions
        num_windows = len(self.windows) - 1  # Exclude desktop window
        if num_windows == 0:
            return
            
        # Calculate grid
        cols = int(num_windows ** 0.5)
        rows = (num_windows + cols - 1) // cols
        
        # Calculate window size
        window_width = screen_geometry.width() // cols
        window_height = screen_geometry.height() // rows
        
        # Position windows
        window_index = 0
        for window in self.windows[1:]:  # Skip desktop window
            if window_index >= num_windows:
                break
                
            row = window_index // cols
            col = window_index % cols
            
            x = screen_geometry.x() + col * window_width
            y = screen_geometry.y() + row * window_height
            
            window.move(x, y)
            window.resize(window_width, window_height)
            window.show()
            window.raise_()
            
            window_index += 1
            
        print(f"🪟 Tiled {num_windows} windows")
        
    def cascade_windows(self):
        """Cascade all document windows."""
        if len(self.windows) <= 1:
            return
            
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Calculate cascade position
        base_x = screen_geometry.x() + 50
        base_y = screen_geometry.y() + 50
        offset = 30
        
        # Position windows
        window_index = 0
        for window in self.windows[1:]:  # Skip desktop window
            x = base_x + window_index * offset
            y = base_y + window_index * offset
            
            # Ensure window stays within screen bounds
            if x + window.width() > screen_geometry.right():
                x = screen_geometry.right() - window.width()
            if y + window.height() > screen_geometry.bottom():
                y = screen_geometry.bottom() - window.height()
                
            window.move(x, y)
            window.show()
            window.raise_()
            
            window_index += 1
            
        print(f"🪟 Cascaded {window_index} windows")
        
    def _update_open_files_menus(self):
        """Update the 'Currently Open' menu in all windows."""
        for window in self.windows:
            if hasattr(window, 'open_files_menu'):
                # Clear existing menu
                window.open_files_menu.clear()
                
                # Add actions for each document window (excluding desktop)
                for doc_window in self.windows[1:]:
                    if doc_window.isVisible():
                        # Create action with window title
                        action = window.open_files_menu.addAction(doc_window.windowTitle())
                        action.triggered.connect(lambda checked, w=doc_window: self._activate_window(w))
                        
    def _activate_window(self, window: QMainWindow):
        """Activate a specific window."""
        window.show()
        window.raise_()
        window.activateWindow()
        
    def _on_document_saved(self, filename: str):
        """Handle document saved signal."""
        print(f"💾 Document saved: {filename}")
        
    def _on_document_closed(self):
        """Handle document closed signal."""
        # Find the window that was closed
        for window in self.windows[:]:  # Copy list to avoid modification during iteration
            if not window.isVisible():
                self.windows.remove(window)
                self.window_closed.emit(window)
                break
                
        # Update open files menu
        self._update_open_files_menus()
        
        print(f"📄 Window closed, {len(self.windows)} windows remaining")
        
    def get_all_windows(self) -> List[QMainWindow]:
        """Get all windows."""
        return self.windows.copy()
        
    def get_document_windows(self) -> list:
        """Get all document windows (excluding desktop)."""
        # Return all DesktopWindow instances except the main desktop_window
        return [w for w in self.windows if isinstance(w, DesktopWindow) and w is not self.desktop_window]
        
    def close_all_windows(self):
        """Close all windows."""
        for window in self.windows[:]:  # Copy list to avoid modification during iteration
            window.close()
            
    def get_active_window(self) -> Optional[QMainWindow]:
        """Get the currently active window."""
        active_window = QApplication.activeWindow()
        if active_window in self.windows:
            return active_window
        return None
        
    def exit_application(self):
        """Exit the application."""
        self.application_exiting.emit()
        self.close_all_windows()
        QApplication.quit()


def create_application_manager(app: QApplication) -> ApplicationManager:
    """Create and return an ApplicationManager instance."""
    manager = ApplicationManager()
    
    # Connect application quit signal
    app.aboutToQuit.connect(manager.exit_application)
    
    return manager


def main():
    """Main entry point for the multi-window ONOTE application."""
    # Create application
    app = QApplication(sys.argv)
    
    # Create application manager
    manager = create_application_manager(app)
    
    # Create initial window
    manager.create_new_window()
    
    # Start the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 