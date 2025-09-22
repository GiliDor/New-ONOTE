from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QDockWidget, QToolBar, QLabel, QMainWindow, QPushButton,
                           QComboBox, QSpinBox, QDialog, QDialogButtonBox, QFormLayout,
                           QTabWidget, QSizePolicy, QFrame, QLineEdit, QTreeWidgetItem,
                           QApplication, QCheckBox, QGroupBox, QScrollArea, QGridLayout,
                           QButtonGroup, QRadioButton)
from PyQt6.QtCore import Qt, QRectF, QPointF, QRect, QPoint, QTimer, QObject, QEvent
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
        
        # PAGE POSITIONING: Make pages moveable within window
        self.page_offset_x = 0.0  # Horizontal offset for page positioning
        self.page_offset_y = 0.0  # Vertical offset for page positioning
        self.is_dragging_page = False
        self.drag_start_pos = None
        self.drag_start_offset = None
        
        # GESTURE SUPPORT: Initialize gesture tracking
        self.last_mouse_pos = None
        self.gesture_start_pos = None
        self.gesture_start_zoom = 1.0
        self.is_gesturing = False
        # Selection visualization mode: use color change in renderer, not overlay
        self.show_selection_overlay = False
        
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
        # Install global event filter so clicks inside StaffView always reach our handler
        try:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
                self._global_click_hook_enabled = True
                print("EVENT_HOOK: Installed global eventFilter for StaffView")
            else:
                self._global_click_hook_enabled = False
        except Exception as e:
            self._global_click_hook_enabled = False
            print(f"EVENT_HOOK: Failed to install global eventFilter: {e}")
        
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
        
        # Create bottom toolbar
        self.toolbar = StaffBarTool(self)
        self.toolbar.staff_changed.connect(self.on_staff_changed)
        self.toolbar.clef_changed.connect(self.on_clef_changed)
        self.toolbar.key_changed.connect(self.on_key_changed)
        
        main_layout.addWidget(self.toolbar)
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
                    
                    # Use section's display order for all staves in the section
                    all_staff_elements.append((section_order, 'staff', staff_data))
                    print(f"STAFFVIEW: Collected staff {staff.instrument_name} from section '{section.name}' with section_order={section_order}")
        
        # Sort all elements by display order and extract staves
        all_staff_elements.sort(key=lambda x: x[0])  # Sort by display_order_index
        added_staves = [element[2] for element in all_staff_elements]
        
        print(f"STAFFVIEW: Built added_staves in proper display order with {len(added_staves)} staves")
        
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
                            self.renderer.measure_number_manager.refresh_settings()
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
        if view_mode == "continuous":
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
    
    def _render_continuous_mode(self, painter, viewport_rect, is_in_setup):
        """Render in continuous scrollable mode with proper A4 page dimensions and unified zoom"""
        print("PAGE_RENDER: Rendering in continuous mode with A4 dimensions and unified zoom")
        
        # Use renderer/document page size instead of hardcoded A4
        MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI
        base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
        base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
        
        # Center the page in the viewport, accounting for zoom
        page_x = (viewport_rect.width() - int(base_page_width * self.zoom_factor)) // 2
        page_y = (viewport_rect.height() - int(base_page_height * self.zoom_factor)) // 2
        
        painter.save()
        painter.translate(page_x, page_y)
        painter.scale(self.zoom_factor, self.zoom_factor)  # Apply zoom ONCE
        
        # Draw page background - PINK for setup mode, WHITE for edit mode
        page_rect = QRect(0, 0, base_page_width, base_page_height)
        if is_in_setup:
            painter.fillRect(page_rect, QColor(255, 192, 203))  # Light pink
        else:
            painter.fillRect(page_rect, QColor(255, 255, 255))
        
        # Draw page border
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(page_rect)
        
        # Set clipping region to page boundaries
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
        # Pass current page index for pagination-aware rendering
        if hasattr(self.renderer, 'current_page'):
            self.renderer.current_page = 0
        mode = 'setup' if is_in_setup else 'edit'
        self.renderer.render_score(painter, page_rect, mode)
        
        painter.restore()
        
        # Update widget size to content so scrollbars know the canvas extents
        try:
            content_w = int(base_page_width * self.zoom_factor)
            # Height should accommodate all pages when page-down mode is active
            total_pages = self._calculate_total_pages()
            content_h = int(base_page_height * self.zoom_factor * max(1, total_pages))
            if self.width() != content_w or self.height() != content_h:
                self.resize(content_w, content_h)
                self.updateGeometry()
        except Exception:
            pass
    
    def _render_page_across_mode(self, painter, viewport_rect, is_in_setup):
        """Render multiple pages side by side"""
        print("PAGE_RENDER: Rendering in page across mode")
        
        # Use renderer/document page size instead of hardcoded A4
        MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI
        base_page_width = getattr(self.renderer, 'page_width', int(210 * MM_TO_PIXELS))
        base_page_height = getattr(self.renderer, 'page_height', int(297 * MM_TO_PIXELS))
        page_margin = 20  # Space between pages (logical)
        
        # Calculate how many pages fit horizontally
        available_width = viewport_rect.width()
        pages_per_row = max(1, int(available_width / ((base_page_width + page_margin) * self.zoom_factor)))
        
        # Get total number of pages needed
        total_pages = self._calculate_total_pages()
        
        # Calculate rows needed
        rows_needed = (total_pages + pages_per_row - 1) // pages_per_row
        
        for page_index in range(total_pages):
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
            mode = 'setup' if is_in_setup else 'edit'
            self.renderer.render_score(painter, page_rect, mode)
            painter.restore()
    
    def _render_page_down_mode(self, painter, viewport_rect, is_in_setup):
        """Render pages stacked vertically so scrolling reveals additional pages"""
        print("PAGE_RENDER: Rendering in page down mode")

        # Ensure total_pages is up to date
        self.total_pages = max(1, self._calculate_total_pages())
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

        # Render each page stacked vertically
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
            mode = 'setup' if is_in_setup else 'edit'
            self.renderer.render_score(painter, page_rect, mode)

            # Footer page number
            painter.setPen(QColor(100, 100, 100))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(page_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, f"Page {page_index + 1}")
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
        try:
            spacing = int(QSettings("ONOTE", "Preferences").value("layout/default_system_spacing", 80))
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
        
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events - no longer used for barline removal"""
        # Double-click functionality removed as per specification
        # Barlines are now only removed via Delete key
        super().mouseDoubleClickEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        print(f"KEYPRESS: Received key event: {event.key()}, focus: {self.hasFocus()}, keyboard grabbed: {getattr(self, '_keyboard_grabbed', False)}")
        
        # Arrow-key navigation for scrolling when embedded in a scroll area
        try:
            if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right):
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
                    step = int(40 * self.zoom_factor)
                    if event.key() == Qt.Key.Key_Up and vbar is not None:
                        vbar.setValue(vbar.value() - step)
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Down and vbar is not None:
                        vbar.setValue(vbar.value() + step)
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Left and hbar is not None:
                        hbar.setValue(hbar.value() - step)
                        event.accept()
                        return
                    if event.key() == Qt.Key.Key_Right and hbar is not None:
                        hbar.setValue(hbar.value() + step)
                        event.accept()
                        return
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
                # Save state for undo BEFORE deletion
                form_widget = self.get_form_widget()
                if form_widget and hasattr(form_widget, 'save_state'):
                    if len(selected_barlines) == 1:
                        form_widget.save_state(f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}")
                    else:
                        form_widget.save_state(f"Delete {len(selected_barlines)} barlines")
                
                # Remove each barline immediately
                successfully_deleted = 0
                for barline in selected_barlines:
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
                
                # Release keyboard grab since barlines are now deleted
                if hasattr(self, '_keyboard_grabbed') and self._keyboard_grabbed:
                    try:
                        self.releaseKeyboard()
                        self._keyboard_grabbed = False
                        print("KEYPRESS_DELETE: Released keyboard grab after deletion")
                    except Exception as e:
                        print(f"KEYPRESS_DELETE: Failed to release keyboard: {e}")
                        self._keyboard_grabbed = False
                
                # Update display
                self.update()
                
                print(f"BARLINE_DELETE: Successfully deleted {successfully_deleted} barline(s) out of {len(selected_barlines)} selected")
                
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
        """Select a barline and highlight it in orange"""
        if not barline:
            return
                
        # Deselect all other barlines first
        self.deselect_all_barlines()
        
        # Select the clicked barline
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

    def is_position_valid_for_barline(self, x, y):
        """Check if the click position is valid for barline placement/selection"""
        # Don't allow barlines too far to the left (before clef/key/time signature area)
        # Use minimal padding so clicks in measure 1 right half are allowed
        if x < LEFT_MARGIN + INITIAL_BARLINE_OFFSET + 10:
            return False
                
        # FIXED: For barline selection, accept ANY y position within the system
        # Since barlines span across all staves, clicking on any staff should work
        
        # Get all staff positions to determine valid system area
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
        
        # Fallback to old behavior if no layout information available
        # Check if y coordinate is within any valid staff area
        staff_index = self.get_staff_index_at_y(y)
        if staff_index is None:
            print(f"BARLINE_POSITION: No staff found at y={y} - INVALID")
            return False
            
        print(f"BARLINE_POSITION: Staff {staff_index} found at y={y} - VALID (fallback)")
        return True
    
    def find_barline_at_position(self, x, y):
        """Find a barline at the given position"""
        if not self.is_position_valid_for_barline(x, y):
            print(f"BARLINE_SELECTION: Position x={x}, y={y} not valid for barline operations")
            return None
            
        # Since barlines span the entire system, we only need to check horizontal distance
        # The y-coordinate validation is already done in is_position_valid_for_barline
        
        # Find the closest barline by horizontal distance only
        closest_measure = None
        min_distance = float('inf')
        
        # Check if document has measures
        if not (hasattr(self.document, 'measures') and self.document.measures):
            print("BARLINE_SELECTION: No measures found in document")
            return None
        
        # Check regular measures collection
        measures = self.document.measures  # Reset iterator
        if isinstance(measures, dict):
            measures = measures.values()
        
        # Filter measures to the clicked system to avoid cross-line interference
        try:
            from PyQt6.QtCore import QSettings
            mps = int(QSettings("ONOTE", "Preferences").value("layout/default_measures_per_system", 4))
            mps = max(1, min(32, mps))
            spacing_pref = int(QSettings("ONOTE", "Preferences").value("layout/default_system_spacing", 80))
        except Exception:
            mps = 4
            spacing_pref = 80
        # Determine top of first staff
        base_top_y = None
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'ungrouped_staves') and self.document.layout.ungrouped_staves:
            base_top_y = float(self.document.layout.ungrouped_staves[0].y_position)
        # Guess system index from y
        sys_idx_guess = 0
        if base_top_y is not None:
            sys_idx_guess = max(0, int((y - base_top_y) // spacing_pref))
        start_num = sys_idx_guess * mps + 1
        end_num = start_num + mps

        for measure in measures:
            if hasattr(measure, 'end_x'):
                mnum = getattr(measure, 'measure_number', 0)
                if not (start_num <= int(mnum) <= end_num):
                    continue
                distance = abs(measure.end_x - x)
                print(f"BARLINE_SELECTION: Measure {mnum} at x={measure.end_x}, distance={distance} (sys {sys_idx_guess})")
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = measure
        
        # ALSO CHECK GRAPHICAL DASHED BARLINES COLLECTION
        if hasattr(self.document, 'graphical_dashed_barlines'):
            print(f"BARLINE_SELECTION: Checking {len(self.document.graphical_dashed_barlines)} graphical dashed barlines")
            for dashed_barline in self.document.graphical_dashed_barlines:
                distance = abs(dashed_barline.x_position - x)
                print(f"BARLINE_SELECTION: Dashed barline at x={dashed_barline.x_position}, distance={distance}, contains={dashed_barline.contains_x_position(x)}")
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = dashed_barline
                    print(f"BARLINE_SELECTION: New closest dashed barline found at distance {distance}px")
        
        # Return the closest barline if within threshold
        selection_threshold = 60  # Widest threshold to ensure reliable selection on empty scores
        if closest_measure and min_distance < selection_threshold:
            barline_type = getattr(closest_measure, 'barline_type', 'unknown')
            measure_id = getattr(closest_measure, 'measure_number', 'unknown')
            print(f"BARLINE_SELECTION: Found {barline_type} barline at {measure_id}, distance={min_distance}px")
            return closest_measure
        else:
            print(f"BARLINE_SELECTION: No barline found within {selection_threshold}px threshold (closest was {min_distance}px)")
            
        return None
    
    def create_barline_at_position(self, x, y):
        """Create a barline at the specified position"""
        print(f"BARLINE_CREATE: Creating barline at x={x}, y={y}")
        
        # Check if we're in edit mode
        if hasattr(self, 'is_setup_mode') and self.is_setup_mode:
            print("BARLINE_CREATE: In setup mode - barline creation disabled")
            return None
        
        # Get barline type from form widget
        barline_type = None
        if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'form_widget') and self.main_window.form_widget:
            barline_type = self.main_window.form_widget.get_selected_barline_type()
            print(f"BARLINE_CREATE: Got barline type '{barline_type}' from form widget")
        # Guard: if no radio selected, do not create measures
        if not barline_type:
            print("BARLINE_CREATE: No barline type selected - no-op")
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
        """Handle mouse wheel for zooming and page navigation"""
        # Check if Ctrl is held for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom in/out
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            # Calculate zoom center point
            zoom_center = event.position()
            
            # Apply zoom
            self._zoom_at_point(zoom_factor, zoom_center)
            
            event.accept()
        else:
            # Page navigation (when not zooming)
            delta = event.angleDelta().y()
            if delta > 0:
                self.previous_page()
            else:
                self.next_page()
            event.accept()
    
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events - no longer used for barline removal"""
        # Double-click functionality removed as per specification
        # Barlines are now only removed via Delete key
        super().mouseDoubleClickEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        print(f"KEYPRESS: Received key event: {event.key()}, focus: {self.hasFocus()}, keyboard grabbed: {getattr(self, '_keyboard_grabbed', False)}")
        
        # Handle both Delete and Backspace keys (Mac "delete" key is actually Backspace in Qt)
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Get all selected barlines
            selected_barlines = self.get_selected_barlines()
            print(f"KEYPRESS_DELETE: Found {len(selected_barlines)} selected barlines")
            
            if selected_barlines:
                # Save state for undo BEFORE deletion
                form_widget = self.get_form_widget()
                if form_widget and hasattr(form_widget, 'save_state'):
                    if len(selected_barlines) == 1:
                        form_widget.save_state(f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}")
                    else:
                        form_widget.save_state(f"Delete {len(selected_barlines)} barlines")
                
                # Remove each barline immediately
                successfully_deleted = 0
                for barline in selected_barlines:
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
                
                # Release keyboard grab since barlines are now deleted
                if hasattr(self, '_keyboard_grabbed') and self._keyboard_grabbed:
                    try:
                        self.releaseKeyboard()
                        self._keyboard_grabbed = False
                        print("KEYPRESS_DELETE: Released keyboard grab after deletion")
                    except Exception as e:
                        print(f"KEYPRESS_DELETE: Failed to release keyboard: {e}")
                        self._keyboard_grabbed = False
                
                # Update display
                self.update()
                
                print(f"BARLINE_DELETE: Successfully deleted {successfully_deleted} barline(s) out of {len(selected_barlines)} selected")
                
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
        """Select a barline and highlight it in orange"""
        if not barline:
            return
                
        # Deselect all other barlines first
        self.deselect_all_barlines()
        
        # Select the clicked barline
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

    def is_position_valid_for_barline(self, x, y):
        """Check if the click position is valid for barline placement/selection"""
        # Don't allow barlines too far to the left (before clef/key/time signature area)
        if x < LEFT_MARGIN + INITIAL_BARLINE_OFFSET + 100:  # Allow some space for signatures
            return False
                
        # FIXED: For barline selection, accept ANY y position within the system
        # Since barlines span across all staves, clicking on any staff should work
        
        # Get all staff positions to determine valid system area
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
        
        # Fallback to old behavior if no layout information available
        # Check if y coordinate is within any valid staff area
        staff_index = self.get_staff_index_at_y(y)
        if staff_index is None:
            print(f"BARLINE_POSITION: No staff found at y={y} - INVALID")
            return False
            
        print(f"BARLINE_POSITION: Staff {staff_index} found at y={y} - VALID (fallback)")
        return True
    
    def find_barline_at_position(self, x, y):
        """Find a barline at the given position"""
        # Selection should not be blocked by area gating; use nearest-x
        # Since barlines are vertical and span the system, use horizontal distance only
        closest = None
        min_distance = float('inf')
        
        # Gather all barlines from measures
        if hasattr(self.document, 'measures') and self.document.measures:
            measures_iter = self.document.measures.values() if isinstance(self.document.measures, dict) else self.document.measures
            for m in measures_iter:
                if hasattr(m, 'end_x'):
                    d = abs(float(m.end_x) - float(x))
                    if d < min_distance:
                        min_distance = d
                        closest = m
        
        # Include graphical dashed barlines
        if hasattr(self.document, 'graphical_dashed_barlines') and self.document.graphical_dashed_barlines:
            for dashed in self.document.graphical_dashed_barlines:
                d = abs(float(getattr(dashed, 'x_position', 0.0)) - float(x))
                if d < min_distance:
                    min_distance = d
                    closest = dashed
        
        if closest is not None:
            print(f"BARLINE_SELECTION: Selected nearest barline (distance={min_distance}px)")
            return closest
        
        print("BARLINE_SELECTION: No barlines available to select")
        return None

    def find_nearest_barline_by_x(self, x):
        """Find nearest barline by x only, ignoring y guards (for selection)."""
        closest = None
        min_distance = float('inf')
        if hasattr(self.document, 'measures') and self.document.measures:
            measures_iter = self.document.measures.values() if isinstance(self.document.measures, dict) else self.document.measures
            for m in measures_iter:
                if hasattr(m, 'end_x'):
                    d = abs(float(m.end_x) - float(x))
                    if d < min_distance:
                        min_distance = d
                        closest = m
        if hasattr(self.document, 'graphical_dashed_barlines'):
            for dashed in getattr(self.document, 'graphical_dashed_barlines', []):
                d = abs(float(getattr(dashed, 'x_position', 0.0)) - float(x))
                if d < min_distance:
                    min_distance = d
                    closest = dashed
        return closest
    
    def create_barline_at_position(self, x, y):
        """Create a barline at the specified position"""
        print(f"BARLINE_CREATE: Creating barline at x={x}, y={y}")
        
        # Check if we're in edit mode
        if hasattr(self, 'is_setup_mode') and self.is_setup_mode:
            print("BARLINE_CREATE: In setup mode - barline creation disabled")
            return None
        
        # Get barline type from form widget
        barline_type = "single"  # Default
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'form_widget') and self.main_window.form_widget:
                barline_type = self.main_window.form_widget.get_selected_barline_type()
                print(f"BARLINE_CREATE: Got barline type '{barline_type}' from form widget")
        
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
            print("DRAW_BARLINES: No measures found in document")
            return
            
        measures = self.document.measures
        if isinstance(measures, dict):
            measures = list(measures.values())
        
        print(f"DRAW_BARLINES: Drawing {len(measures)} measures")
        
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
        
        print(f"DRAW_BARLINES: System bounds - top: {score_top}, bottom: {score_bottom}")
        
        for measure in measures:
            if not hasattr(measure, 'end_x') or not hasattr(measure, 'barline_type'):
                print(f"DRAW_BARLINES: Skipping measure without end_x or barline_type")
                continue
                
            x = measure.end_x
            barline_type = measure.barline_type
            measure_number = getattr(measure, 'measure_number', 1)
            
            print(f"DRAW_BARLINES: Drawing measure {measure_number} at x={x}, type={barline_type}")
            
            # CRITICAL FIX: Skip barline 0 (system connector) - it should not be drawn as a visible barline
            if measure_number == 0:
                print(f"DRAW_BARLINES: Skipping barline 0 (system connector)")
                continue
            
            # Set color based on selection
            if hasattr(measure, 'selected') and measure.selected:
                painter.setPen(QPen(QColor(255, 165, 0, 150), 2))  # Orange for selected
                print(f"DRAW_BARLINES: Drawing selected barline in orange")
            else:
                painter.setPen(QPen(QColor(0, 0, 0), 1))  # Black for normal
                print(f"DRAW_BARLINES: Drawing normal barline in black")
            
            # CRITICAL FIX: Ensure we actually draw the barline
            if barline_type == "single":
                # Single barline: spans full system height
                painter.drawLine(x, score_top, x, score_bottom)
                print(f"DRAW_BARLINES: Drew single barline at x={x}")
                
            elif barline_type == "double":
                # Double barline: spans full system height
                painter.drawLine(x, score_top, x, score_bottom)
                painter.drawLine(x + 3, score_top, x + 3, score_bottom)
                print(f"DRAW_BARLINES: Drew double barline at x={x}")
                
            elif barline_type == "final":
                # Final barline: spans full system height
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawLine(x, score_top, x, score_bottom)
                painter.setPen(QPen(QColor(0, 0, 0), 3))
                painter.drawLine(x + 4, score_top, x + 4, score_bottom)
                print(f"DRAW_BARLINES: Drew final barline at x={x}")
                
            elif barline_type == "dashed":
                # Dashed barline: spans full system height
                pen = QPen(QColor(0, 0, 0), 1)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(x, score_top, x, score_bottom)
                print(f"DRAW_BARLINES: Drew dashed barline at x={x}")
                
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
        """Handle mouse wheel for zooming and page navigation"""
        # Check if Ctrl is held for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom in/out
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            # Calculate zoom center point
            zoom_center = event.position()
            
            # Apply zoom
            self._zoom_at_point(zoom_factor, zoom_center)
            
            event.accept()
        else:
            # Page navigation (when not zooming)
            delta = event.angleDelta().y()
            if delta > 0:
                self.previous_page()
            else:
                self.next_page()
            event.accept()
    
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click events - no longer used for barline removal"""
        # Double-click functionality removed as per specification
        # Barlines are now only removed via Delete key
        super().mouseDoubleClickEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        print(f"KEYPRESS: Received key event: {event.key()}, focus: {self.hasFocus()}, keyboard grabbed: {getattr(self, '_keyboard_grabbed', False)}")
        
        # Handle both Delete and Backspace keys (Mac "delete" key is actually Backspace in Qt)
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            # Get all selected barlines
            selected_barlines = self.get_selected_barlines()
            print(f"KEYPRESS_DELETE: Found {len(selected_barlines)} selected barlines")
            
            if selected_barlines:
                # Save state for undo BEFORE deletion
                form_widget = self.get_form_widget()
                if form_widget and hasattr(form_widget, 'save_state'):
                    if len(selected_barlines) == 1:
                        form_widget.save_state(f"Delete barline at measure {getattr(selected_barlines[0], 'measure_number', 'unknown')}")
                    else:
                        form_widget.save_state(f"Delete {len(selected_barlines)} barlines")
                
                # Remove each barline immediately
                successfully_deleted = 0
                for barline in selected_barlines:
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
                
                # Release keyboard grab since barlines are now deleted
                if hasattr(self, '_keyboard_grabbed') and self._keyboard_grabbed:
                    try:
                        self.releaseKeyboard()
                        self._keyboard_grabbed = False
                        print("KEYPRESS_DELETE: Released keyboard grab after deletion")
                    except Exception as e:
                        print(f"KEYPRESS_DELETE: Failed to release keyboard: {e}")
                        self._keyboard_grabbed = False
                
                # Update display
                self.update()
                
                print(f"BARLINE_DELETE: Successfully deleted {successfully_deleted} barline(s) out of {len(selected_barlines)} selected")
                
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
        """Select a barline and highlight it in orange"""
        if not barline:
            return
                
        # Deselect all other barlines first
        self.deselect_all_barlines()
        
        # Select the clicked barline
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

    def is_position_valid_for_barline(self, x, y):
        """Check if the click position is valid for barline placement/selection"""
        # Don't allow barlines too far to the left (before clef/key/time signature area)
        if x < LEFT_MARGIN + INITIAL_BARLINE_OFFSET + 100:  # Allow some space for signatures
            return False
                
        # FIXED: For barline selection, accept ANY y position within the system
        # Since barlines span across all staves, clicking on any staff should work
        
        # Get all staff positions to determine valid system area
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
        
        # Fallback to old behavior if no layout information available
        # Check if y coordinate is within any valid staff area
        staff_index = self.get_staff_index_at_y(y)
        if staff_index is None:
            print(f"BARLINE_POSITION: No staff found at y={y} - INVALID")
            return False
            
        print(f"BARLINE_POSITION: Staff {staff_index} found at y={y} - VALID (fallback)")
        return True
    
    def find_barline_at_position(self, x, y):
        """Find a barline at the given position"""
        if not self.is_position_valid_for_barline(x, y):
            print(f"BARLINE_SELECTION: Position x={x}, y={y} not valid for barline operations")
            return None
            
        # Since barlines span the entire system, we only need to check horizontal distance
        # The y-coordinate validation is already done in is_position_valid_for_barline
        
        # Find the closest barline by horizontal distance only
        closest_measure = None
        min_distance = float('inf')
        
        # Check if document has measures
        if not (hasattr(self.document, 'measures') and self.document.measures):
            print("BARLINE_SELECTION: No measures found in document")
            return None
        
        # Check regular measures collection
        measures = self.document.measures  # Reset iterator
        if isinstance(measures, dict):
            measures = measures.values()
        
        for measure in measures:
            if hasattr(measure, 'end_x'):
                distance = abs(measure.end_x - x)
                print(f"BARLINE_SELECTION: Measure {getattr(measure, 'measure_number', 'unknown')} at x={measure.end_x}, distance={distance}")
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = measure
        
        # ALSO CHECK GRAPHICAL DASHED BARLINES COLLECTION
        if hasattr(self.document, 'graphical_dashed_barlines'):
            print(f"BARLINE_SELECTION: Checking {len(self.document.graphical_dashed_barlines)} graphical dashed barlines")
            for dashed_barline in self.document.graphical_dashed_barlines:
                distance = abs(dashed_barline.x_position - x)
                print(f"BARLINE_SELECTION: Dashed barline at x={dashed_barline.x_position}, distance={distance}, contains={dashed_barline.contains_x_position(x)}")
                if distance < min_distance:
                    min_distance = distance
                    closest_measure = dashed_barline
                    print(f"BARLINE_SELECTION: New closest dashed barline found at distance {distance}px")
        
        # Return the closest barline if within threshold
        selection_threshold = 90  # Extra-wide to ensure selection near margins
        if closest_measure and min_distance < selection_threshold:
            barline_type = getattr(closest_measure, 'barline_type', 'unknown')
            measure_id = getattr(closest_measure, 'measure_number', 'unknown')
            print(f"BARLINE_SELECTION: Found {barline_type} barline at {measure_id}, distance={min_distance}px")
            return closest_measure
        else:
            print(f"BARLINE_SELECTION: No barline found within {selection_threshold}px threshold (closest was {min_distance}px)")
            
        return None
    
    def create_barline_at_position(self, x, y):
        """Create a barline at the specified position"""
        print(f"BARLINE_CREATE: Creating barline at x={x}, y={y}")
        
        # Check if we're in edit mode
        if hasattr(self, 'is_setup_mode') and self.is_setup_mode:
            print("BARLINE_CREATE: In setup mode - barline creation disabled")
            return None
        
        # Get barline type from form widget
        barline_type = "single"  # Default
        if hasattr(self, 'main_window') and self.main_window:
            if hasattr(self.main_window, 'form_widget') and self.main_window.form_widget:
                barline_type = self.main_window.form_widget.get_selected_barline_type()
                print(f"BARLINE_CREATE: Got barline type '{barline_type}' from form widget")
        
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
        """Handle mouse wheel for zooming and page navigation"""
        # Check if Ctrl is held for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom in/out
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            
            # Calculate zoom center point
            zoom_center = event.position()
            
            # Apply zoom
            self._zoom_at_point(zoom_factor, zoom_center)
            
            event.accept()
        else:
            # Page navigation (when not zooming)
            delta = event.angleDelta().y()
            if delta > 0:
                self.previous_page()
            else:
                self.next_page()
            event.accept()
    

    def eventFilter(self, obj, event):
        """Global event filter to route mouse clicks to StaffView"""
        if event.type() == QEvent.Type.MouseButtonPress:
            # Check if the click is within our geometry
            if self.geometry().contains(event.globalPosition().toPoint()):
                print(f"EVENT_HOOK: Routed global click at {event.position().x()}, {event.position().y()}")
                # Route to our mousePressEvent
                self.mousePressEvent(event)
                return True
        return super().eventFilter(obj, event) if hasattr(super(), 'eventFilter') else False

    def mouseMoveEvent(self, event):
        """Handle mouse move for gesture tracking and page dragging"""
        # Call original mouse move handler first
        super().mouseMoveEvent(event)
        
        # Handle page dragging
        if self.is_dragging_page and event.buttons() & Qt.MouseButton.LeftButton:
            if self.drag_start_pos is not None:
                # Calculate drag delta
                delta = event.position() - self.drag_start_pos
                
                # FIXED: Natural dragging direction (drag left, page moves right)
                self.page_offset_x = self.drag_start_offset.x() + delta.x()
                self.page_offset_y = self.drag_start_offset.y() + delta.y()
                
                # Force redraw
                self.update()
                return
        
        # Track gesture movement
        if self.gesture_start_pos is not None:
            current_pos = event.position()
            distance = (current_pos - self.gesture_start_pos).manhattanLength()
            
            # Start gesture if moved enough
            if distance > 10 and not self.is_gesturing:
                self.is_gesturing = True
            
            # Handle pan gesture
            if self.is_gesturing and event.buttons() & Qt.MouseButton.LeftButton:
                self._handle_pan_gesture(current_pos)
        
        # Touch gestures are now handled by dedicated touch event handlers
        # to avoid conflicts with mouse events
        
        self.last_mouse_pos = event.position()
    
    # Pinch gesture handling moved to dedicated touch event handlers
    # to avoid conflicts with mouse events
    
    def _handle_pan_gesture(self, current_pos):
        """Handle pan gesture for moving around the score"""
        if self.last_mouse_pos is None:
            return
        
        # Calculate pan delta
        delta = current_pos - self.last_mouse_pos
        
        # Update page offset for panning
        self.page_offset_x += delta.x()
        self.page_offset_y += delta.y()
        
        # Force redraw
        self.update()
        
        print(f"GESTURE: Pan gesture delta: {delta}")
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for gesture tracking and page dragging"""
        # Call original mouse release handler first
        super().mouseReleaseEvent(event)
        
        # End gesture tracking
        if event.button() == Qt.MouseButton.LeftButton:
            self.gesture_start_pos = None
            self.is_gesturing = False
            self.is_dragging_page = False
            self.drag_start_pos = None
            self.drag_start_offset = None
            
    def event(self, event):
        """Handle touch and native gesture events for pinch/zoom gestures"""
        try:
            # Route global mouse presses from eventFilter when needed
            if event.type() == QEvent.Type.MouseButtonPress:
                # Let mousePressEvent handle selection/creation
                self.mousePressEvent(event)
                return True
            # Handle Qt gesture framework (pinch)
            if event.type() == QEvent.Type.Gesture:
                pinch = event.gesture(Qt.GestureType.PinchGesture)
                if isinstance(pinch, QPinchGesture):
                    change_flags = pinch.changeFlags()
                    if change_flags & QPinchGesture.ChangeFlag.ScaleFactorChanged:
                        factor = pinch.scaleFactor()
                        # Normalize factor and clamp
                        if factor > 0:
                            new_zoom = max(0.25, min(4.0, self.zoom_factor * factor))
                            if abs(new_zoom - self.zoom_factor) > 0.001:
                                self.zoom_factor = new_zoom
                                print(f"GESTURE: Qt pinch scale factor={factor:.3f}, new_zoom={new_zoom:.3f}")
                                # Notify geometry change for scroll area
                                self.updateGeometry()
                                self.update()
                    event.accept()
                    return True
            # Handle touch events (already present)
            if event.type() == event.Type.TouchBegin:
                return self.touchBeginEvent(event)
            elif event.type() == event.Type.TouchUpdate:
                return self.touchUpdateEvent(event)
            elif event.type() == event.Type.TouchEnd:
                return self.touchEndEvent(event)
            # Handle Mac trackpad pinch gesture (QNativeGestureEvent)
            elif getattr(event, 'type', lambda: None)() == 179:  # QEvent.NativeGesture (fallback)
                # Qt 6: QNativeGestureEvent subtype
                gesture_type = getattr(event, 'gestureType', None)
                zoom_enum = 2
                try:
                    zoom_enum = int(getattr(Qt, 'NativeGestureType').Zoom)
                except Exception:
                    pass
                if gesture_type is not None and int(gesture_type) == zoom_enum:
                    # event.value() is the scale delta (positive for zoom in, negative for zoom out)
                    scale_delta = getattr(event, 'value', lambda: 0.0)()
                    if abs(scale_delta) > 0.001:
                        # Typical scale_delta is small, e.g. 0.05 for 5% zoom
                        new_zoom = self.zoom_factor * (1.0 + scale_delta)
                        new_zoom = max(0.25, min(4.0, new_zoom))
                        if abs(new_zoom - self.zoom_factor) > 0.001:
                            self.zoom_factor = new_zoom
                            print(f"GESTURE: Mac pinch zoom, scale_delta={scale_delta:.3f}, new_zoom={new_zoom:.3f}")
                            self.update()
                        return True
            return super().event(event)
        except Exception as e:
            print(f"GESTURE: Error in event handling: {e}")
            return super().event(event)

    def wheelEvent(self, event):
        """Ctrl/Cmd + wheel to zoom."""
        try:
            modifiers = QApplication.keyboardModifiers()
            if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                delta_steps = event.angleDelta().y() / 120.0
                if abs(delta_steps) > 0:
                    factor = 1.0 + 0.1 * delta_steps
                    self._zoom_at_point(factor, QPointF(event.position().x(), event.position().y()))
                    event.accept()
                    return
        except Exception as e:
            print(f"GESTURE: wheelEvent error: {e}")
        super().wheelEvent(event)
            
    def touchBeginEvent(self, event):
        """Handle touch begin for pinch gesture detection"""
        try:
            touch_points = event.touchPoints()
            if touch_points and len(touch_points) >= 2:
                self.touch_points = touch_points
                self.initial_touch_distance = self._calculate_touch_distance(touch_points)
                self.initial_zoom = self.zoom_factor
                print(f"GESTURE: Touch begin - {len(touch_points)} points, distance={self.initial_touch_distance}")
            return True
        except Exception as e:
            print(f"GESTURE: Error in touch begin: {e}")
            return True
        
    def touchUpdateEvent(self, event):
        """Handle touch update for pinch gesture processing"""
        try:
            if not hasattr(self, 'initial_touch_distance') or not hasattr(self, 'initial_zoom'):
                return True
                
            touch_points = event.touchPoints()
            if not touch_points or len(touch_points) < 2:
                return True
                
            current_distance = self._calculate_touch_distance(touch_points)
            
            if self.initial_touch_distance > 0 and current_distance > 0:
                # Calculate zoom factor based on distance change
                zoom_ratio = current_distance / self.initial_touch_distance
                new_zoom = self.initial_zoom * zoom_ratio
                
                # Clamp zoom to reasonable limits
                new_zoom = max(0.25, min(4.0, new_zoom))
                
                if abs(new_zoom - self.zoom_factor) > 0.01:  # Only update if change is significant
                    self.zoom_factor = new_zoom
                    print(f"GESTURE: Pinch zoom - ratio={zoom_ratio:.2f}, new_zoom={new_zoom:.2f}")
                    self.update()
                    
            return True
        except Exception as e:
            print(f"GESTURE: Error in touch update: {e}")
            return True
        
    def touchEndEvent(self, event):
        """Handle touch end for pinch gesture cleanup"""
        try:
            if hasattr(self, 'initial_touch_distance'):
                delattr(self, 'initial_touch_distance')
            if hasattr(self, 'initial_zoom'):
                delattr(self, 'initial_zoom')
            print("GESTURE: Touch end - pinch gesture completed")
            return True
        except Exception as e:
            print(f"GESTURE: Error in touch end: {e}")
            return True
        
    def _calculate_touch_distance(self, touch_points):
        """Calculate distance between touch points for pinch gesture"""
        try:
            if len(touch_points) < 2:
                return 0
                
            point1 = touch_points[0].pos()
            point2 = touch_points[1].pos()
            
            # Calculate Euclidean distance
            dx = point2.x() - point1.x()
            dy = point2.y() - point1.y()
            distance = (dx * dx + dy * dy) ** 0.5
            
            return distance
        except Exception as e:
            print(f"GESTURE: Error calculating touch distance: {e}")
            return 0
    
    def _zoom_at_point(self, zoom_factor, center_point):
        """Zoom in/out centered on a specific point"""
        try:
            old_zoom = self.zoom_factor
            new_zoom = max(0.25, min(4.0, self.zoom_factor * zoom_factor))
            
            if new_zoom != old_zoom:
                self.zoom_factor = new_zoom
                print(f"GESTURE: Zoomed to {new_zoom * 100:.0f}% at point {center_point}")
                self.update()
        except Exception as e:
            print(f"GESTURE: Error in _zoom_at_point: {e}")
            # Fallback to simple zoom without point centering
            self.zoom_factor = max(0.25, min(4.0, self.zoom_factor * zoom_factor))
            self.update()
    
    def zoom_in(self):
        """Zoom in by 20% (relative to document window height)"""
        center_point = QPointF(self.width() / 2, self.height() / 2)
        self._zoom_at_point(1.2, center_point)
    
    def zoom_out(self):
        """Zoom out by 20% (relative to document window height)"""
        center_point = QPointF(self.width() / 2, self.height() / 2)
        self._zoom_at_point(0.8, center_point)
    
    def reset_zoom(self):
        """Reset zoom to 100% (relative to document window height) and center the page"""
        try:
            # Calculate optimal zoom for 100% (full document window height)
            if hasattr(self, 'parent') and self.parent():
                window_height = self.parent().height() - 100  # Approximate menu bar height
            else:
                window_height = 800  # Fallback
                
            if hasattr(self, 'document') and self.document:
                score_height = getattr(self.document, 'page_height', 800)
                optimal_zoom = window_height / score_height
            else:
                optimal_zoom = 1.0
                
            # Clamp to reasonable bounds
            optimal_zoom = max(0.25, min(4.0, optimal_zoom))
            
            if self.zoom_factor != optimal_zoom:
                self.zoom_factor = optimal_zoom
                # Reset page offset to center
                if hasattr(self, 'page_offset_x'):
                    self.page_offset_x = 0.0
                if hasattr(self, 'page_offset_y'):
                    self.page_offset_y = 0.0
                print(f"GESTURE: Reset zoom to 100% (relative to window height: {int(optimal_zoom * 100)}%) and centered page")
                self.update()
        except Exception as e:
            print(f"GESTURE: Error in reset_zoom: {e}")
            # Fallback to simple reset
            self.zoom_factor = 1.0
            self.update()
    
    def next_page(self):
        """Navigate to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            print(f"PAGE_NAV: Navigated to page {self.current_page + 1}")
            self.update()
    
    def previous_page(self):
        """Navigate to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            print(f"PAGE_NAV: Navigated to page {self.current_page + 1}")
            self.update()
    
    def go_to_page(self, page_num):
        """Navigate to specific page"""
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            print(f"PAGE_NAV: Navigated to page {self.current_page + 1}")
            self.update()
    
    def update_total_pages(self):
        """Update total page count"""
        self.total_pages = self._calculate_total_pages()
        # Ensure current page is valid
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)



class StaffBarTool(QWidget):
    staff_changed = pyqtSignal(dict)  # Signal emitted when staff settings change
    clef_changed = pyqtSignal(dict)   # Signal emitted when clef changes
    key_changed = pyqtSignal(dict)    # Signal emitted when key signature changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border-top: 1px solid #ccc;
            }
            QPushButton {
                min-width: 60px;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the toolbar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Create buttons with icons/text
        self.clef_btn = QPushButton("Clef")
        self.key_btn = QPushButton("Key")
        self.time_btn = QPushButton("Time")  # To be implemented later
        
        # Connect button signals
        self.clef_btn.clicked.connect(self.show_clef_dialog)
        self.key_btn.clicked.connect(self.show_key_dialog)
        
        # Add buttons to layout
        layout.addWidget(self.clef_btn)
        layout.addWidget(self.key_btn)
        layout.addWidget(self.time_btn)
        
        # Add stretch to push controls to the left
        layout.addStretch()
            
    def show_clef_dialog(self):
        """Show the clef selection dialog"""
        dialog = ClefDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.clef_changed.emit(settings)
            
    def show_key_dialog(self):
        """Show the key signature dialog"""
        dialog = KeyDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.key_changed.emit(settings)
            
    def show_time_signature_dialog(self):
        """Show the time signature dialog"""
        dialog = TimeSignatureDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            # Emit the time signature changed signal with the settings
            self.time_changed.emit(settings)
            
    def update_staff_count(self, count):
        """Update the staff count in the clef and key dialogs"""
        # This is for future enhancements of multi-staff selection
        # Enable or disable buttons based on staff count
        enable_buttons = count > 0
        self.clef_btn.setEnabled(enable_buttons)
        self.key_btn.setEnabled(enable_buttons)
        self.time_btn.setEnabled(enable_buttons) 