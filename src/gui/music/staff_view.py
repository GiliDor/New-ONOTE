from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QDockWidget, QToolBar, QLabel, QMainWindow, QPushButton,
                           QComboBox, QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
                           QTabWidget, QSizePolicy, QFrame, QLineEdit, QTreeWidgetItem,
                           QApplication, QCheckBox, QGroupBox, QScrollArea, QGridLayout,
                           QButtonGroup, QRadioButton)
from PyQt6.QtCore import Qt, QRectF, QPointF, QRect, QPoint, QTimer, QObject, QEvent, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QBrush, QFontMetrics, QKeyEvent
from PyQt6.QtWidgets import QPinchGesture
from PyQt6.QtCore import pyqtSignal
from .staff_types import StaffType, StaffBase, SingleStaff, GrandStaff, SectionGroup, ScoreLayout
from .score_document import ScoreDocument
from .score_setup_dialog import ScoreSetupDialog
from .score_renderer import ScoreRenderer
from .measure_object import MeasureObject
from .element_selection import ScoreElementSelection
from .constants import STAFF_LINE_SPACING
from typing import List

# Constants for staff drawing
STAFF_HEIGHT = 32  # Height of a single staff in pixels
STAFF_SPACING = 50  # Space between staves in pixels
STAFF_LINE_SPACING = 8  # Space between staff lines in pixels
STAFF_LINE_THICKNESS = 1  # Thickness of staff lines in pixels
LEFT_MARGIN = 80  # Left margin for brackets and instrument names
RIGHT_MARGIN = 50  # Right margin - CRITICAL FIX: Match renderer and layout margins
TOP_MARGIN = 40  # Top margin

# Constants for clef positioning
TREBLE_CLEF_VERTICAL_OFFSET = -2  # Lines from staff center
BASS_CLEF_VERTICAL_OFFSET = 2  # Lines from staff center
ALTO_CLEF_VERTICAL_OFFSET = 0  # Lines from staff center
TENOR_CLEF_VERTICAL_OFFSET = 1  # Lines from staff center
PERCUSSION_CLEF_VERTICAL_OFFSET = 0  # Lines from staff center
CLEF_HORIZONTAL_OFFSET = 15  # Horizontal offset for all clefs

# Constants for barline drawing
INITIAL_BARLINE_THICKNESS = 2  # Thickness of initial barline
INITIAL_BARLINE_OFFSET = 35  # Offset from left margin for initial barline
BARLINE_EXTENSION = 3  # How much the barline extends above/below staff

# Constants for time signature positioning
TIME_SIG_SPACING = 8  # Space between numerator and denominator

# Constants for staff name positioning
STAFF_NAME_MARGIN = 8  # Margin for staff names

# Remove hardcoded constant - will be calculated dynamically from document layout
# END_BARLINE_X = 750.0   # Must match BarlineTemporalBridge.END_BARLINE_X (page_width - right_margin = 800 - 50)

class StaffDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Staff Settings")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Create main layout
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Staff Properties tab
        properties_tab = QWidget()
        properties_layout = QFormLayout(properties_tab)
        
        # Staff type
        self.staff_type = QComboBox()
        self.staff_type.addItems(["Single Staff", "Grand Staff", "Full Score"])
        properties_layout.addRow("Staff Type:", self.staff_type)
        
        # Staff count
        self.staff_count = QSpinBox()
        self.staff_count.setRange(1, 10)
        self.staff_count.setValue(1)
        self.staff_count.setEnabled(False)  # Only enabled for Full Score
        properties_layout.addRow("Number of Staves:", self.staff_count)
        
        # Staff name
        self.name_edit = QLineEdit()
        properties_layout.addRow("Staff Name:", self.name_edit)
        
        # Staff abbreviation
        self.abbr_edit = QLineEdit()
        properties_layout.addRow("Abbreviation:", self.abbr_edit)
        
        tabs.addTab(properties_tab, "Properties")
        
        # Layout Settings tab
        layout_tab = QWidget()
        layout_settings = QFormLayout(layout_tab)
        
        # Staff spacing
        self.staff_spacing = QSpinBox()
        self.staff_spacing.setRange(20, 100)
        self.staff_spacing.setValue(40)
        self.staff_spacing.setSuffix(" px")
        layout_settings.addRow("Staff Spacing:", self.staff_spacing)
        
        # System spacing
        self.system_spacing = QSpinBox()
        self.system_spacing.setRange(40, 200)
        self.system_spacing.setValue(80)
        self.system_spacing.setSuffix(" px")
        layout_settings.addRow("System Spacing:", self.system_spacing)
        
        tabs.addTab(layout_tab, "Layout")
        
        layout.addWidget(tabs)
        
        # Add Apply, OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        
        # Add Apply button
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.apply_changes)
        buttons.addButton(apply_button, QDialogButtonBox.ButtonRole.ActionRole)
        
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect staff type change to enable/disable staff count
        self.staff_type.currentTextChanged.connect(self.on_staff_type_changed)
        
        # Store parent reference for apply functionality
        self.parent_view = parent
        
    def on_staff_type_changed(self, staff_type):
        """Enable/disable staff count based on staff type"""
        self.staff_count.setEnabled(staff_type == "Full Score")
        
    def get_settings(self):
        """Get the current settings"""
        staff_type = self.staff_type.currentText()
        if staff_type == "Single Staff":
            return {
                'staff_type': 'single_staff',
                'staff_spacing': self.staff_spacing.value(),
                'system_spacing': self.system_spacing.value(),
                'name': self.name_edit.text(),
                'abbr': self.abbr_edit.text()
            }
        elif staff_type == "Grand Staff":
            return {
                'staff_type': 'grand_staff',
                'staff_spacing': self.staff_spacing.value(),
                'system_spacing': self.system_spacing.value(),
                'name': self.name_edit.text(),
                'abbr': self.abbr_edit.text()
            }
        else:  # Full Score
            return {
                'staff_type': f'full_{self.staff_count.value()}',
                'staff_spacing': self.staff_spacing.value(),
                'system_spacing': self.system_spacing.value(),
                'name': self.name_edit.text(),
                'abbr': self.abbr_edit.text()
            }

    def apply_changes(self):
        """Apply changes without closing the dialog"""
        if self.parent_view and hasattr(self.parent_view, 'selected_staff'):
            settings = self.get_settings()
            # Update staff settings
            self.parent_view.selected_staff.staff_type = settings['staff_type']
            self.parent_view.selected_staff.name = settings['name']
            self.parent_view.selected_staff.abbr = settings['abbr']
            self.parent_view.update()

class ClefDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clef Settings")
        self.setModal(True)
        
        # Create layout
        layout = QFormLayout(self)
        
        # Clef selection
        self.clef = QComboBox()
        self.clef.addItems([
            "Treble (G)",
            "Bass (F)",
            "Alto (C)",
            "Tenor (C)",
            "Percussion"
        ])
        layout.addRow("Clef:", self.clef)
        
        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_settings(self):
        """Get the current settings"""
        return {'clef': self.clef.currentText()}

class KeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Key Signature")
        self.setModal(True)
        
        # Create layout
        layout = QFormLayout(self)
        
        # Key selection
        self.key = QComboBox()
        self.key.addItems([
            "C major / A minor (no sharps/flats)",
            "G major / E minor (1 sharp)",
            "D major / B minor (2 sharps)",
            "A major / F# minor (3 sharps)",
            "E major / C# minor (4 sharps)",
            "B major / G# minor (5 sharps)",
            "F# major / D# minor (6 sharps)",
            "C# major / A# minor (7 sharps)",
            "F major / D minor (1 flat)",
            "Bb major / G minor (2 flats)",
            "Eb major / C minor (3 flats)",
            "Ab major / F minor (4 flats)",
            "Db major / Bb minor (5 flats)",
            "Gb major / Eb minor (6 flats)",
            "Cb major / Ab minor (7 flats)"
        ])
        layout.addRow("Key:", self.key)
        
        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_settings(self):
        """Get the current settings"""
        return {'key': self.key.currentText()}

class TimeSignatureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Time Signature")
        self.setModal(True)
        
        # Create layout
        layout = QFormLayout(self)
        
        # Numerator selection
        self.numerator = QSpinBox()
        self.numerator.setRange(1, 32)
        self.numerator.setValue(4)
        layout.addRow("Beats per measure:", self.numerator)
        
        # Denominator selection (only allow standard values: 1, 2, 4, 8, 16, 32)
        self.denominator = QComboBox()
        self.denominator.addItems(['1', '2', '4', '8', '16', '32'])
        self.denominator.setCurrentText('4')
        layout.addRow("Beat unit:", self.denominator)
        
        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
    def get_settings(self):
        """Get the current settings"""
        return {
            'numerator': self.numerator.value(),
            'denominator': int(self.denominator.currentText())
        }

class StaffMeasureSelection:
    """Manages selection of staves and measures for editing operations"""
    
    def __init__(self):
        self.selected_staves = set()  # Set of selected staff indices/IDs
        self.selected_measures = set()  # Set of selected measure indices  
        self.selection_mode = "measure"  # "staff", "measure", or "both"
        self.last_selected_staff = None
        self.last_selected_measure = None
        
    def clear_selection(self):
        """Clear all selections"""
        self.selected_staves.clear()
        self.selected_measures.clear()
        self.last_selected_staff = None
        self.last_selected_measure = None
        
    def select_staff(self, staff_index, toggle=False):
        """Select a staff by index"""
        if toggle and staff_index in self.selected_staves:
            self.selected_staves.discard(staff_index)
        else:
            if not toggle:
                self.selected_staves.clear()
            self.selected_staves.add(staff_index)
            self.last_selected_staff = staff_index
            
    def select_measure(self, measure_index, toggle=False):
        """Select a measure by index"""
        if toggle and measure_index in self.selected_measures:
            self.selected_measures.discard(measure_index)
        else:
            if not toggle:
                self.selected_measures.clear()
            self.selected_measures.add(measure_index)
            self.last_selected_measure = measure_index
            
    def select_measure_range(self, start_measure, end_measure):
        """Select a range of measures (inclusive)"""
        self.selected_measures.clear()
        for i in range(start_measure, end_measure + 1):
            self.selected_measures.add(i)
            
    def is_staff_selected(self, staff_index):
        """Check if a staff is selected"""
        return staff_index in self.selected_staves
        
    def is_measure_selected(self, measure_index):
        """Check if a measure is selected"""
        return measure_index in self.selected_measures
        
    def get_selected_staff_count(self):
        """Get number of selected staves"""
        return len(self.selected_staves)
        
    def get_selected_measure_count(self):
        """Get number of selected measures"""
        return len(self.selected_measures)
        
    def get_selection_summary(self):
        """Get a summary of current selection for debugging"""
        return {
            'staves': sorted(list(self.selected_staves)),
            'measures': sorted(list(self.selected_measures)),
            'mode': self.selection_mode,
            'last_staff': self.last_selected_staff,
            'last_measure': self.last_selected_measure
        }

class StaffView(QWidget):
    # Signals
    barline_created = pyqtSignal(MeasureObject)  # Signal emitted when a new barline is created
    barline_selected = pyqtSignal(MeasureObject)  # Signal emitted when a barline is selected
    barline_removed = pyqtSignal(MeasureObject)   # Signal emitted when a barline is removed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = None
        self.is_setup_mode = False
        self.dialog_settings = {}
        self.element_selection = ScoreElementSelection(self)
        
        # Initialize missing attributes
        self.zoom_factor = 1.0
        self.selected_staff = None
        self.dialog_open = False
        self.staff_dialog_open = False
        self.preserved_document_state = None
        self._keyboard_grabbed = False
        self.barline_creation_enabled = True  # Enable barline creation by default
        
        # PAGE-BASED RENDERING: Initialize page navigation and positioning
        self.current_page = 0
        self.total_pages = 1
        
        # WIDGET SIZE UPDATE: Timer for debounced size updates (prevents flicker)
        self._size_update_timer = QTimer(self)
        self._size_update_timer.setSingleShot(True)
        self._size_update_timer.timeout.connect(self._update_widget_size)
        
        # PAGE POSITIONING: Make pages moveable within window
        self.page_offset_x = 0.0  # Horizontal offset for page positioning
        self.page_offset_y = 0.0  # Vertical offset for page positioning
        self.is_dragging_page = False
        self.drag_start_pos = None
        self.drag_start_offset = QPointF(0, 0)
        
        # Track currently selected barline x-positions (score coordinates)
        self._selected_barline_positions = []
        
        # GESTURE SUPPORT: Initialize gesture tracking
        self.last_mouse_pos = None
        self.gesture_start_pos = None
        self.gesture_start_zoom = 1.0
        self.is_gesturing = False
        # Selection visualization mode: use color change in renderer, not overlay
        self.show_selection_overlay = False
                # DRAG SELECTION: Initialize drag selection system
        self.is_drag_selecting = False
        self.drag_select_start = None
        self.drag_select_end = None
        self.drag_select_rect = None
        
        # Initialize the renderer
        from .score_renderer import ScoreRenderer
        self.renderer = ScoreRenderer()
        
        # Set up UI first
        self.setup_ui()
        
        # Initialize temporal bridge for advanced measure handling
        from .barline_temporal_bridge import BarlineTemporalBridge
        self.temporal_bridge = BarlineTemporalBridge(None, self)  # Pass None initially, will update after document creation
        
        # Initialize test score for development (this creates the document)
        # TEMPORARILY DISABLED: self.create_test_score() - causing crash during initialization
        
        # Create minimal document if none exists
        if not self.document:
            from .score_document import ScoreDocument
            self.document = ScoreDocument()
            print("STAFFVIEW: Created minimal ScoreDocument")
            # Apply default zoom (80%) from Preferences if available
            try:
                from PyQt6.QtCore import QSettings
                default_zoom = QSettings("ONOTE", "Preferences").value("general/default_zoom", "100%")
                # Accept formats like "80%" or numeric strings
                if isinstance(default_zoom, str) and default_zoom.endswith('%'):
                    self.zoom_factor = max(0.25, min(float(default_zoom.strip('%'))/100.0, 4.0))
                else:
                    self.zoom_factor = max(0.25, min(float(default_zoom)/100.0, 4.0))
            except Exception:
                # Fallback to 0.8 as requested default
                self.zoom_factor = 0.8
        
        # Grab pinch gesture (Qt gesture framework) in addition to native gesture path
        try:
            self.grabGesture(Qt.GestureType.PinchGesture)
        except Exception:
            pass

        # Enable mouse tracking for gesture support
        self.setMouseTracking(True)
        
        # Enable touch events for pinch gestures
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)
        
        # Set focus policy for keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Initialize measure manager AFTER document is created
        self._initialize_measure_manager()
        
        # Set focus policy to ensure we can receive keyboard events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def set_document(self, document):
        """Set the document to display"""
        self.document = document
        # NEW: Set up bidirectional reference for element selection
        if document:
            self.document.staff_view = self
        # Set the document in the renderer
        if self.renderer:
            self.renderer.set_document(document)
            # Enforce preferred orientation on first attach to renderer
            try:
                from PyQt6.QtCore import QSettings
                preferred_orientation = str(QSettings("ONOTE", "Preferences").value("layout/default_orientation", "Portrait"))
                preferred_orientation = 'Landscape' if preferred_orientation.lower().startswith('land') else 'Portrait'
                layout = getattr(self.document, 'layout', None)
                # Determine current orientation from renderer
                rw = getattr(self.renderer, 'page_width', 0)
                rh = getattr(self.renderer, 'page_height', 0)
                current_orientation = 'Landscape' if rw > rh else 'Portrait'
                if preferred_orientation != current_orientation:
                    # Swap to match preference
                    self.renderer.set_page_size(rh, rw)
                    if layout is not None:
                        try:
                            layout.page_width, layout.page_height = layout.page_height, layout.page_width
                        except Exception:
                            pass
            except Exception:
                pass
        # CRITICAL FIX: Update temporal bridge with new document
        if self.temporal_bridge:
            self.temporal_bridge.document = document
            # CRITICAL FIX: Attach temporal bridge to document for score renderer access
            document.temporal_bridge = self.temporal_bridge
            # CRITICAL FIX: Don't create initial measure automatically - wait for user interaction
            print("STAFFVIEW: Updated temporal bridge with new document reference")
        # Set widget size immediately and schedule update for future changes
        self._update_widget_size()
        self.schedule_size_update()  # Also schedule for future updates
        self.update()
        
    def setup_ui(self):
        """Setup the UI components"""
        self.setMinimumSize(800, 600)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # CRITICAL FIX: Set resize policy to ensure resizeEvent is called
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Add stretch to push toolbar to bottom
        main_layout.addStretch()
        
        # Create bottom toolbar (temporarily disabled - StaffBarTool class missing)
        # self.toolbar = StaffBarTool(self)
        # self.toolbar.staff_changed.connect(self.on_staff_changed)
        # self.toolbar.clef_changed.connect(self.on_clef_changed)
        # self.toolbar.key_changed.connect(self.on_key_changed)
        # 
        # main_layout.addWidget(self.toolbar)
        self.setLayout(main_layout)
        
        # Ensure the widget size matches page size times zoom so scrollbars can appear
        try:
            base_w = getattr(self.renderer, 'page_width', 800)
            base_h = getattr(self.renderer, 'page_height', 600)
            self.resize(int(base_w * self.zoom_factor), int(base_h * self.zoom_factor))
        except Exception:
            pass
        
    def on_staff_changed(self, settings):
        """Handle staff settings changes"""
        if self.selected_staff:
            self.selected_staff.staff_type = settings['staff_type']
            self.selected_staff.name = settings['name']
            self.selected_staff.abbr = settings['abbr']
            self.update()
            
    def on_clef_changed(self, settings):
        """Handle clef changes"""
        if self.selected_staff:
            self.selected_staff.clef = settings['clef'].lower().split()[0]
            self.update()
            
    def on_key_changed(self, settings):
        """Handle key signature changes"""
        if self.selected_staff:
            self.selected_staff.key = settings['key']
            self.update()
            
    def edit_score_setup(self):
        """Show the score setup dialog"""
        print("=== EDIT_SCORE_SETUP: Method called ===")
        if not self.document:
            print("=== EDIT_SCORE_SETUP: No document available, returning ===")
            return
        # For test development - add a keyboard shortcut to create test score
        # Remove this later when not needed for development
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier:
            print("=== EDIT_SCORE_SETUP: Shift modifier detected, creating test score ===")
            self.create_test_score()
            return
        # Enter setup mode
        print("=== EDIT_SCORE_SETUP: Entering setup mode ===")
        self.enter_setup_mode()
        # Debug print before creating dialog
        print(f"[DEBUG] Creating ScoreSetupDialog, class={ScoreSetupDialog}, id={id(ScoreSetupDialog)}")
        print("=== EDIT_SCORE_SETUP: About to create ScoreSetupDialog ===")
        # Create and show the dialog
        dialog = ScoreSetupDialog(self)
        print("=== EDIT_SCORE_SETUP: ScoreSetupDialog created successfully ===")
        # Critical: Explicitly pass our dialog_settings to ensure they're used
        if hasattr(self, 'dialog_settings') and self.dialog_settings:
            print(f"STAFFVIEW: Directly passing {len(self.dialog_settings.get('added_staves', []))} staves to dialog")
            # Set parent for the dialog to access our settings directly
            dialog.parent_view = self
        # Show the dialog
        self.dialog_open = True
        result = dialog.exec()
        self.dialog_open = False
        print(f"STAFFVIEW: Dialog result: {result} (Accepted={QDialog.DialogCode.Accepted.value})")
        # Check if the dialog was accepted
        if result == QDialog.DialogCode.Accepted.value:
            print("STAFFVIEW: Dialog accepted with Apply, changes already applied")
            # Apply button was clicked - we should now be in edit mode (white)
            # Don't force back to setup mode, stay in current mode
            print("STAFFVIEW: Staying in current mode after Apply button")
        else:
            # Dialog was rejected (Cancel button)
            print("STAFFVIEW: Dialog rejected with Cancel, no changes applied")
            # Cancel button was clicked - ensure we stay in setup mode
            self.is_setup_mode = True
            if hasattr(self.document, 'layout'):
                self.document.layout.set_setup_mode(True)
            print("STAFFVIEW: Forcing SETUP mode after Cancel button")
        
        # Update both menu and toolbar text and visibility to ensure consistency
        if hasattr(self.parent(), 'update_mode_interface_text'):
            print("STAFFVIEW: About to call update_mode_interface_text() in edit_score_setup")
            self.parent().update_mode_interface_text()
            print("STAFFVIEW: Called update_mode_interface_text to ensure all interface text and visibility is correct")
        
        # Ensure UI is updated
        self.update()
        
        return result == QDialog.DialogCode.Accepted.value
            
    def enter_setup_mode(self):
        """Enter score setup mode"""
        # Save the current document state to preserve notation
        if self.document:
            self.preserved_document_state = self.document.to_dict()
            
        print("STAFFVIEW: Switching to SETUP mode (pink)")
        self.is_setup_mode = True
        # CRITICAL FIX: Don't toggle - explicitly set setup mode to avoid flipping back to edit mode
        if hasattr(self.document, 'layout'):
            self.document.layout.set_setup_mode(True)
            print("STAFFVIEW: Explicitly set document layout to SETUP mode")
        else:
            self.document.toggle_setup_mode()  # Fallback
            print("STAFFVIEW: Toggled document setup mode (fallback)")
        print("STAFFVIEW: Entered setup mode")
        print("STAFFVIEW: Toggle button should now say 'Edit Mode'")
        
        # IMPORTANT: Update dialog_settings with current document structure
        # This ensures the dialog shows the current staves when reopening
        if self.dialog_settings is None:
            self.dialog_settings = {}
        
        # Create an up-to-date representation of the document's current staves
        added_staves = []
        
        # ENHANCEMENT: Explicitly track section order
        section_display_order = {}
        if hasattr(self.document, 'section_display_order'):
            section_display_order.update(self.document.section_display_order)
            print(f"STAFFVIEW: Preserved existing section_display_order with {len(section_display_order)} entries")
        
        # CRITICAL FIX: Build staves list in proper display order by collecting all elements first
        all_staff_elements = []
        
        # Collect ungrouped staves with their display order
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'ungrouped_staves'):
            for staff in self.document.layout.ungrouped_staves:
                staff_data = {
                    'instrument_id': staff.instrument_id,
                    'instrument_name': staff.instrument_name,
                    'instrument_abbr': staff.instrument_abbr,
                    'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                    'section': '',  # Ungrouped staff has no section
                    'clef': staff.clef,
                    'plugin': getattr(staff, 'plugin', 'Default'),
                    'staff_data': {
                        'clef': staff.clef,
                        'key': staff.key,
                        'time_signature': staff.time_signature,
                        'section': '',
                        'plugin': getattr(staff, 'plugin', 'Default')
                    }
                }
                
                # CRITICAL: Preserve custom_name and custom_abbr from live staff objects
                if hasattr(staff, 'custom_name') and staff.custom_name:
                    staff_data['custom_name'] = staff.custom_name
                    print(f"STAFFVIEW: Preserved custom_name '{staff.custom_name}' for {staff.instrument_name}")
                else:
                    print(f"STAFFVIEW: No custom_name for {staff.instrument_name}")
                if hasattr(staff, 'custom_abbr') and staff.custom_abbr:
                    staff_data['custom_abbr'] = staff.custom_abbr
                    print(f"STAFFVIEW: Preserved custom_abbr '{staff.custom_abbr}' for {staff.instrument_name}")
                else:
                    print(f"STAFFVIEW: No custom_abbr for {staff.instrument_name} (hasattr={hasattr(staff, 'custom_abbr')}, value={getattr(staff, 'custom_abbr', 'N/A')})")
                
                # Get display order index for ungrouped staff
                display_order = getattr(staff, 'display_order_index', 999)
                all_staff_elements.append((display_order, 'staff', staff_data))
                print(f"STAFFVIEW: Collected ungrouped staff {staff.instrument_name} with display_order={display_order}")
        
        # Collect staves in sections with their section's display order
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'sections'):
            for idx, section in enumerate(self.document.layout.sections):
                # Get section display order
                if hasattr(section, 'display_order_index'):
                    section_order = section.display_order_index
                    section_display_order[section.name] = section_order
                    print(f"STAFFVIEW: Using existing display_order_index {section_order} for section '{section.name}'")
                else:
                    # Fallback: use position in sections list
                    section_order = idx
                    section_display_order[section.name] = section_order
                    print(f"STAFFVIEW: Setting display_order_index {section_order} for section '{section.name}' from layout position")
                    
                for staff in section.staves:
                    staff_data = {
                        'instrument_id': staff.instrument_id,
                        'instrument_name': staff.instrument_name,
                        'instrument_abbr': staff.instrument_abbr,
                        'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                        'section': section.name,
                        'clef': staff.clef,
                        'plugin': getattr(staff, 'plugin', 'Default'),
                        'staff_data': {
                            'clef': staff.clef,
                            'key': staff.key,
                            'time_signature': staff.time_signature,
                            'section': section.name,
                            'plugin': getattr(staff, 'plugin', 'Default')
                        }
                    }
                    
                    # CRITICAL: Preserve custom_name and custom_abbr from live staff objects
                    if hasattr(staff, 'custom_name') and staff.custom_name:
                        staff_data['custom_name'] = staff.custom_name
                        print(f"STAFFVIEW: Preserved custom_name '{staff.custom_name}' for {staff.instrument_name}")
                    if hasattr(staff, 'custom_abbr') and staff.custom_abbr:
                        staff_data['custom_abbr'] = staff.custom_abbr
                        print(f"STAFFVIEW: Preserved custom_abbr '{staff.custom_abbr}' for {staff.instrument_name}")
                    
                    # Use section's display order for all staves in the section
                    all_staff_elements.append((section_order, 'staff', staff_data))
                    print(f"STAFFVIEW: Collected staff {staff.instrument_name} from section '{section.name}' with section_order={section_order}")
        
        # Sort all elements by display order and extract staves
        all_staff_elements.sort(key=lambda x: x[0])  # Sort by display_order_index
        added_staves = [element[2] for element in all_staff_elements]
        
        print(f"STAFFVIEW: Built added_staves in proper display order with {len(added_staves)} staves")
        
        # DEBUG: Check what's in added_staves
        for staff_data in added_staves:
            name = staff_data.get('instrument_name', 'Unknown')
            if 'custom_abbr' in staff_data:
                print(f"STAFFVIEW: added_staves contains custom_abbr='{staff_data['custom_abbr']}' for {name}")
            else:
                print(f"STAFFVIEW: added_staves MISSING custom_abbr for {name}")
        
        # Only update added_staves if we found staves to preserve or if it's not already present
        if added_staves or 'added_staves' not in self.dialog_settings:
            # Update the dialog settings with current staves
            self.dialog_settings['added_staves'] = added_staves
            print(f"STAFFVIEW: Updated dialog_settings with {len(added_staves)} staves")
        else:
            # If no staves were found but we have existing staves in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('added_staves', []))} staves in dialog_settings")
        
        # Update section map in dialog settings
        section_map = {}
        if hasattr(self.document, 'section_map'):
            section_map.update(self.document.section_map)
        
        # Also gather section information from the current layout
        if hasattr(self.document, 'layout'):
            for section in self.document.layout.sections:
                for staff in section.staves:
                    section_map[staff.instrument_id] = section.name
        
        # Only update section_map if we found sections to preserve or if it's not already present
        if section_map or 'section_map' not in self.dialog_settings:
            self.dialog_settings['section_map'] = section_map
            print(f"STAFFVIEW: Updated section_map with {len(section_map)} sections")
        else:
            # If no sections were found but we have existing sections in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('section_map', {}))} sections in dialog_settings")
        
        # ENHANCEMENT: Update section_display_order in dialog settings
        # Only update if we found sections or if it's not already present
        if section_display_order or 'section_display_order' not in self.dialog_settings:
            self.dialog_settings['section_display_order'] = section_display_order
            print(f"STAFFVIEW: Updated dialog_settings with {len(section_display_order)} section display orders")
            for section_name, order_idx in section_display_order.items():
                print(f"  Section '{section_name}' order = {order_idx}")
        else:
            # If no section display orders were found but we have existing ones in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('section_display_order', {}))} section display orders in dialog_settings")
        
        # Create plugin_map similar to section_map
        plugin_map = {}
        if hasattr(self.document, 'layout'):
            # Process ungrouped staves
            for staff in self.document.layout.ungrouped_staves:
                if hasattr(staff, 'plugin') and staff.plugin:
                    plugin_map[staff.instrument_id] = staff.plugin
            
            # Process staves in sections
            for section in self.document.layout.sections:
                for staff in section.staves:
                    if hasattr(staff, 'plugin') and staff.plugin:
                        plugin_map[staff.instrument_id] = staff.plugin
        
        # Only update plugin_map if we found plugins to preserve or if it's not already present
        if plugin_map or 'plugin_map' not in self.dialog_settings:
            self.dialog_settings['plugin_map'] = plugin_map
            print(f"STAFFVIEW: Updated plugin_map with {len(plugin_map)} plugins")
        else:
            # If no plugins were found but we have existing plugins in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('plugin_map', {}))} plugins in dialog_settings")
        
        # Make sure dialog_settings are loaded if we have them
        print(f"STAFFVIEW: dialog_settings present: {self.dialog_settings is not None}")
        if self.dialog_settings:
            print(f"STAFFVIEW: dialog has_unapplied_changes: {self.dialog_settings.get('has_unapplied_changes', False)}")
            if 'section_map' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['section_map'])} sections")
            if 'added_staves' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['added_staves'])} staves")
            if 'section_display_order' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['section_display_order'])} section display orders")
        
        # Just update the UI in setup mode - don't recursively call edit_score_setup from here
        # This allows the Score Setup button to show the dialog without recursion
        self.update()
        
    def enter_edit_mode(self):
        """Enter edit mode"""
        print("STAFFVIEW: Switching to EDIT mode (white)")
        
        # Ensure dialog_settings is initialized as a dictionary
        if self.dialog_settings is None:
            self.dialog_settings = {}
        
        # CRITICAL FIX: Explicitly set the setup mode flag to False
        self.is_setup_mode = False
        
        # Make sure document mode is synced with the view's mode
        if hasattr(self.document, 'layout'):
            # CRITICAL FIX: Explicitly check if we need to change the mode
            if hasattr(self.document.layout, 'is_setup_mode') and self.document.layout.is_setup_mode:
                self.document.layout.set_setup_mode(False)  # Directly set layout mode to False (edit mode)
                print("STAFFVIEW: Explicitly set document layout mode to EDIT")
            elif not hasattr(self.document.layout, 'is_setup_mode'):
                # Fallback if is_setup_mode attribute doesn't exist
                self.document.toggle_setup_mode()
                print("STAFFVIEW: Toggled document setup mode (fallback)")
        else:
            self.document.toggle_setup_mode()  # Fallback to toggle if no layout
            print("STAFFVIEW: Toggled document setup mode (no layout)")
        
        print("STAFFVIEW: Entered edit mode, is_setup_mode is now", self.is_setup_mode)
        
        # CRITICAL FIX: Always update interface when entering edit mode
        print(f"STAFFVIEW: ENTER_EDIT_MODE - FORCING interface update")
        print(f"STAFFVIEW: ENTER_EDIT_MODE - Parent type: {type(self.parent())}")
        print(f"STAFFVIEW: ENTER_EDIT_MODE - Parent has update_mode_interface_text: {hasattr(self.parent(), 'update_mode_interface_text')}")
        
        interface_updated = False
        
        # Method 1: Direct parent call
        if hasattr(self.parent(), 'update_mode_interface_text'):
            print("STAFFVIEW: ENTER_EDIT_MODE - Method 1: Calling parent.update_mode_interface_text()")
            try:
                self.parent().update_mode_interface_text()
                print("STAFFVIEW: ENTER_EDIT_MODE - Method 1: SUCCESS - Called parent.update_mode_interface_text()")
                interface_updated = True
            except Exception as e:
                print(f"STAFFVIEW: ENTER_EDIT_MODE - Method 1: ERROR - {e}")
        
        # Method 2: Try via parent's parent (if this view is inside a dialog)
        if not interface_updated and hasattr(self.parent(), 'parent') and self.parent().parent():
            grandparent = self.parent().parent()
            if hasattr(grandparent, 'update_mode_interface_text'):
                print("STAFFVIEW: ENTER_EDIT_MODE - Method 2: Calling grandparent.update_mode_interface_text()")
                try:
                    grandparent.update_mode_interface_text()
                    print("STAFFVIEW: ENTER_EDIT_MODE - Method 2: SUCCESS - Called grandparent.update_mode_interface_text()")
                    interface_updated = True
                except Exception as e:
                    print(f"STAFFVIEW: ENTER_EDIT_MODE - Method 2: ERROR - {e}")
        
        # Method 3: Try accessing main window through QApplication
        if not interface_updated:
            try:
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    main_windows = [w for w in app.topLevelWidgets() if w.__class__.__name__ == 'MainWindow']
                    if main_windows:
                        main_window = main_windows[0]
                        if hasattr(main_window, 'update_mode_interface_text'):
                            print("STAFFVIEW: ENTER_EDIT_MODE - Method 3: Calling main_window.update_mode_interface_text()")
                            main_window.update_mode_interface_text()
                            print("STAFFVIEW: ENTER_EDIT_MODE - Method 3: SUCCESS - Called main_window.update_mode_interface_text()")
                            interface_updated = True
            except Exception as e:
                print(f"STAFFVIEW: ENTER_EDIT_MODE - Method 3: ERROR - {e}")
        
        if not interface_updated:
            print("STAFFVIEW: ENTER_EDIT_MODE - WARNING: Could not update interface through any method!")
        
        # First apply current staff structure from the setup dialog if available
        if self.dialog_settings and 'added_staves' in self.dialog_settings:
            print("STAFFVIEW: Applying current staff structure from dialog settings")
            
            # Explicitly clear the document layout first
            if hasattr(self.document, 'layout'):
                print("STAFFVIEW: Clearing document layout before rebuilding")
                self.document.layout.sections = []
                self.document.layout.ungrouped_staves = []
            
            # ENHANCEMENT: Ensure section_display_order is transferred to the document
            if 'section_display_order' in self.dialog_settings and self.dialog_settings['section_display_order']:
                if not hasattr(self.document, 'section_display_order'):
                    self.document.section_display_order = {}
                self.document.section_display_order.update(self.dialog_settings['section_display_order'])
                print(f"STAFFVIEW: Transferring {len(self.dialog_settings['section_display_order'])} section display orders to document")
                for section_name, order_idx in self.dialog_settings['section_display_order'].items():
                    print(f"  Section '{section_name}' order = {order_idx}")
            
            # Apply the current staves only (not including removed ones)
            self.apply_setup_options(self.dialog_settings)
            
            # Print the current staves in the document
            current_staves = self.get_current_staff_ids()
            print(f"STAFFVIEW: Current staves after applying dialog settings: {current_staves}")
        
        # Restore preserved notation if available, but only for existing staves
        if hasattr(self, 'preserved_document_state') and self.preserved_document_state:
            # This will only restore notation for staves that still exist in the document
            self.restore_notation_from_preserved_state()
        
        # CRITICAL FIX: Double-check that we're actually in edit mode
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'is_setup_mode'):
            if self.document.layout.is_setup_mode:
                print("STAFFVIEW: WARNING - Document still in setup mode after enter_edit_mode! Forcing mode change...")
                self.document.layout.set_setup_mode(False)
        
        # ENHANCEMENT: Print debug info about sections
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'sections'):
            print(f"STAFFVIEW: Document has {len(self.document.layout.sections)} sections after entering edit mode")
            for idx, section in enumerate(self.document.layout.sections):
                display_order = getattr(section, 'display_order_index', 0)
                print(f"  Section {idx}: '{section.name}' with {len(section.staves)} staves, display_order_index={display_order}")
        
        # Initialize measure manager for proper measure/barline system
        self._initialize_measure_manager()
        
        # ENHANCED: Call temporal bridge's enter_edit_mode to create initial measure
        print(f"STAFFVIEW: Temporal bridge check - hasattr: {hasattr(self, 'temporal_bridge')}, bridge: {getattr(self, 'temporal_bridge', None)}")
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            print("STAFFVIEW: Calling temporal bridge enter_edit_mode to create initial measure")
            try:
                self.temporal_bridge.enter_edit_mode()
                print("STAFFVIEW: Successfully called temporal bridge enter_edit_mode")
                
                # CRITICAL FIX: Force layout refresh to make score responsive immediately
                print("STAFFVIEW: Forcing layout refresh after entering edit mode")
                
                # Keep renderer page size from preferences; do not change on entering edit mode
                if hasattr(self, 'renderer') and self.renderer:
                    print("STAFFVIEW: Keeping renderer page size from preferences on enter_edit_mode")
                
                # Force temporal bridge to recalculate layout
                if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                    print("STAFFVIEW: Forcing temporal bridge layout refresh")
                    self.temporal_bridge._force_layout_refresh()

                    # New: Immediately refresh measure number settings and repaint so positions are correct without user click
                    if hasattr(self.renderer, 'measure_number_manager') and self.renderer.measure_number_manager:
                        try:
                            self.renderer.measure_number_manager.refresh_settings(self.renderer)
                            print("STAFFVIEW: Refreshed measure number settings on enter_edit_mode")
                        except Exception as e:
                            print(f"STAFFVIEW: Error refreshing measure number settings: {e}")

                    # Ensure measures are justified before the first paint so numbers get correct widths
                    try:
                        if hasattr(self.temporal_bridge, '_ensure_all_measures_justified'):
                            self.temporal_bridge._ensure_all_measures_justified()
                            print("STAFFVIEW: Ensured all measures justified before initial paint")
                    except Exception as e:
                        print(f"STAFFVIEW: Error ensuring measures justified: {e}")

                # Trigger immediate geometry update and repaint so measure numbers position correctly
                try:
                    if hasattr(self, 'updateGeometry'):
                        self.updateGeometry()
                except Exception:
                    pass
                self.update()
                
                # Force view update
                print("STAFFVIEW: Forcing UI update in edit mode")
                self.update()

                # Schedule a deferred repaint after the event loop to catch any late layout changes
                try:
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, self.update)
                except Exception:
                    pass
                
            except Exception as e:
                print(f"STAFFVIEW: Error calling temporal bridge enter_edit_mode: {e}")
        else:
            print("STAFFVIEW: No temporal bridge available for enter_edit_mode")
        
        # --- NEW: Ensure dynamic layout is immediately responsive in edit mode ---
        # Do not override renderer logical page size with widget size; keep preferences
        if hasattr(self, 'renderer') and self.renderer:
            try:
                print("STAFFVIEW: Preserving renderer page size after entering edit mode")
            except Exception as e:
                print(f"STAFFVIEW: Error while preserving renderer page size: {e}")
        # 2. Force layout refresh in temporal bridge
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge and hasattr(self.temporal_bridge, '_force_layout_refresh'):
            try:
                self.temporal_bridge._force_layout_refresh()
                print("STAFFVIEW: Forced layout refresh in temporal bridge after entering edit mode")
            except Exception as e:
                print(f"STAFFVIEW: Error forcing layout refresh: {e}")
        # 3. Update the view
        self.update()
        print("STAFFVIEW: Forcing UI update in edit mode")
        
    def restore_notation_from_preserved_state(self):
        """Restore notation data from preserved state to existing staves"""
        try:
            if not hasattr(self, 'preserved_document_state') or not self.preserved_document_state:
                print("STAFFVIEW: No preserved document state to restore")
                return
                
            print("STAFFVIEW: Restoring notation from preserved state")
            
            # This method would typically restore notation data from the preserved state
            # For now, we'll implement a simple placeholder that doesn't break the application
            # In the future, this could be expanded to restore actual notation content
            
            if hasattr(self.document, 'from_dict'):
                # If the document has a from_dict method, we could use it to restore state
                # But for safety, we'll skip this for now to avoid overwriting current changes
                print("STAFFVIEW: Document has from_dict method, but skipping full restore for safety")
            else:
                print("STAFFVIEW: Document doesn't have from_dict method")
                
            print("STAFFVIEW: Notation restoration completed (placeholder implementation)")
            
        except Exception as e:
            print(f"STAFFVIEW: Error restoring notation from preserved state: {e}")
            # Continue execution even if restoration fails

    def _initialize_measure_manager(self):
        """Initialize the measure manager for proper measure/barline system"""
        try:
            # Safety check: ensure document exists before initializing measure manager
            if not self.document:
                print("STAFFVIEW: Cannot initialize measure manager - document is None")
                self.measure_manager = None
                return
            
            from .measure_manager import MeasureManager
            self.measure_manager = MeasureManager(self.document)
            
            # Ensure document has measures attribute
            if not hasattr(self.document, 'measures'):
                print("STAFFVIEW: Document missing measures attribute - creating it")
                self.document.measures = {}
            
            # Check document measures state
            print(f"STAFFVIEW: Document measures before check: {getattr(self.document, 'measures', 'NOT_FOUND')}")
            
            # RESTRUCTURE: No automatic measure creation
            print("STAFFVIEW: Measure manager initialized - no automatic measures (created on first user click)")
            
            print("STAFFVIEW: Initialized measure manager - ready for user-created barlines")
            
            # CRITICAL: Connect temporal bridge to MeasureManager for proper layout integration
            self._connect_temporal_bridge_to_measure_manager()
            
        except Exception as e:
            print(f"STAFFVIEW: Error initializing measure manager: {e}")
            import traceback
            traceback.print_exc()
            self.measure_manager = None
    
    def _ensure_initial_barline_1(self):
        """
\\        Create the initial state in edit mode according to Preferences:
        - If Initial MPS is enabled, BarlineTemporalBridge.enter_edit_mode handles first-system fill.
        - If disabled, create a single compact measure with final barline.
        """
        print("STAFFVIEW: Preparing initial edit-mode state per Initial MPS preference")
        
        # Safety checks
        if not self.document:
            print("STAFFVIEW: Cannot create initial measure - no document")
            return
            
        if not hasattr(self.temporal_bridge, '_ensure_initial_measure_via_manager'):
            print("STAFFVIEW: Cannot create initial measure - temporal bridge missing method")
            return
        
        # Check if we already have measures (skip if they exist)
        if hasattr(self.document, 'measures') and self.document.measures:
            measures_count = len(self.document.measures)
            print(f"STAFFVIEW: Document already has {measures_count} measures - skipping initial measure creation")
            return
        
        # Defer to temporal bridge enter_edit_mode for actual creation logic
        try:
            if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                self.temporal_bridge.enter_edit_mode()
        except Exception as e:
            print(f"STAFFVIEW: Error initializing initial measures: {e}")
            import traceback
            traceback.print_exc()
    
    def _connect_temporal_bridge_to_measure_manager(self):
        """Connect the temporal bridge to the MeasureManager for integrated layout"""
        try:
            if hasattr(self, 'temporal_bridge') and self.temporal_bridge and self.measure_manager:
                # Connect the measure manager to the temporal bridge
                self.temporal_bridge.measure_manager = self.measure_manager
                
                # Store reference to staff view in document for temporal bridge access
                if self.document:
                    self.document.staff_view = self
                
                print("STAFFVIEW: Connected temporal bridge to MeasureManager for responsive layout")
                
                # Don't create initial measure automatically - wait for user interaction
                print("STAFFVIEW: Connected temporal bridge with MeasureManager integration")
            else:
                print("STAFFVIEW: Could not connect temporal bridge to MeasureManager - missing components")
        except Exception as e:
            print(f"STAFFVIEW: Error connecting temporal bridge to MeasureManager: {e}")
            import traceback
            traceback.print_exc()
    
    def preserve_section_data(self):
        """Preserve section data and staff attributes before opening the setup dialog"""
        # Ensure dialog_settings is initialized as a dictionary
        if self.dialog_settings is None:
            self.dialog_settings = {}
            
        # Create a structure to store the current staves in the document
        added_staves = []
        
        # First process ungrouped staves
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'ungrouped_staves'):
            for staff in self.document.layout.ungrouped_staves:
                # FIXED: Ensure clef is directly accessible in the staff_data dictionary
                staff_data = {
                    'instrument_id': staff.instrument_id,
                    'instrument_name': staff.instrument_name,
                    'instrument_abbr': staff.instrument_abbr,
                    'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                    'section': '',  # Ungrouped staff has no section
                    'clef': staff.clef,  # FIXED: Add clef directly to the top level
                    'plugin': getattr(staff, 'plugin', 'Default'),  # Add plugin information
                    'staff_data': {
                        'clef': staff.clef,
                        'key': staff.key,
                        'time_signature': staff.time_signature,
                        'section': '',
                        'plugin': getattr(staff, 'plugin', 'Default')  # Add plugin information in staff_data
                    }
                }
                
                # ENHANCEMENT: Double-check that clef is consistently set for both locations
                if staff_data['clef'] != staff_data['staff_data']['clef']:
                    print(f"WARNING: Fixing clef inconsistency for {staff.instrument_name}: " +
                          f"{staff_data['clef']} vs {staff_data['staff_data']['clef']}")
                    staff_data['staff_data']['clef'] = staff_data['clef']
                    
                added_staves.append(staff_data)
                print(f"STAFFVIEW: Preserved ungrouped staff {staff.instrument_name} with clef={staff.clef} and plugin={getattr(staff, 'plugin', 'Default')} for dialog settings")
        
        # Then process staves in sections
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                for staff in section.staves:
                    # FIXED: Ensure clef is directly accessible in the staff_data dictionary
                    staff_data = {
                        'instrument_id': staff.instrument_id,
                        'instrument_name': staff.instrument_name,
                        'instrument_abbr': staff.instrument_abbr,
                        'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                        'section': section.name,
                        'clef': staff.clef,  # FIXED: Add clef directly to the top level
                        'plugin': getattr(staff, 'plugin', 'Default'),  # Add plugin information
                        'staff_data': {
                            'clef': staff.clef,
                            'key': staff.key,
                            'time_signature': staff.time_signature,
                            'section': section.name,
                            'plugin': getattr(staff, 'plugin', 'Default')  # Add plugin information in staff_data
                        }
                    }
                    
                    # ENHANCEMENT: Double-check that clef is consistently set for both locations
                    if staff_data['clef'] != staff_data['staff_data']['clef']:
                        print(f"WARNING: Fixing clef inconsistency for {staff.instrument_name} in section '{section.name}': " +
                              f"{staff_data['clef']} vs {staff_data['staff_data']['clef']}")
                        staff_data['staff_data']['clef'] = staff_data['clef']
                        
                    added_staves.append(staff_data)
                    print(f"STAFFVIEW: Preserved staff {staff.instrument_name} from section '{section.name}' with clef={staff.clef} and plugin={getattr(staff, 'plugin', 'Default')} for dialog settings")
        
        # Only update added_staves if we found staves to preserve or if it's not already present
        if added_staves or 'added_staves' not in self.dialog_settings:
            # Update the dialog settings with current staves
            self.dialog_settings['added_staves'] = added_staves
            print(f"STAFFVIEW: Updated dialog_settings with {len(added_staves)} staves")
        else:
            # If no staves were found but we have existing staves in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('added_staves', []))} staves in dialog_settings")
        
        # Update section map in dialog settings
        section_map = {}
        if hasattr(self.document, 'section_map'):
            section_map.update(self.document.section_map)
        
        # Also gather section information from the current layout
        if hasattr(self.document, 'layout'):
            for section in self.document.layout.sections:
                for staff in section.staves:
                    section_map[staff.instrument_id] = section.name
        
        # Only update section_map if we found sections to preserve or if it's not already present
        if section_map or 'section_map' not in self.dialog_settings:
            self.dialog_settings['section_map'] = section_map
            print(f"STAFFVIEW: Updated section_map with {len(section_map)} sections")
        else:
            # If no sections were found but we have existing sections in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('section_map', {}))} sections in dialog_settings")
        
        # Update section display order
        if hasattr(self.document, 'section_display_order'):
            self.dialog_settings['section_display_order'] = self.document.section_display_order.copy()
            print(f"STAFFVIEW: Updated dialog_settings with {len(self.dialog_settings.get('section_display_order', {}))} section display orders")
            for section_name, order_idx in self.dialog_settings['section_display_order'].items():
                print(f"  Section '{section_name}' order = {order_idx}")
        
        # Create plugin_map similar to section_map
        plugin_map = {}
        if hasattr(self.document, 'layout'):
            # Process ungrouped staves
            for staff in self.document.layout.ungrouped_staves:
                if hasattr(staff, 'plugin') and staff.plugin:
                    plugin_map[staff.instrument_id] = staff.plugin
            
            # Process staves in sections
            for section in self.document.layout.sections:
                for staff in section.staves:
                    if hasattr(staff, 'plugin') and staff.plugin:
                        plugin_map[staff.instrument_id] = staff.plugin
        
        # Only update plugin_map if we found plugins to preserve or if it's not already present
        if plugin_map or 'plugin_map' not in self.dialog_settings:
            self.dialog_settings['plugin_map'] = plugin_map
            print(f"STAFFVIEW: Updated plugin_map with {len(plugin_map)} plugins")
        else:
            # If no plugins were found but we have existing plugins in dialog_settings, keep them
            print(f"STAFFVIEW: Kept existing {len(self.dialog_settings.get('plugin_map', {}))} plugins in dialog_settings")
        
        # Make sure dialog_settings are loaded if we have them
        print(f"STAFFVIEW: dialog_settings present: {self.dialog_settings is not None}")
        if self.dialog_settings:
            print(f"STAFFVIEW: dialog has_unapplied_changes: {self.dialog_settings.get('has_unapplied_changes', False)}")
            if 'section_map' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['section_map'])} sections")
            if 'added_staves' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['added_staves'])} staves")
            if 'section_display_order' in self.dialog_settings:
                print(f"STAFFVIEW: dialog has {len(self.dialog_settings['section_display_order'])} section display orders")
        
        # Just update the UI in setup mode - don't recursively call edit_score_setup from here
        # This allows the Score Setup button to show the dialog without recursion
        self.update()

    def apply_setup_options(self, options):
        print(f"[DEBUG] StaffView.apply_setup_options called with options: {list(options.keys())}")
        # Save state before applying setup changes for undo/redo functionality
        # This is the main point where we save meaningful undo states
        if hasattr(self, 'document') and hasattr(self.document, 'save_state'):
            # Add context to indicate this is an Apply operation
            if hasattr(self.document, '_undo_context'):
                self.document._undo_context = "Apply Setup Changes"
            self.document.save_state("Apply Setup Changes")
            print("UNDO: Saved state before applying setup changes")
            
        # Check if we should force setup mode
        force_setup_mode = options.get('force_setup_mode', False)
        if force_setup_mode:
            print("APPLY_SETUP: Forcing setup mode")
            self.is_setup_mode = True
            
        # Preserve staff types flag (default to true if not specified)
        preserve_staff_types = options.get('preserve_staff_types', True)
        print(f"APPLY_SETUP: preserve_staff_types = {preserve_staff_types}")
            
        # Save section data from options explicitly to document
        if 'section_map' in options:
            if not hasattr(self.document, 'section_map'):
                self.document.section_map = {}
            self.document.section_map.update(options['section_map'])
            print(f"APPLY_SETUP: Updated document section_map with {len(options['section_map'])} entries")
            
        # Save staff type data from options explicitly to document
        if 'staff_type_map' in options and preserve_staff_types:
            if not hasattr(self.document, 'staff_type_map'):
                self.document.staff_type_map = {}
            self.document.staff_type_map.update(options['staff_type_map'])
            print(f"APPLY_SETUP: Updated document staff_type_map with {len(options['staff_type_map'])} entries")
            
            # Verify each staff in added_staves has the correct type and clef based on staff_type_map
            if 'added_staves' in options:
                for staff in options['added_staves']:
                    instrument_id = staff.get('instrument_id', '')
                    if instrument_id and instrument_id in options['staff_type_map']:
                        staff_type = options['staff_type_map'][instrument_id]
                        if staff.get('staff_type', '') != staff_type:
                            staff['staff_type'] = staff_type
                            print(f"APPLY_SETUP: Updated {staff.get('instrument_name', 'Unknown')} to type={staff_type} from staff_type_map")
                            
        # Save plugin data from options explicitly to document
        if 'plugin_map' in options:
            if not hasattr(self.document, 'plugin_map'):
                self.document.plugin_map = {}
            self.document.plugin_map.update(options['plugin_map'])
            print(f"APPLY_SETUP: Updated document plugin_map with {len(options['plugin_map'])} entries")
            
            # CRITICAL FIX: Update actual staff objects with plugin information
            if hasattr(self.document, 'layout'):
                # Update ungrouped staves
                for staff in self.document.layout.ungrouped_staves:
                    if staff.instrument_id in options['plugin_map']:
                        plugin = options['plugin_map'][staff.instrument_id]
                        staff.plugin = plugin
                        print(f"APPLY_SETUP: Updated staff object {staff.instrument_name} plugin to {plugin}")
                
                # Update staves in sections
                for section in self.document.layout.sections:
                    for staff in section.staves:
                        if staff.instrument_id in options['plugin_map']:
                            plugin = options['plugin_map'][staff.instrument_id]
                            staff.plugin = plugin
                            print(f"APPLY_SETUP: Updated staff object {staff.instrument_name} plugin to {plugin}")
            
            # Verify each staff in added_staves has the correct plugin based on plugin_map
            if 'added_staves' in options:
                for staff in options['added_staves']:
                    instrument_id = staff.get('instrument_id', '')
                    if instrument_id and instrument_id in options['plugin_map']:
                        plugin = options['plugin_map'][instrument_id]
                        if staff.get('plugin', '') != plugin:
                            staff['plugin'] = plugin
                            print(f"APPLY_SETUP: Updated {staff.get('instrument_name', 'Unknown')} plugin to {plugin} from plugin_map")
                            # Ensure plugin is synced with staff_data too
                            if 'staff_data' in staff:
                                staff['staff_data']['plugin'] = plugin
        
        # Always fully rebuild the score layout when applying options
        # This ensures removed staves aren't accidentally kept in the document
        if hasattr(self.document, 'layout'):
            print("APPLY_SETUP: Resetting document layout to ensure removed staves don't persist")
            # Explicitly reset the layout sections and ungrouped staves
            self.document.layout.sections = []
            self.document.layout.ungrouped_staves = []
            
            # Make sure the document's setup mode matches the view's mode
            if hasattr(self.document.layout, 'set_setup_mode'):
                setup_mode = force_setup_mode or self.is_setup_mode
                self.document.layout.set_setup_mode(setup_mode)
                print(f"APPLY_SETUP: Explicitly set document layout setup mode to {setup_mode}")
                
                # Force 5 measures for setup mode display
                if setup_mode and hasattr(self.document.layout, 'set_measure_count'):
                    self.document.layout.set_measure_count(5)
                    print("APPLY_SETUP: Forcing 5 measures for setup mode display")
        
        # IMPORTANT: When applying changes from reordering, we need to ensure
        # the ordering is respected exactly as in the options
        if 'immediate_apply' in options and options['immediate_apply'] and 'added_staves' in options:
            print("APPLY_SETUP: Immediate apply requested - ensuring exact staff order is maintained")
        
        # Apply setup options to rebuild the score with current staves
        self.document.apply_setup_options(options)
        
        # Save dialog settings
        self.dialog_settings = options
        
        # Print information about current document state
        if hasattr(self.document, 'layout'):
            num_staves = len(self.document.layout.ungrouped_staves)
            for section in self.document.layout.sections:
                num_staves += len(section.staves)
            print(f"APPLY_SETUP: Document now has {num_staves} total staves")
            
            # Double-check that the document's setup mode matches the view's mode
            if hasattr(self.document.layout, 'is_setup_mode'):
                print(f"APPLY_SETUP: Document layout setup mode is {self.document.layout.is_setup_mode}")
                setup_mode = force_setup_mode or self.is_setup_mode
                if self.document.layout.is_setup_mode != setup_mode:
                    print(f"APPLY_SETUP: Mode mismatch detected, fixing by setting document layout to {setup_mode}")
                    self.document.layout.set_setup_mode(setup_mode)
                    
                    # Force 5 measures for setup mode display
                    if setup_mode and hasattr(self.document.layout, 'set_measure_count'):
                        self.document.layout.set_measure_count(5)
                        print("APPLY_SETUP: Forcing 5 measures for setup mode display")
        
        # Check for immediate apply flag
        if options.get('immediate_apply', False) or options.get('force_render', False):
            print("[DEBUG] StaffView: Immediate apply requested, calling update()")
            if hasattr(self.document, 'rebuild_score'):
                self.document.rebuild_score()
                print("[DEBUG] StaffView: Called document.rebuild_score()")
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'set_document'):
                self.renderer.set_document(self.document)
                print("[DEBUG] StaffView: Updated renderer with latest document state")
            self.update()
            print("[DEBUG] StaffView: update() called for immediate repaint")
        
        # Update UI without changing mode
        self.update()

    def paintEvent(self, event):
        """Draw the score with proper page-based rendering and zoom support"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Check if we're in setup mode
        is_in_setup = self.is_setup_mode
        
        # Get current view mode
        view_mode = self.renderer.get_view_mode()
        
        # Fill background based on mode
        background_rect = QRect(0, 0, self.width(), self.height())
        if is_in_setup:
            # Pink background for setup mode
            painter.fillRect(background_rect, QColor(255, 240, 240))  # Light pink
            print("PAINT: Drawing SETUP mode pink background")
        else:
            # White background for edit mode
            painter.fillRect(background_rect, QColor(255, 255, 255))  # White
            print("PAINT: Drawing EDIT mode white background")
        
        # PAGE-BASED RENDERING: Render based on view mode
        if is_in_setup:
            # In setup mode we always show page view (no continuous)
            self._render_page_down_mode(painter, background_rect, is_in_setup)
        elif view_mode == "continuous":
            # Continuous mode: render all content in one long scrollable view
            self._render_continuous_mode(painter, background_rect, is_in_setup)
        elif view_mode == "page_across":
            # Page across mode: render multiple pages side by side
            self._render_page_across_mode(painter, background_rect, is_in_setup)
        else:
            # Page down mode (default): render one page at a time
            self._render_page_down_mode(painter, background_rect, is_in_setup)
        
        # REMOVED: Conflicting barline drawing call - ScoreRenderer handles all barline drawing
        # The main barline rendering is done by ScoreRenderer._render_connecting_barlines
        
        # Render element selection highlights
        if hasattr(self, 'element_selection'):
            self.element_selection.render_all_selections(painter)
        
        # Draw selection overlay only if explicitly enabled (default False)
        if getattr(self, 'show_selection_overlay', False):
            self.draw_selected_barlines(painter)
        
        # If a staff is selected in setup mode, highlight it
        if is_in_setup and self.selected_staff:
            # Set up a semitransparent highlight color
            highlight_color = QColor(200, 200, 255, 100)  # Light blue with alpha
            
            # Draw the highlight area
            if isinstance(self.selected_staff, GrandStaff):
                # Highlight the entire grand staff
                painter.fillRect(
                    self.document.layout.left_margin,
                    self.selected_staff.y_position,
                    self.width() - self.document.layout.left_margin - self.document.layout.right_margin,
                    self.selected_staff.height,
                    highlight_color
                )
            else:
                # Highlight a single staff
                painter.fillRect(
                    self.document.layout.left_margin,
                    self.selected_staff.y_position,
                    self.width() - self.document.layout.left_margin - self.document.layout.right_margin,
                    self.selected_staff.height,
                    highlight_color
                )
        
        # Draw drag selection rectangle if active
        if self.is_drag_selecting and self.drag_select_rect:
            painter.save()
            painter.setPen(QPen(QColor(0, 0, 255), 1, Qt.PenStyle.DashLine))  # Blue dashed border
            painter.setBrush(QColor(0, 0, 255, 30))  # Light blue fill
            painter.drawRect(self.drag_select_rect)
            painter.restore()
    
        # Draw orange overlay lines for selected barlines across all staves
        # Gate behind a flag to avoid drawing page-height overlays. The renderer
        # already highlights selected barlines at their exact staff heights.
        if getattr(self, 'show_selection_overlay', False):
            self._draw_selected_barline_overlay(painter)
        
        # Don't schedule size updates during paint events - causes flickering
        # Size updates should only happen when content actually changes, not on every paint
    
    def _render_continuous_mode(self, painter, viewport_rect, is_in_setup):
        """True continuous mode: no pages/margins/wrap. Horizontal lane only."""
        # Fill background
        painter.fillRect(viewport_rect, QColor(255, 255, 255))
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(self.zoom_factor, self.zoom_factor)

        # Ask bridge to enforce continuous positions (no wrap)
        try:
            if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                self.temporal_bridge.ensure_continuous_positions()
        except Exception as e:
            print(f"CONTINUOUS: ensure_continuous_positions error: {e}")

        # Build a simple infinite-lane rect and ask renderer to draw inside it
        # We skip margins and page, passing a large viewport box.
        lane_rect = QRect(0, 0, max(2000, viewport_rect.width()), viewport_rect.height())
        try:
            if hasattr(self.renderer, 'render_continuous'):
                self.renderer.render_continuous(painter, lane_rect)
            else:
                # Fallback: call standard render with our lane rect
                mode = 'setup' if is_in_setup else 'edit'
                self.renderer.render_score(painter, lane_rect, mode)
        except Exception as e:
            print(f"CONTINUOUS: renderer.render_continuous fallback error: {e}")

        painter.restore()
        
        # Don't schedule size updates during paint events - causes flickering
        # Size updates should only happen when content actually changes, not on every paint
    
    def _render_page_across_mode(self, painter, viewport_rect, is_in_setup):
        """Render multiple pages side by side"""
        print("PAGE_RENDER: Rendering in page across mode")
        
        # Safety check: ensure renderer exists
        if not hasattr(self, 'renderer') or self.renderer is None:
            print("PAGE_RENDER ERROR: Renderer not available")
            return
        
        # Ensure page_across_mode is set on renderer
        if hasattr(self.renderer, 'set_page_across_mode'):
            # Ensure page_across_mode is enabled (but don't call if already set to avoid recursion)
            if not getattr(self.renderer, 'page_across_mode', False):
                self.renderer.set_page_across_mode(True)
        
        # Use renderer/document page size instead of hardcoded A4
        MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI
        base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
        base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
        page_margin = 20  # Space between pages (logical)
        
        # Calculate how many pages fit horizontally
        available_width = viewport_rect.width()
        if available_width <= 0:
            available_width = 800  # Fallback width
        pages_per_row = max(1, int(available_width / ((base_page_width + page_margin) * self.zoom_factor)))
        
        # Get total number of pages needed and detect changes
        old_total = getattr(self, 'total_pages', 1)
        new_total = max(1, self._calculate_total_pages())
        if old_total != new_total:
            self.total_pages = new_total
            # Schedule size update after paint completes (use longer delay to prevent flickering)
            QTimer.singleShot(100, self.schedule_size_update)
        else:
            self.total_pages = new_total
        
        # Calculate rows needed
        rows_needed = (self.total_pages + pages_per_row - 1) // pages_per_row
        
        for page_index in range(self.total_pages):
            row = page_index // pages_per_row
            col = page_index % pages_per_row
            
            page_x = int(col * (base_page_width + page_margin) * self.zoom_factor)
            page_y = int(row * (base_page_height + page_margin) * self.zoom_factor)
            
            painter.save()
            painter.translate(page_x, page_y)
            painter.scale(self.zoom_factor, self.zoom_factor)
            
            page_rect = QRect(0, 0, base_page_width, base_page_height)
            painter.fillRect(page_rect, QColor(255, 255, 255))
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawRect(page_rect)
            painter.setClipRect(page_rect)
            
            # Use current renderer margins if available
            base_margins = getattr(self.renderer, 'margins', {
                'left': int(25 * MM_TO_PIXELS),
                'right': int(25 * MM_TO_PIXELS),
                'top': int(20 * MM_TO_PIXELS),
                'bottom': int(20 * MM_TO_PIXELS)
            })
            # Keep renderer logical page size from preferences; do not reset per paint
            self.renderer.set_margins(base_margins)
            if hasattr(self.renderer, 'current_page'):
                self.renderer.current_page = page_index
            # page_down_mode is already set to True by set_page_across_mode() for pagination filtering
            # No need to call set_page_down_mode() here as it would disable page_across_mode
            mode = 'setup' if is_in_setup else 'edit'
            self.renderer.render_score(painter, page_rect, mode)
            
            # Footer page number
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, f"Page {page_index + 1}/{self.total_pages}")
            
            painter.restore()
    
    def _render_page_down_mode(self, painter, viewport_rect, is_in_setup):
        """Render pages stacked vertically so scrolling reveals additional pages"""
        print("PAGE_RENDER: Rendering in page down mode")

        # Ensure total_pages is up to date (but don't resize during paint - causes flicker)
        old_total = getattr(self, 'total_pages', 1)
        new_total = max(1, self._calculate_total_pages())
        if old_total != new_total:
            self.total_pages = new_total
            # Schedule size update after paint completes (use longer delay to prevent flickering)
            QTimer.singleShot(100, self.schedule_size_update)
        else:
            self.total_pages = new_total
        if self.current_page >= self.total_pages:
            self.current_page = self.total_pages - 1

        # Page metrics
        MM_TO_PIXELS = 3.78  # 96 DPI
        base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
        base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
        page_margin = 20  # gap between stacked pages (logical px)

        # Center horizontally; top of first page vertically
        page_x = (viewport_rect.width() - int(base_page_width * self.zoom_factor)) // 2
        start_y = int(self.page_offset_y * self.zoom_factor)

        # CRITICAL FIX: Render ALL pages stacked vertically for scrolling (not just current page)
        # This allows the scroll area to show any page based on scroll position
        for page_index in range(self.total_pages):
            painter.save()
            offset_y = start_y + int(page_index * (base_page_height + page_margin) * self.zoom_factor)
            painter.translate(page_x, offset_y)
            painter.scale(self.zoom_factor, self.zoom_factor)

            page_rect = QRect(0, 0, base_page_width, base_page_height)
            painter.fillRect(page_rect, QColor(255, 255, 255))
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawRect(page_rect)
            painter.setClipRect(page_rect)

            # Margins and renderer page index
            base_margins = getattr(self.renderer, 'margins', {
                'left': int(25 * MM_TO_PIXELS),
                'right': int(25 * MM_TO_PIXELS),
                'top': int(20 * MM_TO_PIXELS),
                'bottom': int(20 * MM_TO_PIXELS)
            })
            self.renderer.set_margins(base_margins)
            if hasattr(self.renderer, 'current_page'):
                self.renderer.current_page = page_index
            # Set page_down_mode for renderer filtering
            if hasattr(self.renderer, 'set_page_down_mode'):
                self.renderer.set_page_down_mode(True)
            mode = 'setup' if is_in_setup else 'edit'
            self.renderer.render_score(painter, page_rect, mode)

            # Footer page number
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, f"Page {page_index + 1}/{self.total_pages}")
            painter.restore()
    
    def _render_single_page(self, painter, page_rect, page_num, is_in_setup):
        """Render content for a single page with proper A4 dimensions and margins and unified zoom"""
        painter.save()
        
        # A4 standard margins: 25mm left/right, 20mm top/bottom
        MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI
        A4_MARGIN_LEFT_MM = 25
        A4_MARGIN_RIGHT_MM = 25
        A4_MARGIN_TOP_MM = 20
        A4_MARGIN_BOTTOM_MM = 20
        
        # Convert margins to pixels
        base_margins = {
            'left': int(A4_MARGIN_LEFT_MM * MM_TO_PIXELS),    # ≈ 95 pixels
            'right': int(A4_MARGIN_RIGHT_MM * MM_TO_PIXELS),  # ≈ 95 pixels
            'top': int(A4_MARGIN_TOP_MM * MM_TO_PIXELS),      # ≈ 76 pixels
            'bottom': int(A4_MARGIN_BOTTOM_MM * MM_TO_PIXELS) # ≈ 76 pixels
        }
        
        # Set clipping region to page boundaries
        painter.setClipRect(page_rect)
        
        # Pass margins; keep renderer page size already set from preferences
        self.renderer.set_margins(base_margins)
        mode = 'setup' if is_in_setup else 'edit'
        self.renderer.render_score(painter, page_rect, mode)
        
        painter.restore()
    
    def _calculate_total_pages(self):
        """Calculate total number of pages from current preferences and layout"""
        if not self.document or not hasattr(self.document, 'measures'):
            return 1

        # Count measures
        if isinstance(self.document.measures, dict):
            measure_count = len([k for k in self.document.measures.keys() if isinstance(k, int)])
        else:
            measure_count = len(self.document.measures) if self.document.measures else 0

        # Measures per system
        from PyQt6.QtCore import QSettings
        try:
            mps = int(QSettings("ONOTE", "Preferences").value("layout/default_measures_per_system", 4))
        except Exception:
            mps = 4
        mps = max(1, min(32, mps))

        # Systems per page from vertical spacing and margins
        # CRITICAL FIX: Use wrapping_spacing (same as rendering) for pagination calculation
        try:
            wrapping_spacing = 80  # Default
            if hasattr(self.document, 'settings') and self.document.settings:
                doc_wrapping_spacing = self.document.settings.get('layout/wrapping_spacing', 0) or 0
                if doc_wrapping_spacing > 0:
                    wrapping_spacing = int(doc_wrapping_spacing)
            if wrapping_spacing <= 0:
                wrapping_spacing = int(QSettings("ONOTE", "Preferences").value("layout/default_wrapping_spacing", 80))
            wrapping_spacing = max(40, min(200, int(wrapping_spacing)))
            spacing = wrapping_spacing  # Use wrapping_spacing for single staff systems
        except Exception:
            spacing = 80
        try:
            top_margin = float(getattr(self.renderer, 'margins', {}).get('top', 0))
            bottom_margin = float(getattr(self.renderer, 'margins', {}).get('bottom', 120))
            page_h = int(getattr(self.renderer, 'page_height', 1123))
            avail_h = int(page_h - top_margin - bottom_margin)
        except Exception:
            avail_h = 900
        systems_per_page = max(1, avail_h // max(1, spacing))

        total_systems = (measure_count + mps - 1) // mps if measure_count > 0 else 1
        total_pages = max(1, (total_systems + systems_per_page - 1) // systems_per_page)
        return total_pages
    
    def sizeHint(self):
        """Return the recommended size for the widget based on view mode"""
        # Get view mode
        view_mode = self.renderer.get_view_mode() if hasattr(self.renderer, 'get_view_mode') else "page_down"
        
        MM_TO_PIXELS = 3.78  # 96 DPI
        base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
        base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
        
        if view_mode == "page_down" or self.is_setup_mode:
            # In page-down mode, widget should be tall enough for all pages stacked vertically
            page_margin = 20  # gap between stacked pages
            
            # Use cached total_pages if available, otherwise calculate
            if not hasattr(self, 'total_pages'):
                self.total_pages = max(1, self._calculate_total_pages())
            
            # Calculate total height: all pages + margins between them + some padding
            total_height = int(self.total_pages * (base_page_height + page_margin) * self.zoom_factor)
            total_width = int(base_page_width * self.zoom_factor)
            
            # Add some padding for scrolling
            total_height += 100
            
            return QSize(total_width, total_height)
        
        elif view_mode == "continuous":
            # In continuous mode, calculate width based on total content width
            # Get total measures to calculate content width
            if not hasattr(self, 'document') or not self.document:
                return QSize(2000, 1200)  # Default wide size
            
            try:
                # Try to get actual measure positions from temporal bridge for accurate width
                content_width = 2000  # Default minimum width
                if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                    try:
                        measures = self.temporal_bridge._get_current_measures()
                        if measures and len(measures) > 0:
                            # Find the rightmost measure end position
                            max_x = 0
                            for measure in measures:
                                if hasattr(measure, 'end_x') and measure.end_x:
                                    max_x = max(max_x, float(measure.end_x))
                            if max_x > 0:
                                content_width = max_x + 200  # Add padding
                    except Exception as e:
                        print(f"SIZEHINT_CONTINUOUS_BRIDGE_ERROR: {e}")
                
                # Fallback: calculate from measure count if bridge didn't work
                if content_width == 2000:
                    measures = getattr(self.document, 'measures', [])
                    measure_count = len([m for m in measures if hasattr(m, 'is_user_created') and m.is_user_created])
                    
                    if measure_count > 0:
                        # Get measures per system from settings
                        mps = int(QSettings("ONOTE", "Preferences").value("layout/measures_per_line", 4))
                        if mps <= 0:
                            mps = 4
                        
                        # Calculate content width: measures spread across systems
                        # Each measure is approximately 150px wide (adjust based on your actual measure width)
                        measure_width = 150  # Approximate measure width in pixels
                        systems_needed = (measure_count + mps - 1) // mps if measure_count > 0 else 1
                        content_width = systems_needed * mps * measure_width + 200
                
                # Apply zoom and ensure minimum width
                total_width = max(2000, int(content_width * self.zoom_factor))
                total_height = int(base_page_height * self.zoom_factor) + 200
                
                return QSize(total_width, total_height)
            except Exception as e:
                print(f"SIZEHINT_CONTINUOUS_ERROR: {e}")
                return QSize(2000, 1200)
        
        elif view_mode == "page_across":
            # In page-across mode, calculate size based on grid layout
            page_margin = 20  # Space between pages
            
            # Use cached total_pages if available, otherwise calculate
            if not hasattr(self, 'total_pages'):
                self.total_pages = max(1, self._calculate_total_pages())
            
            # Calculate how many pages fit horizontally (based on viewport, but we'll use a reasonable default)
            # The actual pages_per_row will be calculated during paint, but for sizeHint we estimate
            pages_per_row = 3  # Default estimate
            
            # Calculate rows needed
            rows_needed = (self.total_pages + pages_per_row - 1) // pages_per_row
            
            # Calculate total dimensions
            total_width = int(pages_per_row * (base_page_width + page_margin) * self.zoom_factor) + 100
            total_height = int(rows_needed * (base_page_height + page_margin) * self.zoom_factor) + 100
            
            return QSize(total_width, total_height)
        
        else:
            # For unknown modes, use default size
            return super().sizeHint() if hasattr(super(), 'sizeHint') else QSize(800, 1200)
    
    def schedule_size_update(self):
        """Schedule a widget size update (debounced to prevent flicker)"""
        # Stop any pending timer and start a new one (debounce)
        if hasattr(self, '_size_update_timer'):
            self._size_update_timer.stop()
            self._size_update_timer.start(100)  # 100ms debounce
    
    def _update_widget_size(self):
        """Update widget size when content changes (called outside of paint events)"""
        print(f"_UPDATE_WIDGET_SIZE: Called! document={self.document is not None}, renderer={self.renderer is not None}")
        try:
            old_total_pages = getattr(self, 'total_pages', 1)
            self.total_pages = max(1, self._calculate_total_pages())
            
            # Always update size to ensure scroll area recognizes it
            size_hint = self.sizeHint()
            print(f"WIDGET_SIZE_DEBUG: sizeHint() returned {size_hint}, isValid={size_hint.isValid() if size_hint else False}")
            
            if not size_hint or not size_hint.isValid():
                # Fallback: calculate size manually
                MM_TO_PIXELS = 3.78
                base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
                base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
                page_margin = 20
                total_height = int(self.total_pages * (base_page_height + page_margin) * self.zoom_factor) + 100
                total_width = int(base_page_width * self.zoom_factor)
                size_hint = QSize(total_width, total_height)
                print(f"WIDGET_SIZE_DEBUG: Using fallback size {size_hint.width()}x{size_hint.height()}")
            
            old_size = self.size()
            self.setMinimumSize(size_hint)
            self.resize(size_hint)
            self.updateGeometry()
            
            # Debug output
            print(f"WIDGET_SIZE: Setting widget size to {size_hint.width()}x{size_hint.height()} for {self.total_pages} pages (was {old_size.width()}x{old_size.height()})")
            
            # Check if scroll area parent exists and update scrollbar ranges
            parent = self.parent()
            if parent and hasattr(parent, 'verticalScrollBar'):
                from PyQt6.QtWidgets import QScrollArea
                if isinstance(parent, QScrollArea):
                    vbar = parent.verticalScrollBar()
                    hbar = parent.horizontalScrollBar()
                    if vbar:
                        viewport_height = parent.viewport().height() if parent.viewport() else 600
                        # Set scrollbar range to match widget size (widget height - viewport height = max scroll)
                        max_scroll = max(0, size_hint.height() - viewport_height)
                        vbar.setMaximum(max_scroll)
                        vbar.setPageStep(viewport_height)
                        vbar.setSingleStep(20)  # Smooth scrolling step
                        vbar.setEnabled(max_scroll > 0)  # Enable scrollbar only if scrolling is possible
                        print(f"SCROLL_DEBUG: Widget height={size_hint.height()}, viewport height={viewport_height}, scrollbar max={vbar.maximum()}, pageStep={vbar.pageStep()}, current={vbar.value()}, enabled={vbar.isEnabled()}")
                    if hbar:
                        viewport_width = parent.viewport().width() if parent.viewport() else 800
                        max_h_scroll = max(0, size_hint.width() - viewport_width)
                        hbar.setMaximum(max_h_scroll)
                        hbar.setPageStep(viewport_width)
                        hbar.setSingleStep(20)
                        hbar.setEnabled(max_h_scroll > 0)
                    # Force scroll area to update
                    parent.updateGeometry()
            else:
                print(f"SCROLL_DEBUG: No scroll area parent found (parent={parent}, type={type(parent) if parent else None})")
            
            # Trigger a repaint after resize
            QTimer.singleShot(0, self.update)
        except Exception as e:
            print(f"WIDGET_SIZE_ERROR: Exception in _update_widget_size: {e}")
            import traceback
            traceback.print_exc()
    
    def updateGeometry(self):
        """Update widget geometry when total pages changes"""
        super().updateGeometry()
        # Notify parent scroll area that size changed (important for scrolling)
        parent = self.parent()
        if parent and hasattr(parent, 'updateGeometry'):
            parent.updateGeometry()
    
    def next_page(self):
        """Navigate to the next page"""
        self.update_total_pages()
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            # Sync renderer current_page
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'current_page'):
                self.renderer.current_page = self.current_page
            print(f"PAGE_NAV: Moved to next page: {self.current_page + 1}/{self.total_pages}")
            self.update()
            return True
        return False
    
    def previous_page(self):
        """Navigate to the previous page"""
        self.update_total_pages()
        if self.current_page > 0:
            self.current_page -= 1
            # Sync renderer current_page
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'current_page'):
                self.renderer.current_page = self.current_page
            print(f"PAGE_NAV: Moved to previous page: {self.current_page + 1}/{self.total_pages}")
            self.update()
            return True
        return False
    
    def update_total_pages(self):
        """Recalculate total pages and adjust current_page if needed"""
        old_total = self.total_pages
        self.total_pages = max(1, self._calculate_total_pages())
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
            # Sync renderer current_page
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'current_page'):
                self.renderer.current_page = self.current_page
        if old_total != self.total_pages:
            print(f"PAGE_NAV: Total pages updated: {old_total} -> {self.total_pages}")
            # Schedule widget size update (debounced to prevent flicker)
            self.schedule_size_update()
    
    def draw_selected_barlines(self, painter):
        """Draw orange highlighting for selected barlines"""
        if not hasattr(self.document, 'measures') or not self.document.measures:
            return
        
        # Set up orange highlight color
        orange_color = QColor(255, 165, 0, 150)  # Orange with transparency
        painter.setBrush(orange_color)
        painter.setPen(QPen(QColor(255, 140, 0), 3))  # Darker orange border
        
        # Handle both list and dictionary formats for measures
        measures = self.document.measures
        if isinstance(measures, dict):
            measures = measures.values()
        
        for measure in measures:
            if hasattr(measure, 'selected') and measure.selected and hasattr(measure, 'end_x'):
                # Calculate barline position and dimensions
                barline_x = measure.end_x
                
                # Calculate exact highlight dimensions based on actual staff positions
                highlight_top = None
                highlight_bottom = None
                
                # Get all staves to find actual top and bottom positions
                all_staves = []
                
                if hasattr(self.document, 'layout') and self.document.layout:
                    # Add staves from sections
                    if hasattr(self.document.layout, 'sections'):
                        for section in self.document.layout.sections:
                            if hasattr(section, 'staves'):
                                all_staves.extend(section.staves)
                    
                    # Add ungrouped staves
                    if hasattr(self.document.layout, 'ungrouped_staves'):
                        all_staves.extend(self.document.layout.ungrouped_staves)
                
                if all_staves:
                    # Find actual top and bottom staff positions
                    staff_positions = []
                    for staff in all_staves:
                        if hasattr(staff, 'y_position'):
                            staff_positions.append(staff.y_position)
                            # Also include the bottom of this staff
                            staff_height = getattr(staff, 'height', 32)  # Default staff height
                            staff_positions.append(staff.y_position + staff_height)
                    
                    if staff_positions:
                        highlight_top = min(staff_positions) - 10  # Extend above top staff
                        highlight_bottom = max(staff_positions) + 10  # Extend below bottom staff
                        print(f"ORANGE_SELECTION: Using actual staff positions - top: {highlight_top}, bottom: {highlight_bottom}")
                
                # Fallback calculation if no layout information found
                if highlight_top is None or highlight_bottom is None:
                    # Use the entire visible score area
                    # Start from the top margin area
                    highlight_top = 30  # Just above the first staff
                    
                    # Calculate bottom based on total staves in the score
                    total_staves = self.get_total_staff_count()
                    
                    # Calculate positioning similar to how the renderer does it
                    staff_spacing = 72  # Space between staves (staff height + gap)
                    first_staff_y = 40  # Y position of first staff
                    
                    if total_staves == 1:
                        # Single staff
                        highlight_bottom = first_staff_y + 40  # Staff height + margin
                    elif total_staves == 2:
                        # Two staves (like treble + bass)
                        # Bottom staff is positioned for grand staff
                        highlight_bottom = 216 + 10  # Bottom staff bottom + margin
                    else:
                        # Multiple staves
                        last_staff_y = first_staff_y + ((total_staves - 1) * staff_spacing)
                        highlight_bottom = last_staff_y + 40  # Last staff + height + margin
                    
                    print(f"ORANGE_SELECTION: Using fallback calculation - total staves: {total_staves}, top: {highlight_top}, bottom: {highlight_bottom}")
                
                # Ensure we have valid dimensions
                if highlight_bottom <= highlight_top:
                    highlight_bottom = highlight_top + 50  # Minimum height
                
                # Draw system-wide highlight rectangle around the barline
                highlight_width = 8
                highlight_rect = QRect(
                    int(barline_x - highlight_width // 2),
                    int(highlight_top),
                    highlight_width,
                    int(highlight_bottom - highlight_top)
                )
                
                print(f"ORANGE_SELECTION: Drawing highlight rect at barline_x={barline_x}, rect={highlight_rect}")
                painter.fillRect(highlight_rect, orange_color)
                painter.drawRect(highlight_rect)
    
    def get_total_staff_count(self):
        """Get the total number of staves in the current score"""
        total_staves = 0
        
        if hasattr(self.document, 'layout') and self.document.layout:
            # Count staves from sections
            if hasattr(self.document.layout, 'sections'):
                for section in self.document.layout.sections:
                    if hasattr(section, 'staves'):
                        total_staves += len(section.staves)
            
            # Count ungrouped staves
            if hasattr(self.document.layout, 'ungrouped_staves'):
                total_staves += len(self.document.layout.ungrouped_staves)
        
        # Return at least 1 staff as fallback
        return max(1, total_staves)

    def show_clef_dialog(self):
        """Show the clef selection dialog"""
        if not self.selected_staff:
            return
            
        dialog = ClefDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.selected_staff.clef = settings['clef'].lower().split()[0]
            self.update()
            
    def show_key_dialog(self):
        """Show the key signature dialog"""
        if not self.selected_staff:
            return
            
        dialog = KeyDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.selected_staff.key = settings['key']
            self.update()
            
    def show_time_signature_dialog(self):
        """Show the time signature dialog"""
        if not self.selected_staff:
            return
            
        dialog = TimeSignatureDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.selected_staff.time_signature = f"{settings['numerator']}/{settings['denominator']}"
            self.update()
            
    def show_staff_dialog(self):
        """Show the staff settings dialog"""
        if not self.selected_staff:
            return
            
        self.staff_dialog_open = True
        dialog = StaffDialog(self)
        dialog.finished.connect(lambda: self.on_staff_dialog_closed())
        
        if dialog.exec():
            settings = dialog.get_settings()
            # Update staff settings
            self.selected_staff.staff_type = settings['staff_type']
            self.selected_staff.name = settings['name']
            self.selected_staff.abbr = settings['abbr']
            self.update()
            
    def on_staff_dialog_closed(self):
        """Handle staff dialog being closed"""
        self.staff_dialog_open = False
        
    def set_staff_dialog_open(self, is_open):
        """Set whether the staff dialog is open"""
        self.staff_dialog_open = is_open
        
    def mousePressEvent(self, event):
        """Handle mouse press for gesture tracking, page dragging, and barline creation"""
        print(f"MOUSE_PRESS: Button {event.button()} at position {event.position()}")
        
        # Only set focus on left click (for barline operations), not on other interactions
        # This allows scroll area to handle scrolling without interference
        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
        
        # Track gesture start
        if event.button() == Qt.MouseButton.LeftButton:
            # FIRST: Check for barline operations before setting up page dragging
            click_pos = event.position().toPoint()
            
            # Check for shift key modifier for multi-selection
            shift_pressed = event.modifiers() & Qt.KeyboardModifier.ShiftModifier
            
            # Check for Ctrl/Cmd key modifier for drag selection
            ctrl_pressed = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            
            # DRAG SELECTION: Start drag selection if Ctrl/Cmd is held
            if ctrl_pressed and not shift_pressed:
                self.start_drag_selection(event.position())
                return  # Skip barline operations for drag selection
            
            # Track if a barline operation occurred (to prevent page dragging)
            barline_operation_occurred = False
            
            # Adjust x for continuous horizontal offset when hit-testing
            try:
                view_mode = self.renderer.get_view_mode() if hasattr(self, 'renderer') else 'page'
                adj_x = click_pos.x()
                if view_mode == 'continuous' and hasattr(self, 'continuous_offset_x'):
                    adj_x = click_pos.x() + int(self.continuous_offset_x)
            except Exception:
                adj_x = click_pos.x()

            # Check if we're in a valid area for barline operations
            if self.is_position_valid_for_barline(adj_x, click_pos.y()):
                # Try to find existing barline first
                existing_barline = self.find_barline_at_position(adj_x, click_pos.y())
                
                if existing_barline:
                    barline_operation_occurred = True  # Mark that we handled a barline
                    
                    # Select the existing barline
                    if shift_pressed:
                        # Shift-click: toggle selection of this barline (multi-select)
                        if hasattr(existing_barline, 'selected') and existing_barline.selected:
                            existing_barline.selected = False
                            print(f"SHIFT_CLICK: Deselected barline at measure {getattr(existing_barline, 'measure_number', 'unknown')}")
                            
                            # Check if any barlines are still selected
                            selected_barlines = self.get_selected_barlines()
                            if not selected_barlines:
                                # No barlines selected, release keyboard grab
                                try:
                                    self.releaseKeyboard()
                                    print("SHIFT_CLICK: Released keyboard grab - no barlines selected")
                                except:
                                    pass
                        else:
                            existing_barline.selected = True
                            # Grab keyboard for delete key handling
                            self.grabKeyboard()
                            print(f"SHIFT_CLICK: Added barline at measure {getattr(existing_barline, 'measure_number', 'unknown')} to selection, keyboard grabbed")
                        
                        # Only emit signal for actual MeasureObjects, not graphical dashed barlines
                        from .measure_object import MeasureObject
                        if isinstance(existing_barline, MeasureObject):
                            # Emit selection signal for form widget
                            self.barline_selected.emit(existing_barline)
                        
                        # Update display to show selection changes
                        self.update()
                        self._rebuild_selected_barline_positions()
                    else:
                        # Normal click: select only this barline (single select)
                        self.select_barline(existing_barline)
                else:
                    # No existing barline found
                    if not shift_pressed:
                        # Normal click: deselect all barlines first
                        self.deselect_all_barlines()
                    
                    # CRITICAL FIX: Only create barlines when form widget is active
                    # This prevents automatic barline creation on regular clicks that causes undo reversion
                    if not shift_pressed and self.is_form_widget_active():
                        new_barline = self.create_barline_at_position(click_pos.x(), click_pos.y())
                        if new_barline:
                            # Only emit signal for actual MeasureObjects, not graphical dashed barlines
                            from .measure_object import MeasureObject
                            if isinstance(new_barline, MeasureObject):
                                # Emit signal for form widget (if available)
                                self.barline_created.emit(new_barline)
                            barline_operation_occurred = True  # Mark that we created a barline
                            # Update display
                            self.update()
                            print(f"BARLINE_CREATE: Created barline at x={click_pos.x()}")
                        else:
                            print(f"BARLINE_CREATE: Failed to create barline at x={click_pos.x()}")
                    elif not shift_pressed:
                        print(f"CLICK: Form widget not active, not creating barline at x={click_pos.x()}")
            else:
                # Click outside valid area
                if not shift_pressed:
                    # Normal click outside: deselect all barlines
                    self.deselect_all_barlines()
                # Shift-click outside: do nothing (preserve current selection)
            
            # AFTER barline operations: Page dragging disabled by default to allow normal scrolling
            # This allows two-finger trackpad scrolling to work without interference
            # Users can scroll normally with trackpad/arrow keys
            if not barline_operation_occurred:
                self.gesture_start_pos = None
                self.is_dragging_page = False
            else:
                print("BARLINE_OPERATION: Barline operation occurred, skipping page dragging setup")
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for gesture tracking, page dragging, and drag selection"""
        if event.buttons() & Qt.MouseButton.LeftButton:
            # Handle drag selection
            if self.is_drag_selecting:
                self.update_drag_selection(event.position())
                return
            
            # Handle page dragging (existing logic)
            if self.is_dragging_page:
                # Calculate drag distance
                drag_distance = event.position() - self.drag_start_pos
                
                # Update page offset
                self.page_offset_x = self.drag_start_offset.x() + drag_distance.x()
                self.page_offset_y = self.drag_start_offset.y() + drag_distance.y()
                
                # Force repaint
                self.update()
                return
            
            # Handle gesture tracking (existing logic)
            if self.gesture_start_pos:
                current_pos = event.position()
                distance = (current_pos - self.gesture_start_pos).manhattanLength()
                
                if distance > 10:  # Threshold for gesture start
                    self.is_gesturing = True
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for gesture tracking, page dragging, and drag selection"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Handle drag selection end
            if self.is_drag_selecting:
                self.end_drag_selection(event.position())
                return
            
            # Handle page dragging end
            if self.is_dragging_page:
                self.is_dragging_page = False
                self.drag_start_pos = None
                self.drag_start_offset = None
                return
            
            # Handle gesture end (existing logic)
            if self.is_gesturing:
                self.is_gesturing = False
                self.gesture_start_pos = None
        
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events - no longer used for barline removal"""
        # Double-click functionality removed as per specification
        # Barlines are now only removed via Delete key
        super().mouseDoubleClickEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events - arrow keys scroll, Page Up/Down navigate pages"""
        print(f"KEYPRESS: Received key event: {event.key()}, focus: {self.hasFocus()}, keyboard grabbed: {getattr(self, '_keyboard_grabbed', False)}")
        
        # Get current view mode
        try:
            view_mode = self.renderer.get_view_mode() if hasattr(self, 'renderer') and hasattr(self.renderer, 'get_view_mode') else 'page_down'
        except Exception:
            view_mode = 'page_down'
        
        # Page navigation with Page Up/Page Down keys (word processor style)
        if view_mode in ('page_down', 'page_across'):
            if event.key() == Qt.Key.Key_PageUp:
                # Previous page
                if self.previous_page():
                    event.accept()
                    return
            elif event.key() == Qt.Key.Key_PageDown:
                # Next page
                if self.next_page():
                    event.accept()
                    return
        
        # Arrow keys always scroll (word processor style) - never change pages
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
            try:
                from PyQt6.QtWidgets import QAbstractScrollArea
                # Find an ancestor scroll area if present
                parent = self.parent()
                scroll_area = None
                while parent is not None and scroll_area is None:
                    if hasattr(parent, 'verticalScrollBar') and hasattr(parent, 'horizontalScrollBar'):
                        scroll_area = parent
                        break
                    parent = parent.parent()
                if scroll_area is not None:
                    vbar = scroll_area.verticalScrollBar()
                    hbar = scroll_area.horizontalScrollBar()
                    # Smooth scrolling step (word processor style)
                    step = int(20 * self.zoom_factor)  # Smaller step for smoother scrolling
                    if event.key() == Qt.Key.Key_Up and vbar is not None:
                        old_val = vbar.value()
                        new_val = max(0, old_val - step)
                        vbar.setValue(new_val)
                        print(f"ARROW_UP: Scrollbar value {old_val} -> {new_val} (max={vbar.maximum()})")
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Down and vbar is not None:
                        old_val = vbar.value()
                        new_val = min(vbar.maximum(), old_val + step)
                        vbar.setValue(new_val)
                        print(f"ARROW_DOWN: Scrollbar value {old_val} -> {new_val} (max={vbar.maximum()})")
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Left and hbar is not None:
                        old_val = hbar.value()
                        new_val = max(0, old_val - step)
                        hbar.setValue(new_val)
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Right and hbar is not None:
                        old_val = hbar.value()
                        new_val = min(hbar.maximum(), old_val + step)
                        hbar.setValue(new_val)
                        event.accept()
                        return
                    # If we get here, arrow key wasn't handled (scrollbar might be None)
                    print(f"ARROW_KEY: Scroll area found but arrow key not handled (key={event.key()}, vbar={vbar}, hbar={hbar})")
                else:
                    # No scroll area found - ensure widget can receive focus for arrow keys
                    print(f"ARROW_KEY: No scroll area found")
                    if not self.hasFocus():
                        self.setFocus()
            except Exception:
                pass

        # Test score creation shortcut (Ctrl+Shift+T)
        if (event.key() == Qt.Key.Key_T and 
            event.modifiers() & Qt.KeyboardModifier.ControlModifier and
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            print("=== KEYPRESS: Ctrl+Shift+T detected, creating test score ===")
            self.create_test_score()
            event.accept()
            return
        
        # Handle both Delete and Backspace keys (Mac "delete" key is actually Backspace in Qt)
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Get all selected barlines
            selected_barlines = self.get_selected_barlines()
            print(f"KEYPRESS_DELETE: Found {len(selected_barlines)} selected barlines")
            
            if selected_barlines:
                # Save state for undo BEFORE deletion (one-by-one redo behavior)
                # Use document.save_state when available for consistent undo/redo
                if hasattr(self, 'document') and hasattr(self.document, 'save_state'):
                    if len(selected_barlines) == 1:
                        self.document.save_state(
                            f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}"
                        )
                    else:
                        self.document.save_state(f"Delete {len(selected_barlines)} barlines")
                else:
                    form_widget = self.get_form_widget()
                    if form_widget and hasattr(form_widget, 'save_state'):
                        if len(selected_barlines) == 1:
                            form_widget.save_state(
                                f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}"
                            )
                        else:
                            form_widget.save_state(f"Delete {len(selected_barlines)} barlines")
                
                # Remove each barline immediately
                successfully_deleted = 0
                for barline in selected_barlines:
                    # If this is a graphical dashed barline overlay, remove only the overlay
                    try:
                        if getattr(barline, 'is_graphical_dashed', False):
                            if hasattr(self.document, 'graphical_dashed_barlines'):
                                try:
                                    self.document.graphical_dashed_barlines.remove(barline)
                                except ValueError:
                                    pass
                            if hasattr(barline, 'selected'):
                                barline.selected = False
                            self._rebuild_selected_barline_positions()
                            print("BARLINE_DEMOTE: Removed graphical dashed overlay; underlying single remains")
                            continue
                    except Exception:
                        pass
                    # Ensure a granular undo boundary per barline
                    try:
                        if hasattr(self, 'document') and hasattr(self.document, 'save_state'):
                            self.document.save_state(
                                f"Delete barline at measure {getattr(barline, 'measure_number', 'unknown')}"
                            )
                    except Exception:
                        pass
                    # If this is an overlay type (final/double/repeat variants), only demote to 'single'
                    barline_type = getattr(barline, 'barline_type', None)
                    overlay_type = getattr(barline, 'overlay_type', None)
                    measure_number = getattr(barline, 'measure_number', None)
                    overlay_types = {'final', 'double', 'repeat_start', 'repeat_end', 'repeat_both', 'dashed'}
                    # Treat the rightmost measure as a visual final overlay even if stored as 'single'
                    is_rightmost = False
                    try:
                        if hasattr(self.document, 'measures') and isinstance(self.document.measures, dict) and self.document.measures:
                            rightmost_num = max(k for k in self.document.measures.keys() if isinstance(k, int))
                            is_rightmost = (int(measure_number) == int(rightmost_num))
                    except Exception:
                        is_rightmost = False
                    # CRITICAL FIX: Check both barline_type and overlay_type for overlay detection
                    is_overlay = (barline_type in overlay_types) or (overlay_type in overlay_types) or is_rightmost
                    if is_overlay and measure_number is not None:
                        try:
                            # CRITICAL FIX: Remove overlay_type to reveal the single barline underneath
                            if hasattr(barline, 'barline_type'):
                                barline.barline_type = 'single'
                            if hasattr(barline, 'overlay_type'):
                                barline.overlay_type = None  # Remove overlay to reveal single barline
                            if hasattr(barline, 'selected'):
                                barline.selected = False
                            if self.temporal_bridge:
                                if hasattr(self.temporal_bridge, 'update_barline_type'):
                                    self.temporal_bridge.update_barline_type(measure_number, 'single')
                                elif hasattr(self.temporal_bridge, 'modify_barline_type'):
                                    self.temporal_bridge.modify_barline_type(barline, 'single')
                        except Exception as e:
                            print(f"BARLINE_DEMOTE: Failed to demote measure {measure_number}: {e}")
                        self._rebuild_selected_barline_positions()
                        # Force immediate repaint and selection resync
                        try:
                            if hasattr(self, 'renderer') and hasattr(self.renderer, 'set_selected_barline_positions'):
                                self.renderer.set_selected_barline_positions(self._selected_barline_positions)
                        except Exception:
                            pass
                        self.update()
                        overlay_info = overlay_type if overlay_type else (barline_type if barline_type in overlay_types else ('rightmost' if is_rightmost else 'unknown'))
                        print(f"BARLINE_DEMOTE: Demoted {overlay_info} at measure {measure_number} to single (measure intact, overlay removed)")
                        continue
                    # Check if barline can be removed
                    can_remove = True
                    if hasattr(self, 'measure_manager') and self.measure_manager:
                        can_remove = self.measure_manager.can_remove_barline(barline)
                        if not can_remove:
                            print(f"KEYPRESS_DELETE: Cannot remove barline at measure {getattr(barline, 'measure_number', 'unknown')} - it's the initial end bar")
                            continue
                    
                    # Deselect the barline before removal
                    if hasattr(barline, 'selected'):
                        barline.selected = False
                    
                    # Remove the barline
                    if self._remove_barline_direct(barline):
                        successfully_deleted += 1
                        # Emit removal signal
                        from .measure_object import MeasureObject
                        if isinstance(barline, MeasureObject):
                            self.barline_removed.emit(barline)
                        print(f"BARLINE_DELETE: Deleted barline at measure {getattr(barline, 'measure_number', 'unknown')}")
                    else:
                        print(f"BARLINE_DELETE: Failed to delete barline at measure {getattr(barline, 'measure_number', 'unknown')}")
                
                # CRITICAL FIX: Re-justify measures after deletion
                if successfully_deleted > 0:
                    try:
                        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                            if hasattr(self.temporal_bridge, '_ensure_all_measures_justified'):
                                self.temporal_bridge._ensure_all_measures_justified()
                                print(f"BARLINE_DELETE: Re-justified measures after deleting {successfully_deleted} barline(s)")
                            elif hasattr(self.temporal_bridge, '_recalculate_uniform_spacing'):
                                self.temporal_bridge._recalculate_uniform_spacing()
                                print(f"BARLINE_DELETE: Recalculated spacing after deleting {successfully_deleted} barline(s)")
                    except Exception as e:
                        print(f"BARLINE_DELETE: Error re-justifying after deletion: {e}")
                
                # Release keyboard grab since barlines are now deleted
                if hasattr(self, '_keyboard_grabbed') and self._keyboard_grabbed:
                    try:
                        self.releaseKeyboard()
                        self._keyboard_grabbed = False
                        print("KEYPRESS_DELETE: Released keyboard grab after deletion")
                    except Exception as e:
                        print(f"KEYPRESS_DELETE: Failed to release keyboard: {e}")
                        self._keyboard_grabbed = False
                
                # Force update to show changes
                if successfully_deleted > 0:
                    self.update()
                
                # Update display and force renderer to rebuild selection cache
                try:
                    if hasattr(self, 'renderer') and hasattr(self.renderer, 'set_selected_barline_positions'):
                        self.renderer.set_selected_barline_positions([])
                    if hasattr(self.renderer, 'set_selected_barline_measures'):
                        self.renderer.set_selected_barline_measures([])
                except Exception:
                    pass
                self.update()
                
                print(f"BARLINE_DELETE: Successfully deleted {successfully_deleted} barline(s) out of {len(selected_barlines)} selected")
                # No extra post-delete snapshot; we already wrote a per-barline snapshot above
                
                # Accept the event to prevent further propagation
                event.accept()
                return
            else:
                print("BARLINE_DELETE: No barlines selected for deletion")
        
        # Call parent implementation for other keys
        super().keyPressEvent(event)
    
    def _remove_barline_direct(self, measure_obj):
        """Remove a barline directly with proper temporal bridge integration"""
        if not measure_obj or not hasattr(measure_obj, 'measure_number'):
            print("STAFFVIEW: Cannot remove barline - invalid measure object")
            return False
            
        measure_number = measure_obj.measure_number
        print(f"STAFFVIEW: Removing barline at measure {measure_number}")
        
        # Use temporal bridge for proper removal and renumbering
        if self.temporal_bridge:
            success = self.temporal_bridge.remove_barline(measure_number)
            if success:
                print(f"STAFFVIEW: Successfully removed barline at measure {measure_number}")
                
                # Clear selection after successful removal - use proper method
                self.deselect_all_barlines(skip_form_widget_notification=True)
                self._selected_barline_positions = []
                self._rebuild_selected_barline_positions()
                
                # Trigger re-render
                self.update()
                return True
            else:
                print(f"STAFFVIEW: Failed to remove barline at measure {measure_number}")
                return False
        else:
            print("STAFFVIEW: No temporal bridge available for barline removal")
            return False
    
    def select_barline(self, barline):
        """
        Select a barline and highlight it in orange.
        
        ONOTE SPECIFICATION: Barline selection is per staff system (single/grand/section).
        A measure object represents a barline that spans across all staves in its system.
        Selecting a barline selects it for the entire system - the barline at the same
        x position across all staves in that system will be highlighted.
        """
        if not barline:
            return
                
        # Deselect all other barlines first
        self.deselect_all_barlines()
        
        # Select the clicked barline (this is system-wide - spans all staves in the system)
        barline.selected = True
        
        # CRITICAL: Grab keyboard focus to ensure delete key works
        # This ensures delete key works even when cursor moves away from barlines
        try:
            self.grabKeyboard()
            self._keyboard_grabbed = True
            print("BARLINE_SELECT: Grabbed keyboard focus")
        except Exception as e:
            print(f"BARLINE_SELECT: Failed to grab keyboard: {e}")
            self._keyboard_grabbed = False
        
        # Set focus to this widget as primary handler
        self.setFocus()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Only emit signal for actual MeasureObjects, not graphical dashed barlines
        from .measure_object import MeasureObject
        if isinstance(barline, MeasureObject):
            # Emit selection signal for form widget
            self.barline_selected.emit(barline)
        
        # Update display to show orange highlighting
        self.update()
        self._rebuild_selected_barline_positions()
        
        print(f"BARLINE_SELECT: Selected barline at measure {getattr(barline, 'measure_number', 'unknown')}, global filter installed: {self._keyboard_grabbed}")

    def deselect_all_barlines(self, skip_form_widget_notification=False):
        """Deselect all barlines"""
        # Deselect regular measures
        if hasattr(self.document, 'measures') and self.document.measures:
            measures = self.document.measures
            if isinstance(measures, dict):
                measures = measures.values()
            
            for measure in measures:
                if hasattr(measure, 'selected'):
                    measure.selected = False
        
        # Deselect graphical dashed barlines
        if hasattr(self.document, 'graphical_dashed_barlines'):
            for dashed_barline in self.document.graphical_dashed_barlines:
                if hasattr(dashed_barline, 'selected'):
                    dashed_barline.selected = False
        
        # Release keyboard grab since no barlines are selected
        if self._keyboard_grabbed:
            try:
                self.releaseKeyboard()
                self._keyboard_grabbed = False
                print("BARLINE_DESELECT: Released keyboard grab")
            except Exception as e:
                print(f"BARLINE_DESELECT: Failed to release keyboard: {e}")
                self._keyboard_grabbed = False
        
        # Notify form widget to clear its selected barline reference
        # Use skip_form_widget_notification to prevent infinite recursion
        if not skip_form_widget_notification:
            form_widget = self.get_form_widget()
            if form_widget and hasattr(form_widget, 'on_deselect_all_barlines'):
                form_widget.on_deselect_all_barlines()
        
        # Update display
        self.update()
        self._rebuild_selected_barline_positions()
    
    def get_selected_barline(self):
        """Get the currently selected barline (returns first selected if multiple)"""
        # Check regular measures first
        if hasattr(self.document, 'measures') and self.document.measures:
            measures = self.document.measures
            if isinstance(measures, dict):
                measures = measures.values()
            
            for measure in measures:
                if hasattr(measure, 'selected') and measure.selected:
                    return measure
        
        # Check graphical dashed barlines
        if hasattr(self.document, 'graphical_dashed_barlines'):
            for dashed_barline in self.document.graphical_dashed_barlines:
                if hasattr(dashed_barline, 'selected') and dashed_barline.selected:
                    return dashed_barline
        
        return None

    def get_selected_barlines(self):
        """Get all currently selected barlines"""
        selected_barlines = []
        
        # Get selected regular measures
        if hasattr(self.document, 'measures') and self.document.measures:
            measures = self.document.measures
            if isinstance(measures, dict):
                measures = measures.values()
            
            for measure in measures:
                if hasattr(measure, 'selected') and measure.selected:
                    selected_barlines.append(measure)
        
        # Get selected graphical dashed barlines
        if hasattr(self.document, 'graphical_dashed_barlines'):
            for dashed_barline in self.document.graphical_dashed_barlines:
                if hasattr(dashed_barline, 'selected') and dashed_barline.selected:
                    selected_barlines.append(dashed_barline)
        
        return selected_barlines
    
    def start_drag_selection(self, start_pos):
        """Start drag selection at the given position"""
        self.is_drag_selecting = True
        self.drag_select_start = start_pos
        self.drag_select_end = start_pos
        self.drag_select_rect = None
        print(f"DRAG_SELECT: Started drag selection at {start_pos}")
    
    def update_drag_selection(self, current_pos):
        """Update drag selection rectangle"""
        if self.is_drag_selecting:
            self.drag_select_end = current_pos
            # Create selection rectangle
            from PyQt6.QtCore import QRectF
            self.drag_select_rect = QRectF(self.drag_select_start, current_pos).normalized()
            # Force repaint to show selection rectangle
            self.update()
    
    def end_drag_selection(self, end_pos):
        """End drag selection and select elements in rectangle"""
        if not self.is_drag_selecting:
            return
        
        self.drag_select_end = end_pos
        from PyQt6.QtCore import QRectF
        self.drag_select_rect = QRectF(self.drag_select_start, end_pos).normalized()
        
        # Find and select elements in the rectangle
        selected_elements = self.find_elements_in_rect(self.drag_select_rect)
        
        # Filter out protected elements
        draggable_elements = self.filter_draggable_elements(selected_elements)
        
        # Select the draggable elements
        for element in draggable_elements:
            if hasattr(element, 'selected'):
                element.selected = True
        
        print(f"DRAG_SELECT: Selected {len(draggable_elements)} draggable elements")
        self._rebuild_selected_barline_positions()
        
        # Keep drag rectangle visible; clear only when explicitly deselected / action done
        self.is_drag_selecting = False
        self.drag_select_rect = None
        self.update()
    
    def find_elements_in_rect(self, rect):
        """Find all score elements within the selection rectangle"""
        elements = []
        
        # Find barlines in rectangle
        if hasattr(self.document, 'measures') and self.document.measures:
            measures = self.document.measures
            if isinstance(measures, dict):
                measures = list(measures.values())
            
            for measure in measures:
                if hasattr(measure, 'x_position') and hasattr(measure, 'measure_number'):
                    # Check if barline position is within rectangle
                    barline_x = measure.x_position
                    barline_y = TOP_MARGIN + STAFF_HEIGHT // 2  # Approximate barline position
                    
                    if rect.contains(barline_x, barline_y):
                        elements.append(measure)
        
        # Find graphical dashed barlines in rectangle
        if hasattr(self.document, 'graphical_dashed_barlines'):
            for dashed_barline in self.document.graphical_dashed_barlines:
                if hasattr(dashed_barline, 'x_position') and hasattr(dashed_barline, 'y_position'):
                    if rect.contains(dashed_barline.x_position, dashed_barline.y_position):
                        elements.append(dashed_barline)
        
        return elements
    
    def filter_draggable_elements(self, elements):
        """Filter elements to exclude protected ones from drag selection"""
        draggable = []
        for element in elements:
            if hasattr(element, 'barline_type'):
                barline_type = getattr(element, 'barline_type', 'unknown')
                measure_number = getattr(element, 'measure_number', 0)
                
                # Skip single barlines (protected)
                if barline_type == 'single':
                    continue
                
                # Skip ultimate final barline (protected)
                if barline_type == 'final':
                    if hasattr(self.document, 'measures') and self.document.measures:
                        max_measure = max(self.document.measures.keys()) if isinstance(self.document.measures, dict) else len(self.document.measures) - 1
                        if measure_number == max_measure:
                            continue
                
                draggable.append(element)
            elif hasattr(element, 'x_position'):  # Dashed barlines
                draggable.append(element)
        
        return draggable

    def is_position_valid_for_barline(self, x, y):
        """Check if the click position is valid for barline placement/selection"""
        # More permissive left bound: use temporal bridge LEFTMOST_NOTE_X if available
        left_bound = None
        try:
            if hasattr(self, 'temporal_bridge') and self.temporal_bridge and hasattr(self.temporal_bridge, 'LEFTMOST_NOTE_X'):
                left_bound = float(self.temporal_bridge.LEFTMOST_NOTE_X)
        except Exception:
            left_bound = None
        if left_bound is None:
            left_bound = max(0, LEFT_MARGIN + INITIAL_BARLINE_OFFSET)
        if x < left_bound:
            return False
                
        # SIMPLIFIED: Check if click is within widget bounds (more permissive)
        print(f"BARLINE_POSITION: Checking click at ({x}, {y}) within widget bounds")
        
        # Check if click is within widget bounds
        if (0 <= x <= self.width() and 0 <= y <= self.height()):
            print(f"BARLINE_POSITION: Click at ({x}, {y}) is within widget bounds - VALID")
            return True
        else:
            print(f"BARLINE_POSITION: Click at ({x}, {y}) is outside widget bounds - INVALID")
            return False
        
        # Fallback to original logic if system boundaries can't be determined
        all_staves = []
        if hasattr(self.document, 'layout') and self.document.layout:
            # Add staves from sections
            if hasattr(self.document.layout, 'sections'):
                for section in self.document.layout.sections:
                    if hasattr(section, 'staves'):
                        all_staves.extend(section.staves)
            
            # Add ungrouped staves
            if hasattr(self.document.layout, 'ungrouped_staves'):
                all_staves.extend(self.document.layout.ungrouped_staves)
        
        if all_staves:
            # Find actual top and bottom system boundaries
            staff_positions = [staff.y_position for staff in all_staves if hasattr(staff, 'y_position')]
            if staff_positions:
                system_top = min(staff_positions) - 50  # More generous tolerance above top staff
                # Calculate bottom including staff height (5 lines with 4 spaces between them)
                staff_height = (4 * 8)  # 4 spaces * 8px line spacing = 32px staff height
                system_bottom = max(staff_positions) + staff_height + 50  # More generous tolerance below bottom staff
                
                # Check if y is within the system boundaries
                if y < system_top or y > system_bottom:
                    print(f"BARLINE_POSITION: y={y} outside system bounds (top={system_top}, bottom={system_bottom})")
                    return False
                
                print(f"BARLINE_POSITION: y={y} within system bounds (top={system_top}, bottom={system_bottom}) - VALID")
                return True

        # Final fallback: be permissive so clicks anywhere on rendered staff areas work
        # Accept any y within the viewport as valid when layout info is missing
        if 0 <= y <= self.height():
            print(f"BARLINE_POSITION: No detailed layout; accepting y={y} within widget height {self.height()} - VALID")
            return True
        return False
    
    def _get_system_boundaries(self):
        """Get the boundaries of all rendered score systems"""
        print("SYSTEM_BOUNDARIES: Calculating system boundaries...")
        try:
            # Get layout settings
            from PyQt6.QtCore import QSettings
            settings = QSettings("ONOTE", "Preferences")
            measures_per_system = int(settings.value("layout/default_measures_per_system", 4))
            system_spacing = int(settings.value("layout/default_system_spacing", 80))
            measures_per_system = max(1, min(32, measures_per_system))
            
            # Get staff information
            all_staves = []
            if hasattr(self.document, 'layout') and self.document.layout:
                if hasattr(self.document.layout, 'sections'):
                    for section in self.document.layout.sections:
                        if hasattr(section, 'staves'):
                            all_staves.extend(section.staves)
                if hasattr(self.document.layout, 'ungrouped_staves'):
                    all_staves.extend(self.document.layout.ungrouped_staves)
            
            if not all_staves:
                return None
            
            # Get measure count
            measure_count = 0
            if hasattr(self.document, 'measures') and self.document.measures:
                if isinstance(self.document.measures, dict):
                    measure_count = len(self.document.measures)
                else:
                    measure_count = len(list(self.document.measures))
            
            if measure_count == 0:
                return None
            
            # Calculate number of systems needed
            num_systems = (measure_count + measures_per_system - 1) // measures_per_system
            
            # Calculate system boundaries
            systems = []
            staff_positions = [staff.y_position for staff in all_staves if hasattr(staff, 'y_position')]
            if not staff_positions:
                return None
                
            base_top = min(staff_positions)
            base_bottom = max(staff_positions) + (4 * 8)  # Staff height
            system_height = base_bottom - base_top + 100  # Add padding
            
            # Calculate x boundaries (approximate)
            left_bound = LEFT_MARGIN + INITIAL_BARLINE_OFFSET
            right_bound = self.width() - 50  # Leave some margin
            
            for system_idx in range(num_systems):
                system_top = base_top + (system_idx * system_spacing)
                system_bottom = system_top + system_height
                
                # CRITICAL FIX: Mark wrapped systems (system_idx > 0) as continuations
                # System 0 is the first system, systems > 0 are wrapped continuations
                is_wrapped = system_idx > 0
                
                systems.append({
                    'index': system_idx,
                    'top': system_top - 25,  # Add tolerance
                    'bottom': system_bottom + 25,  # Add tolerance
                    'left': left_bound,
                    'right': right_bound,
                    'measures_start': system_idx * measures_per_system + 1,
                    'measures_end': min((system_idx + 1) * measures_per_system, measure_count),
                    'is_wrapped': is_wrapped,
                    'is_continuation': is_wrapped  # Alias for clarity
                })
            
            print(f"SYSTEM_BOUNDARIES: Calculated {len(systems)} systems for {measure_count} measures")
            return systems
            
        except Exception as e:
            print(f"SYSTEM_BOUNDARIES: Error calculating boundaries: {e}")
            return None
    
    def find_barline_at_position(self, x, y):
        """Find a barline at the given position"""
        # Convert from view/widget coordinates to unscaled score coordinates
        try:
            score_x, score_y = self.to_score_coords(float(x), float(y))
        except Exception:
            score_x, score_y = x, y

        # In continuous mode, adjust score_x by horizontal offset so we test against real positions
        try:
            if hasattr(self, 'renderer') and self.renderer.get_view_mode() == 'continuous':
                score_x = float(score_x + float(getattr(self, 'continuous_offset_x', 0.0)))
        except Exception:
            pass

        if not self.is_position_valid_for_barline(score_x, score_y):
            print(f"BARLINE_SELECTION: Position x={x}, y={y} not valid for barline operations")
            return None
            
        # Check if click is ON a barline (not just closest)
        # The y-coordinate validation is already done in is_position_valid_for_barline
        
        # Check if document has measures
        if not (hasattr(self.document, 'measures') and self.document.measures):
            print("BARLINE_SELECTION: No measures found in document")
            return None
        
        # Get system boundaries to filter measures more accurately
        system_boundaries = self._get_system_boundaries()
        target_system = None
        
        if system_boundaries:
            # Find which system the click is in
            for system in system_boundaries:
                if (system['top'] <= score_y <= system['bottom'] and 
                    system['left'] <= score_x <= system['right']):
                    target_system = system
                    break
            
            if target_system:
                print(f"BARLINE_SELECTION: Click is in system {target_system['index']} (measures {target_system['measures_start']}-{target_system['measures_end']})")
                # CRITICAL FIX: Exclude wrapped systems (continuations) from selection
                # Wrapped systems are continuations of the same logical system, so we only allow
                # selection in the first system of each logical group
                if target_system.get('is_wrapped', False) or target_system.get('is_continuation', False):
                    print(f"BARLINE_SELECTION: Click is in wrapped/continuation system - excluding from selection")
                    return None
        
        # Check regular measures collection - look for barlines the user clicked ON
        measures = self.document.measures
        if isinstance(measures, dict):
            measures = measures.values()

        closest_measure = None
        min_distance = float('inf')

        for measure in measures:
            if hasattr(measure, 'end_x'):
                mnum = getattr(measure, 'measure_number', 0)
                
                # Filter to target system if we have system boundaries
                if target_system:
                    if not (target_system['measures_start'] <= int(mnum) <= target_system['measures_end']):
                        continue
                
                # Check if click is ON this barline (within narrow margin)
                barline_x = measure.end_x
                distance = abs(barline_x - score_x)
                system_info = f" (sys {target_system['index']})" if target_system else ""
                print(f"BARLINE_SELECTION: Measure {mnum} at x={barline_x}, distance={distance}{system_info}")
                
                # If click is directly on or very close to this barline, select it immediately
                if distance <= 6:  # Very narrow margin for clicking directly ON barline
                    print(f"BARLINE_SELECTION: Click is ON barline {mnum} at x={barline_x} (distance={distance}px)")
                    return measure
                
                # Track closest barline as fallback
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = measure
        
        # ALSO CHECK GRAPHICAL DASHED BARLINES COLLECTION
        if hasattr(self.document, 'graphical_dashed_barlines'):
            print(f"BARLINE_SELECTION: Checking {len(self.document.graphical_dashed_barlines)} graphical dashed barlines")
            for dashed_barline in self.document.graphical_dashed_barlines:
                distance = abs(dashed_barline.x_position - score_x)
                print(f"BARLINE_SELECTION: Dashed barline at x={dashed_barline.x_position}, distance={distance}, contains={dashed_barline.contains_x_position(x)}")
                
                # Check if click is directly on dashed barline
                if distance <= 6:  # Very narrow margin for clicking directly ON dashed barline
                    print(f"BARLINE_SELECTION: Click is ON dashed barline at x={dashed_barline.x_position} (distance={distance}px)")
                    return dashed_barline
                
                # Track closest dashed barline as fallback
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = dashed_barline
                    print(f"BARLINE_SELECTION: New closest dashed barline found at distance {distance}px")
        
        # Return the closest barline if within reasonable threshold (fallback for near misses)
        selection_threshold = 12  # Reasonable threshold - click near barline with some margin
        if closest_measure and min_distance < selection_threshold:
            barline_type = getattr(closest_measure, 'barline_type', 'unknown')
            measure_id = getattr(closest_measure, 'measure_number', 'unknown')
            print(f"BARLINE_SELECTION: Fallback - Found {barline_type} barline at {measure_id}, distance={min_distance}px")
            return closest_measure
        else:
            print(f"BARLINE_SELECTION: No barline found within {selection_threshold}px threshold (closest was {min_distance}px)")
            
        return None

    def to_score_coords(self, x: float, y: float):
        """Convert view/widget coordinates to unscaled score/page coordinates used by renderer.

        Returns a tuple (score_x, score_y).
        """
        try:
            # In continuous mode there is no page centering/stacking; only zoom applies
            try:
                if hasattr(self, 'renderer') and self.renderer.get_view_mode() == 'continuous':
                    zoom = float(getattr(self, 'zoom_factor', 1.0))
                    score_x = float(x) / zoom
                    score_y = float(y) / zoom
                    print(f"COORDS: Continuous View({x:.1f},{y:.1f}) -> Score({score_x:.1f},{score_y:.1f}) zoom={zoom}")
                    return score_x, score_y
            except Exception:
                pass
            # Base page size from renderer
            base_page_width = int(getattr(self.renderer, 'page_width', 800))
            base_page_height = int(getattr(self.renderer, 'page_height', 600))
            zoom = float(getattr(self, 'zoom_factor', 1.0))

            # Horizontal centering of the page within the current widget width
            page_x = int((self.width() - int(base_page_width * zoom)) // 2)

            # Vertical stacking offset for page-down mode (page 0 only for hit tests)
            # Use page_offset_y which is in unscaled page units
            start_y = int(self.page_offset_y * zoom)

            # Inverse transform: first undo translation, then undo scaling
            score_x = (float(x) - float(page_x)) / zoom
            score_y = (float(y) - float(start_y)) / zoom

            # Clamp within page bounds to avoid negative surprises
            if score_x < 0:
                score_x = 0.0
            if score_y < 0:
                score_y = 0.0
            if score_x > base_page_width:
                score_x = float(base_page_width)
            if score_y > base_page_height:
                score_y = float(base_page_height)

            print(f"COORDS: View({x:.1f},{y:.1f}) -> Score({score_x:.1f},{score_y:.1f}) zoom={zoom} page_x={page_x} start_y={start_y}")
            return score_x, score_y
        except Exception as e:
            print(f"COORDS: Fallback conversion due to error: {e}")
            return x, y
    
    def create_barline_at_position(self, x, y):
        """Create a barline at the specified position"""
        print(f"BARLINE_CREATE: Creating barline at x={x}, y={y}")
        
        # Check if we're in edit mode
        if hasattr(self, 'is_setup_mode') and self.is_setup_mode:
            print("BARLINE_CREATE: In setup mode - barline creation disabled")
            return None
        
        # Get barline type from form widget - CRITICAL: No default, respect deselection
        barline_type = None
        form_widget = self.get_form_widget()
        if form_widget and hasattr(form_widget, 'get_selected_barline_type'):
            barline_type = form_widget.get_selected_barline_type()
            print(f"BARLINE_CREATE: Got barline type '{barline_type}' from form widget")
        else:
            print("BARLINE_CREATE: No form widget found or no get_selected_barline_type method")

        # Respect deselection: if no barline type is selected, do not create
        if barline_type is None:
            print("BARLINE_CREATE: No barline type selected - not creating")
            return None
        
        # Respect deselection: if no barline type is selected, do not create
        if barline_type is None:
            print("BARLINE_CREATE: No barline type selected - not creating")
            return None
        
        # Use temporal bridge for barline creation
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            print("BARLINE_CREATE: Using temporal bridge for barline creation")
            new_measure = self.temporal_bridge.create_barline_at_position(x, barline_type)
            
            if new_measure:
                print(f"BARLINE_CREATE: Created barline at x={x}")
                # Force UI update
                self.update()
                return new_measure
            else:
                print(f"BARLINE_CREATE: Failed to create barline at x={x}")
                return None
        
        # Fallback to legacy method if temporal bridge not available
        print("BARLINE_CREATE: Temporal bridge not available - using legacy method")
        return self._create_barline_legacy(x, y, barline_type)
    
    def _create_barline_legacy(self, x, y, barline_type):
        """Fallback method for creating barlines when temporal bridge is not available"""
        # This method should be implemented to create barlines in a legacy way
        # You can use the existing logic for creating barlines if temporal bridge is not available
        # For example, you can use the measure manager to insert a barline
        # or you can use a simple method to create a barline at the specified position
        # This method should return the created barline object
        pass
    
    def get_form_widget(self):
        """Get the Form Widget instance if available"""
        if hasattr(self, 'parent') and self.parent:
            if hasattr(self.parent, 'form_widget'):
                return self.parent.form_widget
        
        # Try to get from main window reference
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'form_widget'):
                return self.main_window.form_widget
        
        # Method 3: Search through parent chain
        parent = self.parent()
        while parent:
            if hasattr(parent, 'form_widget') and parent.form_widget:
                return parent.form_widget
            parent = parent.parent()
        
        # Method 4: Search for any visible FormWidget globally
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            for widget in app.allWidgets():
                if widget.__class__.__name__ == 'FormWidget' and widget.isVisible():
                    return widget
        
        return None
    
    def remove_barline(self, barline):
        """Remove a barline from the score with proper measure system checks"""
        if not barline:
            return
            
        # Check if barline can be removed using measure manager
        if hasattr(self, 'measure_manager') and self.measure_manager:
            if not self.measure_manager.can_remove_barline(barline):
                print(f"BARLINE_REMOVE: Cannot remove barline - it's the initial end bar (measure 1)")
                return
        
        # Check if this is a graphical dashed barline
        if hasattr(barline, 'is_graphical_dashed') and barline.is_graphical_dashed:
            # Remove from graphical dashed barlines collection
            if hasattr(self.document, 'graphical_dashed_barlines'):
                if barline in self.document.graphical_dashed_barlines:
                    self.document.graphical_dashed_barlines.remove(barline)
                    print(f"BARLINE_REMOVE: Removed graphical dashed barline at x={getattr(barline, 'x_position', 'unknown')}")
        else:
            # CRITICAL FIX: Use temporal bridge if the barline was created by it
            if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                if self.temporal_bridge.remove_barline(barline):
                    print(f"BARLINE_REMOVE: Used temporal bridge to remove barline at measure {getattr(barline, 'measure_number', 'unknown')}")
                else:
                    print(f"BARLINE_REMOVE: Temporal bridge could not remove barline, trying fallback methods")
                    # Fallback to measure manager and direct removal
                    self._fallback_remove_barline(barline)
            else:
                # No temporal bridge, use fallback methods
                self._fallback_remove_barline(barline)
        
        # Update display
        self.update()
        
        print(f"BARLINE_REMOVE: Completed removal of barline at {getattr(barline, 'measure_number', getattr(barline, 'x_position', 'unknown'))}")
    
    def _fallback_remove_barline(self, barline):
        """Fallback method for removing barlines when temporal bridge is not available"""
        # Use measure manager if available for proper removal
        if hasattr(self, 'measure_manager') and self.measure_manager and hasattr(barline, 'measure_number'):
            if self.measure_manager.remove_measure(barline.measure_number):
                print(f"BARLINE_REMOVE: Used measure manager to remove measure {barline.measure_number}")
            else:
                print(f"BARLINE_REMOVE: Measure manager failed to remove measure {barline.measure_number}")
        else:
            # Fallback to original removal method
            if hasattr(self.document, 'measures'):
                if isinstance(self.document.measures, dict):
                    if hasattr(barline, 'measure_number') and barline.measure_number in self.document.measures:
                        del self.document.measures[barline.measure_number]
                        print(f"BARLINE_REMOVE: Removed regular measure {barline.measure_number} (fallback)")
                else:
                    if barline in self.document.measures:
                        self.document.measures.remove(barline)
                        print(f"BARLINE_REMOVE: Removed barline from measures list (fallback)")
    
    # NEW: Rhythm Input Methods
    
    def add_note_at_position(self, x_position: float, y_position: float, pitch: str = "C4") -> bool:
        """Add a note at a specific position"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.add_note_at_position(x_position, pitch)
        return False
    
    def add_rest_at_position(self, x_position: float, y_position: float) -> bool:
        """Add a rest at a specific position"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.add_rest_at_position(x_position)
        return False
    
    def add_chord_at_position(self, x_position: float, y_position: float, pitches: list = None) -> bool:
        """Add a chord at a specific position"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.add_chord_at_position(x_position, pitches)
        return False
    
    def remove_notation_at_position(self, x_position: float, y_position: float) -> bool:
        """Remove notation element at a specific position"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.remove_notation_element_at_position(x_position)
        return False
    
    def set_rhythm_input_mode(self, mode: str, duration: str = "QUARTER"):
        """Set the rhythm input mode for notation entry"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            from .temporal_measure_system import NoteDuration
            try:
                duration_enum = NoteDuration[duration.upper()]
                self.temporal_bridge.set_rhythm_input_mode(mode, duration_enum)
                print(f"RHYTHM_INPUT: Set mode to {mode} with duration {duration}")
            except KeyError:
                print(f"RHYTHM_INPUT: Invalid duration {duration}, using QUARTER")
                self.temporal_bridge.set_rhythm_input_mode(mode, NoteDuration.QUARTER)
    
    def get_temporal_layout_info(self) -> dict:
        """Get temporal layout information"""
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.get_layout_info()
        return {}

    def create_test_score(self):
        """
        Create a test score with various staves and sections for testing rendering.
        This method can be called to populate a sample score layout for development.
        """
        print("Creating test score with multiple staves and sections...")
        
        # Create document if it doesn't exist
        if not self.document:
            from .score_document import ScoreDocument
            self.document = ScoreDocument()
            print("STAFFVIEW: Created new ScoreDocument for test score")
        
        # Clear any existing content
        if hasattr(self.document, 'layout'):
            self.document.layout.sections = []
            self.document.layout.ungrouped_staves = []
            
        # Create a strings section
        strings_section = SectionGroup(name="Strings", staves=[])
        
        # Add violin with G major key
        violin = SingleStaff(
            instrument_id="violin",
            instrument_name="Violin",
            instrument_abbr="Vln",
            clef="treble",
            key="G major / E minor (1 sharp)",
            time_signature="4/4"
        )
        strings_section.staves.append(violin)
        
        # Add viola with D major key (alto clef)
        viola = SingleStaff(
            instrument_id="viola",
            instrument_name="Viola",
            instrument_abbr="Vla",
            clef="alto",
            key="D major / B minor (2 sharps)",
            time_signature="4/4"
        )
        strings_section.staves.append(viola)
        
        # Add cello with F major key (bass clef)
        cello = SingleStaff(
            instrument_id="cello",
            instrument_name="Violoncello",
            instrument_abbr="Vc",
            clef="bass",
            key="F major / D minor (1 flat)",
            time_signature="4/4"
        )
        strings_section.staves.append(cello)
        
        # Add the section to the document
        self.document.layout.add_section(strings_section)
        
        # Create a woodwinds section
        woodwinds_section = SectionGroup(name="Woodwinds", staves=[])
        
        # Add flute with Bb major
        flute = SingleStaff(
            instrument_id="flute",
            instrument_name="Flute",
            instrument_abbr="Fl",
            clef="treble",
            key="Bb major / G minor (2 flats)", 
            time_signature="3/4"  # Different time signature
        )
        woodwinds_section.staves.append(flute)
        
        # Add clarinet with Eb major
        clarinet = SingleStaff(
            instrument_id="clarinet",
            instrument_name="Clarinet in Bb",
            instrument_abbr="Cl",
            clef="treble",
            key="Eb major / C minor (3 flats)",
            time_signature="3/4"
        )
        woodwinds_section.staves.append(clarinet)
        
        # Add the section to the document
        self.document.layout.add_section(woodwinds_section)
        
        # CRITICAL: Create some test measures using the temporal bridge
        print("TEST_SCORE: Creating test measures with barlines...")
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            # Create 3 test measures
            for i in range(1, 4):  # Measures 1, 2, 3
                x_position = 200 + (i * 150)  # Space them out
                print(f"TEST_SCORE: Creating measure {i} at x={x_position}")
                success = self.temporal_bridge.create_barline_at_position(x_position, "single")  # Use "single" barline type
                if success:
                    print(f"TEST_SCORE: Successfully created measure {i}")
                else:
                    print(f"TEST_SCORE: Failed to create measure {i}")
        else:
            print("TEST_SCORE: No temporal bridge available for measure creation")
        
        # Add piano grand staff with A major
        top_staff = SingleStaff(
            instrument_id="piano",
            instrument_name="Piano",
            instrument_abbr="Pno",
            clef="treble",
            key="A major / F# minor (3 sharps)",
            time_signature="4/4"
        )
        
        bottom_staff = SingleStaff(
            instrument_id="piano",
            instrument_name="Piano",
            instrument_abbr="Pno",
            clef="bass",
            key="A major / F# minor (3 sharps)",
            time_signature="4/4"
        )
        
        grand_staff = GrandStaff(
            instrument_id="piano",
            instrument_name="Piano",
            instrument_abbr="Pno",
            clef="treble",  # This will be set separately for each staff
            key="A major / F# minor (3 sharps)",
            time_signature="4/4",
            top_staff=top_staff,
            bottom_staff=bottom_staff
        )
        
        self.document.layout.add_staff(grand_staff)
        
        # Add another staff with rare key signature
        rare_key_staff = SingleStaff(
            instrument_id="harp",
            instrument_name="Harp",
            instrument_abbr="Hp",
            clef="treble",
            key="B major / G# minor (5 sharps)",
            time_signature="2/2"  # Cut time
        )
        self.document.layout.add_staff(rare_key_staff)
        
        # Update positions and force refresh
        self.document.layout._update_positions()
        self.update()
        
        print("Test score created with 2 sections (5 staves) and 2 independent staves")
        
        # Switch to edit mode to see the rendering
        self.enter_edit_mode()

    def set_barline_creation_enabled(self, enabled):
        """Enable or disable barline creation mode"""
        self.barline_creation_enabled = enabled
        print(f"STAFFVIEW: Barline creation {'enabled' if enabled else 'disabled'}")

    def is_form_widget_active(self):
        """Check if the form widget is active and visible"""
        # Method 1: Check via main_window attribute
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'form_widget') and self.main_window.form_widget:
                if self.main_window.form_widget.isVisible():
                    print(f"FORM_DEBUG: Form widget is active via main_window")
                    return True
        
        # Method 2: Check via parent chain
        parent = self.parent()
        while parent:
            if hasattr(parent, 'form_widget') and parent.form_widget:
                if parent.form_widget.isVisible():
                    print(f"FORM_DEBUG: Form widget is active via parent chain")
                    return True
            parent = parent.parent()
        
        # Method 3: Check via get_form_widget helper
        form_widget = self.get_form_widget()
        if form_widget and form_widget.isVisible():
            print(f"FORM_DEBUG: Form widget is active via get_form_widget")
            return True
        
        print(f"FORM_DEBUG: No active form widget found")
        return False

    def get_current_staff_ids(self):
        """Get the list of current staff IDs in the document"""
        try:
            staff_ids = []
            if hasattr(self.document, 'layout'):
                # Get ungrouped staves
                if hasattr(self.document.layout, 'ungrouped_staves'):
                    for staff in self.document.layout.ungrouped_staves:
                        staff_ids.append(staff.instrument_id)
                
                # Get staves from sections
                if hasattr(self.document.layout, 'sections'):
                    for section in self.document.layout.sections:
                        for staff in section.staves:
                            staff_ids.append(staff.instrument_id)
            
            print(f"GET_CURRENT_STAFF_IDS: Found {len(staff_ids)} staff IDs: {staff_ids}")
            return staff_ids
        except Exception as e:
            print(f"GET_CURRENT_STAFF_IDS: Error getting staff IDs: {e}")
            return []

    def on_element_selection_changed(self, selected_elements):
        """Handle changes in element selection"""
        try:
            print(f"SELECTION: Element selection changed, {len(selected_elements)} elements selected")
            
            # Clear any previous staff selection when elements are selected
            if selected_elements:
                self.selected_staff = None
            
            # Print selection details for debugging
            for element in selected_elements:
                print(f"SELECTION: Selected {element.element_type}: {element.element_id}")
                
            # Update display to show selection highlights
            self.update()
            
            # TODO: Update preferences panel to show properties of selected elements
            
        except Exception as e:
            print(f"SELECTION_ERROR: Exception in on_element_selection_changed: {e}")
            import traceback
            traceback.print_exc()

    def on_element_double_clicked(self, element):
        """Handle double-click on an element to edit its properties"""
        try:
            print(f"SELECTION: Element double-clicked: {element.element_type} - {element.element_id}")
            
            # Show appropriate properties dialog based on element type
            if element.element_type == 'clef':
                self.show_clef_properties_dialog(element)
            elif element.element_type == 'key_signature':
                self.show_key_signature_properties_dialog(element)
            elif element.element_type == 'time_signature':
                self.show_time_signature_properties_dialog(element)
            elif element.element_type == 'staff_name':
                self.show_staff_name_properties_dialog(element)
            elif element.element_type == 'section_name':
                self.show_section_name_properties_dialog(element)
            else:
                print(f"SELECTION: No properties dialog available for {element.element_type}")
                
        except Exception as e:
            print(f"SELECTION_ERROR: Exception in on_element_double_clicked: {e}")
            import traceback
            traceback.print_exc()

    def on_element_properties_requested(self, element):
        """Handle request to show properties for an element"""
        try:
            print(f"SELECTION: Properties requested for: {element.element_type} - {element.element_id}")
            
            # For now, just print the element properties
            print(f"SELECTION: Element properties: {element.properties}")
            
            # TODO: Open the preferences dialog with the appropriate tab focused
            # and the element properties loaded
            
        except Exception as e:
            print(f"SELECTION_ERROR: Exception in on_element_properties_requested: {e}")
            import traceback
            traceback.print_exc()

    def show_clef_properties_dialog(self, element):
        """Show properties dialog for a clef element"""
        try:
            from ..dialogs.preferences_dialog import PreferencesDialog
            
            # Create and show preferences dialog with clef settings
            prefs_dialog = PreferencesDialog(self)
            # TODO: Set up dialog to focus on clef properties for this element
            prefs_dialog.exec()
            
        except Exception as e:
            print(f"CLEF_PROPS_ERROR: Exception in show_clef_properties_dialog: {e}")

    def show_key_signature_properties_dialog(self, element):
        """Show properties dialog for a key signature element"""
        try:
            from ..dialogs.preferences_dialog import PreferencesDialog
            
            # Create and show preferences dialog with key signature settings
            prefs_dialog = PreferencesDialog(self)
            # TODO: Set up dialog to focus on key signature properties for this element
            prefs_dialog.exec()
            
        except Exception as e:
            print(f"KEY_SIG_PROPS_ERROR: Exception in show_key_signature_properties_dialog: {e}")

    def show_time_signature_properties_dialog(self, element):
        """Show properties dialog for a time signature element"""
        try:
            from ..dialogs.preferences_dialog import PreferencesDialog
            
            # Create and show preferences dialog with time signature settings
            prefs_dialog = PreferencesDialog(self)
            # TODO: Set up dialog to focus on time signature properties for this element
            prefs_dialog.exec()
            
        except Exception as e:
            print(f"TIME_SIG_PROPS_ERROR: Exception in show_time_signature_properties_dialog: {e}")

    def show_staff_name_properties_dialog(self, element):
        """Show properties dialog for a staff name element"""
        try:
            from ..dialogs.preferences_dialog import PreferencesDialog
            
            # Create and show preferences dialog with staff name settings
            prefs_dialog = PreferencesDialog(self)
            # TODO: Set up dialog to focus on staff name properties for this element
            prefs_dialog.exec()
            
        except Exception as e:
            print(f"STAFF_NAME_PROPS_ERROR: Exception in show_staff_name_properties_dialog: {e}")

    def show_section_name_properties_dialog(self, element):
        """Show properties dialog for a section name element"""
        try:
            from ..dialogs.preferences_dialog import PreferencesDialog
            
            # Create and show preferences dialog with section name settings
            prefs_dialog = PreferencesDialog(self)
            # TODO: Set up dialog to focus on section name properties for this element
            prefs_dialog.exec()
            
        except Exception as e:
            print(f"SECTION_NAME_PROPS_ERROR: Exception in show_section_name_properties_dialog: {e}")

    def get_staff_index_at_y(self, y):
        """Get the staff index at the given y coordinate"""
        if not self.document or not hasattr(self.document, 'layout'):
            return None
            
        # Get all staves with their actual positions from the layout system
        all_staves = []
        
        # Add ungrouped staves
        if hasattr(self.document.layout, 'ungrouped_staves'):
            for staff in self.document.layout.ungrouped_staves:
                all_staves.append(staff)
                
        # Add staves from sections
        if hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                if hasattr(section, 'staves'):
                    for staff in section.staves:
                        all_staves.append(staff)
        
        # If no staves found, fall back to simple calculation
        if not all_staves:
            staff_height = STAFF_HEIGHT + STAFF_SPACING
            staff_index = int((y - TOP_MARGIN) / staff_height)
            return staff_index if staff_index >= 0 else None
        
        # Find which staff the y coordinate falls within using actual positions
        for idx, staff in enumerate(all_staves):
            if hasattr(staff, 'y_position'):
                staff_top = staff.y_position
                staff_bottom = staff_top + STAFF_HEIGHT
                
                # Add some tolerance for easier clicking
                tolerance = 15
                if staff_top - tolerance <= y <= staff_bottom + tolerance:
                    return idx
                    
                # Special handling for grand staves - they have two physical staves
                if hasattr(staff, "is_grand_staff") and staff.is_grand_staff:
                    # Check bass clef part of grand staff (typically 72px below treble)
                    bass_staff_top = staff_top + 72
                    bass_staff_bottom = bass_staff_top + STAFF_HEIGHT
                    if bass_staff_top - tolerance <= y <= bass_staff_bottom + tolerance:
                        return idx  # Same index for both parts of grand staff
        
        return None

    def draw_barlines(self, painter, staff_y, staff_height):
        """Draw barlines for the staff"""
        if not hasattr(self.document, 'measures') or not self.document.measures:
                        return
            
        measures = self.document.measures
        if isinstance(measures, dict):
            measures = list(measures.values())
        
        # Determine if this is a single staff or multi-staff system
        total_staves = self.get_total_staff_count()
        is_single_staff = total_staves == 1
        
        # Calculate barline heights based on staff system
        # ALL barlines (including repeat endings) should span the full system height
        if is_single_staff:
            # Single staff: all barlines span just the single staff height
            score_top = TOP_MARGIN
            score_bottom = TOP_MARGIN + STAFF_HEIGHT
        else:
            # Multi-staff: ALL barlines span entire score from top staff line to bottom staff line
            score_top = TOP_MARGIN
            # Calculate the bottom of the last staff including its full height
            last_staff_y = TOP_MARGIN + ((total_staves - 1) * (STAFF_HEIGHT + STAFF_SPACING))
            score_bottom = last_staff_y + STAFF_HEIGHT
        
        for measure in measures:
            if not hasattr(measure, 'end_x') or not hasattr(measure, 'barline_type'):
                continue
                
            x = measure.end_x
            barline_type = measure.barline_type
            
            # Set color based on selection
            if hasattr(measure, 'selected') and measure.selected:
                painter.setPen(QPen(QColor(255, 165, 0, 150), 2))  # Orange for selected
            else:
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # Black for normal
            
            if barline_type == "single":
                # Single barline: spans full system height
                painter.drawLine(x, score_top, x, score_bottom)
                
            elif barline_type == "double":
                # Double barline: spans full system height
                painter.drawLine(x, score_top, x, score_bottom)
                painter.drawLine(x + 3, score_top, x + 3, score_bottom)
                
            elif barline_type == "final":
                # Final barline: spans full system height
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawLine(x, score_top, x, score_bottom)
                painter.setPen(QPen(QColor(0, 0, 0), 3))
                painter.drawLine(x + 4, score_top, x + 4, score_bottom)
                
            elif barline_type == "dashed":
                # Dashed barline: spans full system height
                pen = QPen(QColor(0, 0, 0), 1)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(x, score_top, x, score_bottom)
                
            elif barline_type == "repeat_start":
                # Repeat start: draw barlines spanning full system height, then add dots
                painter.setPen(QPen(QColor(0, 0, 0), 3))  # Thick line
                painter.drawLine(x, score_top, x, score_bottom)
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # Thin line
                painter.drawLine(x + 4, score_top, x + 4, score_bottom)
                
                # Draw repeat dots on each staff with correct positioning
                self.draw_repeat_dots_all_staves(painter, x + 8, "start")
                
            elif barline_type == "repeat_end":
                # Repeat end: draw barlines spanning full system height, then add dots
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # Thin line
                painter.drawLine(x, score_top, x, score_bottom)
                painter.setPen(QPen(QColor(0, 0, 0), 3))  # Thick line
                painter.drawLine(x + 4, score_top, x + 4, score_bottom)
                
                # Draw repeat dots on each staff with correct positioning
                self.draw_repeat_dots_all_staves(painter, x - 4, "end")
                
            elif barline_type == "repeat_both":
                # Repeat both: draw barlines spanning full system height, then add dots on both sides
                painter.setPen(QPen(QColor(0, 0, 0), 3))  # Thick lines
                painter.drawLine(x - 2, score_top, x - 2, score_bottom)
                painter.drawLine(x + 6, score_top, x + 6, score_bottom)
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # Thin lines
                painter.drawLine(x + 2, score_top, x + 2, score_bottom)
                painter.drawLine(x + 10, score_top, x + 10, score_bottom)
                
                # Draw repeat dots on each staff with correct positioning
                self.draw_repeat_dots_all_staves(painter, x - 6, "end")    # Left dots
                self.draw_repeat_dots_all_staves(painter, x + 14, "start") # Right dots
    
    def draw_repeat_dots_all_staves(self, painter, x, repeat_type):
        """Draw repeat dots on all staves with correct positioning"""
        total_staves = self.get_total_staff_count()
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        for staff_index in range(total_staves):
            staff_y_start = TOP_MARGIN + (staff_index * (STAFF_HEIGHT + STAFF_SPACING))
            
            # Calculate correct dot positions:
            # Staff lines are at: y, y+8, y+16, y+24, y+32 (with STAFF_LINE_SPACING = 8)
            # Top dot: exactly in the middle of the space between 2nd and 3rd staff lines
            # Space between 2nd and 3rd lines is from y+8 to y+16, middle is at y+12
            top_dot_y = staff_y_start + STAFF_LINE_SPACING + (STAFF_LINE_SPACING // 2)  # y + 8 + 4 = y + 12
            
            # Bottom dot: exactly in the middle of the space between 3rd and 4th staff lines  
            # Space between 3rd and 4th lines is from y+16 to y+24, middle is at y+20
            bottom_dot_y = staff_y_start + (2 * STAFF_LINE_SPACING) + (STAFF_LINE_SPACING // 2)  # y + 16 + 4 = y + 20
            
            # Draw the two dots with consistent 2.0 radius (same as score_layout.py)
            # This ensures the 3rd staff line falls exactly between the dots
            painter.drawEllipse(QPointF(x, top_dot_y), 2.0, 2.0)
            painter.drawEllipse(QPointF(x, bottom_dot_y), 2.0, 2.0)
        
        painter.setBrush(QBrush())  # Reset brush

    def get_actual_end_barline_x(self) -> float:
        """Get the actual end barline position using dynamic proportional calculation"""
        # Use the same dynamic system as the temporal bridge for consistency
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.get_current_end_barline_x()
        
        # Fallback: calculate dynamically from renderer
        if hasattr(self, 'renderer') and self.renderer:
            page_width = getattr(self.renderer, 'page_width', 800)
            margins = getattr(self.renderer, 'margins', {'right': 50})
            right_margin = margins.get('right', 50)
            return float(page_width - right_margin)
        else:
            # Fallback
            return 750.0  # 800 - 50 default

    def snap_to_measure_grid(self, click_x: float) -> float:
        """Snap click position to the nearest measure grid position"""
        # CRITICAL FIX: Use dynamic end position instead of hardcoded 1136px
        END_BARLINE_X = self.get_actual_end_barline_x()  # Dynamic calculation
        
        # CRITICAL FIX: Use the EXACT same constants as BarlineTemporalBridge
        # to ensure coordinate system alignment
        LEFTMOST_NOTE_X = 225.0  # CRITICAL FIX: Reduced from 265.0 to 225.0 for smaller padding from time signature
        PRACTICAL_SPACE = 180.0   # Must match BarlineTemporalBridge practical space
        BARLINE_SPACING = 15.0    # Must match BarlineTemporalBridge spacing
        
        # CRITICAL FIX: Always generate enough grid positions for user to create more measures
        # Don't limit based on current measure count - allow user to create many more
        MAX_MEASURES = 20  # INCREASED: Allow creation of up to 20 measures per system
        
        # ENHANCED FIX: Always provide full grid regardless of current measure count
        # This ensures users can always create more measures
        current_measures = 0
        if hasattr(self.document, 'measures') and self.document.measures:
            if isinstance(self.document.measures, dict):
                current_measures = len(self.document.measures)
            else:
                current_measures = len(self.document.measures)
        
        # CRITICAL: Always provide MANY grid positions beyond current measures
        measure_count = max(current_measures + 15, MAX_MEASURES)  # INCREASED: Ensure plenty of grid positions
        
        # FIXED: Calculate grid positions using JUSTIFIED SPACING logic
        # This ensures grid positions match the actual justified measure positions
        grid_positions = []
        
        # Get the actual end barline position for the full staff width
        actual_end_x = self.get_actual_end_barline_x()  # This will get the real end position
        
        # Calculate justified positions for the requested number of measures
        for i in range(measure_count):
            if measure_count == 1:
                # Single measure spans from leftmost note to end position
                end_x = actual_end_x
            else:
                # Multiple measures: use justified spacing calculation
                # Total notation space divided equally among measures
                total_notation_space = actual_end_x - LEFTMOST_NOTE_X
                measure_width = total_notation_space / measure_count
                end_x = LEFTMOST_NOTE_X + ((i + 1) * measure_width)
            
            grid_positions.append(round(end_x))
        
        print(f"SNAP_TO_GRID: Generated {len(grid_positions)} justified grid positions for {measure_count} measures")
        
        # Ensure we don't exceed the end barline boundary - but allow plenty of room for expansion
        # Don't artificially limit the grid positions too early
        grid_positions = [pos for pos in grid_positions if pos <= END_BARLINE_X + 200]  # Allow some expansion beyond end
        
        # IMPORTANT: Only include grid positions that make sense for the current document state
        # Remove duplicate positions at the boundary
        grid_positions = list(set(grid_positions))  # Remove duplicates
        grid_positions.sort()  # Sort for consistency
        
        # Find the closest grid position
        closest_position = min(grid_positions, key=lambda x: abs(x - click_x))
        
        print(f"SNAP_TO_GRID: Click at x={click_x} snapped to x={closest_position}")
        print(f"SNAP_TO_GRID: Available grid positions: {grid_positions}")
        return closest_position

    def showEvent(self, event):
        """Handle widget show events - ensure size is set for scrolling"""
        super().showEvent(event)
        # Set widget size when first shown to ensure scroll area recognizes it
        if self.document:
            # Use QTimer to ensure this happens after the widget is fully shown
            QTimer.singleShot(50, self._update_widget_size)
    
    def resizeEvent(self, event):
        """Handle widget resize events to ensure dynamic layout responsiveness"""
        try:
            print(f"STAFFVIEW_RESIZE_DEBUG: StaffView resizeEvent called - size: {self.width()}x{self.height()}")
            super().resizeEvent(event)
            # Do not mutate logical page size on viewport resize; keep document/renderer page size from Preferences
            if hasattr(self, 'renderer') and self.renderer:
                self.update()
            else:
                print(f"STAFFVIEW_RESIZE_DEBUG: No renderer available")
            
            # Force layout refresh if we have a temporal bridge (as backup)
            if (hasattr(self, 'temporal_bridge') and self.temporal_bridge and 
                hasattr(self.temporal_bridge, '_force_layout_refresh')):
                print(f"STAFFVIEW_RESIZE: Forcing backup layout refresh for widget resize to {self.width()}x{self.height()}")
                try:
                    self.temporal_bridge._force_layout_refresh()
                except Exception as e:
                    print(f"STAFFVIEW_RESIZE_ERROR: Error in _force_layout_refresh: {e}")
            else:
                print(f"STAFFVIEW_RESIZE_DEBUG: No temporal_bridge available")
                if not hasattr(self, 'temporal_bridge'):
                    print(f"STAFFVIEW_RESIZE_DEBUG: No temporal_bridge attribute")
                elif not self.temporal_bridge:
                    print(f"STAFFVIEW_RESIZE_DEBUG: temporal_bridge is None")
                elif not hasattr(self.temporal_bridge, '_force_layout_refresh'):
                    print(f"STAFFVIEW_RESIZE_DEBUG: No _force_layout_refresh method on temporal_bridge")
            
            # Force repaint
            try:
                self.update()
                print(f"STAFFVIEW_RESIZE: Forced update after resize")
            except Exception as e:
                print(f"STAFFVIEW_RESIZE_ERROR: Error updating widget: {e}")
        except Exception as e:
            print(f"STAFFVIEW_RESIZE_CRITICAL_ERROR: Unexpected error in resizeEvent: {e}")
            # Don't let resize errors crash the application
            super().resizeEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming and scrolling"""
        # Check if Ctrl/Cmd is held for zooming (macOS trackpad gesture)
        if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
            # Zoom in/out
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            # Calculate zoom center point
            zoom_center = event.position()
            
            # Apply zoom
            self._zoom_at_point(zoom_factor, zoom_center)
            
            event.accept()
        else:
            # For normal scrolling, let the scroll area handle it natively (trackpad gestures work automatically)
            # Only handle continuous mode manually, otherwise pass to parent
            view_mode = self.renderer.get_view_mode() if hasattr(self, 'renderer') else 'page_down'
            if view_mode == 'continuous':
                # Horizontal scrolling in continuous mode
                try:
                    if not hasattr(self, 'continuous_offset_x'):
                        self.continuous_offset_x = 0.0
                    # Prefer horizontal delta when available, otherwise use vertical
                    dx = event.angleDelta().x()
                    delta = event.angleDelta().y()
                    step = 60  # logical px per notch
                    move = -dx if dx != 0 else -delta
                    self.continuous_offset_x = max(0.0, float(self.continuous_offset_x + (move / 120.0) * step))
                    self.update()
                    event.accept()
                    return
                except Exception:
                    pass
            
            # For page modes, handle scrolling via scroll area's scrollbar
            # This enables native macOS trackpad two-finger scrolling
            parent = self.parent()
            scroll_area = None
            while parent is not None:
                from PyQt6.QtWidgets import QScrollArea
                if isinstance(parent, QScrollArea):
                    scroll_area = parent
                    break
                parent = parent.parent()
            
            if scroll_area:
                # Use scrollbar to handle scrolling - this works with macOS trackpad gestures
                vbar = scroll_area.verticalScrollBar()
                hbar = scroll_area.horizontalScrollBar()
                
                # Get scroll delta from event (macOS trackpad provides pixelDelta)
                pixel_delta = event.pixelDelta()
                angle_delta = event.angleDelta()
                
                print(f"WHEEL_EVENT: pixelDelta=({pixel_delta.x()}, {pixel_delta.y()}), angleDelta=({angle_delta.x()}, {angle_delta.y()}), vbar.max={vbar.maximum() if vbar else None}")
                
                if pixel_delta.y() != 0:
                    # Pixel-based scrolling (macOS trackpad)
                    if vbar:
                        old_val = vbar.value()
                        new_val = max(0, min(vbar.maximum(), vbar.value() - pixel_delta.y()))
                        vbar.setValue(new_val)
                        print(f"WHEEL_SCROLL: Pixel scroll {old_val} -> {new_val} (delta={pixel_delta.y()})")
                elif angle_delta.y() != 0:
                    # Angle-based scrolling (mouse wheel fallback)
                    step = int(angle_delta.y() / 8)  # Standard scroll step
                    if vbar:
                        old_val = vbar.value()
                        new_val = max(0, min(vbar.maximum(), vbar.value() - step))
                        vbar.setValue(new_val)
                        print(f"WHEEL_SCROLL: Angle scroll {old_val} -> {new_val} (step={step})")
                
                if pixel_delta.x() != 0:
                    # Horizontal pixel scrolling
                    if hbar:
                        old_val = hbar.value()
                        new_val = max(0, min(hbar.maximum(), hbar.value() - pixel_delta.x()))
                        hbar.setValue(new_val)
                elif angle_delta.x() != 0:
                    # Horizontal angle scrolling
                    step = int(angle_delta.x() / 8)
                    if hbar:
                        old_val = hbar.value()
                        new_val = max(0, min(hbar.maximum(), hbar.value() - step))
                        hbar.setValue(new_val)
                
                event.accept()
            else:
                # Fallback: let event propagate naturally
                event.ignore()
                super().wheelEvent(event)
    
    def _zoom_at_point(self, zoom_factor, zoom_center):
        """Zoom in or out at a specific point on the screen"""
        # Calculate the zoom center in view coordinates
        zoom_center_view = zoom_center - self.rect().center()
        zoom_center_view /= self.zoom_factor
        zoom_center_view += self.rect().center()
            
        # Apply zoom
        self.zoom_factor *= zoom_factor
        self.update()

        # Update the selected barline positions
        try:
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'set_selected_barline_positions'):
                self.renderer.set_selected_barline_positions(self._selected_barline_positions)
        except Exception:
            pass

    def _draw_selected_barline_overlay(self, painter):
        if not getattr(self, '_selected_barline_positions', None):
            return
            
        try:
            zoom = float(getattr(self, 'zoom_factor', 1.0))
            renderer = getattr(self, 'renderer', None)
            if not renderer:
                return
            
            page_width = float(getattr(renderer, 'page_width', self.width()))
            page_height = float(getattr(renderer, 'page_height', self.height()))
            margins = getattr(renderer, 'margins', {}) or {}
            top_margin = float(margins.get('top', 0))
            bottom_margin = float(margins.get('bottom', 0))

            # Compute page origin similar to continuous/page-down mode centering
            page_x = (self.width() - int(page_width * zoom)) / 2.0
            page_y = (self.height() - int(page_height * zoom)) / 2.0 + float(self.page_offset_y) * zoom

            top_y = page_y + top_margin * zoom
            bottom_y = page_y + (page_height - bottom_margin) * zoom

            painter.save()
            pen = QPen(QColor(255, 165, 0, 180), 2)
            pen.setCosmetic(True)
            painter.setPen(pen)

            # Positions are absolute score coordinates (already include left margin).
            # Convert to view by applying page centering and zoom only.
            # Group selected positions by their system so vertical selection lines don't span wrapped systems
            # Build system boundaries using temporal bridge justification/grid
            system_groups = {}
            try:
                if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
                    measures = self.temporal_bridge._get_current_measures()
                    mps = int(getattr(self.temporal_bridge, 'measures_per_system', 4) or 4)
                    for idx, m in enumerate(measures):
                        sys_idx = idx // max(1, mps)
                        system_groups.setdefault(sys_idx, []).append(float(getattr(m, 'end_x', 0.0)))
                else:
                    # Fallback: treat all as one system
                    system_groups = {0: list(map(float, self._selected_barline_positions))}
            except Exception:
                system_groups = {0: list(map(float, self._selected_barline_positions))}

            for score_x in self._selected_barline_positions:
                try:
                    sx = float(score_x)
                except Exception:
                    sx = score_x
                view_x = page_x + sx * zoom
                # Determine which system this x belongs to and clamp to that system's staff heights
                try:
                    sys_top = top_y
                    sys_bottom = bottom_y
                    if hasattr(self, 'renderer') and hasattr(self.renderer, 'document') and hasattr(self.renderer.document, 'layout'):
                        # Approximate by finding nearest system group index
                        sys_idx = 0
                        if system_groups:
                            # Choose the system whose barline set contains/nearest this x
                            best = None
                            for idx, xs in system_groups.items():
                                if any(abs(x - sx) <= 3.0 for x in xs):
                                    best = idx
                                    break
                            if best is None:
                                best = 0
                            sys_idx = best
                        # Compute vertical bounds for that system using staff spacing
                        # Assume single-staff systems; clamp to single staff lines
                        staff_y = None
                        try:
                            # Single staff position (first staff)
                            if hasattr(self.renderer.document.layout, 'ungrouped_staves') and self.renderer.document.layout.ungrouped_staves:
                                staff_y = float(self.renderer.document.layout.ungrouped_staves[0].y_position)
                        except Exception:
                            staff_y = None
                        if staff_y is not None:
                            # Offset by system index using spacing preference
                            spacing_pref = 80
                            try:
                                from PyQt6.QtCore import QSettings
                                spacing_pref = int(QSettings("ONOTE", "Preferences").value("layout/default_system_spacing", 80))
                            except Exception:
                                spacing_pref = 80
                            sys_top = page_y + (staff_y + sys_idx * spacing_pref) * zoom
                            sys_bottom = sys_top + (self.renderer.STAFF_LINE_SPACING * (self.renderer.STAFF_LINE_COUNT - 1)) * zoom
                    painter.drawLine(QPointF(view_x, sys_top), QPointF(view_x, sys_bottom))
                except Exception:
                    painter.drawLine(QPointF(view_x, top_y), QPointF(view_x, bottom_y))

            painter.restore()
        except Exception as e:
            print(f"OVERLAY_DRAW: Failed to draw selection overlay: {e}")

    def _rebuild_selected_barline_positions(self):
        """Synchronize overlay positions with the currently selected barlines."""
        positions = []
        selected_measure_numbers = []
        try:
            # Collect positions from standard measures
            if hasattr(self.document, 'measures') and self.document.measures:
                measures = self.document.measures
                if isinstance(measures, dict):
                    measures = measures.values()
                for measure in measures:
                    if getattr(measure, 'selected', False) and hasattr(measure, 'end_x'):
                        positions.append(float(measure.end_x))
                        try:
                            selected_measure_numbers.append(int(getattr(measure, 'measure_number', 0)))
                        except Exception:
                            pass
            
            # Collect positions from graphical dashed barlines
            if hasattr(self.document, 'graphical_dashed_barlines'):
                for dashed_barline in self.document.graphical_dashed_barlines:
                    if getattr(dashed_barline, 'selected', False) and hasattr(dashed_barline, 'x_position'):
                        positions.append(float(dashed_barline.x_position))

            # Store and pass to renderer (positions in absolute score coordinates)
            self._selected_barline_positions = positions
            if hasattr(self, 'renderer') and hasattr(self.renderer, 'set_selected_barline_positions'):
                self.renderer.set_selected_barline_positions(positions)
                if hasattr(self.renderer, 'set_selected_barline_measures'):
                    self.renderer.set_selected_barline_measures(selected_measure_numbers)
        except Exception as e:
            print(f"BARLINE_OVERLAY: Failed to rebuild selected positions: {e}")

    def keyPressEvent(self, event):
        """Handle key press events for navigation and editing shortcuts"""
        try:
            view_mode = self.renderer.get_view_mode() if hasattr(self, 'renderer') else 'page'
        except Exception:
            view_mode = 'page'
        # Horizontal scroll in continuous mode via arrow keys
        if view_mode == 'continuous' and event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            try:
                if not hasattr(self, 'continuous_offset_x'):
                    self.continuous_offset_x = 0.0
                step = 60
                if event.key() == Qt.Key.Key_Left:
                    self.continuous_offset_x = max(0.0, float(self.continuous_offset_x - step))
                else:
                    self.continuous_offset_x = max(0.0, float(self.continuous_offset_x + step))
                self.update()
                event.accept()
                return
            except Exception:
                pass

        # Delete selected barlines/measures
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            try:
                # Ensure selection state is current
                if hasattr(self, '_rebuild_selected_barline_positions'):
                    self._rebuild_selected_barline_positions()
                selected_measures = []
                if hasattr(self, 'renderer') and hasattr(self.renderer, 'get_selected_measure_numbers'):
                    selected_measures = list(self.renderer.get_selected_measure_numbers() or [])
                if not selected_measures and hasattr(self, 'overlay_selected_measures'):
                    selected_measures = list(getattr(self, 'overlay_selected_measures') or [])
                if selected_measures and hasattr(self, 'document') and hasattr(self.document, 'temporal_bridge') and hasattr(self.document.temporal_bridge, 'delete_measures'):
                    self.document.temporal_bridge.delete_measures(selected_measures)
                    # Clear renderer selection & refresh
                    if hasattr(self, 'renderer'):
                        try:
                            self.renderer.set_selected_barline_measures([])
                        except Exception:
                            pass
                    self.update()
                    event.accept()
                    return
            except Exception as e:
                print(f"DELETE_MEASURE: Failed to delete selected measures: {e}")

