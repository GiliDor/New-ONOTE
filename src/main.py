import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QMenuBar, 
                           QMenu, QWidget, QVBoxLayout, QMessageBox,
                           QPushButton, QLabel, QHBoxLayout, QDockWidget,
                           QFileDialog, QStatusBar, QTabWidget, QDialog,
                           QScrollArea, QCheckBox, QComboBox, QSlider,
                           QSpinBox, QRadioButton, QGroupBox, QLineEdit)
from PyQt6.QtCore import Qt, QTimer, QDir, QSettings, QPoint, QSize
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from src.gui.rhythm_widget import RhythmWidget
from src.gui.music.staff_view import StaffView
from src.gui.music.rhythm_palette import RhythmPalette
from src.gui.music.pitch_widget import PitchWidget
from src.gui.dialogs.preferences_dialog import PreferencesDialog
from src.gui.music.score_setup_widget import ScoreSetupWidget
from src.gui.music.main_window import MainWindow
from src.core.settings_manager import settings
from src.gui.music.widgets.form_widget import FormWidget

print("Starting ONOTE application...")

# Set application name before any Qt initialization
os.environ['PYTHONNAME'] = 'ONOTE'
os.environ['PYTHONAPPLICATION'] = 'ONOTE'

# macOS specific environment variables
if sys.platform == 'darwin':
    os.environ['PYTHON_APP_NAME'] = 'ONOTE'
    os.environ['PYTHON_APP_DISPLAY_NAME'] = 'ONOTE'
    os.environ['PYTHON_APP_ORGANIZATION'] = 'ONOTE'
    os.environ['PYTHON_APP_DOMAIN'] = 'onote.app'

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ONOTEMainWindow(QMainWindow):
    # Class variable to track untitled document numbers
    _untitled_counter = 0
    # Class variables for singleton ScoreSetupWidget and its dock
    _score_setup_widget = None
    _score_setup_dock = None
    
    def __init__(self, is_welcome_window=False):
        print("Initializing main window...")
        super().__init__()
        self.is_welcome_window = is_welcome_window  # Store the flag
        self.setWindowTitle("ONOTE")
        self.setMinimumSize(1200, 800)
        
        # Initialize active_score
        self.active_score = None
        
        # Set window flags based on window type
        if is_welcome_window:
            # Desktop window flags
            self.setWindowFlags(Qt.WindowType.WindowMaximizeButtonHint | 
                              Qt.WindowType.WindowStaysOnBottomHint)
            # Create singleton ScoreSetupWidget if this is the desktop window
            if ONOTEMainWindow._score_setup_widget is None:
                ONOTEMainWindow._score_setup_widget = ScoreSetupWidget()
                # Create a dock widget to contain the score setup widget
                ONOTEMainWindow._score_setup_dock = QDockWidget("Score Setup", self)
                ONOTEMainWindow._score_setup_dock.setWidget(ONOTEMainWindow._score_setup_widget)
                ONOTEMainWindow._score_setup_dock.setFloating(True)
                ONOTEMainWindow._score_setup_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
                ONOTEMainWindow._score_setup_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                                QDockWidget.DockWidgetFeature.DockWidgetFloatable)
                self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, ONOTEMainWindow._score_setup_dock)
                ONOTEMainWindow._score_setup_dock.hide()  # Initially hidden
        else:
            # Regular document window flags
            self.setWindowFlags(Qt.WindowType.WindowMaximizeButtonHint)
        
        # Add window tracking - use class variable to track all windows
        if not hasattr(ONOTEMainWindow, '_all_windows'):
            ONOTEMainWindow._all_windows = []
        self.windows = ONOTEMainWindow._all_windows
        self.windows.append(self)
        
        # Store original size
        self.original_size = self.size()
        
        self.current_file = None
        self.scores_directory = settings.get_score_directory()
        
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
        
        # Set initial state based on window type
        if is_welcome_window:
            # Set grey background
            self.central_widget.setStyleSheet("""
                QWidget {
                    background-color: #f0f0f0;
                }
            """)
            # Maximize the desktop window
            self.showMaximized()
            # Set window title to indicate it's the desktop
            self.setWindowTitle("ONOTE Desktop")
            # Set window flags to keep it in background
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnBottomHint)
        else:
            # Initialize staff view
            self.staff_view = StaffView()
            self.main_layout.addWidget(self.staff_view)
        
        # Create score setup widget
        self.score_setup = ScoreSetupWidget()
        self.score_setup.setup_completed.connect(self.on_setup_completed)
        
        # Create dock widget for score setup
        self.setup_dock = QDockWidget("Score Setup", self)
        self.setup_dock.setWidget(self.score_setup)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.setup_dock)
        
        # Initially show setup dock
        self.setup_dock.show()
        
        print("Main window initialized")
        
    def handle_note_selected(self, note_type):
        """Handle note selection from rhythm widget"""
        print(f"Note selected: {note_type}")
        # Get the active window (last focused document window)
        active_window = self.get_active_document_window()
        if active_window and hasattr(active_window, 'staff_view'):
            # TODO: Handle note selection and add to score
            pass
        
    def handle_pattern_selected(self, pattern):
        """Handle rhythm pattern selection"""
        print(f"Pattern selected: {pattern}")
        # Get the active window
        active_window = self.get_active_document_window()
        if active_window and hasattr(active_window, 'staff_view'):
            # TODO: Implement pattern insertion into score
            pass
        
    def handle_pitch_selected(self, note_str):
        """Handle pitch selection"""
        print(f"Pitch selected: {note_str}")
        # Get the active window
        active_window = self.get_active_document_window()
        if active_window and hasattr(active_window, 'staff_view'):
            # TODO: Implement pitch insertion into score
            pass
            
    def get_active_document_window(self):
        """Get the currently active document window"""
        active_window = QApplication.activeWindow()
        if isinstance(active_window, ONOTEMainWindow) and not active_window.is_welcome_window:
            print(f"Found active document window: {active_window.windowTitle()}")
            return active_window
        # If no active document window found, try to find the most recently focused one
        for window in reversed(self.windows):
            if isinstance(window, ONOTEMainWindow) and not window.is_welcome_window:
                print(f"Using most recent document window: {window.windowTitle()}")
                window.raise_()
                window.activateWindow()
                return window
        print("No active document window found")
        return None
        
    def position_floating_tools(self):
        """Position the floating tools in a reasonable layout"""
        if self.is_welcome_window:
            # Get the window geometry
            window_geom = self.geometry()
            
            # Position each tool
            x_offset = 50
            y_offset = 50
            
            for name, widget in ONOTEMainWindow._shared_widgets.items():
                dock = widget.parent()
                if isinstance(dock, QDockWidget):
                    dock.move(window_geom.x() + x_offset,
                             window_geom.y() + y_offset)
                    x_offset += 300
                    
                    # Reset x_offset if we're going off screen
                    if x_offset + 300 > window_geom.width():
                        x_offset = 50
                        y_offset += 150
        
    def showEvent(self, event):
        """Handle window show event"""
        super().showEvent(event)
        # Only show About dialog for the welcome window
        if hasattr(self, 'is_welcome_window') and self.is_welcome_window:
            QTimer.singleShot(100, self.show_about_dialog)
        
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
        
        # Score menu
        score_menu = menubar.addMenu("&Score")
        
        # Score Setup action
        score_setup_action = QAction("&Score Setup", self)
        score_setup_action.setShortcut("Ctrl+Alt+S")
        score_setup_action.triggered.connect(self.show_score_setup)
        score_menu.addAction(score_setup_action)
        
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
        
        print("Menu bar created")
        
    def show_score_setup(self):
        """Show the score setup widget for the active document"""
        try:
            active_window = self.get_active_document_window()
            if active_window and hasattr(active_window, 'staff_view'):
                print(f"Showing score setup for window: {active_window.windowTitle()}")
                # Show the singleton score setup widget
                if ONOTEMainWindow._score_setup_widget and ONOTEMainWindow._score_setup_dock:
                    # Safely disconnect any existing connections
                    try:
                        ONOTEMainWindow._score_setup_widget.staff_added.disconnect()
                        print("Disconnected existing staff_added signal")
                    except TypeError:
                        print("No staff_added connections to disconnect")
                    try:
                        ONOTEMainWindow._score_setup_widget.staff_removed.disconnect()
                        print("Disconnected existing staff_removed signal")
                    except TypeError:
                        print("No staff_removed connections to disconnect")
                    try:
                        ONOTEMainWindow._score_setup_widget.staff_visibility_changed.disconnect()
                        print("Disconnected existing staff_visibility_changed signal")
                    except TypeError:
                        print("No staff_visibility_changed connections to disconnect")
                    try:
                        ONOTEMainWindow._score_setup_widget.staff_options_changed.disconnect()
                        print("Disconnected existing staff_options_changed signal")
                    except TypeError:
                        print("No staff_options_changed connections to disconnect")
                    
                    # Connect signals to current active window's staff view
                    ONOTEMainWindow._score_setup_widget.staff_added.connect(active_window.staff_view.handle_staff_added)
                    ONOTEMainWindow._score_setup_widget.staff_removed.connect(active_window.staff_view.handle_staff_removed)
                    ONOTEMainWindow._score_setup_widget.staff_visibility_changed.connect(active_window.staff_view.handle_staff_visibility)
                    ONOTEMainWindow._score_setup_widget.staff_options_changed.connect(active_window.staff_view.handle_staff_options)
                    print("Connected signals to active window's staff view")
                    
                    # Show and position the dock widget relative to the active window
                    ONOTEMainWindow._score_setup_dock.setParent(active_window)
                    ONOTEMainWindow._score_setup_dock.show()
                    ONOTEMainWindow._score_setup_dock.raise_()
                    
                    # Position the dock widget relative to the active window
                    window_geom = active_window.geometry()
                    ONOTEMainWindow._score_setup_dock.move(
                        window_geom.x() + window_geom.width() - ONOTEMainWindow._score_setup_dock.width() - 20,
                        window_geom.y() + 50
                    )
                    
                    # Enter setup mode in the active window
                    active_window.enter_setup_mode()
                    print("Score setup widget shown and setup mode entered")
            else:
                print("No active document window with staff view found")
        except Exception as e:
            print(f"Error showing score setup: {str(e)}")
            import traceback
            traceback.print_exc()
        
    def handle_staff_added(self, instrument_id: str, staff_type: str):
        """Handle adding a new staff"""
        # TODO: Implement staff addition logic
        print(f"Adding staff: {instrument_id} - {staff_type}")
        
    def handle_staff_removed(self, staff_index: int):
        """Handle removing a staff"""
        # TODO: Implement staff removal logic
        print(f"Removing staff at index: {staff_index}")
        
    def handle_staff_visibility(self, staff_index: int, is_visible: bool):
        """Handle staff visibility changes"""
        # TODO: Implement staff visibility logic
        print(f"Setting staff {staff_index} visibility to {is_visible}")
        
    def handle_staff_options(self, staff_index: int, options: dict):
        """Handle staff options changes"""
        # TODO: Implement staff options update logic
        print(f"Updating staff {staff_index} options: {options}")
        
    def show_form(self):
        """Show the Form widget"""
        print("FORM: show_form() called")
        # Get the active document window that has a staff view
        active_window = self.get_active_document_window()
        print(f"FORM: active_window = {active_window}")
        if not active_window or not hasattr(active_window, 'staff_view'):
            print("FORM: No active document window with staff view found")
            return
            
        if not hasattr(active_window, 'form_widget'):
            print("FORM: Creating new form widget")
            try:
                print("FORM: FormWidget imported successfully")
                active_window.form_widget = FormWidget(active_window)
                print("FORM: FormWidget created successfully")
            except Exception as e:
                print(f"FORM: Error creating FormWidget: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Connect form widget signals to document updates
            active_window.form_widget.structure_changed.connect(
                lambda measures: active_window.handle_form_structure_changed(measures)
            )
            active_window.form_widget.measure_modified.connect(
                lambda num, props: active_window.handle_measure_modified(num, props)
            )
            
            dock = QDockWidget("Form Control", active_window)
            dock.setWidget(active_window.form_widget)
            dock.setFloating(True)
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                           QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            active_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            
            # Initialize form widget with current document state
            if hasattr(active_window.staff_view, 'document') and active_window.staff_view.document:
                # Get current measure count from document
                num_measures = getattr(active_window.staff_view.document, 'num_measures', 32)
                active_window.form_widget.measure_count_spin.setValue(num_measures)
                active_window.form_widget.initialize_default_measures()
            
            # Position the dock widget relative to the active window
            window_geom = active_window.geometry()
            dock.move(
                window_geom.x() + window_geom.width() - dock.width() - 50,
                window_geom.y() + 100
            )
            
        active_window.form_widget.parent().show()
        active_window.form_widget.parent().raise_()
        print("Form widget shown for active document window")
        
    def show_notes(self):
        """Show the Notes widget"""
        if not hasattr(self, 'notes_widget'):
            from gui.music.widgets.notes import NotesWidget
            self.notes_widget = NotesWidget(self)
            dock = QDockWidget("Notes", self)
            dock.setWidget(self.notes_widget)
            dock.setFloating(True)
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                           QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.notes_widget.parent().show()
        
    def show_rhythm(self):
        """Show the Rhythm widget and dialogs"""
        if not hasattr(self, 'rhythm_tab_widget'):
            # Create main tab widget
            from PyQt6.QtWidgets import QTabWidget
            self.rhythm_tab_widget = QTabWidget()
            dock = QDockWidget("Rhythm", self)
            dock.setWidget(self.rhythm_tab_widget)
            dock.setFloating(True)
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                           QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
            
            # Create rhythm palette tab
            from gui.music.rhythm_palette import RhythmPalette
            self.rhythm_palette = RhythmPalette(self)
            self.rhythm_palette.pattern_selected.connect(self.handle_pattern_selected)
            self.rhythm_tab_widget.addTab(self.rhythm_palette, "Rhythm Pattern Generator")
            
            # Create rhythm pattern generator tab
            from gui.music.widgets.rhythm import RhythmPatternWidget
            self.rhythm_pattern_widget = RhythmPatternWidget(self)
            self.rhythm_pattern_widget.pattern_selected.connect(self.handle_pattern_selected)
            self.rhythm_tab_widget.addTab(self.rhythm_pattern_widget, "Rhythm Palette")
            
            # Create basic notation tab
            from gui.music.widgets.rhythm import SimpleRhythmWidget
            self.simple_rhythm_widget = SimpleRhythmWidget(self)
            self.simple_rhythm_widget.note_selected.connect(self.handle_note_selected)
            self.rhythm_tab_widget.addTab(self.simple_rhythm_widget, "Basic Notation")
            
            # Position the dock widget
            window_geom = self.geometry()
            dock.move(window_geom.x() + 50, window_geom.y() + 50)
            
        # Show the dock widget
        self.rhythm_tab_widget.parent().show()
        
    def show_pitch(self):
        """Show the Pitch widget"""
        if not hasattr(self, 'pitch_widget'):
            from gui.music.widgets.pitch import PitchWidget
            self.pitch_widget = PitchWidget(self)
            dock = QDockWidget("Pitch Input", self)
            dock.setWidget(self.pitch_widget)
            dock.setFloating(True)
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                           QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.pitch_widget.parent().show()
        
    def show_harmony(self):
        """Show the Harmony widget"""
        if not hasattr(self, 'harmony_widget'):
            from gui.music.widgets.harmony import HarmonyWidget
            self.harmony_widget = HarmonyWidget(self)
            dock = QDockWidget("Harmony", self)
            dock.setWidget(self.harmony_widget)
            dock.setFloating(True)
            dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
            dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                           QDockWidget.DockWidgetFeature.DockWidgetFloatable)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.harmony_widget.parent().show()
        
    def show_about_dialog(self):
        """Show the about dialog"""
        QMessageBox.about(self, "About ONOTE",
                         "ONOTE - Object Oriented Notation by Gil Dor\n\n"
                         f"Version {__version__}\n"
                         "Copyright © 2024 Gil Dor\n\n"
                         "A modern music notation software focusing on rhythm patterns "
                         "and user-friendly note input.")
        
    def new_score(self):
        """Handle New Score menu action"""
        print("Creating new score...")
        try:
            # Create a new window
            new_window = ONOTEMainWindow(is_welcome_window=False)
            
            # Increment the untitled counter and set the window title
            ONOTEMainWindow._untitled_counter += 1
            if ONOTEMainWindow._untitled_counter == 1:
                new_window.setWindowTitle("ONOTE - Untitled")
            else:
                new_window.setWindowTitle(f"ONOTE - Untitled {ONOTEMainWindow._untitled_counter}")
            
            # Create staff view and set it as central widget
            new_window.staff_view = StaffView()
            new_window.setCentralWidget(new_window.staff_view)
            
            # Position the new window
            current_pos = self.pos()
            new_window.move(current_pos.x() + 30, current_pos.y() + 30)
            new_window.show()
            new_window.raise_()
            new_window.activateWindow()
            
            # Set this as the active score
            new_window.active_score = new_window
            
            # Clear the score display in the new window
            new_window.statusBar.showMessage("New Score")
            
            # Update open files menu in all windows
            for window in self.windows:
                window.update_open_files_menu()
                
            print("New document created successfully")
            return True
        except Exception as e:
            print(f"Error in new_score: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def open_score(self):
        """Handle Open Score menu action"""
        print("Opening score...")
        try:
            print(f"Opening file dialog in directory: {self.scores_directory}")
            # Ensure the directory exists
            os.makedirs(self.scores_directory, exist_ok=True)
            
            # Create a file dialog with explicit style
            dialog = QFileDialog()
            dialog.setParent(self)
            dialog.setWindowTitle("Open Score")
            dialog.setDirectory(self.scores_directory)
            dialog.setNameFilter("ONOTE Scores (*.otn);;All Files (*.*)")
            dialog.setViewMode(QFileDialog.ViewMode.List)
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
            
            # Force dialog to be modal and stay on top
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dialog.setModal(True)
            
            print("Showing dialog...")
            dialog.show()  # Show the dialog
            print("Dialog shown")
            if dialog.exec():
                print("Dialog accepted")
                file_name = dialog.selectedFiles()[0]
                print(f"Selected file: {file_name}")
                # Create a new window for the opened file
                new_window = ONOTEMainWindow(is_welcome_window=False)
                if new_window.load_file(file_name):
                    # Position the new window
                    current_pos = self.pos()
                    new_window.move(current_pos.x() + 30, current_pos.y() + 30)
                    new_window.show()
                    new_window.raise_()
                    new_window.activateWindow()
                    new_window.statusBar.showMessage(f"Opened: {os.path.basename(file_name)}")
                    
                    # Update open files menu in all windows
                    for window in self.windows:
                        window.update_open_files_menu()
                else:
                    new_window.close()
            else:
                print("Dialog rejected")
        except Exception as e:
            print(f"Error in open_score: {str(e)}")
            import traceback
            traceback.print_exc()
                
    def save_score(self):
        print("Saving score...")
        try:
            if self.current_file is None:
                print("No current file, calling save as...")
                return self.save_score_as()
            print(f"Saving to current file: {self.current_file}")
            if self.save_file(self.current_file):
                self.statusBar.showMessage(f"Saved: {os.path.basename(self.current_file)}")
        except Exception as e:
            print(f"Error in save_score: {str(e)}")
            import traceback
            traceback.print_exc()
        
    def save_score_as(self):
        print("Saving score as...")
        try:
            print(f"Opening save dialog in directory: {self.scores_directory}")
            # Ensure the directory exists
            os.makedirs(self.scores_directory, exist_ok=True)
            
            # Create a file dialog with explicit style
            dialog = QFileDialog()
            dialog.setParent(self)
            dialog.setWindowTitle("Save Score As")
            dialog.setDirectory(self.scores_directory)
            dialog.setNameFilter("ONOTE Scores (*.otn);;All Files (*.*)")
            dialog.setViewMode(QFileDialog.ViewMode.List)
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            dialog.setDefaultSuffix("otn")
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            
            # Force dialog to be modal and stay on top
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            dialog.setModal(True)
            
            print("Showing dialog...")
            dialog.show()  # Show the dialog
            print("Dialog shown")
            if dialog.exec():
                print("Dialog accepted")
                file_name = dialog.selectedFiles()[0]
                print(f"Selected file: {file_name}")
                # Ensure the file has .otn extension
                if not file_name.endswith('.otn'):
                    file_name += '.otn'
                print(f"Final file name: {file_name}")
                if self.save_file(file_name):
                    # Update window title and status
                    self.setWindowTitle(f"ONOTE - {os.path.basename(file_name)}")
                    self.statusBar.showMessage(f"Saved as: {os.path.basename(file_name)}")
                    
                    # Update open files menu in all windows
                    for window in self.windows:
                        window.update_open_files_menu()
                    
                    # If this was an untitled window, decrement the counter
                    if self.current_file is None:
                        ONOTEMainWindow._untitled_counter = max(0, ONOTEMainWindow._untitled_counter - 1)
                    
                    return True
            else:
                print("Dialog rejected")
            return False
        except Exception as e:
            print(f"Error in save_score_as: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def maybe_save(self):
        """Check if we need to save changes before proceeding"""
        print("Checking if save is needed...")
        # TODO: Implement actual change tracking
        # For now, we'll just return True
        return True
        
    def load_file(self, file_name):
        """Load a score from a file"""
        print(f"Attempting to load file: {file_name}")
        try:
            # Convert to absolute path if not already
            if not os.path.isabs(file_name):
                file_name = os.path.join(self.scores_directory, file_name)
            
            # Check if file exists
            if not os.path.exists(file_name):
                raise FileNotFoundError(f"File not found: {file_name}")
            
            # Try to read the file
            with open(file_name, 'r') as f:
                content = f.read()
                print(f"File content: {content}")
                
                # Parse the content and load into staff view
                if content.startswith("ONOTE Score Format"):
                    # Clear existing staves
                    if hasattr(self, 'staff_view'):
                        self.staff_view.clear_staves()
                        
                    # TODO: Parse and load actual score content
                    # For now, just create an empty score
                    self.staff_view.show()
                    
                    # Update window state
                    self.current_file = file_name
                    self.setWindowTitle(f"ONOTE - {os.path.basename(file_name)}")
                    return True
                else:
                    raise ValueError("Invalid file format")
                    
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "ONOTE",
                f"Cannot read file {file_name}:\n{str(e)}"
            )
            return False
            
    def save_file(self, file_name):
        """Save the score to a file"""
        print(f"Attempting to save file: {file_name}")
        try:
            # Convert to absolute path if not already
            if not os.path.isabs(file_name):
                file_name = os.path.join(self.scores_directory, file_name)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_name), exist_ok=True)
            
            # Try to write to the file
            with open(file_name, 'w') as f:
                # For now, just write a simple version number
                f.write("ONOTE Score Format v0.1.0\n")
                print(f"Successfully saved file: {file_name}")
                self.current_file = file_name
                self.setWindowTitle(f"ONOTE - {os.path.basename(file_name)}")
                return True
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self,
                "ONOTE",
                f"Cannot write file {file_name}:\n{str(e)}"
            )
            return False
            
    def import_score(self):
        print("Importing score...")
        # TODO: Implement score import
        pass

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
                
                # If this was an untitled window, decrement the counter
                if self.current_file is None:
                    ONOTEMainWindow._untitled_counter = max(0, ONOTEMainWindow._untitled_counter - 1)
                
                # Update open files menu in remaining windows
                for window in self.windows:
                    window.update_open_files_menu()
                    
            event.accept()
        else:
            event.ignore()

    def cascade_windows(self):
        """Cascade all windows except the desktop"""
        if not self.windows:
            return
            
        # Get the screen geometry
        screen = QApplication.primaryScreen().geometry()
        
        # Start position
        x = screen.x() + 50
        y = screen.y() + 50
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        
        # Position each window except the desktop
        for window in self.windows[1:]:  # Skip desktop window
            if window.isVisible():
                # Restore window to a standard size
                window.resize(width, height)
                window.move(x, y)
                
                # Increment position for next window
                x += 30
                y += 30
                
                # If window would go off screen, reset position
                if x + width > screen.width() or y + height > screen.height():
                    x = screen.x() + 50
                    y = screen.y() + 50
                
                # Ensure window is visible and on top
                window.show()
                window.raise_()
                window.activateWindow()
                
        # Ensure desktop stays in background
        if self.windows and self.windows[0].isVisible():
            self.windows[0].lower()

    def tile_windows(self):
        """Tile all windows except the desktop"""
        if not self.windows:
            return
            
        # Get the screen geometry
        screen = QApplication.primaryScreen().geometry()
        
        # Get visible windows except the desktop
        visible_windows = [w for w in self.windows[1:] if w.isVisible()]  # Skip desktop window
        if not visible_windows:
            return
            
        # Calculate grid dimensions
        n = len(visible_windows)
        cols = int((n ** 0.5) + 0.5)  # Round to nearest for better layout
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
            
            # Resize and move window
            window.resize(window_width, window_height)
            window.move(x, y)
            window.show()
            window.raise_()
            window.activateWindow()

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

    def show_preferences(self):
        """Show the preferences dialog"""
        dialog = PreferencesDialog(self)
        dialog.exec()
        
    def show_documentation(self):
        """Show the documentation"""
        # TODO: Implement documentation viewer
        QMessageBox.information(self, "Documentation", "Documentation viewer will be implemented in a future version.")
        
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        # TODO: Implement shortcuts dialog
        QMessageBox.information(self, "Keyboard Shortcuts", "Keyboard shortcuts dialog will be implemented in a future version.")
        
    def check_for_updates(self):
        """Check for application updates"""
        # TODO: Implement update checker
        QMessageBox.information(self, "Check for Updates", "Update checker will be implemented in a future version.")
        
    def print_score(self):
        """Print the score"""
        # TODO: Implement score printing
        QMessageBox.information(self, "Print Score", "Score printing will be implemented in a future version.")
        
    def print_preview(self):
        """Show print preview"""
        # TODO: Implement print preview
        QMessageBox.information(self, "Print Preview", "Print preview will be implemented in a future version.")
        
    def zoom_in(self):
        """Zoom in the score view"""
        if hasattr(self, 'staff_view') and self.staff_view:
            current_zoom = getattr(self.staff_view, 'zoom_factor', 1.0)
            new_zoom = min(current_zoom * 1.2, 3.0)  # Max zoom 3x
            self.staff_view.zoom_factor = new_zoom
            self.staff_view.update()
            self.statusBar().showMessage(f"Zoom: {int(new_zoom * 100)}%", 2000)
        else:
            QMessageBox.information(self, "Zoom In", "No score view available to zoom.")
        
    def zoom_out(self):
        """Zoom out the score view"""
        if hasattr(self, 'staff_view') and self.staff_view:
            current_zoom = getattr(self.staff_view, 'zoom_factor', 1.0)
            new_zoom = max(current_zoom / 1.2, 0.3)  # Min zoom 30%
            self.staff_view.zoom_factor = new_zoom
            self.staff_view.update()
            self.statusBar().showMessage(f"Zoom: {int(new_zoom * 100)}%", 2000)
        else:
            QMessageBox.information(self, "Zoom Out", "No score view available to zoom.")
        
    def reset_zoom(self):
        """Reset the zoom level"""
        if hasattr(self, 'staff_view') and self.staff_view:
            self.staff_view.zoom_factor = 1.0
            self.staff_view.update()
            self.statusBar().showMessage("Zoom reset to 100%", 2000)
        else:
            QMessageBox.information(self, "Reset Zoom", "No score view available to reset zoom.")

    def toggle_rhythm_input(self):
        """Toggle the rhythm input widget visibility"""
        if hasattr(self, 'rhythm_widget'):
            dock = self.staff_view.findChild(QDockWidget, "Rhythm Input")
            if dock:
                dock.setVisible(not dock.isVisible())
                
    def toggle_rhythm_palette(self):
        """Toggle the rhythm palette widget visibility"""
        if hasattr(self, 'rhythm_palette'):
            dock = self.staff_view.findChild(QDockWidget, "Rhythm Palette")
            if dock:
                dock.setVisible(not dock.isVisible())
                
    def toggle_pitch_input(self):
        """Toggle the pitch input widget visibility"""
        if hasattr(self, 'pitch_widget'):
            dock = self.staff_view.findChild(QDockWidget, "Pitch Input")
            if dock:
                dock.setVisible(not dock.isVisible())

    def undo(self):
        """Handle undo action"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Simple undo system - restore from document history
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'undo'):
                if self.staff_view.document.undo():
                    # Update the staff view
                    self.staff_view.update()
                    
                    # Also refresh the setup widget if it's open
                    if ONOTEMainWindow._score_setup_widget and ONOTEMainWindow._score_setup_dock:
                        if ONOTEMainWindow._score_setup_dock.isVisible():
                            # Refresh the setup widget with the restored document state
                            ONOTEMainWindow._score_setup_widget.refresh_from_document()
                    
                    self.statusBar().showMessage("Undo successful", 2000)
                else:
                    self.statusBar().showMessage("Nothing to undo", 2000)
            else:
                self.statusBar().showMessage("Undo not available", 2000)
        else:
            QMessageBox.information(self, "Undo", "No active document to undo changes.")
        
    def redo(self):
        """Handle redo action"""
        if hasattr(self, 'staff_view') and self.staff_view:
            # Simple redo system - replay from document history
            if hasattr(self.staff_view, 'document') and hasattr(self.staff_view.document, 'redo'):
                if self.staff_view.document.redo():
                    # Update the staff view
                    self.staff_view.update()
                    
                    # Also refresh the setup widget if it's open
                    if ONOTEMainWindow._score_setup_widget and ONOTEMainWindow._score_setup_dock:
                        if ONOTEMainWindow._score_setup_dock.isVisible():
                            # Refresh the setup widget with the restored document state
                            ONOTEMainWindow._score_setup_widget.refresh_from_document()
                    
                    self.statusBar().showMessage("Redo successful", 2000)
                else:
                    self.statusBar().showMessage("Nothing to redo", 2000)
            else:
                self.statusBar().showMessage("Redo not available", 2000)
        else:
            QMessageBox.information(self, "Redo", "No active document to redo changes.")
        
    def activate_window(self, window):
        """Activate a specific window"""
        window.show()
        window.showMaximized()  # Maximize the window
        window.raise_()
        window.activateWindow()

    def close_active_score(self):
        """Close the active score window"""
        active_window = self.get_active_document_window()
        if active_window:
            active_window.close()
    
    def handle_form_structure_changed(self, measures):
        """Handle when form widget changes the measure structure"""
        if hasattr(self, 'staff_view') and self.staff_view and hasattr(self.staff_view, 'document'):
            # Update document measure count
            self.staff_view.document.num_measures = len(measures)
            
            # Store measure objects in document for rendering
            self.staff_view.document.measures = measures
            
            # Update the staff view display
            self.staff_view.update()
            print(f"Document structure updated: {len(measures)} measures")
    
    def handle_measure_modified(self, measure_number, properties):
        """Handle when form widget modifies a specific measure"""
        if hasattr(self, 'staff_view') and self.staff_view and hasattr(self.staff_view, 'document'):
            # Update the specific measure in document
            if hasattr(self.staff_view.document, 'measures') and self.staff_view.document.measures:
                for measure in self.staff_view.document.measures:
                    if measure.measure_number == measure_number:
                        # Update measure properties
                        for prop, value in properties.items():
                            if hasattr(measure, prop):
                                setattr(measure, prop, value)
                        break
            
            # Update the staff view display
            self.staff_view.update()
            print(f"Measure {measure_number} modified: {properties}")
            
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

    def show_full_score_options(self):
        """Show the full score options dialog"""
        # Check if we have a valid staff_view first
        if not hasattr(self, 'staff_view') or self.staff_view is None:
            QMessageBox.warning(self, "No Score", "Please create or open a score first.")
            return
            
        from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
        
        try:
            dialog = FullScoreOptionsDialog(self)
            
            # Set the document on the dialog so it can load current settings
            if hasattr(self.staff_view, 'document') and self.staff_view.document:
                dialog.set_document(self.staff_view.document)
            
            if dialog.exec():
                # Get settings from the dialog
                font_settings = dialog.get_font_settings()
                layout_settings = dialog.get_layout_settings()
                
                # Apply the settings to the score
                if hasattr(self, 'staff_view') and self.staff_view:
                    # Apply font settings if a category was selected
                    if font_settings:
                        print(f"Applying font settings for {font_settings['category']}")
                        # TODO: Implement applying font settings to the score
                    
                    # Apply layout settings
                    print("Applying layout settings")
                    # TODO: Implement applying layout settings to the score
                    
                    # Refresh the view only if staff_view is still valid
                    if hasattr(self, 'staff_view') and self.staff_view:
                        self.staff_view.update()
                    
                # Log the settings that were applied
                print(f"Font settings: {font_settings}")
                print(f"Layout settings: {layout_settings}")
        except Exception as e:
            print(f"Error showing full score options dialog: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_parts_options(self):
        """Show the parts options dialog"""
        # TODO: Implement parts options dialog
        pass

    def show_title_options(self):
        """Show the title, header, and footer options dialog"""
        # TODO: Implement title options dialog
        pass

    def show_notation_setup(self):
        """Show the notation setup dialog"""
        print("\n\n*** CALLED show_notation_setup ***\n\n")
        from src.gui.music.dialogs import NotationSetupDialog
        
        try:
            dialog = NotationSetupDialog(self)
            if dialog.exec():
                # Get settings from the dialog
                notation_settings = dialog.get_notation_settings()
                
                # Apply the settings to the score
                if hasattr(self, 'staff_view') and self.staff_view:
                    # Apply notation settings
                    print("Applying notation settings")
                    # TODO: Implement applying notation settings to the score
                    
                    # Refresh the view only if staff_view is still valid
                    if hasattr(self, 'staff_view') and self.staff_view:
                        self.staff_view.update()
                    
                # Log the settings that were applied
                print(f"Notation settings applied: {notation_settings}")
        except Exception as e:
            print(f"Error showing notation setup dialog: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_dynamic_parts(self):
        """Show the dynamic parts dialog"""
        # TODO: Implement dynamic parts dialog
        pass

    def enter_setup_mode(self):
        """Enter score setup mode"""
        print("ONOTEMainWindow: Entering setup mode...")
        if hasattr(self, 'staff_view'):
            self.staff_view.enter_setup_mode()
            
    def exit_setup_mode(self):
        """Exit score setup mode"""
        print("ONOTEMainWindow: Exiting setup mode...")
        if hasattr(self, 'staff_view'):
            self.staff_view.exit_setup_mode()
            # Hide the score setup widget
            if ONOTEMainWindow._score_setup_dock:
                ONOTEMainWindow._score_setup_dock.hide()

    def on_setup_completed(self):
        """Handle setup completion"""
        self.staff_view.enter_edit_mode()  # Switch to edit mode
        self.setup_dock.hide()  # Hide setup dock

    def export_score(self):
        """Export the score"""
        if not hasattr(self, 'staff_view') or not self.staff_view:
            QMessageBox.warning(self, "Export Score", "No active score to export.")
            return
            
        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Score",
            "",
            "PDF Files (*.pdf);;PNG Images (*.png);;SVG Files (*.svg);;JPEG Images (*.jpg)"
        )
        
        if file_name:
            try:
                if selected_filter.startswith("PDF"):
                    self.export_as_pdf(file_name)
                elif selected_filter.startswith("PNG"):
                    self.export_as_png(file_name)
                elif selected_filter.startswith("SVG"):
                    self.export_as_svg(file_name)
                elif selected_filter.startswith("JPEG"):
                    self.export_as_jpeg(file_name)
                    
                self.statusBar().showMessage(f"Score exported to {file_name}", 3000)
                QMessageBox.information(self, "Export Complete", f"Score successfully exported to:\n{file_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export score:\n{str(e)}")
                
    def export_as_pdf(self, file_name):
        """Export score as PDF"""
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QPainter
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file_name)
        printer.setPageSize(QPrinter.PageSize.A4)
        printer.setPageMargins(20, 20, 20, 20, QPrinter.Unit.Millimeter)
        
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Render the staff view to the PDF
        scale_factor = printer.pageRect().width() / self.staff_view.width()
        painter.scale(scale_factor, scale_factor)
        
        self.staff_view.render(painter)
        painter.end()
        
    def export_as_png(self, file_name):
        """Export score as PNG image"""
        from PyQt6.QtGui import QPixmap
        
        # Create a pixmap of the staff view
        pixmap = QPixmap(self.staff_view.size())
        pixmap.fill(Qt.GlobalColor.white)
        self.staff_view.render(pixmap)
        
        # Save as PNG
        pixmap.save(file_name, "PNG")
        
    def export_as_svg(self, file_name):
        """Export score as SVG"""
        from PyQt6.QtSvg import QSvgGenerator
        from PyQt6.QtGui import QPainter
        
        generator = QSvgGenerator()
        generator.setFileName(file_name)
        generator.setSize(self.staff_view.size())
        generator.setViewBox(self.staff_view.rect())
        generator.setTitle("ONOTE Score")
        generator.setDescription("Music score exported from ONOTE")
        
        painter = QPainter(generator)
        self.staff_view.render(painter)
        painter.end()
        
    def export_as_jpeg(self, file_name):
        """Export score as JPEG image"""
        from PyQt6.QtGui import QPixmap
        
        # Create a pixmap of the staff view
        pixmap = QPixmap(self.staff_view.size())
        pixmap.fill(Qt.GlobalColor.white)
        self.staff_view.render(pixmap)
        
        # Save as JPEG
        pixmap.save(file_name, "JPEG", 95)  # 95% quality

def main():
    print("Starting main function...")
    try:
        # Basic application setup
        app = QApplication(sys.argv)
        
        # Set up application identity
        app.setApplicationName("ONOTE")
        app.setApplicationDisplayName("ONOTE")
        app.setOrganizationName("ONOTE")
        app.setOrganizationDomain("onote.app")
        
        # Set window title for source code version
        os.environ['PYTHON_APP_NAME'] = 'ONOTE'
        
        # macOS specific settings
        if sys.platform == 'darwin':
            # Use native macOS style
            app.setStyle('macOS')
            
            # Configure native menu bar
            app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, False)
            app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, True)
            
            # High DPI settings - using currently supported attributes
            app.setAttribute(Qt.ApplicationAttribute.AA_Use96Dpi, False)
            
            # Set application identity
            import ctypes
            if hasattr(ctypes.pythonapi, 'Py_SetProgramName'):
                name = 'ONOTE'.encode('utf-8')
                ctypes.pythonapi.Py_SetProgramName(name)
            
            # Additional macOS-specific settings
            os.environ['PYTHONUNBUFFERED'] = '1'
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # Try to force the application name in the menu bar
            try:
                from Foundation import NSBundle
                bundle = NSBundle.mainBundle()
                if bundle:
                    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                    if info:
                        info['CFBundleName'] = 'ONOTE'
                        info['CFBundleDisplayName'] = 'ONOTE'
                        info['CFBundleIdentifier'] = 'com.onote.app'
                        info['CFBundlePackageType'] = 'APPL'
                        info['CFBundleExecutable'] = 'ONOTE'
                        info['CFBundleShortVersionString'] = '2.0.0'
                        info['CFBundleVersion'] = '2.0.0'
                        info['LSMinimumSystemVersion'] = '10.15'
                        info['NSPrincipalClass'] = 'NSApplication'
                        info['NSSupportsAutomaticGraphicsSwitching'] = True
                        info['LSEnvironment'] = {
                            'PYTHON_APP_NAME': 'ONOTE',
                            'PYTHON_APP_DISPLAY_NAME': 'ONOTE',
                            'PYTHON_APP_ORGANIZATION': 'ONOTE',
                            'PYTHON_APP_DOMAIN': 'onote.app'
                        }
            except ImportError:
                print("Could not import Foundation module")
        
        # Create and show the main window (welcome window)
        window = MainWindow(is_welcome_window=True)
        window.setWindowTitle("ONOTE")
        window.show()
        print("Window shown, entering event loop...")
        
        # Process any pending events before entering the main event loop
        app.processEvents()
        
        # Enter the main event loop
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Script started")
    main() 