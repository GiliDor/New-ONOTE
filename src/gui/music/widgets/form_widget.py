from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                           QLabel, QLineEdit, QComboBox, QSpinBox, QCheckBox,
                           QGroupBox, QRadioButton, QScrollArea, QTabWidget,
                           QSplitter, QDialog, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QSettings, QPoint, QSize, QEvent
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from ..measure_object import MeasureObject
from ..staff_types import StaffType, StaffBase, SingleStaff, GrandStaff
from ..score_document import ScoreDocument

"""
Enhanced Form Widget - Comprehensive Musical Form Control

This widget provides complete control over musical form elements including:
- Barline creation and management with proper SMuFL symbols
- Repeat markings and endings
- Musical directions (D.C., D.S., Segno, Coda, etc.)
- Dynamic measure width and layout
- Mouse interaction for barline placement
- Comprehensive undo/redo support
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QGroupBox, QLabel, QPushButton, QComboBox, QSpinBox, QCheckBox,
    QButtonGroup, QRadioButton, QListWidget, QListWidgetItem,
    QSplitter, QTextEdit, QLineEdit, QSlider, QProgressBar,
    QTabWidget, QScrollArea, QFrame, QSizePolicy, QSpacerItem,
    QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QRect
from PyQt6.QtGui import QFont, QFontMetrics, QPainter, QPen, QColor, QBrush

from ..notation_constants import (
    BARLINE_CONSTANTS, MUSICAL_DIRECTION_CONSTANTS, FORM_LAYOUT_CONSTANTS,
    MUSIC_FONTS, FONT_SIZES, POSITION_CONSTANTS, SYMBOL_MAP
)


class FormWidget(QWidget):
    """
    Enhanced Form Widget for comprehensive musical form control
    
    Features:
    - Barline creation with proper SMuFL symbols
    - Musical directions and jumps
    - Dynamic measure width and layout
    - Mouse interaction support
    - Undo/redo integration
    """
    
    # Signals
    measure_added = pyqtSignal(int)  # measure_number
    measure_deleted = pyqtSignal(int)  # measure_number
    measure_modified = pyqtSignal(int, dict)  # measure_number, properties
    structure_changed = pyqtSignal(list)  # list of measures
    barline_placement_requested = pyqtSignal(str, float)  # barline_type, x_position
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # CRITICAL FIX: Ensure widget always shows on Desktop background, never behind it
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Enable keyboard focus for delete key functionality
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Store the document reference from parent
        if hasattr(parent, 'document'):
            self.document = parent.document
        elif hasattr(parent, 'staff_view') and hasattr(parent.staff_view, 'document'):
            self.document = parent.staff_view.document
        else:
            # Create a minimal document if none exists
            from ..score_document import ScoreDocument
            self.document = ScoreDocument()
        
        # Store main window reference - traverse up the parent chain to find MainWindow
        self.main_window_ref = parent
        while self.main_window_ref and not hasattr(self.main_window_ref, 'staff_view'):
            self.main_window_ref = self.main_window_ref.parent()
        
        # Initialize state management
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50  # Maximum number of undo steps to keep
        self.current_measure = None
        self.current_measure_number = 1  # Initialize to first measure
        self.measures = {}  # Dictionary of measure_number -> MeasureObject
        self.measures_per_system = 4
        # Layout settings (auto_justify, dynamic_width) are now handled by Preferences dialog
        self.selected_barline = None  # Track selected barline for modification
        self.barline_creation_enabled = True  # Always enabled according to spec
        self._syncing_ui_to_selection = False  # Flag to prevent modification during UI sync
        
        # Set up the UI
        self.setup_ui()
        
        # RESTRUCTURE: No automatic measure initialization
        # DISABLED: self.initialize_default_measures() - measures created on first user click
        print("FORM_WIDGET: No automatic measures - created on first staff click")
        
        # Connect signals after everything is initialized
        self.connect_signals()
        
        # Enable staff interaction
        self.enable_staff_interaction()
        
        # NEW: Integrate temporal bridge if available
        self._integrate_temporal_bridge()
        
        # Mark initialization as complete
        self._initialization_complete = True
        
        # Add flag to prevent saving settings during initialization
        self._loading_settings = True
    
        # Load settings from document (but don't save during initialization)
        self.load_settings_from_document()
        
        # Mark loading as complete
        self._loading_settings = False
    
    def load_settings_from_document(self):
        """Load settings from the current document or QSettings for new documents"""
        from PyQt6.QtCore import QSettings
        qsettings = QSettings()
        
        # Temporarily disconnect signals to prevent triggering save_settings_to_document during loading
        signal_connections = []
        # Layout settings (auto_justify_check, dynamic_width_check) are now handled by Preferences dialog
        if hasattr(self, 'max_measures_per_system') and self.max_measures_per_system is not None:
            try:
                signal_connections.append((self.max_measures_per_system.valueChanged, self.update_score))
                self.max_measures_per_system.valueChanged.disconnect(self.update_score)
            except Exception:
                pass
        if hasattr(self, 'show_measure_numbers') and self.show_measure_numbers is not None:
            try:
                signal_connections.append((self.show_measure_numbers.toggled, self.update_score))
                self.show_measure_numbers.toggled.disconnect(self.update_score)
            except Exception:
                pass
        if hasattr(self, 'barline_numbering') and self.barline_numbering is not None:
            try:
                signal_connections.append((self.barline_numbering.toggled, self.update_score))
                self.barline_numbering.toggled.disconnect(self.update_score)
            except Exception:
                pass
        
        # Helper function to get setting with precedence: QSettings first for new documents, then document settings
        def get_setting_with_precedence(key1, key2, default_value):
            # For new documents, prefer QSettings (preferences) over document settings
            # This ensures that preferences are respected for new scores
            if hasattr(self, 'document') and self.document and hasattr(self.document, 'settings') and self.document.settings:
                # Check if this is a new document (no measures yet)
                is_new_document = not hasattr(self.document, 'measures') or not self.document.measures
                
                if is_new_document:
                    # For new documents, use QSettings (preferences) first
                    val = qsettings.value(key1, None)
                    if val is not None:
                        return val
                    val = qsettings.value(key2, None)
                    if val is not None:
                        return val
                    # Then fall back to document settings if they exist
                    if key1 in self.document.settings:
                        return self.document.settings[key1]
                    if key2 in self.document.settings:
                        return self.document.settings[key2]
                else:
                    # For existing documents, use document settings first
                    if key1 in self.document.settings:
                        return self.document.settings[key1]
                    if key2 in self.document.settings:
                        return self.document.settings[key2]
                    # Then fall back to QSettings
                    val = qsettings.value(key1, None)
                    if val is not None:
                        return val
                    val = qsettings.value(key2, None)
                    if val is not None:
                        return val
            
            # If no document or no document settings, use QSettings
            val = qsettings.value(key1, None)
            if val is not None:
                return val
            val = qsettings.value(key2, None)
            if val is not None:
                return val
            
            return default_value
        
        try:
            # Measures per system
            max_measures = get_setting_with_precedence('notation/max_measures_per_system', 'layout/default_measures_per_system', 4)
            self.max_measures_per_system.setValue(int(max_measures))
            
            # Load measure numbers settings using helper function
            show_measure_numbers = get_setting_with_precedence('notation/show_measure_numbers', 'notation/show_measure_numbers', True)
            self.show_measure_numbers.setChecked(bool(show_measure_numbers))
            
            measure_number_frequency = get_setting_with_precedence('notation/measure_number_frequency', 'notation/measure_number_frequency', 'Every Measure')
            self.measure_number_frequency.setCurrentText(str(measure_number_frequency))
            
            measure_number_position = get_setting_with_precedence('notation/measure_number_position', 'notation/measure_number_position', 'Center')
            self.measure_number_position.setCurrentText(str(measure_number_position))
            
            measure_numbers_vertical = get_setting_with_precedence('notation/measure_numbers_vertical', 'notation/measure_numbers_vertical', 'Above System')
            self.measure_numbers_vertical.setCurrentText(str(measure_numbers_vertical))
            
            measure_numbers_font_size = get_setting_with_precedence('notation/measure_numbers_font_size', 'notation/measure_numbers_font_size', 10)
            self.measure_numbers_font_size.setValue(int(measure_numbers_font_size))
            
            measure_numbers_vertical_offset = get_setting_with_precedence('notation/measure_numbers_vertical_offset', 'notation/measure_numbers_vertical_offset', -20)
            self.measure_numbers_vertical_offset.setValue(int(measure_numbers_vertical_offset))
            
            measure_numbers_horizontal_offset = get_setting_with_precedence('notation/measure_numbers_horizontal_offset', 'notation/measure_numbers_horizontal_offset', -34)
            self.measure_numbers_horizontal_offset.setValue(int(measure_numbers_horizontal_offset))
            
            # Load barline control settings using helper function
            barline_numbering = get_setting_with_precedence('notation/barline_numbering', 'notation/barline_numbering', False)
            self.barline_numbering.setChecked(bool(barline_numbering))
            
            barline_number_font_size = get_setting_with_precedence('notation/barline_number_font_size', 'notation/barline_number_font_size', 8)
            self.barline_number_font_size.setValue(int(barline_number_font_size))
            
            # Layout settings are now handled by Preferences dialog
            # These settings are loaded from QSettings as global defaults
            
            # Load color settings using helper function
            measure_numbers_color = get_setting_with_precedence('notation/measure_numbers_font_color', 'notation/measure_numbers_font_color', '#000000')
            barline_numbers_color = get_setting_with_precedence('notation/barline_numbers_font_color', 'notation/barline_numbers_font_color', '#666666')
            
            # Set color values and update button styles
            setattr(self, 'measure_numbers_color_value', measure_numbers_color)
            setattr(self, 'barline_numbers_color_value', barline_numbers_color)
            
            # Update color button styles if they exist
            if hasattr(self, 'measure_numbers_font_color'):
                self.measure_numbers_font_color.setStyleSheet(
                    f"background-color: {measure_numbers_color}; color: {'white' if self.is_dark_color_hex(measure_numbers_color) else 'black'}; border-radius: 4px; padding: 6px;"
                )
            
            if hasattr(self, 'barline_number_font_color'):
                self.barline_number_font_color.setStyleSheet(
                    f"background-color: {barline_numbers_color}; color: {'white' if self.is_dark_color_hex(barline_numbers_color) else 'black'}; border-radius: 4px; padding: 6px;"
                )
            
        except Exception as e:
            print(f"FORM_WIDGET: Failed to load settings: {e}")
            import traceback
            traceback.print_exc()
            # Set defaults if loading fails
            self.max_measures_per_system.setValue(4)
            self.show_measure_numbers.setChecked(True)
            self.measure_number_frequency.setCurrentText('Every Measure')
            self.measure_number_position.setCurrentText('Center')
            self.measure_numbers_vertical.setCurrentText('Above System')
            self.measure_numbers_font_size.setValue(10)
            self.measure_numbers_vertical_offset.setValue(-20)
            self.measure_numbers_horizontal_offset.setValue(-34)
            self.barline_numbering.setChecked(False)
            self.barline_number_font_size.setValue(8)
            # Layout settings are now handled by Preferences dialog
        finally:
            # Reconnect signals (only if sender still exists and not deleted)
            for signal, slot in signal_connections:
                try:
                    sender = signal.sender()
                    if sender is not None:
                        signal.connect(slot)
                except Exception:
                    pass
    
    def enable_staff_interaction(self):
        """Enable staff interaction for barline creation and selection"""
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            # Enable barline creation on staff view
            self.main_window_ref.staff_view.set_barline_creation_enabled(True)
            
            # Connect mouse events if not already connected
            if not hasattr(self.main_window_ref.staff_view, '_form_widget_connected'):
                self.main_window_ref.staff_view._form_widget_connected = True
                # The staff view will emit signals that we're already connected to
    
    def _integrate_temporal_bridge(self):
        """Integrate with temporal bridge for rhythm input capabilities"""
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            if hasattr(staff_view, 'temporal_bridge'):
                from ..barline_temporal_bridge import integrate_bridge_with_form_widget
                integrate_bridge_with_form_widget(self, staff_view.temporal_bridge)
                print("FORM_WIDGET: Integrated with temporal bridge for rhythm input")
    
    def add_measure_to_score(self, x_position):
        """Add a new measure to the score at the specified position"""
        # Get current barline type
        selected_button = self.barline_button_group.checkedButton()
        if not selected_button:
            return None
            
        barline_type = selected_button.property("barline_type")
        
        # Dashed barlines don't add measures
        if barline_type == "dashed":
            self.add_dashed_barline(x_position)
            return None
        
        # Save state for undo
        self.save_state("Add measure to score")
        
        # Create new measure
        measure_num = len(self.measures) + 1
        measure = MeasureObject(measure_num, x_position)
        measure.barline_type = barline_type
        
        # Set repeat count for repeat barlines
        if barline_type in ["repeat_start", "repeat_end", "repeat_both"]:
            measure.repeat_count = self.repeat_count_spin.value()
        
        # Add to measures
        self.measures[measure_num] = measure
        
        # Update score document if available
        if hasattr(self, 'document') and self.document:
            if not hasattr(self.document, 'measures'):
                self.document.measures = {}
            self.document.measures[measure_num] = measure
        
        # Update layout based on settings
        self.update_score_layout()
        
        # Update status
        self.update_status(f"Added {barline_type} barline at measure {measure_num}")
        
        # Update undo/redo buttons
        self.update_undo_redo_buttons()
        
        return measure
    
    def add_dashed_barline(self, x_position):
        """Add a dashed barline for notation convenience (doesn't create a measure)"""
        
        # CRITICAL FIX: Check for overlap with existing barlines before inserting
        if self._check_barline_overlap(x_position):
            print(f"FORM_WIDGET: Cannot add dashed barline at x={x_position} - position already occupied by another barline")
            self.update_status(f"Cannot add dashed barline - position already occupied by another barline")
            return None
        
        # Save state for undo
        self.save_state("Add dashed barline")
        
        # Create a special dashed barline object (not a full measure)
        dashed_id = f"dashed_{len([m for m in self.measures.values() if getattr(m, 'is_dashed', False)]) + 1}"
        
        # For now, we'll create a special measure object marked as dashed
        measure = MeasureObject(dashed_id, x_position)
        measure.barline_type = "dashed"
        measure.is_dashed = True  # Mark as dashed for special handling
        
        # Add to measures with special key
        self.measures[dashed_id] = measure
        
        # Update status
        self.update_status(f"Added dashed barline at position {x_position}")
        
        # Update undo/redo buttons
        self.update_undo_redo_buttons()
        
        return measure
    
    def _check_barline_overlap(self, x_position):
        """Check if a barline already exists at the given x position"""
        # Tolerance for overlap detection (in pixels)
        tolerance = 5.0
        
        # Check all existing measures for overlap
        for measure in self.measures.values():
            if hasattr(measure, 'end_x'):
                if abs(measure.end_x - x_position) < tolerance:
                    print(f"FORM_WIDGET: Overlap detected - existing barline at {measure.end_x}, trying to insert at {x_position}")
                    return True
        
        # Also check document measures if available
        if hasattr(self, 'document') and self.document and hasattr(self.document, 'measures'):
            for measure in self.document.measures.values():
                if hasattr(measure, 'end_x'):
                    if abs(measure.end_x - x_position) < tolerance:
                        print(f"FORM_WIDGET: Overlap detected in document - existing barline at {measure.end_x}, trying to insert at {x_position}")
                        return True
        
        return False
    
    def update_score_layout(self):
        """Update the score layout based on current settings"""
        if not hasattr(self, 'document') or not self.document:
            return
            
        # Get measures per system from the new barline control setting
        measures_per_system = self.max_measures_per_system.value()
        
        # Layout settings (auto_justify, dynamic_width) are now handled by Preferences dialog
        # Only update measures per system in document settings
        
        print(f"FORM_WIDGET: Updating layout - measures_per_system={measures_per_system}")
        
        # Update document settings
        if not hasattr(self.document, 'settings'):
            self.document.settings = {}
        
        self.document.settings.update({
            'layout/measures_per_system': measures_per_system,
        })
        
        # Update the staff view if available
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            
            # CRITICAL FIX: Reload renderer settings after updating document
            if hasattr(staff_view, 'renderer') and staff_view.renderer:
                # Force the renderer to reload notation settings with document precedence
                staff_view.renderer.load_notation_settings()
                print("FORM_WIDGET: Reloaded renderer notation settings in layout update")
            
            # Force a repaint
            staff_view.update()
        
        print("FORM_WIDGET: Layout updated")
    
    def setup_ui(self):
        """Set up the user interface with improved layout and styling"""
        self.setWindowTitle("Musical Form")
        self.setMinimumSize(520, 500)
        self.resize(580, 700)
        
        # Set window flags for floating window
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        
        # Apply modern styling with improved font sizes
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 12pt;
            }
            QGroupBox {
                font-size: 13pt;
                font-weight: bold;
                margin-top: 18px;
                margin-bottom: 8px;
            }
            QLabel {
                font-size: 12pt;
            }
            QCheckBox, QRadioButton, QComboBox, QSpinBox, QLineEdit {
                font-size: 12pt;
            }
            QPushButton {
                font-size: 12pt;
            }
        """)
        
        # Create main layout with better spacing
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(12)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.setLayout(self.main_layout)
        
        # Create tab widget with improved styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: white;
                padding: 12px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px 4px 0 0;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
        """)
        
        # Install event filter on tab widget to handle clicks on tab content
        self.tab_widget.installEventFilter(self)
        
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_barlines_tab()
        self.create_endings_tab()
        self.create_directions_tab()
        
        # Status functionality removed - space redistributed to main content areas

        # After creating the barline tab widget (replace 'barline_tab_widget' with the actual variable name)
        self.barline_tab_widget.installEventFilter(self)

        # Remove the old action buttons and their frame
        # (Remove: self.create_action_buttons(self.main_layout))

        # Add the 'Set as Default for New Scores', 'Apply Changes', and 'Close' buttons in a single yellow area at the bottom
        button_row = QFrame()
        button_row.setFrameStyle(QFrame.Shape.StyledPanel)
        button_row.setStyleSheet("""
            QFrame {
                background-color: #ffc107;
                border: 1px solid #ffb300;
                border-radius: 6px;
                padding: 12px 16px 12px 16px;
                margin-top: 12px;
            }
        """)
        button_layout = QHBoxLayout(button_row)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 10, 10, 10)

        # Set as Default button
        self.set_default_button = QPushButton("Set as Default for New Scores")
        self.set_default_button.setMinimumHeight(32)
        self.set_default_button.setStyleSheet("""
            QPushButton {
                background-color: #ffe082;
                color: #212529;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #ffd54f;
            }
        """)
        self.set_default_button.clicked.connect(self.save_settings_as_default)
        button_layout.addWidget(self.set_default_button)

        # Apply Changes button
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.setMinimumHeight(32)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12pt;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_btn)

        # Close button
        self.close_btn = QPushButton("Close")
        self.close_btn.setMinimumHeight(32)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12pt;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)

        # Add the button row to the main layout at the bottom
        self.main_layout.addWidget(button_row, alignment=Qt.AlignmentFlag.AlignBottom)

        # Ensure the scroll area fills all available space above the button row
        # (If not already, set the scroll area to expand vertically)
        self.main_layout.setStretchFactor(self.tab_widget, 1)
        self.main_layout.setStretchFactor(button_row, 0)
    
    def save_settings_as_default(self):
        """Save current form settings to QSettings as defaults for new documents"""
        from PyQt6.QtCore import QSettings
        settings = QSettings()
        
        # Save measure numbers settings
        settings.setValue('notation/show_measure_numbers', self.show_measure_numbers.isChecked())
        settings.setValue('notation/measure_number_frequency', self.measure_number_frequency.currentText())
        settings.setValue('notation/measure_number_position', self.measure_number_position.currentText())
        settings.setValue('notation/measure_numbers_vertical', self.measure_numbers_vertical.currentText())
        settings.setValue('notation/measure_numbers_custom_interval', self.measure_numbers_custom_interval.value())
        settings.setValue('notation/measure_numbers_font_size', self.measure_numbers_font_size.value())
        settings.setValue('notation/measure_numbers_vertical_offset', self.measure_numbers_vertical_offset.value())
        settings.setValue('notation/measure_numbers_horizontal_offset', self.measure_numbers_horizontal_offset.value())
        
        # Save measure numbers font color - use actual color value, not fallback
        measure_numbers_color = getattr(self, 'measure_numbers_color_value', '#000000')
        if hasattr(self, 'measure_numbers_font_color'):
            # Extract color from button style if available
            style = self.measure_numbers_font_color.styleSheet()
            if 'background-color:' in style:
                import re
                match = re.search(r'background-color:\s*([^;]+)', style)
                if match:
                    measure_numbers_color = match.group(1).strip()
        settings.setValue('notation/measure_numbers_font_color', measure_numbers_color)
        
        # Save barline control settings
        max_measures = self.max_measures_per_system.value()
        settings.setValue('notation/max_measures_per_system', max_measures)
        settings.setValue('layout/default_measures_per_system', max_measures)  # For compatibility
        settings.setValue('notation/barline_numbering', self.barline_numbering.isChecked())
        settings.setValue('notation/barline_number_font_size', self.barline_number_font_size.value())
        
        # Save barline numbers font color - use actual color value, not fallback
        barline_numbers_color = getattr(self, 'barline_numbers_color_value', '#666666')
        if hasattr(self, 'barline_number_font_color'):
            # Extract color from button style if available
            style = self.barline_number_font_color.styleSheet()
            if 'background-color:' in style:
                import re
                match = re.search(r'background-color:\s*([^;]+)', style)
                if match:
                    barline_numbers_color = match.group(1).strip()
        settings.setValue('notation/barline_numbers_font_color', barline_numbers_color)
        
        # Layout settings are now handled by Preferences dialog
        
        print(f"FORM_WIDGET: Saved all settings to QSettings - measures per system: {max_measures}")
        
        # Force barline temporal bridge to reload preferences
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            if hasattr(staff_view, 'temporal_bridge'):
                staff_view.temporal_bridge.reload_layout_preferences()
                print("FORM_WIDGET: Forced temporal bridge to reload preferences")
        
        self.update_status("Defaults saved for new scores.")
    
    def create_barlines_tab(self):
        """Create the barlines tab with improved layout and organization"""
        tab = QWidget()
        self.barline_tab_widget = tab  # Save reference for event filtering
        layout = QVBoxLayout()
        layout.setSpacing(16)  # Reduced spacing
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Create scroll area for better handling of content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 7px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
        
        # Install event filter on scroll area to catch clicks
        scroll_area.installEventFilter(self)
        
        # Create scroll content widget
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)  # Reduced spacing between sections
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        
        # Install event filter on scroll content to catch clicks
        scroll_content.installEventFilter(self)
        
        # ===== BARLINE TYPE SELECTION =====
        type_group = QGroupBox("🎵 Barline Type")
        type_layout = QVBoxLayout()
        type_layout.setSpacing(6)  # Reduced spacing
        
        # Create button group for barline types with improved layout
        self.barline_button_group = QButtonGroup(self)
        self.barline_button_group.setExclusive(True)
        
        # Create radio buttons for each barline type with SMuFL symbols
        barline_types = [
            ("Single Barline", "single", "\uE030"),
            ("Double Barline", "double", "\uE031"),
            ("Final Barline", "final", "\uE032"),
            ("Dashed Barline", "dashed", "\uE036"),
            ("Repeat Start", "repeat_start", "\uE040"),
            ("Repeat End", "repeat_end", "\uE041"),
            ("Repeat Both", "repeat_both", "\uE042")
        ]
        
        # Create a more compact 3-column grid layout
        type_grid = QGridLayout()
        type_grid.setSpacing(4)  # Reduced spacing
        
        for i, (label, value, symbol) in enumerate(barline_types):
            radio = QRadioButton(f"{label}")
            radio.setProperty("barline_type", value)
            radio.setStyleSheet("""
                QRadioButton {
                    font-family: 'Segoe UI', 'Arial', sans-serif;
                    font-size: 8pt;  /* Smaller font */
                    padding: 4px 6px;  /* Reduced padding */
                    border-radius: 3px;
                }
                QRadioButton:hover {
                    background-color: #e3f2fd;
                }
            """)
            
            # Create symbol label
            symbol_label = QLabel(symbol)
            symbol_label.setStyleSheet("""
                QLabel {
                    font-family: 'Bravura', 'Arial Unicode MS', sans-serif;
                    font-size: 14px;  /* Slightly smaller */
                    color: #2c3e50;
                    padding: 3px;  /* Reduced padding */
                    border: 1px solid #e9ecef;
                    border-radius: 3px;
                    background-color: white;
                    min-width: 25px;  /* Smaller width */
                    text-align: center;
                }
            """)
            
            # Add to grid (3 columns for more compact layout)
            row = i // 3
            col = i % 3 * 2
            type_grid.addWidget(radio, row, col)
            type_grid.addWidget(symbol_label, row, col + 1)
            
            self.barline_button_group.addButton(radio)
        
        type_layout.addLayout(type_grid)
        
        # Repeat count (only shown for repeat barlines) - more compact
        repeat_count_layout = QHBoxLayout()
        repeat_count_layout.setSpacing(6)  # Reduced spacing
        repeat_count_label = QLabel("Repeat Count:")
        repeat_count_label.setStyleSheet("font-weight: bold; color: #495057; font-size: 8pt;")  # Smaller font
        self.repeat_count_spin = QSpinBox()
        self.repeat_count_spin.setRange(2, 8)
        self.repeat_count_spin.setValue(2)
        self.repeat_count_spin.setVisible(False)  # Initially hidden
        self.repeat_count_spin.setStyleSheet("""
            QSpinBox {
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 3px 6px;  /* Reduced padding */
                background-color: white;
                min-width: 50px;  /* Smaller width */
                font-size: 8pt;  /* Smaller font */
            }
        """)
        repeat_count_layout.addWidget(repeat_count_label)
        repeat_count_layout.addWidget(self.repeat_count_spin)
        repeat_count_layout.addStretch()
        type_layout.addLayout(repeat_count_layout)
        
        # Connect signals
        self.barline_button_group.buttonClicked.connect(self.on_barline_type_changed)
        
        # Set default selection to Single
        self.barline_button_group.buttons()[0].setChecked(True)
        
        type_group.setLayout(type_layout)
        scroll_layout.addWidget(type_group)
        
        # Install event filter on group box to catch clicks
        type_group.installEventFilter(self)

        # ===== MEASURE NUMBERS SETTINGS =====
        # UI removed per request (keep controls instantiated for internal logic)
        show_removed_sections = False
        measure_numbers_group = QGroupBox("🔢 Measure Numbers")
        measure_numbers_layout = QFormLayout(measure_numbers_group)
        measure_numbers_layout.setSpacing(8)  # Reduced spacing for more compact layout
        measure_numbers_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Enable measure numbers
        self.show_measure_numbers = QCheckBox("Show measure numbers")
        self.show_measure_numbers.setChecked(True)
        self.show_measure_numbers.setToolTip("Show measure numbers in this document")
        self.show_measure_numbers.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.show_measure_numbers.toggled.connect(self.update_score)
        measure_numbers_layout.addRow("", self.show_measure_numbers)
        
        # Frequency
        self.measure_number_frequency = QComboBox()
        self.measure_number_frequency.addItems(["None", "Every System", "Every Measure", "Every 2 Measures", "Every 5 Measures", "Every 10 Measures", "Custom Interval"])
        self.measure_number_frequency.setCurrentText("Every Measure")
        self.measure_number_frequency.setMinimumWidth(160)
        self.measure_number_frequency.setToolTip("How frequently to show measure numbers")
        self.measure_number_frequency.currentIndexChanged.connect(self.update_score)
        self.measure_number_frequency.currentIndexChanged.connect(self.on_measure_numbers_frequency_changed)
        measure_numbers_layout.addRow("Frequency:", self.measure_number_frequency)
        
        # Custom interval (initially hidden)
        self.measure_numbers_custom_interval = QSpinBox()
        self.measure_numbers_custom_interval.setRange(1, 100)
        self.measure_numbers_custom_interval.setValue(5)
        self.measure_numbers_custom_interval.setMinimumWidth(160)
        self.measure_numbers_custom_interval.setToolTip("Custom interval for measure numbers")
        self.measure_numbers_custom_interval.setVisible(False)
        self.measure_numbers_custom_interval.valueChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Custom Interval:", self.measure_numbers_custom_interval)
        
        # Position
        self.measure_number_position = QComboBox()
        self.measure_number_position.addItems(["Beginning", "Center", "End"])
        self.measure_number_position.setCurrentText("Center")
        self.measure_number_position.setMinimumWidth(160)
        self.measure_number_position.setToolTip("Position within the measure")
        self.measure_number_position.currentIndexChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Position:", self.measure_number_position)
        
        # Vertical position
        self.measure_numbers_vertical = QComboBox()
        self.measure_numbers_vertical.addItems(["Above Staff", "Above System", "Below Staff", "Below System"])
        self.measure_numbers_vertical.setCurrentText("Above System")
        self.measure_numbers_vertical.setMinimumWidth(160)
        self.measure_numbers_vertical.setToolTip("Vertical position relative to staff")
        self.measure_numbers_vertical.currentIndexChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Vertical Position:", self.measure_numbers_vertical)
        
        # Font size for measure numbers
        self.measure_numbers_font_size = QSpinBox()
        self.measure_numbers_font_size.setRange(6, 24)
        self.measure_numbers_font_size.setValue(10)
        self.measure_numbers_font_size.setSuffix(" pt")
        self.measure_numbers_font_size.setMinimumWidth(160)
        self.measure_numbers_font_size.setToolTip("Font size for measure numbers")
        self.measure_numbers_font_size.valueChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Font Size:", self.measure_numbers_font_size)
        
        # Vertical offset
        self.measure_numbers_vertical_offset = QSpinBox()
        self.measure_numbers_vertical_offset.setRange(-100, 50)
        self.measure_numbers_vertical_offset.setValue(-20)
        self.measure_numbers_vertical_offset.setSuffix(" px")
        self.measure_numbers_vertical_offset.setMinimumWidth(160)
        self.measure_numbers_vertical_offset.setToolTip("Fine vertical adjustment (negative = above)")
        self.measure_numbers_vertical_offset.valueChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Vertical Offset:", self.measure_numbers_vertical_offset)
        
        # Horizontal offset
        self.measure_numbers_horizontal_offset = QSpinBox()
        self.measure_numbers_horizontal_offset.setRange(-200, 100)
        self.measure_numbers_horizontal_offset.setValue(-34)
        self.measure_numbers_horizontal_offset.setSuffix(" px")
        self.measure_numbers_horizontal_offset.setMinimumWidth(160)
        self.measure_numbers_horizontal_offset.setToolTip("Fine horizontal adjustment")
        self.measure_numbers_horizontal_offset.valueChanged.connect(self.update_score)
        measure_numbers_layout.addRow("Horizontal Offset:", self.measure_numbers_horizontal_offset)
        
        # Font Color
        self.measure_numbers_font_color = QPushButton("Choose Color")
        self.measure_numbers_font_color.setMinimumWidth(160)
        self.measure_numbers_font_color.setStyleSheet("background-color: #000000; color: white; border-radius: 4px; padding: 6px;")
        self.measure_numbers_font_color.clicked.connect(lambda: self.choose_font_color('measure_numbers'))
        measure_numbers_layout.addRow("Font Color:", self.measure_numbers_font_color)
        
        measure_numbers_group.setLayout(measure_numbers_layout)
        if show_removed_sections:
            scroll_layout.addWidget(measure_numbers_group)
        else:
            # Keep widgets alive but hidden to satisfy existing logic without showing UI
            measure_numbers_group.setParent(self)
            measure_numbers_group.hide()
        
        # Install event filter on measure numbers group box to catch clicks
        measure_numbers_group.installEventFilter(self)

        # ===== BARLINE CONTROL SETTINGS =====
        # UI removed per request (keep controls instantiated for internal logic)
        barline_group = QGroupBox("🎼 Barline Control")
        barline_group.setMinimumHeight(240)  # Make the area taller
        barline_group.setStyleSheet("""
            QGroupBox {
                font-size: 15px; /* Larger font for group title */
                font-weight: bold;
                padding: 12px 8px 12px 8px; /* More padding for space */
                margin-top: 8px;
            }
            QGroupBox:title {
                subcontrol-origin: margin;
                left: 12px;
                top: 8px;
            }
            QLabel, QCheckBox, QSpinBox, QLineEdit {
                font-size: 14px; /* Larger font for controls */
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 0px;
            }
        """)
        barline_layout = QFormLayout(barline_group)
        barline_layout.setSpacing(28)  # More spacing for clarity
        barline_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Maximum measures per system
        self.max_measures_per_system = QSpinBox()
        self.max_measures_per_system.setRange(1, 16)
        self.max_measures_per_system.setValue(8)
        self.max_measures_per_system.setMinimumWidth(130)
        self.max_measures_per_system.setToolTip("Maximum number of measures per system")
        self.max_measures_per_system.valueChanged.connect(self.update_score)
        barline_layout.addRow("Max Measures/System:", self.max_measures_per_system)
        
        # Barline numbering
        self.barline_numbering = QCheckBox("Show barline numbers")
        self.barline_numbering.setChecked(False)
        self.barline_numbering.setToolTip("Show small numbers on barlines for debugging")
        self.barline_numbering.setStyleSheet("font-weight: bold; color: #2c3e50;")
        self.barline_numbering.toggled.connect(self.update_score)
        barline_layout.addRow("", self.barline_numbering)
        
        # Barline number font size
        self.barline_number_font_size = QSpinBox()
        self.barline_number_font_size.setRange(6, 16)
        self.barline_number_font_size.setValue(8)
        self.barline_number_font_size.setSuffix(" pt")
        self.barline_number_font_size.setMinimumWidth(130)
        self.barline_number_font_size.setToolTip("Font size for barline numbers")
        self.barline_number_font_size.valueChanged.connect(self.update_score)
        barline_layout.addRow("Barline Number Size:", self.barline_number_font_size)
        
        # Barline Number Color
        self.barline_number_font_color = QPushButton("Choose Color")
        self.barline_number_font_color.setMinimumWidth(160)
        self.barline_number_font_color.setStyleSheet("background-color: #666666; color: white; border-radius: 4px; padding: 6px;")
        self.barline_number_font_color.clicked.connect(lambda: self.choose_font_color('barline_numbers'))
        barline_layout.addRow("Barline Number Color:", self.barline_number_font_color)
        
        barline_group.setLayout(barline_layout)
        if show_removed_sections:
            scroll_layout.addWidget(barline_group)
        else:
            # Keep widgets alive but hidden to satisfy existing logic without showing UI
            barline_group.setParent(self)
            barline_group.hide()
        
        # Install event filter on barline group box to catch clicks
        barline_group.installEventFilter(self)

        # ===== BATCH OPERATIONS =====
        batch_group = QGroupBox("⚡ Batch Operations")
        batch_layout = QVBoxLayout()
        batch_layout.setSpacing(8)  # Reduced spacing for more compact layout
        
        # Batch measure insertion
        batch_measures_layout = QHBoxLayout()
        batch_measures_label = QLabel("Insert Measures:")
        batch_measures_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.batch_count_spin = QSpinBox()
        self.batch_count_spin.setRange(1, 20)
        self.batch_count_spin.setValue(4)
        self.batch_count_spin.setToolTip("Number of measures to insert in batch")
        self.batch_count_spin.setMinimumWidth(80)
        batch_measures_layout.addWidget(batch_measures_label)
        batch_measures_layout.addWidget(self.batch_count_spin)
        
        # Batch insertion position
        self.batch_position_combo = QComboBox()
        self.batch_position_combo.addItems(["At End", "At Beginning", "After Selected"])
        self.batch_position_combo.setToolTip("Where to insert the new measures")
        self.batch_position_combo.setMinimumWidth(120)
        batch_measures_layout.addWidget(self.batch_position_combo)
        
        # Batch insert button
        self.batch_insert_btn = QPushButton("Insert Batch")
        self.batch_insert_btn.setToolTip("Insert multiple measures at once")
        self.batch_insert_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.batch_insert_btn.clicked.connect(self.on_batch_insert_measures)
        batch_measures_layout.addWidget(self.batch_insert_btn)
        batch_measures_layout.addStretch()
        
        batch_layout.addLayout(batch_measures_layout)
        
        batch_group.setLayout(batch_layout)
        scroll_layout.addWidget(batch_group)
        
        # Install event filter on batch group box to catch clicks
        batch_group.installEventFilter(self)
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎵 Barlines")

    def on_barline_type_changed(self, button):
        """Handle barline type selection changes"""
        barline_type = button.property("barline_type")
        print(f"FORM_WIDGET: on_barline_type_changed called with type: {barline_type}")
        
        # CRITICAL FIX: Don't process during deselection
        if hasattr(self, '_deselecting_radio_buttons') and self._deselecting_radio_buttons:
            print(f"FORM_WIDGET: Deselecting radio buttons - NOT processing type change")
            return
        
        # Update preview
        self.update_barline_preview()
        
        # CRITICAL FIX: Only modify barlines when user intentionally clicks buttons
        # Don't modify when UI is syncing to show selected barline's current type
        if hasattr(self, '_syncing_ui_to_selection') and self._syncing_ui_to_selection:
            # UI is just syncing to show selected barline's current type
            print(f"FORM_WIDGET: Syncing UI to selection - NOT modifying barline")
            return
        
        print(f"FORM_WIDGET: User clicked button - proceeding to modify selected barlines")
        
        # Get all selected barlines from staff view
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            selected_barlines = self.main_window_ref.staff_view.get_selected_barlines()
            
            if selected_barlines:
                # User has selected barlines and chosen a new type - modify them
                print(f"FORM_WIDGET: Modifying {len(selected_barlines)} selected barlines to type '{barline_type}'")
                
                # Save state for undo
                if len(selected_barlines) == 1:
                    self.save_state(f"Change barline to {barline_type}")
                else:
                    self.save_state(f"Change {len(selected_barlines)} barlines to {barline_type}")
                
                for barline in selected_barlines:
                    old_type = getattr(barline, 'barline_type', 'single')
                    old_overlay = getattr(barline, 'overlay_type', None)
                    
                    # Implement overlay model: single base + overlay
                    if barline_type == 'single':
                        barline.barline_type = 'single'
                        barline.overlay_type = None
                    elif barline_type in ['final', 'double']:
                        barline.barline_type = 'single'
                        barline.overlay_type = barline_type
                    else:
                        # For repeat types, keep as barline_type for now
                        barline.barline_type = barline_type
                        barline.overlay_type = None
                    
                    print(f"FORM_WIDGET: Changed barline {getattr(barline, 'measure_number', 'unknown')} from '{old_type}' to '{barline_type}' (overlay: {getattr(barline, 'overlay_type', None)})")
                    
                    # Update repeat count for repeat barlines
                    if 'repeat' in barline_type:
                        if hasattr(barline, 'repeat_count'):
                            if not barline.repeat_count or barline.repeat_count < 2:
                                barline.repeat_count = self.repeat_count_spin.value()
                        else:
                            # Add repeat_count attribute if it doesn't exist
                            barline.repeat_count = self.repeat_count_spin.value()
                
                # Update the score
                self.update_score()
                self.update_status(f"Changed {len(selected_barlines)} barlines to {barline_type}")
            else:
                # No barlines selected - just prepare for creation
                print(f"FORM_WIDGET: No barlines selected - ready to create '{barline_type}' barlines")
                self.update_status(f"Selected '{barline_type}' barline type - click on staff to create")
        else:
            print(f"FORM_WIDGET: No staff view available")
        
        # Update repeat count visibility
        is_repeat = barline_type in ["repeat_start", "repeat_end", "repeat_both"]
        self.repeat_count_spin.setVisible(is_repeat)
    
    def modify_selected_barline(self, new_type):
        """Modify the selected barline with the new type"""
        if not self.selected_barline:
            return
            
        # Save state for undo
        self.save_state("Modify selected barline")
        
        # Update barline type
        self.selected_barline.barline_type = new_type
        
        # For repeat barlines, update repeat count and properties
        if new_type in ["repeat_start", "repeat_end", "repeat_both"]:
            self.selected_barline.repeat_count = self.repeat_count_spin.value()
            
            # Set repeat properties for proper rendering
            self.selected_barline.is_repeat_start = new_type in ["repeat_start", "repeat_both"]
            self.selected_barline.is_repeat_end = new_type in ["repeat_end", "repeat_both"]
        else:
            # Clear repeat properties for non-repeat barlines
            self.selected_barline.repeat_count = None
            self.selected_barline.is_repeat_start = False
            self.selected_barline.is_repeat_end = False
        
        # Update the score document if available
        if hasattr(self, 'document') and self.document and hasattr(self.document, 'measures'):
            if isinstance(self.document.measures, dict):
                if hasattr(self.selected_barline, 'measure_number'):
                    self.document.measures[self.selected_barline.measure_number] = self.selected_barline
            else:
                # Handle list format
                for i, measure in enumerate(self.document.measures):
                    if measure == self.selected_barline:
                        self.document.measures[i] = self.selected_barline
                        break
        
        # Update the staff view display
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            self.main_window_ref.staff_view.update()
        
        # Update status
        repeat_info = ""
        if new_type in ["repeat_start", "repeat_end", "repeat_both"]:
            repeat_info = f" (repeat {self.repeat_count_spin.value()}×)"
        self.update_status(f"Changed barline type to {new_type}{repeat_info}")
    
    def select_barline(self, barline):
        """Select a barline in the score"""
        if self.selected_barline:
            # Deselect previous barline
            self.selected_barline.selected = False
        
        self.selected_barline = barline
        if barline:
            barline.selected = True
            
            # Update UI to match selected barline
            for button in self.barline_button_group.buttons():
                if button.property("barline_type") == barline.barline_type:
                    button.setChecked(True)
                    break
            
            if barline.barline_type in ["repeat_start", "repeat_end", "repeat_both"]:
                self.repeat_count_spin.setValue(barline.repeat_count)
                self.repeat_count_spin.setVisible(True)
            
            self.update_status(f"Selected barline at measure {barline.measure_number}")
            
            # Note: Focus management and delete key handling is now entirely handled by StaffView
        else:
            self.update_status("No barline selected")
        
        # Update the score display
        self.update_score()
    
    def update_barline_preview(self):
        """Update barline type handling (preview area removed since symbols are next to type names)"""
        button = self.barline_button_group.checkedButton()
        if not button:
            return
            
        barline_type = button.property("barline_type")
        
        # Show/hide repeat count for repeat barlines
        is_repeat = barline_type in ["repeat_start", "repeat_end", "repeat_both"]
        if hasattr(self, 'repeat_count_spin'):
            self.repeat_count_spin.setVisible(is_repeat)
        
        # Note: Preview widget removed - SMuFL symbols are now displayed directly in radio button labels
    
    def create_endings_tab(self):
        """Create the endings tab with improved layout and styling"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Create scroll area for better handling of content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        
        # ===== REPEAT ENDINGS =====
        endings_group = QGroupBox("🔄 Repeat Endings")
        endings_layout = QVBoxLayout()
        endings_layout.setSpacing(12)
        
        # Ending type selection
        ending_type_layout = QHBoxLayout()
        ending_type_label = QLabel("Ending Type:")
        ending_type_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.ending_type_combo = QComboBox()
        self.ending_type_combo.addItems(["1.", "2.", "3.", "4.", "1.2.", "1.2.3.", "1.2.3.4."])
        self.ending_type_combo.setCurrentText("1.")
        self.ending_type_combo.setMinimumWidth(120)
        self.ending_type_combo.setToolTip("Type of repeat ending")
        ending_type_layout.addWidget(ending_type_label)
        ending_type_layout.addWidget(self.ending_type_combo)
        ending_type_layout.addStretch()
        endings_layout.addLayout(ending_type_layout)
        
        # Ending range
        ending_range_layout = QHBoxLayout()
        ending_range_label = QLabel("Measure Range:")
        ending_range_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.ending_start_spin = QSpinBox()
        self.ending_start_spin.setRange(1, 999)
        self.ending_start_spin.setValue(1)
        self.ending_start_spin.setMinimumWidth(80)
        self.ending_start_spin.setToolTip("Starting measure for this ending")
        
        range_separator = QLabel("to")
        range_separator.setStyleSheet("color: #6c757d; font-weight: bold;")
        
        self.ending_end_spin = QSpinBox()
        self.ending_end_spin.setRange(1, 999)
        self.ending_end_spin.setValue(4)
        self.ending_end_spin.setMinimumWidth(80)
        self.ending_end_spin.setToolTip("Ending measure for this ending")
        
        ending_range_layout.addWidget(ending_range_label)
        ending_range_layout.addWidget(self.ending_start_spin)
        ending_range_layout.addWidget(range_separator)
        ending_range_layout.addWidget(self.ending_end_spin)
        ending_range_layout.addStretch()
        endings_layout.addLayout(ending_range_layout)
        
        # Add ending button
        self.add_ending_btn = QPushButton("➕ Add Ending")
        self.add_ending_btn.setToolTip("Add a new repeat ending to the score")
        self.add_ending_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_ending_btn.clicked.connect(self.add_repeat_ending)
        endings_layout.addWidget(self.add_ending_btn)
        
        # Current endings list
        endings_list_label = QLabel("Current Endings:")
        endings_list_label.setStyleSheet("font-weight: bold; color: #495057; margin-top: 8px;")
        endings_layout.addWidget(endings_list_label)
        
        self.endings_list = QListWidget()
        self.endings_list.setMaximumHeight(150)
        self.endings_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        endings_layout.addWidget(self.endings_list)
        
        # Remove ending button
        self.remove_ending_btn = QPushButton("🗑️ Remove Selected")
        self.remove_ending_btn.setToolTip("Remove the selected ending")
        self.remove_ending_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.remove_ending_btn.clicked.connect(self.remove_repeat_ending)
        endings_layout.addWidget(self.remove_ending_btn)
        
        endings_group.setLayout(endings_layout)
        scroll_layout.addWidget(endings_group)
        
        # ===== ENDING STYLING =====
        styling_group = QGroupBox("🎨 Ending Styling")
        styling_layout = QFormLayout(styling_group)
        styling_layout.setSpacing(8)
        styling_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Font size
        self.ending_font_size = QSpinBox()
        self.ending_font_size.setRange(8, 24)
        self.ending_font_size.setValue(12)
        self.ending_font_size.setSuffix(" pt")
        self.ending_font_size.setMinimumWidth(120)
        self.ending_font_size.setToolTip("Font size for ending numbers")
        styling_layout.addRow("Font Size:", self.ending_font_size)
        
        # Vertical position
        self.ending_vertical_pos = QComboBox()
        self.ending_vertical_pos.addItems(["Above Staff", "Above System", "Below Staff", "Below System"])
        self.ending_vertical_pos.setCurrentText("Above System")
        self.ending_vertical_pos.setMinimumWidth(120)
        self.ending_vertical_pos.setToolTip("Vertical position of ending numbers")
        styling_layout.addRow("Vertical Position:", self.ending_vertical_pos)
        
        # Horizontal offset
        self.ending_horizontal_offset = QSpinBox()
        self.ending_horizontal_offset.setRange(-100, 100)
        self.ending_horizontal_offset.setValue(0)
        self.ending_horizontal_offset.setSuffix(" px")
        self.ending_horizontal_offset.setMinimumWidth(120)
        self.ending_horizontal_offset.setToolTip("Horizontal offset from barline")
        styling_layout.addRow("Horizontal Offset:", self.ending_horizontal_offset)
        
        # Vertical offset
        self.ending_vertical_offset = QSpinBox()
        self.ending_vertical_offset.setRange(-50, 50)
        self.ending_vertical_offset.setValue(-10)
        self.ending_vertical_offset.setSuffix(" px")
        self.ending_vertical_offset.setMinimumWidth(120)
        self.ending_vertical_offset.setToolTip("Vertical offset from position")
        styling_layout.addRow("Vertical Offset:", self.ending_vertical_offset)
        
        styling_group.setLayout(styling_layout)
        scroll_layout.addWidget(styling_group)
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🔄 Endings")
    
    def add_repeat_ending(self):
        """Add a new repeat ending to the score"""
        ending_type = self.ending_type_combo.currentText()
        start_measure = self.ending_start_spin.value()
        end_measure = self.ending_end_spin.value()
        
        # Add to list
        item_text = f"{ending_type} (measures {start_measure}-{end_measure})"
        self.endings_list.addItem(item_text)
        
        # Update status
        self.update_status(f"Added {ending_type} ending for measures {start_measure}-{end_measure}")
    
    def remove_repeat_ending(self):
        """Remove the selected ending"""
        current_item = self.endings_list.currentItem()
        if current_item:
            self.endings_list.takeItem(self.endings_list.row(current_item))
            self.update_status("Removed selected ending")
        else:
            self.update_status("No ending selected to remove")
    
    def create_directions_tab(self):
        """Create the directions tab with improved layout and styling"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Create scroll area for better handling of content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #f1f3f4;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #c1c1c1;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #a8a8a8;
            }
        """)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        scroll_layout.setContentsMargins(8, 8, 8, 8)
        
        # ===== MUSICAL DIRECTIONS =====
        directions_group = QGroupBox("🎼 Musical Directions")
        directions_layout = QVBoxLayout()
        directions_layout.setSpacing(12)
        
        # Direction type selection
        direction_type_layout = QHBoxLayout()
        direction_type_label = QLabel("Direction Type:")
        direction_type_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.direction_type_combo = QComboBox()
        self.direction_type_combo.addItems([
            "D.C.", "D.S.", "D.C. al Fine", "D.S. al Fine", 
            "D.C. al Coda", "D.S. al Coda", "To Coda", "Fine",
            "Segno", "Coda", "Repeat", "Volta"
        ])
        self.direction_type_combo.setCurrentText("D.C.")
        self.direction_type_combo.setMinimumWidth(140)
        self.direction_type_combo.setToolTip("Type of musical direction")
        direction_type_layout.addWidget(direction_type_label)
        direction_type_layout.addWidget(self.direction_type_combo)
        direction_type_layout.addStretch()
        directions_layout.addLayout(direction_type_layout)
        
        # Direction position
        direction_pos_layout = QHBoxLayout()
        direction_pos_label = QLabel("Position:")
        direction_pos_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.direction_pos_spin = QSpinBox()
        self.direction_pos_spin.setRange(1, 999)
        self.direction_pos_spin.setValue(1)
        self.direction_pos_spin.setMinimumWidth(80)
        self.direction_pos_spin.setToolTip("Measure where this direction appears")
        direction_pos_layout.addWidget(direction_pos_label)
        direction_pos_layout.addWidget(self.direction_pos_spin)
        direction_pos_layout.addStretch()
        directions_layout.addLayout(direction_pos_layout)
        
        # Custom text
        custom_text_layout = QHBoxLayout()
        custom_text_label = QLabel("Custom Text:")
        custom_text_label.setStyleSheet("font-weight: bold; color: #495057;")
        self.direction_text_edit = QLineEdit()
        self.direction_text_edit.setPlaceholderText("Optional custom text")
        self.direction_text_edit.setMinimumWidth(200)
        self.direction_text_edit.setToolTip("Custom text for the direction")
        custom_text_layout.addWidget(custom_text_label)
        custom_text_layout.addWidget(self.direction_text_edit)
        custom_text_layout.addStretch()
        directions_layout.addLayout(custom_text_layout)
        
        # Add direction button
        self.add_direction_btn = QPushButton("➕ Add Direction")
        self.add_direction_btn.setToolTip("Add a new musical direction to the score")
        self.add_direction_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.add_direction_btn.clicked.connect(self.add_musical_direction)
        directions_layout.addWidget(self.add_direction_btn)
        
        # Current directions list
        directions_list_label = QLabel("Current Directions:")
        directions_list_label.setStyleSheet("font-weight: bold; color: #495057; margin-top: 8px;")
        directions_layout.addWidget(directions_list_label)
        
        self.directions_list = QListWidget()
        self.directions_list.setMaximumHeight(150)
        self.directions_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 6px;
                border-bottom: 1px solid #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        directions_layout.addWidget(self.directions_list)
        
        # Remove direction button
        self.remove_direction_btn = QPushButton("🗑️ Remove Selected")
        self.remove_direction_btn.setToolTip("Remove the selected direction")
        self.remove_direction_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.remove_direction_btn.clicked.connect(self.remove_musical_direction)
        directions_layout.addWidget(self.remove_direction_btn)
        
        directions_group.setLayout(directions_layout)
        scroll_layout.addWidget(directions_group)
        
        # ===== DIRECTION STYLING =====
        direction_styling_group = QGroupBox("🎨 Direction Styling")
        direction_styling_layout = QFormLayout(direction_styling_group)
        direction_styling_layout.setSpacing(8)
        direction_styling_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Font size
        self.direction_font_size = QSpinBox()
        self.direction_font_size.setRange(8, 24)
        self.direction_font_size.setValue(12)
        self.direction_font_size.setSuffix(" pt")
        self.direction_font_size.setMinimumWidth(120)
        self.direction_font_size.setToolTip("Font size for direction text")
        direction_styling_layout.addRow("Font Size:", self.direction_font_size)
        
        # Font style
        self.direction_font_style = QComboBox()
        self.direction_font_style.addItems(["Normal", "Bold", "Italic", "Bold Italic"])
        self.direction_font_style.setCurrentText("Bold")
        self.direction_font_style.setMinimumWidth(120)
        self.direction_font_style.setToolTip("Font style for direction text")
        direction_styling_layout.addRow("Font Style:", self.direction_font_style)
        
        # Vertical position
        self.direction_vertical_pos = QComboBox()
        self.direction_vertical_pos.addItems(["Above Staff", "Above System", "Below Staff", "Below System"])
        self.direction_vertical_pos.setCurrentText("Above System")
        self.direction_vertical_pos.setMinimumWidth(120)
        self.direction_vertical_pos.setToolTip("Vertical position of direction text")
        direction_styling_layout.addRow("Vertical Position:", self.direction_vertical_pos)
        
        # Horizontal alignment
        self.direction_horizontal_align = QComboBox()
        self.direction_horizontal_align.addItems(["Left", "Center", "Right"])
        self.direction_horizontal_align.setCurrentText("Center")
        self.direction_horizontal_align.setMinimumWidth(120)
        self.direction_horizontal_align.setToolTip("Horizontal alignment of direction text")
        direction_styling_layout.addRow("Horizontal Alignment:", self.direction_horizontal_align)
        
        # Horizontal offset
        self.direction_horizontal_offset = QSpinBox()
        self.direction_horizontal_offset.setRange(-200, 200)
        self.direction_horizontal_offset.setValue(0)
        self.direction_horizontal_offset.setSuffix(" px")
        self.direction_horizontal_offset.setMinimumWidth(120)
        self.direction_horizontal_offset.setToolTip("Horizontal offset from measure")
        direction_styling_layout.addRow("Horizontal Offset:", self.direction_horizontal_offset)
        
        # Vertical offset
        self.direction_vertical_offset = QSpinBox()
        self.direction_vertical_offset.setRange(-100, 100)
        self.direction_vertical_offset.setValue(-20)
        self.direction_vertical_offset.setSuffix(" px")
        self.direction_vertical_offset.setMinimumWidth(120)
        self.direction_vertical_offset.setToolTip("Vertical offset from position")
        direction_styling_layout.addRow("Vertical Offset:", self.direction_vertical_offset)
        
        direction_styling_group.setLayout(direction_styling_layout)
        scroll_layout.addWidget(direction_styling_group)
        
        # ===== QUICK DIRECTIONS =====
        quick_group = QGroupBox("⚡ Quick Directions")
        quick_layout = QGridLayout()
        quick_layout.setSpacing(8)
        
        # Quick direction buttons
        quick_directions = [
            ("D.C.", "D.C."),
            ("D.S.", "D.S."),
            ("Fine", "Fine"),
            ("Coda", "Coda"),
            ("Segno", "Segno"),
            ("Repeat", "Repeat")
        ]
        
        for i, (text, value) in enumerate(quick_directions):
            btn = QPushButton(text)
            btn.setProperty("direction_value", value)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #6f42c1;
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #5a32a3;
                }
            """)
            btn.clicked.connect(lambda checked, v=value: self.quick_add_direction(v))
            quick_layout.addWidget(btn, i // 3, i % 3)
        
        quick_group.setLayout(quick_layout)
        scroll_layout.addWidget(quick_group)
        
        # Add stretch to push everything to the top
        scroll_layout.addStretch()
        
        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "🎼 Directions")
    
    def add_musical_direction(self):
        """Add a new musical direction to the score"""
        direction_type = self.direction_type_combo.currentText()
        position = self.direction_pos_spin.value()
        custom_text = self.direction_text_edit.text()
        
        # Add to list
        if custom_text:
            item_text = f"{direction_type} at measure {position} ({custom_text})"
        else:
            item_text = f"{direction_type} at measure {position}"
        self.directions_list.addItem(item_text)
        
        # Clear text field
        self.direction_text_edit.clear()
        
        # Update status
        self.update_status(f"Added {direction_type} at measure {position}")
    
    def remove_musical_direction(self):
        """Remove the selected direction"""
        current_item = self.directions_list.currentItem()
        if current_item:
            self.directions_list.takeItem(self.directions_list.row(current_item))
            self.update_status("Removed selected direction")
        else:
            self.update_status("No direction selected to remove")
    
    def quick_add_direction(self, direction_type):
        """Quick add a direction by setting the combo box and adding it"""
        # Set the combo box to the selected direction
        index = self.direction_type_combo.findText(direction_type)
        if index >= 0:
            self.direction_type_combo.setCurrentIndex(index)
        
        # Add the direction
        self.add_musical_direction()
    
    def create_action_buttons(self, layout):
        """Create the action buttons at the bottom"""
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        
        button_layout = QHBoxLayout(button_frame)
        
        # Note: Undo/Redo buttons removed - functionality available via Ctrl+Z and Ctrl+Y keyboard shortcuts
        
        button_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # Apply and Close buttons
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.apply_btn.clicked.connect(self.apply_changes)
        button_layout.addWidget(self.apply_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addWidget(button_frame)
    
    def connect_signals(self):
        """Connect all widget signals to their handlers"""
        # Barline type changes
        if hasattr(self, 'barline_button_group'):
            self.barline_button_group.buttonClicked.connect(self.on_barline_type_changed)
        
        # Repeat count changes
        if hasattr(self, 'repeat_count_spin'):
            self.repeat_count_spin.valueChanged.connect(self.on_property_changed)
        
        # Layout changes
        if hasattr(self, 'measures_per_system_spin'):
            self.measures_per_system_spin.valueChanged.connect(self.on_property_changed)
        # Layout settings (auto_justify_check, dynamic_width_check) are now handled by Preferences dialog
        
        # Connect to staff view for barline creation (if available)
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            if hasattr(self.main_window_ref.staff_view, 'barline_created'):
                self.main_window_ref.staff_view.barline_created.connect(self.on_barline_created)
            if hasattr(self.main_window_ref.staff_view, 'barline_selected'):
                self.main_window_ref.staff_view.barline_selected.connect(self.on_barline_selected)
            if hasattr(self.main_window_ref.staff_view, 'barline_removed'):
                self.main_window_ref.staff_view.barline_removed.connect(self.on_barline_removed)
        
        # Ending changes
        if hasattr(self, 'ending_combo'):
            self.ending_combo.currentIndexChanged.connect(self.on_property_changed)
        
        # Direction changes
        if hasattr(self, 'direction_combo'):
            self.direction_combo.currentIndexChanged.connect(self.on_property_changed)
        
        # Text edits
        if hasattr(self, 'direction_text_edit'):
            self.direction_text_edit.textChanged.connect(self.on_property_changed)
        if hasattr(self, 'ending_text_edit'):
            self.ending_text_edit.textChanged.connect(self.on_property_changed)
    
    def on_barline_selected(self, barline):
        """Handle barline selection from staff view"""
        print(f"FORM_WIDGET: on_barline_selected called with barline type: {getattr(barline, 'barline_type', 'unknown')}")
        
        # Update the selected barline
        self.selected_barline = barline
        
        # Update UI to match the selected barline's properties
        if hasattr(barline, 'barline_type'):
            # Set sync flag to prevent modification during UI update
            self._syncing_ui_to_selection = True
            print(f"FORM_WIDGET: Setting sync flag to True, updating UI to match barline type: {barline.barline_type}")
            
            # Find and check the corresponding radio button
            for button in self.barline_button_group.buttons():
                if button.property("barline_type") == barline.barline_type:
                    # Temporarily disconnect signal to avoid recursion
                    self.barline_button_group.buttonClicked.disconnect()
                    button.setChecked(True)
                    # Reconnect signal
                    self.barline_button_group.buttonClicked.connect(self.on_barline_type_changed)
                    print(f"FORM_WIDGET: Set button {barline.barline_type} to checked")
                    break
            
            # Clear sync flag after UI update
            self._syncing_ui_to_selection = False
            print(f"FORM_WIDGET: Cleared sync flag")
        
        # Update preview
        self.update_barline_preview()
        
        # Show repeat count if it's a repeat barline
        if hasattr(barline, 'barline_type') and 'repeat' in barline.barline_type:
            self.repeat_count_spin.show()
        else:
            self.repeat_count_spin.hide()
    
    def on_barline_removed(self, barline):
        """Handle barline removal from staff view"""
        # Save state for undo
        self.save_state("Remove barline")
        
        # Remove from our internal collection
        if hasattr(barline, 'measure_number') and barline.measure_number in self.measures:
            del self.measures[barline.measure_number]
        
        # Clear selection if this was the selected barline
        if self.selected_barline == barline:
            self.selected_barline = None
        
        # Update UI
        self.update_undo_redo_buttons()
        
        # Update status
        self.update_status(f"Removed barline at measure {getattr(barline, 'measure_number', 'unknown')}")
    
    def initialize_default_measures(self):
        """Initialize form widget measures collection from document"""
        # CRITICAL FIX: Don't create measures - just sync with existing document measures
        
        # Safety check: ensure document exists
        if not hasattr(self, 'document') or self.document is None:
            print("FORM_WIDGET: Warning - No document available during initialization")
            self.measures = {}
            return
        
        # Sync our internal measures collection with document measures
        if hasattr(self.document, 'measures') and self.document.measures:
            if isinstance(self.document.measures, dict):
                # Copy existing measures from document
                self.measures = self.document.measures.copy()
                print(f"FORM_WIDGET: Synced {len(self.measures)} measures from document")
            else:
                # Convert list to dict format for internal use
                self.measures = {}
                for i, measure in enumerate(self.document.measures):
                    measure_num = getattr(measure, 'measure_number', i+1)
                    self.measures[measure_num] = measure
                print(f"FORM_WIDGET: Converted and synced {len(self.measures)} measures from document list")
        else:
            # No measures in document yet - initialize empty
            self.measures = {}
            print("FORM_WIDGET: No measures found in document - initialized empty collection")
        
        # Save initial state for undo
        if hasattr(self, 'save_state'):
            self.save_state("Initialize form widget")
    
    # Core functionality methods
    
    def save_state(self, message):
        """Save current state for undo functionality - delegates to document"""
        # Don't sync during initialization to avoid overwriting document data
        if message == "Initialize form widget":
            print(f"FORM_WIDGET: Skipping sync during initialization - {message}")
            # Just save state without syncing
            if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
                if hasattr(self.main_window_ref.staff_view, 'document'):
                    document = self.main_window_ref.staff_view.document
                    if hasattr(document, 'save_state'):
                        document.save_state(message)
                        print(f"FORM_WIDGET: Delegated save_state to document (no sync) - {message}")
                        return
        
        # Save state in the document instead of locally  
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            if hasattr(self.main_window_ref.staff_view, 'document'):
                document = self.main_window_ref.staff_view.document
                if hasattr(document, 'save_state'):
                    # CRITICAL FIX: Don't sync TO document during barline creation
                    # Instead, sync FROM document to form widget to pick up new measures
                    if "Created barline" in message:
                        # After barline creation, sync FROM document TO form widget
                        self._sync_from_document_to_form_widget()
                        print(f"FORM_WIDGET: Synced FROM document to form widget after barline creation")
                    else:
                        # For other operations, sync TO document as before
                        self._sync_measures_to_document()
                    
                    # Save state with operation description
                    document.save_state(message)
                    print(f"FORM_WIDGET: Delegated save_state to document - {message}")
                    # Update status
                    self.update_status(message)
                    return
        
        # Fallback: show warning if document is not available
        print(f"FORM_WIDGET: Warning - Could not save state to document, no document available - {message}")
        self.update_status(f"Warning: {message} (no undo available)")
    
    def _sync_measures_to_document(self):
        """Sync FormWidget measures to the document"""
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            if hasattr(self.main_window_ref.staff_view, 'document'):
                document = self.main_window_ref.staff_view.document
                
                # Convert FormWidget measures to document format
                document_measures = []
                graphical_dashed_barlines = []
                
                # Sort measures by measure number/id
                sorted_keys = sorted([k for k in self.measures.keys() if isinstance(k, int)])
                sorted_keys.extend([k for k in self.measures.keys() if not isinstance(k, int)])
                
                for key in sorted_keys:
                    measure = self.measures[key]
                    # Check for graphical dashed barlines using the new attribute
                    if hasattr(measure, 'is_graphical_dashed') and measure.is_graphical_dashed:
                        # This is a graphical dashed barline
                        graphical_dashed_barlines.append(measure)
                    elif hasattr(measure, 'is_dashed') and measure.is_dashed:
                        # Legacy check for dashed barlines
                        graphical_dashed_barlines.append(measure)
                    elif hasattr(measure, 'barline_type') and measure.barline_type == 'dashed' and isinstance(key, str):
                        # Dashed barline identified by type and string key
                        graphical_dashed_barlines.append(measure)
                    else:
                        # This is a regular measure
                        document_measures.append(measure)
                
                # Update document
                document.measures = document_measures
                if not hasattr(document, 'graphical_dashed_barlines'):
                    document.graphical_dashed_barlines = []
                document.graphical_dashed_barlines = graphical_dashed_barlines
                
                # Note: Removed coordinate fixing here as it was interfering with barline creation
                # The temporal bridge handles coordinate management during barline creation
                
                print(f"FORM_WIDGET: Synced {len(document_measures)} measures and {len(graphical_dashed_barlines)} dashed barlines to document")
    
    def _sync_from_document_to_form_widget(self):
        """Sync measures FROM document TO form widget - used after barline creation"""
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            if hasattr(self.main_window_ref.staff_view, 'document'):
                document = self.main_window_ref.staff_view.document
                
                # Clear current measures
                self.measures.clear()
                
                # Get measures from document
                document_measures = getattr(document, 'measures', [])
                if isinstance(document_measures, dict):
                    # CRITICAL FIX: Use document's dictionary keys instead of measure.measure_number
                    # This ensures we use the corrected measure numbering from temporal bridge
                    for measure_key, measure in document_measures.items():
                        if isinstance(measure_key, int):
                            # Use the document's key (which is the correct measure number)
                            # and update the measure object to match
                            measure.measure_number = measure_key
                            self.measures[measure_key] = measure
                            print(f"FORM_WIDGET: Synced measure #{measure_key} from document")
                else:
                    # Handle list format - use indices as measure numbers
                    for i, measure in enumerate(document_measures):
                        measure_num = i + 1
                        measure.measure_number = measure_num
                        self.measures[measure_num] = measure
                        print(f"FORM_WIDGET: Synced measure #{measure_num} from document list")
                
                # Add graphical dashed barlines if they exist
                graphical_dashed_barlines = getattr(document, 'graphical_dashed_barlines', [])
                for i, dashed_barline in enumerate(graphical_dashed_barlines):
                    # Use string keys for dashed barlines
                    key = f"dashed_{i}"
                    self.measures[key] = dashed_barline
                
                print(f"FORM_WIDGET: Synced {len(document_measures)} measures and {len(graphical_dashed_barlines)} dashed barlines FROM document")
    
    def restore_state(self, state):
        """Restore state from undo/redo"""
        # Restore measures
        self.measures.clear()
        for k, v in state['measures'].items():
            try:
                # Handle both integer and string keys (for dashed barlines)
                key = int(k) if k.isdigit() else k
                self.measures[key] = MeasureObject.from_dict(v)
            except (ValueError, AttributeError):
                # Skip invalid measures
                continue
        
        # Restore other properties
        self.current_measure_number = state.get('current_measure_number', 1)
        self.measures_per_system = state.get('measures_per_system', 4)
        self.auto_justify = state.get('auto_justify', True)
        self.dynamic_width = state.get('dynamic_width', True)
        
        # Update UI controls
        if hasattr(self, 'measures_per_system_spin'):
            self.measures_per_system_spin.setValue(self.measures_per_system)
        if hasattr(self, 'auto_justify_check'):
            self.auto_justify_check.setChecked(self.auto_justify)
        if hasattr(self, 'dynamic_width_check'):
            self.dynamic_width_check.setChecked(self.dynamic_width)
        
        # Restore selected barline
        selected_barline_id = state.get('selected_barline_id')
        if selected_barline_id and selected_barline_id in self.measures:
            self.select_barline(self.measures[selected_barline_id])
        else:
            self.select_barline(None)
    
    def get_current_state(self):
        """Get the current state for undo/redo"""
        return {
            'measures': {k: v.to_dict() for k, v in self.measures.items() if hasattr(v, 'to_dict')},
            'current_measure_number': self.current_measure_number,
            'measures_per_system': self.measures_per_system,
            'auto_justify': self.auto_justify,
            'dynamic_width': self.dynamic_width,
            'selected_barline_id': getattr(self.selected_barline, 'measure_number', None) if self.selected_barline else None
        }
    
    def update_undo_redo_buttons(self):
        """Update the enabled state of undo/redo buttons - now obsolete since buttons are removed"""
        # Note: Undo/redo buttons have been removed - functionality is now only available via keyboard shortcuts
        pass
    
    def update_status(self, message):
        """Update status label (no-op since status area was removed)"""
        # Status functionality removed - space redistributed to main content areas
        pass
    
    def update_measure_selector_range(self):
        """Update the range of available measures"""
        if not self.measures:
            return
            
        # Only consider integer keys (regular measures) for max calculation
        integer_keys = [k for k in self.measures.keys() if isinstance(k, int)]
        max_measure = max(integer_keys) if integer_keys else 1
        
        # Update status instead of measure selector
        self.update_status(f"Score has {max_measure} measures")
    
    def select_measure(self, measure_number):
        """Select a measure for editing"""
        if measure_number in self.measures:
            self.current_measure_number = measure_number
            self.update_properties_display()
            self.update_status(f"Selected measure {measure_number}")
        else:
            self.update_status(f"Measure {measure_number} not found")
    
    def update_properties_display(self):
        """Update the display of properties for the current measure"""
        if not self.current_measure:
            return
            
        measure = self.current_measure
        
        # Update barline type selection
        if hasattr(self, 'barline_button_group'):
            for button in self.barline_button_group.buttons():
                if button.property("barline_type") == measure.barline_type:
                    button.setChecked(True)
                    break
        
        # Update repeat count
        if hasattr(self, 'repeat_count_spin') and hasattr(measure, 'repeat_count'):
            self.repeat_count_spin.setValue(measure.repeat_count or 2)
        
        # Show/hide repeat count based on barline type
        if hasattr(self, 'repeat_count_spin'):
            is_repeat = measure.barline_type in ["repeat_start", "repeat_end", "repeat_both"]
            self.repeat_count_spin.setVisible(is_repeat)
        
        # Update layout settings
        if hasattr(self, 'force_break_check') and hasattr(measure, 'force_break'):
            self.force_break_check.setChecked(measure.force_break or False)
            
        if hasattr(self, 'custom_width_check') and hasattr(self, 'custom_width_spin'):
            if self.custom_width_check.isChecked():
                measure.custom_width = self.custom_width_spin.value()
            else:
                measure.custom_width = None
        
        # Update repeat count for repeat barlines
        if hasattr(self, 'repeat_count_spin') and measure.barline_type in ["repeat_start", "repeat_end", "repeat_both"]:
            measure.repeat_count = self.repeat_count_spin.value()
            
            # Update repeat properties
            measure.is_repeat_start = measure.barline_type in ["repeat_start", "repeat_both"]
            measure.is_repeat_end = measure.barline_type in ["repeat_end", "repeat_both"]
            
            # Update the score document
            if self.document and hasattr(self.document, 'measures'):
                if isinstance(self.document.measures, dict):
                    if hasattr(measure, 'measure_number'):
                        self.document.measures[measure.measure_number] = measure
                else:
                    # Handle list format
                    for i, doc_measure in enumerate(self.document.measures):
                        if doc_measure == measure:
                            self.document.measures[i] = measure
                            break
            
            # Update staff view
            if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
                self.main_window_ref.staff_view.update()
        
        # Update score layout
        self.update_score_layout()
        
        # Update display
        self.update_barline_preview()
        self.update_undo_redo_buttons()
        
        # Update status
        self.update_status("Properties updated")
    
    # Event handlers
    
    def on_barline_created(self, measure):
        """Handle barline creation from staff view"""
        # Add the measure to our internal collection
        self.measures[measure.measure_number] = measure
        
        # Update the display
        self.update_status(f"Created barline at measure {measure.measure_number}")
        
        # Save state for undo
        self.save_state(f"Created barline at measure {measure.measure_number}")
        
        # Update any UI elements that depend on the measure count
        self.update_undo_redo_buttons()
    
    # Note: Undo/Redo operations are now handled by the document system via keyboard shortcuts
    # The FormWidget no longer has its own undo/redo methods
    
    def get_selected_barline_type(self):
        """Get the currently selected barline type"""
        selected_button = self.barline_button_group.checkedButton()
        if selected_button:
            return selected_button.property("barline_type")
        return None  # Return None when no radio button is selected (after deselection)
    
    def create_barline_at_position(self, x_position: float):
        """Create a barline at the specified position with clean first-click logic"""
        # Get current barline type
        barline_type = self.get_selected_barline_type()
        
        # ONOTE SPECIFICATION: No barline type selected means no action
        if barline_type is None:
            print("FORM_WIDGET: No barline type selected - select a barline type first")
            self.update_status("No barline type selected - choose Single or Dashed to create barlines")
            return None
        
        # RESTRUCTURE: Detect first click on empty document
        is_first_click = not self.document.measures
        
        if is_first_click:
            print("FORM_WIDGET: First click detected - creating first barline at staff end")
            return self.create_first_barline()
        
        # RESTRICTION: Only allow direct creation of single and dashed barlines
        # All other barline types can only modify existing selected barlines
        if barline_type not in ["single", "dashed"]:
            print(f"FORM_WIDGET: Cannot directly create {barline_type} barline. Only single and dashed barlines can be inserted directly.")
            print(f"FORM_WIDGET: To use {barline_type}, first select an existing barline, then choose the type from the dialog.")
            self.update_status(f"Cannot create {barline_type} directly - select an existing barline first")
            return None
        
        # Dashed barlines don't add measures
        if barline_type == "dashed":
            return self.add_dashed_barline(x_position)
        
        # SUBSEQUENT CLICKS: Use existing shuffle system
        return self.create_subsequent_barline(x_position, barline_type)
    
    def create_first_barline(self):
        """RESTRUCTURE: Create the first barline at staff end"""
        print("FORM_WIDGET: Creating first barline at staff end")
        
        # CRITICAL FIX: Get staff end position dynamically instead of hardcoding 1136px
        STAFF_END_X = self._get_staff_end_position()
        print(f"FORM_WIDGET: Calculated staff end position: {STAFF_END_X}")
        
        # ONOTE SPECIFICATION: First barline is always 'single' type per specification
        # "Initially a 'single' bar line type - radio button should be preselected by default"
        barline_type = 'single'
        
        # Create measure #1 spanning full staff width
        measure = MeasureObject(
            measure_number=1,  # First parameter
            end_x=STAFF_END_X,  # Second parameter (dynamic)
            document=self.document,  # Third parameter
            barline_type=barline_type  # Fourth parameter - always single for first barline
        )
        
        # Verify the end_x was set correctly
        print(f"FORM_WIDGET: Created measure with end_x={measure.end_x} (expected {STAFF_END_X})")
        
        # Set position to span from leftmost note position to staff end
        LEFTMOST_NOTE_X = 265.0  # From temporal bridge constants
        measure.x_position = LEFTMOST_NOTE_X
        measure.width = STAFF_END_X - LEFTMOST_NOTE_X  # Full staff width
        
        # Force set end_x to ensure it's correct
        measure.end_x = STAFF_END_X
        print(f"FORM_WIDGET: Forced end_x to {measure.end_x}")
        
        # Save state for undo
        self.save_state("Created first barline at staff end")
        
        # Add to document measures
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        self.document.measures[1] = measure
        
        # Add to form widget measures
        self.measures[1] = measure
        
        print(f"FORM_WIDGET: First measure created - spans from x={LEFTMOST_NOTE_X} to x={STAFF_END_X}")
        print(f"FORM_WIDGET: First barline positioned at x={STAFF_END_X} (staff end) with type='{barline_type}'")
        
        # Update temporal bridge if available
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            self.temporal_bridge.document = self.document
        
        # Update layout and UI
        self.update_score_layout()
        self.update_measure_selector_range()
        
        # Force UI update
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            self.main_window_ref.staff_view.update()
        
        return measure

    def _get_staff_end_position(self):
        """Get the staff end position dynamically using the proportional system"""
        # Use the same dynamic system as the temporal bridge for consistency
        if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
            return self.temporal_bridge.get_current_end_barline_x()
        
        # Try to get from document renderer
        if hasattr(self, 'main_window_ref') and self.main_window_ref:
            if hasattr(self.main_window_ref.staff_view) and self.main_window_ref.staff_view:
                if hasattr(self.main_window_ref.staff_view, 'renderer'):
                    renderer = self.main_window_ref.staff_view.renderer
                    page_width = getattr(renderer, 'page_width', 800)
                    margins = getattr(renderer, 'margins', {'right': 50})
                    right_margin = margins.get('right', 50)
                    return float(page_width - right_margin)
        
        # Fallback calculation
        default_page_width = 800
        default_right_margin = 50
        return float(default_page_width - default_right_margin)
    
    def create_subsequent_barline(self, x_position: float, barline_type: str):
        """RESTRUCTURE: Create subsequent barlines using simplified shuffle system"""
        print(f"FORM_WIDGET: Creating subsequent barline at x={x_position} (shuffle insertion)")
        
        # CONSTRAINT: Check measures per system limit before creating
        current_count = len([k for k in self.measures.keys() if isinstance(k, int)])
        max_measures = self.measures_per_system_spin.value()
        if current_count >= max_measures:
            print(f"CONSTRAINT: Cannot create more barlines - already at maximum {max_measures} measures per system")
            self.update_status(f"Cannot create more barlines - already at maximum {max_measures} measures per system")
            return None
        
        # For subsequent clicks, implement simplified shuffle logic
        measure_num = len([k for k in self.measures.keys() if isinstance(k, int)]) + 1
        
        # Create new measure with proper positioning
        measure = MeasureObject(
            measure_number=measure_num,
            end_x=x_position,  # Barline at clicked position
            document=self.document,
            barline_type=barline_type
        )
        
        # Calculate start position based on previous measure
        if measure_num > 1:
            # Get the previous measure to determine start position
            prev_measure_num = measure_num - 1
            if prev_measure_num in self.measures:
                prev_measure = self.measures[prev_measure_num]
                measure.x_position = prev_measure.x_position  # Start where previous measure started
                
                # Recalculate previous measure's width to make room for this one
                # This implements simplified shuffle: divide space equally
                total_width = prev_measure.width  # Total space to divide
                equal_width = total_width / 2  # Divide equally between two measures
                
                # Update previous measure
                prev_measure.width = equal_width
                prev_measure.end_x = prev_measure.x_position + equal_width
                
                # Set current measure position
                measure.x_position = prev_measure.end_x
                measure.width = equal_width
                measure.end_x = measure.x_position + measure.width
                
                print(f"FORM_WIDGET: Shuffled measures - prev: {prev_measure.x_position:.1f}-{prev_measure.end_x:.1f}, new: {measure.x_position:.1f}-{measure.end_x:.1f}")
            else:
                # Fallback if previous measure not found
                measure.x_position = 265.0
                measure.width = x_position - 265.0
        else:
            # This shouldn't happen since measure 1 already exists
            measure.x_position = 265.0
            measure.width = x_position - 265.0
        
        # Save state for undo
        self.save_state(f"Created {barline_type} barline at measure {measure_num}")
        
        # Add to both document and form widget measures
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        self.document.measures[measure_num] = measure
        self.measures[measure_num] = measure
        
        print(f"FORM_WIDGET: Added measure {measure_num} to document - now has {len(self.document.measures)} measures")
        
        # Update layout (but preserve first measure positioning)
        self.update_score_layout()
        self.update_measure_selector_range()
        
        # Force UI update
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            self.main_window_ref.staff_view.update()
        
        return measure
    
    def apply_changes(self):
        """Apply all changes and notify document"""
        self.emit_structure_changed()
        self.update_status("Changes applied to document")
    
    def emit_measure_modified(self):
        """Emit measure modified signal"""
        if self.current_measure_number in self.measures:
            measure = self.measures[self.current_measure_number]
            self.measure_modified.emit(self.current_measure_number, measure.to_dict())
    
    def emit_structure_changed(self):
        """Emit structure changed signal"""
        measures_list = [self.measures[k].to_dict() for k in sorted(self.measures.keys())]
        self.structure_changed.emit(measures_list)
    
    # Window event handlers
    
    def showEvent(self, event):
        """Handle show event to ensure proper initialization"""
        super().showEvent(event)
        
        # Reload settings to ensure we have the latest from QSettings
        self.load_settings_from_document()
        
        # Enable staff interaction for barline creation
        self.enable_staff_interaction()
        
        # Integrate with temporal bridge for rhythm input
        self._integrate_temporal_bridge()
        
        # Update status
        self.update_status("Musical Form widget ready - select barline type and click on staff")
        
        print("FORM_WIDGET: Widget shown and initialized")
    
    def hideEvent(self, event):
        """Handle widget hide event"""
        super().hideEvent(event)
        
        # Disable staff interaction when form widget is hidden
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            self.main_window_ref.staff_view.set_barline_creation_enabled(False)
    
    # Public interface methods
    
    def set_document(self, document):
        """Set the document to work with"""
        self.document = document
        # Only sync if we're not in the middle of initialization
        if hasattr(self, '_initialization_complete') and self._initialization_complete:
            # Sync with both regular measures and dashed barlines
            if hasattr(document, 'measures'):
                self.sync_with_document_measures(document.measures)
            else:
                # No measures, but still sync dashed barlines if they exist
                self.sync_with_document_measures([])
        else:
            print("FORM_WIDGET: Skipping sync during initialization to preserve document data")
    
    def sync_with_document_measures(self, document_measures):
        """Sync with measures from document, including dashed barlines"""
        # Don't clear existing measures - preserve them and add new ones from document
        # This prevents losing existing barlines when Form Widget opens
        
        # Sync regular measures from document
        for i, doc_measure in enumerate(document_measures):
            if hasattr(doc_measure, 'to_dict'):
                measure_dict = doc_measure.to_dict()
                measure = MeasureObject.from_dict(measure_dict)
            else:
                # Create from basic properties
                measure = MeasureObject(i + 1)
                if hasattr(doc_measure, 'barline_type'):
                    measure.barline_type = doc_measure.barline_type
                if hasattr(doc_measure, 'end_x'):
                    measure.end_x = doc_measure.end_x
                
            self.measures[measure.measure_number] = measure
        
        # IMPORTANT: Also sync graphical dashed barlines from document
        if hasattr(self.document, 'graphical_dashed_barlines') and self.document.graphical_dashed_barlines:
            print(f"FORM_WIDGET: Syncing {len(self.document.graphical_dashed_barlines)} dashed barlines from document")
            
            for i, dashed_barline in enumerate(self.document.graphical_dashed_barlines):
                if hasattr(dashed_barline, 'to_dict'):
                    measure_dict = dashed_barline.to_dict()
                    measure = MeasureObject.from_dict(measure_dict)
                else:
                    # Create from basic properties
                    measure = MeasureObject()
                    if hasattr(dashed_barline, 'barline_type'):
                        measure.barline_type = dashed_barline.barline_type
                    if hasattr(dashed_barline, 'end_x'):
                        measure.end_x = dashed_barline.end_x
                    elif hasattr(dashed_barline, 'x_position'):
                        measure.end_x = dashed_barline.x_position
                
                # Mark as graphical dashed barline and use unique key
                measure.is_graphical_dashed = True
                dashed_key = f"dashed_{i}"
                self.measures[dashed_key] = measure
                print(f"FORM_WIDGET: Added dashed barline at x={measure.end_x} with key '{dashed_key}'")
        
        print(f"FORM_WIDGET: Synced {len(self.measures)} total barlines ({len(document_measures)} regular + {len(getattr(self.document, 'graphical_dashed_barlines', []))} dashed)")
        
        self.update_measure_selector_range()
        if self.measures:
            # Find first regular measure (not dashed) for selection
            regular_measures = [k for k in self.measures.keys() if isinstance(k, int)]
            if regular_measures:
                self.select_measure(min(regular_measures))
    
    def update_score(self):
        """Update the score display and save settings to document"""
        # Save current settings to document
        self.save_settings_to_document()
        
        # Update score layout
        self.update_score_layout()
        
        # Update the staff view if available
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            
            # CRITICAL FIX: Reload renderer settings after saving to document
            if hasattr(staff_view, 'renderer') and staff_view.renderer:
                # Force the renderer to reload notation settings with document precedence
                staff_view.renderer.load_notation_settings()
                print("FORM_WIDGET: Reloaded renderer notation settings")
            
            # CRITICAL FIX: Also refresh measure number manager if available
            if hasattr(staff_view, 'renderer') and hasattr(staff_view.renderer, 'measure_number_manager'):
                if staff_view.renderer.measure_number_manager:
                    staff_view.renderer.measure_number_manager.refresh_settings()
                    print("FORM_WIDGET: Refreshed measure number manager settings")
            
            # Force a repaint
            staff_view.update()
        
        # Update measure range
        self.update_measure_selector_range()
        
        # Update status
        self.update_status("Score updated")
    
    def save_settings_to_document(self):
        """Save current form widget settings to the document"""
        # Don't save settings during initialization to preserve preferences for new documents
        if hasattr(self, '_loading_settings') and self._loading_settings:
            print("FORM_WIDGET: Skipping save_settings_to_document during initialization")
            return
            
        if not hasattr(self, 'document') or not self.document:
            return
        
        # Initialize document settings if not present
        if not hasattr(self.document, 'settings'):
            self.document.settings = {}
        
        # Save measure numbers settings
        self.document.settings.update({
            'notation/show_measure_numbers': self.show_measure_numbers.isChecked(),
            'notation/measure_number_frequency': self.measure_number_frequency.currentText(),
            'notation/measure_numbers_custom_interval': self.measure_numbers_custom_interval.value(),
            'notation/measure_number_position': self.measure_number_position.currentText(),
            'notation/measure_numbers_vertical': self.measure_numbers_vertical.currentText(),
            'notation/measure_numbers_font_size': self.measure_numbers_font_size.value(),
            'notation/measure_numbers_vertical_offset': self.measure_numbers_vertical_offset.value(),
            'notation/measure_numbers_horizontal_offset': self.measure_numbers_horizontal_offset.value(),
            'notation/measure_numbers_font_color': getattr(self, 'measure_numbers_color_value', '#000000'),
        })
        
        # Save barline control settings
        self.document.settings.update({
            'notation/max_measures_per_system': self.max_measures_per_system.value(),
            'layout/default_measures_per_system': self.max_measures_per_system.value(),  # Also save to layout key for compatibility
            'notation/barline_numbering': self.barline_numbering.isChecked(),
            'notation/barline_number_font_size': self.barline_number_font_size.value(),
            'notation/barline_numbers_font_color': getattr(self, 'barline_numbers_color_value', '#666666'),
        })
        
        # Layout settings are now handled by Preferences dialog
        # These settings are saved globally in QSettings
        
        # Mark document as modified
        if hasattr(self.document, 'set_modified'):
            self.document.set_modified(True)
        
        print(f"FORM_WIDGET: Saved all settings to document - measures per system: {self.max_measures_per_system.value()}")
    
    def on_property_changed(self):
        """Handle property changes from UI controls"""
        if not hasattr(self, 'measures_per_system_spin'):
            return
            
        # Save state for undo
        self.save_state(f"Updated layout settings")
        
        # Update measures per system setting
        self.measures_per_system = self.measures_per_system_spin.value()
        # Layout settings (auto_justify, dynamic_width) are now handled by Preferences dialog
        
        # Save settings to document immediately
        self.save_settings_to_document()
        
        # Update current measure properties if one is selected
        if self.selected_barline:
            measure = self.selected_barline
            
            # Layout settings (force_break_check, custom_width_check) are now handled by Preferences dialog
            
            # Update repeat count for repeat barlines
            if hasattr(self, 'repeat_count_spin') and measure.barline_type in ["repeat_start", "repeat_end", "repeat_both"]:
                measure.repeat_count = self.repeat_count_spin.value()
                
                # Update repeat properties
                measure.is_repeat_start = measure.barline_type in ["repeat_start", "repeat_both"]
                measure.is_repeat_end = measure.barline_type in ["repeat_end", "repeat_both"]
                
                # Update the score document
                if self.document and hasattr(self.document, 'measures'):
                    if isinstance(self.document.measures, dict):
                        if hasattr(measure, 'measure_number'):
                            self.document.measures[measure.measure_number] = measure
                    else:
                        # Handle list format
                        for i, doc_measure in enumerate(self.document.measures):
                            if doc_measure == measure:
                                self.document.measures[i] = measure
                                break
                
                # Update staff view
                if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
                    self.main_window_ref.staff_view.update()
        
        # Update score layout
        self.update_score_layout()
        
        # Update display
        self.update_barline_preview()
        self.update_undo_redo_buttons()
        
        # Update status
        self.update_status("Properties updated")
    
    def on_batch_insert_measures(self):
        """Handle batch measure insertion"""
        print(f"FORM_WIDGET: Batch insert button clicked!")
        print(f"FORM_WIDGET: Button enabled: {self.batch_insert_btn.isEnabled()}")
        print(f"FORM_WIDGET: Button visible: {self.batch_insert_btn.isVisible()}")
        count = self.batch_count_spin.value()
        position_text = self.batch_position_combo.currentText()
        
        print(f"FORM_WIDGET: Batch inserting {count} measures at {position_text}")
        
        # Get references to temporal bridge (preferred) or measure manager
        temporal_bridge = None
        measure_manager = None
        
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            if hasattr(staff_view, 'temporal_bridge'):
                temporal_bridge = staff_view.temporal_bridge
                # Ensure temporal bridge has the document reference
                if temporal_bridge:
                    if hasattr(staff_view, 'document') and staff_view.document:
                        temporal_bridge.document = staff_view.document
                        print(f"FORM_WIDGET: Set temporal bridge document reference to staff_view.document")
                    elif hasattr(self, 'document') and self.document:
                        temporal_bridge.document = self.document
                        print(f"FORM_WIDGET: Set temporal bridge document from form widget")
                    else:
                        print(f"FORM_WIDGET: Warning - no document found for temporal bridge")
                        temporal_bridge = None
            if hasattr(staff_view, 'document') and hasattr(staff_view.document, 'measure_manager'):
                measure_manager = staff_view.document.measure_manager
        
        if not temporal_bridge and not measure_manager:
            print("FORM_WIDGET: No temporal bridge or measure manager available for batch insertion")
            return
        
        # Determine insertion position
        insertion_position = None
        if position_text == "At End":
            insertion_position = None  # Insert at end
        elif position_text == "At Beginning":
            insertion_position = 2  # Insert after measure 1 (which is non-removable)
        elif position_text == "After Selected":
            if self.selected_barline and hasattr(self.selected_barline, 'measure_number'):
                insertion_position = self.selected_barline.measure_number + 1
            else:
                insertion_position = None  # Default to end if nothing selected
        
        # Save state for undo
        self.save_state(f"Batch insert {count} measures")
        
        # Perform batch insertion
        try:
            created_measures = []
            print(f"FORM_WIDGET: Attempting batch insertion - temporal_bridge={temporal_bridge is not None}, measure_manager={measure_manager is not None}")
            if temporal_bridge and hasattr(temporal_bridge, 'insert_measures_batch'):
                print(f"FORM_WIDGET: Calling temporal_bridge.insert_measures_batch({count}, {insertion_position})")
                created_measures = temporal_bridge.insert_measures_batch(count, insertion_position)
                print(f"FORM_WIDGET: Used temporal bridge for batch insertion - got {len(created_measures)} measures")
            elif measure_manager and hasattr(measure_manager, 'insert_measures_batch'):
                print(f"FORM_WIDGET: Calling measure_manager.insert_measures_batch({count}, {insertion_position})")
                created_measures = measure_manager.insert_measures_batch(count, insertion_position)
                print(f"FORM_WIDGET: Used measure manager for batch insertion - got {len(created_measures)} measures")
            else:
                print(f"FORM_WIDGET: No batch insertion method available - temporal_bridge={temporal_bridge}, measure_manager={measure_manager}")
                return
            print(f"FORM_WIDGET: Successfully created {len(created_measures)} measures in batch")
            
            # Update the display
            if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
                self.main_window_ref.staff_view.update()
            
            # Update status
            position_desc = f"at position {insertion_position}" if insertion_position else "at end"
            self.update_status(f"Inserted {count} measures {position_desc}")
            
        except Exception as e:
            print(f"FORM_WIDGET: Error during batch insertion: {e}")
            self.update_status(f"Error inserting measures: {e}")

    def on_deselect_all_barlines(self):
        """Handle deselection of all barlines"""
        # Clear the selected barline reference
        self.selected_barline = None
        
        # Deselect all barlines in the staff view
        # Use skip_form_widget_notification=True to prevent infinite recursion
        if self.main_window_ref and hasattr(self.main_window_ref, 'staff_view'):
            staff_view = self.main_window_ref.staff_view
            if hasattr(staff_view, 'deselect_all_barlines'):
                staff_view.deselect_all_barlines(skip_form_widget_notification=True)
            
            # Update the staff view display
            staff_view.update()
        
        # Hide repeat count spin for a cleaner interface when nothing is selected
        self.repeat_count_spin.setVisible(False)
        
        # Update status
        self.update_status("All barlines deselected - click on staff to create new barlines")
        
        print("FORM_WIDGET: Deselected all barlines - staff view handles focus management")

    # ONOTE SPECIFICATION: Mouse event handling for radio button deselection
    def mousePressEvent(self, event):
        """
        Handle mouse press events to implement click-anywhere-to-deselect radio buttons.
        
        According to ONOTE specification:
        "Returning to the form widget and clicking anywhere on it should deselect it as well 
        as all other radio buttons, making the form ready to accept a new user selection. 
        This should avoid any accidental insertion of unwanted barlines."
        """
        # Get the widget that was actually clicked
        clicked_widget = self.childAt(event.position().toPoint())
        
        print(f"FORM_WIDGET: Mouse press at {event.position().toPoint()}, clicked widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
        
        # Check if the click was on an interactive control
        if clicked_widget and self._is_interactive_widget(clicked_widget):
            print(f"FORM_WIDGET: Clicked on interactive widget {type(clicked_widget).__name__} - not deselecting")
            # Let the normal widget handle the event
            super().mousePressEvent(event)
            return
        
        # Click was on empty space or non-interactive area - deselect all radio buttons
        print("FORM_WIDGET: Clicked on empty area - deselecting all radio buttons")
        self._deselect_all_radio_buttons()
        
        # Call parent implementation to handle any other necessary processing
        super().mousePressEvent(event)
    

    
    def _is_interactive_widget(self, widget):
        """Check if a widget is interactive (should not trigger deselection)"""
        if not widget:
            return False
            
        # Check if it's an interactive control
        if isinstance(widget, (QRadioButton, QSpinBox, QCheckBox, QPushButton, QComboBox)):
            return True
            
        # Check if it's a label associated with an interactive control
        if isinstance(widget, QLabel):
            parent = widget.parent()
            if parent and hasattr(parent, 'layout') and parent.layout():
                # Only consider labels interactive if they're part of form layouts or next to controls
                layout = parent.layout()
                if isinstance(layout, QFormLayout):
                    return True
                # Check if this label is next to an interactive control in the same parent
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() and isinstance(item.widget(), (QRadioButton, QSpinBox, QCheckBox, QPushButton, QComboBox)):
                        return True
                return False
                
        # Check if it's a tab bar or tab widget (for tab switching)
        if isinstance(widget, QTabWidget) or hasattr(widget, 'tabBar'):
            return True
            
        # Check if it's a scroll area (for scrolling)
        if isinstance(widget, QScrollArea):
            return True
            
        # For containers with layouts, only consider them interactive if they contain actual interactive controls
        if hasattr(widget, 'layout') and widget.layout():
            layout = widget.layout()
            # Check if this container has any interactive controls
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.widget():
                    if isinstance(item.widget(), (QRadioButton, QSpinBox, QCheckBox, QPushButton, QComboBox)):
                        return True
                    # Recursively check child widgets
                    if self._has_interactive_children(item.widget()):
                        return True
            return False
            
        return False
    
    def _has_interactive_children(self, widget):
        """Recursively check if a widget contains any interactive children"""
        if not widget:
            return False
            
        # Check if this widget itself is interactive
        if isinstance(widget, (QRadioButton, QSpinBox, QCheckBox, QPushButton, QComboBox)):
            return True
            
        # Check children recursively
        for child in widget.findChildren(QWidget):
            if isinstance(child, (QRadioButton, QSpinBox, QCheckBox, QPushButton, QComboBox)):
                return True
            if hasattr(child, 'layout') and child.layout():
                if self._has_interactive_children(child):
                    return True
                    
        return False
    
    def _deselect_all_radio_buttons(self):
        """Helper method to deselect all radio buttons"""
        print("FORM_WIDGET: _deselect_all_radio_buttons called")
        
        if hasattr(self, 'barline_button_group'):
            print("FORM_WIDGET: Found barline_button_group")
            
            # Set a flag to prevent signal handling during deselection
            self._deselecting_radio_buttons = True
            
            # Temporarily disconnect the signal to prevent interference
            self.barline_button_group.buttonClicked.disconnect()
            
            # Temporarily disable exclusive mode to allow deselection
            was_exclusive = self.barline_button_group.exclusive()
            self.barline_button_group.setExclusive(False)
            
            # Get all buttons in the group
            buttons = self.barline_button_group.buttons()
            print(f"FORM_WIDGET: Found {len(buttons)} radio buttons")
            
            # Deselect all buttons by setting each one to unchecked
            for button in buttons:
                if button.isChecked():
                    print(f"FORM_WIDGET: Deselecting button: {button.text()}")
                    button.setChecked(False)
            
            # Restore exclusive mode
            self.barline_button_group.setExclusive(was_exclusive)
            
            # Reconnect the signal
            self.barline_button_group.buttonClicked.connect(self.on_barline_type_changed)
            
            # Clear the deselection flag
            self._deselecting_radio_buttons = False
            
            print("FORM_WIDGET: All barline radio buttons deselected - ready for new selection")
            
            # Update status to indicate deselection
            self.update_status("Barline types deselected - select a type and click on staff to create barlines")
            
            # Hide repeat count since no barline type is selected
            if hasattr(self, 'repeat_count_spin'):
                self.repeat_count_spin.setVisible(False)
            
            # Update barline preview to reflect no selection
            self.update_barline_preview()
        else:
            print("FORM_WIDGET: No barline_button_group found")
    
    def on_measure_numbers_frequency_changed(self, index):
        """Handle measure numbers frequency change to show/hide custom interval"""
        frequency = self.measure_number_frequency.currentText()
        is_custom = frequency == "Custom Interval"
        self.measure_numbers_custom_interval.setVisible(is_custom)
        
        # Find the custom interval row and show/hide it
        parent_layout = self.measure_numbers_custom_interval.parent().layout()
        if isinstance(parent_layout, QFormLayout):
            for i in range(parent_layout.rowCount()):
                label_item = parent_layout.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if label_item and label_item.widget() and label_item.widget().text() == "Custom Interval:":
                    label_item.widget().setVisible(is_custom)
                    break
        
        # Update score
        self.update_score()
    
    def choose_font_color(self, category):
        """Choose font color for the specified category"""
        from PyQt6.QtWidgets import QColorDialog
        
        # Get current color
        current_color = "#000000"  # Default
        if category == 'measure_numbers':
            current_color = getattr(self, 'measure_numbers_color_value', '#000000')
        elif category == 'barline_numbers':
            current_color = getattr(self, 'barline_numbers_color_value', '#666666')
        
        # Show color dialog
        color = QColorDialog.getColor(QColor(current_color), self, f"Choose {category.replace('_', ' ').title()} Color")
        
        if color.isValid():
            hex_color = color.name()
            
            # Update the button style
            if category == 'measure_numbers':
                self.measure_numbers_font_color.setStyleSheet(f"background-color: {hex_color}; color: {'white' if self.is_dark_color_hex(hex_color) else 'black'};")
                setattr(self, 'measure_numbers_color_value', hex_color)
            elif category == 'barline_numbers':
                self.barline_number_font_color.setStyleSheet(f"background-color: {hex_color}; color: {'white' if self.is_dark_color_hex(hex_color) else 'black'};")
                setattr(self, 'barline_numbers_color_value', hex_color)
            
            # Update score
            self.update_score()
    
    def is_dark_color_hex(self, hex_color):
        """Check if a hex color is dark (for determining text color)"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Calculate luminance
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        
        return luminance < 0.5

    def eventFilter(self, obj, event):
        """
        Event filter to handle clicks on tab widget content areas.
        This ensures that clicks anywhere on the form widget (except interactive controls)
        will deselect radio buttons.
        """
        from PyQt6.QtCore import QEvent
        
        # Handle clicks on the Barline tab content area
        if hasattr(self, 'barline_tab_widget') and obj == self.barline_tab_widget and event.type() == QEvent.Type.MouseButtonPress:
            clicked_widget = self.barline_tab_widget.childAt(event.position().toPoint())
            print(f"FORM_WIDGET: EventFilter - Barline tab click at {event.position().toPoint()}, widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
            if not self._is_interactive_widget(clicked_widget):
                print("FORM_WIDGET: Clicked on Barline tab area - deselecting all radio buttons")
                self._deselect_all_radio_buttons()
            return True
            
        # Handle clicks on scroll areas and their content
        if isinstance(obj, QScrollArea) and event.type() == QEvent.Type.MouseButtonPress:
            clicked_widget = obj.childAt(event.position().toPoint())
            print(f"FORM_WIDGET: EventFilter - Scroll area click at {event.position().toPoint()}, widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
            if not self._is_interactive_widget(clicked_widget):
                print("FORM_WIDGET: Clicked on scroll area - deselecting all radio buttons")
                self._deselect_all_radio_buttons()
            return True
            
        # Handle clicks on scroll content widgets
        if isinstance(obj, QWidget) and hasattr(obj, 'layout') and obj.layout() and event.type() == QEvent.Type.MouseButtonPress:
            # Check if this is a scroll content widget (has a layout but no specific class)
            clicked_widget = obj.childAt(event.position().toPoint())
            print(f"FORM_WIDGET: EventFilter - Scroll content click at {event.position().toPoint()}, widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
            if not self._is_interactive_widget(clicked_widget):
                print("FORM_WIDGET: Clicked on scroll content - deselecting all radio buttons")
                self._deselect_all_radio_buttons()
            return True
            
        # Handle clicks on group boxes
        if isinstance(obj, QGroupBox) and event.type() == QEvent.Type.MouseButtonPress:
            clicked_widget = obj.childAt(event.position().toPoint())
            print(f"FORM_WIDGET: EventFilter - Group box click at {event.position().toPoint()}, widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
            if not self._is_interactive_widget(clicked_widget):
                print("FORM_WIDGET: Clicked on group box - deselecting all radio buttons")
                self._deselect_all_radio_buttons()
            return True
            
        # Handle clicks on the main tab widget
        if obj == self.tab_widget and event.type() == QEvent.Type.MouseButtonPress:
            # Get the current tab widget
            current_widget = self.tab_widget.currentWidget()
            if current_widget:
                # Check if the click was on the tab content area (not on interactive controls)
                clicked_widget = current_widget.childAt(event.position().toPoint())
                print(f"FORM_WIDGET: EventFilter - Main tab click at {event.position().toPoint()}, widget: {type(clicked_widget).__name__ if clicked_widget else 'None'}")
                
                # If clicking on empty space or non-interactive areas, deselect radio buttons
                if not clicked_widget or not self._is_interactive_widget(clicked_widget):
                    print("FORM_WIDGET: Clicked on tab content area - deselecting all radio buttons")
                    self._deselect_all_radio_buttons()
        
        # Let the event continue to be processed normally
        return super().eventFilter(obj, event)