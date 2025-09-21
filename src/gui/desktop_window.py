#!/usr/bin/env python3
"""
ONOTE Desktop Window
Page-based desktop architecture similar to Pages/Word.
Features:
- Resizable desktop with scrollable area
- Fixed-size music page that floats on desktop
- Independent page zoom while desktop resizes
- Free desktop area for floating dialogs
- Mode transitions (setup/edit) with visual feedback
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QMenuBar, QToolBar, QStatusBar, QScrollArea,
    QApplication, QFileDialog, QMessageBox,
    QDockWidget, QLabel, QFrame, QGraphicsView,
    QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsProxyWidget, QSizePolicy, QMenu, QToolButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QRectF, QPointF, QEvent
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QCloseEvent, QPainter, QBrush, QColor, QPen, QTransform
from PyQt6.QtWidgets import QGestureRecognizer, QGesture, QPinchGesture
from PyQt6.QtWidgets import QStyle

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.music.staff_view import StaffView
from src.gui.music.score_document import ScoreDocument
from src.gui.music.widgets.form_widget import FormWidget
from src.gui.dialogs.preferences_dialog import PreferencesDialog
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.music.score_setup_dialog import ScoreSetupDialog
from src.gui.music.widgets.rhythm import RhythmWidget
from src.gui.music.widgets.pitch import PitchWidget
from src.gui.music.widgets.harmony import HarmonyWidget
from src.gui.music.widgets.notes import NotesWidget
from src import __version__


class MusicPage(QGraphicsItem):
    """
    Music page that floats on the desktop.
    Similar to a page in Pages/Word with independent zoom and positioning.
    """
    
    def __init__(self, document: ScoreDocument, parent=None):
        super().__init__(parent)
        
        # Page properties
        self.document = document
        self.page_width = 800  # A4-like width
        self.page_height = 1100  # A4-like height
        self.zoom_level = 1.0
        self.mode = "edit"  # "edit" or "setup"
        
        # Visual properties
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # Page content
        self.staff_view = None
        self.form_widget = None
        self._setup_page_content()
        
        # Page appearance
        self._update_appearance()
        
    def _setup_page_content(self):
        """Setup the staff view and form widget on the page."""
        # Create staff view
        self.staff_view = StaffView()
        self.staff_view.set_document(self.document)
        self.staff_view.setFixedSize(self.page_width, self.page_height)
        
        # Create proxy widget to embed staff view in graphics scene
        self.staff_proxy = QGraphicsProxyWidget(self)
        self.staff_proxy.setWidget(self.staff_view)
        self.staff_proxy.setPos(0, 0)
        
        # Create form widget (floating on desktop, not on page)
        # Form widget will be managed by DesktopWindow
        
    def _update_appearance(self):
        """Update page appearance based on mode."""
        if self.mode == "setup":
            # Setup mode: pink background with grid (traditional ONOTE setup mode)
            self.page_color = QColor(255, 240, 245)  # Light pink
            self.border_color = QColor(255, 105, 180)  # Hot pink
            self.grid_color = QColor(255, 182, 193)  # Light pink grid
        else:
            # Edit mode: white background
            self.page_color = QColor(255, 255, 255)  # White
            self.border_color = QColor(200, 200, 200)  # Light gray
            self.grid_color = QColor(240, 240, 240)  # Very light gray grid
            
        self.update()
        
    def set_mode(self, mode: str):
        """Set page mode (edit/setup) and update appearance."""
        self.mode = mode
        self._update_appearance()
        
    def set_zoom(self, zoom_level: float):
        """Set page zoom level."""
        self.zoom_level = zoom_level
        self.setScale(zoom_level)
        
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the page."""
        return QRectF(0, 0, self.page_width, self.page_height)
        
    def paint(self, painter: QPainter, option, widget):
        """Paint the page with background, border, and grid."""
        # Set up painter
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw page background
        painter.setBrush(QBrush(self.page_color))
        painter.setPen(QPen(self.border_color, 2))
        painter.drawRect(0, 0, self.page_width, self.page_height)
        
        # Draw grid in setup mode
        if self.mode == "setup":
            painter.setPen(QPen(self.grid_color, 1))
            grid_size = 20
            
            # Vertical grid lines
            for x in range(0, self.page_width, grid_size):
                painter.drawLine(x, 0, x, self.page_height)
                
            # Horizontal grid lines
            for y in range(0, self.page_height, grid_size):
                painter.drawLine(0, y, self.page_width, y)
                
        # Draw page shadow
        shadow_offset = 5
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(shadow_offset, shadow_offset, self.page_width, self.page_height)


class DesktopWindow(QMainWindow):
    """
    Desktop window with page-based architecture.
    Features a resizable desktop with a floating music page.
    """
    
    # Signals
    document_saved = pyqtSignal(str)  # filename
    document_closed = pyqtSignal()
    page_mode_changed = pyqtSignal(str)  # "setup" or "edit"
    
    def __init__(self, app_manager=None, parent=None):
        super().__init__(parent)
        
        # Store app manager reference
        self.app_manager = app_manager
        
        # Window properties
        self.setWindowTitle("ONOTE Desktop")
        self.setMinimumSize(1200, 800)
        
        # Full screen support - keep menu visible
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)
        
        # Document state
        self.document = None
        self.filename = None
        self.is_modified = False
        
        # Page properties
        self.page_zoom = 0.81
        self.page_size = QSize(800, 1000)  # A4-like proportions
        
        # Dialog tracking
        self.score_setup_dialog = None
        
        # Setup UI
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_status_bar()
        
        # Create initial document
        self._create_new_document()
        
        # Show window just short of full screen (leave space for menu bar)
        self._setup_initial_window_size()
        self.show()
        
        # Calculate and apply optimal zoom to fill desktop height
        self._apply_optimal_zoom()
        
        # Auto-launch score setup dialog on startup
        QTimer.singleShot(500, self._auto_launch_score_setup)
        
    def _setup_ui(self):
        """Setup the main UI layout with graphics scene for draggable page."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create graphics scene for desktop
        self.desktop_scene = QGraphicsScene()
        self.desktop_scene.setSceneRect(0, 0, 3000, 3000)  # Large desktop area
        
        # Create graphics view for desktop
        self.desktop_view = QGraphicsView(self.desktop_scene)
        self.desktop_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.desktop_view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.desktop_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.desktop_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.desktop_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Enable gesture recognition for Mac 2-finger zooming
        self.desktop_view.grabGesture(Qt.GestureType.PinchGesture)
        self.desktop_view.installEventFilter(self)
        
        # Set desktop background (grid pattern)
        self.desktop_view.setStyleSheet("""
            QGraphicsView {
                background-color: #f0f0f0;
                background-image: 
                    linear-gradient(0deg, transparent 24%, rgba(0,0,0,.05) 25%, rgba(0,0,0,.05) 26%, transparent 27%, transparent 74%, rgba(0,0,0,.05) 75%, rgba(0,0,0,.05) 76%, transparent 77%, transparent),
                    linear-gradient(90deg, transparent 24%, rgba(0,0,0,.05) 25%, rgba(0,0,0,.05) 26%, transparent 27%, transparent 74%, rgba(0,0,0,.05) 75%, rgba(0,0,0,.05) 76%, transparent 77%, transparent);
                background-size: 50px 50px;
                border: none;
            }
        """)
        
        # Add graphics view to main layout
        main_layout.addWidget(self.desktop_view)
        
        # Music page will be created and added to scene when document is created
        self.music_page = None
        
    def _setup_menus(self):
        """Setup the complete menu bar with all menus and actions."""
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        # File menu
        file_menu = menubar.addMenu("&File")

        # New
        new_action = QAction("&New", self)
        new_action.setShortcut("Ctrl+N")
        new_action.setStatusTip("Create a new score")
        new_action.triggered.connect(self._file_new)
        file_menu.addAction(new_action)

        # Open
        open_action = QAction("&Open...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open an existing score")
        open_action.triggered.connect(self._file_open)
        file_menu.addAction(open_action)

        # Save
        save_action = QAction("&Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Save the current score")
        save_action.triggered.connect(self._file_save)
        file_menu.addAction(save_action)

        # Save As
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_action.setStatusTip("Save the current score with a new name")
        save_as_action.triggered.connect(self._file_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # Import
        import_action = QAction("&Import...", self)
        import_action.setStatusTip("Import a score from another format")
        import_action.triggered.connect(self._file_import)
        file_menu.addAction(import_action)

        # Export
        export_action = QAction("&Export...", self)
        export_action.setStatusTip("Export the score to another format")
        export_action.triggered.connect(self._file_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        # Print Preview
        print_preview_action = QAction("Print Pre&view...", self)
        print_preview_action.setStatusTip("Preview the score before printing")
        print_preview_action.triggered.connect(self._print_preview)
        file_menu.addAction(print_preview_action)

        # Print
        print_action = QAction("&Print...", self)
        print_action.setShortcut("Ctrl+P")
        print_action.setStatusTip("Print the current score")
        print_action.triggered.connect(self._print)
        file_menu.addAction(print_action)

        file_menu.addSeparator()

        # Close
        close_action = QAction("&Close", self)
        close_action.setShortcut("Ctrl+W")
        close_action.setStatusTip("Close this document")
        close_action.triggered.connect(self.close_document)
        file_menu.addAction(close_action)

        file_menu.addSeparator()

        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit ONOTE")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # Undo
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setStatusTip("Undo last action")
        undo_action.triggered.connect(self._edit_undo)
        edit_menu.addAction(undo_action)

        # Redo
        redo_action = QAction("&Redo", self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setStatusTip("Redo last action")
        redo_action.triggered.connect(self._edit_redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        # Toggle Edit Mode
        self.toggle_edit_mode_action = QAction("&Toggle Edit Mode", self)
        self.toggle_edit_mode_action.setShortcut("F2")
        self.toggle_edit_mode_action.setStatusTip("Toggle between edit and setup modes")
        self.toggle_edit_mode_action.triggered.connect(self._toggle_edit_mode)
        edit_menu.addAction(self.toggle_edit_mode_action)

        # Score menu
        score_menu = menubar.addMenu("&Score")
        
        # Score Setup action (toggles between setup and edit modes)
        self.score_setup_action = QAction("&Score Setup", self)
        self.score_setup_action.setStatusTip("Open score setup dialog")
        self.score_setup_action.triggered.connect(self._handle_score_setup_toggle)
        score_menu.addAction(self.score_setup_action)
        
        # Full Score Options action
        full_score_options_action = QAction("&Full Score Options", self)
        full_score_options_action.setStatusTip("Open full score options dialog")
        full_score_options_action.triggered.connect(self.open_full_score_options)
        score_menu.addAction(full_score_options_action)
        
        score_menu.addSeparator()
        
        # Notation Setup action
        notation_setup_action = QAction("&Notation Setup", self)
        notation_setup_action.setStatusTip("Open notation setup dialog")
        notation_setup_action.triggered.connect(self.open_notation_setup)
        score_menu.addAction(notation_setup_action)
        
        # Rhythm menu
        rhythm_menu = menubar.addMenu("&Rhythm")
        
        # Rhythm Pattern action
        rhythm_pattern_action = QAction("&Rhythm Pattern", self)
        rhythm_pattern_action.setStatusTip("Open rhythm pattern dialog")
        rhythm_pattern_action.triggered.connect(self.open_rhythm_pattern)
        rhythm_menu.addAction(rhythm_pattern_action)
        
        # Simple Rhythm action
        simple_rhythm_action = QAction("&Simple Rhythm", self)
        simple_rhythm_action.setStatusTip("Open simple rhythm dialog")
        simple_rhythm_action.triggered.connect(self.open_simple_rhythm)
        rhythm_menu.addAction(simple_rhythm_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # View options
        self.continuous_view_action = QAction("&Continuous View", self)
        self.continuous_view_action.setCheckable(True)
        self.continuous_view_action.setStatusTip("Toggle continuous view mode")
        self.continuous_view_action.triggered.connect(self._toggle_continuous_view)
        view_menu.addAction(self.continuous_view_action)

        self.page_across_action = QAction("Page &Across", self)
        self.page_across_action.setCheckable(True)
        self.page_across_action.setStatusTip("Toggle page across view mode")
        self.page_across_action.triggered.connect(self._toggle_page_across)
        view_menu.addAction(self.page_across_action)

        self.page_down_action = QAction("Page &Down", self)
        self.page_down_action.setCheckable(True)
        self.page_down_action.setChecked(True)  # Default
        self.page_down_action.setStatusTip("Toggle page down view mode")
        self.page_down_action.triggered.connect(self._toggle_page_down)
        view_menu.addAction(self.page_down_action)

        view_menu.addSeparator()

        # Zoom In
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.setStatusTip("Zoom in on the page")
        zoom_in_action.triggered.connect(self._zoom_in)
        view_menu.addAction(zoom_in_action)

        # Zoom Out
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.setStatusTip("Zoom out on the page")
        zoom_out_action.triggered.connect(self._zoom_out)
        view_menu.addAction(zoom_out_action)

        # Reset Zoom
        reset_zoom_action = QAction("Reset &Zoom", self)
        reset_zoom_action.setShortcut("Ctrl+0")
        reset_zoom_action.setStatusTip("Reset zoom to 100%")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        view_menu.addAction(reset_zoom_action)

        # --- Zoom Presets menu for manual zoom selection ---
        zoom_menu = QMenu("Zoom Presets", self)
        self.menu_zoom_actions = []  # Separate zoom actions for menu
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_zoom_level(v))
            zoom_menu.addAction(act)
            self.menu_zoom_actions.append((act, value))
        view_menu.addMenu(zoom_menu)

        view_menu.addSeparator()

        # Window arrangement options
        tile_action = QAction("&Tile Windows", self)
        tile_action.setStatusTip("Tile all open windows")
        tile_action.triggered.connect(self._tile_windows)
        view_menu.addAction(tile_action)

        cascade_action = QAction("&Cascade Windows", self)
        cascade_action.setStatusTip("Cascade all open windows")
        cascade_action.triggered.connect(self._cascade_windows)
        view_menu.addAction(cascade_action)

        view_menu.addSeparator()

        # Open Files submenu
        self.open_files_menu = view_menu.addMenu("&Currently Open")

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        # Form
        form_action = QAction("&Form", self)
        form_action.setStatusTip("Show/hide form widget")
        form_action.triggered.connect(self._show_form)
        tools_menu.addAction(form_action)

        # Notes
        notes_action = QAction("&Notes", self)
        notes_action.setStatusTip("Show/hide notes widget")
        notes_action.triggered.connect(self._show_notes)
        tools_menu.addAction(notes_action)

        # Rhythm
        rhythm_action = QAction("&Rhythm", self)
        rhythm_action.setStatusTip("Show/hide rhythm widget")
        rhythm_action.triggered.connect(self._show_rhythm)
        tools_menu.addAction(rhythm_action)

        # Pitch
        pitch_action = QAction("&Pitch", self)
        pitch_action.setStatusTip("Show/hide pitch widget")
        pitch_action.triggered.connect(self._show_pitch)
        tools_menu.addAction(pitch_action)

        # Harmony
        harmony_action = QAction("&Harmony", self)
        harmony_action.setStatusTip("Show/hide harmony widget")
        harmony_action.triggered.connect(self._show_harmony)
        tools_menu.addAction(harmony_action)

        tools_menu.addSeparator()

        # Preferences
        preferences_action = QAction("&Preferences...", self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Open preferences dialog")
        preferences_action.triggered.connect(self.open_preferences)
        tools_menu.addAction(preferences_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # Documentation
        documentation_action = QAction("&Documentation", self)
        documentation_action.setShortcut("F1")
        documentation_action.setStatusTip("Open documentation")
        documentation_action.triggered.connect(self._show_documentation)
        help_menu.addAction(documentation_action)

        # Keyboard Shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("Ctrl+/")
        shortcuts_action.setStatusTip("Show keyboard shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        help_menu.addSeparator()

        # Check for Updates
        updates_action = QAction("Check for &Updates", self)
        updates_action.setStatusTip("Check for ONOTE updates")
        updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(updates_action)

        # About
        about_action = QAction("&About", self)
        about_action.setStatusTip("About ONOTE")
        about_action.triggered.connect(self.open_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Setup the toolbar with common actions."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setMovable(True)
        
        # File actions
        toolbar.addAction(self.findChild(QAction, "&New"))
        toolbar.addAction(self.findChild(QAction, "&Open..."))
        toolbar.addAction(self.findChild(QAction, "&Save"))
        toolbar.addSeparator()
        
        # Edit actions
        toolbar.addAction(self.findChild(QAction, "&Undo"))
        toolbar.addAction(self.findChild(QAction, "&Redo"))
        toolbar.addSeparator()
        
        # View actions
        toolbar.addAction(self.findChild(QAction, "Page &Down"))
        toolbar.addAction(self.findChild(QAction, "Page &Across"))
        toolbar.addAction(self.findChild(QAction, "&Continuous View"))
        toolbar.addSeparator()
        
        # Zoom actions
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        zoom_in_action.setStatusTip("Zoom in on the page")
        zoom_in_action.triggered.connect(self._zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        zoom_out_action.setStatusTip("Zoom out on the page")
        zoom_out_action.triggered.connect(self._zoom_out)
        toolbar.addAction(zoom_out_action)
        
        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        reset_zoom_action.setStatusTip("Reset zoom to 100%")
        reset_zoom_action.triggered.connect(self._reset_zoom)
        toolbar.addAction(reset_zoom_action)

        # --- Zoom Presets menu/button for manual zoom selection ---
        zoom_menu = QMenu("Zoom Presets", self)
        self.toolbar_zoom_actions = []  # Separate zoom actions for toolbar
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_zoom_level(v))
            zoom_menu.addAction(act)
            self.toolbar_zoom_actions.append((act, value))
        zoom_tool_btn = QToolButton()
        zoom_tool_btn.setText("Zoom Presets")
        zoom_tool_btn.setMenu(zoom_menu)
        zoom_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        toolbar.addWidget(zoom_tool_btn)

        toolbar.addSeparator()
        
        # Notation tools
        clef_action = QAction("Clef", self)
        clef_action.setStatusTip("Insert clef")
        clef_action.triggered.connect(self._insert_clef)
        toolbar.addAction(clef_action)
        
        time_sig_action = QAction("Time Signature", self)
        time_sig_action.setStatusTip("Insert time signature")
        time_sig_action.triggered.connect(self._insert_time_signature)
        toolbar.addAction(time_sig_action)
        
        key_sig_action = QAction("Key Signature", self)
        key_sig_action.setStatusTip("Insert key signature")
        key_sig_action.triggered.connect(self._insert_key_signature)
        toolbar.addAction(key_sig_action)
        
        note_action = QAction("Note", self)
        note_action.setStatusTip("Insert note")
        note_action.triggered.connect(self._insert_note)
        toolbar.addAction(note_action)
        
        rest_action = QAction("Rest", self)
        rest_action.setStatusTip("Insert rest")
        rest_action.triggered.connect(self._insert_rest)
        toolbar.addAction(rest_action)

    def _setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_initial_window_size(self):
        """Setup window to launch just short of full screen with menu accessible."""
        # Get screen geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Calculate window size (leave 50px at top for menu bar visibility)
        window_width = screen_geometry.width()
        window_height = screen_geometry.height() - 50  # Leave space for menu
        
        # Set window geometry
        self.setGeometry(0, 0, window_width, window_height)
        
        # Position window at top-left of screen
        self.move(0, 0)
        
    def _create_new_document(self):
        """Create a new document and setup the page."""
        # Create new document
        self.document = ScoreDocument()
        self.filename = None
        self.is_modified = False
        
        # Create music page
        self.music_page = MusicPage(self.document)
        # Position page on the left side of desktop
        self.music_page.setPos(100, 200)  # Left side positioning
        
        # Add page to scene
        self.desktop_scene.addItem(self.music_page)
        
        # Start in setup mode (pink page)
        self._enter_setup_mode()
        
        # Center view on page
        self.desktop_view.centerOn(self.music_page)
        
        # Update window title
        self._update_window_title()

    def _update_window_title(self):
        """Update the window title based on current state."""
        title = "ONOTE Desktop"
        if self.filename:
            title = f"ONOTE - {os.path.basename(self.filename)}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)

    # File menu actions
    def _file_new(self):
        """Create a new document."""
        if self.app_manager:
            self.app_manager.create_new_window()

    def _file_open(self):
        """Open an existing document."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open ONOTE File", "", 
            "ONOTE Files (*.onote);;All Files (*)"
        )
        if filename:
            if self.app_manager:
                self.app_manager.open_document(filename)

    def _file_save(self):
        """Save the current document."""
        if self.filename:
            self._save_to_file(self.filename)
        else:
            self._file_save_as()

    def _file_save_as(self):
        """Save the current document with a new name."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save ONOTE File As", "", 
            "ONOTE Files (*.onote);;All Files (*)"
        )
        if filename:
            self.filename = filename
            return self.save_document()
        return False

    def _file_import(self):
        """Import a document from another format."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import File", "", 
            "MusicXML Files (*.musicxml);;MIDI Files (*.mid);;All Files (*)"
        )
        if filename:
            # TODO: Implement import functionality
            self.status_bar.showMessage(f"Import functionality coming soon: {os.path.basename(filename)}")

    def _file_export(self):
        """Export the document to another format."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export File", "", 
            "MusicXML Files (*.musicxml);;MIDI Files (*.mid);;PDF Files (*.pdf);;All Files (*)"
        )
        if filename:
            # TODO: Implement export functionality
            self.status_bar.showMessage(f"Export functionality coming soon: {os.path.basename(filename)}")

    def _print_preview(self):
        """Show print preview."""
        # TODO: Implement print preview
        QMessageBox.information(self, "Print Preview", "Print preview functionality coming soon!")

    def _print(self):
        """Print the document."""
        # TODO: Implement print functionality
        QMessageBox.information(self, "Print", "Print functionality coming soon!")

    # Edit menu actions
    def _edit_undo(self):
        """Undo last action."""
        if self.document and hasattr(self.document, 'undo'):
            self.document.undo()
            self.status_bar.showMessage("Undo")

    def _edit_redo(self):
        """Redo last action."""
        if self.document and hasattr(self.document, 'redo'):
            self.document.redo()
            self.status_bar.showMessage("Redo")

    def _toggle_edit_mode(self):
        """Toggle between edit and setup modes."""
        if self.music_page:
            current_mode = self.music_page.mode
            new_mode = "setup" if current_mode == "edit" else "edit"
            
            if new_mode == "setup":
                self._enter_setup_mode()
            else:
                self._enter_edit_mode()
                
            # Emit signal
            self.page_mode_changed.emit(new_mode)
            
            # Update status
            self.status_bar.showMessage(f"Switched to {new_mode} mode")
            
    def _enter_setup_mode(self):
        """Enter setup mode (pink page)."""
        if self.music_page and self.music_page.staff_view:
            # Set page to setup mode
            self.music_page.set_mode("setup")
            
            # Enter setup mode in staff view
            self.music_page.staff_view.enter_setup_mode()
            
            # Update menu text
            self.toggle_edit_mode_action.setText("&Toggle Edit Mode")
            self._update_score_setup_action_text()
            
            # Update status
            self.status_bar.showMessage("Setup mode - configure your score")
            
    def _enter_edit_mode(self):
        """Enter edit mode (white page)."""
        if self.music_page and self.music_page.staff_view:
            # Set page to edit mode
            self.music_page.set_mode("edit")
            
            # Enter edit mode in staff view
            self.music_page.staff_view.enter_edit_mode()
            
            # Update menu text
            self.toggle_edit_mode_action.setText("&Toggle Setup Mode")
            self._update_score_setup_action_text()
            
            # Update status
            self.status_bar.showMessage("Edit mode - ready for notation")

    # Score menu actions
    def _page_setup(self):
        """Open page setup dialog."""
        # TODO: Implement page setup dialog
        QMessageBox.information(self, "Page Setup", "Page setup functionality coming soon!")

    def _parts_options(self):
        """Open parts options dialog."""
        # TODO: Implement parts options dialog
        QMessageBox.information(self, "Parts Options", "Parts options functionality coming soon!")

    def _add_title_header_footer(self):
        """Add title, header, and footer dialog."""
        # TODO: Implement title/header/footer dialog
        QMessageBox.information(self, "Add Title/Header/Footer", "Title/header/footer functionality coming soon!")

    def _dynamic_parts(self):
        """Dynamic parts dialog."""
        # TODO: Implement dynamic parts dialog
        QMessageBox.information(self, "Dynamic Parts", "Dynamic parts functionality coming soon!")

    def _notation_setup(self):
        """Open the notation setup dialog."""
        from src.gui.music.dialogs.notation_setup_dialog import NotationSetupDialog
        dialog = NotationSetupDialog(self)
        dialog.exec()

    # View menu actions
    def _toggle_continuous_view(self):
        """Toggle continuous view mode."""
        self.continuous_view_action.setChecked(not self.continuous_view_action.isChecked())
        # TODO: Implement continuous view

    def _toggle_page_across(self):
        """Toggle page across view mode."""
        self.page_across_action.setChecked(not self.page_across_action.isChecked())
        # TODO: Implement page across view

    def _toggle_page_down(self):
        """Toggle page down view mode."""
        self.page_down_action.setChecked(not self.page_down_action.isChecked())
        # TODO: Implement page down view

    def _zoom_in(self):
        """Zoom in on the page."""
        self.page_zoom = min(self.page_zoom * 1.2, 3.0)
        self._apply_zoom()

    def _zoom_out(self):
        """Zoom out on the page."""
        self.page_zoom = max(self.page_zoom / 1.2, 0.3)
        self._apply_zoom()

    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.page_zoom = 0.81
        self._apply_zoom()

    def _apply_zoom(self):
        """Apply the current zoom level to the page."""
        if self.music_page:
            self.music_page.set_zoom(self.page_zoom)
            
            # Center the view on the music page after zooming
            self.desktop_view.centerOn(self.music_page)
            
            # Update status bar with zoom percentage
            self.status_bar.showMessage(f"Zoom: {int(self.page_zoom * 100)}%")

    def _tile_windows(self):
        """Tile all open windows."""
        if self.app_manager:
            self.app_manager.tile_windows()

    def _cascade_windows(self):
        """Cascade all open windows."""
        if self.app_manager:
            self.app_manager.cascade_windows()

    # Tools menu actions
    def _show_form(self):
        """Show/hide form widget."""
        if not hasattr(self, 'form_widget') or not self.form_widget:
            # Create form widget
            self.form_widget = FormWidget(self)
            
            # Create dock widget
            self.form_dock = QDockWidget("Musical Form", self)
            self.form_dock.setWidget(self.form_widget)
            self.form_dock.setFloating(True)
            self.form_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.form_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            
            # Add dock to window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.form_dock)
            
            # Position the dock widget to the right of the page
            if hasattr(self, 'music_page') and self.music_page:
                page_pos = self.music_page.pos()
                page_width = self.music_page.page_width
                dock_x = page_pos.x() + page_width + 20
                dock_y = page_pos.y() + 50
                self.form_dock.move(int(dock_x), int(dock_y))
            
            # Connect form widget to staff view if available
            if hasattr(self, 'music_page') and self.music_page and self.music_page.staff_view:
                # Set the document for the form widget
                self.form_widget.set_document(self.music_page.staff_view.document)
                
                # Integrate with temporal bridge if available
                if hasattr(self.music_page.staff_view, 'temporal_bridge'):
                    from src.gui.music.barline_temporal_bridge import integrate_bridge_with_form_widget
                    integrate_bridge_with_form_widget(self.form_widget, self.music_page.staff_view.temporal_bridge)
            
            self.status_bar.showMessage("Form widget opened")
        else:
            # Toggle visibility
            if self.form_dock.isVisible():
                self.form_dock.hide()
                self.status_bar.showMessage("Form widget hidden")
            else:
                self.form_dock.show()
                self.form_dock.raise_()
                self.status_bar.showMessage("Form widget shown")

    def _show_notes(self):
        """Show/hide notes widget."""
        if not hasattr(self, 'notes_widget') or not self.notes_widget:
            # Create notes widget
            self.notes_widget = NotesWidget(self)
            
            # Create dock widget
            self.notes_dock = QDockWidget("Notes", self)
            self.notes_dock.setWidget(self.notes_widget)
            self.notes_dock.setFloating(True)
            self.notes_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.notes_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            
            # Add dock to window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.notes_dock)
            
            # Position the dock widget
            if hasattr(self, 'music_page') and self.music_page:
                page_pos = self.music_page.pos()
                page_width = self.music_page.page_width
                dock_x = page_pos.x() + page_width + 20
                dock_y = page_pos.y() + 200
                self.notes_dock.move(int(dock_x), int(dock_y))
            
            self.status_bar.showMessage("Notes widget opened")
        else:
            # Toggle visibility
            if self.notes_dock.isVisible():
                self.notes_dock.hide()
                self.status_bar.showMessage("Notes widget hidden")
            else:
                self.notes_dock.show()
                self.notes_dock.raise_()
                self.status_bar.showMessage("Notes widget shown")

    def _show_rhythm(self):
        """Show/hide rhythm widget."""
        if not hasattr(self, 'rhythm_widget') or not self.rhythm_widget:
            # Create rhythm widget
            self.rhythm_widget = RhythmWidget(self)
            
            # Create dock widget
            self.rhythm_dock = QDockWidget("Rhythm", self)
            self.rhythm_dock.setWidget(self.rhythm_widget)
            self.rhythm_dock.setFloating(True)
            self.rhythm_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.rhythm_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            
            # Add dock to window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.rhythm_dock)
            
            # Position the dock widget
            if hasattr(self, 'music_page') and self.music_page:
                page_pos = self.music_page.pos()
                page_width = self.music_page.page_width
                dock_x = page_pos.x() + page_width + 20
                dock_y = page_pos.y() + 350
                self.rhythm_dock.move(int(dock_x), int(dock_y))
            
            self.status_bar.showMessage("Rhythm widget opened")
        else:
            # Toggle visibility
            if self.rhythm_dock.isVisible():
                self.rhythm_dock.hide()
                self.status_bar.showMessage("Rhythm widget hidden")
            else:
                self.rhythm_dock.show()
                self.rhythm_dock.raise_()
                self.status_bar.showMessage("Rhythm widget shown")

    def _show_pitch(self):
        """Show/hide pitch widget."""
        if not hasattr(self, 'pitch_widget') or not self.pitch_widget:
            # Create pitch widget
            self.pitch_widget = PitchWidget(self)
            
            # Create dock widget
            self.pitch_dock = QDockWidget("Pitch", self)
            self.pitch_dock.setWidget(self.pitch_widget)
            self.pitch_dock.setFloating(True)
            self.pitch_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.pitch_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            
            # Add dock to window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.pitch_dock)
            
            # Position the dock widget
            if hasattr(self, 'music_page') and self.music_page:
                page_pos = self.music_page.pos()
                page_width = self.music_page.page_width
                dock_x = page_pos.x() + page_width + 20
                dock_y = page_pos.y() + 500
                self.pitch_dock.move(int(dock_x), int(dock_y))
            
            self.status_bar.showMessage("Pitch widget opened")
        else:
            # Toggle visibility
            if self.pitch_dock.isVisible():
                self.pitch_dock.hide()
                self.status_bar.showMessage("Pitch widget hidden")
            else:
                self.pitch_dock.show()
                self.pitch_dock.raise_()
                self.status_bar.showMessage("Pitch widget shown")

    def _show_harmony(self):
        """Show/hide harmony widget."""
        if not hasattr(self, 'harmony_widget') or not self.harmony_widget:
            # Create harmony widget
            self.harmony_widget = HarmonyWidget(self)
            
            # Create dock widget
            self.harmony_dock = QDockWidget("Harmony", self)
            self.harmony_dock.setWidget(self.harmony_widget)
            self.harmony_dock.setFloating(True)
            self.harmony_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            self.harmony_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            
            # Add dock to window
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.harmony_dock)
            
            # Position the dock widget
            if hasattr(self, 'music_page') and self.music_page:
                page_pos = self.music_page.pos()
                page_width = self.music_page.page_width
                dock_x = page_pos.x() + page_width + 20
                dock_y = page_pos.y() + 650
                self.harmony_dock.move(int(dock_x), int(dock_y))
            
            self.status_bar.showMessage("Harmony widget opened")
        else:
            # Toggle visibility
            if self.harmony_dock.isVisible():
                self.harmony_dock.hide()
                self.status_bar.showMessage("Harmony widget hidden")
            else:
                self.harmony_dock.show()
                self.harmony_dock.raise_()
                self.status_bar.showMessage("Harmony widget shown")

    # Help menu actions
    def _show_documentation(self):
        """Show documentation."""
        QMessageBox.information(self, "Documentation", "Documentation coming soon!")

    def _show_shortcuts(self):
        """Show keyboard shortcuts."""
        QMessageBox.information(self, "Keyboard Shortcuts", "Keyboard shortcuts reference coming soon!")

    def _check_for_updates(self):
        """Check for updates."""
        QMessageBox.information(self, "Check for Updates", "Update checking functionality coming soon!")

    def _show_about(self):
        """Open the about dialog."""
        QMessageBox.about(self, "About ONOTE", 
                         "ONOTE - Music Notation Software\n\n"
                         "Version: 2.0.0\n"
                         "A modern, page-based music notation editor\n\n"
                         "Features:\n"
                         "• Multi-window architecture\n"
                         "• Page-based desktop layout\n"
                         "• Professional music notation\n"
                         "• Real-time editing\n"
                         "• Comprehensive dialog system")

    # Document methods
    def save_document(self) -> bool:
        """Save the current document."""
        if not self.filename:
            return self.save_document_as()
            
        # Save logic here
        self.is_modified = False
        self._update_window_title()
        self.document_saved.emit(self.filename)
        return True
        
    def save_document_as(self) -> bool:
        """Save the current document with a new name."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save ONOTE File As", "", "ONOTE Files (*.onote);;All Files (*)"
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
                
        self.document_closed.emit()
        self.close()
        
    # Dialog methods
    def open_score_setup(self):
        """Open the score setup dialog."""
        from src.gui.music.score_setup_dialog import ScoreSetupDialog
        
        # Ensure we're in setup mode before opening dialog
        if self.music_page and self.music_page.mode != "setup":
            self._enter_setup_mode()
        
        # Create and show the dialog
        print(f"[DEBUG] DesktopWindow creating ScoreSetupDialog, parent type: {type(self)}")
        dialog = ScoreSetupDialog(self)
        
        # Store dialog reference
        self.score_setup_dialog = dialog
        
        # Position dialog to the right of the page
        self._position_dialog_right_of_page(dialog)
        
        # Connect dialog signals to handle completion
        dialog.setup_widget.setup_completed.connect(self._on_score_setup_completed)
        
        # Show dialog modelessly (allows multiple dialogs)
        dialog.show()
        
        # Update status
        self.status_bar.showMessage("Score setup dialog opened")

    def _handle_score_setup_toggle(self):
        """Handle score setup action toggle between setup and edit modes."""
        if self.music_page and self.music_page.mode == "setup":
            # Currently in setup mode, switch to edit mode
            # Close any open score setup dialog first
            if self.score_setup_dialog and self.score_setup_dialog.isVisible():
                self.score_setup_dialog.close()
                self.score_setup_dialog = None
            
            self._enter_edit_mode()
            self.status_bar.showMessage("Switched to edit mode")
        else:
            # Currently in edit mode, open score setup dialog
            self.open_score_setup()
            
    def _update_score_setup_action_text(self):
        """Update the score setup action text based on current mode."""
        if self.music_page and self.music_page.mode == "setup":
            self.score_setup_action.setText("&Edit Mode")
            self.score_setup_action.setStatusTip("Switch to edit mode")
        else:
            self.score_setup_action.setText("&Score Setup")
            self.score_setup_action.setStatusTip("Open score setup dialog")
            
    def _auto_launch_score_setup(self):
        """Auto-launch score setup dialog on startup."""
        if self.music_page and self.music_page.mode == "setup":
            self.open_score_setup()
            
    def _on_score_setup_completed(self):
        """Handle completion of score setup."""
        # Switch to edit mode
        self._enter_edit_mode()
        
        # Update status
        self.status_bar.showMessage("Score setup complete - switched to edit mode")
        
        # Emit signal
        self.page_mode_changed.emit("edit")
            
    def open_full_score_options(self):
        """Open the full score options dialog."""
        from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
        dialog = FullScoreOptionsDialog(self)
        
        # Set the document on the dialog so it can load current settings
        if hasattr(self, 'music_page') and self.music_page and hasattr(self.music_page, 'staff_view') and self.music_page.staff_view.document:
            dialog.set_document(self.music_page.staff_view.document)
        
        self._position_dialog_right_of_page(dialog)
        dialog.show()
        self.status_bar.showMessage("Full score options dialog opened")

    def _save_to_file(self, filename: str):
        """Save document to file."""
        # TODO: Implement actual file saving
        self.is_modified = False
        self._update_window_title()
        self.status_bar.showMessage(f"Saved: {os.path.basename(filename)}")

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
                
        # Close the window
        event.accept() 

    def open_notation_setup(self):
        """Open the notation setup dialog."""
        from src.gui.music.dialogs.notation_setup_dialog import NotationSetupDialog
        dialog = NotationSetupDialog(self)
        self._position_dialog_right_of_page(dialog)
        dialog.show()
        self.status_bar.showMessage("Notation setup dialog opened")
        
    def open_rhythm_pattern(self):
        """Open the rhythm pattern dialog."""
        from src.gui.music.dialogs.rhythm_dialogs import RhythmPatternDialog
        dialog = RhythmPatternDialog(self)
        dialog.pattern_selected.connect(self.on_rhythm_pattern_selected)
        self._position_dialog_right_of_page(dialog)
        dialog.show()
        self.status_bar.showMessage("Rhythm pattern dialog opened")
        
    def open_simple_rhythm(self):
        """Open the simple rhythm dialog."""
        from src.gui.music.dialogs.rhythm_dialogs import SimpleRhythmDialog
        dialog = SimpleRhythmDialog(self)
        dialog.note_selected.connect(self.on_note_selected)
        self._position_dialog_right_of_page(dialog)
        dialog.show()
        self.status_bar.showMessage("Simple rhythm dialog opened")
        
    def on_rhythm_pattern_selected(self, pattern):
        """Handle rhythm pattern selection."""
        self.status_bar.showMessage(f"Rhythm pattern selected: {pattern}")
        
    def on_note_selected(self, note_symbol):
        """Handle note selection."""
        self.status_bar.showMessage(f"Note selected: {note_symbol}")
        
    def _insert_clef(self):
        """Insert a clef at the current position."""
        self.status_bar.showMessage("Insert clef - functionality coming soon!")
        
    def _insert_time_signature(self):
        """Insert a time signature at the current position."""
        self.status_bar.showMessage("Insert time signature - functionality coming soon!")
        
    def _insert_key_signature(self):
        """Insert a key signature at the current position."""
        self.status_bar.showMessage("Insert key signature - functionality coming soon!")
        
    def _insert_note(self):
        """Insert a note at the current position."""
        self.status_bar.showMessage("Insert note - functionality coming soon!")
        
    def _insert_rest(self):
        """Insert a rest at the current position."""
        self.status_bar.showMessage("Insert rest - functionality coming soon!")

    # Rename method

    
    def open_about(self):
        """Open the about dialog."""
        QMessageBox.about(self, "About ONOTE", 
                         "ONOTE - Music Notation Software\n\n"
                         "Version: 2.0.0\n"
                         "A modern, page-based music notation editor\n\n"
                         "Features:\n"
                         "• Multi-window architecture\n"
                         "• Page-based desktop layout\n"
                         "• Professional music notation\n"
                         "• Real-time editing\n"
                         "• Comprehensive dialog system")
    
    def eventFilter(self, obj, event):
        """Event filter to handle gesture events for Mac 2-finger zooming."""
        if obj == self.desktop_view:
            if event.type() == QEvent.Type.Gesture:
                gesture_event = event
                pinch_gesture = gesture_event.gesture(Qt.GestureType.PinchGesture)
                if pinch_gesture:
                    self._handle_pinch_gesture(pinch_gesture)
                    return True
        return super().eventFilter(obj, event)
    
    def _handle_pinch_gesture(self, pinch_gesture):
        """Handle pinch gesture for zooming the music page."""
        if not self.music_page:
            return
            
        # Get the gesture center point in viewport coordinates
        gesture_center = pinch_gesture.centerPoint()
        viewport_pos = gesture_center.toPoint()
        
        # Convert viewport coordinates to scene coordinates
        scene_pos = self.desktop_view.mapToScene(viewport_pos)
        
        # Get the music page's bounding rectangle in scene coordinates
        page_rect = self.music_page.boundingRect()
        page_scene_rect = self.music_page.mapRectToScene(page_rect)
        
        # Add some tolerance for easier gesture detection
        tolerance = 20  # pixels
        expanded_rect = page_scene_rect.adjusted(-tolerance, -tolerance, tolerance, tolerance)
        
        # Only apply zoom if gesture is over the music page (with tolerance)
        if not expanded_rect.contains(scene_pos):
            # Gesture is not over the page, ignore it
            return
            
        # Get the scale factor from the pinch gesture
        scale_factor = pinch_gesture.scaleFactor()
        
        # Calculate new zoom level
        new_zoom = self.page_zoom * scale_factor
        
        # Clamp zoom to reasonable bounds (30% to 300%)
        new_zoom = max(0.3, min(3.0, new_zoom))
        
        # Apply zoom if it changed significantly
        if abs(new_zoom - self.page_zoom) > 0.01:
            # Store the center point before zooming
            old_center = self.desktop_view.mapToScene(self.desktop_view.viewport().rect().center())
            
            # Apply the new zoom
            self.page_zoom = new_zoom
            self._apply_zoom()
            
            # Calculate the new center point to maintain zoom center
            new_center = self.desktop_view.mapToScene(self.desktop_view.viewport().rect().center())
            
            # Adjust the view to maintain the zoom center
            offset = new_center - old_center
            self.desktop_view.horizontalScrollBar().setValue(
                self.desktop_view.horizontalScrollBar().value() + int(offset.x())
            )
            self.desktop_view.verticalScrollBar().setValue(
                self.desktop_view.verticalScrollBar().value() + int(offset.y())
            )
            
            # Update status bar with zoom percentage
            self.status_bar.showMessage(f"Page Zoom: {int(self.page_zoom * 100)}%")
            
            # Update zoom action check states
            for act, value in self.menu_zoom_actions:
                act.setChecked(abs(self.page_zoom - value) < 0.01)
            for act, value in self.toolbar_zoom_actions:
                act.setChecked(abs(self.page_zoom - value) < 0.01)
    
    def event(self, event):
        """Override event method to handle gesture events."""
        if event.type() == QEvent.Type.Gesture:
            # Handle gesture events at the window level
            pinch_gesture = event.gesture(Qt.GestureType.PinchGesture)
            if pinch_gesture:
                self._handle_pinch_gesture(pinch_gesture)
                return True
        return super().event(event)
    
    def _set_zoom_level(self, zoom_level):
        """Set the page zoom to a specific value from the Zoom Presets menu."""
        self.page_zoom = zoom_level
        self._apply_zoom()
        # Update check state for both menu and toolbar zoom actions
        for act, value in self.menu_zoom_actions:
            act.setChecked(abs(self.page_zoom - value) < 0.01)
        for act, value in self.toolbar_zoom_actions:
            act.setChecked(abs(self.page_zoom - value) < 0.01)
            
    def _apply_optimal_zoom(self):
        """Calculate and apply optimal zoom to fill desktop height."""
        if not self.music_page:
            return
            
        # Get desktop view height (accounting for menu bar and toolbar)
        view_height = self.desktop_view.viewport().height() - 100  # Leave some margin
        
        # Calculate optimal zoom to fit page height
        page_height = self.music_page.page_height
        optimal_zoom = view_height / page_height
        
        # Clamp to reasonable bounds (30% to 300%)
        optimal_zoom = max(0.3, min(3.0, optimal_zoom))
        
        # Apply the optimal zoom
        self.page_zoom = optimal_zoom
        self._apply_zoom()
        
        # Center the page in the view
        self.desktop_view.centerOn(self.music_page)
        
        self.status_bar.showMessage(f"Applied optimal zoom: {int(self.page_zoom * 100)}%")
        
    def _position_dialog_right_of_page(self, dialog):
        """Position any dialog to the right of the music page."""
        if not self.music_page:
            return
            
        # Get page position and size
        page_pos = self.music_page.pos()
        page_width = self.music_page.page_width * self.page_zoom
        
        # Get dialog size
        dialog_width = dialog.width()
        dialog_height = dialog.height()
        
        # Calculate position to the right of the page
        x = page_pos.x() + page_width + 50  # 50px gap between page and dialog
        y = page_pos.y() + (self.music_page.page_height * self.page_zoom - dialog_height) // 2  # Center vertically
        
        # Ensure dialog stays within window bounds
        window_width = self.width()
        window_height = self.height()
        
        # Adjust if dialog would go off the right edge
        if x + dialog_width > window_width - 50:
            x = window_width - dialog_width - 50
            
        # Adjust if dialog would go off the bottom
        if y + dialog_height > window_height - 100:  # Leave space for menu/toolbar
            y = window_height - dialog_height - 100
            
        # Ensure dialog doesn't go off the top
        y = max(100, y)  # Leave space for menu/toolbar
        
        # Set dialog position
        dialog.move(int(x), int(y)) 

    def open_preferences(self):
        """Open the preferences dialog."""
        from src.gui.dialogs.preferences_dialog import PreferencesDialog
        dialog = PreferencesDialog(self)
        self._position_dialog_right_of_page(dialog)
        dialog.show()
        self.status_bar.showMessage("Preferences dialog opened")

    def apply_setup_options(self, options):
        """Apply setup options to the music page's staff view."""
        if self.music_page and hasattr(self.music_page, 'staff_view'):
            return self.music_page.staff_view.apply_setup_options(options)
        return False 


def main() -> int:
    """Application entry point for the ONOTE Desktop shell."""
    app = QApplication(sys.argv)
    app.setApplicationName("ONOTE")
    app.setOrganizationName("ONOTE")
    window = DesktopWindow()
    # Ensure the window is brought to the front on macOS
    window.show()
    window.raise_()
    window.activateWindow()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())