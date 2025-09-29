from PyQt6.QtWidgets import (QMainWindow, QMenuBar, QMenu, QToolBar,
                            QDockWidget, QStatusBar, QFileDialog, QMessageBox,
                            QWidget, QVBoxLayout, QDialog, QHBoxLayout,
                            QLabel, QPushButton, QLineEdit, QComboBox, QSpinBox,
                            QCheckBox, QGroupBox, QRadioButton, QScrollArea,
                            QTabWidget, QSplitter, QApplication, QDialogButtonBox,
                            QSizePolicy)
from PyQt6.QtCore import Qt, QTimer, QSettings, QPoint, QSize, QDir, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
import os
import json
from datetime import datetime

from src.core.settings_manager import settings
from .staff_view import StaffView
from .score_setup_dialog import ScoreSetupDialog
from .page_setup_dialog import PageSetupDialog
from .score_document import ScoreDocument
from .staff_types import StaffType, SingleStaff, GrandStaff, SectionGroup
from .measure_object import MeasureObject
from .widgets.form_widget import FormWidget
from .widgets.rhythm import RhythmWidget
from .widgets.pitch import PitchWidget
from .widgets.harmony import HarmonyWidget
from .widgets.notes import NotesWidget
from .widgets.form import FormDockWidget
try:
    from .measure_manager import PageLayout
except Exception:
    # Fallback: define a minimal PageLayout to allow app to start if import fails
    from dataclasses import dataclass
    @dataclass
    class PageLayout:  # type: ignore
        page_width: float = 800.0
        page_height: float = 1120.0
        left_margin: float = 40.0
        right_margin: float = 40.0
        top_margin: float = 40.0
        bottom_margin: float = 120.0
        system_spacing: int = 80

        @property
        def available_width(self) -> float:
            return max(0.0, float(self.page_width) - float(self.left_margin + self.right_margin))

        @property
        def available_height(self) -> float:
            return max(0.0, float(self.page_height) - float(self.top_margin + self.bottom_margin))

class WindowManager:
    """Central window management system for ONOTE application"""
    
    # Class variables to track all windows and dialogs
    _document_windows = []
    _open_dialogs = {}  # dialog_type: dialog_instance
    _next_document_position = None
    _cascade_offset = 30
    
    @classmethod
    def register_document_window(cls, window):
        """Register a new document window"""
        cls._document_windows.append(window)
        cls._position_document_window(window)
        
    @classmethod
    def unregister_document_window(cls, window):
        """Unregister a document window"""
        if window in cls._document_windows:
            cls._document_windows.remove(window)
        # Reset cascade positioning if no windows left
        if not cls._document_windows:
            cls._next_document_position = None
            
    @classmethod
    def _position_document_window(cls, window):
        """Position document window with optimal sizing for ONOTE desktop"""
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate optimal window size to fit within desktop with margins
        # Leave small equal margins at top and bottom (20px each)
        margin = 20
        window_width = 1200  # Keep horizontal size as is
        window_height = screen.height() - (2 * margin)  # Desktop height minus margins
        
        # Ensure minimum height
        window_height = max(600, window_height)
        
        if cls._next_document_position is None:
            # First window - position at top-left corner with proper margins
            x = screen.x() + 50
            y = screen.y() + margin  # Use margin instead of 50
        else:
            # Subsequent windows - cascade from previous position
            x = cls._next_document_position[0] + cls._cascade_offset
            y = cls._next_document_position[1] + cls._cascade_offset
            
            # Reset cascade if going off screen
            max_x = screen.width() - window_width - 50  # Leave room for window
            max_y = screen.height() - window_height - 50  # Leave room for window
            
            if x > max_x or y > max_y:
                x = screen.x() + 50
                y = screen.y() + margin  # Use margin instead of 50
        
        # Store next position for cascading
        cls._next_document_position = (x, y)
        
        # Set window size and position with optimal height
        window.resize(window_width, window_height)
        window.move(x, y)
        
        print(f"WINDOW_SIZING: Document window sized to {window_width}x{window_height} with {margin}px margins")
        
    @classmethod
    def show_dialog(cls, dialog_type, dialog_class, parent_window, *args, **kwargs):
        """Show dialog positioned at top-right corner, allowing multiple dialogs"""
        print(f"[DEBUG] WindowManager.show_dialog called:")
        print(f"[DEBUG]   dialog_type: {dialog_type}")
        print(f"[DEBUG]   dialog_class: {dialog_class}")
        print(f"[DEBUG]   parent_window type: {type(parent_window)}")
        print(f"[DEBUG]   parent_window id: {id(parent_window)}")
        
        # Check if this dialog type is already open
        if dialog_type in cls._open_dialogs:
            existing_dialog = cls._open_dialogs[dialog_type]
            if existing_dialog and existing_dialog.isVisible():
                # Bring existing dialog to front
                existing_dialog.raise_()
                existing_dialog.activateWindow()
                print(f"[DEBUG]   Using existing dialog: {existing_dialog}")
                return existing_dialog
            else:
                # Clean up dead reference
                del cls._open_dialogs[dialog_type]
        
        # Create new dialog
        print(f"[DEBUG]   Creating new dialog instance...")
        dialog = dialog_class(parent_window, *args, **kwargs)
        print(f"[DEBUG]   Created dialog instance: {dialog}")
        print(f"[DEBUG]   Dialog id: {id(dialog)}")
        print(f"[DEBUG]   Dialog parent: {dialog.parent()}")
        print(f"[DEBUG]   Dialog parent type: {type(dialog.parent())}")
        
        cls._open_dialogs[dialog_type] = dialog
        
        # Position at top-right corner with stacking
        cls._position_dialog(dialog, dialog_type)
        
        # Connect finished signal to cleanup
        dialog.finished.connect(lambda: cls._cleanup_dialog(dialog_type))
        
        # Show dialog non-modally to allow multiple dialogs
        dialog.setModal(False)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        
        print(f"[DEBUG]   Dialog shown and activated")
        return dialog
        
    @classmethod
    def _position_dialog(cls, dialog, dialog_type):
        """Position dialog at top-right corner with proper stacking"""
        screen = QApplication.primaryScreen().geometry()
        
        # Base position at top-right corner
        base_x = screen.width() - 650  # Leave room for dialog width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_count = len([d for d in cls._open_dialogs.values() if d and d.isVisible()])
        stack_offset = open_count * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure dialog stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        dialog.move(final_x, final_y)
        
    @classmethod
    def _cleanup_dialog(cls, dialog_type):
        """Clean up dialog reference when dialog is closed"""
        if dialog_type in cls._open_dialogs:
            del cls._open_dialogs[dialog_type]
            
    @classmethod
    def cascade_document_windows(cls):
        """Manually cascade all document windows with optimal sizing"""
        if not cls._document_windows:
            return
            
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate optimal window size to fit within desktop with margins
        margin = 20
        window_width = 1200  # Keep horizontal size as is
        window_height = screen.height() - (2 * margin)  # Desktop height minus margins
        window_height = max(600, window_height)  # Ensure minimum height
        
        x = screen.x() + 50
        y = screen.y() + margin  # Use margin instead of 50
        
        for i, window in enumerate(cls._document_windows):
            if window.isVisible():
                window.resize(window_width, window_height)
                window.move(x + i * cls._cascade_offset, y + i * cls._cascade_offset)
                window.raise_()
                
        # Update next position
        if cls._document_windows:
            last_window = cls._document_windows[-1]
            cls._next_document_position = (last_window.x(), last_window.y())
            
    @classmethod
    def tile_document_windows(cls):
        """Tile all document windows"""
        visible_windows = [w for w in cls._document_windows if w.isVisible()]
        if not visible_windows:
            return
            
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate grid dimensions
        n = len(visible_windows)
        cols = int((n ** 0.5) + 0.5)
        rows = (n + cols - 1) // cols
        
        # Calculate window size
        window_width = screen.width() // cols
        window_height = screen.height() // rows
        
        # Position each window
        for i, window in enumerate(visible_windows):
            row = i // cols
            col = i % cols
            
            x = screen.x() + col * window_width
            y = screen.y() + row * window_height
            
            window.resize(window_width, window_height)
            window.move(x, y)
            window.show()
            window.raise_()
            
    @classmethod
    def get_open_dialogs(cls):
        """Get list of currently open dialogs"""
        return {k: v for k, v in cls._open_dialogs.items() if v and v.isVisible()}

class MainWindow(QMainWindow):
    # Class variable to track untitled document numbers
    _untitled_counter = 0
    # Class variables for singleton ScoreSetupWidget and its dock
    _score_setup_widget = None
    _score_setup_dock = None
    
    def __init__(self, is_welcome_window=False):
        super().__init__()
        self.is_welcome_window = is_welcome_window
        self.setWindowTitle("ONOTE")
        self.setMinimumSize(1024, 768)
        
        # CRITICAL FIX: Set resize policy to ensure resizeEvent is called
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Initialize active_score
        self.active_score = None
        
        # Initialize file-related attributes
        self.current_file = None
        self.is_modified = False
        self.untitled_number = None  # Track this window's untitled number
        self.scores_directory = settings.get_score_directory()
        
        # Set window flags based on window type
        if is_welcome_window:
            # Desktop window flags
            self.setWindowFlags(Qt.WindowType.WindowMaximizeButtonHint | 
                              Qt.WindowType.WindowStaysOnBottomHint)
            # Set grey background
            self.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                }
            """)
            # Maximize the desktop window
            self.showMaximized()
            # Set window title to indicate it's the desktop
            self.setWindowTitle("ONOTE Desktop")
        else:
            # Document window flags - ensure resize is enabled
            self.setWindowFlags(Qt.WindowType.Window | 
                              Qt.WindowType.WindowMinMaxButtonsHint |
                              Qt.WindowType.WindowCloseButtonHint)
            # Ensure window can be resized - remove problematic setFixedSize
            # self.setFixedSize(QSize())  # This was causing resize issues
        
        # Add window tracking
        if not hasattr(MainWindow, '_all_windows'):
            MainWindow._all_windows = []
        self.windows = MainWindow._all_windows
        self.windows.append(self)
        
        # Register with WindowManager for positioning (only if not welcome window)
        if not is_welcome_window:
            WindowManager.register_document_window(self)
        
        # Store original size
        self.original_size = self.size()
        
        # Create scores directory if it doesn't exist
        if not os.path.exists(self.scores_directory):
            os.makedirs(self.scores_directory)
            print(f"Created scores directory: {self.scores_directory}")
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create menu bar first
        self.create_menu_bar()
        
        # Create toolbar for non-welcome windows
        if not is_welcome_window:
            self.create_toolbar()
        
        # Initialize staff view for non-welcome windows
        if not is_welcome_window:
            self.staff_view = StaffView()
            self.staff_view.main_window = self  # Add reference for barline functionality
            self.main_layout.addWidget(self.staff_view)
            # Create initial score document
            self.score_document = ScoreDocument()
            self.staff_view.set_document(self.score_document)
            # Ensure initial page layout from Preferences is applied immediately
            try:
                layout = self.score_document.layout
                # Enforce preferred orientation (Portrait by default) on first render
                try:
                    from PyQt6.QtCore import QSettings
                    preferred_orientation = str(QSettings("ONOTE", "Preferences").value("layout/default_orientation", "Portrait"))
                    # Normalize
                    preferred_orientation = 'Landscape' if preferred_orientation.lower().startswith('land') else 'Portrait'
                    # Swap if needed
                    if preferred_orientation == 'Portrait' and getattr(layout, 'page_width', 0) > getattr(layout, 'page_height', 1):
                        w, h = layout.page_width, layout.page_height
                        layout.page_width, layout.page_height = h, w
                    elif preferred_orientation == 'Landscape' and getattr(layout, 'page_width', 1) < getattr(layout, 'page_height', 0):
                        w, h = layout.page_width, layout.page_height
                        layout.page_width, layout.page_height = h, w
                except Exception:
                    pass
                # Recompute staff positions based on margins/top margin
                if hasattr(layout, '_update_positions'):
                    layout._update_positions()
                if hasattr(self.staff_view, 'renderer') and self.staff_view.renderer:
                    # Force renderer to use document page size and margins now
                    self.staff_view.renderer.set_page_size(getattr(layout, 'page_width', self.staff_view.renderer.page_width),
                                                          getattr(layout, 'page_height', self.staff_view.renderer.page_height))
                    self.staff_view.renderer.set_margins({
                        'left': getattr(layout, 'left_margin', self.staff_view.renderer.margins.get('left', 0)),
                        'right': getattr(layout, 'right_margin', self.staff_view.renderer.margins.get('right', 0)),
                        'top': getattr(layout, 'top_margin', self.staff_view.renderer.margins.get('top', 0)),
                        'bottom': getattr(layout, 'bottom_margin', self.staff_view.renderer.margins.get('bottom', 0))
                    })
                # Ask temporal bridge to refresh layout once at startup
                if hasattr(self.staff_view, 'temporal_bridge') and self.staff_view.temporal_bridge:
                    try:
                        self.staff_view.temporal_bridge._force_layout_refresh()
                    except Exception:
                        pass
                self.staff_view.update()
            except Exception as _e:
                # Non-fatal: initial layout application best-effort
                pass
            
            # CRITICAL FIX: Automatically switch to edit mode after document initialization
            # This ensures users see the proper end bar and measure system immediately
            print("MAIN_WINDOW: Automatically switching to edit mode after document initialization")
            self.staff_view.enter_edit_mode()
            
            # Set initial toggle mode action text based on mode
            if hasattr(self, 'toggle_mode_action'):
                initial_text = "Edit Mode" if self.staff_view.is_setup_mode else "Score Setup"
                self.toggle_mode_action.setText(initial_text)
                
            # Update document dependent actions now that we have a document
            self.update_document_dependent_actions()
        else:
            self.staff_view = None
            self.score_document = None
        
        print("Main window initialized")
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # New action
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_score)
        file_menu.addAction(new_action)
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_score)
        file_menu.addAction(open_action)
        
        # Save action
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_score)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_score_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Import action
        import_action = QAction("&Import...", self)
        import_action.triggered.connect(self.import_score)
        file_menu.addAction(import_action)
        
        # Export action
        export_action = QAction("&Export...", self)
        export_action.triggered.connect(self.export_score)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Print Preview action
        print_preview_action = QAction("Print Pre&view...", self)
        print_preview_action.triggered.connect(self.print_preview)
        file_menu.addAction(print_preview_action)
        
        # Print action
        print_action = QAction("&Print...", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_score)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        # Close Score action
        close_score_action = QAction("&Close Score", self)
        close_score_action.setShortcut("Ctrl+W")
        close_score_action.triggered.connect(self.close_active_score)
        file_menu.addAction(close_score_action)
        
        # Close All action
        close_all_action = QAction("Close &All", self)
        close_all_action.setShortcut("Ctrl+Shift+W")
        close_all_action.triggered.connect(self.close_all_scores)
        file_menu.addAction(close_all_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.quit)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Undo action
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        # Redo action
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        # Add toggle_edit_mode action with F2 shortcut
        toggle_edit_mode_action = QAction("&Toggle Edit Mode", self)
        toggle_edit_mode_action.setShortcut("F2")
        toggle_edit_mode_action.triggered.connect(self.toggle_edit_mode)
        edit_menu.addAction(toggle_edit_mode_action)
        
        # Score menu
        score_menu = menubar.addMenu("&Score")
        
        # Score Setup action - store as instance variable for dynamic text updates
        self.score_setup_action = QAction("&Score Setup", self)
        self.score_setup_action.setShortcut("Ctrl+Alt+S")
        self.score_setup_action.triggered.connect(self.show_score_setup)
        score_menu.addAction(self.score_setup_action)
        
        # Initial state - disable if no document
        self.update_document_dependent_actions()
        
        page_setup_action = QAction("&Page Setup", self)
        page_setup_action.triggered.connect(self.show_page_setup)
        score_menu.addAction(page_setup_action)
        
        score_menu.addSeparator()
        
        # Full Score Options action
        full_score_options_action = QAction("&Full Score Options", self)
        full_score_options_action.triggered.connect(self.show_full_score_options)
        score_menu.addAction(full_score_options_action)
        
        # Parts Options action
        parts_options_action = QAction("&Parts Options", self)
        parts_options_action.triggered.connect(self.show_parts_options)
        score_menu.addAction(parts_options_action)
        
        # Add Title, Header, Footer action
        add_title_action = QAction("Add &Title, Header, Footer...", self)
        add_title_action.triggered.connect(self.show_title_options)
        score_menu.addAction(add_title_action)
        
        # Dynamic Parts action
        dynamic_parts_action = QAction("&Dynamic Parts", self)
        dynamic_parts_action.triggered.connect(self.show_dynamic_parts)
        score_menu.addAction(dynamic_parts_action)
        
        # Notation Setup action
        notation_setup_action = QAction("&Notation Setup", self)
        notation_setup_action.triggered.connect(self.show_notation_setup)
        score_menu.addAction(notation_setup_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # View options
        self.continuous_view_action = QAction("&Continuous View", self)
        self.continuous_view_action.setCheckable(True)
        self.continuous_view_action.triggered.connect(self.toggle_continuous_view)
        view_menu.addAction(self.continuous_view_action)
        
        self.page_across_action = QAction("Page &Across", self)
        self.page_across_action.setCheckable(True)
        self.page_across_action.triggered.connect(self.toggle_page_across)
        view_menu.addAction(self.page_across_action)
        
        self.page_down_action = QAction("Page &Down", self)
        self.page_down_action.setCheckable(True)
        self.page_down_action.triggered.connect(self.toggle_page_down)
        view_menu.addAction(self.page_down_action)
        
        view_menu.addSeparator()
        
        # Zoom In action
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        # Zoom Out action
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        # Reset Zoom action
        reset_zoom_action = QAction("Reset &Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)
        
        # Zoom Presets action
        zoom_presets_action = QAction("Zoom &Presets...", self)
        zoom_presets_action.setShortcut("Ctrl+Shift+Z")
        zoom_presets_action.triggered.connect(self.show_zoom_presets)
        view_menu.addAction(zoom_presets_action)
        
        view_menu.addSeparator()
        
        # Window arrangement options
        tile_action = QAction("&Tile Windows", self)
        tile_action.triggered.connect(self.tile_windows)
        view_menu.addAction(tile_action)
        
        cascade_action = QAction("&Cascade Windows", self)
        cascade_action.triggered.connect(self.cascade_windows)
        view_menu.addAction(cascade_action)
        
        view_menu.addSeparator()
        
        # Open Files submenu
        self.open_files_menu = view_menu.addMenu("&Currently Open")
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Form action
        form_action = QAction("&Form", self)
        form_action.triggered.connect(self.show_form)
        tools_menu.addAction(form_action)
        
        # Notes action
        notes_action = QAction("&Notes", self)
        notes_action.triggered.connect(self.show_notes)
        tools_menu.addAction(notes_action)
        
        # Rhythm action
        rhythm_action = QAction("&Rhythm", self)
        rhythm_action.triggered.connect(self.show_rhythm)
        tools_menu.addAction(rhythm_action)
        
        # Pitch action
        pitch_action = QAction("&Pitch", self)
        pitch_action.triggered.connect(self.show_pitch)
        tools_menu.addAction(pitch_action)
        
        # Harmony action
        harmony_action = QAction("&Harmony", self)
        harmony_action.triggered.connect(self.show_harmony)
        tools_menu.addAction(harmony_action)
        
        tools_menu.addSeparator()
        
        # Preferences action
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(preferences_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # Documentation action
        documentation_action = QAction("&Documentation", self)
        documentation_action.setShortcut("F1")
        documentation_action.triggered.connect(self.show_documentation)
        help_menu.addAction(documentation_action)
        
        # Keyboard Shortcuts action
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+/")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # Check for Updates action
        updates_action = QAction("Check for &Updates", self)
        updates_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(updates_action)
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)
        
        # Test menu removed
        
        # Add window management menu
        window_menu = menubar.addMenu("&Window")
        
        # Bring All to Front action
        bring_all_to_front_action = QAction("&Bring All to Front", self)
        bring_all_to_front_action.setShortcut("Ctrl+Shift+F")
        bring_all_to_front_action.triggered.connect(self.bring_all_to_front)
        window_menu.addAction(bring_all_to_front_action)
        
        window_menu.addSeparator()
        
        # Tile Windows action
        tile_windows_action = QAction("&Tile Windows", self)
        tile_windows_action.triggered.connect(self.tile_windows)
        window_menu.addAction(tile_windows_action)
        
        # Cascade Windows action
        cascade_windows_action = QAction("&Cascade Windows", self)
        cascade_windows_action.triggered.connect(self.cascade_windows)
        window_menu.addAction(cascade_windows_action)
        
        print("Menu bar created")
        
    def create_toolbar(self):
        """Create the main toolbar"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Add toolbar actions
        toolbar.addAction("New", self.new_score)
        toolbar.addAction("Open", self.open_score)
        toolbar.addAction("Save", self.save_score)
        toolbar.addSeparator()
        
        # Store reference to toggle mode action
        self.toggle_mode_action = toolbar.addAction("Score Setup", self.toggle_edit_mode)
        
        return toolbar
        
    def new_score(self):
        """Create a new score"""
        # Create a new window (WindowManager handles positioning)
        new_window = MainWindow(is_welcome_window=False)
        
        # Increment the untitled counter and set the window title
        MainWindow._untitled_counter += 1
        new_window.untitled_number = MainWindow._untitled_counter
        if MainWindow._untitled_counter == 1:
            new_window.setWindowTitle("ONOTE - Untitled")
        else:
            new_window.setWindowTitle(f"ONOTE - Untitled {MainWindow._untitled_counter}")
        
        # Use the NotationService to create an empty document
        from src.notation.service import notation_service
        new_window.score_document = notation_service.create_empty_document("New Score", "")
        new_window.staff_view.set_document(new_window.score_document)
        # PATCH: Sync renderer and dialog with document settings
        if hasattr(new_window.staff_view, 'renderer') and new_window.staff_view.renderer:
            new_window.staff_view.renderer.set_document(new_window.score_document)
            new_window.staff_view.renderer.load_notation_settings()
        if hasattr(new_window, 'full_score_options_dialog') and new_window.full_score_options_dialog:
            new_window.full_score_options_dialog.set_document(new_window.score_document)
        
        # Set up the new score
        new_window.staff_view.is_setup_mode = True
        new_window.staff_view.document.toggle_setup_mode()
        new_window.staff_view.update()
        
        # Initialize the toggle_mode_action text and visibility for new scores (setup mode)
        if hasattr(new_window, 'toggle_mode_action'):
            new_window.toggle_mode_action.setText("Edit Mode")
        
        # Update all interface text and visibility based on current mode (setup mode)
        new_window.update_mode_interface_text()
        
        # Update document dependent actions
        new_window.update_document_dependent_actions()
        
        # Show the window first
        new_window.show()
        
        # Initialize view options
        new_window.update_view_options()
        
        # Then show the setup dialog
        dialog = ScoreSetupDialog(new_window)
        if dialog.exec():
            options = dialog.get_setup_options()
            new_window.staff_view.apply_setup_options(options)
            # Update open files menu for all windows
            for window in self.windows:
                window.update_open_files_menu()
        else:
            # If dialog was cancelled, close the window
            new_window.close()
            
    def open_score(self):
        """Handle Open Score menu action"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Score",
            self.scores_directory,
            "ONOTE Files (*.otn);;All Files (*.*)"
        )
        
        if file_name:
            try:
                # Ensure .otn extension
                if not file_name.lower().endswith('.otn'):
                    file_name += '.otn'
                # Enforce single-instance per file: if already open, focus it
                normalized = os.path.abspath(file_name)
                for w in self.windows:
                    if getattr(w, 'current_file', None) and os.path.abspath(w.current_file) == normalized:
                        w.show(); w.raise_(); w.activateWindow()
                        self.statusBar.showMessage(f"Already open: {os.path.basename(file_name)} — focusing existing window", 2000)
                        return
                    
                # Create a new window for the score (WindowManager handles positioning)
                new_window = MainWindow(is_welcome_window=False)
                
                # Set up the file path and window title
                new_window.current_file = file_name
                new_window.setWindowTitle(f"ONOTE - {os.path.basename(file_name)}")
                
                # Load the document directly from JSON (matching the save format)
                if not os.path.isfile(file_name):
                    # If file doesn't exist, create a new default document
                    new_window.score_document = ScoreDocument()
                    QMessageBox.information(
                        self, 
                        "New File", 
                        f"File {os.path.basename(file_name)} does not exist. Creating a new score."
                    )
                else:
                    # Try to load the existing file using the same format as save()
                    try:
                        import json
                        with open(file_name, 'r') as f:
                            document_data = json.load(f)
                        
                        # Use ScoreDocument.from_dict() to restore the document
                        new_window.score_document = ScoreDocument.from_dict(document_data)
                        
                        # Set the filename on the document
                        new_window.score_document.filename = file_name
                        print(f"LOAD: Successfully loaded document from {file_name}")
                        
                    except Exception as e:
                        print(f"LOAD: Error loading file {file_name}: {e}")
                        # If loading fails, create a new default document
                        new_window.score_document = ScoreDocument()
                        QMessageBox.warning(
                            self, 
                            "Load Error", 
                            f"Could not load {os.path.basename(file_name)}. Created a new score instead."
                        )
                
                new_window.staff_view.set_document(new_window.score_document)
                # PATCH: Sync renderer and dialog with document settings
                if hasattr(new_window.staff_view, 'renderer') and new_window.staff_view.renderer:
                    new_window.staff_view.renderer.set_document(new_window.score_document)
                    new_window.staff_view.renderer.load_notation_settings()
                if hasattr(new_window, 'full_score_options_dialog') and new_window.full_score_options_dialog:
                    new_window.full_score_options_dialog.set_document(new_window.score_document)
                
                # Load score in edit mode
                new_window.staff_view.is_setup_mode = False
                new_window.staff_view.document.toggle_setup_mode()
                new_window.staff_view.update()
                
                # Initialize the toggle_mode_action text and visibility for opened scores (edit mode)  
                if hasattr(new_window, 'toggle_mode_action'):
                    new_window.toggle_mode_action.setText("Score Setup")
                
                # Update all interface text and visibility based on current mode (edit mode)
                new_window.update_mode_interface_text()
                
                # Update document dependent actions
                new_window.update_document_dependent_actions()
                
                # Initialize view options
                new_window.update_view_options()
                
                # Show the window
                new_window.show()
                
                # Update open files menu for all windows
                for window in self.windows:
                    window.update_open_files_menu()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open score: {str(e)}")
                
    def show_score_setup(self):
        """Handle Score Setup menu action - switch to setup mode and open the Score Setup Dialog"""
        # Check if we have a valid document before proceeding
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.information(
                self,
                "No Document Available",
                "Please create a new score or open an existing document before accessing Score Setup."
            )
            return
            
        print("MAINWINDOW: Switching to setup mode and opening Score Setup Dialog from menu")
        
        # Save state before mode transition for undo functionality
        if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'save_state'):
            current_mode = "Setup" if self.staff_view.is_setup_mode else "Edit"
            self.staff_view.document._undo_context = f"Switch from {current_mode} to Setup Mode via menu"
            self.staff_view.document.save_state(f"Switch from {current_mode} to Setup Mode via menu")
            print(f"UNDO: Saved state before switching from {current_mode} to Setup mode via menu")
        
        # If not already in setup mode, switch to setup mode first
        if not self.staff_view.is_setup_mode:
            print("MAINWINDOW: Currently in EDIT mode, switching to SETUP mode")
            
            # Set setup mode and update interface
            self.staff_view.is_setup_mode = True
            self.update_mode_interface_text()
            
            # Enter setup mode through staff_view to trigger pink background
            self.staff_view.enter_setup_mode()
            
            # Verify we actually entered setup mode
            if not self.staff_view.is_setup_mode:
                print("MAINWINDOW: ERROR - Failed to enter setup mode! Forcing mode change...")
                self.staff_view.is_setup_mode = True
                if hasattr(self.staff_view.document, 'layout'):
                    self.staff_view.document.layout.set_setup_mode(True)
                self.staff_view.update()
        else:
            print("MAINWINDOW: Already in SETUP mode")
        
        # Use WindowManager to show the Score Setup Dialog at top-right
        dialog = WindowManager.show_dialog('score_setup', ScoreSetupDialog, self)
        
        # Update status bar to indicate dialog is open
        self.statusBar.showMessage("Score Setup mode activated and dialog opened", 2000)
        
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About ONOTE",
                         "ONOTE - Object Oriented Notation by Gil Dor\n\n"
                         "Version 0.1.0\n"
                         "Copyright © 2024 Gil Dor\n\n"
                         "A modern music notation software focusing on rhythm patterns "
                         "and user-friendly note input.")
        
    def show_preferences(self):
        """Show the preferences dialog"""
        from src.gui.dialogs.preferences_dialog import PreferencesDialog
        
        # Use WindowManager to show dialog at top-right corner
        dialog = WindowManager.show_dialog('preferences', PreferencesDialog, self)
        
        # Note: Preferences dialog only affects new documents, not current document
        # No signal connection needed - settings are saved to QSettings only
        
        # Note: WindowManager shows dialog non-modally, so we handle results via signals
        
    def update_open_files_menu(self):
        """Update the Open Files menu with all open documents"""
        self.open_files_menu.clear()
        
        # Add actions for each window except the desktop
        for window in self.windows[1:]:
            if window.isVisible():
                # Create action with window title
                action = QAction(window.windowTitle(), self)
                action.triggered.connect(lambda checked, w=window: self.activate_window(w))
                self.open_files_menu.addAction(action)
                
    def activate_window(self, window):
        """Activate a specific window"""
        window.show()
        window.raise_()
        window.activateWindow()
        
    def tile_windows(self):
        """Tile all document windows using WindowManager"""
        WindowManager.tile_document_windows()
            
    def bring_all_to_front(self):
        """Bring all ONOTE windows to the front"""
        # Get all ONOTE windows and bring them to front
        for window in self.windows:
            if window.isVisible():
                window.raise_()
                window.activateWindow()
        print("Brought all ONOTE windows to front")
        
    def cascade_windows(self):
        """Cascade all document windows using WindowManager"""
        WindowManager.cascade_document_windows()
            
    def close_all_scores(self):
        """Close all score windows except the desktop"""
        # Check for unsaved changes in all windows
        for window in self.windows[1:]:  # Skip desktop window
            if not window.maybe_save():
                return
                
        # Close all document windows
        for window in self.windows[1:]:  # Skip desktop window
            window.close()
            
    def quit(self):
        """Handle application quit"""
        # First close all document windows
        self.close_all_scores()
        # Then quit the application
        QApplication.quit()
        
    # Undo/Redo functionality
    def undo(self):
        """Handle undo action with enhanced UI updates"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Simple undo system - restore from document history
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'undo'):
                # Check if document was in setup mode before undo
                was_in_setup_mode = False
                if hasattr(self.staff_view.document, 'layout') and hasattr(self.staff_view.document.layout, 'is_setup_mode'):
                    was_in_setup_mode = self.staff_view.document.layout.is_setup_mode
                
                # Perform the undo operation
                if self.staff_view.document.undo():
                    # Check if we're now in setup mode after undo
                    now_in_setup_mode = False
                    if hasattr(self.staff_view.document, 'layout') and hasattr(self.staff_view.document.layout, 'is_setup_mode'):
                        now_in_setup_mode = self.staff_view.document.layout.is_setup_mode
                    
                    # Don't automatically switch to setup mode on undo - stay in current mode
                    # The user can manually open setup mode if they want to modify the restored state
                    if now_in_setup_mode and not was_in_setup_mode:
                        print("UNDO: Detected setup mode state - keeping current edit mode (white background)")
                        # Force the document to stay in edit mode
                        if hasattr(self.staff_view.document, 'layout'):
                            self.staff_view.document.layout.set_setup_mode(False)
                            print("UNDO: Forced document layout to edit mode")
                    
                    # Force a complete document state refresh
                    print("UNDO: Starting complete document refresh sequence")
                    
                    # 1. Force document layout recalculation
                    if hasattr(self.staff_view.document, 'layout'):
                        # Clear any cached layout data
                        if hasattr(self.staff_view.document.layout, '_cached_positions'):
                            delattr(self.staff_view.document.layout, '_cached_positions')
                        # Force complete layout rebuild
                        self.staff_view.document.layout._update_positions()
                        print("UNDO: Forced layout position update and cache clear")
                    
                    # 2. Force staff view to rebuild from document
                    if hasattr(self.staff_view, 'rebuild_from_document'):
                        self.staff_view.rebuild_from_document()
                        print("UNDO: Forced staff view rebuild from document")
                    
                    # 3. Update the staff view with multiple refresh methods
                    self.staff_view.update()
                    self.staff_view.repaint()  # Force immediate repaint
                    
                    # 4. Also trigger a scheduled update to catch any delayed refreshes
                    QTimer.singleShot(50, lambda: self.staff_view.update())
                    QTimer.singleShot(100, lambda: self.staff_view.repaint())
                    print("UNDO: Forced staff view repaint with delayed updates")
                    
                    # 5. Update the mode interface
                    self.update_mode_interface_text()
                    
                    # 6. CRITICAL: Always refresh the setup widget completely
                    if MainWindow._score_setup_widget:
                        # Force complete refresh of setup widget
                        print("UNDO: Refreshing setup widget with complete rebuild")
                        MainWindow._score_setup_widget.refresh_from_document()
                        
                        # Also clear any cached dialog settings that might conflict
                        if hasattr(MainWindow._score_setup_widget, 'dialog_settings'):
                            MainWindow._score_setup_widget.dialog_settings = None
                            print("UNDO: Cleared cached dialog settings")
                        
                        # Force UI rebuild
                        MainWindow._score_setup_widget.update()
                        MainWindow._score_setup_widget.repaint()
                        print("UNDO: Forced setup widget UI refresh")
                    
                    self.statusBar.showMessage("Undo successful", 2000)
                    print("UNDO: Successfully applied undo operation with complete refresh")
                else:
                    self.statusBar.showMessage("Nothing to undo", 2000)
                    print("UNDO: No undo states available")
            else:
                self.statusBar.showMessage("Undo not available", 2000)
                print("UNDO: Document or undo method not available")
        else:
            QMessageBox.information(self, "Undo", "No active document to undo changes.")
            print("UNDO: No active staff_view available")
        
    def redo(self):
        """Handle redo action with enhanced UI updates"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Simple redo system - replay from document history
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'redo'):
                # Check if document was in setup mode before redo
                was_in_setup_mode = False
                if hasattr(self.staff_view.document, 'layout') and hasattr(self.staff_view.document.layout, 'is_setup_mode'):
                    was_in_setup_mode = self.staff_view.document.layout.is_setup_mode
                
                # Perform the redo operation
                if self.staff_view.document.redo():
                    # Check if we're now in setup mode after redo
                    now_in_setup_mode = False
                    if hasattr(self.staff_view.document, 'layout') and hasattr(self.staff_view.document.layout, 'is_setup_mode'):
                        now_in_setup_mode = self.staff_view.document.layout.is_setup_mode
                    
                    # Don't automatically switch to setup mode on redo - stay in current mode
                    # The user can manually open setup mode if they want to modify the restored state
                    if now_in_setup_mode and not was_in_setup_mode:
                        print("REDO: Detected setup mode state - keeping current edit mode (white background)")
                        # Force the document to stay in edit mode
                        if hasattr(self.staff_view.document, 'layout'):
                            self.staff_view.document.layout.set_setup_mode(False)
                            print("REDO: Forced document layout to edit mode")
                    
                    # Force a complete document state refresh
                    print("REDO: Starting complete document refresh sequence")
                    
                    # 1. Force document layout recalculation
                    if hasattr(self.staff_view.document, 'layout'):
                        # Clear any cached layout data
                        if hasattr(self.staff_view.document.layout, '_cached_positions'):
                            delattr(self.staff_view.document.layout, '_cached_positions')
                        # Force complete layout rebuild
                        self.staff_view.document.layout._update_positions()
                        print("REDO: Forced layout position update and cache clear")
                    
                    # 2. Force staff view to rebuild from document
                    if hasattr(self.staff_view, 'rebuild_from_document'):
                        self.staff_view.rebuild_from_document()
                        print("REDO: Forced staff view rebuild from document")
                    
                    # 3. Update the staff view with multiple refresh methods
                    self.staff_view.update()
                    self.staff_view.repaint()  # Force immediate repaint
                    
                    # 4. Also trigger a scheduled update to catch any delayed refreshes
                    QTimer.singleShot(50, lambda: self.staff_view.update())
                    QTimer.singleShot(100, lambda: self.staff_view.repaint())
                    print("REDO: Forced staff view repaint with delayed updates")
                    
                    # 5. Update the mode interface
                    self.update_mode_interface_text()
                    
                    # 6. CRITICAL: Always refresh the setup widget completely
                    if MainWindow._score_setup_widget:
                        # Force complete refresh of setup widget
                        print("REDO: Refreshing setup widget with complete rebuild")
                        MainWindow._score_setup_widget.refresh_from_document()
                        
                        # Also clear any cached dialog settings that might conflict
                        if hasattr(MainWindow._score_setup_widget, 'dialog_settings'):
                            MainWindow._score_setup_widget.dialog_settings = None
                            print("REDO: Cleared cached dialog settings")
                        
                        # Force UI rebuild
                        MainWindow._score_setup_widget.update()
                        MainWindow._score_setup_widget.repaint()
                        print("REDO: Forced setup widget UI refresh")
                    
                    self.statusBar.showMessage("Redo successful", 2000)
                    print("REDO: Successfully applied redo operation with complete refresh")
                else:
                    self.statusBar.showMessage("Nothing to redo", 2000)
                    print("REDO: No redo states available")
            else:
                self.statusBar.showMessage("Redo not available", 2000)
                print("REDO: Document or redo method not available")
        else:
            QMessageBox.information(self, "Redo", "No active document to redo changes.")
            print("REDO: No active staff_view available")
    def save_score(self):
        """Handle Save Score menu action"""
        if not self.current_file:
            return self.save_score_as()
            
        try:
            # Use direct JSON serialization to preserve all data
            if hasattr(self, 'score_document') and self.score_document:
                # Use the document's to_dict method for full serialization
                if hasattr(self.score_document, 'to_dict'):
                    try:
                        document_data = self.score_document.to_dict()
                        print(f"SAVE_SCORE: Using document.to_dict() for full serialization")
                    except Exception as e:
                        print(f"SAVE_SCORE: Warning - Could not use document.to_dict(): {e}")
                        # Fall back to basic data structure
                        document_data = {
                            'version': '1.0',
                            'created': str(datetime.now().isoformat()),
                            'staff_count': self.score_document.get_total_staff_count() if hasattr(self.score_document, 'get_total_staff_count') else 0
                        }
                else:
                    # Basic fallback structure
                    document_data = {
                        'version': '1.0',
                        'created': str(datetime.now().isoformat()),
                        'staff_count': 0
                    }
                
                # Write to file
                with open(self.current_file, 'w') as f:
                    json.dump(document_data, f, indent=2)
                    
                print(f"SAVE_SCORE: Successfully saved to {self.current_file}")
                self.is_modified = False
                self.update_window_title()
                self.statusBar.showMessage(f"Saved {os.path.basename(self.current_file)}")
                return True
            else:
                # No document to save, create empty file
                with open(self.current_file, 'w') as f:
                    json.dump({'version': '1.0', 'created': str(datetime.now().isoformat())}, f, indent=2)
                print(f"SAVE_SCORE: Created empty file {self.current_file}")
                self.statusBar.showMessage(f"Created {os.path.basename(self.current_file)}")
                return True
                
        except Exception as e:
            print(f"SAVE_SCORE: Error saving file: {e}")
            QMessageBox.warning(self, "Save Error", f"Could not save file: {str(e)}")
            return False
            
    def save_score_as(self):
        """Handle Save Score As menu action"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Score As",
            self.scores_directory,
            "ONOTE Files (*.otn);;All Files (*.*)"
        )
        
        if file_name:
            # Ensure .otn extension
            if not file_name.lower().endswith('.otn'):
                file_name += '.otn'
            # Capture original file to enforce close of old instance(s)
            original_file = getattr(self, 'current_file', None)
            self.current_file = file_name
            
            # If this was an untitled window, decrement the counter
            if self.untitled_number is not None:
                MainWindow._untitled_counter = max(0, MainWindow._untitled_counter - 1)
                self.untitled_number = None
            
            # Update window title with the new file name
            self.update_window_title()
            
            # Save immediately under the new name
            ok = self.save_score()
            if ok:
                # Update document.filename for downstream consumers (dialogs, renderer titles)
                if hasattr(self, 'score_document') and self.score_document:
                    self.score_document.filename = self.current_file
                # Close any other windows showing the original file (safety)
                if original_file:
                    try:
                        original_abs = os.path.abspath(original_file)
                        for w in self.windows[:]:
                            if w is self:
                                continue
                            if getattr(w, 'current_file', None) and os.path.abspath(w.current_file) == original_abs:
                                # Ask no questions per spec: close by default
                                w.close()
                    except Exception:
                        pass
                # Refresh open files menus
                for window in self.windows:
                    window.update_open_files_menu()
            return ok
        return False
        
    def import_score(self):
        """Handle Import Score menu action"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Score",
            self.scores_directory,
            "MusicXML Files (*.musicxml);;MIDI Files (*.mid);;All Files (*.*)"
        )
        
        if file_name:
            try:
                # TODO: Implement import functionality
                self.statusBar.showMessage(f"Imported {os.path.basename(file_name)}")
                return True
            except Exception as e:
                QMessageBox.warning(self, "Import Error", f"Could not import file: {str(e)}")
                return False
                
    def export_score(self):
        """Handle Export Score menu action"""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Score",
            self.scores_directory,
            "MusicXML Files (*.musicxml);;MIDI Files (*.mid);;PDF Files (*.pdf);;All Files (*.*)"
        )
        
        if file_name:
            try:
                # TODO: Implement export functionality
                self.statusBar.showMessage(f"Exported {os.path.basename(file_name)}")
                return True
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Could not export file: {str(e)}")
                return False
                
    def print_preview(self):
        """Handle Print Preview menu action"""
        # TODO: Implement print preview functionality
        QMessageBox.information(self, "Print Preview", "Print preview functionality coming soon!")
        
    def print_score(self):
        """Handle Print Score menu action"""
        # TODO: Implement print functionality
        QMessageBox.information(self, "Print", "Print functionality coming soon!")
        
    def close_active_score(self):
        """Handle Close Score menu action"""
        if self.maybe_save():
            self.close()
            
    def show_full_score_options(self):
        """Show the full score options dialog"""
        # Check if we have a valid staff_view first
        if not hasattr(self, 'staff_view') or self.staff_view is None:
            QMessageBox.warning(self, "No Score", "Please create or open a score first.")
            return
            
        from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
        
        try:
            # Create a unique dialog type per window instance to allow multiple dialogs
            dialog_type = f'full_score_options_{id(self)}'
            
            # Use WindowManager to show dialog at top-right corner
            dialog = WindowManager.show_dialog(dialog_type, FullScoreOptionsDialog, self)
            
            # Set the document on the dialog so it can load current settings
            if hasattr(self.staff_view, 'document') and self.staff_view.document:
                dialog.set_document(self.staff_view.document)
            
            # Note: With non-modal dialogs, we need to handle results via signals
            # TODO: Add signal handling for apply/cancel actions
            
        except Exception as e:
            print(f"Error showing full score options dialog: {str(e)}")
            import traceback
            traceback.print_exc()
        
    def show_parts_options(self): pass
    def show_title_options(self): pass
    def show_dynamic_parts(self): pass
    def zoom_in(self):
        """Zoom in the staff view"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Get current zoom
            current_zoom = getattr(self.staff_view, 'zoom_factor', 1.0)
            # Calculate new zoom (increase by 20%)
            new_zoom = min(current_zoom * 1.2, 4.0)
            self.apply_relative_zoom(new_zoom)
            print(f"ZOOM: Zoomed in via menu action - {int(new_zoom * 100)}%")
    
    def zoom_out(self):
        """Zoom out the staff view"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Get current zoom
            current_zoom = getattr(self.staff_view, 'zoom_factor', 1.0)
            # Calculate new zoom (decrease by 20%)
            new_zoom = max(current_zoom / 1.2, 0.25)
            self.apply_relative_zoom(new_zoom)
            print(f"ZOOM: Zoomed out via menu action - {int(new_zoom * 100)}%")
    
    def reset_zoom(self):
        """Reset zoom in the staff view"""
        if hasattr(self, 'staff_view') and self.staff_view:
            self.staff_view.reset_zoom()
            print(f"ZOOM: Reset zoom via menu action")
    
    def show_zoom_presets(self):
        """Show the zoom presets dialog"""
        if not hasattr(self, 'staff_view') or self.staff_view is None:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Score", "Please create or open a score first.")
            return
        
        from src.gui.music.dialogs.zoom_presets_dialog import ZoomPresetsDialog
        # Get current zoom from staff view
        current_zoom = getattr(self.staff_view, 'zoom_factor', 1.0)
        # Create dialog and connect signal so Apply and Preset buttons work
        dialog = ZoomPresetsDialog(self, current_zoom)
        dialog.zoom_changed.connect(self.apply_zoom_from_presets)
        dialog.show()
        
    def apply_zoom_from_presets(self, zoom_factor):
        """Apply zoom from the presets dialog"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Apply zoom factor directly
            self.apply_relative_zoom(zoom_factor)
            print(f"ZOOM: Applied zoom {int(zoom_factor * 100)}% from presets")
    
    def apply_relative_zoom(self, zoom_factor):
        """Apply zoom directly to staff view"""
        try:
            if hasattr(self, 'staff_view') and self.staff_view:
                # Apply zoom factor directly to staff view
                self.staff_view.zoom_factor = zoom_factor
                self.staff_view.update()
                
                # Update status bar
                if hasattr(self, 'statusBar') and self.statusBar():
                    self.statusBar().showMessage(f"Zoom: {int(zoom_factor * 100)}%", 2000)
                    
                print(f"ZOOM: Applied direct zoom factor {zoom_factor} to staff view")
            else:
                print(f"ZOOM: No staff view available for zoom")
        except Exception as e:
            print(f"ZOOM: Error applying zoom: {e}")
            # Fallback: try to set zoom factor directly
            try:
                if hasattr(self, 'staff_view') and self.staff_view:
                    self.staff_view.zoom_factor = zoom_factor
                    self.staff_view.update()
            except Exception as e2:
                print(f"ZOOM: Fallback also failed: {e2}")
    def show_notation_setup(self):
        """Show the notation setup dialog"""
        # Check if we have a valid staff_view first
        if not hasattr(self, 'staff_view') or self.staff_view is None:
            QMessageBox.warning(self, "No Score", "Please create or open a score first.")
            return
            
        from src.gui.music.dialogs import NotationSetupDialog
        
        try:
            # Use WindowManager to show dialog at top-right corner
            dialog = WindowManager.show_dialog('notation_setup', NotationSetupDialog, self)
            
            # Note: With non-modal dialogs, we need to handle results via signals
            # TODO: Add signal handling for apply/cancel actions
            
        except Exception as e:
            print(f"Error showing notation setup dialog: {str(e)}")
            import traceback
            traceback.print_exc()
    def show_form(self):
        """Show the Form Widget for musical form editing"""
        # Check if we have a valid staff_view and document
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.warning(self, "No Document", "Please create or open a score first.")
            return
            
        if not hasattr(self, 'form_widget') or self.form_widget is None:
            self.form_widget = FormWidget(self)
            self.form_widget.set_document(self.staff_view.document)
            
            # Connect signals
            self.form_widget.measure_modified.connect(self.handle_form_measure_modified)
            self.form_widget.measure_added.connect(self.handle_form_measure_added)
            self.form_widget.measure_deleted.connect(self.handle_form_measure_deleted)
            self.form_widget.structure_changed.connect(self.handle_form_structure_changed)
        else:
            # Form widget already exists, only sync if document has changed
            if self.form_widget.document != self.staff_view.document:
                print(f"FORM: Document changed, syncing Form Widget with new document")
                self.form_widget.set_document(self.staff_view.document)
            else:
                print(f"FORM: Document unchanged, skipping sync to preserve existing barlines")
        
        # Use WindowManager to position form widget (treating it as a dialog)
        # Position at top-right corner using WindowManager logic
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - 650  # Leave room for widget width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_dialogs = WindowManager.get_open_dialogs()
        stack_offset = len(open_dialogs) * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure widget stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        self.form_widget.move(final_x, final_y)
        self.form_widget.show()
        self.form_widget.raise_()
        self.form_widget.activateWindow()
        
        print(f"FORM: Form Widget displayed at position ({final_x}, {final_y})")

    def handle_form_structure_changed(self, measures):
        """Handle when the form structure (measures) changes"""
        print(f"FORM: Structure changed - {len(measures)} discrete measure objects")
        if hasattr(self, 'staff_view') and self.staff_view and self.staff_view.document:
            # Use the new document measure management system
            self.staff_view.document.set_measures(measures)
            self.staff_view.update()
            
    def handle_form_measure_modified(self, measure_num, properties):
        """Handle when a measure is modified"""
        print(f"FORM: Measure {measure_num} modified - {properties}")
        if hasattr(self, 'staff_view') and self.staff_view and self.staff_view.document:
            # Use the new document measure update system
            if self.staff_view.document.update_measure(measure_num, properties):
                self.staff_view.update()
                print(f"FORM: Measure {measure_num} updated successfully")
            else:
                print(f"FORM: Warning - Could not find measure {measure_num} to update")
            
    def handle_form_measure_added(self, measure_num):
        """Handle when a measure is added"""
        print(f"FORM: Measure {measure_num} added")
        if hasattr(self, 'staff_view') and self.staff_view and self.staff_view.document:
            # The Form Widget will send a new structure_changed signal with updated measures
            print(f"FORM: Waiting for structure_changed signal with new measure list")
            
    def handle_form_measure_deleted(self, measure_num):
        """Handle when a measure is deleted"""
        print(f"FORM: Measure {measure_num} deleted")
        if hasattr(self, 'staff_view') and self.staff_view and self.staff_view.document:
            # The Form Widget will send a new structure_changed signal with updated measures
            print(f"FORM: Waiting for structure_changed signal with updated measure list")
    def show_notes(self):
        """Show the Notes Widget for note editing"""
        # Check if we have a valid staff_view and document
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.warning(self, "No Document", "Please create or open a score first.")
            return
            
        if not hasattr(self, 'notes_widget') or self.notes_widget is None:
            self.notes_widget = NotesWidget(self)
            self.notes_widget.set_document(self.staff_view.document)
        else:
            # Notes widget already exists, sync if document has changed
            if self.notes_widget.document != self.staff_view.document:
                print(f"NOTES: Document changed, syncing Notes Widget with new document")
                self.notes_widget.set_document(self.staff_view.document)
        
        # Position at top-right corner using WindowManager logic
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - 400  # Leave room for widget width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_dialogs = WindowManager.get_open_dialogs()
        stack_offset = len(open_dialogs) * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure widget stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        self.notes_widget.move(final_x, final_y)
        self.notes_widget.show()
        self.notes_widget.raise_()
        self.notes_widget.activateWindow()
        
        print(f"NOTES: Notes Widget displayed at position ({final_x}, {final_y})")

    def show_rhythm(self):
        """Show the Rhythm Widget for rhythm editing"""
        # Check if we have a valid staff_view and document
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.warning(self, "No Document", "Please create or open a score first.")
            return
            
        if not hasattr(self, 'rhythm_widget') or self.rhythm_widget is None:
            self.rhythm_widget = RhythmWidget(self)
            self.rhythm_widget.set_document(self.staff_view.document)
        else:
            # Rhythm widget already exists, sync if document has changed
            if self.rhythm_widget.document != self.staff_view.document:
                print(f"RHYTHM: Document changed, syncing Rhythm Widget with new document")
                self.rhythm_widget.set_document(self.staff_view.document)
        
        # Position at top-right corner using WindowManager logic
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - 400  # Leave room for widget width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_dialogs = WindowManager.get_open_dialogs()
        stack_offset = len(open_dialogs) * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure widget stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        self.rhythm_widget.move(final_x, final_y)
        self.rhythm_widget.show()
        self.rhythm_widget.raise_()
        self.rhythm_widget.activateWindow()
        
        print(f"RHYTHM: Rhythm Widget displayed at position ({final_x}, {final_y})")

    def show_pitch(self):
        """Show the Pitch Widget for pitch editing"""
        # Check if we have a valid staff_view and document
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.warning(self, "No Document", "Please create or open a score first.")
            return
            
        if not hasattr(self, 'pitch_widget') or self.pitch_widget is None:
            self.pitch_widget = PitchWidget(self)
            self.pitch_widget.set_document(self.staff_view.document)
        else:
            # Pitch widget already exists, sync if document has changed
            if self.pitch_widget.document != self.staff_view.document:
                print(f"PITCH: Document changed, syncing Pitch Widget with new document")
                self.pitch_widget.set_document(self.staff_view.document)
        
        # Position at top-right corner using WindowManager logic
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - 400  # Leave room for widget width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_dialogs = WindowManager.get_open_dialogs()
        stack_offset = len(open_dialogs) * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure widget stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        self.pitch_widget.move(final_x, final_y)
        self.pitch_widget.show()
        self.pitch_widget.raise_()
        self.pitch_widget.activateWindow()
        
        print(f"PITCH: Pitch Widget displayed at position ({final_x}, {final_y})")

    def show_harmony(self):
        """Show the Harmony Widget for harmony editing"""
        # Check if we have a valid staff_view and document
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            QMessageBox.warning(self, "No Document", "Please create or open a score first.")
            return
            
        if not hasattr(self, 'harmony_widget') or self.harmony_widget is None:
            self.harmony_widget = HarmonyWidget(self)
            self.harmony_widget.set_document(self.staff_view.document)
        else:
            # Harmony widget already exists, sync if document has changed
            if self.harmony_widget.document != self.staff_view.document:
                print(f"HARMONY: Document changed, syncing Harmony Widget with new document")
                self.harmony_widget.set_document(self.staff_view.document)
        
        # Position at top-right corner using WindowManager logic
        screen = QApplication.primaryScreen().geometry()
        base_x = screen.width() - 400  # Leave room for widget width
        base_y = screen.y() + 50
        
        # Calculate stacking offset based on number of open dialogs
        open_dialogs = WindowManager.get_open_dialogs()
        stack_offset = len(open_dialogs) * 40
        
        final_x = base_x - stack_offset
        final_y = base_y + stack_offset
        
        # Ensure widget stays on screen
        final_x = max(50, final_x)
        final_y = max(50, final_y)
        
        self.harmony_widget.move(final_x, final_y)
        self.harmony_widget.show()
        self.harmony_widget.raise_()
        self.harmony_widget.activateWindow()
        
        print(f"HARMONY: Harmony Widget displayed at position ({final_x}, {final_y})")
    def show_documentation(self): pass
    def show_shortcuts(self): pass
    def check_for_updates(self): pass

    def maybe_save(self):
        """Check if there are unsaved changes and prompt to save if needed.
        Returns True if it's okay to continue, False if the operation should be cancelled."""
        if not self.is_modified:
            return True
            
        reply = QMessageBox.question(
            self,
            "Save Changes?",
            f"The document '{self.get_window_title()}' has been modified.\nDo you want to save your changes?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )
        
        if reply == QMessageBox.StandardButton.Save:
            return self.save()
        elif reply == QMessageBox.StandardButton.Cancel:
            return False
        return True
        
    def save(self):
        """Save the current document. Returns True if successful, False otherwise."""
        if not self.current_file:
            return self.save_as()
            
        try:
            # Basic save implementation - save document state as JSON
            if hasattr(self, 'staff_view') and self.staff_view and hasattr(self.staff_view, 'document'):
                # Create a basic document structure to save
                document_data = {
                    'version': '1.0',
                    'created': str(datetime.now().isoformat()),
                    'staff_count': self.staff_view.document.get_total_staff_count() if hasattr(self.staff_view.document, 'get_total_staff_count') else 0,
                    'layout': {
                        'continuous_view': getattr(self.staff_view.document.layout, 'continuous_view', False) if hasattr(self.staff_view.document, 'layout') else False,
                        'page_across': getattr(self.staff_view.document.layout, 'page_across', False) if hasattr(self.staff_view.document, 'layout') else False,
                        'page_down': getattr(self.staff_view.document.layout, 'page_down', False) if hasattr(self.staff_view.document, 'layout') else False
                    }
                }
                
                # Use the document's to_dict method if available for full serialization
                if hasattr(self.staff_view.document, 'to_dict'):
                    try:
                        document_data = self.staff_view.document.to_dict()
                        print(f"SAVE: Using document.to_dict() for full serialization")
                    except Exception as e:
                        print(f"SAVE: Warning - Could not use document.to_dict(): {e}")
                        # Fall back to basic data structure above
                
                # Write to file
                with open(self.current_file, 'w') as f:
                    json.dump(document_data, f, indent=2)
                    
                print(f"SAVE: Successfully saved to {self.current_file}")
                self.statusBar().showMessage(f"Saved {os.path.basename(self.current_file)}", 2000)
            else:
                # No document to save, just create an empty file
                with open(self.current_file, 'w') as f:
                    f.write('{}')
                print(f"SAVE: Created empty file {self.current_file}")
                self.statusBar().showMessage(f"Created {os.path.basename(self.current_file)}", 2000)
                
            self.is_modified = False
            self.update_window_title()
            return True
            
        except Exception as e:
            print(f"SAVE: Error saving file: {e}")
            QMessageBox.warning(self, "Save Error", f"Could not save file: {str(e)}")
            return False
            
    def save_as(self):
        """Show save dialog and save the document. Returns True if successful, False otherwise."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Score",
            self.scores_directory,
            "ONOTE Files (*.otn);;All Files (*.*)"
        )
        
        if file_name:
            # Ensure .otn extension
            if not file_name.lower().endswith('.otn'):
                file_name += '.otn'
            self.current_file = file_name
            return self.save()
        return False
        
    def get_window_title(self):
        """Get the window title based on the current file and modification state."""
        if self.is_welcome_window:
            return "ONOTE Desktop"
            
        if self.current_file:
            name = os.path.basename(self.current_file)
        else:
            # Use the same logic as when setting the window title
            if self.untitled_number == 1:
                name = "Untitled"
            else:
                name = f"Untitled {self.untitled_number}"
            
        if self.is_modified:
            name += "*"
        return name
        
    def update_window_title(self):
        """Update the window title."""
        if self.is_welcome_window:
            self.setWindowTitle("ONOTE Desktop")
        else:
            base_title = self.get_window_title()
            self.setWindowTitle(f"ONOTE - {base_title}")

    def show_page_setup(self):
        """Show the enhanced page setup dialog"""
        from PyQt6.QtWidgets import QDialog
        dialog = PageSetupDialog(self)
        
        # Connect the settings changed signal
        dialog.settings_changed.connect(self.apply_page_setup_options)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            options = dialog.get_page_options()
            self.apply_page_setup_options(options)
            self.statusBar.showMessage("Page setup updated", 2000)
            
    def apply_page_setup_options(self, options):
        """Apply page setup options to the current document"""
        if hasattr(self, 'staff_view') and self.staff_view and hasattr(self.staff_view, 'document'):
            # Update document margins and page settings
            if hasattr(self.staff_view.document, 'layout'):
                # Convert margins to pixels (approximate conversion for display)
                if options['units'] == 'mm':
                    # Rough conversion: 1mm ≈ 3.78 pixels at 96 DPI
                    margin_scale = 3.78
                else:
                    # 1 inch = 96 pixels at 96 DPI
                    margin_scale = 96
                    
                # Update layout margins
                layout = self.staff_view.document.layout
                layout.left_margin = int(options['left_margin'] * margin_scale)
                layout.right_margin = int(options['right_margin'] * margin_scale)
                layout.top_margin = int(options['top_margin'] * margin_scale)
                layout.bottom_margin = int(options['bottom_margin'] * margin_scale)
                # Recompute staff and section positions based on new top margin
                if hasattr(layout, '_update_positions'):
                    layout._update_positions()
                
                # Update renderer if available (margins and page size)
                if hasattr(self.staff_view, 'renderer') and self.staff_view.renderer:
                    self.staff_view.renderer.set_page_size(getattr(layout, 'page_width', self.staff_view.renderer.page_width),
                                                          getattr(layout, 'page_height', self.staff_view.renderer.page_height))
                    self.staff_view.renderer.set_margins({
                        'left': layout.left_margin,
                        'right': layout.right_margin,
                        'top': layout.top_margin,
                        'bottom': layout.bottom_margin
                    })
                
                # Refresh MeasureManager and BarlineTemporalBridge with new layout
                if hasattr(self.staff_view, 'measure_manager') and self.staff_view.measure_manager:
                    # Update the page layout in existing manager
                    page_width = getattr(self.staff_view.renderer, 'page_width', 800)
                    new_page_layout = PageLayout(
                        page_width=page_width,
                        left_margin=layout.left_margin,
                        right_margin=layout.right_margin,
                        top_margin=layout.top_margin,
                        bottom_margin=layout.bottom_margin
                    )
                    self.staff_view.measure_manager.page_layout = new_page_layout
                    self.staff_view.measure_manager.recalculate_complete_layout()
                    print(f"PAGE_SETUP: Updated MeasureManager page layout - right_margin={layout.right_margin}")
                
                if hasattr(self.staff_view, 'temporal_bridge') and self.staff_view.temporal_bridge:
                    # Recalculate END_BARLINE_X in temporal bridge
                    page_width = getattr(self.staff_view.renderer, 'page_width', 800)
                    right_margin = layout.right_margin
                    self.staff_view.temporal_bridge.END_BARLINE_X = page_width - right_margin
                    print(f"PAGE_SETUP: Updated temporal bridge END_BARLINE_X = {self.staff_view.temporal_bridge.END_BARLINE_X}")
                    
                    # Force recalculation of measure positions
                    if hasattr(self.staff_view.temporal_bridge, '_force_layout_refresh'):
                        self.staff_view.temporal_bridge._force_layout_refresh()
                
                # Force redraw
                self.staff_view.update()
                
                print(f"PAGE_SETUP: Applied margins - L:{layout.left_margin}, R:{layout.right_margin}, T:{layout.top_margin}")
                print(f"PAGE_SETUP: Page type: {options['page_type']}, Orientation: {options['orientation']}")
                print(f"PAGE_SETUP: Print quality: {options['print_quality']}, Resolution: {options['print_resolution']}")

            # Update QSettings if 'set_as_defaults' is in options
            if options.get('set_as_defaults', False):
                self._update_qsettings_from_page_options(options)

    def _update_qsettings_from_page_options(self, options):
        """Update QSettings with the given page layout options (for Preferences / Page Layout tab)"""
        from PyQt6.QtCore import QSettings
        qsettings = QSettings("ONOTE", "Preferences")
        # Save margins in mm
        qsettings.setValue('page_setup/left_margin_mm', options.get('left_margin', 25.0))
        qsettings.setValue('page_setup/right_margin_mm', options.get('right_margin', 25.0))
        qsettings.setValue('page_setup/top_margin_mm', options.get('top_margin', 20.0))
        qsettings.setValue('page_setup/bottom_margin_mm', options.get('bottom_margin', 20.0))
        # Save page type and orientation
        qsettings.setValue('page_setup/page_type', options.get('page_type', 'A4 (210 × 297 mm)'))
        qsettings.setValue('page_setup/orientation', options.get('orientation', 'Portrait'))
        print('QSETTINGS: Updated page layout defaults from Score / Page Setup dialog')

    def apply_notation_settings(self, settings):
        """Apply notation setup settings to the current document"""
        if hasattr(self, 'staff_view') and self.staff_view and hasattr(self.staff_view, 'document'):
            # Update renderer settings if available
            if hasattr(self.staff_view, 'renderer'):
                # Staff name settings
                self.staff_view.renderer.staff_name_font_size = settings.get('staff_name_font_size', 10)
                self.staff_view.renderer.staff_name_vertical_offset = settings.get('staff_name_vertical', -8)
                self.staff_view.renderer.staff_name_horizontal_offset = settings.get('staff_name_horizontal', -50)
                
                # Section name settings
                self.staff_view.renderer.section_name_font_size = settings.get('section_name_font_size', 12)
                self.staff_view.renderer.section_name_vertical_offset = settings.get('section_name_vertical', -25)
                self.staff_view.renderer.section_name_horizontal_offset = settings.get('section_name_horizontal', -60)
                
                # Time signature settings
                self.staff_view.renderer.time_sig_font_size = settings.get('time_sig_font_size', 24)
                self.staff_view.renderer.time_sig_vertical_offset = settings.get('time_sig_vertical', 0)
                self.staff_view.renderer.time_sig_horizontal_offset = settings.get('time_sig_horizontal', 40)
                self.staff_view.renderer.time_sig_spacing = settings.get('time_sig_spacing', 18)
                
                # Key signature settings
                self.staff_view.renderer.key_sig_font_size = settings.get('key_sig_font_size', 14)
                self.staff_view.renderer.key_sig_vertical_offset = settings.get('key_sig_vertical', 0)
                self.staff_view.renderer.key_sig_horizontal_offset = settings.get('key_sig_horizontal', 75)
                self.staff_view.renderer.key_sig_accidental_spacing = settings.get('key_sig_accidental_spacing', 12)
                
                # Musical directions settings
                self.staff_view.renderer.directions_font_size = settings.get('directions_font_size', 11)
                self.staff_view.renderer.directions_vertical_offset = settings.get('directions_vertical', 30)
                
                print(f"NOTATION_SETUP: Applied notation settings")
                
            # Update document layout settings if available
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'layout'):
                layout = self.staff_view.document.layout
                
                # Apply layout spacing settings
                if 'default_staff_spacing' in settings:
                    layout.staff_spacing = settings['default_staff_spacing']
                    print(f"NOTATION_SETUP: Applied staff spacing: {settings['default_staff_spacing']}px")
                    
                if 'default_system_spacing' in settings:
                    layout.system_spacing = settings['default_system_spacing']
                    print(f"NOTATION_SETUP: Applied system spacing: {settings['default_system_spacing']}px")
                    
                if 'default_notation_size' in settings:
                    layout.notation_size = settings['default_notation_size']
                    print(f"NOTATION_SETUP: Applied notation size: {settings['default_notation_size']}")
                    
                # Update layout positions to reflect changes
                if hasattr(layout, '_update_positions'):
                    layout._update_positions()
                
            # CRITICAL FIX: Refresh measure number manager settings
            if hasattr(self.staff_view, 'renderer') and hasattr(self.staff_view.renderer, 'measure_number_manager'):
                self.staff_view.renderer.measure_number_manager.refresh_settings()
                print("NOTATION_SETUP: Refreshed measure number manager settings")
            
            # Force redraw to show changes
            self.staff_view.update()

    def toggle_continuous_view(self):
        """Toggle continuous view mode"""
        if (hasattr(self, 'staff_view') and self.staff_view is not None and 
            hasattr(self.staff_view, 'document') and self.staff_view.document is not None):
            
            # Set continuous view mode in document
            if hasattr(self.staff_view.document, 'layout'):
                self.staff_view.document.layout.continuous_view = self.continuous_view_action.isChecked()
                
                # Disable other modes when continuous is enabled
                if self.continuous_view_action.isChecked():
                    self.page_across_action.setChecked(False)
                    self.page_down_action.setChecked(False)
                    self.staff_view.document.layout.page_across = False
                    self.staff_view.document.layout.page_down = False
                
                print(f"VIEW_MODE: Continuous view set to {self.continuous_view_action.isChecked()}")
            
            # Update renderer view mode
            if hasattr(self.staff_view, 'renderer'):
                self.staff_view.renderer.set_continuous_mode(self.continuous_view_action.isChecked())
                print(f"VIEW_MODE: Set renderer to continuous mode: {self.continuous_view_action.isChecked()}")
            
            # Update the measure manager if available
            if hasattr(self.staff_view, 'measure_manager') and self.staff_view.measure_manager:
                view_mode = "continuous" if self.continuous_view_action.isChecked() else "paginated"
                self.staff_view.measure_manager.set_view_mode(view_mode)
                print(f"VIEW_MODE: Set measure manager view mode to {view_mode}")
            
            # Update total pages for page navigation
            if hasattr(self.staff_view, 'update_total_pages'):
                self.staff_view.update_total_pages()
            
            # Force re-render
            self.staff_view.update()
        else:
            print("TOGGLE_CONTINUOUS_VIEW: Staff view or document not available")
            
    def toggle_page_across(self):
        """Toggle page across mode"""
        if (hasattr(self, 'staff_view') and self.staff_view is not None and 
            hasattr(self.staff_view, 'document') and self.staff_view.document is not None):
            
            # Set page across mode in document
            if hasattr(self.staff_view.document, 'layout'):
                self.staff_view.document.layout.page_across = self.page_across_action.isChecked()
                
                # Disable other modes when page across is enabled
                if self.page_across_action.isChecked():
                    self.continuous_view_action.setChecked(False)
                    self.page_down_action.setChecked(False)
                    self.staff_view.document.layout.continuous_view = False
                    self.staff_view.document.layout.page_down = False
                
                print(f"VIEW_MODE: Page across set to {self.page_across_action.isChecked()}")
            
            # Update renderer view mode
            if hasattr(self.staff_view, 'renderer'):
                self.staff_view.renderer.set_page_across_mode(self.page_across_action.isChecked())
                print(f"VIEW_MODE: Set renderer to page across mode: {self.page_across_action.isChecked()}")
            
            # Update total pages for page navigation
            if hasattr(self.staff_view, 'update_total_pages'):
                self.staff_view.update_total_pages()
            
            # Force re-render
            self.staff_view.update()
        else:
            print("TOGGLE_PAGE_ACROSS: Staff view or document not available")
            
    def toggle_page_down(self):
        """Toggle page down mode"""
        if (hasattr(self, 'staff_view') and self.staff_view is not None and 
            hasattr(self.staff_view, 'document') and self.staff_view.document is not None):
            
            # Set page down mode in document (this is the default mode)
            if hasattr(self.staff_view.document, 'layout'):
                self.staff_view.document.layout.page_down = self.page_down_action.isChecked()
                
                # Disable other modes when page down is enabled
                if self.page_down_action.isChecked():
                    self.continuous_view_action.setChecked(False)
                    self.page_across_action.setChecked(False)
                    self.staff_view.document.layout.continuous_view = False
                    self.staff_view.document.layout.page_across = False
                
                print(f"VIEW_MODE: Page down set to {self.page_down_action.isChecked()}")
            
            # Update renderer view mode
            if hasattr(self.staff_view, 'renderer'):
                self.staff_view.renderer.set_page_down_mode(self.page_down_action.isChecked())
                print(f"VIEW_MODE: Set renderer to page down mode: {self.page_down_action.isChecked()}")
            
            # Update total pages for page navigation
            if hasattr(self.staff_view, 'update_total_pages'):
                self.staff_view.update_total_pages()
            
            # Force re-render
            self.staff_view.update()
        else:
            print("TOGGLE_PAGE_DOWN: Staff view or document not available")
            
    def update_view_options(self):
        """Update view options menu items to match document state"""
        if (hasattr(self, 'staff_view') and self.staff_view is not None and 
            hasattr(self.staff_view, 'document') and self.staff_view.document is not None and
            hasattr(self.staff_view.document, 'layout')):
            self.continuous_view_action.setChecked(self.staff_view.document.layout.continuous_view)
            self.page_across_action.setChecked(self.staff_view.document.layout.page_across)
            self.page_down_action.setChecked(self.staff_view.document.layout.page_down)
        else:
            print("UPDATE_VIEW_OPTIONS: Staff view or document not available") 

    def closeEvent(self, event):
        """Handle window closing"""
        # If this is the desktop window (first window)
        if self == self.windows[0]:
            # Check if there are any unsaved changes in other windows
            for window in self.windows[1:]:
                if not window.maybe_save():
                    event.ignore()
                    return
            # If all windows are saved or can be closed, quit the application
            QApplication.quit()
            return
            
        # For document windows
        if self.maybe_save():
            # Remove this window from the windows list
            if self in self.windows:
                self.windows.remove(self)
                
                # Unregister from WindowManager (only for non-welcome windows)
                if not self.is_welcome_window:
                    WindowManager.unregister_document_window(self)
                
                # If this was an untitled window, decrement the counter
                if self.current_file is None and self.untitled_number is not None:
                    MainWindow._untitled_counter = max(0, MainWindow._untitled_counter - 1)
                
                # Update open files menu in remaining windows
                for window in self.windows:
                    window.update_open_files_menu()
                    
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event):
        """Handle window resize events to ensure dynamic layout responsiveness"""
        try:
            print(f"RESIZE_DEBUG: MainWindow resizeEvent called - size: {self.width()}x{self.height()}")
            super().resizeEvent(event)
            
            # Only handle resize for document windows (not welcome window)
            if self.is_welcome_window:
                print(f"RESIZE_DEBUG: Skipping resize handling for welcome window")
                return
                
            print(f"RESIZE_DEBUG: Processing resize for document window")
            
            # Check if we have a staff view and temporal bridge
            if (hasattr(self, 'staff_view') and self.staff_view and 
                hasattr(self, 'staff_view') and hasattr(self.staff_view, 'temporal_bridge') and self.staff_view.temporal_bridge):
                
                print(f"RESIZE_DEBUG: Found staff_view and temporal_bridge")
                
                # Do not mutate renderer logical page width on window resize; keep preferences
                if hasattr(self.staff_view, 'renderer') and self.staff_view.renderer:
                    print("RESIZE: Preserving renderer page width from preferences on window resize")
                
                # Force staff view update
                try:
                    self.staff_view.update()
                    print(f"RESIZE: Forced staff view update after resize")
                except Exception as e:
                    print(f"RESIZE_ERROR: Error updating staff view: {e}")
            else:
                print(f"RESIZE_DEBUG: Missing staff_view or temporal_bridge")
                if not hasattr(self, 'staff_view'):
                    print(f"RESIZE_DEBUG: No staff_view attribute")
                elif not self.staff_view:
                    print(f"RESIZE_DEBUG: staff_view is None")
                elif not hasattr(self.staff_view, 'temporal_bridge'):
                    print(f"RESIZE_DEBUG: No temporal_bridge attribute on staff_view")
                elif not self.staff_view.temporal_bridge:
                    print(f"RESIZE_DEBUG: temporal_bridge is None")
        except Exception as e:
            print(f"RESIZE_CRITICAL_ERROR: Unexpected error in resizeEvent: {e}")
            # Don't let resize errors crash the application
            super().resizeEvent(event)

    def toggle_edit_mode(self):
        """Toggle between edit mode and score setup mode"""
        print("=== TOGGLE_EDIT_MODE: Method called ===")
        # Check if we have a valid document before proceeding
        if not hasattr(self, 'staff_view') or not self.staff_view or not hasattr(self.staff_view, 'document') or not self.staff_view.document:
            print("=== TOGGLE_EDIT_MODE: No document available, showing message box ===")
            QMessageBox.information(
                self,
                "No Document Available",
                "Please create a new score or open an existing document before toggling edit mode."
            )
            return
            
        # Save state before mode transition for undo functionality
        if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'save_state'):
            current_mode = "Setup" if self.staff_view.is_setup_mode else "Edit"
            target_mode = "Edit" if self.staff_view.is_setup_mode else "Setup"
            self.staff_view.document._undo_context = f"Switch from {current_mode} to {target_mode} Mode"
            self.staff_view.document.save_state(f"Switch from {current_mode} to {target_mode} Mode")
            print(f"UNDO: Saved state before switching from {current_mode} to {target_mode} mode")
            
        if hasattr(self, 'staff_view'):
            # Get the current mode directly from staff_view
            current_mode_is_setup = self.staff_view.is_setup_mode
            
            # CRITICAL FIX: Force sync the document layout mode with the view mode
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'layout'):
                actual_doc_mode = self.staff_view.document.layout.is_setup_mode
                if actual_doc_mode != current_mode_is_setup:
                    print(f"MAINWINDOW: Mode mismatch detected! View: {current_mode_is_setup}, Doc: {actual_doc_mode}")
                    # Force sync the document mode with the view mode
                    self.staff_view.document.layout.set_setup_mode(current_mode_is_setup)
                    print(f"MAINWINDOW: Forced document layout mode to match view mode: {current_mode_is_setup}")
            
            if not current_mode_is_setup:
                # We're currently in edit mode, switching to setup mode and opening dialog
                print(f"MAINWINDOW: Currently in EDIT mode, switching to SETUP mode and opening dialog")
                
                # CRITICAL FIX: Hide the button immediately when clicked
                self.staff_view.is_setup_mode = True  # Set mode first
                self.update_mode_interface_text()     # Update interface immediately
                
                # ENHANCEMENT: Show feedback to the user
                self.statusBar.showMessage("Switching to Score Setup mode...", 2000)
                
                # Exit edit mode and enter setup mode - this will handle text/visibility updates
                self.staff_view.enter_setup_mode()
                
                # CRITICAL FIX: Double-check that we actually entered setup mode
                if not self.staff_view.is_setup_mode:
                    print("MAINWINDOW: ERROR - Failed to enter setup mode! Forcing mode change...")
                    self.staff_view.is_setup_mode = True
                    if hasattr(self.staff_view.document, 'layout'):
                        self.staff_view.document.layout.set_setup_mode(True)
                    self.staff_view.update()
                    
                    # ENHANCEMENT: Show feedback about recovery
                    self.statusBar.showMessage("Recovered from mode switching issue", 2000)
                
                # Open the score setup dialog
                self.staff_view.edit_score_setup()
            else:
                # We're already in setup mode - the button shouldn't normally be clicked in this state
                # But if it is, just ensure the dialog is open
                print(f"MAINWINDOW: Already in SETUP mode, opening dialog")
                
                # ENHANCEMENT: Show feedback to the user
                self.statusBar.showMessage("Opening Score Setup dialog...", 2000)
                
                # Open the score setup dialog
                self.staff_view.edit_score_setup()

    def enter_score_setup_mode(self):
        """Enter score setup mode"""
        active_score = None
        for window in self.windows:
            if hasattr(window, 'score_document') and window.score_document == self.active_score:
                active_score = window.score_document
                break
                
        if active_score:
            # Update button text to "Edit Mode" as clicking it will enter edit mode next time
            if hasattr(self, 'toggle_mode_action'):
                self.toggle_mode_action.setText("Edit Mode")
            active_score.enter_setup_mode()
        
    def exit_score_setup_mode(self):
        """Exit score setup mode"""
        active_score = None
        for window in self.windows:
            if hasattr(window, 'score_document') and window.score_document == self.active_score:
                active_score = window.score_document
                break
                
        if active_score:
            # Update button text to "Score Setup" as clicking it will enter setup mode next time
            if hasattr(self, 'toggle_mode_action'):
                self.toggle_mode_action.setText("Score Setup")
            active_score.exit_setup_mode()

    def update_mode_interface_text(self):
        """Update menu and toolbar text based on current mode"""
        if hasattr(self, 'staff_view'):
            current_mode_is_setup = self.staff_view.is_setup_mode
            
            if current_mode_is_setup:
                # In setup mode - show "Edit Mode" options
                menu_text = "&Edit Mode"
                toolbar_text = "Edit Mode"
                # Hide both menu action and toggle button in setup mode since Apply button handles switching
                menu_action_visible = False
                toggle_button_visible = False
            else:
                # In edit mode - show "Score Setup" options
                menu_text = "&Score Setup"
                toolbar_text = "Score Setup"
                # Show both menu action and toggle button in edit mode to allow switching to setup mode
                menu_action_visible = True
                toggle_button_visible = True
            
            # Update menu action text and visibility
            if hasattr(self, 'score_setup_action'):
                self.score_setup_action.setText(menu_text)
                self.score_setup_action.setVisible(menu_action_visible)
                print(f"MAINWINDOW: Updated menu text to '{menu_text}' and visibility to {menu_action_visible}")
            
            # Update toolbar action text and visibility
            if hasattr(self, 'toggle_mode_action'):
                self.toggle_mode_action.setText(toolbar_text)
                self.toggle_mode_action.setVisible(toggle_button_visible)
                print(f"MAINWINDOW: Updated toolbar text to '{toolbar_text}' and visibility to {toggle_button_visible}")
                
            # Update document dependent actions to ensure they're in sync
            self.update_document_dependent_actions()

    def update_document_dependent_actions(self):
        """Update document dependent actions based on the current state"""
        # Check if we have a valid document and staff_view
        has_document = (hasattr(self, 'staff_view') and self.staff_view and 
                       hasattr(self.staff_view, 'document') and self.staff_view.document is not None)
        
        # Update Score Setup action if it exists
        if hasattr(self, 'score_setup_action'):
            self.score_setup_action.setEnabled(has_document)
            if not has_document:
                self.score_setup_action.setText("&Score Setup (No Document)")
            else:
                # Restore normal text based on current mode
                if hasattr(self.staff_view, 'is_setup_mode') and self.staff_view.is_setup_mode:
                    self.score_setup_action.setText("&Edit Mode")
                else:
                    self.score_setup_action.setText("&Score Setup")
        
        # Update toolbar toggle action if it exists        
        if hasattr(self, 'toggle_mode_action'):
            self.toggle_mode_action.setEnabled(has_document) 

    def create_staff_view(self):
        """Create the main staff view widget"""
        from PyQt6.QtWidgets import QScrollArea
        self.staff_view = StaffView(self.document)
        self.staff_view.main_window = self  # Add reference for barline functionality
        # Wrap StaffView in a scroll area to provide scroll thumbs
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(False)  # Keep content size based on page/zoom
        # Show scroll thumbs so the user sees scrolling affordance
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_area.setWidget(self.staff_view)
        self.setCentralWidget(self.scroll_area)

    # Removed debug/test helpers (test_layout_refresh, check_resize_configuration)



        print("Main window initialized") 