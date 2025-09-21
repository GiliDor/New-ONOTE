from PyQt6.QtWidgets import (QDialog, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QCheckBox, QLabel, QScrollArea, 
                             QComboBox, QSlider, QPushButton, QSpinBox,
                             QDoubleSpinBox, QRadioButton, QGroupBox, QFileDialog, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QFormLayout, QDialogButtonBox, QListWidget,
                             QToolBar, QToolButton, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QDir, QSettings, pyqtSignal
from PyQt6.QtGui import QColor
import os
import sounddevice as sd
import rtmidi
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from plugins.plugin_scanner import PluginScanner, Plugin

class PreferencesDialog(QDialog):
    # Signal emitted when notation setup settings change
    notation_settings_changed = pyqtSignal(dict)
    # NEW: General signal for all preferences
    preferences_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(False)  # Make modeless
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # CRITICAL FIX: Ensure dialog always shows on Desktop background, never behind it
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.settings = QSettings()
        self.dialog_zoom = 1.0
        self._dirty = False  # Track unsaved changes

        # --- Zoom controls bar ---
        zoom_toolbar = QToolBar()
        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("+")
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom * 1.2))
        zoom_toolbar.addWidget(zoom_in_btn)
        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("–")
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom / 1.2))
        zoom_toolbar.addWidget(zoom_out_btn)
        reset_btn = QToolButton()
        reset_btn.setText("100%")
        reset_btn.setToolTip("Reset Zoom")
        reset_btn.clicked.connect(lambda: self._set_dialog_zoom(1.0))
        zoom_toolbar.addWidget(reset_btn)
        zoom_menu = QMenu("In View", self)
        self.zoom_actions = []
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_dialog_zoom(v))
            zoom_menu.addAction(act)
            self.zoom_actions.append((act, value))
        zoom_tool_btn = QToolButton()
        zoom_tool_btn.setText("In View")
        zoom_tool_btn.setMenu(zoom_menu)
        zoom_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        zoom_toolbar.addWidget(zoom_tool_btn)

        # --- Main content in a scroll area for scalable zoom ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        main_layout = QVBoxLayout()
        main_layout.addWidget(zoom_toolbar)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        self.scroll_area.setWidget(self.content_widget)
        self._set_dialog_zoom(1.0)
        
        # Initialize settings
        self.settings = QSettings("ONOTE", "Preferences")
        
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #cccccc; background: white; padding: 10px; }
            QTabBar::tab { background: #f0f0f0; border: 1px solid #cccccc; padding: 8px 12px; margin-right: 2px; min-width: 100px; }
            QTabBar::tab:selected { background: white; border-bottom-color: white; }
            QGroupBox { margin-top: 15px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            
            /* Simplified ComboBox styling for better functionality */
            QComboBox { 
                color: black; 
                background: white; 
                border: 1px solid #cccccc; 
                padding: 2px 4px; 
                min-height: 18px;
            }
            QComboBox:focus { 
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down { 
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background: white;
                selection-background-color: #0078d4;
                selection-color: white;
                border: 1px solid #cccccc;
            }
            
            /* Simplified ListWidget styling */
            QListWidget {
                color: black;
                background: white;
                border: 1px solid #cccccc;
            }
            QListWidget::item {
                color: black;
                background: white;
                padding: 2px;
            }
            QListWidget::item:selected {
                background: #0078d4;
                color: white;
            }
        """)
        self.content_layout.addWidget(self.tab_widget)
        
        # Create and set up tabs
        self.general_tab = QWidget()
        self.layout_tab = QWidget()
        self.font_tab = QWidget()
        self.audio_tab = QWidget()
        self.midi_io_tab = QWidget()
        self.midi_record_tab = QWidget()
        self.midi_import_tab = QWidget()
        self.plugins_tab = QWidget()
        
        self.setup_general_tab()
        self.setup_layout_tab()
        self.setup_font_tab()
        self.setup_audio_tab()
        self.setup_midi_io_tab()
        self.setup_midi_record_tab()
        self.setup_midi_import_tab()
        self.setup_plugins_tab()
        
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.layout_tab, "Page Layout")
        self.tab_widget.addTab(self.font_tab, "Fonts")
        
        # Create notation setup tab (NEW)
        self.notation_tab = QWidget()
        self.setup_notation_tab()
        self.tab_widget.addTab(self.notation_tab, "Default Notation Setup")
        
        self.tab_widget.addTab(self.audio_tab, "Audio")
        self.tab_widget.addTab(self.midi_io_tab, "MIDI I/O")
        self.tab_widget.addTab(self.midi_record_tab, "MIDI Record")
        self.tab_widget.addTab(self.midi_import_tab, "MIDI Import")
        self.tab_widget.addTab(self.plugins_tab, "Plug-in Manager")
        
        # Add dialog buttons
        button_box = QDialogButtonBox()
        
        # Apply button - applies settings but keeps dialog open
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_box.addButton(self.apply_button, QDialogButtonBox.ButtonRole.ApplyRole)
        # Keep Apply enabled across all tabs; we'll still gate saves in apply_settings
        self.apply_button.setEnabled(True)
        
        # Close button - closes dialog
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept_settings)
        button_box.addButton(close_button, QDialogButtonBox.ButtonRole.RejectRole)
        
        self.content_layout.addWidget(button_box)
        
        # Load saved settings
        self.load_settings()

        # After all widgets are created in __init__ or setup methods, connect their change signals to _mark_dirty
        # Example for a few widgets:
        self.staff_name_font_size.valueChanged.connect(self._mark_dirty)
        self.staff_name_vertical.valueChanged.connect(self._mark_dirty)
        self.staff_name_horizontal.valueChanged.connect(self._mark_dirty)
        self.section_name_font_size.valueChanged.connect(self._mark_dirty)
        self.section_name_vertical.valueChanged.connect(self._mark_dirty)
        self.section_name_horizontal.valueChanged.connect(self._mark_dirty)
        self.time_sig_font_size.valueChanged.connect(self._mark_dirty)
        self.time_sig_vertical.valueChanged.connect(self._mark_dirty)
        self.time_sig_horizontal.valueChanged.connect(self._mark_dirty)
        self.time_sig_spacing.valueChanged.connect(self._mark_dirty)
        self.key_sig_font_size.valueChanged.connect(self._mark_dirty)
        self.key_sig_vertical.valueChanged.connect(self._mark_dirty)
        self.key_sig_horizontal.valueChanged.connect(self._mark_dirty)
        self.key_sig_accidental_spacing.valueChanged.connect(self._mark_dirty)
        self.clef_font_size.valueChanged.connect(self._mark_dirty)
        self.clef_vertical.valueChanged.connect(self._mark_dirty)
        self.clef_horizontal.valueChanged.connect(self._mark_dirty)
        self.directions_font_size.valueChanged.connect(self._mark_dirty)
        self.directions_vertical.valueChanged.connect(self._mark_dirty)
        self.directions_horizontal.valueChanged.connect(self._mark_dirty)
        # For color buttons, connect their clicked signal to _mark_dirty as well
        self.staff_name_font_color.clicked.connect(self._mark_dirty)
        self.section_name_font_color.clicked.connect(self._mark_dirty)
        self.time_sig_font_color.clicked.connect(self._mark_dirty)
        self.key_sig_font_color.clicked.connect(self._mark_dirty)
        self.clef_font_color.clicked.connect(self._mark_dirty)
        
        # Connect measure numbers and barline controls to _mark_dirty
        self.show_measure_numbers.toggled.connect(self._mark_dirty)
        self.measure_numbers_frequency.currentTextChanged.connect(self._mark_dirty)
        self.measure_numbers_custom_interval.valueChanged.connect(self._mark_dirty)
        self.measure_numbers_position.currentTextChanged.connect(self._mark_dirty)
        self.measure_numbers_vertical.currentTextChanged.connect(self._mark_dirty)
        self.measure_numbers_font_size.valueChanged.connect(self._mark_dirty)
        self.measure_numbers_vertical_offset.valueChanged.connect(self._mark_dirty)
        self.measure_numbers_horizontal_offset.valueChanged.connect(self._mark_dirty)
        self.measure_numbers_font_color.clicked.connect(self._mark_dirty)
        
        self.max_measures_per_system.valueChanged.connect(self._mark_dirty)
        self.barline_numbering.toggled.connect(self._mark_dirty)
        self.barline_number_font_size.valueChanged.connect(self._mark_dirty)
        self.barline_number_vertical_offset.valueChanged.connect(self._mark_dirty)
        self.barline_number_horizontal_offset.valueChanged.connect(self._mark_dirty)
        self.barline_number_font_color.clicked.connect(self._mark_dirty)

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01)

    def _mark_dirty(self):
        self._dirty = True
        if hasattr(self, 'apply_button'):
            self.apply_button.setEnabled(True)

    def load_settings(self):
        """Load settings from QSettings"""
        # General settings
        default_score_dir = "/Users/gilidor/Library/Mobile Documents/com~apple~CloudDocs/QC-Projects/ONOTE Music scores"
        self.score_dir.setText(self.settings.value("general/score_directory", default_score_dir))
        self.view_mode.setCurrentText(self.settings.value("general/view_mode", "Pages Down"))
        self.autosave.setValue(int(self.settings.value("general/autosave_interval", 5)))
        self.default_zoom.setCurrentText(self.settings.value("general/default_zoom", "100%"))
        self.show_rulers.setChecked(self.settings.value("general/show_rulers", True, type=bool))
        self.show_grid.setChecked(self.settings.value("general/show_grid", False, type=bool))
        self.recent_files_count.setValue(int(self.settings.value("general/recent_files_count", 10)))
        self.create_backup.setChecked(self.settings.value("general/create_backup", True, type=bool))
        self.auto_backup.setChecked(self.settings.value("general/auto_backup", True, type=bool))
        
        # Layout and Page settings
        self.default_page_size.setCurrentText(self.settings.value("layout/default_page_size", "A4 (210 × 297 mm)"))
        self.default_orientation.setCurrentText(self.settings.value("layout/default_orientation", "Portrait"))
        self.default_top_margin.setValue(float(self.settings.value("layout/default_top_margin", 20.0)))
        self.default_bottom_margin.setValue(float(self.settings.value("layout/default_bottom_margin", 20.0)))
        self.default_left_margin.setValue(float(self.settings.value("layout/default_left_margin", 25.0)))
        self.default_right_margin.setValue(float(self.settings.value("layout/default_right_margin", 25.0)))
        self.default_staff_spacing.setValue(int(self.settings.value("layout/default_staff_spacing", 40)))
        self.default_grand_staff_spacing.setValue(int(self.settings.value("layout/default_grand_staff_spacing", 32)))
        self.default_system_spacing.setValue(int(self.settings.value("layout/default_system_spacing", 80)))
        self.default_measures_per_system.setValue(int(self.settings.value("layout/default_measures_per_system", 4)))
        # Initial MPS preference
        if hasattr(self, 'initial_mps_enabled') and self.initial_mps_enabled is not None:
            self.initial_mps_enabled.setChecked(self.settings.value("layout/initial_mps_enabled", True, type=bool))
        self.default_notation_size.setValue(float(self.settings.value("layout/default_notation_size", 1.0)))
        self.show_staff_names.setChecked(self.settings.value("layout/show_staff_names", True, type=bool))
        self.show_page_numbers.setChecked(self.settings.value("layout/show_page_numbers", True, type=bool))
        self.justify_last_system.setChecked(self.settings.value("layout/justify_last_system", False, type=bool))
        self.hide_empty_staves.setChecked(self.settings.value("layout/hide_empty_staves", False, type=bool))
        self.default_print_quality.setCurrentText(self.settings.value("layout/default_print_quality", "Normal"))
        self.default_print_resolution.setCurrentText(self.settings.value("layout/default_print_resolution", "600 DPI"))
        
        # Layout Settings (moved from form widget)
        self.auto_justify.setChecked(self.settings.value("layout/auto_justify", True, type=bool))
        self.dynamic_width.setChecked(self.settings.value("layout/dynamic_width", True, type=bool))
        self.force_break.setChecked(self.settings.value("layout/force_break", False, type=bool))
        self.custom_width_enabled.setChecked(self.settings.value("layout/custom_width_enabled", False, type=bool))
        self.custom_width_value.setValue(int(self.settings.value("layout/custom_width_value", 100)))
        self.truncate_empty.setChecked(self.settings.value("layout/truncate_empty", False, type=bool))
        
        # Font settings
        self.font_name_combo.setCurrentText(self.settings.value("fonts/default_font_name", "Arial"))
        self.font_style_combo.setCurrentText(self.settings.value("fonts/default_font_style", "Regular"))
        self.font_size_spin.setValue(int(self.settings.value("fonts/default_font_size", 12)))
        
        # Audio settings
        self.audio_device.setCurrentText(self.settings.value("audio/device", "System Default"))
        self.sample_rate.setCurrentText(self.settings.value("audio/sample_rate", "44100 Hz"))
        self.buffer_size.setCurrentText(self.settings.value("audio/buffer_size", "512"))
        
        # MIDI Record settings
        self.quantize_input.setCurrentText(self.settings.value("midi_record/quantize_input", "None"))
        self.record_mode.setCurrentText(self.settings.value("midi_record/record_mode", "Replace"))
        self.count_in.setValue(int(self.settings.value("midi_record/count_in", 1)))
        self.metronome_volume.setValue(int(self.settings.value("midi_record/metronome_volume", 80)))
        self.metronome_sound.setCurrentText(self.settings.value("midi_record/metronome_sound", "Click"))
        self.metronome_playback.setChecked(self.settings.value("midi_record/metronome_playback", True, type=bool))
        self.metronome_recording.setChecked(self.settings.value("midi_record/metronome_recording", True, type=bool))
        
        # MIDI Import settings
        self.import_quantize.setCurrentText(self.settings.value("midi_import/quantize", "None"))
        self.channel_handling.setCurrentText(self.settings.value("midi_import/channel_handling", "Merge All"))
        self.import_tempo.setChecked(self.settings.value("midi_import/import_tempo", True, type=bool))
        self.import_dynamics.setChecked(self.settings.value("midi_import/import_dynamics", True, type=bool))
        self.import_articulations.setChecked(self.settings.value("midi_import/import_articulations", True, type=bool))
        self.split_point.setValue(int(self.settings.value("midi_import/split_point", 60)))
        self.detect_tuplets.setChecked(self.settings.value("midi_import/detect_tuplets", True, type=bool))
        self.detect_grace_notes.setChecked(self.settings.value("midi_import/detect_grace_notes", True, type=bool))
        self.detect_pickup.setChecked(self.settings.value("midi_import/detect_pickup", True, type=bool))
        
        # Notation setup settings (NEW)
        # Staff name settings - FIXED to use factory defaults consistently
        self.staff_name_font_size.setValue(int(self.settings.value("notation/staff_name_font_size", 10)))
        self.staff_name_vertical.setValue(int(self.settings.value("notation/staff_name_vertical", -8)))
        self.staff_name_horizontal.setValue(int(self.settings.value("notation/staff_name_horizontal", 0)))
        staff_name_color = self.settings.value("notation/staff_name_font_color", "#000000")
        self.staff_name_font_color.setStyleSheet(f"background-color: {staff_name_color}; color: {'white' if self.is_dark_color_hex(staff_name_color) else 'black'};")
        self.staff_names_color_value = staff_name_color
        
        # Section name settings - FIXED to use factory defaults consistently
        self.section_name_font_size.setValue(int(self.settings.value("notation/section_name_font_size", 10)))
        self.section_name_vertical.setValue(int(self.settings.value("notation/section_name_vertical", 0)))
        self.section_name_horizontal.setValue(int(self.settings.value("notation/section_name_horizontal", 0)))
        section_name_color = self.settings.value("notation/section_name_font_color", "#000000")
        self.section_name_font_color.setStyleSheet(f"background-color: {section_name_color}; color: {'white' if self.is_dark_color_hex(section_name_color) else 'black'};")
        self.section_names_color_value = section_name_color
        
        # Time signature settings
        self.time_sig_font_size.setValue(int(self.settings.value("notation/time_sig_font_size", 24)))
        self.time_sig_vertical.setValue(int(self.settings.value("notation/time_sig_vertical", 0)))
        self.time_sig_horizontal.setValue(int(self.settings.value("notation/time_sig_horizontal", 40)))
        self.time_sig_spacing.setValue(int(self.settings.value("notation/time_sig_spacing", 18)))
        self.time_sig_color_value = self.settings.value("notation/time_sig_font_color", "#000000")
        self.time_sig_font_color.setStyleSheet(f"background-color: {self.time_sig_color_value}; color: {'white' if self.is_dark_color_hex(self.time_sig_color_value) else 'black'};")
        
        # Key signature settings
        self.key_sig_font_size.setValue(int(self.settings.value("notation/key_sig_font_size", 14)))
        self.key_sig_vertical.setValue(int(self.settings.value("notation/key_sig_vertical", 0)))
        self.key_sig_horizontal.setValue(int(self.settings.value("notation/key_sig_horizontal", 75)))
        self.key_sig_accidental_spacing.setValue(int(self.settings.value("notation/key_sig_accidental_spacing", 12)))
        self.key_sig_color_value = self.settings.value("notation/key_sig_font_color", "#000000")
        self.key_sig_font_color.setStyleSheet(f"background-color: {self.key_sig_color_value}; color: {'white' if self.is_dark_color_hex(self.key_sig_color_value) else 'black'};")
        
        # Clef settings
        self.clef_font_size.setValue(int(self.settings.value("notation/clef_font_size", 32)))
        self.clef_vertical.setValue(int(self.settings.value("notation/clef_vertical", 0)))
        self.clef_horizontal.setValue(int(self.settings.value("notation/clef_horizontal", 20)))
        self.clef_color_value = self.settings.value("notation/clef_font_color", "#000000")
        self.clef_font_color.setStyleSheet(f"background-color: {self.clef_color_value}; color: {'white' if self.is_dark_color_hex(self.clef_color_value) else 'black'};")
        
        # Musical directions settings - FIXED to use factory defaults consistently
        self.directions_font_size.setValue(int(self.settings.value("notation/directions_font_size", 10)))
        self.directions_vertical.setValue(int(self.settings.value("notation/directions_vertical", 0)))
        self.directions_horizontal.setValue(int(self.settings.value("notation/directions_horizontal", 0)))
        
        # Measure numbers settings (moved from layout)
        self.show_measure_numbers.setChecked(self.settings.value("notation/show_measure_numbers", True, type=bool))
        self.measure_numbers_frequency.setCurrentText(self.settings.value("notation/measure_numbers_frequency", "Every Measure"))
        self.measure_numbers_custom_interval.setValue(int(self.settings.value("notation/measure_numbers_custom_interval", 5)))
        self.measure_numbers_position.setCurrentText(self.settings.value("notation/measure_numbers_position", "Center"))
        self.measure_numbers_vertical.setCurrentText(self.settings.value("notation/measure_numbers_vertical", "Above System"))
        self.measure_numbers_font_size.setValue(int(self.settings.value("notation/measure_numbers_font_size", 10)))
        self.measure_numbers_vertical_offset.setValue(int(self.settings.value("notation/measure_numbers_vertical_offset", -20)))
        self.measure_numbers_horizontal_offset.setValue(int(self.settings.value("notation/measure_numbers_horizontal_offset", -34)))
        
        # Barline control settings
        # Try to read from notation key first, then fallback to layout key for compatibility
        max_measures = self.settings.value("notation/max_measures_per_system", None)
        if max_measures is None:
            max_measures = self.settings.value("layout/default_measures_per_system", 8)
        self.max_measures_per_system.setValue(int(max_measures))
        self.barline_numbering.setChecked(self.settings.value("notation/barline_numbering", False, type=bool))
        self.barline_number_font_size.setValue(int(self.settings.value("notation/barline_number_font_size", 8)))
        
        # NEW: Barline number offset controls
        self.barline_number_vertical_offset.setValue(int(self.settings.value("notation/barline_number_vertical_offset", 0)))
        self.barline_number_horizontal_offset.setValue(int(self.settings.value("notation/barline_number_horizontal_offset", 3)))
        
        # Font color settings for measure numbers and barline numbers
        self.measure_numbers_color_value = self.settings.value("notation/measure_numbers_font_color", "#000000")
        self.measure_numbers_font_color.setStyleSheet(f"background-color: {self.measure_numbers_color_value}; color: {'white' if self.is_dark_color_hex(self.measure_numbers_color_value) else 'black'};")
        
        self.barline_numbers_color_value = self.settings.value("notation/barline_numbers_font_color", "#666666")
        self.barline_number_font_color.setStyleSheet(f"background-color: {self.barline_numbers_color_value}; color: {'white' if self.is_dark_color_hex(self.barline_numbers_color_value) else 'black'};")
    
        self._dirty = False
        if hasattr(self, 'apply_button'):
            self.apply_button.setEnabled(False)
    
    def save_settings(self):
        """Save settings to QSettings"""
        # General settings
        self.settings.setValue("general/score_directory", self.score_dir.text())
        self.settings.setValue("general/view_mode", self.view_mode.currentText())
        self.settings.setValue("general/autosave_interval", self.autosave.value())
        self.settings.setValue("general/default_zoom", self.default_zoom.currentText())
        self.settings.setValue("general/show_rulers", self.show_rulers.isChecked())
        self.settings.setValue("general/show_grid", self.show_grid.isChecked())
        self.settings.setValue("general/recent_files_count", self.recent_files_count.value())
        self.settings.setValue("general/create_backup", self.create_backup.isChecked())
        self.settings.setValue("general/auto_backup", self.auto_backup.isChecked())
        
        # Layout and Page settings
        self.settings.setValue("layout/default_page_size", self.default_page_size.currentText())
        self.settings.setValue("layout/default_orientation", self.default_orientation.currentText())
        self.settings.setValue("layout/default_top_margin", self.default_top_margin.value())
        self.settings.setValue("layout/default_bottom_margin", self.default_bottom_margin.value())
        self.settings.setValue("layout/default_left_margin", self.default_left_margin.value())
        self.settings.setValue("layout/default_right_margin", self.default_right_margin.value())
        # Also persist default zoom percentage selected in Page Layout tab
        try:
            if hasattr(self, 'default_zoom_spin') and self.default_zoom_spin is not None:
                self.settings.setValue("general/default_zoom", f"{self.default_zoom_spin.value()}%")
        except Exception:
            pass
        self.settings.setValue("layout/default_staff_spacing", self.default_staff_spacing.value())
        self.settings.setValue("layout/default_grand_staff_spacing", self.default_grand_staff_spacing.value())
        self.settings.setValue("layout/default_system_spacing", self.default_system_spacing.value())
        # Canonicalize Measures/System: prefer Page Layout tab spinner and mirror to notation key later
        canonical_mps = self.default_measures_per_system.value()
        self.settings.setValue("layout/default_measures_per_system", canonical_mps)
        # Persist Initial MPS preference
        if hasattr(self, 'initial_mps_enabled') and self.initial_mps_enabled is not None:
            self.settings.setValue("layout/initial_mps_enabled", self.initial_mps_enabled.isChecked())
        self.settings.setValue("layout/default_notation_size", self.default_notation_size.value())
        self.settings.setValue("layout/show_staff_names", self.show_staff_names.isChecked())
        self.settings.setValue("layout/show_page_numbers", self.show_page_numbers.isChecked())
        self.settings.setValue("layout/justify_last_system", self.justify_last_system.isChecked())
        self.settings.setValue("layout/hide_empty_staves", self.hide_empty_staves.isChecked())
        self.settings.setValue("layout/default_print_quality", self.default_print_quality.currentText())
        self.settings.setValue("layout/default_print_resolution", self.default_print_resolution.currentText())
        
        # Layout Settings (moved from form widget)
        self.settings.setValue("layout/auto_justify", self.auto_justify.isChecked())
        self.settings.setValue("layout/dynamic_width", self.dynamic_width.isChecked())
        self.settings.setValue("layout/force_break", self.force_break.isChecked())
        self.settings.setValue("layout/custom_width_enabled", self.custom_width_enabled.isChecked())
        self.settings.setValue("layout/custom_width_value", self.custom_width_value.value())
        self.settings.setValue("layout/truncate_empty", self.truncate_empty.isChecked())
        
        # Font settings
        self.settings.setValue("fonts/default_font_name", self.font_name_combo.currentText())
        self.settings.setValue("fonts/default_font_style", self.font_style_combo.currentText())
        self.settings.setValue("fonts/default_font_size", self.font_size_spin.value())
        
        # Audio settings
        self.settings.setValue("audio/device", self.audio_device.currentText())
        self.settings.setValue("audio/sample_rate", self.sample_rate.currentText())
        self.settings.setValue("audio/buffer_size", self.buffer_size.currentText())
        
        # MIDI Record settings
        self.settings.setValue("midi_record/quantize_input", self.quantize_input.currentText())
        self.settings.setValue("midi_record/record_mode", self.record_mode.currentText())
        self.settings.setValue("midi_record/count_in", self.count_in.value())
        self.settings.setValue("midi_record/metronome_volume", self.metronome_volume.value())
        self.settings.setValue("midi_record/metronome_sound", self.metronome_sound.currentText())
        self.settings.setValue("midi_record/metronome_playback", self.metronome_playback.isChecked())
        self.settings.setValue("midi_record/metronome_recording", self.metronome_recording.isChecked())
        
        # MIDI Import settings
        self.settings.setValue("midi_import/quantize", self.import_quantize.currentText())
        self.settings.setValue("midi_import/channel_handling", self.channel_handling.currentText())
        self.settings.setValue("midi_import/import_tempo", self.import_tempo.isChecked())
        self.settings.setValue("midi_import/import_dynamics", self.import_dynamics.isChecked())
        self.settings.setValue("midi_import/import_articulations", self.import_articulations.isChecked())
        self.settings.setValue("midi_import/split_point", self.split_point.value())
        self.settings.setValue("midi_import/detect_tuplets", self.detect_tuplets.isChecked())
        self.settings.setValue("midi_import/detect_grace_notes", self.detect_grace_notes.isChecked())
        self.settings.setValue("midi_import/detect_pickup", self.detect_pickup.isChecked())
        
        # Notation setup settings
        # Staff name settings
        self.settings.setValue("notation/staff_name_font_size", self.staff_name_font_size.value())
        self.settings.setValue("notation/staff_name_vertical", self.staff_name_vertical.value())
        self.settings.setValue("notation/staff_name_horizontal", self.staff_name_horizontal.value())
        self.settings.setValue("notation/staff_name_font_color", getattr(self, 'staff_names_color_value', '#000000'))
        
        # Section name settings
        self.settings.setValue("notation/section_name_font_size", self.section_name_font_size.value())
        self.settings.setValue("notation/section_name_vertical", self.section_name_vertical.value())
        self.settings.setValue("notation/section_name_horizontal", self.section_name_horizontal.value())
        self.settings.setValue("notation/section_name_font_color", getattr(self, 'section_names_color_value', '#000000'))
        
        # Time signature settings
        self.settings.setValue("notation/time_sig_font_size", self.time_sig_font_size.value())
        self.settings.setValue("notation/time_sig_vertical", self.time_sig_vertical.value())
        self.settings.setValue("notation/time_sig_horizontal", self.time_sig_horizontal.value())
        self.settings.setValue("notation/time_sig_spacing", self.time_sig_spacing.value())
        self.settings.setValue("notation/time_sig_font_color", getattr(self, 'time_sig_color_value', '#000000'))
        
        # Key signature settings
        self.settings.setValue("notation/key_sig_font_size", self.key_sig_font_size.value())
        self.settings.setValue("notation/key_sig_vertical", self.key_sig_vertical.value())
        self.settings.setValue("notation/key_sig_horizontal", self.key_sig_horizontal.value())
        self.settings.setValue("notation/key_sig_accidental_spacing", self.key_sig_accidental_spacing.value())
        self.settings.setValue("notation/key_sig_font_color", getattr(self, 'key_sig_color_value', '#000000'))
        
        # Clef settings
        self.settings.setValue("notation/clef_font_size", self.clef_font_size.value())
        self.settings.setValue("notation/clef_vertical", self.clef_vertical.value())
        self.settings.setValue("notation/clef_horizontal", self.clef_horizontal.value())
        self.settings.setValue("notation/clef_font_color", getattr(self, 'clef_color_value', '#000000'))
        
        # Musical directions settings
        self.settings.setValue("notation/directions_font_size", self.directions_font_size.value())
        self.settings.setValue("notation/directions_vertical", self.directions_vertical.value())
        self.settings.setValue("notation/directions_horizontal", self.directions_horizontal.value())
        
        # Measure numbers settings (moved from layout)
        self.settings.setValue("notation/show_measure_numbers", self.show_measure_numbers.isChecked())
        self.settings.setValue("notation/measure_numbers_frequency", self.measure_numbers_frequency.currentText())
        self.settings.setValue("notation/measure_numbers_custom_interval", self.measure_numbers_custom_interval.value())
        self.settings.setValue("notation/measure_numbers_position", self.measure_numbers_position.currentText())
        self.settings.setValue("notation/measure_numbers_vertical", self.measure_numbers_vertical.currentText())
        self.settings.setValue("notation/measure_numbers_font_size", self.measure_numbers_font_size.value())
        self.settings.setValue("notation/measure_numbers_vertical_offset", self.measure_numbers_vertical_offset.value())
        self.settings.setValue("notation/measure_numbers_horizontal_offset", self.measure_numbers_horizontal_offset.value())
        
        # Barline control settings
        # Keep Notation in sync with Page Layout canonical value
        try:
            mps_value = canonical_mps
        except NameError:
            mps_value = self.default_measures_per_system.value() if hasattr(self, 'default_measures_per_system') else self.max_measures_per_system.value()
        self.settings.setValue("notation/max_measures_per_system", mps_value)
        # Do not overwrite layout/default_measures_per_system here
        self.settings.setValue("notation/barline_numbering", self.barline_numbering.isChecked())
        self.settings.setValue("notation/barline_number_font_size", self.barline_number_font_size.value())
        
        # NEW: Save barline number offset settings
        self.settings.setValue("notation/barline_number_vertical_offset", self.barline_number_vertical_offset.value())
        self.settings.setValue("notation/barline_number_horizontal_offset", self.barline_number_horizontal_offset.value())
        
        self.settings.setValue("notation/barline_numbers_font_color", getattr(self, 'barline_numbers_color_value', '#666666'))
        
        # Measure numbers font color
        self.settings.setValue("notation/measure_numbers_font_color", getattr(self, 'measure_numbers_color_value', '#000000'))
    
        self._dirty = False
        if hasattr(self, 'apply_button'):
            self.apply_button.setEnabled(False)
        # Ensure values are written to persistent storage immediately
        try:
            self.settings.sync()
        except Exception:
            pass

    def apply_settings(self):
        """Apply settings without closing the dialog - ONLY saves to QSettings for new documents"""
        print("PREFERENCES: Saving settings to QSettings for new documents only")
        self.save_settings()
        # Emit signal to notify that preferences have been saved (but NOT applied to current document)
        self.preferences_changed.emit({})
        print("PREFERENCES: Settings saved to QSettings - will affect new documents only")
        
    def accept_settings(self):
        """Accept and save settings, then close dialog - ONLY saves to QSettings for new documents"""
        print("PREFERENCES: Saving settings to QSettings and closing dialog")
        self.save_settings()
        # Emit signal to notify that preferences have been saved (but NOT applied to current document)
        self.preferences_changed.emit({})
        # Close the dialog
        super().accept()

    def get_preference(self, key, default_value=None):
        """Get a preference value by key"""
        return self.settings.value(key, default_value)

    def setup_general_tab(self):
        """Set up the general preferences tab"""
        layout = QVBoxLayout(self.general_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Default score directory section
        dir_group = QGroupBox("Default Score Directory")
        dir_layout = QVBoxLayout(dir_group)
        
        # Directory path with browse button
        dir_path_layout = QHBoxLayout()
        self.score_dir = QLineEdit()
        self.score_dir.setReadOnly(True)
        self.score_dir.setPlaceholderText("ONOTE Music scores")
        # Set default path
        default_path = "/Users/gilidor/Library/Mobile Documents/com~apple~CloudDocs/QC-Projects/ONOTE Music scores"
        self.score_dir.setText(default_path)
        
        dir_browse_btn = QPushButton("Browse...")
        dir_browse_btn.setMinimumWidth(100)
        dir_browse_btn.clicked.connect(self.browse_score_directory)
        
        dir_path_layout.addWidget(self.score_dir)
        dir_path_layout.addWidget(dir_browse_btn)
        dir_layout.addLayout(dir_path_layout)
        
        # Add description
        dir_desc = QLabel("Choose the default directory where new scores will be saved and where the Open dialog will start.")
        dir_desc.setStyleSheet("color: gray; font-size: 11px;")
        dir_desc.setWordWrap(True)
        dir_layout.addWidget(dir_desc)
        
        layout.addWidget(dir_group)
        
        # View and Interface section
        view_group = QGroupBox("View and Interface")
        view_layout = QFormLayout(view_group)
        view_layout.setSpacing(10)
        
        # Default view mode - Updated options
        self.view_mode = QComboBox()
        self.view_mode.addItems(["Pages Down", "Pages Across", "Continuous"])
        self.view_mode.setCurrentText("Pages Down")
        self.view_mode.setMinimumWidth(200)
        view_layout.addRow("Default View:", self.view_mode)
        
        # Auto-save interval
        self.autosave = QSpinBox()
        self.autosave.setRange(1, 60)
        self.autosave.setValue(5)
        self.autosave.setSuffix(" minutes")
        self.autosave.setMinimumWidth(200)
        view_layout.addRow("Auto-save Interval:", self.autosave)
        
        # Zoom level
        self.default_zoom = QComboBox()
        self.default_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.default_zoom.setCurrentText("100%")
        self.default_zoom.setMinimumWidth(200)
        view_layout.addRow("Default Zoom:", self.default_zoom)
        
        # Show rulers
        self.show_rulers = QCheckBox("Show rulers by default")
        self.show_rulers.setChecked(True)
        view_layout.addRow("", self.show_rulers)
        
        # Show grid
        self.show_grid = QCheckBox("Show grid in edit mode")
        self.show_grid.setChecked(False)
        view_layout.addRow("", self.show_grid)
        
        layout.addWidget(view_group)
        
        # File Management section  
        file_group = QGroupBox("File Management")
        file_layout = QFormLayout(file_group)
        file_layout.setSpacing(10)
        
        # Recent files count
        self.recent_files_count = QSpinBox()
        self.recent_files_count.setRange(1, 20)
        self.recent_files_count.setValue(10)
        self.recent_files_count.setMinimumWidth(200)
        file_layout.addRow("Recent Files Count:", self.recent_files_count)
        
        # Backup options
        self.create_backup = QCheckBox("Create backup files (.bak)")
        self.create_backup.setChecked(True)
        file_layout.addRow("", self.create_backup)
        
        self.auto_backup = QCheckBox("Auto-backup to external drive when available")
        self.auto_backup.setChecked(True)
        file_layout.addRow("", self.auto_backup)
        
        layout.addWidget(file_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
    def setup_layout_tab(self):
        """Set up the layout and page preferences tab with compact 2-column layout"""
        layout = QVBoxLayout(self.layout_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create main horizontal layout for 2 columns
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(15)
        
        # LEFT COLUMN
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        # Default Page Setup section
        page_group = QGroupBox("Default Page Setup")
        page_layout = QFormLayout(page_group)
        page_layout.setSpacing(6)
        
        # Page size
        self.default_page_size = QComboBox()
        self.default_page_size.addItems([
            "A4 (210 × 297 mm)",
            "A3 (297 × 420 mm)", 
            "Letter (8.5 × 11 in)",
            "Legal (8.5 × 14 in)",
            "Tabloid (11 × 17 in)"
        ])
        self.default_page_size.setCurrentText("A4 (210 × 297 mm)")
        self.default_page_size.setMinimumWidth(160)
        self.default_page_size.currentTextChanged.connect(self._mark_dirty)
        page_layout.addRow("Page Size:", self.default_page_size)

        # Default Zoom (%) for new documents (also available on General tab)
        from PyQt6.QtWidgets import QSpinBox
        self.default_zoom_spin = QSpinBox()
        self.default_zoom_spin.setRange(25, 400)
        self.default_zoom_spin.setSuffix("%")
        # Initialize from Preferences; fallback to 100%
        try:
            dz_value = self.settings.value("general/default_zoom", "100%")
            if isinstance(dz_value, str) and dz_value.endswith('%'):
                dz_int = int(float(dz_value.strip('%')))
            else:
                dz_int = int(float(dz_value))
        except Exception:
            dz_int = 100
        self.default_zoom_spin.setValue(dz_int)
        # Mark dialog dirty on change
        self.default_zoom_spin.valueChanged.connect(self._mark_dirty)
        page_layout.addRow("Default Zoom (%):", self.default_zoom_spin)
        
        # Page orientation
        self.default_orientation = QComboBox()
        self.default_orientation.addItems(["Portrait", "Landscape"])
        self.default_orientation.setCurrentText("Portrait")
        self.default_orientation.setMinimumWidth(160)
        self.default_orientation.currentTextChanged.connect(self._mark_dirty)
        page_layout.addRow("Orientation:", self.default_orientation)
        
        left_column.addWidget(page_group)
        
        # Margins (compact layout)
        margins_group = QGroupBox("Default Margins")
        margins_layout = QFormLayout(margins_group)
        margins_layout.setSpacing(4)
        
        self.default_top_margin = QDoubleSpinBox()
        self.default_top_margin.setRange(0.0, 100.0)
        self.default_top_margin.setValue(20.0)
        self.default_top_margin.setSuffix(" mm")
        self.default_top_margin.setMinimumWidth(80)
        margins_layout.addRow("Top:", self.default_top_margin)
        self.default_top_margin.valueChanged.connect(self._mark_dirty)
        
        self.default_bottom_margin = QDoubleSpinBox()
        self.default_bottom_margin.setRange(0.0, 100.0)
        self.default_bottom_margin.setValue(20.0)
        self.default_bottom_margin.setSuffix(" mm")
        self.default_bottom_margin.setMinimumWidth(80)
        margins_layout.addRow("Bottom:", self.default_bottom_margin)
        self.default_bottom_margin.valueChanged.connect(self._mark_dirty)
        
        self.default_left_margin = QDoubleSpinBox()
        self.default_left_margin.setRange(0.0, 100.0)
        self.default_left_margin.setValue(25.0)
        self.default_left_margin.setSuffix(" mm")
        self.default_left_margin.setMinimumWidth(80)
        margins_layout.addRow("Left:", self.default_left_margin)
        self.default_left_margin.valueChanged.connect(self._mark_dirty)
        
        self.default_right_margin = QDoubleSpinBox()
        self.default_right_margin.setRange(0.0, 100.0)
        self.default_right_margin.setValue(25.0)
        self.default_right_margin.setSuffix(" mm")
        self.default_right_margin.setMinimumWidth(80)
        margins_layout.addRow("Right:", self.default_right_margin)
        self.default_right_margin.valueChanged.connect(self._mark_dirty)
        
        left_column.addWidget(margins_group)
        
        # Score Layout section
        score_layout_group = QGroupBox("Default Score Layout")
        score_layout_layout = QFormLayout(score_layout_group)
        score_layout_layout.setSpacing(6)
        
        # Staff spacing
        self.default_staff_spacing = QSpinBox()
        self.default_staff_spacing.setRange(20, 100)
        self.default_staff_spacing.setValue(40)
        self.default_staff_spacing.setSuffix(" px")
        self.default_staff_spacing.setMinimumWidth(120)
        score_layout_layout.addRow("Staff Spacing:", self.default_staff_spacing)
        self.default_staff_spacing.valueChanged.connect(self._mark_dirty)
        
        # Grand Staff spacing (min internal gap for piano brace)
        self.default_grand_staff_spacing = QSpinBox()
        self.default_grand_staff_spacing.setRange(8, 160)
        self.default_grand_staff_spacing.setValue(32)
        self.default_grand_staff_spacing.setSuffix(" px")
        self.default_grand_staff_spacing.setMinimumWidth(120)
        score_layout_layout.addRow("Grand Staff Spacing:", self.default_grand_staff_spacing)
        self.default_grand_staff_spacing.valueChanged.connect(self._mark_dirty)

        # System spacing
        self.default_system_spacing = QSpinBox()
        self.default_system_spacing.setRange(40, 200)
        self.default_system_spacing.setValue(80)
        self.default_system_spacing.setSuffix(" px")
        self.default_system_spacing.setMinimumWidth(120)
        score_layout_layout.addRow("System Spacing:", self.default_system_spacing)
        self.default_system_spacing.valueChanged.connect(self._mark_dirty)
        
        # Measures per system
        self.default_measures_per_system = QSpinBox()
        self.default_measures_per_system.setRange(1, 8)
        self.default_measures_per_system.setValue(4)
        self.default_measures_per_system.setMinimumWidth(120)
        score_layout_layout.addRow("Measures/System:", self.default_measures_per_system)
        self.default_measures_per_system.valueChanged.connect(self._mark_dirty)

        # Initial MPS (auto-fill first system on entering Edit)
        from PyQt6.QtWidgets import QCheckBox
        self.initial_mps_enabled = QCheckBox("Initial MPS (auto-fill first system on enter Edit)")
        self.initial_mps_enabled.setChecked(True)
        score_layout_layout.addRow("Initial MPS:", self.initial_mps_enabled)
        self.initial_mps_enabled.toggled.connect(self._mark_dirty)
        # Persist immediately so new scores honor the toggle without reopening Preferences
        def _immediate_save_initial_mps(checked):
            try:
                self.settings.setValue("layout/initial_mps_enabled", bool(checked))
            except Exception:
                pass
        self.initial_mps_enabled.toggled.connect(_immediate_save_initial_mps)
        
        # Notation size
        self.default_notation_size = QDoubleSpinBox()
        self.default_notation_size.setRange(0.5, 3.0)
        self.default_notation_size.setValue(1.0)
        self.default_notation_size.setSingleStep(0.1)
        self.default_notation_size.setSuffix("x")
        self.default_notation_size.setMinimumWidth(120)
        score_layout_layout.addRow("Notation Scale:", self.default_notation_size)
        self.default_notation_size.valueChanged.connect(self._mark_dirty)
        
        left_column.addWidget(score_layout_group)
        
        # RIGHT COLUMN
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Layout Settings section (moved from form widget)
        layout_settings_group = QGroupBox("Layout Settings")
        layout_settings_layout = QVBoxLayout(layout_settings_group)
        layout_settings_layout.setSpacing(8)
        
        # Auto justify checkbox
        self.auto_justify = QCheckBox("Auto-justify measures")
        self.auto_justify.setChecked(True)
        self.auto_justify.setToolTip("Automatically justify measures across the system width")
        layout_settings_layout.addWidget(self.auto_justify)
        self.auto_justify.toggled.connect(self._mark_dirty)
        
        # Dynamic width checkbox
        self.dynamic_width = QCheckBox("Dynamic measure width")
        self.dynamic_width.setChecked(True)
        self.dynamic_width.setToolTip("Allow measures to adjust width based on content")
        layout_settings_layout.addWidget(self.dynamic_width)
        self.dynamic_width.toggled.connect(self._mark_dirty)
        
        # Force break checkbox
        self.force_break = QCheckBox("Force system break")
        self.force_break.setChecked(False)
        self.force_break.setToolTip("Force a system break at this point")
        layout_settings_layout.addWidget(self.force_break)
        self.force_break.toggled.connect(self._mark_dirty)
        
        # Custom width checkbox and spin box
        custom_width_layout = QHBoxLayout()
        self.custom_width_enabled = QCheckBox("Custom measure width")
        self.custom_width_enabled.setChecked(False)
        self.custom_width_enabled.setToolTip("Use custom width for measures")
        custom_width_layout.addWidget(self.custom_width_enabled)
        
        self.custom_width_value = QSpinBox()
        self.custom_width_value.setRange(50, 500)
        self.custom_width_value.setValue(100)
        self.custom_width_value.setSuffix(" px")
        self.custom_width_value.setEnabled(False)  # Initially disabled
        self.custom_width_value.setMinimumWidth(80)
        custom_width_layout.addWidget(self.custom_width_value)
        custom_width_layout.addStretch()
        
        # Connect custom width checkbox to enable/disable spin box
        self.custom_width_enabled.toggled.connect(self.custom_width_value.setEnabled)
        self.custom_width_enabled.toggled.connect(self._mark_dirty)
        self.custom_width_value.valueChanged.connect(self._mark_dirty)
        
        layout_settings_layout.addLayout(custom_width_layout)
        
        # Truncate empty measures checkbox
        self.truncate_empty = QCheckBox("Truncate empty measures after end bar")
        self.truncate_empty.setChecked(False)
        self.truncate_empty.setToolTip("Remove empty measures that appear after the final barline")
        layout_settings_layout.addWidget(self.truncate_empty)
        self.truncate_empty.toggled.connect(self._mark_dirty)
        
        right_column.addWidget(layout_settings_group)
        
        # Display Options section
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(6)
        
        self.show_staff_names = QCheckBox("Show staff names by default")
        self.show_staff_names.setChecked(True)
        display_layout.addWidget(self.show_staff_names)
        
        self.show_page_numbers = QCheckBox("Show page numbers by default")
        self.show_page_numbers.setChecked(True)
        display_layout.addWidget(self.show_page_numbers)
        
        self.justify_last_system = QCheckBox("Justify measures in last system")
        self.justify_last_system.setChecked(False)
        display_layout.addWidget(self.justify_last_system)
        
        self.hide_empty_staves = QCheckBox("Hide empty staves by default")
        self.hide_empty_staves.setChecked(False)
        display_layout.addWidget(self.hide_empty_staves)
        
        right_column.addWidget(display_group)
        
        # Print Quality section
        print_group = QGroupBox("Print Settings")
        print_layout = QFormLayout(print_group)
        print_layout.setSpacing(6)
        
        self.default_print_quality = QComboBox()
        self.default_print_quality.addItems(["Draft", "Normal", "High", "Best"])
        self.default_print_quality.setCurrentText("Normal")
        self.default_print_quality.setMinimumWidth(120)
        print_layout.addRow("Quality:", self.default_print_quality)
        
        self.default_print_resolution = QComboBox()
        self.default_print_resolution.addItems(["300 DPI", "600 DPI", "1200 DPI"])
        self.default_print_resolution.setCurrentText("600 DPI")
        self.default_print_resolution.setMinimumWidth(120)
        print_layout.addRow("Resolution:", self.default_print_resolution)
        
        right_column.addWidget(print_group)
        
        # Add columns to main horizontal layout
        main_h_layout.addLayout(left_column, 1)
        main_h_layout.addLayout(right_column, 1)
        
        layout.addLayout(main_h_layout)
        layout.addStretch()
    
    def on_measure_numbers_frequency_changed(self, text):
        """Show/hide custom interval controls based on frequency selection"""
        is_custom = text == "Custom Interval"
        self.measure_numbers_custom_interval.setVisible(is_custom)
        # Find the label widget and set its visibility too
        for i in range(self.measure_numbers_custom_interval.parent().layout().count()):
            item = self.measure_numbers_custom_interval.parent().layout().itemAt(i)
            if hasattr(item, 'widget') and item.widget() and hasattr(item.widget(), 'text'):
                if item.widget().text() == "Custom Interval:":
                    item.widget().setVisible(is_custom)
    
    def choose_font_color(self, category):
        """Open color picker dialog for font colors"""
        from PyQt6.QtWidgets import QColorDialog
        from PyQt6.QtCore import Qt
        
        # Get current color from button style
        current_color = Qt.GlobalColor.black
        if category == 'staff_names':
            button = self.staff_name_font_color
        elif category == 'section_names':
            button = self.section_name_font_color
        elif category == 'measure_numbers':
            button = self.measure_numbers_font_color
        elif category == 'barline_numbers':
            button = self.barline_number_font_color
        elif category == 'clef':
            button = self.clef_font_color
        elif category == 'time_sig':
            button = self.time_sig_font_color
        elif category == 'key_sig':
            button = self.key_sig_font_color
        else:
            return
        
        # Open color picker
        color = QColorDialog.getColor(current_color, self, f"Choose {category.replace('_', ' ').title()} Color")
        
        if color.isValid():
            # Update button appearance
            hex_color = color.name()
            # Choose contrasting text color
            text_color = "#FFFFFF" if self.is_dark_color(color) else "#000000"
            button.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")
            
            # Store the color value for saving
            setattr(self, f"{category}_color_value", hex_color)
    
    def is_dark_color(self, color):
        """Determine if a color is dark (for choosing contrasting text color)"""
        # Use luminance formula to determine if color is dark
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5
    
    def is_dark_color_hex(self, hex_color):
        """Determine if a hex color is dark (for choosing contrasting text color)"""
        # Convert hex to RGB values
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Use luminance formula to determine if color is dark
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return luminance < 0.5
    
    def setup_font_tab(self):
        """Set up the Font tab with font selection options (replicated from Full Score Options)"""
        layout = QHBoxLayout(self.font_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Left side - Categories list
        left_side = QVBoxLayout()
        left_side.setSpacing(10)
        
        # Categories label
        categories_label = QLabel("Text Categories:")
        categories_label.setStyleSheet("font-weight: bold; color: #333;")
        left_side.addWidget(categories_label)
        
        # Create scrollable list for categories
        self.font_categories_list = QListWidget()
        self.font_categories_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.font_categories_list.setMinimumHeight(300)
        
        # Add text categories including Measure Numbers
        categories = [
            "Staff Names", 
            "Measure Numbers",
            "Tempo Markings",
            "Dynamics",
            "Lyrics",
            "Chord Symbols",
            "Headers",
            "Footers",
            "Title",
            "Composer",
            "Subtitle",
            "System Text",
            "Staff Text",
            "Expression Text",
            "Rehearsal Marks"
        ]
        
        for category in categories:
            self.font_categories_list.addItem(category)
        
        # Select first item by default
        self.font_categories_list.setCurrentRow(0)
        
        # Connect selection signal
        self.font_categories_list.currentRowChanged.connect(self.on_font_category_selected)
        
        left_side.addWidget(self.font_categories_list)
        
        # Button layout for Create/Remove Category
        button_layout = QHBoxLayout()
        
        # Create Category button
        create_category_btn = QPushButton("Create Category")
        create_category_btn.clicked.connect(self.on_create_font_category)
        create_category_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(create_category_btn)
        
        # Remove Category button
        remove_category_btn = QPushButton("Remove Category")
        remove_category_btn.clicked.connect(self.on_remove_font_category)
        remove_category_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        button_layout.addWidget(remove_category_btn)
        
        left_side.addLayout(button_layout)
        
        # Right side - Font controls
        right_side = QVBoxLayout()
        right_side.setSpacing(15)
        
        # Font Name
        font_name_group = QGroupBox("Font Name")
        font_name_layout = QVBoxLayout(font_name_group)
        self.font_name_combo = QComboBox()
        self.font_name_combo.setMinimumHeight(28)
        
        # Add common font names
        font_names = [
            "Arial", 
            "Times New Roman", 
            "Helvetica", 
            "Courier New", 
            "Georgia", 
            "Verdana",
            "Palatino", 
            "Garamond", 
            "Bookman", 
            "Tahoma", 
            "Trebuchet MS",
            "Calibri",
            "Cambria",
            "Century Gothic",
            "Franklin Gothic Medium"
        ]
        self.font_name_combo.addItems(font_names)
        font_name_layout.addWidget(self.font_name_combo)
        right_side.addWidget(font_name_group)
        
        # Font Style
        style_group = QGroupBox("Style")
        style_layout = QVBoxLayout(style_group)
        self.font_style_combo = QComboBox()
        self.font_style_combo.setMinimumHeight(28)
        
        # Add font styles
        styles = [
            "Regular", 
            "Italic", 
            "SemiBold", 
            "SemiBold Italic", 
            "Bold", 
            "Bold Italic"
        ]
        self.font_style_combo.addItems(styles)
        style_layout.addWidget(self.font_style_combo)
        right_side.addWidget(style_group)
        
        # Font Size
        size_group = QGroupBox("Font Size")
        size_layout = QVBoxLayout(size_group)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(12)
        self.font_size_spin.setSuffix(" pt")
        self.font_size_spin.setMinimumHeight(28)
        size_layout.addWidget(self.font_size_spin)
        right_side.addWidget(size_group)
        
        # Use Defaults button
        self.use_defaults_check = QCheckBox("Use Default Font")
        self.use_defaults_check.toggled.connect(self.on_use_font_defaults_toggled)
        right_side.addWidget(self.use_defaults_check)
        
        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.font_preview_label = QLabel("Sample Text\nABCDEFG abcdefg\n1234567890")
        self.font_preview_label.setStyleSheet("""
            QLabel {
                background: white;
                border: 1px solid #ccc;
                padding: 10px;
                min-height: 60px;
                color: black;
            }
        """)
        self.font_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.font_preview_label)
        right_side.addWidget(preview_group)
        
        # Add spacing
        right_side.addStretch()
        
        # Add left and right layouts to main layout
        layout.addLayout(left_side, 1)
        layout.addLayout(right_side, 2)
        
        # Connect font change signals to update preview
        self.font_name_combo.currentTextChanged.connect(self.update_font_preview)
        self.font_style_combo.currentTextChanged.connect(self.update_font_preview)
        self.font_size_spin.valueChanged.connect(self.update_font_preview)
        
        # Initial preview update
        self.update_font_preview()
    
    def on_font_category_selected(self, row):
        """Handle font category selection from the list"""
        if row >= 0:
            category = self.font_categories_list.item(row).text()
            print(f"Selected font category: {category}")
            # Here you would load the font settings for the selected category
            # For now, just update the preview
            self.update_font_preview()
    
    def on_create_font_category(self):
        """Handle creating a new font category"""
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(self, 'Create Font Category', 'Enter category name:')
        if ok and text.strip():
            # Check if category already exists
            existing_categories = [self.font_categories_list.item(i).text() 
                                 for i in range(self.font_categories_list.count())]
            if text.strip() not in existing_categories:
                self.font_categories_list.addItem(text.strip())
                # Select the new category
                self.font_categories_list.setCurrentRow(self.font_categories_list.count() - 1)
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, 'Duplicate Category', 
                                  f'Category "{text.strip()}" already exists.')
    
    def on_remove_font_category(self):
        """Handle removing the selected font category"""
        current_row = self.font_categories_list.currentRow()
        if current_row >= 0:
            category_name = self.font_categories_list.item(current_row).text()
            
            # Don't allow removal of essential categories
            essential_categories = ["Staff Names", "Measure Numbers", "Tempo Markings", 
                                  "Dynamics", "Title", "Composer"]
            if category_name in essential_categories:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, 'Cannot Remove Category', 
                                  f'Cannot remove essential category "{category_name}".')
                return
            
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, 'Remove Category', 
                                       f'Are you sure you want to remove category "{category_name}"?',
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.font_categories_list.takeItem(current_row)
                # Select the previous item if available
                if current_row > 0:
                    self.font_categories_list.setCurrentRow(current_row - 1)
                elif self.font_categories_list.count() > 0:
                    self.font_categories_list.setCurrentRow(0)
    
    def on_use_font_defaults_toggled(self, checked):
        """Handle use defaults checkbox toggle"""
        self.font_name_combo.setEnabled(not checked)
        self.font_style_combo.setEnabled(not checked)
        self.font_size_spin.setEnabled(not checked)
        
        if checked:
            # Reset to defaults
            self.font_name_combo.setCurrentText("Arial")
            self.font_style_combo.setCurrentText("Regular")
            self.font_size_spin.setValue(12)
        
        self.update_font_preview()
    
    def update_font_preview(self):
        """Update the font preview label"""
        if hasattr(self, 'font_preview_label'):
            font_name = self.font_name_combo.currentText()
            font_size = self.font_size_spin.value()
            font_style = self.font_style_combo.currentText()
            
            # Create font style string
            weight = "normal"
            style = "normal"
            
            if "Bold" in font_style:
                weight = "bold"
            elif "SemiBold" in font_style:
                weight = "600"
                
            if "Italic" in font_style:
                style = "italic"
            
            if self.use_defaults_check.isChecked():
                style_str = "font-family: Arial; font-size: 12pt; font-weight: normal; font-style: normal; color: #888;"
            else:
                style_str = f"font-family: {font_name}; font-size: {font_size}pt; font-weight: {weight}; font-style: {style}; color: black;"
            
            self.font_preview_label.setStyleSheet(f"""
                QLabel {{
                    background: white;
                    border: 1px solid #ccc;
                    padding: 10px;
                    min-height: 60px;
                    {style_str}
                }}
            """)
    
    def setup_notation_tab(self):
        """Set up the default notation setup preferences tab with improved layout"""
        layout = QVBoxLayout(self.notation_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create main horizontal layout for 3 columns for better balance
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(15)
        
        # LEFT COLUMN - Text Elements
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        # Staff Name Settings
        staff_name_group = QGroupBox("Staff Names")
        staff_name_layout = QFormLayout(staff_name_group)
        staff_name_layout.setSpacing(6)
        
        # Font size
        self.staff_name_font_size = QSpinBox()
        self.staff_name_font_size.setRange(6, 24)
        self.staff_name_font_size.setValue(10)
        self.staff_name_font_size.setSuffix(" pt")
        self.staff_name_font_size.setMinimumWidth(80)
        self.staff_name_font_size.setToolTip("Font size for staff names")
        staff_name_layout.addRow("Font Size:", self.staff_name_font_size)
        
        # Vertical position
        self.staff_name_vertical = QSpinBox()
        self.staff_name_vertical.setRange(-50, 20)
        self.staff_name_vertical.setValue(-8)
        self.staff_name_vertical.setSuffix(" px")
        self.staff_name_vertical.setMinimumWidth(80)
        self.staff_name_vertical.setToolTip("Vertical offset (negative = above staff)")
        staff_name_layout.addRow("Vertical:", self.staff_name_vertical)
        
        # Horizontal position
        self.staff_name_horizontal = QSpinBox()
        self.staff_name_horizontal.setRange(-100, 0)
        self.staff_name_horizontal.setValue(-50)
        self.staff_name_horizontal.setSuffix(" px")
        self.staff_name_horizontal.setMinimumWidth(80)
        self.staff_name_horizontal.setToolTip("Horizontal offset (negative = left of staff)")
        staff_name_layout.addRow("Horizontal:", self.staff_name_horizontal)
        
        # Font Color
        self.staff_name_font_color = QPushButton("Choose Color")
        self.staff_name_font_color.setMinimumWidth(100)
        self.staff_name_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.staff_name_font_color.clicked.connect(lambda: self.choose_font_color('staff_names'))
        staff_name_layout.addRow("Font Color:", self.staff_name_font_color)
        
        left_column.addWidget(staff_name_group)
        
        # Section Name Settings
        section_name_group = QGroupBox("Section Names")
        section_name_layout = QFormLayout(section_name_group)
        section_name_layout.setSpacing(6)
        
        # Font size
        self.section_name_font_size = QSpinBox()
        self.section_name_font_size.setRange(8, 32)
        self.section_name_font_size.setValue(12)
        self.section_name_font_size.setSuffix(" pt")
        self.section_name_font_size.setMinimumWidth(80)
        self.section_name_font_size.setToolTip("Font size for section names")
        section_name_layout.addRow("Font Size:", self.section_name_font_size)
        
        # Vertical position
        self.section_name_vertical = QSpinBox()
        self.section_name_vertical.setRange(-60, 10)
        self.section_name_vertical.setValue(-25)
        self.section_name_vertical.setSuffix(" px")
        self.section_name_vertical.setMinimumWidth(80)
        self.section_name_vertical.setToolTip("Vertical offset (negative = above staff group)")
        section_name_layout.addRow("Vertical:", self.section_name_vertical)
        
        # Horizontal position
        self.section_name_horizontal = QSpinBox()
        self.section_name_horizontal.setRange(-120, 0)
        self.section_name_horizontal.setValue(-60)
        self.section_name_horizontal.setSuffix(" px")
        self.section_name_horizontal.setMinimumWidth(80)
        self.section_name_horizontal.setToolTip("Horizontal offset (negative = left of staff)")
        section_name_layout.addRow("Horizontal:", self.section_name_horizontal)
        
        # Font Color
        self.section_name_font_color = QPushButton("Choose Color")
        self.section_name_font_color.setMinimumWidth(100)
        self.section_name_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.section_name_font_color.clicked.connect(lambda: self.choose_font_color('section_names'))
        section_name_layout.addRow("Font Color:", self.section_name_font_color)
        
        left_column.addWidget(section_name_group)
        
        # Musical Directions Settings
        directions_group = QGroupBox("Musical Directions")
        directions_layout = QFormLayout(directions_group)
        directions_layout.setSpacing(6)
        
        # Font size for directions
        self.directions_font_size = QSpinBox()
        self.directions_font_size.setRange(8, 18)
        self.directions_font_size.setValue(11)
        self.directions_font_size.setSuffix(" pt")
        self.directions_font_size.setMinimumWidth(80)
        self.directions_font_size.setToolTip("Font size for musical directions")
        directions_layout.addRow("Font Size:", self.directions_font_size)
        
        # Vertical position
        self.directions_vertical = QSpinBox()
        self.directions_vertical.setRange(10, 60)
        self.directions_vertical.setValue(30)
        self.directions_vertical.setSuffix(" px")
        self.directions_vertical.setMinimumWidth(80)
        self.directions_vertical.setToolTip("Distance below staff")
        directions_layout.addRow("Vertical:", self.directions_vertical)
        
        # Horizontal position
        self.directions_horizontal = QSpinBox()
        self.directions_horizontal.setRange(-50, 50)
        self.directions_horizontal.setValue(0)
        self.directions_horizontal.setSuffix(" px")
        self.directions_horizontal.setMinimumWidth(80)
        self.directions_horizontal.setToolTip("Horizontal offset from center")
        directions_layout.addRow("Horizontal:", self.directions_horizontal)
        
        left_column.addWidget(directions_group)
        
        # MIDDLE COLUMN - Notation Elements
        middle_column = QVBoxLayout()
        middle_column.setSpacing(10)
        
        # Clef Settings
        clef_group = QGroupBox("Clefs")
        clef_layout = QFormLayout(clef_group)
        clef_layout.setSpacing(6)
        
        # Font size for clefs
        self.clef_font_size = QSpinBox()
        self.clef_font_size.setRange(16, 48)
        self.clef_font_size.setValue(32)
        self.clef_font_size.setSuffix(" pt")
        self.clef_font_size.setMinimumWidth(80)
        self.clef_font_size.setToolTip("Size of clef symbols")
        clef_layout.addRow("Font Size:", self.clef_font_size)
        
        # Vertical position
        self.clef_vertical = QSpinBox()
        self.clef_vertical.setRange(-20, 20)
        self.clef_vertical.setValue(0)
        self.clef_vertical.setSuffix(" px")
        self.clef_vertical.setMinimumWidth(80)
        self.clef_vertical.setToolTip("Vertical adjustment from standard position")
        clef_layout.addRow("Vertical:", self.clef_vertical)
        
        # Horizontal position
        self.clef_horizontal = QSpinBox()
        self.clef_horizontal.setRange(-500, 2000)
        self.clef_horizontal.setValue(20)
        self.clef_horizontal.setSuffix(" px")
        self.clef_horizontal.setMinimumWidth(80)
        self.clef_horizontal.setToolTip("Distance from left margin")
        clef_layout.addRow("Horizontal:", self.clef_horizontal)
        
        # Font Color
        self.clef_font_color = QPushButton("Choose Color")
        self.clef_font_color.setMinimumWidth(100)
        self.clef_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.clef_font_color.clicked.connect(lambda: self.choose_font_color('clef'))
        self.clef_font_color.setEnabled(True)  # Ensure it's enabled
        clef_layout.addRow("Font Color:", self.clef_font_color)
        
        middle_column.addWidget(clef_group)
        
        # Time Signature Settings
        time_sig_group = QGroupBox("Time Signature")
        time_sig_layout = QFormLayout(time_sig_group)
        time_sig_layout.setSpacing(6)
        
        # Font size
        self.time_sig_font_size = QSpinBox()
        self.time_sig_font_size.setRange(12, 48)
        self.time_sig_font_size.setValue(24)
        self.time_sig_font_size.setSuffix(" pt")
        self.time_sig_font_size.setMinimumWidth(80)
        self.time_sig_font_size.setToolTip("Font size for time signature")
        time_sig_layout.addRow("Font Size:", self.time_sig_font_size)
        
        # Vertical position
        self.time_sig_vertical = QSpinBox()
        self.time_sig_vertical.setRange(-20, 20)
        self.time_sig_vertical.setValue(0)
        self.time_sig_vertical.setSuffix(" px")
        self.time_sig_vertical.setMinimumWidth(80)
        self.time_sig_vertical.setToolTip("Vertical offset (0 = centered on staff)")
        time_sig_layout.addRow("Vertical:", self.time_sig_vertical)
        
        # Horizontal position
        self.time_sig_horizontal = QSpinBox()
        self.time_sig_horizontal.setRange(-500, 2000)
        self.time_sig_horizontal.setValue(40)
        self.time_sig_horizontal.setSuffix(" px")
        self.time_sig_horizontal.setMinimumWidth(80)
        self.time_sig_horizontal.setToolTip("Distance from left margin")
        time_sig_layout.addRow("Horizontal:", self.time_sig_horizontal)
        
        # Spacing between numerator and denominator
        self.time_sig_spacing = QSpinBox()
        self.time_sig_spacing.setRange(10, 30)
        self.time_sig_spacing.setValue(18)
        self.time_sig_spacing.setSuffix(" px")
        self.time_sig_spacing.setMinimumWidth(80)
        self.time_sig_spacing.setToolTip("Vertical spacing between numerator and denominator")
        time_sig_layout.addRow("Spacing:", self.time_sig_spacing)
        
        # Font Color
        self.time_sig_font_color = QPushButton("Choose Color")
        self.time_sig_font_color.setMinimumWidth(100)
        self.time_sig_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.time_sig_font_color.clicked.connect(lambda: self.choose_font_color('time_sig'))
        self.time_sig_font_color.setEnabled(True)  # Ensure it's enabled
        time_sig_layout.addRow("Font Color:", self.time_sig_font_color)
        
        middle_column.addWidget(time_sig_group)
        
        # Key Signature Settings
        key_sig_group = QGroupBox("Key Signature")
        key_sig_layout = QFormLayout(key_sig_group)
        key_sig_layout.setSpacing(6)
        
        # Font size
        self.key_sig_font_size = QSpinBox()
        self.key_sig_font_size.setRange(10, 24)
        self.key_sig_font_size.setValue(14)
        self.key_sig_font_size.setSuffix(" pt")
        self.key_sig_font_size.setMinimumWidth(80)
        self.key_sig_font_size.setToolTip("Font size for key signature")
        key_sig_layout.addRow("Font Size:", self.key_sig_font_size)
        
        # Vertical position
        self.key_sig_vertical = QSpinBox()
        self.key_sig_vertical.setRange(-15, 15)
        self.key_sig_vertical.setValue(0)
        self.key_sig_vertical.setSuffix(" px")
        self.key_sig_vertical.setMinimumWidth(80)
        self.key_sig_vertical.setToolTip("Vertical offset (0 = centered on staff)")
        key_sig_layout.addRow("Vertical:", self.key_sig_vertical)
        
        # Horizontal position
        self.key_sig_horizontal = QSpinBox()
        self.key_sig_horizontal.setRange(60, 120)
        self.key_sig_horizontal.setValue(75)
        self.key_sig_horizontal.setSuffix(" px")
        self.key_sig_horizontal.setMinimumWidth(80)
        self.key_sig_horizontal.setToolTip("Distance from left margin (after time signature)")
        key_sig_layout.addRow("Horizontal:", self.key_sig_horizontal)
        
        # Accidental spacing
        self.key_sig_accidental_spacing = QSpinBox()
        self.key_sig_accidental_spacing.setRange(8, 20)
        self.key_sig_accidental_spacing.setValue(12)
        self.key_sig_accidental_spacing.setSuffix(" px")
        self.key_sig_accidental_spacing.setMinimumWidth(80)
        self.key_sig_accidental_spacing.setToolTip("Horizontal spacing between accidentals")
        key_sig_layout.addRow("Spacing:", self.key_sig_accidental_spacing)
        
        # Font Color
        self.key_sig_font_color = QPushButton("Choose Color")
        self.key_sig_font_color.setMinimumWidth(100)
        self.key_sig_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.key_sig_font_color.clicked.connect(lambda: self.choose_font_color('key_sig'))
        self.key_sig_font_color.setEnabled(True)  # Ensure it's enabled
        key_sig_layout.addRow("Font Color:", self.key_sig_font_color)
        
        middle_column.addWidget(key_sig_group)
        
        # RIGHT COLUMN - Measure Numbers and Barlines
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Measure Numbers Settings
        measure_numbers_group = QGroupBox("Measure Numbers (New Documents Only)")
        measure_numbers_layout = QFormLayout(measure_numbers_group)
        measure_numbers_layout.setSpacing(6)
        
        # Note about current document settings
        note_label = QLabel("Note: For current document settings, use the Musical Form widget.")
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #666; font-style: italic; font-size: 9pt;")
        measure_numbers_layout.addRow("", note_label)
        
        # Enable measure numbers
        self.show_measure_numbers = QCheckBox("Show by default")
        self.show_measure_numbers.setChecked(True)
        self.show_measure_numbers.setToolTip("Show measure numbers by default in new scores")
        measure_numbers_layout.addRow("", self.show_measure_numbers)
        
        # Frequency dropdown
        self.measure_numbers_frequency = QComboBox()
        self.measure_numbers_frequency.addItems([
            "None", "Every System", "Every Measure", "Every 2 Measures", 
            "Every 5 Measures", "Every 10 Measures", "Custom Interval"
        ])
        self.measure_numbers_frequency.setCurrentText("Every Measure")
        self.measure_numbers_frequency.setMinimumWidth(140)
        self.measure_numbers_frequency.setToolTip("How frequently to show measure numbers")
        measure_numbers_layout.addRow("Frequency:", self.measure_numbers_frequency)
        
        # Custom interval (only visible when Custom Interval is selected)
        self.measure_numbers_custom_interval = QSpinBox()
        self.measure_numbers_custom_interval.setRange(2, 50)
        self.measure_numbers_custom_interval.setValue(5)
        self.measure_numbers_custom_interval.setMinimumWidth(140)
        self.measure_numbers_custom_interval.setVisible(False)
        self.measure_numbers_custom_interval.setToolTip("Custom interval for measure numbers")
        measure_numbers_layout.addRow("Custom Interval:", self.measure_numbers_custom_interval)
        
        # Position dropdown
        self.measure_numbers_position = QComboBox()
        self.measure_numbers_position.addItems(["Beginning", "Center", "End"])
        self.measure_numbers_position.setCurrentText("Center")
        self.measure_numbers_position.setMinimumWidth(140)
        self.measure_numbers_position.setToolTip("Position within the measure")
        measure_numbers_layout.addRow("Position:", self.measure_numbers_position)
        
        # Vertical position dropdown
        self.measure_numbers_vertical = QComboBox()
        self.measure_numbers_vertical.addItems([
            "Above Staff", "Above System", "Below Staff", "Below System"
        ])
        self.measure_numbers_vertical.setCurrentText("Above System")
        self.measure_numbers_vertical.setMinimumWidth(140)
        self.measure_numbers_vertical.setToolTip("Vertical position relative to staff")
        measure_numbers_layout.addRow("Vertical:", self.measure_numbers_vertical)
        
        # Font size
        self.measure_numbers_font_size = QSpinBox()
        self.measure_numbers_font_size.setRange(6, 18)
        self.measure_numbers_font_size.setValue(10)
        self.measure_numbers_font_size.setSuffix(" pt")
        self.measure_numbers_font_size.setMinimumWidth(100)
        self.measure_numbers_font_size.setToolTip("Font size for measure numbers")
        measure_numbers_layout.addRow("Font Size:", self.measure_numbers_font_size)
        
        # Pixel-perfect positioning controls
        self.measure_numbers_vertical_offset = QSpinBox()
        self.measure_numbers_vertical_offset.setRange(-100, 50)
        self.measure_numbers_vertical_offset.setValue(-20)
        self.measure_numbers_vertical_offset.setSuffix(" px")
        self.measure_numbers_vertical_offset.setMinimumWidth(100)
        self.measure_numbers_vertical_offset.setToolTip("Fine vertical adjustment (negative = above)")
        measure_numbers_layout.addRow("Vertical Offset:", self.measure_numbers_vertical_offset)
        
        self.measure_numbers_horizontal_offset = QSpinBox()
        self.measure_numbers_horizontal_offset.setRange(-200, 100)
        self.measure_numbers_horizontal_offset.setValue(-34)
        self.measure_numbers_horizontal_offset.setSuffix(" px")
        self.measure_numbers_horizontal_offset.setMinimumWidth(100)
        self.measure_numbers_horizontal_offset.setToolTip("Fine horizontal adjustment")
        measure_numbers_layout.addRow("Horizontal Offset:", self.measure_numbers_horizontal_offset)
        
        # Font Color
        self.measure_numbers_font_color = QPushButton("Choose Color")
        self.measure_numbers_font_color.setMinimumWidth(100)
        self.measure_numbers_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.measure_numbers_font_color.clicked.connect(lambda: self.choose_font_color('measure_numbers'))
        measure_numbers_layout.addRow("Font Color:", self.measure_numbers_font_color)
        
        right_column.addWidget(measure_numbers_group)
        
        # Barline Control Settings
        barline_group = QGroupBox("Barline Control (New Documents Only)")
        barline_layout = QFormLayout(barline_group)
        barline_layout.setSpacing(6)
        
        # Note about current document settings
        note_label2 = QLabel("Note: For current document settings, use the Musical Form widget.")
        note_label2.setWordWrap(True)
        note_label2.setStyleSheet("color: #666; font-style: italic; font-size: 9pt;")
        barline_layout.addRow("", note_label2)
        
        # Maximum measures per system
        self.max_measures_per_system = QSpinBox()
        self.max_measures_per_system.setRange(1, 16)
        self.max_measures_per_system.setValue(8)
        self.max_measures_per_system.setMinimumWidth(80)
        self.max_measures_per_system.setToolTip("Maximum number of measures per system")
        barline_layout.addRow("Max Measures/System:", self.max_measures_per_system)
        
        # Barline numbering
        self.barline_numbering = QCheckBox("Show barline numbers")
        self.barline_numbering.setChecked(False)
        self.barline_numbering.setToolTip("Show small numbers on barlines for debugging")
        barline_layout.addRow("", self.barline_numbering)
        
        # Barline number font size
        self.barline_number_font_size = QSpinBox()
        self.barline_number_font_size.setRange(6, 16)
        self.barline_number_font_size.setValue(8)
        self.barline_number_font_size.setSuffix(" pt")
        self.barline_number_font_size.setMinimumWidth(80)
        self.barline_number_font_size.setToolTip("Font size for barline numbers")
        barline_layout.addRow("Barline Number Size:", self.barline_number_font_size)
        
        # Barline Number Vertical Offset (NEW)
        self.barline_number_vertical_offset = QSpinBox()
        self.barline_number_vertical_offset.setRange(-100, 100)
        self.barline_number_vertical_offset.setValue(0)
        self.barline_number_vertical_offset.setSuffix(" px")
        self.barline_number_vertical_offset.setMinimumWidth(80)
        self.barline_number_vertical_offset.setToolTip("Vertical offset for barline numbers (negative = above)")
        barline_layout.addRow("Vertical Offset:", self.barline_number_vertical_offset)
        
        # Barline Number Horizontal Offset (NEW)
        self.barline_number_horizontal_offset = QSpinBox()
        self.barline_number_horizontal_offset.setRange(-50, 50)
        self.barline_number_horizontal_offset.setValue(3)
        self.barline_number_horizontal_offset.setSuffix(" px")
        self.barline_number_horizontal_offset.setMinimumWidth(80)
        self.barline_number_horizontal_offset.setToolTip("Horizontal offset for barline numbers")
        barline_layout.addRow("Horizontal Offset:", self.barline_number_horizontal_offset)
        
        # Barline Number Color
        self.barline_number_font_color = QPushButton("Choose Color")
        self.barline_number_font_color.setMinimumWidth(100)
        self.barline_number_font_color.setStyleSheet("background-color: #666666; color: white;")
        self.barline_number_font_color.clicked.connect(lambda: self.choose_font_color('barline_numbers'))
        barline_layout.addRow("Barline Number Color:", self.barline_number_font_color)
        
        right_column.addWidget(barline_group)
        
        # Add columns to main horizontal layout
        main_h_layout.addLayout(left_column, 1)
        main_h_layout.addLayout(middle_column, 1)
        main_h_layout.addLayout(right_column, 1)
        
        layout.addLayout(main_h_layout)
        
        # Bottom section with preview and reset button
        bottom_section = QVBoxLayout()
        bottom_section.setSpacing(10)
        
        # Preview note
        preview_note = QLabel("These are the default settings for new documents. Use 'Full Score Options' to modify settings for the current document.")
        preview_note.setStyleSheet("color: #666; font-size: 11px; font-style: italic;")
        preview_note.setWordWrap(True)
        preview_note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_section.addWidget(preview_note)
        
        # Reset to defaults button
        reset_btn = QPushButton("Reset All to Defaults")
        reset_btn.setMaximumWidth(200)
        reset_btn.clicked.connect(self.reset_notation_defaults)
        bottom_section.addWidget(reset_btn)
        
        layout.addLayout(bottom_section)
        layout.addStretch()
    
    def reset_notation_defaults(self):
        """Reset all notation settings to factory defaults (same as Full Score Options reset)"""
        # CRITICAL FIX: Use consistent attribute names with Full Score Options dialog
        # and reset to proper factory defaults instead of arbitrary values
        
        # Staff name defaults
        self.staff_name_font_size.setValue(10)
        self.staff_name_vertical.setValue(-8)
        self.staff_name_horizontal.setValue(0)  # Consistent with Full Score Options
        staff_name_color = "#000000"
        self.staff_name_font_color.setStyleSheet(f"background-color: {staff_name_color}; color: white;")
        self.staff_names_color_value = staff_name_color  # Keep this for backward compatibility
        
        # Section name defaults
        self.section_name_font_size.setValue(10)  # Consistent with Full Score Options
        self.section_name_vertical.setValue(0)   # Consistent with Full Score Options
        self.section_name_horizontal.setValue(0)  # Consistent with Full Score Options
        section_name_color = "#000000"
        self.section_name_font_color.setStyleSheet(f"background-color: {section_name_color}; color: white;")
        self.section_names_color_value = section_name_color  # Keep this for backward compatibility
        
        # Time signature defaults
        self.time_sig_font_size.setValue(24)
        self.time_sig_vertical.setValue(0)
        self.time_sig_horizontal.setValue(40)
        self.time_sig_spacing.setValue(18)
        self.time_sig_color_value = "#000000"
        self.time_sig_font_color.setStyleSheet(f"background-color: {self.time_sig_color_value}; color: white;")
        
        # Key signature defaults
        self.key_sig_font_size.setValue(14)
        self.key_sig_vertical.setValue(0)
        self.key_sig_horizontal.setValue(75)
        self.key_sig_accidental_spacing.setValue(12)
        self.key_sig_color_value = "#000000"
        self.key_sig_font_color.setStyleSheet(f"background-color: {self.key_sig_color_value}; color: white;")
        
        # Clef defaults
        self.clef_font_size.setValue(32)
        self.clef_vertical.setValue(0)
        self.clef_horizontal.setValue(20)
        self.clef_color_value = "#000000"
        self.clef_font_color.setStyleSheet(f"background-color: {self.clef_color_value}; color: white;")
        
        # Musical directions defaults
        self.directions_font_size.setValue(10)  # Consistent with Full Score Options
        self.directions_vertical.setValue(0)    # Consistent with Full Score Options
        self.directions_horizontal.setValue(0)  # Consistent with Full Score Options
        
        # Measure numbers defaults (moved from Layout tab)
        self.show_measure_numbers.setChecked(True)
        self.measure_numbers_frequency.setCurrentText("Every Measure")
        self.measure_numbers_custom_interval.setValue(5)
        self.measure_numbers_position.setCurrentText("Center")
        self.measure_numbers_vertical.setCurrentText("Above System")
        self.measure_numbers_vertical_offset.setValue(25)  # More reasonable default
        self.measure_numbers_horizontal_offset.setValue(0)  # Centered by default
        self.measure_numbers_font_size.setValue(9)  # Smaller, less intrusive
        measure_numbers_color = "#e8161a"  # Default red color
        self.measure_numbers_font_color.setStyleSheet(f"background-color: {measure_numbers_color}; color: white;")
        self.measure_numbers_color_value = measure_numbers_color
        
        # Barline control defaults
        self.max_measures_per_system.setValue(5)  # More reasonable default than 8
        self.barline_numbering.setChecked(False)
        self.barline_number_font_size.setValue(8)
        barline_numbers_color = "#229c00"  # Default green color
        self.barline_numbers_font_color.setStyleSheet(f"background-color: {barline_numbers_color}; color: white;")
        self.barline_numbers_color_value = barline_numbers_color
        
        print("PREFERENCES: Reset all notation settings to factory defaults")

    def load_from_full_score_options(self, full_score_dialog):
        """Load settings from Full Score Options dialog when 'Set as Defaults' is used"""
        print("PREFERENCES: Loading settings from Full Score Options dialog")
        
        # CRITICAL FIX: Ensure parameter isolation - each setting is independent
        # This method allows Full Score Options to update Preferences with proper isolation
        
        try:
            # Staff name settings - completely independent
            if hasattr(full_score_dialog, 'staff_name_font_size'):
                self.staff_name_font_size.setValue(full_score_dialog.staff_name_font_size.value())
            if hasattr(full_score_dialog, 'staff_name_vertical'):
                self.staff_name_vertical.setValue(full_score_dialog.staff_name_vertical.value())
            if hasattr(full_score_dialog, 'staff_name_horizontal'):
                self.staff_name_horizontal.setValue(full_score_dialog.staff_name_horizontal.value())
            if hasattr(full_score_dialog, 'staff_name_color_value'):
                color = getattr(full_score_dialog, 'staff_name_color_value', '#000000')
                self.staff_names_color_value = color  # Update our attribute name
                self.staff_name_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Section name settings - completely independent  
            if hasattr(full_score_dialog, 'section_name_font_size'):
                self.section_name_font_size.setValue(full_score_dialog.section_name_font_size.value())
            if hasattr(full_score_dialog, 'section_name_vertical'):
                self.section_name_vertical.setValue(full_score_dialog.section_name_vertical.value())
            if hasattr(full_score_dialog, 'section_name_horizontal'):
                self.section_name_horizontal.setValue(full_score_dialog.section_name_horizontal.value())
            if hasattr(full_score_dialog, 'section_name_color_value'):
                color = getattr(full_score_dialog, 'section_name_color_value', '#000000')
                self.section_names_color_value = color  # Update our attribute name
                self.section_name_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Time signature settings - completely independent
            if hasattr(full_score_dialog, 'time_sig_font_size'):
                self.time_sig_font_size.setValue(full_score_dialog.time_sig_font_size.value())
            if hasattr(full_score_dialog, 'time_sig_vertical'):
                self.time_sig_vertical.setValue(full_score_dialog.time_sig_vertical.value())
            if hasattr(full_score_dialog, 'time_sig_horizontal'):
                self.time_sig_horizontal.setValue(full_score_dialog.time_sig_horizontal.value())
            if hasattr(full_score_dialog, 'time_sig_spacing'):
                self.time_sig_spacing.setValue(full_score_dialog.time_sig_spacing.value())
            if hasattr(full_score_dialog, 'time_sig_color_value'):
                color = getattr(full_score_dialog, 'time_sig_color_value', '#000000')
                self.time_sig_color_value = color
                self.time_sig_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Key signature settings - completely independent
            if hasattr(full_score_dialog, 'key_sig_font_size'):
                self.key_sig_font_size.setValue(full_score_dialog.key_sig_font_size.value())
            if hasattr(full_score_dialog, 'key_sig_vertical'):
                self.key_sig_vertical.setValue(full_score_dialog.key_sig_vertical.value())
            if hasattr(full_score_dialog, 'key_sig_horizontal'):
                self.key_sig_horizontal.setValue(full_score_dialog.key_sig_horizontal.value())
            if hasattr(full_score_dialog, 'key_sig_accidental_spacing'):
                self.key_sig_accidental_spacing.setValue(full_score_dialog.key_sig_accidental_spacing.value())
            if hasattr(full_score_dialog, 'key_sig_color_value'):
                color = getattr(full_score_dialog, 'key_sig_color_value', '#000000')
                self.key_sig_color_value = color
                self.key_sig_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Clef settings - completely independent
            if hasattr(full_score_dialog, 'clef_font_size'):
                self.clef_font_size.setValue(full_score_dialog.clef_font_size.value())
            if hasattr(full_score_dialog, 'clef_vertical'):
                self.clef_vertical.setValue(full_score_dialog.clef_vertical.value())
            if hasattr(full_score_dialog, 'clef_horizontal'):
                self.clef_horizontal.setValue(full_score_dialog.clef_horizontal.value())
            if hasattr(full_score_dialog, 'clef_color_value'):
                color = getattr(full_score_dialog, 'clef_color_value', '#000000')
                self.clef_color_value = color
                self.clef_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Musical directions settings - completely independent
            if hasattr(full_score_dialog, 'directions_font_size'):
                self.directions_font_size.setValue(full_score_dialog.directions_font_size.value())
            if hasattr(full_score_dialog, 'directions_vertical'):
                self.directions_vertical.setValue(full_score_dialog.directions_vertical.value())
            if hasattr(full_score_dialog, 'directions_horizontal'):
                self.directions_horizontal.setValue(full_score_dialog.directions_horizontal.value())
            
            # Measure numbers settings - completely independent
            if hasattr(full_score_dialog, 'show_measure_numbers'):
                self.show_measure_numbers.setChecked(full_score_dialog.show_measure_numbers.isChecked())
            if hasattr(full_score_dialog, 'measure_numbers_frequency'):
                self.measure_numbers_frequency.setCurrentText(full_score_dialog.measure_numbers_frequency.currentText())
            if hasattr(full_score_dialog, 'measure_numbers_custom_interval'):
                self.measure_numbers_custom_interval.setValue(full_score_dialog.measure_numbers_custom_interval.value())
            if hasattr(full_score_dialog, 'measure_numbers_position'):
                self.measure_numbers_position.setCurrentText(full_score_dialog.measure_numbers_position.currentText())
            if hasattr(full_score_dialog, 'measure_numbers_vertical'):
                self.measure_numbers_vertical.setCurrentText(full_score_dialog.measure_numbers_vertical.currentText())
            if hasattr(full_score_dialog, 'measure_numbers_font_size'):
                self.measure_numbers_font_size.setValue(full_score_dialog.measure_numbers_font_size.value())
            if hasattr(full_score_dialog, 'measure_numbers_vertical_offset'):
                self.measure_numbers_vertical_offset.setValue(full_score_dialog.measure_numbers_vertical_offset.value())
            if hasattr(full_score_dialog, 'measure_numbers_horizontal_offset'):
                self.measure_numbers_horizontal_offset.setValue(full_score_dialog.measure_numbers_horizontal_offset.value())
            if hasattr(full_score_dialog, 'measure_numbers_color_value'):
                color = getattr(full_score_dialog, 'measure_numbers_color_value', '#000000')
                self.measure_numbers_color_value = color
                self.measure_numbers_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            # Barline control settings - completely independent
            if hasattr(full_score_dialog, 'max_measures_per_system'):
                self.max_measures_per_system.setValue(full_score_dialog.max_measures_per_system.value())
            if hasattr(full_score_dialog, 'barline_numbering'):
                self.barline_numbering.setChecked(full_score_dialog.barline_numbering.isChecked())
            if hasattr(full_score_dialog, 'barline_number_font_size'):
                self.barline_number_font_size.setValue(full_score_dialog.barline_number_font_size.value())
            if hasattr(full_score_dialog, 'barline_number_vertical_offset'):
                self.barline_number_vertical_offset.setValue(full_score_dialog.barline_number_vertical_offset.value())
            if hasattr(full_score_dialog, 'barline_number_horizontal_offset'):
                self.barline_number_horizontal_offset.setValue(full_score_dialog.barline_number_horizontal_offset.value())
            if hasattr(full_score_dialog, 'barline_numbers_color_value'):
                color = getattr(full_score_dialog, 'barline_numbers_color_value', '#666666')
                self.barline_numbers_color_value = color
                self.barline_numbers_font_color.setStyleSheet(f"background-color: {color}; color: white;")
            
            print("PREFERENCES: Successfully loaded all settings from Full Score Options with parameter isolation")
            self.save_settings()  # Persist the new defaults to QSettings
        except Exception as e:
            print(f"PREFERENCES: Error loading from Full Score Options: {e}")

    def sync_with_full_score_options(self):
        """Sync current Preferences settings to any open Full Score Options dialog"""
        try:
            # Try to find and update any open Full Score Options dialog
            from PyQt6.QtWidgets import QApplication
            for widget in QApplication.allWidgets():
                if widget.__class__.__name__ == 'FullScoreOptionsDialog':
                    print("PREFERENCES: Found open Full Score Options dialog, syncing settings")
                    
                    # Update Full Score Options dialog with our current values
                    # This ensures immediate visual consistency
                    
                    # Staff name settings
                    if hasattr(widget, 'staff_name_font_size'):
                        widget.staff_name_font_size.setValue(self.staff_name_font_size.value())
                    if hasattr(widget, 'staff_name_vertical'):
                        widget.staff_name_vertical.setValue(self.staff_name_vertical.value())
                    if hasattr(widget, 'staff_name_horizontal'):
                        widget.staff_name_horizontal.setValue(self.staff_name_horizontal.value())
                    if hasattr(self, 'staff_names_color_value'):
                        setattr(widget, 'staff_name_color_value', getattr(self, 'staff_names_color_value', '#000000'))
                        # Update button color
                        if hasattr(widget, 'staff_name_font_color'):
                            widget.staff_name_font_color.setStyleSheet(f"background-color: {self.staff_names_color_value}; color: white;")
                    
                    # Section name settings
                    if hasattr(widget, 'section_name_font_size'):
                        widget.section_name_font_size.setValue(self.section_name_font_size.value())
                    if hasattr(widget, 'section_name_vertical'):
                        widget.section_name_vertical.setValue(self.section_name_vertical.value())
                    if hasattr(widget, 'section_name_horizontal'):
                        widget.section_name_horizontal.setValue(self.section_name_horizontal.value())
                    if hasattr(self, 'section_names_color_value'):
                        setattr(widget, 'section_name_color_value', getattr(self, 'section_names_color_value', '#000000'))
                        # Update button color
                        if hasattr(widget, 'section_name_font_color'):
                            widget.section_name_font_color.setStyleSheet(f"background-color: {self.section_names_color_value}; color: white;")
                    
                    # Continue with other settings...
                    print("PREFERENCES: Successfully synced with Full Score Options dialog")
                    break
        except Exception as e:
            print(f"PREFERENCES: Error syncing with Full Score Options dialog: {e}")

    def get_factory_defaults(self):
        """Get factory default values for all notation settings"""
        return {
            # Staff name defaults
            'notation/staff_name_font_size': 10,
            'notation/staff_name_vertical': -8,
            'notation/staff_name_horizontal': 0,
            'notation/staff_name_font_color': '#000000',
            
            # Section name defaults  
            'notation/section_name_font_size': 10,
            'notation/section_name_vertical': 0,
            'notation/section_name_horizontal': 0,
            'notation/section_name_font_color': '#000000',
            
            # Time signature defaults
            'notation/time_sig_font_size': 24,
            'notation/time_sig_vertical': 0,
            'notation/time_sig_horizontal': 40,
            'notation/time_sig_spacing': 18,
            'notation/time_sig_font_color': '#000000',
            
            # Key signature defaults
            'notation/key_sig_font_size': 14,
            'notation/key_sig_vertical': 0,
            'notation/key_sig_horizontal': 75,
            'notation/key_sig_accidental_spacing': 12,
            'notation/key_sig_font_color': '#000000',
            
            # Clef defaults
            'notation/clef_font_size': 32,
            'notation/clef_vertical': 0,
            'notation/clef_horizontal': 20,
            'notation/clef_font_color': '#000000',
            
            # Musical directions defaults
            'notation/directions_font_size': 10,
            'notation/directions_vertical': 0,
            'notation/directions_horizontal': 0,
        }
    
    def browse_score_directory(self):
        """Browse for score directory"""
        current_dir = self.score_dir.text() or QDir.homePath()
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Default Score Directory",
            current_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if selected_dir:
            self.score_dir.setText(selected_dir)
        
    def setup_audio_tab(self):
        """Set up the audio preferences tab"""
        layout = QFormLayout(self.audio_tab)
        
        # Audio device
        self.audio_device = QComboBox()
        self.audio_device.addItems(["System Default", "Built-in Output", "External Device"])
        layout.addRow("Audio Output Device:", self.audio_device)
        
        # Sample rate
        self.sample_rate = QComboBox()
        self.sample_rate.addItems(["44100 Hz", "48000 Hz", "96000 Hz"])
        layout.addRow("Sample Rate:", self.sample_rate)
        
        # Buffer size
        self.buffer_size = QComboBox()
        self.buffer_size.addItems(["256", "512", "1024", "2048"])
        layout.addRow("Buffer Size:", self.buffer_size)
        
    def setup_midi_io_tab(self):
        """Set up the MIDI IO preferences tab"""
        layout = QFormLayout(self.midi_io_tab)
        
        # MIDI Input section
        input_group = QGroupBox("MIDI Input Ports")
        input_layout = QVBoxLayout(input_group)
        
        # Get available MIDI input ports
        try:
            input_ports = self.midi_in.get_ports()
            if input_ports:
                for port_name in input_ports:
                    port_checkbox = QCheckBox(port_name)
                    input_layout.addWidget(port_checkbox)
            else:
                input_layout.addWidget(QLabel("No MIDI input ports available"))
        except Exception as e:
            error_label = QLabel(f"Error scanning MIDI inputs: {str(e)}")
            error_label.setStyleSheet("color: red;")
            input_layout.addWidget(error_label)
            
        layout.addWidget(input_group)
        
        # MIDI Output section
        output_group = QGroupBox("MIDI Output Ports")
        output_layout = QVBoxLayout(output_group)
        
        # Get available MIDI output ports
        try:
            output_ports = self.midi_out.get_ports()
            output_ports = ["None"] + output_ports if output_ports else ["None"]
            
            # Create 4 output port selections (A, B, C, D)
            for port_letter in ['A', 'B', 'C', 'D']:
                port_layout = QHBoxLayout()
                port_layout.addWidget(QLabel(f"Port {port_letter}:"))
                port_combo = QComboBox()
                port_combo.addItems(output_ports)
                port_layout.addWidget(port_combo)
                output_layout.addLayout(port_layout)
        except Exception as e:
            error_label = QLabel(f"Error scanning MIDI outputs: {str(e)}")
            error_label.setStyleSheet("color: red;")
            output_layout.addWidget(error_label)
            
        layout.addWidget(output_group)
        
    def setup_midi_record_tab(self):
        """Set up the MIDI recording preferences tab"""
        layout = QVBoxLayout(self.midi_record_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Recording settings
        record_group = QGroupBox("Recording Settings")
        record_layout = QFormLayout()
        record_layout.setSpacing(10)

        # Quantization settings
        self.quantize_input = QComboBox()
        self.quantize_input.addItems(["None", "1/4", "1/8", "1/16", "1/32"])
        self.quantize_input.setMinimumWidth(300)
        record_layout.addRow("Input Quantization:", self.quantize_input)

        # Recording mode
        self.record_mode = QComboBox()
        self.record_mode.addItems(["Replace", "Overdub", "Merge"])
        self.record_mode.setMinimumWidth(300)
        record_layout.addRow("Recording Mode:", self.record_mode)

        # Count-in settings
        self.count_in = QSpinBox()
        self.count_in.setRange(0, 4)
        self.count_in.setValue(1)
        self.count_in.setSuffix(" measures")
        self.count_in.setMinimumWidth(300)
        record_layout.addRow("Count-in:", self.count_in)

        record_group.setLayout(record_layout)
        layout.addWidget(record_group)

        # Metronome settings
        metronome_group = QGroupBox("Metronome Settings")
        metronome_layout = QFormLayout()
        metronome_layout.setSpacing(10)

        # Metronome volume
        volume_layout = QHBoxLayout()
        self.metronome_volume = QSlider(Qt.Orientation.Horizontal)
        self.metronome_volume.setRange(0, 100)
        self.metronome_volume.setValue(80)
        self.metronome_volume.setMinimumWidth(250)
        self.volume_label = QLabel("80%")
        self.metronome_volume.valueChanged.connect(
            lambda v: self.volume_label.setText(f"{v}%")
        )
        volume_layout.addWidget(self.metronome_volume)
        volume_layout.addWidget(self.volume_label)
        metronome_layout.addRow("Volume:", volume_layout)

        # Metronome sound
        self.metronome_sound = QComboBox()
        self.metronome_sound.addItems(["Click", "Beep", "Wood Block", "Cowbell"])
        self.metronome_sound.setMinimumWidth(300)
        metronome_layout.addRow("Sound:", self.metronome_sound)

        # Enable during playback
        self.metronome_playback = QCheckBox("Enable during playback")
        self.metronome_playback.setChecked(True)
        metronome_layout.addRow("", self.metronome_playback)

        # Enable during recording
        self.metronome_recording = QCheckBox("Enable during recording")
        self.metronome_recording.setChecked(True)
        metronome_layout.addRow("", self.metronome_recording)

        metronome_group.setLayout(metronome_layout)
        layout.addWidget(metronome_group)

        layout.addStretch()
        
    def setup_midi_import_tab(self):
        """Set up the MIDI import preferences tab"""
        layout = QVBoxLayout(self.midi_import_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Import settings
        import_group = QGroupBox("Import Settings")
        import_layout = QFormLayout()
        import_layout.setSpacing(10)

        # Quantization settings
        self.import_quantize = QComboBox()
        self.import_quantize.addItems(["None", "1/4", "1/8", "1/16", "1/32"])
        self.import_quantize.setMinimumWidth(300)
        import_layout.addRow("Quantization:", self.import_quantize)

        # Channel handling
        self.channel_handling = QComboBox()
        self.channel_handling.addItems(["Merge All", "Separate Voices", "Separate Parts"])
        self.channel_handling.setMinimumWidth(300)
        import_layout.addRow("Channel Handling:", self.channel_handling)

        # Import options
        self.import_tempo = QCheckBox("Import tempo changes")
        self.import_tempo.setChecked(True)
        import_layout.addRow("", self.import_tempo)

        self.import_dynamics = QCheckBox("Import dynamics")
        self.import_dynamics.setChecked(True)
        import_layout.addRow("", self.import_dynamics)

        self.import_articulations = QCheckBox("Import articulations")
        self.import_articulations.setChecked(True)
        import_layout.addRow("", self.import_articulations)

        import_group.setLayout(import_layout)
        layout.addWidget(import_group)

        # Notation settings
        notation_group = QGroupBox("Notation Settings")
        notation_layout = QFormLayout()
        notation_layout.setSpacing(10)

        # Split point
        self.split_point = QSpinBox()
        self.split_point.setRange(0, 127)
        self.split_point.setValue(60)  # Middle C
        self.split_point.setMinimumWidth(300)
        notation_layout.addRow("Split Point (for Grand Staff):", self.split_point)

        # Notation options
        self.detect_tuplets = QCheckBox("Detect tuplets")
        self.detect_tuplets.setChecked(True)
        notation_layout.addRow("", self.detect_tuplets)

        self.detect_grace_notes = QCheckBox("Detect grace notes")
        self.detect_grace_notes.setChecked(True)
        notation_layout.addRow("", self.detect_grace_notes)

        self.detect_pickup = QCheckBox("Detect pickup measures")
        self.detect_pickup.setChecked(True)
        notation_layout.addRow("", self.detect_pickup)

        notation_group.setLayout(notation_layout)
        layout.addWidget(notation_group)

        layout.addStretch()
        
    def setup_plugins_tab(self):
        """Set up the plugins preferences tab"""
        layout = QVBoxLayout(self.plugins_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Plugin list
        plugin_group = QGroupBox("Available Plugins")
        plugin_layout = QVBoxLayout(plugin_group)
        
        # Plugin filter controls
        filter_layout = QHBoxLayout()
        self.hide_disabled_checkbox = QCheckBox("Hide Disabled Plugins")
        self.hide_disabled_checkbox.setChecked(False)
        self.hide_disabled_checkbox.stateChanged.connect(self.filter_plugins)
        filter_layout.addWidget(self.hide_disabled_checkbox)
        filter_layout.addStretch()
        
        # Plugin count label
        self.plugin_count_label = QLabel("0 plugins found")
        self.plugin_count_label.setStyleSheet("color: gray; font-size: 11px;")
        filter_layout.addWidget(self.plugin_count_label)
        
        plugin_layout.addLayout(filter_layout)
        
        # Create table for plugins
        self.plugin_table = QTableWidget()
        self.plugin_table.setColumnCount(5)
        self.plugin_table.setHorizontalHeaderLabels(["Name", "Version", "Format", "Status", "Path"])
        
        # Set column resize modes
        self.plugin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Name
        self.plugin_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Version
        self.plugin_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Format
        self.plugin_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Status
        self.plugin_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Style the table
        self.plugin_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                selection-background-color: #e0e9f5;
                selection-color: black;
                background: white;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
                color: #333;
            }
            QTableWidget::item:selected {
                background-color: #e0e9f5;
            }
        """)
        self.plugin_table.setAlternatingRowColors(True)
        self.plugin_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plugin_table.setSortingEnabled(True)
        plugin_layout.addWidget(self.plugin_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        scan_button = QPushButton("Scan for Plugins")
        enable_button = QPushButton("Enable Selected")
        disable_button = QPushButton("Disable Selected")
        refresh_button = QPushButton("Refresh List")
        
        # Style the buttons
        button_style = """
            QPushButton {
                padding: 6px 16px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #6c757d;
                border-color: #dee2e6;
            }
        """
        
        for button in [scan_button, enable_button, disable_button, refresh_button]:
            button.setStyleSheet(button_style)
        
        button_layout.addWidget(scan_button)
        button_layout.addWidget(enable_button)
        button_layout.addWidget(disable_button)
        button_layout.addStretch()
        button_layout.addWidget(refresh_button)
        plugin_layout.addLayout(button_layout)
        
        layout.addWidget(plugin_group)
        
        # Plugin libraries paths
        paths_group = QGroupBox("Plugin Directories")
        paths_layout = QVBoxLayout(paths_group)
        
        # VST Path
        vst_layout = QHBoxLayout()
        vst_layout.addWidget(QLabel("VST Paths:"))
        self.vst_path = QLineEdit()
        self.vst_path.setReadOnly(True)
        self.vst_path.setMinimumHeight(24)
        vst_layout.addWidget(self.vst_path)
        vst_browse = QPushButton("Browse...")
        vst_browse.setMinimumWidth(80)
        vst_browse.setStyleSheet(button_style)
        vst_layout.addWidget(vst_browse)
        paths_layout.addLayout(vst_layout)
        
        # VST3 Path
        vst3_layout = QHBoxLayout()
        vst3_layout.addWidget(QLabel("VST3 Paths:"))
        self.vst3_path = QLineEdit()
        self.vst3_path.setReadOnly(True)
        self.vst3_path.setMinimumHeight(24)
        vst3_layout.addWidget(self.vst3_path)
        vst3_browse = QPushButton("Browse...")
        vst3_browse.setMinimumWidth(80)
        vst3_browse.setStyleSheet(button_style)
        vst3_layout.addWidget(vst3_browse)
        paths_layout.addLayout(vst3_layout)
        
        # Add description
        paths_desc = QLabel("Add custom plugin directories to scan for VST and VST3 plugins.")
        paths_desc.setStyleSheet("color: gray; font-size: 11px;")
        paths_desc.setWordWrap(True)
        paths_layout.addWidget(paths_desc)
        
        layout.addWidget(paths_group)
        
        # Connect signals
        scan_button.clicked.connect(self.scan_plugins)
        enable_button.clicked.connect(self.enable_selected_plugins)
        disable_button.clicked.connect(self.disable_selected_plugins)
        refresh_button.clicked.connect(self.scan_plugins)
        vst_browse.clicked.connect(lambda: self.browse_plugin_path("VST"))
        vst3_browse.clicked.connect(lambda: self.browse_plugin_path("VST3"))
        
        # Initialize plugin scanner
        self.plugin_scanner = PluginScanner()
        self.update_path_displays()
        
        # Store all plugins for filtering
        self.all_plugins = []
        
        # Initial plugin scan
        self.scan_plugins()
        
    def update_path_displays(self):
        """Update the path displays with current scanner paths"""
        self.vst_path.setText("; ".join(self.plugin_scanner.vst_paths))
        self.vst3_path.setText("; ".join(self.plugin_scanner.vst3_paths))
        
    def browse_plugin_path(self, format_type: str):
        """Browse for a plugin directory"""
        dir_path = QFileDialog.getExistingDirectory(self, f"Select {format_type} Plugin Directory")
        if dir_path:
            self.plugin_scanner.add_custom_path(dir_path, format_type)
            self.update_path_displays()
            self.scan_plugins()
            
    def scan_plugins(self):
        """Scan for plugins and update the display"""
        plugins = self.plugin_scanner.scan_plugins()
        
        # Sort plugins: enabled first, then by name
        self.all_plugins = sorted(plugins, key=lambda p: (not p.is_enabled, p.name.lower()))
        
        # Apply current filter
        self.filter_plugins()
        
    def update_plugin_table(self, plugins):
        """Update the plugin table with the given plugins list"""
        self.plugin_table.setSortingEnabled(False)  # Disable sorting while updating
        self.plugin_table.setRowCount(len(plugins))
        
        # Update plugin count
        total_count = len(self.all_plugins)
        shown_count = len(plugins)
        enabled_count = len([p for p in self.all_plugins if p.is_enabled])
        
        if self.hide_disabled_checkbox.isChecked():
            self.plugin_count_label.setText(f"{shown_count} enabled plugins (of {total_count} total)")
        else:
            self.plugin_count_label.setText(f"{shown_count} plugins ({enabled_count} enabled, {total_count - enabled_count} disabled)")
        
        for row, plugin in enumerate(plugins):
            # Create table items
            name_item = QTableWidgetItem(plugin.name)
            version_item = QTableWidgetItem(plugin.version)
            format_item = QTableWidgetItem(plugin.format)
            status_item = QTableWidgetItem("Enabled" if plugin.is_enabled else "Disabled")
            path_item = QTableWidgetItem(plugin.path)
            
            # Store the plugin object in the name item for reference
            name_item.setData(Qt.ItemDataRole.UserRole, plugin)
            
            # Set items as not editable
            for item in [name_item, version_item, format_item, path_item]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # Style the status item based on enabled/disabled state
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if plugin.is_enabled:
                status_item.setBackground(QColor(144, 238, 144))  # Light green
                status_item.setForeground(QColor(0, 100, 0))      # Dark green
                # Make enabled plugin rows slightly highlighted
                for item in [name_item, version_item, format_item, path_item]:
                    item.setBackground(QColor(255, 255, 255))     # White
            else:
                status_item.setBackground(QColor(211, 211, 211))  # Light gray
                status_item.setForeground(QColor(139, 0, 0))      # Dark red
                # Make disabled plugin rows slightly grayed out
                gray_color = QColor(211, 211, 211)               # Light gray
                for item in [name_item, version_item, format_item, path_item]:
                    item.setBackground(gray_color)
                    item.setForeground(QColor(105, 105, 105))     # Dark gray
            
            # Add items to table
            self.plugin_table.setItem(row, 0, name_item)
            self.plugin_table.setItem(row, 1, version_item)
            self.plugin_table.setItem(row, 2, format_item)
            self.plugin_table.setItem(row, 3, status_item)
            self.plugin_table.setItem(row, 4, path_item)
            
        self.plugin_table.setSortingEnabled(True)  # Re-enable sorting
        
    def enable_selected_plugins(self):
        """Enable selected plugins"""
        selected_rows = set(item.row() for item in self.plugin_table.selectedItems())
        changes_made = False
        
        for row in selected_rows:
            # Get the plugin object from the name item
            name_item = self.plugin_table.item(row, 0)
            plugin = name_item.data(Qt.ItemDataRole.UserRole)
            if plugin and not plugin.is_enabled:
                plugin.is_enabled = True
                # Update plugin state in scanner
                self.plugin_scanner.update_plugin_state(plugin)
                changes_made = True
                
        if changes_made:
            # Re-sort and filter the plugins
            self.all_plugins = sorted(self.all_plugins, key=lambda p: (not p.is_enabled, p.name.lower()))
            self.filter_plugins()
                
    def disable_selected_plugins(self):
        """Disable selected plugins"""
        selected_rows = set(item.row() for item in self.plugin_table.selectedItems())
        changes_made = False
        
        for row in selected_rows:
            # Get the plugin object from the name item
            name_item = self.plugin_table.item(row, 0)
            plugin = name_item.data(Qt.ItemDataRole.UserRole)
            if plugin and plugin.is_enabled:
                plugin.is_enabled = False
                # Update plugin state in scanner
                self.plugin_scanner.update_plugin_state(plugin)
                changes_made = True
                
        if changes_made:
            # Re-sort and filter the plugins
            self.all_plugins = sorted(self.all_plugins, key=lambda p: (not p.is_enabled, p.name.lower()))
            self.filter_plugins()
                
    def filter_plugins(self):
        """Filter plugins based on the hide disabled checkbox"""
        hide_disabled = self.hide_disabled_checkbox.isChecked()
        
        if hide_disabled:
            # Show only enabled plugins
            filtered_plugins = [p for p in self.all_plugins if p.is_enabled]
        else:
            # Show all plugins
            filtered_plugins = self.all_plugins
            
        self.update_plugin_table(filtered_plugins) 

    def closeEvent(self, event):
        if not self._dirty:
            event.accept()
            return
        from PyQt6.QtWidgets import QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle("Unsaved Changes")
        box.setText("You have unsaved changes. Apply to save changes!")
        box.setIcon(QMessageBox.Icon.Warning)
        apply_btn = box.addButton("Apply", QMessageBox.ButtonRole.AcceptRole)
        discard_btn = box.addButton("Discard", QMessageBox.ButtonRole.DestructiveRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(apply_btn)
        box.exec()
        if box.clickedButton() == apply_btn:
            self.apply_settings()
            event.accept()
        elif box.clickedButton() == discard_btn:
            event.accept()
        else:
            event.ignore()