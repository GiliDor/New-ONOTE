from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QTabWidget, 
                             QWidget, QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit,
                             QGroupBox, QScrollArea, QInputDialog, QDialogButtonBox, QToolBar, QToolButton, QMenu, QMessageBox, QColorDialog, QSlider, QApplication)
from PyQt6.QtGui import QAction, QKeySequence, QShortcut
from PyQt6.QtCore import Qt, QEvent
import os
import sys
import copy

class FullScoreOptionsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        print("FULL_SCORE_OPTIONS: Dialog initialized with debug output")
        print("[DEBUG] FullScoreOptionsDialog __init__ called from", __file__)
        print("[DEBUG] FullScoreOptionsDialog init args:", args)
        print("[DEBUG] FullScoreOptionsDialog init kwargs:", kwargs)
        super().__init__(*args, **kwargs)
        self._suppress_undo = False
        self.setWindowTitle("Full Score Options")
        self.setModal(False)  # Make modeless
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # Ensure dialog can receive key events
        self.dialog_zoom = 1.0
        self._undo_stack = []
        self._redo_stack = []
        self._dirty = False

        # CRITICAL FIX: Initialize all color variables to default values
        # This prevents save_settings() from reading uninitialized values
        self.staff_name_color_value = '#000000'
        self.section_name_color_value = '#000000'
        self.clef_color_value = '#000000'
        self.time_sig_color_value = '#000000'
        self.key_sig_color_value = '#000000'

        # --- Zoom controls bar ---
        zoom_toolbar = QToolBar()
        zoom_toolbar.setFloatable(False)
        zoom_toolbar.setMovable(False)
        zoom_toolbar.setStyleSheet("QToolBar { border: none; background: transparent; }")
        
        # --- Zoom Presets menu/button for manual zoom selection ---
        zoom_menu = QMenu("Zoom Presets", self)
        self.zoom_actions = []
        for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
            act = QAction(percent, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked, v=value: self._set_dialog_zoom(v))
            zoom_menu.addAction(act)
            self.zoom_actions.append((act, value))
        zoom_tool_btn = QToolButton()
        zoom_tool_btn.setText("Zoom Presets")
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
        
        # Get document reference from parent window
        self.document = None
        if self.parent():
            if hasattr(self.parent(), 'staff_view') and self.parent().staff_view and hasattr(self.parent().staff_view, 'document'):
                self.document = self.parent().staff_view.document
            elif hasattr(self.parent(), 'music_page') and hasattr(self.parent().music_page, 'staff_view') and hasattr(self.parent().music_page.staff_view, 'document'):
                self.document = self.parent().music_page.staff_view.document
            elif hasattr(self.parent(), 'document'):
                self.document = self.parent().document
        
        print("[DEBUG] About to call setup_ui()...")
        self.setup_ui()
        print("[DEBUG] setup_ui() completed successfully")
        
        # Create QShortcut objects for undo/redo with correct shortcuts
        # Connect all control change signals to push undo states
        self.connect_undo_signals()
        
        # Initialize undo/redo system with working implementation
        self._undo_stack = []
        self._redo_stack = []
        self._suppress_undo = False
        
        # Capture initial state
        initial_state = self._get_current_state()
        self._undo_stack.append(copy.deepcopy(initial_state))
        print(f"[DEBUG] Initial undo state captured with {len(initial_state)} controls")
        
        # Set up undo/redo shortcuts using proven working approach
        self.setup_undo_redo()
        
        # CRITICAL FIX: Connect all valueChanged signals after UI setup
        self._connect_value_changed_signals()
        
        print("[DEBUG] FullScoreOptionsDialog __init__ completed")
        
    def setup_ui(self):
        """Setup the main UI layout"""
        print("[DEBUG] setup_ui() started")
        try:
            # Create zoom toolbar first
            print("[DEBUG] Creating zoom toolbar...")
            zoom_toolbar = QToolBar()
            zoom_toolbar.setFloatable(False)
            zoom_toolbar.setMovable(False)
            zoom_toolbar.setStyleSheet("QToolBar { border: none; background: transparent; }")
            
            # --- Zoom Presets menu/button for manual zoom selection ---
            print("[DEBUG] Creating zoom menu...")
            zoom_menu = QMenu("Zoom Presets", self)
            self.zoom_actions = []
            for percent, value in [("50%", 0.5), ("75%", 0.75), ("100%", 1.0), ("125%", 1.25), ("150%", 1.5)]:
                act = QAction(percent, self)
                act.setCheckable(True)
                act.triggered.connect(lambda checked, v=value: self._set_dialog_zoom(v))
                zoom_menu.addAction(act)
                self.zoom_actions.append((act, value))
            zoom_tool_btn = QToolButton()
            zoom_tool_btn.setText("Zoom Presets")
            zoom_tool_btn.setMenu(zoom_menu)
            zoom_tool_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            zoom_toolbar.addWidget(zoom_tool_btn)
            
            # Add zoom in/out buttons
            print("[DEBUG] Adding zoom buttons...")
            zoom_in_btn = QToolButton()
            zoom_in_btn.setText("+")
            zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
            zoom_in_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom * 1.2))
            zoom_toolbar.addWidget(zoom_in_btn)
            
            zoom_out_btn = QToolButton()
            zoom_out_btn.setText("-")
            zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
            zoom_out_btn.clicked.connect(lambda: self._set_dialog_zoom(self.dialog_zoom * 0.8))
            zoom_toolbar.addWidget(zoom_out_btn)
            
            # Add reset zoom button
            reset_zoom_btn = QToolButton()
            reset_zoom_btn.setText("Reset")
            reset_zoom_btn.setToolTip("Reset to 100%")
            reset_zoom_btn.clicked.connect(lambda: self._set_dialog_zoom(1.0))
            zoom_toolbar.addWidget(reset_zoom_btn)
            
            # Create tab widget for different option categories
            print("[DEBUG] Creating tab widget...")
            self.tab_widget = QTabWidget()
            
            # Create tabs
            self.font_tab = QWidget()
            self.layout_tab = QWidget()
            self.notation_tab = QWidget()
            
            # Setup tab contents
            print("[DEBUG] Setting up font tab...")
            self.setup_font_tab()
            print("[DEBUG] Setting up layout tab...")
            self.setup_layout_tab()
            print("[DEBUG] Setting up notation tab...")
            self.setup_notation_tab()
            
            # Add tabs to tab widget
            self.tab_widget.addTab(self.font_tab, "Fonts")
            self.tab_widget.addTab(self.layout_tab, "Layout")
            self.tab_widget.addTab(self.notation_tab, "Notation Setup")
            
            # Add tab widget to content layout
            self.content_layout.addWidget(self.tab_widget)
            
            print("[DEBUG] Creating main layout...")
            main_layout = QVBoxLayout()
            main_layout.addWidget(zoom_toolbar)
            main_layout.addWidget(self.scroll_area)
            self.setLayout(main_layout)
            self.scroll_area.setWidget(self.content_widget)
            self._set_dialog_zoom(1.0)
            
            # Add dialog buttons
            print("[DEBUG] Adding dialog buttons...")
            button_box = QDialogButtonBox()
            
            # Note: Set as Defaults button is created in setup_notation_tab() to avoid duplication
            
            # Close button - closes dialog (settings are applied immediately on change)
            close_button = button_box.addButton(QDialogButtonBox.StandardButton.Close)
            close_button.clicked.connect(self.close)
            
            # Add Reset to Saved button
            self.reset_to_saved_button = QPushButton("Reset to Saved")
            self.reset_to_saved_button.setMinimumWidth(150)
            self.reset_to_saved_button.setToolTip("Revert Fonts/Layout/Notation options to the last saved state for this document")
            self.reset_to_saved_button.clicked.connect(self.on_reset_to_saved)
            # Disable if no snapshot available
            has_snapshot = bool(getattr(self.document, 'last_saved_options', {})) if self.document else False
            self.reset_to_saved_button.setEnabled(has_snapshot)
            # Place it to the left of Close
            layout_for_buttons = QHBoxLayout()
            layout_for_buttons.addWidget(self.reset_to_saved_button)
            layout_for_buttons.addStretch(1)
            layout_for_buttons.addWidget(button_box)

            container = QWidget()
            container.setLayout(layout_for_buttons)
            main_layout.addWidget(container)
            
            print("[DEBUG] setup_ui() completed successfully")
            
        except Exception as e:
            print(f"[DEBUG] Exception in setup_ui(): {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # IMPORTANT: Load current settings ONLY after all widgets are created
        # This was moved from __init__ to ensure all widgets exist before loading
        self.load_current_settings()
        
        # Undo/Redo actions
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Undo))
        undo_action.triggered.connect(self._undo)
        self.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Redo))  # Cmd/Ctrl+Y
        redo_action.triggered.connect(self._redo)
        self.addAction(redo_action)
        # Remove any conflicting shortcut for Zoom Presets (handled in main window/menu, not here)
        
        # Create initial snapshot for new documents if none exists
        self._ensure_snapshot_exists()

        
    def _ensure_snapshot_exists(self):
        """Create initial snapshot for new documents if none exists."""
        try:
            if not self.document:
                return
            if not hasattr(self.document, 'last_saved_options'):
                self.document.last_saved_options = {}
            if not self.document.last_saved_options:
                # Create initial snapshot from current document settings
                if hasattr(self.document, 'settings') and self.document.settings:
                    self.document.last_saved_options = self.document._extract_full_score_options(self.document.settings)
                    print(f"RESET_TO_SAVED: Created initial snapshot with {len(self.document.last_saved_options)} options")
                else:
                    # Create empty snapshot for completely new documents
                    self.document.last_saved_options = {}
                    print("RESET_TO_SAVED: Created empty initial snapshot for new document")
            # Update button state
            if hasattr(self, 'reset_to_saved_button'):
                has_snapshot = bool(self.document.last_saved_options)
                self.reset_to_saved_button.setEnabled(has_snapshot)
                print(f"RESET_TO_SAVED: Button enabled = {has_snapshot}")
        except Exception as e:
            print(f"RESET_TO_SAVED: Error creating snapshot - {e}")
            import traceback; traceback.print_exc()
    
    def _update_snapshot_after_change(self):
        """Update the snapshot after any setting change to enable Reset to Saved."""
        try:
            if not self.document or not hasattr(self.document, 'settings'):
                return
            # Create/update snapshot from current document settings
            if self.document.settings:
                self.document.last_saved_options = self.document._extract_full_score_options(self.document.settings)
                print(f"RESET_TO_SAVED: Updated snapshot with {len(self.document.last_saved_options)} options")
            # Update button state
            if hasattr(self, 'reset_to_saved_button'):
                has_snapshot = bool(self.document.last_saved_options)
                self.reset_to_saved_button.setEnabled(has_snapshot)
        except Exception as e:
            print(f"RESET_TO_SAVED: Error updating snapshot - {e}")
        
    def on_reset_to_saved(self):
        """Reset only Full Score Options to the document's last-saved snapshot."""
        try:
            if not self.document:
                QMessageBox.warning(self, "Reset to Saved", "No active document.")
                return
            if not getattr(self.document, 'last_saved_options', {}):
                QMessageBox.information(self, "Reset to Saved", "No saved options found for this document.")
                return
            
            # Ask for confirmation with Cancel button
            reply = QMessageBox.question(
                self,
                "Reset to Saved",
                "Are you sure you want to reset all layout and notation settings to the last saved state?\n\n"
                "This will revert Fonts, Layout, and Notation settings to when the document was last saved.\n"
                "Musical content will not be affected.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
                
            ok = self.document.reset_full_score_options_to_saved()
            if not ok:
                QMessageBox.warning(self, "Reset to Saved", "Could not reset to saved options.")
                return
            
            # Reload controls from document.settings
            self.load_current_settings()
            
            # Force immediate re-render by triggering temporal bridge signals
            try:
                if hasattr(self.parent(), 'staff_view') and hasattr(self.parent().staff_view, 'document'):
                    doc = self.parent().staff_view.document
                    # If temporal bridge exists, notify it
                    if hasattr(doc, 'temporal_bridge') and doc.temporal_bridge:
                        try:
                            doc.temporal_bridge.temporal_structure_changed.emit()
                            doc.temporal_bridge.measure_layout_changed.emit()
                        except Exception:
                            pass
                    # Also force staff view update
                    if hasattr(self.parent().staff_view, 'update'):
                        self.parent().staff_view.update()
            except Exception:
                pass
                
            QMessageBox.information(self, "Reset to Saved", "Layout/Notation/Fonts restored to last saved state.")
        except Exception as e:
            print(f"RESET_TO_SAVED ERROR: {e}")
            import traceback; traceback.print_exc()
    def setup_font_tab(self):
        """Set up the Font tab with font selection options"""
        layout = QVBoxLayout(self.font_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Body container
        body = QHBoxLayout()
        
        # Left side - Categories list
        left_side = QVBoxLayout()
        
        # Categories label
        categories_label = QLabel("Text Categories:")
        left_side.addWidget(categories_label)
        
        # Create scrollable list for categories
        self.categories_list = QListWidget()
        self.categories_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        # Add sample categories
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
            "Staff Text"
        ]
        
        for category in categories:
            self.categories_list.addItem(category)
        
        # Connect selection signal
        self.categories_list.currentRowChanged.connect(self.on_category_selected)
        
        left_side.addWidget(self.categories_list)
        
        # Create Category button
        create_category_btn = QPushButton("Create Category")
        create_category_btn.clicked.connect(self.on_create_category)
        left_side.addWidget(create_category_btn)
        
        # Right side - Font controls
        right_side = QVBoxLayout()
        
        # Font Name
        font_name_group = QGroupBox("Font Name")
        font_name_layout = QVBoxLayout(font_name_group)
        self.font_name_combo = QComboBox()
        
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
            "Trebuchet MS"
        ]
        self.font_name_combo.addItems(font_names)
        font_name_layout.addWidget(self.font_name_combo)
        right_side.addWidget(font_name_group)
        
        # Font Style
        style_group = QGroupBox("Style")
        style_layout = QVBoxLayout(style_group)
        self.style_combo = QComboBox()
        
        # Add font styles
        styles = [
            "Regular", 
            "Italic", 
            "SemiBold", 
            "SemiBold Italic", 
            "Bold", 
            "Bold Italic"
        ]
        self.style_combo.addItems(styles)
        style_layout.addWidget(self.style_combo)
        right_side.addWidget(style_group)
        
        # Font Size
        size_group = QGroupBox("Font Size")
        size_layout = QVBoxLayout(size_group)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 72)
        self.size_spin.setValue(12)
        size_layout.addWidget(self.size_spin)
        right_side.addWidget(size_group)
        
        # Use Defaults button
        self.use_defaults_check = QCheckBox("Use Default Font")
        self.use_defaults_check.toggled.connect(self.on_use_defaults_toggled)
        right_side.addWidget(self.use_defaults_check)
        
        # Add spacing
        right_side.addStretch()
        
        # Add left and right layouts to body
        body.addLayout(left_side, 1)
        body.addLayout(right_side, 2)
        layout.addLayout(body)

        # Bottom section with Set/Reset Defaults buttons
        bottom_section = QHBoxLayout()
        bottom_section.addStretch()
        self.fonts_set_defaults_button = QPushButton("Set as Defaults")
        self.fonts_set_defaults_button.setMinimumWidth(150)
        self.fonts_set_defaults_button.clicked.connect(self.set_as_defaults)
        bottom_section.addWidget(self.fonts_set_defaults_button)
        self.fonts_reset_defaults_button = QPushButton("Reset to Defaults")
        self.fonts_reset_defaults_button.setMinimumWidth(150)
        self.fonts_reset_defaults_button.clicked.connect(self.reset_to_defaults)
        bottom_section.addWidget(self.fonts_reset_defaults_button)
        bottom_section.addStretch()
        layout.addLayout(bottom_section)
        
        self.font_name_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('font_name', value))
        self.style_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('font_style', value))
        self.size_spin.valueChanged.connect(lambda value: self._apply_single_parameter_change('font_size', value))
        self.use_defaults_check.toggled.connect(lambda checked: self._apply_single_parameter_change('use_default_font', checked))
        
    def setup_layout_tab(self):
        """Set up the Layout tab with document-specific layout options"""
        layout = QVBoxLayout(self.layout_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Document-specific note
        doc_note = QLabel("⚠️ These layout settings apply only to the current document.")
        doc_note.setStyleSheet("background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; padding: 8px; color: #856404; font-weight: bold;")
        doc_note.setWordWrap(True)
        layout.addWidget(doc_note)
        
        # Create scroll area for layout options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # Document Layout section
        doc_layout_group = QGroupBox("Document Layout")
        doc_layout_layout = QFormLayout(doc_layout_group)
        doc_layout_layout.setSpacing(8)
        
        # Notation Size (document-specific scaling)
        self.notation_size_spin = QDoubleSpinBox()
        self.notation_size_spin.setRange(0.5, 3.0)
        self.notation_size_spin.setValue(1.0)
        self.notation_size_spin.setSingleStep(0.1)
        self.notation_size_spin.setSuffix("x")
        self.notation_size_spin.setToolTip("Scale factor for notation elements in this document")
        doc_layout_layout.addRow("Notation Scale:", self.notation_size_spin)
        
        # Page Layout
        self.page_layout_combo = QComboBox()
        self.page_layout_combo.addItems(["Single Page", "Facing Pages", "Continuous Scroll"])
        self.page_layout_combo.setCurrentText("Single Page")
        doc_layout_layout.addRow("Page Layout:", self.page_layout_combo)
        
        # Measures per System (document-specific)  
        self.measures_system_spin = QSpinBox()
        self.measures_system_spin.setRange(1, 12)
        # CRITICAL FIX: Always load initial value from Preferences for consistency
        from PyQt6.QtCore import QSettings
        preferences_settings = QSettings("ONOTE", "Preferences")
        default_measures_per_system = int(preferences_settings.value("layout/default_measures_per_system", 4))
        self.measures_system_spin.setValue(default_measures_per_system)
        self.measures_system_spin.setSpecialValueText("Auto")
        self.measures_system_spin.setToolTip("Number of measures per system (0 = automatic)")
        doc_layout_layout.addRow("Measures per System:", self.measures_system_spin)
        
        # System Spacing (document-specific)
        self.doc_system_spacing = QSpinBox()
        self.doc_system_spacing.setRange(40, 200)
        # CRITICAL FIX: Always load initial value from Preferences for consistency
        default_system_spacing = int(preferences_settings.value("layout/default_system_spacing", 80))
        self.doc_system_spacing.setValue(default_system_spacing)
        self.doc_system_spacing.setSuffix(" px")
        self.doc_system_spacing.setToolTip("Vertical spacing between systems in this document")
        doc_layout_layout.addRow("System Spacing:", self.doc_system_spacing)
        
        # Staff Spacing (document-specific)
        self.doc_staff_spacing = QSpinBox()
        self.doc_staff_spacing.setRange(20, 120)
        # CRITICAL FIX: Always load initial value from Preferences for consistency
        default_staff_spacing = int(preferences_settings.value("layout/default_staff_spacing", 40))
        self.doc_staff_spacing.setValue(default_staff_spacing)
        self.doc_staff_spacing.setSuffix(" px")
        self.doc_staff_spacing.setToolTip("Vertical spacing between individual staves within the score-system")
        doc_layout_layout.addRow("Staff Spacing:", self.doc_staff_spacing)
        
        # Grand Staff Spacing (document-specific)
        self.doc_grand_staff_spacing = QSpinBox()
        self.doc_grand_staff_spacing.setRange(8, 160)
        try:
            default_grand_spacing = int(preferences_settings.value("layout/default_grand_staff_spacing", 32))
        except Exception:
            default_grand_spacing = 32
        self.doc_grand_staff_spacing.setValue(default_grand_spacing)
        self.doc_grand_staff_spacing.setSuffix(" px")
        self.doc_grand_staff_spacing.setToolTip("Minimum spacing between treble and bass within a grand staff (auto-expands if needed)")
        doc_layout_layout.addRow("Grand Staff Spacing:", self.doc_grand_staff_spacing)
        
        scroll_layout.addWidget(doc_layout_group)
        
        # Text and Markings section
        text_group = QGroupBox("Text and Markings")
        text_layout = QFormLayout(text_group)
        text_layout.setSpacing(8)
        

        
        # Staff Names
        self.staff_names_combo = QComboBox()
        self.staff_names_combo.addItems(["Full Names", "Abbreviations", "First System Only", "None"])
        self.staff_names_combo.setCurrentText("First System Only")
        text_layout.addRow("Staff Names:", self.staff_names_combo)
        
        # Title Display
        self.title_display_combo = QComboBox()
        self.title_display_combo.addItems(["Full Title", "Abbreviated", "None"])
        self.title_display_combo.setCurrentText("Full Title")
        text_layout.addRow("Title Display:", self.title_display_combo)
        
        scroll_layout.addWidget(text_group)
        
        # Formatting section
        format_group = QGroupBox("Formatting")
        format_layout = QFormLayout(format_group)
        format_layout.setSpacing(8)
        
        # Notation Style
        self.notation_style_combo = QComboBox()
        self.notation_style_combo.addItems(["Standard", "Jazz", "Handwritten", "Engraved"])
        format_layout.addRow("Notation Style:", self.notation_style_combo)
        
        # Barline Style
        self.barline_style_combo = QComboBox()
        self.barline_style_combo.addItems(["Standard", "Thick", "Thin", "Dashed"])
        format_layout.addRow("Barline Style:", self.barline_style_combo)
        
        # Beam Style
        self.beam_style_combo = QComboBox()
        self.beam_style_combo.addItems(["Standard", "Heavy", "Light", "Feathered"])
        format_layout.addRow("Beam Style:", self.beam_style_combo)
        
        scroll_layout.addWidget(format_group)
        
        # Advanced Document Options
        advanced_group = QGroupBox("Advanced Document Options")
        advanced_layout = QFormLayout(advanced_group)
        advanced_layout.setSpacing(8)
        
        # Justify Last System
        self.justify_last_system = QCheckBox("Justify measures in last system")
        self.justify_last_system.setChecked(False)
        advanced_layout.addRow("", self.justify_last_system)
        
        # Hide Empty Staves
        self.hide_empty_staves = QCheckBox("Hide empty staves")
        self.hide_empty_staves.setChecked(False)
        advanced_layout.addRow("", self.hide_empty_staves)
        
        # Optimize Page Turns
        self.optimize_page_turns = QCheckBox("Optimize page turns")
        self.optimize_page_turns.setChecked(True)
        advanced_layout.addRow("", self.optimize_page_turns)
        
        scroll_layout.addWidget(advanced_group)
        
        # Document note
        doc_info = QLabel("💡 For application-wide layout defaults, use Edit → Preferences → Layout")
        doc_info.setStyleSheet("background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; padding: 8px; color: #0c5460; font-style: italic;")
        doc_info.setWordWrap(True)
        scroll_layout.addWidget(doc_info)

        # Bottom section with Set/Reset Defaults buttons for Layout
        bottom_section = QHBoxLayout()
        bottom_section.addStretch()
        self.layout_set_defaults_button = QPushButton("Set as Defaults")
        self.layout_set_defaults_button.setMinimumWidth(150)
        self.layout_set_defaults_button.clicked.connect(self.set_as_defaults)
        bottom_section.addWidget(self.layout_set_defaults_button)
        self.layout_reset_defaults_button = QPushButton("Reset to Defaults")
        self.layout_reset_defaults_button.setMinimumWidth(150)
        self.layout_reset_defaults_button.clicked.connect(self.reset_to_defaults)
        bottom_section.addWidget(self.layout_reset_defaults_button)
        bottom_section.addStretch()
        scroll_layout.addLayout(bottom_section)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        self.notation_size_spin.valueChanged.connect(lambda value: self._apply_single_parameter_change('notation_scale', value))
        self.page_layout_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('page_layout', value))
        self.measures_system_spin.valueChanged.connect(lambda value: self._apply_single_parameter_change('measures_per_system', value))
        self.doc_system_spacing.valueChanged.connect(lambda value: self._apply_single_parameter_change('system_spacing', value))
        self.doc_staff_spacing.valueChanged.connect(lambda value: self._apply_single_parameter_change('staff_spacing', value))
        self.doc_grand_staff_spacing.valueChanged.connect(lambda value: self._apply_single_parameter_change('grand_staff_spacing', value))
        self.staff_names_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('staff_names', value))
        self.title_display_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('title_display', value))
        self.notation_style_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('notation_style', value))
        self.barline_style_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('barline_style', value))
        self.beam_style_combo.currentTextChanged.connect(lambda value: self._apply_single_parameter_change('beam_style', value))
        self.justify_last_system.toggled.connect(lambda checked: self._apply_single_parameter_change('justify_last_system', checked))
        self.hide_empty_staves.toggled.connect(lambda checked: self._apply_single_parameter_change('hide_empty_staves', checked))
        self.optimize_page_turns.toggled.connect(lambda checked: self._apply_single_parameter_change('optimize_page_turns', checked))
        
    def setup_notation_tab(self):
        """Set up the Notation Setup tab with comprehensive notation controls and immediate score updates"""
        layout = QVBoxLayout(self.notation_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Document-specific note
        doc_note = QLabel("⚙️ These notation settings apply to the current document only. Use 'Set as Defaults' to save for new documents.")
        doc_note.setStyleSheet("background: #e7f3ff; border: 1px solid #b3d9ff; border-radius: 4px; padding: 8px; color: #0066cc; font-weight: bold;")
        doc_note.setWordWrap(True)
        layout.addWidget(doc_note)
        
        # Create main horizontal layout for 3 columns
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(15)
        
        # LEFT COLUMN - Empty (content moved to right column for better balance)
        left_column = QVBoxLayout()
        left_column.setSpacing(10)
        
        # Measure Numbers and Barline Control Settings
        measure_numbers_group = QGroupBox("Measure Numbers")
        measure_numbers_layout = QFormLayout(measure_numbers_group)
        measure_numbers_layout.setSpacing(6)
        
        # Enable measure numbers
        self.show_measure_numbers = QCheckBox("Show measure numbers")
        self.show_measure_numbers.setChecked(True)
        self.show_measure_numbers.setToolTip("Show measure numbers on the score")
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
        
        # Connect frequency change to show/hide custom interval
        self.measure_numbers_frequency.currentTextChanged.connect(self.on_measure_numbers_frequency_changed)
        
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
        
        left_column.addWidget(measure_numbers_group)
        
        # Barline Control Settings
        barline_group = QGroupBox("Barline Control")
        barline_layout = QFormLayout(barline_group)
        barline_layout.setSpacing(6)
        
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
        
        # Barline Number Vertical Offset
        self.barline_number_vertical_offset = QSpinBox()
        self.barline_number_vertical_offset.setRange(-100, 100)
        self.barline_number_vertical_offset.setValue(0)
        self.barline_number_vertical_offset.setSuffix(" px")
        self.barline_number_vertical_offset.setMinimumWidth(80)
        self.barline_number_vertical_offset.setToolTip("Vertical offset for barline numbers (negative = above)")
        barline_layout.addRow("Vertical Offset:", self.barline_number_vertical_offset)
        
        # Barline Number Horizontal Offset
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
        
        left_column.addWidget(barline_group)
        
        left_column.addStretch()
        
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
        self.clef_font_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus issues
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
        self.time_sig_font_size.valueChanged.connect(lambda value: self._apply_single_parameter_change('time_sig_font_size', value))
        time_sig_layout.addRow("Font Size:", self.time_sig_font_size)
        
        # Vertical position
        self.time_sig_vertical = QSpinBox()
        self.time_sig_vertical.setRange(-20, 20)
        self.time_sig_vertical.setValue(0)
        self.time_sig_vertical.setSuffix(" px")
        self.time_sig_vertical.setMinimumWidth(80)
        self.time_sig_vertical.setToolTip("Vertical offset (0 = centered on staff)")
        self.time_sig_vertical.valueChanged.connect(lambda value: self._apply_single_parameter_change('time_sig_vertical', value))
        time_sig_layout.addRow("Vertical:", self.time_sig_vertical)
        
        # Horizontal position
        self.time_sig_horizontal = QSpinBox()
        self.time_sig_horizontal.setRange(-500, 2000)
        self.time_sig_horizontal.setValue(40)
        self.time_sig_horizontal.setSuffix(" px")
        self.time_sig_horizontal.setMinimumWidth(80)
        self.time_sig_horizontal.setToolTip("Distance from left margin")
        self.time_sig_horizontal.valueChanged.connect(lambda value: self._apply_single_parameter_change('time_sig_horizontal', value))
        
        time_sig_layout.addRow("Horizontal:", self.time_sig_horizontal)
        
        # Spacing between numerator and denominator
        self.time_sig_spacing = QSpinBox()
        self.time_sig_spacing.setRange(10, 30)
        self.time_sig_spacing.setValue(18)
        self.time_sig_spacing.setSuffix(" px")
        self.time_sig_spacing.setMinimumWidth(80)
        self.time_sig_spacing.setToolTip("Vertical spacing between numerator and denominator")
        self.time_sig_spacing.valueChanged.connect(lambda value: self._apply_single_parameter_change('time_sig_spacing', value))
        time_sig_layout.addRow("Spacing:", self.time_sig_spacing)
        
        # Font Color
        self.time_sig_font_color = QPushButton("Choose Color")
        self.time_sig_font_color.setMinimumWidth(100)
        self.time_sig_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.time_sig_font_color.clicked.connect(lambda: self.choose_font_color('time_sig'))
        self.time_sig_font_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus issues
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
        self.key_sig_font_size.valueChanged.connect(lambda value: self._apply_single_parameter_change('key_sig_font_size', value))
        key_sig_layout.addRow("Font Size:", self.key_sig_font_size)
        
        # Vertical position
        self.key_sig_vertical = QSpinBox()
        self.key_sig_vertical.setRange(-15, 15)
        self.key_sig_vertical.setValue(0)
        self.key_sig_vertical.setSuffix(" px")
        self.key_sig_vertical.setMinimumWidth(80)
        self.key_sig_vertical.setToolTip("Vertical offset (0 = centered on staff)")
        self.key_sig_vertical.valueChanged.connect(lambda value: self._apply_single_parameter_change('key_sig_vertical', value))
        key_sig_layout.addRow("Vertical:", self.key_sig_vertical)
        
        # Horizontal position
        self.key_sig_horizontal = QSpinBox()
        self.key_sig_horizontal.setRange(60, 120)
        self.key_sig_horizontal.setValue(75)
        self.key_sig_horizontal.setSuffix(" px")
        self.key_sig_horizontal.setMinimumWidth(80)
        self.key_sig_horizontal.setToolTip("Distance from left margin (after time signature)")
        self.key_sig_horizontal.valueChanged.connect(lambda value: self._apply_single_parameter_change('key_sig_horizontal', value))
        key_sig_layout.addRow("Horizontal:", self.key_sig_horizontal)
        
        # Accidental spacing
        self.key_sig_accidental_spacing = QSpinBox()
        self.key_sig_accidental_spacing.setRange(8, 20)
        self.key_sig_accidental_spacing.setValue(12)
        self.key_sig_accidental_spacing.setSuffix(" px")
        self.key_sig_accidental_spacing.setMinimumWidth(80)
        self.key_sig_accidental_spacing.setToolTip("Horizontal spacing between accidentals")
        self.key_sig_accidental_spacing.valueChanged.connect(lambda value: self._apply_single_parameter_change('key_sig_accidental_spacing', value))
        key_sig_layout.addRow("Spacing:", self.key_sig_accidental_spacing)
        
        # Font Color
        self.key_sig_font_color = QPushButton("Choose Color")
        self.key_sig_font_color.setMinimumWidth(100)
        self.key_sig_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.key_sig_font_color.clicked.connect(lambda: self.choose_font_color('key_sig'))
        self.key_sig_font_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus issues
        key_sig_layout.addRow("Font Color:", self.key_sig_font_color)
        
        middle_column.addWidget(key_sig_group)
        
        # RIGHT COLUMN - Staff Names and Section Names (moved from left column)
        right_column = QVBoxLayout()
        right_column.setSpacing(10)
        
        # Staff Name Settings (moved from left column)
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
        self.staff_name_font_size.valueChanged.connect(lambda value: self._apply_single_parameter_change('staff_name_font_size', value))
        staff_name_layout.addRow("Font Size:", self.staff_name_font_size)
        
        # Vertical position
        self.staff_name_vertical = QSpinBox()
        self.staff_name_vertical.setRange(-50, 20)
        self.staff_name_vertical.setValue(-8)
        self.staff_name_vertical.setSuffix(" px")
        self.staff_name_vertical.setMinimumWidth(80)
        self.staff_name_vertical.setToolTip("Vertical offset (negative = above staff)")
        self.staff_name_vertical.valueChanged.connect(lambda value: self._apply_single_parameter_change('staff_name_vertical', value))
        staff_name_layout.addRow("Vertical:", self.staff_name_vertical)
        
        # Horizontal position
        self.staff_name_horizontal = QSpinBox()
        self.staff_name_horizontal.setRange(-100, 0)
        self.staff_name_horizontal.setValue(-50)
        self.staff_name_horizontal.setSuffix(" px")
        self.staff_name_horizontal.setMinimumWidth(80)
        self.staff_name_horizontal.setToolTip("Horizontal offset (negative = left of staff)")
        self.staff_name_horizontal.valueChanged.connect(lambda value: self._apply_single_parameter_change('staff_name_horizontal', value))
        staff_name_layout.addRow("Horizontal:", self.staff_name_horizontal)
        
        # Font Color
        self.staff_name_font_color = QPushButton("Choose Color")
        self.staff_name_font_color.setMinimumWidth(100)
        self.staff_name_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.staff_name_font_color.clicked.connect(lambda: self.choose_font_color('staff_names'))
        self.staff_name_font_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus issues
        staff_name_layout.addRow("Font Color:", self.staff_name_font_color)
        
        right_column.addWidget(staff_name_group)
        
        # Section Name Settings (moved from left column)
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
        self.section_name_font_size.valueChanged.connect(lambda value: self._apply_single_parameter_change('section_name_font_size', value))
        section_name_layout.addRow("Font Size:", self.section_name_font_size)
        
        # Vertical position
        self.section_name_vertical = QSpinBox()
        self.section_name_vertical.setRange(-60, 10)
        self.section_name_vertical.setValue(-25)
        self.section_name_vertical.setSuffix(" px")
        self.section_name_vertical.setMinimumWidth(80)
        self.section_name_vertical.setToolTip("Vertical offset (negative = above staff group)")
        self.section_name_vertical.valueChanged.connect(lambda value: self._apply_single_parameter_change('section_name_vertical', value))
        section_name_layout.addRow("Vertical:", self.section_name_vertical)
        
        # Horizontal position
        self.section_name_horizontal = QSpinBox()
        self.section_name_horizontal.setRange(-120, 0)
        self.section_name_horizontal.setValue(-60)
        self.section_name_horizontal.setSuffix(" px")
        self.section_name_horizontal.setMinimumWidth(80)
        self.section_name_horizontal.setToolTip("Horizontal offset (negative = left of staff)")
        self.section_name_horizontal.valueChanged.connect(lambda value: self._apply_single_parameter_change('section_name_horizontal', value))
        section_name_layout.addRow("Horizontal:", self.section_name_horizontal)
        
        # Font Color
        self.section_name_font_color = QPushButton("Choose Color")
        self.section_name_font_color.setMinimumWidth(100)
        self.section_name_font_color.setStyleSheet("background-color: #000000; color: white;")
        self.section_name_font_color.clicked.connect(lambda: self.choose_font_color('section_names'))
        self.section_name_font_color.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent focus issues
        section_name_layout.addRow("Font Color:", self.section_name_font_color)
        
        right_column.addWidget(section_name_group)
        
        # Musical Directions Settings (moved from left column)
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
        self.directions_font_size.valueChanged.connect(lambda value: self._apply_single_parameter_change('directions_font_size', value))
        directions_layout.addRow("Font Size:", self.directions_font_size)
        
        # Vertical position
        self.directions_vertical = QSpinBox()
        self.directions_vertical.setRange(10, 60)
        self.directions_vertical.setValue(30)
        self.directions_vertical.setSuffix(" px")
        self.directions_vertical.setMinimumWidth(80)
        self.directions_vertical.setToolTip("Distance below staff")
        self.directions_vertical.valueChanged.connect(lambda value: self._apply_single_parameter_change('directions_vertical', value))
        directions_layout.addRow("Vertical:", self.directions_vertical)
        
        # Horizontal position
        self.directions_horizontal = QSpinBox()
        self.directions_horizontal.setRange(-50, 50)
        self.directions_horizontal.setValue(0)
        self.directions_horizontal.setSuffix(" px")
        self.directions_horizontal.setMinimumWidth(80)
        self.directions_horizontal.setToolTip("Horizontal offset from center")
        self.directions_horizontal.valueChanged.connect(lambda value: self._apply_single_parameter_change('directions_horizontal', value))
        directions_layout.addRow("Horizontal:", self.directions_horizontal)
        
        right_column.addWidget(directions_group)
        
        # Add columns to main horizontal layout
        main_h_layout.addLayout(left_column, 1)
        main_h_layout.addLayout(middle_column, 1)
        main_h_layout.addLayout(right_column, 1)
        
        # Add the main layout to the tab
        layout.addLayout(main_h_layout)
        
        # Bottom section with Set as Defaults button
        bottom_section = QHBoxLayout()
        bottom_section.setSpacing(10)
        
        # Add stretch to center the button
        bottom_section.addStretch()
        
        # Add the "Set as Defaults" button
        self.set_defaults_button = QPushButton("Set as Defaults")
        self.set_defaults_button.setMinimumWidth(150)
        self.set_defaults_button.setMinimumHeight(32)
        self.set_defaults_button.setToolTip("Save the current settings as defaults for new documents")
        self.set_defaults_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.set_defaults_button.clicked.connect(self.set_as_defaults)
        bottom_section.addWidget(self.set_defaults_button)
        
        # Add the "Reset to Defaults" button
        self.reset_defaults_button = QPushButton("Reset to Defaults")
        self.reset_defaults_button.setMinimumWidth(150)
        self.reset_defaults_button.setMinimumHeight(32)
        self.reset_defaults_button.setToolTip("Reset all settings to application defaults")
        self.reset_defaults_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.reset_defaults_button.clicked.connect(self.reset_to_defaults)
        bottom_section.addWidget(self.reset_defaults_button)
        
        # Add stretch to center the button
        bottom_section.addStretch()
        
        layout.addLayout(bottom_section)

    def choose_font_color(self, category):
        """Open color picker dialog for font colors - SAFE VERSION"""
        print(f"COLOR_PICKER: Starting SAFE color selection for {category}")
        print(f"COLOR_PICKER: Button clicked for category: {category}")
        
        # CRITICAL FIX: Use a safer approach that doesn't trigger system events
        try:
            from PyQt6.QtWidgets import QColorDialog
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QColor
            
            # Get current color from button style or stored value
            current_color = QColor("#000000")  # Default black
            if category == 'staff_names':
                button = self.staff_name_font_color
                current_color = QColor(getattr(self, 'staff_name_color_value', '#000000'))
            elif category == 'section_names':
                button = self.section_name_font_color
                current_color = QColor(getattr(self, 'section_name_color_value', '#000000'))
            elif category == 'clef':
                button = self.clef_font_color
                current_color = QColor(getattr(self, 'clef_color_value', '#000000'))
            elif category == 'time_sig':
                button = self.time_sig_font_color
                current_color = QColor(getattr(self, 'time_sig_color_value', '#000000'))
            elif category == 'key_sig':
                button = self.key_sig_font_color
                current_color = QColor(getattr(self, 'key_sig_color_value', '#000000'))
            elif category == 'measure_numbers':
                button = self.measure_numbers_font_color
                current_color = QColor(getattr(self, 'measure_numbers_color_value', '#000000'))
            elif category == 'barline_numbers':
                button = self.barline_number_font_color
                current_color = QColor(getattr(self, 'barline_numbers_color_value', '#666666'))
                print(f"COLOR_PICKER: Loading barline_numbers_color_value = {getattr(self, 'barline_numbers_color_value', 'NOT SET')}")
            else:
                print(f"COLOR_PICKER: Unknown category: {category}")
                return
            
            print(f"COLOR_PICKER: About to open SAFE color dialog for {category}")
            
            # SAFE VERSION: Use explicit dialog creation to avoid system conflicts
            color_dialog = QColorDialog(current_color, self)
            color_dialog.setWindowTitle(f"Choose {category.replace('_', ' ').title()} Color")
            color_dialog.setModal(True)
            
            # Execute dialog safely
            if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
                color = color_dialog.currentColor()
                print(f"COLOR_PICKER: SAFE dialog returned color: {color.name()}")
                
                if color.isValid():
                    # Update button appearance
                    hex_color = color.name()
                    print(f"COLOR_PICKER: Selected color for {category}: {hex_color}")
                    
                    # Choose contrasting text color
                    text_color = "#FFFFFF" if self.is_dark_color(color) else "#000000"
                    button.setStyleSheet(f"background-color: {hex_color}; color: {text_color};")
                    
                    # Store the color value for saving
                    setattr(self, f"{category}_color_value", hex_color)
                    print(f"COLOR_PICKER: Stored {category}_color_value = {hex_color}")
                    
                    # IMMEDIATE UPDATE: Apply color change immediately like other Full Score Options
                    print(f"COLOR_PICKER: Applying {category} color change immediately")
                    self._apply_color_change_immediately(category, hex_color)
                else:
                    print(f"COLOR_PICKER: Invalid color returned for {category}")
            else:
                print(f"COLOR_PICKER: Color selection cancelled for {category}")
                
        except Exception as e:
            print(f"COLOR_PICKER: ERROR in choose_font_color: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_color_change_immediately(self, category, hex_color):
        """Apply color change immediately without side effects - COMPLETELY ISOLATED"""
        print(f"IMMEDIATE_COLOR: Applying {category} color {hex_color} with complete isolation")
        
        # Step 1: Save ONLY the specific color to document settings (no other changes)
        if hasattr(self, 'document') and self.document:
            if not hasattr(self.document, 'settings'):
                self.document.settings = {}
            
            # Map categories to exact document setting keys
            color_key_mapping = {
                'staff_names': 'notation/staff_name_font_color',
                'section_names': 'notation/section_name_font_color', 
                'clef': 'notation/clef_font_color',
                'time_sig': 'notation/time_sig_font_color',
                'time_signature': 'notation/time_sig_font_color',
                'key_sig': 'notation/key_sig_font_color',
                'measure_numbers': 'notation/measure_numbers_font_color',
                'barline_numbers': 'notation/barline_numbers_font_color'
            }
            
            if category in color_key_mapping:
                key = color_key_mapping[category]
                self.document.settings[key] = hex_color
                print(f"IMMEDIATE_COLOR: Saved {key} = {hex_color} to document settings")
                
                # Mark document as modified
                if hasattr(self.document, 'set_modified'):
                    self.document.set_modified(True)
            
        # Step 2: Apply ONLY the specific color to renderer (no full reload)
        staff_view = self._get_staff_view()
        if staff_view and hasattr(staff_view, 'renderer') and staff_view.renderer:
            renderer = staff_view.renderer
            print(f"IMMEDIATE_COLOR: Found renderer, applying ONLY {category} color")
            
            # CRITICAL: Apply ONLY the specific color attribute - no other changes
            if category == 'staff_names':
                renderer.staff_name_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.staff_name_font_color = {hex_color}")
                # CRITICAL FIX: Also update document settings immediately
                if hasattr(self, 'document') and self.document:
                    if not hasattr(self.document, 'settings'):
                        self.document.settings = {}
                    self.document.settings['notation/staff_name_font_color'] = hex_color
                    print(f"IMMEDIATE_COLOR: Updated document settings with staff_name_font_color = {hex_color}")
                # CRITICAL FIX: Force immediate visual refresh
                staff_view.repaint()
                print(f"IMMEDIATE_COLOR: Forced immediate repaint for staff name color change")
                # CRITICAL FIX: Also force the renderer to reload settings
                if hasattr(staff_view, 'renderer') and staff_view.renderer:
                    staff_view.renderer.load_notation_settings()
                    print(f"IMMEDIATE_COLOR: Forced renderer to reload notation settings")
            elif category == 'section_names':
                renderer.section_name_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.section_name_font_color = {hex_color}")
            elif category == 'clef':
                renderer.clef_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.clef_font_color = {hex_color}")
            elif category == 'time_sig':
                renderer.time_sig_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.time_sig_font_color = {hex_color}")
            elif category == 'key_sig':
                renderer.key_sig_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.key_sig_font_color = {hex_color}")
            elif category == 'measure_numbers':
                # CRITICAL FIX: Measure numbers are managed by MeasureNumberManager, not renderer directly
                if hasattr(renderer, 'measure_number_manager') and renderer.measure_number_manager:
                    renderer.measure_number_manager.settings.font_color = hex_color
                    renderer.measure_number_manager.refresh_settings()
                    print(f"IMMEDIATE_COLOR: Set measure_number_manager.settings.font_color = {hex_color}")
                else:
                    print(f"IMMEDIATE_COLOR: No measure_number_manager found in renderer")
            elif category == 'barline_numbers':
                renderer.barline_numbers_font_color = hex_color
                print(f"IMMEDIATE_COLOR: Set renderer.barline_numbers_font_color = {hex_color}")
            
            # Step 3: Force only a visual refresh (no settings reload)
            staff_view.update()
            print(f"IMMEDIATE_COLOR: Applied isolated {category} color update successfully")
        else:
            print("IMMEDIATE_COLOR: Could not find staff_view or renderer for immediate update")

    def _update_color_only(self, category, hex_color):
        """Update ONLY the specific color in the document without affecting other settings"""
        print(f"COLOR_UPDATE: Updating only {category} color to {hex_color}")
        
        if not hasattr(self, 'document') or not self.document:
            print("COLOR_UPDATE: No document available")
            return
        
        # Initialize document settings if not present
        if not hasattr(self.document, 'settings'):
            self.document.settings = {}
        
        # Save ONLY the specific color setting
        if category == 'staff_names':
            self.document.settings['notation/staff_name_font_color'] = hex_color
        elif category == 'section_names':
            self.document.settings['notation/section_name_font_color'] = hex_color
        elif category == 'clef':
            self.document.settings['notation/clef_font_color'] = hex_color
        elif category == 'time_sig':
            self.document.settings['notation/time_sig_font_color'] = hex_color
        elif category == 'key_sig':
            self.document.settings['notation/key_sig_font_color'] = hex_color
        elif category == 'measure_numbers':
            self.document.settings['notation/measure_numbers_font_color'] = hex_color
        elif category == 'barline_numbers':
            self.document.settings['notation/barline_numbers_font_color'] = hex_color
        
        print(f"COLOR_UPDATE: Saved {category} color setting to document")
        
        # Now update only the renderer - don't reload ALL settings
        parent_window = self.parent()
        if not parent_window:
            print("COLOR_UPDATE: No parent window found")
            return
        
        # Get staff view
        staff_view = None
        if hasattr(parent_window, 'staff_view'):
            staff_view = parent_window.staff_view
        elif hasattr(parent_window, 'central_widget') and hasattr(parent_window.central_widget, 'staff_view'):
            staff_view = parent_window.central_widget.staff_view
        elif hasattr(parent_window, 'music_page') and hasattr(parent_window.music_page, 'staff_view'):
            staff_view = parent_window.music_page.staff_view
        
        if staff_view and hasattr(staff_view, 'renderer') and staff_view.renderer:
            # TARGETED UPDATE: Only reload the specific color attribute
            renderer = staff_view.renderer
            
            if category == 'staff_names':
                renderer.staff_name_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer staff_name_font_color to {hex_color}")
            elif category == 'section_names':
                renderer.section_name_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer section_name_font_color to {hex_color}")
            elif category == 'clef':
                renderer.clef_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer clef_font_color to {hex_color}")
            elif category == 'time_sig':
                renderer.time_sig_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer time_sig_font_color to {hex_color}")
            elif category == 'key_sig':
                renderer.key_sig_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer key_sig_font_color to {hex_color}")
            elif category == 'measure_numbers':
                renderer.measure_numbers_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer measure_numbers_font_color to {hex_color}")
            elif category == 'barline_numbers':
                renderer.barline_numbers_font_color = hex_color
                print(f"COLOR_UPDATE: Updated renderer barline_numbers_font_color to {hex_color}")
            
            # Force immediate visual update
            staff_view.update()
            staff_view.repaint()
            print("COLOR_UPDATE: Updated staff view")
        else:
            print("COLOR_UPDATE: No staff view or renderer found")

    def is_dark_color(self, color):
        """Determine if a color is dark (for choosing contrasting text color)"""
        # Use luminance formula to determine if color is dark
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5
    
    def is_dark_color_hex(self, hex_color):
        """Determine if a hex color string is dark"""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Use luminance formula
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance < 0.5
        except:
            return True  # Default to dark if parsing fails
        
    def on_category_selected(self, row):
        """Handle category selection from the list"""
        if row >= 0:
            category = self.categories_list.item(row).text()
            # Here you would load the font settings for the selected category
            # For now, just print a message
            print(f"Selected category: {category}")
            
    def on_create_category(self):
        """Handle create category button click"""
        # Show input dialog for new category name
        category_name, ok = QInputDialog.getText(
            self, 
            "Create Category", 
            "Enter name for new text category:",
            text="New Category"
        )
        
        # Add the category if the user provided a name
        if ok and category_name.strip():
            # Check if this category already exists
            existing_items = [self.categories_list.item(i).text() 
                             for i in range(self.categories_list.count())]
            
            if category_name in existing_items:
                # Category already exists, select it
                for i in range(self.categories_list.count()):
                    if self.categories_list.item(i).text() == category_name:
                        self.categories_list.setCurrentRow(i)
                        break
            else:
                # Add new category and select it
                item = QListWidgetItem(category_name)
                self.categories_list.addItem(item)
                self.categories_list.setCurrentItem(item)
        
    def on_use_defaults_toggled(self, checked):
        """Handle use defaults checkbox toggle"""
        # Disable font controls if using defaults
        self.font_name_combo.setEnabled(not checked)
        self.style_combo.setEnabled(not checked)
        self.size_spin.setEnabled(not checked)
        
    def get_font_settings(self):
        """Get the font settings from the dialog"""
        selected_items = self.categories_list.selectedItems()
        if not selected_items:
            return None
            
        category = selected_items[0].text()
        use_default = self.use_defaults_check.isChecked()
        
        if use_default:
            return {
                'category': category,
                'use_default': True
            }
        else:
            return {
                'category': category,
                'use_default': False,
                'font_name': self.font_name_combo.currentText(),
                'font_style': self.style_combo.currentText(),
                'font_size': self.size_spin.value()
            }
            
    def get_layout_settings(self):
        """Get the document-specific layout settings from the dialog"""
        return {
            # Document layout
            'notation_scale': self.notation_size_spin.value(),
            'page_layout': self.page_layout_combo.currentText(),
            'measures_per_system': self.measures_system_spin.value(),
            'system_spacing': self.doc_system_spacing.value(),
            'staff_spacing': self.doc_staff_spacing.value(),
            
            # Measure number settings (comprehensive)
            'measure_number_frequency': self.measure_number_frequency.currentText(),
            'measure_numbers_custom_interval': self.measure_numbers_custom_interval.value(),
            'measure_numbers_position': self.measure_number_position.currentText(),
            'measure_numbers_vertical': self.measure_numbers_vertical.currentText(),
            'measure_numbers_vertical_offset': self.measure_numbers_vertical_offset.value(),
            'measure_numbers_horizontal_offset': self.measure_numbers_horizontal_offset.value(),
            'measure_numbers_font_size': self.measure_numbers_font_size.value(),
            
            # Other text and markings
            'staff_names': self.staff_names_combo.currentText(),
            'title_display': self.title_display_combo.currentText(),
            
            # Formatting
            'notation_style': self.notation_style_combo.currentText(),
            'barline_style': self.barline_style_combo.currentText(),
            'beam_style': self.beam_style_combo.currentText(),
            
            # Advanced options
            'justify_last_system': self.justify_last_system.isChecked(),
            'hide_empty_staves': self.hide_empty_staves.isChecked(),
            'optimize_page_turns': self.optimize_page_turns.isChecked()
        } 

    def load_current_settings(self):
        """Load current settings from document or preferences"""
        print("FULL_SCORE_OPTIONS: Loading current settings")
        
        # Update the title first
        self._update_title()
        
        def get_setting_with_precedence(key, default_value):
            # CRITICAL FIX: For saved documents, ALWAYS use document settings first
            # For new documents, prefer preferences (QSettings) over document settings
            if hasattr(self, 'document') and self.document and hasattr(self.document, 'settings'):
                # Check if this is a saved document (has filename) or new document
                is_saved_document = hasattr(self.document, 'filename') and self.document.filename
                
                if is_saved_document:
                    # SAVED DOCUMENT: Document settings take absolute precedence
                    if key in self.document.settings:
                        value = self.document.settings[key]
                        print(f"LOAD_SETTINGS: Using SAVED document setting {key}: {value}")
                        return value
                    # If not in document settings, use default (not preferences)
                    print(f"LOAD_SETTINGS: Saved document missing {key}, using default {default_value}")
                    return default_value
                else:
                    # NEW DOCUMENT: Use document settings first, then fall back to preferences
                    if key in self.document.settings:
                        value = self.document.settings[key]
                        print(f"LOAD_SETTINGS: Using document setting {key}: {value}")
                        return value
                    # Then try QSettings (preferences)
                    from PyQt6.QtCore import QSettings
                    qsettings = QSettings("ONOTE", "Preferences")
                    pref_value = qsettings.value(key, None)
                    if pref_value is not None:
                        print(f"LOAD_SETTINGS: Using preference setting {key}: {pref_value}")
                        return pref_value
                    print(f"LOAD_SETTINGS: New document, using default {key}: {default_value}")
                    return default_value
            else:
                # No document - use QSettings
                from PyQt6.QtCore import QSettings
                qsettings = QSettings("ONOTE", "Preferences")
                value = qsettings.value(key, default_value)
                print(f"LOAD_SETTINGS: No document, using preference {key}: {value}")
                return value
        
        # CRITICAL FIX: Temporarily disconnect all valueChanged signals to prevent
        # triggering update_score() while loading settings
        self._disconnect_value_changed_signals()
        
        try:
            # Load settings for widgets that exist in this dialog
            # Staff name settings - FIXED defaults to match Preferences factory defaults
            if hasattr(self, 'staff_name_font_size'):
                self.staff_name_font_size.setValue(int(get_setting_with_precedence('notation/staff_name_font_size', 10)))
            if hasattr(self, 'staff_name_vertical'):
                self.staff_name_vertical.setValue(int(get_setting_with_precedence('notation/staff_name_vertical', -8)))
            if hasattr(self, 'staff_name_horizontal'):
                self.staff_name_horizontal.setValue(int(get_setting_with_precedence('notation/staff_name_horizontal', 0)))
            
            # Section name settings - FIXED defaults to match Preferences factory defaults
            if hasattr(self, 'section_name_font_size'):
                self.section_name_font_size.setValue(int(get_setting_with_precedence('notation/section_name_font_size', 10)))
            if hasattr(self, 'section_name_vertical'):
                self.section_name_vertical.setValue(int(get_setting_with_precedence('notation/section_name_vertical', 0)))
            if hasattr(self, 'section_name_horizontal'):
                self.section_name_horizontal.setValue(int(get_setting_with_precedence('notation/section_name_horizontal', 0)))
            
            # Directions settings - FIXED defaults to match Preferences factory defaults
            if hasattr(self, 'directions_font_size'):
                self.directions_font_size.setValue(int(get_setting_with_precedence('notation/directions_font_size', 10)))
            if hasattr(self, 'directions_vertical'):
                self.directions_vertical.setValue(int(get_setting_with_precedence('notation/directions_vertical', 0)))
            if hasattr(self, 'directions_horizontal'):
                self.directions_horizontal.setValue(int(get_setting_with_precedence('notation/directions_horizontal', 0)))
            
            # Clef settings - FIXED defaults to match Preferences dialog exactly
            if hasattr(self, 'clef_font_size'):
                self.clef_font_size.setValue(int(get_setting_with_precedence('notation/clef_font_size', 32)))
            if hasattr(self, 'clef_vertical'):
                self.clef_vertical.setValue(int(get_setting_with_precedence('notation/clef_vertical', 0)))
            if hasattr(self, 'clef_horizontal'):
                self.clef_horizontal.setValue(int(get_setting_with_precedence('notation/clef_horizontal', 20)))
            
            # Time signature settings - FIXED defaults to match Preferences dialog exactly
            if hasattr(self, 'time_sig_font_size'):
                self.time_sig_font_size.setValue(int(get_setting_with_precedence('notation/time_sig_font_size', 24)))
            if hasattr(self, 'time_sig_vertical'):
                self.time_sig_vertical.setValue(int(get_setting_with_precedence('notation/time_sig_vertical', 0)))
            if hasattr(self, 'time_sig_horizontal'):
                self.time_sig_horizontal.setValue(int(get_setting_with_precedence('notation/time_sig_horizontal', 40)))
            if hasattr(self, 'time_sig_spacing'):
                self.time_sig_spacing.setValue(int(get_setting_with_precedence('notation/time_sig_spacing', 18)))
            
            # Key signature settings - FIXED defaults to match Preferences dialog exactly
            if hasattr(self, 'key_sig_font_size'):
                self.key_sig_font_size.setValue(int(get_setting_with_precedence('notation/key_sig_font_size', 14)))
            if hasattr(self, 'key_sig_vertical'):
                self.key_sig_vertical.setValue(int(get_setting_with_precedence('notation/key_sig_vertical', 0)))
            if hasattr(self, 'key_sig_horizontal'):
                self.key_sig_horizontal.setValue(int(get_setting_with_precedence('notation/key_sig_horizontal', 75)))
            if hasattr(self, 'key_sig_accidental_spacing'):
                self.key_sig_accidental_spacing.setValue(int(get_setting_with_precedence('notation/key_sig_accidental_spacing', 12)))
            
            # CRITICAL FIX: Load color settings and ALWAYS set the color_value attributes
            # This prevents the color reset bug when Apply is pressed
            if hasattr(self, 'staff_name_font_color'):
                color = get_setting_with_precedence('notation/staff_name_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading staff_name color: {color}")
                self.staff_name_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                # CRITICAL: Always set the color_value attribute to prevent reset to black
                self.staff_name_color_value = color
            
            if hasattr(self, 'section_name_font_color'):
                color = get_setting_with_precedence('notation/section_name_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading section_name color: {color}")
                self.section_name_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                # CRITICAL: Always set the color_value attribute to prevent reset to black
                self.section_name_color_value = color
            
            if hasattr(self, 'clef_font_color'):
                color = get_setting_with_precedence('notation/clef_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading clef color: {color}")
                self.clef_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                # CRITICAL: Always set the color_value attribute to prevent reset to black
                self.clef_color_value = color
            
            if hasattr(self, 'time_sig_font_color'):
                color = get_setting_with_precedence('notation/time_sig_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading time_sig color: {color}")
                self.time_sig_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                # CRITICAL: Always set the color_value attribute to prevent reset to black
                self.time_sig_color_value = color
            
            if hasattr(self, 'key_sig_font_color'):
                color = get_setting_with_precedence('notation/key_sig_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading key_sig color: {color}")
                self.key_sig_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                # CRITICAL: Always set the color_value attribute to prevent reset to black
                self.key_sig_color_value = color
            
            # Load measure numbers settings
            if hasattr(self, 'show_measure_numbers'):
                self.show_measure_numbers.setChecked(get_setting_with_precedence('notation/show_measure_numbers', True))
            if hasattr(self, 'measure_numbers_frequency'):
                self.measure_numbers_frequency.setCurrentText(get_setting_with_precedence('notation/measure_numbers_frequency', 'Every Measure'))
            if hasattr(self, 'measure_numbers_custom_interval'):
                self.measure_numbers_custom_interval.setValue(int(get_setting_with_precedence('notation/measure_numbers_custom_interval', 5)))
            if hasattr(self, 'measure_numbers_position'):
                self.measure_numbers_position.setCurrentText(get_setting_with_precedence('notation/measure_numbers_position', 'Center'))
            if hasattr(self, 'measure_numbers_vertical'):
                self.measure_numbers_vertical.setCurrentText(get_setting_with_precedence('notation/measure_numbers_vertical', 'Above System'))
            if hasattr(self, 'measure_numbers_font_size'):
                self.measure_numbers_font_size.setValue(int(get_setting_with_precedence('notation/measure_numbers_font_size', 10)))
            if hasattr(self, 'measure_numbers_vertical_offset'):
                self.measure_numbers_vertical_offset.setValue(int(get_setting_with_precedence('notation/measure_numbers_vertical_offset', -20)))
            if hasattr(self, 'measure_numbers_horizontal_offset'):
                self.measure_numbers_horizontal_offset.setValue(int(get_setting_with_precedence('notation/measure_numbers_horizontal_offset', -34)))
            
            if hasattr(self, 'measure_numbers_font_color'):
                color = get_setting_with_precedence('notation/measure_numbers_font_color', '#000000')
                print(f"LOAD_SETTINGS: Loading measure_numbers color: {color}")
                self.measure_numbers_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                self.measure_numbers_color_value = color
            
            # Load barline control settings
            if hasattr(self, 'max_measures_per_system'):
                self.max_measures_per_system.setValue(int(get_setting_with_precedence('notation/max_measures_per_system', 8)))
            if hasattr(self, 'barline_numbering'):
                self.barline_numbering.setChecked(get_setting_with_precedence('notation/barline_numbering', False))
            if hasattr(self, 'barline_number_font_size'):
                self.barline_number_font_size.setValue(int(get_setting_with_precedence('notation/barline_number_font_size', 8)))
            if hasattr(self, 'barline_number_vertical_offset'):
                self.barline_number_vertical_offset.setValue(int(get_setting_with_precedence('notation/barline_number_vertical_offset', 0)))
            if hasattr(self, 'barline_number_horizontal_offset'):
                self.barline_number_horizontal_offset.setValue(int(get_setting_with_precedence('notation/barline_number_horizontal_offset', 3)))
            
            if hasattr(self, 'barline_number_font_color'):
                color = get_setting_with_precedence('notation/barline_numbers_font_color', '#666666')
                print(f"LOAD_SETTINGS: Loading barline_numbers color: {color}")
                self.barline_number_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
                self.barline_numbers_color_value = color
            
        finally:
            # CRITICAL FIX: Reconnect all valueChanged signals after loading settings
            self._connect_value_changed_signals()
    
    def _disconnect_value_changed_signals(self):
        """Temporarily disconnect valueChanged signals to prevent loops during loading"""
        try:
            # Staff name signals
            self.staff_name_font_size.valueChanged.disconnect()
            self.staff_name_vertical.valueChanged.disconnect() 
            self.staff_name_horizontal.valueChanged.disconnect()
            
            # Section name signals
            self.section_name_font_size.valueChanged.disconnect()
            self.section_name_vertical.valueChanged.disconnect()
            self.section_name_horizontal.valueChanged.disconnect()
            
            # Directions signals
            self.directions_font_size.valueChanged.disconnect()
            self.directions_vertical.valueChanged.disconnect()
            self.directions_horizontal.valueChanged.disconnect()
            
            # Clef signals
            self.clef_font_size.valueChanged.disconnect()
            self.clef_vertical.valueChanged.disconnect()
            self.clef_horizontal.valueChanged.disconnect()
            
            # Time signature signals
            self.time_sig_font_size.valueChanged.disconnect()
            self.time_sig_vertical.valueChanged.disconnect()
            self.time_sig_horizontal.valueChanged.disconnect()
            self.time_sig_spacing.valueChanged.disconnect()
            
            # Key signature signals
            self.key_sig_font_size.valueChanged.disconnect()
            self.key_sig_vertical.valueChanged.disconnect()
            self.key_sig_horizontal.valueChanged.disconnect()
            self.key_sig_accidental_spacing.valueChanged.disconnect()
            
            # CRITICAL FIX: Disconnect measure numbers signals
            if hasattr(self, 'show_measure_numbers'):
                try:
                    self.show_measure_numbers.toggled.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_frequency'):
                try:
                    self.measure_numbers_frequency.currentTextChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_custom_interval'):
                try:
                    self.measure_numbers_custom_interval.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_position'):
                try:
                    self.measure_numbers_position.currentTextChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_vertical'):
                try:
                    self.measure_numbers_vertical.currentTextChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_font_size'):
                try:
                    self.measure_numbers_font_size.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_vertical_offset'):
                try:
                    self.measure_numbers_vertical_offset.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'measure_numbers_horizontal_offset'):
                try:
                    self.measure_numbers_horizontal_offset.valueChanged.disconnect()
                except:
                    pass
            
            # CRITICAL FIX: Disconnect barline control signals
            if hasattr(self, 'max_measures_per_system'):
                try:
                    self.max_measures_per_system.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'barline_numbering'):
                try:
                    self.barline_numbering.toggled.disconnect()
                except:
                    pass
            if hasattr(self, 'barline_number_font_size'):
                try:
                    self.barline_number_font_size.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'barline_number_vertical_offset'):
                try:
                    self.barline_number_vertical_offset.valueChanged.disconnect()
                except:
                    pass
            if hasattr(self, 'barline_number_horizontal_offset'):
                try:
                    self.barline_number_horizontal_offset.valueChanged.disconnect()
                except:
                    pass
            
            print("FULL_SCORE_OPTIONS: Disconnected all valueChanged signals")
        except Exception as e:
            print(f"FULL_SCORE_OPTIONS: Warning - some signals already disconnected: {e}")
    
    def _connect_value_changed_signals(self):
        """Connect valueChanged signals to isolated handlers (NO cross-contamination)"""
        try:
            # CRITICAL FIX: Connect to isolated handlers instead of update_score()
            
            # Staff name signals - ISOLATED
            self.staff_name_font_size.valueChanged.connect(self._on_staff_name_font_size_changed)
            self.staff_name_vertical.valueChanged.connect(self._on_staff_name_vertical_changed)
            self.staff_name_horizontal.valueChanged.connect(self._on_staff_name_horizontal_changed)
            
            # Section name signals - ISOLATED  
            self.section_name_font_size.valueChanged.connect(self._on_section_name_font_size_changed)
            self.section_name_vertical.valueChanged.connect(self._on_section_name_vertical_changed)
            self.section_name_horizontal.valueChanged.connect(self._on_section_name_horizontal_changed)
            
            # Clef signals - ISOLATED
            self.clef_font_size.valueChanged.connect(self._on_clef_font_size_changed)
            self.clef_vertical.valueChanged.connect(self._on_clef_vertical_changed)
            self.clef_horizontal.valueChanged.connect(self._on_clef_horizontal_changed)
            
            # Time signature signals - ISOLATED
            self.time_sig_font_size.valueChanged.connect(self._on_time_sig_font_size_changed)
            self.time_sig_vertical.valueChanged.connect(self._on_time_sig_vertical_changed)
            self.time_sig_horizontal.valueChanged.connect(self._on_time_sig_horizontal_changed)
            self.time_sig_spacing.valueChanged.connect(self._on_time_sig_spacing_changed)
            
            # Directions signals - ISOLATED
            self.directions_font_size.valueChanged.connect(self._on_directions_font_size_changed)
            self.directions_vertical.valueChanged.connect(self._on_directions_vertical_changed)
            self.directions_horizontal.valueChanged.connect(self._on_directions_horizontal_changed)
            
            # Key signature signals - ISOLATED
            self.key_sig_font_size.valueChanged.connect(self._on_key_sig_font_size_changed)
            self.key_sig_vertical.valueChanged.connect(self._on_key_sig_vertical_changed)
            self.key_sig_horizontal.valueChanged.connect(self._on_key_sig_horizontal_changed)
            self.key_sig_accidental_spacing.valueChanged.connect(self._on_key_sig_accidental_spacing_changed)
            
            # CRITICAL FIX: Connect measure numbers signals to isolated handlers
            if hasattr(self, 'show_measure_numbers'):
                self.show_measure_numbers.toggled.connect(self._on_show_measure_numbers_changed)
            if hasattr(self, 'measure_numbers_frequency'):
                self.measure_numbers_frequency.currentTextChanged.connect(self._on_measure_numbers_frequency_changed)
            if hasattr(self, 'measure_numbers_custom_interval'):
                self.measure_numbers_custom_interval.valueChanged.connect(self._on_measure_numbers_custom_interval_changed)
            if hasattr(self, 'measure_numbers_position'):
                self.measure_numbers_position.currentTextChanged.connect(self._on_measure_numbers_position_changed)
            if hasattr(self, 'measure_numbers_vertical'):
                self.measure_numbers_vertical.currentTextChanged.connect(self._on_measure_numbers_vertical_changed)
            if hasattr(self, 'measure_numbers_font_size'):
                self.measure_numbers_font_size.valueChanged.connect(self._on_measure_numbers_font_size_changed)
            if hasattr(self, 'measure_numbers_vertical_offset'):
                self.measure_numbers_vertical_offset.valueChanged.connect(self._on_measure_numbers_vertical_offset_changed)
            if hasattr(self, 'measure_numbers_horizontal_offset'):
                self.measure_numbers_horizontal_offset.valueChanged.connect(self._on_measure_numbers_horizontal_offset_changed)
            
            # CRITICAL FIX: Connect barline control signals to isolated handlers
            if hasattr(self, 'max_measures_per_system'):
                self.max_measures_per_system.valueChanged.connect(self._on_max_measures_per_system_changed)
            if hasattr(self, 'barline_numbering'):
                self.barline_numbering.toggled.connect(self._on_barline_numbering_changed)
            if hasattr(self, 'barline_number_font_size'):
                self.barline_number_font_size.valueChanged.connect(self._on_barline_number_font_size_changed)
            if hasattr(self, 'barline_number_vertical_offset'):
                self.barline_number_vertical_offset.valueChanged.connect(self._on_barline_number_vertical_offset_changed)
            if hasattr(self, 'barline_number_horizontal_offset'):
                self.barline_number_horizontal_offset.valueChanged.connect(self._on_barline_number_horizontal_offset_changed)
            
            print("FULL_SCORE_OPTIONS: Connected ISOLATED valueChanged signals (no cross-contamination)")
        except Exception as e:
            print(f"FULL_SCORE_OPTIONS: Error connecting isolated signals: {e}")

    def save_settings(self):
        """Save current settings to document and QSettings"""
        if not hasattr(self, 'document') or not self.document:
            return
        
        # Initialize document settings if not present
        if not hasattr(self.document, 'settings'):
            self.document.settings = {}
        
        # Save staff name settings - FIXED attribute names
        self.document.settings.update({
            'notation/staff_name_font_size': self.staff_name_font_size.value(),
            'notation/staff_name_vertical': self.staff_name_vertical.value(),
            'notation/staff_name_horizontal': self.staff_name_horizontal.value(),
            'notation/staff_name_font_color': getattr(self, 'staff_name_color_value', '#000000'),
        })
        
        # Save section name settings - FIXED attribute names
        self.document.settings.update({
            'notation/section_name_font_size': self.section_name_font_size.value(),
            'notation/section_name_vertical': self.section_name_vertical.value(),
            'notation/section_name_horizontal': self.section_name_horizontal.value(),
            'notation/section_name_font_color': getattr(self, 'section_name_color_value', '#000000'),
        })
        
        # Save directions settings
        self.document.settings.update({
            'notation/directions_font_size': self.directions_font_size.value(),
            'notation/directions_vertical': self.directions_vertical.value(),
            'notation/directions_horizontal': self.directions_horizontal.value(),
        })
        
        # Save clef settings
        clef_color = getattr(self, 'clef_color_value', '#000000')
        print(f"[DEBUG] save_settings: staff_name_color_value = {getattr(self, 'staff_name_color_value', None)}")
        print(f"[DEBUG] save_settings: section_name_color_value = {getattr(self, 'section_name_color_value', None)}")
        print(f"[DEBUG] save_settings: clef_color_value = {getattr(self, 'clef_color_value', None)}")
        print(f"[DEBUG] save_settings: key_sig_color_value = {getattr(self, 'key_sig_color_value', None)}")
        print(f"[DEBUG] save_settings: time_sig_color_value = {getattr(self, 'time_sig_color_value', None)}")
        self.document.settings.update({
            'notation/clef_font_size': self.clef_font_size.value(),
            'notation/clef_vertical': self.clef_vertical.value(),
            'notation/clef_horizontal': self.clef_horizontal.value(),
            'notation/clef_font_color': clef_color,
        })
        
        # Save time signature settings
        time_sig_color = getattr(self, 'time_sig_color_value', '#000000')
        print(f"SAVE_SETTINGS: Saving time_sig color: {time_sig_color}")
        self.document.settings.update({
            'notation/time_sig_font_size': self.time_sig_font_size.value(),
            'notation/time_sig_vertical': self.time_sig_vertical.value(),
            'notation/time_sig_horizontal': self.time_sig_horizontal.value(),
            'notation/time_sig_spacing': self.time_sig_spacing.value(),
            'notation/time_sig_font_color': time_sig_color,
        })
        
        # Save key signature settings
        key_sig_color = getattr(self, 'key_sig_color_value', '#000000')
        print(f"SAVE_SETTINGS: Saving key_sig color: {key_sig_color}")
        self.document.settings.update({
            'notation/key_sig_font_size': self.key_sig_font_size.value(),
            'notation/key_sig_vertical': self.key_sig_vertical.value(),
            'notation/key_sig_horizontal': self.key_sig_horizontal.value(),
            'notation/key_sig_accidental_spacing': self.key_sig_accidental_spacing.value(),
            'notation/key_sig_font_color': key_sig_color,
        })
        
        # Save measure numbers settings
        measure_numbers_color = getattr(self, 'measure_numbers_color_value', '#000000')
        self.document.settings.update({
            'notation/show_measure_numbers': self.show_measure_numbers.isChecked(),
            'notation/measure_numbers_frequency': self.measure_numbers_frequency.currentText(),
            'notation/measure_numbers_custom_interval': self.measure_numbers_custom_interval.value(),
            'notation/measure_numbers_position': self.measure_numbers_position.currentText(),
            'notation/measure_numbers_vertical': self.measure_numbers_vertical.currentText(),
            'notation/measure_numbers_font_size': self.measure_numbers_font_size.value(),
            'notation/measure_numbers_vertical_offset': self.measure_numbers_vertical_offset.value(),
            'notation/measure_numbers_horizontal_offset': self.measure_numbers_horizontal_offset.value(),
            'notation/measure_numbers_font_color': measure_numbers_color,
        })
        
        # Save barline control settings
        barline_numbers_color = getattr(self, 'barline_numbers_color_value', '#666666')
        self.document.settings.update({
            'notation/max_measures_per_system': self.max_measures_per_system.value(),
            'notation/barline_numbering': self.barline_numbering.isChecked(),
            'notation/barline_number_font_size': self.barline_number_font_size.value(),
            'notation/barline_number_vertical_offset': self.barline_number_vertical_offset.value(),
            'notation/barline_number_horizontal_offset': self.barline_number_horizontal_offset.value(),
            'notation/barline_numbers_font_color': barline_numbers_color,
        })
        
        # Save layout settings
        self.document.settings.update({
            'layout/notation_scale': self.notation_size_spin.value(),
            'layout/page_layout': self.page_layout_combo.currentText(),
            'layout/measures_per_system': self.measures_system_spin.value(),
            'layout/system_spacing': self.doc_system_spacing.value(),
            'layout/staff_spacing': self.doc_staff_spacing.value(),
            'layout/grand_staff_spacing': self.doc_grand_staff_spacing.value(),
        })
        
        # Mark document as modified
        if hasattr(self.document, 'set_modified'):
            self.document.set_modified(True)
        
        print("FULL_SCORE_OPTIONS: Saved notation and layout settings to document")


    
    def accept(self):
        """Override accept to save settings and close dialog"""
        print("[DIALOG] Dialog closing - saving final settings")
        self.save_settings()
        super().accept()



    def update_score(self):
        """Update the score with COMPLETE parameter isolation - no cross-effects"""
        print("FULL_SCORE_OPTIONS: update_score called with complete isolation")
        
        # CRITICAL: Prevent recursive update calls during update_score
        if hasattr(self, '_updating_score') and self._updating_score:
            print("FULL_SCORE_OPTIONS: Skipping recursive update_score call")
            return
        
        self._updating_score = True
        try:
            # Step 1: Save ALL current settings to document (isolated by parameter type)
            self.save_settings()
            
            # Step 2: Get staff view for updates
            staff_view = self._get_staff_view()
            if not staff_view:
                print("FULL_SCORE_OPTIONS: No staff view found for update")
                return
            
            # Step 3: Apply updates with complete isolation
            # Force renderer to reload settings with document precedence
            if hasattr(staff_view, 'renderer') and staff_view.renderer:
                print("FULL_SCORE_OPTIONS: Reloading renderer settings with document precedence")
                staff_view.renderer.load_notation_settings()
                
                # Refresh measure number manager if available
                if hasattr(staff_view.renderer, 'measure_number_manager') and staff_view.renderer.measure_number_manager:
                    staff_view.renderer.measure_number_manager.refresh_settings()
                    print("FULL_SCORE_OPTIONS: Refreshed measure number manager")
            
            # Force visual update
            staff_view.update()
            staff_view.repaint()
            print("FULL_SCORE_OPTIONS: Applied all updates with complete isolation")
            
        except Exception as e:
            print(f"FULL_SCORE_OPTIONS: Error in update_score: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._updating_score = False

    def set_as_defaults(self):
        """Save current settings as defaults for new documents"""
        from PyQt6.QtCore import QSettings
        
        print("SET_AS_DEFAULTS: Button clicked - function called")
        print("FULL_SCORE_OPTIONS: Starting set_as_defaults")
        
        # CRITICAL DEBUG: Check what color values we have before saving
        print(f"SET_AS_DEFAULTS: Current barline_numbers_color_value = {getattr(self, 'barline_numbers_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current staff_name_color_value = {getattr(self, 'staff_name_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current measure_numbers_color_value = {getattr(self, 'measure_numbers_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current section_name_color_value = {getattr(self, 'section_name_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current clef_color_value = {getattr(self, 'clef_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current time_sig_color_value = {getattr(self, 'time_sig_color_value', 'NOT SET')}")
        print(f"SET_AS_DEFAULTS: Current key_sig_color_value = {getattr(self, 'key_sig_color_value', 'NOT SET')}")
        
        # Save all current settings to QSettings for new documents
        settings = QSettings("ONOTE", "Preferences")
        
        # Staff name settings
        if hasattr(self, 'staff_name_font_size'):
            settings.setValue("notation/staff_name_font_size", self.staff_name_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving staff_name_font_size = {self.staff_name_font_size.value()}")
        if hasattr(self, 'staff_name_vertical'):
            settings.setValue("notation/staff_name_vertical", self.staff_name_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving staff_name_vertical = {self.staff_name_vertical.value()}")
        if hasattr(self, 'staff_name_horizontal'):
            settings.setValue("notation/staff_name_horizontal", self.staff_name_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving staff_name_horizontal = {self.staff_name_horizontal.value()}")
        staff_color = getattr(self, 'staff_name_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving staff_name_font_color = {staff_color}")
        settings.setValue("notation/staff_name_font_color", staff_color)
        
        # Staff names display option
        if hasattr(self, 'staff_names_combo'):
            settings.setValue("notation/staff_names_display", self.staff_names_combo.currentText())
            print(f"SET_AS_DEFAULTS: Saving staff_names_display = {self.staff_names_combo.currentText()}")
        
        # Section name settings
        if hasattr(self, 'section_name_font_size'):
            settings.setValue("notation/section_name_font_size", self.section_name_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving section_name_font_size = {self.section_name_font_size.value()}")
        if hasattr(self, 'section_name_vertical'):
            settings.setValue("notation/section_name_vertical", self.section_name_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving section_name_vertical = {self.section_name_vertical.value()}")
        if hasattr(self, 'section_name_horizontal'):
            settings.setValue("notation/section_name_horizontal", self.section_name_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving section_name_horizontal = {self.section_name_horizontal.value()}")
        section_color = getattr(self, 'section_name_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving section_name_font_color = {section_color}")
        settings.setValue("notation/section_name_font_color", section_color)
        
        # Clef settings
        if hasattr(self, 'clef_font_size'):
            settings.setValue("notation/clef_font_size", self.clef_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving clef_font_size = {self.clef_font_size.value()}")
        if hasattr(self, 'clef_vertical'):
            settings.setValue("notation/clef_vertical", self.clef_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving clef_vertical = {self.clef_vertical.value()}")
        if hasattr(self, 'clef_horizontal'):
            settings.setValue("notation/clef_horizontal", self.clef_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving clef_horizontal = {self.clef_horizontal.value()}")
        clef_color = getattr(self, 'clef_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving clef_font_color = {clef_color}")
        settings.setValue("notation/clef_font_color", clef_color)
        
        # Time signature settings
        if hasattr(self, 'time_sig_font_size'):
            settings.setValue("notation/time_sig_font_size", self.time_sig_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving time_sig_font_size = {self.time_sig_font_size.value()}")
        if hasattr(self, 'time_sig_vertical'):
            settings.setValue("notation/time_sig_vertical", self.time_sig_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving time_sig_vertical = {self.time_sig_vertical.value()}")
        if hasattr(self, 'time_sig_horizontal'):
            settings.setValue("notation/time_sig_horizontal", self.time_sig_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving time_sig_horizontal = {self.time_sig_horizontal.value()}")
        if hasattr(self, 'time_sig_spacing'):
            settings.setValue("notation/time_sig_spacing", self.time_sig_spacing.value())
            print(f"SET_AS_DEFAULTS: Saving time_sig_spacing = {self.time_sig_spacing.value()}")
        time_sig_color = getattr(self, 'time_sig_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving time_sig_font_color = {time_sig_color}")
        settings.setValue("notation/time_sig_font_color", time_sig_color)
        
        # Key signature settings
        if hasattr(self, 'key_sig_font_size'):
            settings.setValue("notation/key_sig_font_size", self.key_sig_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving key_sig_font_size = {self.key_sig_font_size.value()}")
        if hasattr(self, 'key_sig_vertical'):
            settings.setValue("notation/key_sig_vertical", self.key_sig_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving key_sig_vertical = {self.key_sig_vertical.value()}")
        if hasattr(self, 'key_sig_horizontal'):
            settings.setValue("notation/key_sig_horizontal", self.key_sig_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving key_sig_horizontal = {self.key_sig_horizontal.value()}")
        if hasattr(self, 'key_sig_accidental_spacing'):
            settings.setValue("notation/key_sig_accidental_spacing", self.key_sig_accidental_spacing.value())
            print(f"SET_AS_DEFAULTS: Saving key_sig_accidental_spacing = {self.key_sig_accidental_spacing.value()}")
        key_sig_color = getattr(self, 'key_sig_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving key_sig_font_color = {key_sig_color}")
        settings.setValue("notation/key_sig_font_color", key_sig_color)
        
        # Musical directions settings
        if hasattr(self, 'directions_font_size'):
            settings.setValue("notation/directions_font_size", self.directions_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving directions_font_size = {self.directions_font_size.value()}")
        if hasattr(self, 'directions_vertical'):
            settings.setValue("notation/directions_vertical", self.directions_vertical.value())
            print(f"SET_AS_DEFAULTS: Saving directions_vertical = {self.directions_vertical.value()}")
        if hasattr(self, 'directions_horizontal'):
            settings.setValue("notation/directions_horizontal", self.directions_horizontal.value())
            print(f"SET_AS_DEFAULTS: Saving directions_horizontal = {self.directions_horizontal.value()}")
        
        # Measure numbers settings
        if hasattr(self, 'show_measure_numbers'):
            settings.setValue("notation/show_measure_numbers", self.show_measure_numbers.isChecked())
            print(f"SET_AS_DEFAULTS: Saving show_measure_numbers = {self.show_measure_numbers.isChecked()}")
        if hasattr(self, 'measure_numbers_frequency'):
            settings.setValue("notation/measure_numbers_frequency", self.measure_numbers_frequency.currentText())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_frequency = {self.measure_numbers_frequency.currentText()}")
        if hasattr(self, 'measure_numbers_custom_interval'):
            settings.setValue("notation/measure_numbers_custom_interval", self.measure_numbers_custom_interval.value())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_custom_interval = {self.measure_numbers_custom_interval.value()}")
        if hasattr(self, 'measure_numbers_position'):
            settings.setValue("notation/measure_numbers_position", self.measure_numbers_position.currentText())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_position = {self.measure_numbers_position.currentText()}")
        if hasattr(self, 'measure_numbers_vertical'):
            settings.setValue("notation/measure_numbers_vertical", self.measure_numbers_vertical.currentText())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_vertical = {self.measure_numbers_vertical.currentText()}")
        if hasattr(self, 'measure_numbers_font_size'):
            settings.setValue("notation/measure_numbers_font_size", self.measure_numbers_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_font_size = {self.measure_numbers_font_size.value()}")
        if hasattr(self, 'measure_numbers_vertical_offset'):
            settings.setValue("notation/measure_numbers_vertical_offset", self.measure_numbers_vertical_offset.value())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_vertical_offset = {self.measure_numbers_vertical_offset.value()}")
        if hasattr(self, 'measure_numbers_horizontal_offset'):
            settings.setValue("notation/measure_numbers_horizontal_offset", self.measure_numbers_horizontal_offset.value())
            print(f"SET_AS_DEFAULTS: Saving measure_numbers_horizontal_offset = {self.measure_numbers_horizontal_offset.value()}")
        measure_numbers_color = getattr(self, 'measure_numbers_color_value', '#000000')
        print(f"SET_AS_DEFAULTS: Saving measure_numbers_font_color = {measure_numbers_color}")
        settings.setValue("notation/measure_numbers_font_color", measure_numbers_color)
        
        # Barline control settings
        if hasattr(self, 'max_measures_per_system'):
            settings.setValue("notation/max_measures_per_system", self.max_measures_per_system.value())
            print(f"SET_AS_DEFAULTS: Saving max_measures_per_system = {self.max_measures_per_system.value()}")
        if hasattr(self, 'barline_numbering'):
            settings.setValue("notation/barline_numbering", self.barline_numbering.isChecked())
            print(f"SET_AS_DEFAULTS: Saving barline_numbering = {self.barline_numbering.isChecked()}")
        if hasattr(self, 'barline_number_font_size'):
            settings.setValue("notation/barline_number_font_size", self.barline_number_font_size.value())
            print(f"SET_AS_DEFAULTS: Saving barline_number_font_size = {self.barline_number_font_size.value()}")
        if hasattr(self, 'barline_number_vertical_offset'):
            settings.setValue("notation/barline_number_vertical_offset", self.barline_number_vertical_offset.value())
            print(f"SET_AS_DEFAULTS: Saving barline_number_vertical_offset = {self.barline_number_vertical_offset.value()}")
        if hasattr(self, 'barline_number_horizontal_offset'):
            settings.setValue("notation/barline_number_horizontal_offset", self.barline_number_horizontal_offset.value())
            print(f"SET_AS_DEFAULTS: Saving barline_number_horizontal_offset = {self.barline_number_horizontal_offset.value()}")
        # DEBUG: Check what color value we're actually saving
        barline_color = getattr(self, 'barline_numbers_color_value', '#666666')
        print(f"SET_AS_DEFAULTS: Saving barline_numbers_font_color = {barline_color}")
        settings.setValue("notation/barline_numbers_font_color", barline_color)

        # Also persist Fonts tab defaults
        try:
            if hasattr(self, 'font_name_combo'):
                settings.setValue("fonts/default_font_name", self.font_name_combo.currentText())
            if hasattr(self, 'style_combo'):
                settings.setValue("fonts/default_font_style", self.style_combo.currentText())
            if hasattr(self, 'size_spin'):
                settings.setValue("fonts/default_font_size", self.size_spin.value())
        except Exception:
            pass

        # Also persist Layout tab defaults (application-wide)
        try:
            if hasattr(self, 'notation_size_spin'):
                settings.setValue("layout/default_notation_size", float(self.notation_size_spin.value()))
            if hasattr(self, 'measures_system_spin'):
                settings.setValue("notation/max_measures_per_system", int(self.measures_system_spin.value()))
                settings.setValue("layout/default_measures_per_system", int(self.measures_system_spin.value()))
            if hasattr(self, 'doc_system_spacing'):
                settings.setValue("layout/default_system_spacing", int(self.doc_system_spacing.value()))
                print(f"SET_AS_DEFAULTS: Saving system_spacing = {self.doc_system_spacing.value()}")
            if hasattr(self, 'doc_staff_spacing'):
                settings.setValue("layout/default_staff_spacing", int(self.doc_staff_spacing.value()))
                print(f"SET_AS_DEFAULTS: Saving staff_spacing = {self.doc_staff_spacing.value()}")
            if hasattr(self, 'page_layout_combo'):
                settings.setValue("layout/default_page_layout", self.page_layout_combo.currentText())
                print(f"SET_AS_DEFAULTS: Saving page_layout = {self.page_layout_combo.currentText()}")
            if hasattr(self, 'justify_last_system'):
                settings.setValue("layout/justify_last_system", bool(self.justify_last_system.isChecked()))
            if hasattr(self, 'hide_empty_staves'):
                settings.setValue("layout/hide_empty_staves", bool(self.hide_empty_staves.isChecked()))
        except Exception:
            pass
        
        # Force settings to be written to disk
        settings.sync()
        print("DEBUG: Called settings.sync() to write to disk")
        
        print("FULL_SCORE_OPTIONS: All notation settings saved as defaults")
        
        # CRITICAL FIX: Update any open Preferences dialog to reflect the new defaults
        # This ensures immediate visual consistency between dialogs
        self._sync_with_preferences_dialog()
        
        # CRITICAL FIX: Also force QSettings to sync immediately
        from PyQt6.QtCore import QSettings
        settings = QSettings("ONOTE", "Preferences")
        settings.sync()
        print("SET_AS_DEFAULTS: Forced QSettings sync to ensure immediate persistence")
        
        # Show confirmation to user with Cancel button
        reply = QMessageBox.question(
            self,
            "Settings Saved",
            "Current notation settings have been saved as defaults for new documents.\n\n"
            "These settings will be used when creating new scores and can be found in:\n"
            "Edit → Preferences → Default Notation Setup\n\n"
            "Continue?",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Ok
        )
        
        if reply != QMessageBox.StandardButton.Ok:
            print("SET_AS_DEFAULTS: User cancelled confirmation")
            return

    def _sync_with_preferences_dialog(self):
        """Sync current settings with any open Preferences dialog"""
        try:
            # Try to find and update any open Preferences dialog
            from PyQt6.QtWidgets import QApplication
            print(f"FULL_SCORE_OPTIONS: Searching for Preferences dialog among {len(QApplication.allWidgets())} widgets")
            for widget in QApplication.allWidgets():
                print(f"FULL_SCORE_OPTIONS: Checking widget {widget.__class__.__name__}")
                if widget.__class__.__name__ == 'PreferencesDialog':
                    print("FULL_SCORE_OPTIONS: Found open Preferences dialog, syncing settings")
                    
                    # CRITICAL FIX: Use the new load_from_full_score_options method for proper parameter isolation
                    if hasattr(widget, 'load_from_full_score_options'):
                        print("FULL_SCORE_OPTIONS: Calling load_from_full_score_options method")
                        widget.load_from_full_score_options(self)
                        print("FULL_SCORE_OPTIONS: Used load_from_full_score_options method for proper isolation")
                        # CRITICAL FIX: Force the Preferences dialog to save settings immediately
                        if hasattr(widget, 'save_settings'):
                            widget.save_settings()
                            print("FULL_SCORE_OPTIONS: Forced Preferences dialog to save settings")
                    else:
                        # Fallback to manual sync for backward compatibility
                        print("FULL_SCORE_OPTIONS: Using fallback manual sync method")
                        
                        # Staff name settings
                        if hasattr(widget, 'staff_name_font_size'):
                            widget.staff_name_font_size.setValue(self.staff_name_font_size.value())
                        if hasattr(widget, 'staff_name_vertical'):
                            widget.staff_name_vertical.setValue(self.staff_name_vertical.value())
                        if hasattr(widget, 'staff_name_horizontal'):
                            widget.staff_name_horizontal.setValue(self.staff_name_horizontal.value())
                        # Fix attribute naming consistency
                        staff_color = getattr(self, 'staff_name_color_value', '#000000')
                        if hasattr(widget, 'staff_names_color_value'):
                            widget.staff_names_color_value = staff_color
                        # Update button color with correct attribute
                        if hasattr(widget, 'staff_name_font_color'):
                            widget.staff_name_font_color.setStyleSheet(f"background-color: {staff_color}; color: white;")
                        
                        # Section name settings
                        if hasattr(widget, 'section_name_font_size'):
                            widget.section_name_font_size.setValue(self.section_name_font_size.value())
                        if hasattr(widget, 'section_name_vertical'):
                            widget.section_name_vertical.setValue(self.section_name_vertical.value())
                        if hasattr(widget, 'section_name_horizontal'):
                            widget.section_name_horizontal.setValue(self.section_name_horizontal.value())
                        # Fix attribute naming consistency
                        section_color = getattr(self, 'section_name_color_value', '#000000')
                        if hasattr(widget, 'section_names_color_value'):
                            widget.section_names_color_value = section_color
                        # Update button color with correct attribute
                        if hasattr(widget, 'section_name_font_color'):
                            widget.section_name_font_color.setStyleSheet(f"background-color: {section_color}; color: white;")
                        
                        # Time signature settings
                        if hasattr(widget, 'time_sig_font_size'):
                            widget.time_sig_font_size.setValue(self.time_sig_font_size.value())
                        if hasattr(widget, 'time_sig_vertical'):
                            widget.time_sig_vertical.setValue(self.time_sig_vertical.value())
                        if hasattr(widget, 'time_sig_horizontal'):
                            widget.time_sig_horizontal.setValue(self.time_sig_horizontal.value())
                        if hasattr(widget, 'time_sig_spacing'):
                            widget.time_sig_spacing.setValue(self.time_sig_spacing.value())
                        if hasattr(widget, 'time_sig_color_value'):
                            widget.time_sig_color_value = getattr(self, 'time_sig_color_value', '#000000')
                            # Update button color
                            if hasattr(widget, 'time_sig_font_color'):
                                widget.time_sig_font_color.setStyleSheet(f"background-color: {widget.time_sig_color_value}; color: white;")
                        
                        # Key signature settings
                        if hasattr(widget, 'key_sig_font_size'):
                            widget.key_sig_font_size.setValue(self.key_sig_font_size.value())
                        if hasattr(widget, 'key_sig_vertical'):
                            widget.key_sig_vertical.setValue(self.key_sig_vertical.value())
                        if hasattr(widget, 'key_sig_horizontal'):
                            widget.key_sig_horizontal.setValue(self.key_sig_horizontal.value())
                        if hasattr(widget, 'key_sig_accidental_spacing'):
                            widget.key_sig_accidental_spacing.setValue(self.key_sig_accidental_spacing.value())
                        if hasattr(widget, 'key_sig_color_value'):
                            widget.key_sig_color_value = getattr(self, 'key_sig_color_value', '#000000')
                            # Update button color
                            if hasattr(widget, 'key_sig_font_color'):
                                widget.key_sig_font_color.setStyleSheet(f"background-color: {widget.key_sig_color_value}; color: white;")
                        
                        # Clef settings
                        if hasattr(widget, 'clef_font_size'):
                            widget.clef_font_size.setValue(self.clef_font_size.value())
                        if hasattr(widget, 'clef_vertical'):
                            widget.clef_vertical.setValue(self.clef_vertical.value())
                        if hasattr(widget, 'clef_horizontal'):
                            widget.clef_horizontal.setValue(self.clef_horizontal.value())
                        if hasattr(widget, 'clef_color_value'):
                            widget.clef_color_value = getattr(self, 'clef_color_value', '#000000')
                            # Update button color
                            if hasattr(widget, 'clef_font_color'):
                                widget.clef_font_color.setStyleSheet(f"background-color: {widget.clef_color_value}; color: white;")
                        
                        # Musical directions settings
                        if hasattr(widget, 'directions_font_size'):
                            widget.directions_font_size.setValue(self.directions_font_size.value())
                        if hasattr(widget, 'directions_vertical'):
                            widget.directions_vertical.setValue(self.directions_vertical.value())
                        if hasattr(widget, 'directions_horizontal'):
                            widget.directions_horizontal.setValue(self.directions_horizontal.value())
                        
                        # CRITICAL FIX: Add missing measure numbers settings
                        if hasattr(widget, 'show_measure_numbers'):
                            widget.show_measure_numbers.setChecked(self.show_measure_numbers.isChecked())
                        if hasattr(widget, 'measure_numbers_frequency'):
                            widget.measure_numbers_frequency.setCurrentText(self.measure_numbers_frequency.currentText())
                        if hasattr(widget, 'measure_numbers_custom_interval'):
                            widget.measure_numbers_custom_interval.setValue(self.measure_numbers_custom_interval.value())
                        if hasattr(widget, 'measure_numbers_position'):
                            widget.measure_numbers_position.setCurrentText(self.measure_numbers_position.currentText())
                        if hasattr(widget, 'measure_numbers_vertical'):
                            widget.measure_numbers_vertical.setCurrentText(self.measure_numbers_vertical.currentText())
                        if hasattr(widget, 'measure_numbers_font_size'):
                            widget.measure_numbers_font_size.setValue(self.measure_numbers_font_size.value())
                        if hasattr(widget, 'measure_numbers_vertical_offset'):
                            widget.measure_numbers_vertical_offset.setValue(self.measure_numbers_vertical_offset.value())
                        if hasattr(widget, 'measure_numbers_horizontal_offset'):
                            widget.measure_numbers_horizontal_offset.setValue(self.measure_numbers_horizontal_offset.value())
                        # Update measure numbers color
                        measure_numbers_color = getattr(self, 'measure_numbers_color_value', '#000000')
                        if hasattr(widget, 'measure_numbers_color_value'):
                            widget.measure_numbers_color_value = measure_numbers_color
                        if hasattr(widget, 'measure_numbers_font_color'):
                            widget.measure_numbers_font_color.setStyleSheet(f"background-color: {measure_numbers_color}; color: white;")
                        
                        # CRITICAL FIX: Add missing barline control settings
                        if hasattr(widget, 'max_measures_per_system'):
                            widget.max_measures_per_system.setValue(self.max_measures_per_system.value())
                        if hasattr(widget, 'show_barline_numbers'):
                            widget.show_barline_numbers.setChecked(self.barline_numbering.isChecked())
                        if hasattr(widget, 'barline_number_font_size'):
                            widget.barline_number_font_size.setValue(self.barline_number_font_size.value())
                        if hasattr(widget, 'barline_number_vertical_offset'):
                            widget.barline_number_vertical_offset.setValue(self.barline_number_vertical_offset.value())
                        if hasattr(widget, 'barline_number_horizontal_offset'):
                            widget.barline_number_horizontal_offset.setValue(self.barline_number_horizontal_offset.value())
                        # Update barline numbers color
                        barline_color = getattr(self, 'barline_numbers_color_value', '#666666')
                        if hasattr(widget, 'barline_numbers_color_value'):
                            widget.barline_numbers_color_value = barline_color
                        if hasattr(widget, 'barline_number_font_color'):
                            widget.barline_number_font_color.setStyleSheet(f"background-color: {barline_color}; color: white;")
                    
                    print("FULL_SCORE_OPTIONS: Successfully synced with Preferences dialog")
                    break
        except Exception as e:
            print(f"FULL_SCORE_OPTIONS: Error syncing with Preferences dialog: {e}")

    def reset_to_defaults(self):
        """Reset all settings to the current Preferences defaults (not hard-coded constants)"""
        from PyQt6.QtWidgets import QMessageBox
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all notation settings to the current Preferences defaults?\n\n"
            "This will replace all current settings with those saved in Edit → Preferences.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            print("FULL_SCORE_OPTIONS: Resetting all settings to Preferences defaults")
            
            # CRITICAL FIX: Load settings from Preferences instead of hard-coded constants
            from PyQt6.QtCore import QSettings
            settings = QSettings("ONOTE", "Preferences")
            
            # CRITICAL FIX: Temporarily disconnect value change signals to prevent triggering update_score during reset
            self._disconnect_value_changed_signals()
            
            try:
                # Reset all notation settings to Preferences defaults
                # Staff name settings
                self.staff_name_font_size.setValue(int(settings.value("notation/staff_name_font_size", 10)))
                self.staff_name_vertical.setValue(int(settings.value("notation/staff_name_vertical", -8)))
                self.staff_name_horizontal.setValue(int(settings.value("notation/staff_name_horizontal", 0)))
                staff_name_color = settings.value("notation/staff_name_font_color", "#000000")
                self.staff_name_font_color.setStyleSheet(f"background-color: {staff_name_color}; color: white;")
                setattr(self, 'staff_name_color_value', staff_name_color)
                
                # Section name settings
                self.section_name_font_size.setValue(int(settings.value("notation/section_name_font_size", 10)))
                self.section_name_vertical.setValue(int(settings.value("notation/section_name_vertical", 0)))
                self.section_name_horizontal.setValue(int(settings.value("notation/section_name_horizontal", 0)))
                section_name_color = settings.value("notation/section_name_font_color", "#000000")
                self.section_name_font_color.setStyleSheet(f"background-color: {section_name_color}; color: white;")
                setattr(self, 'section_name_color_value', section_name_color)
                
                # Clef settings
                self.clef_font_size.setValue(int(settings.value("notation/clef_font_size", 32)))
                self.clef_vertical.setValue(int(settings.value("notation/clef_vertical", 0)))
                self.clef_horizontal.setValue(int(settings.value("notation/clef_horizontal", 20)))
                clef_color = settings.value("notation/clef_font_color", "#000000")
                self.clef_font_color.setStyleSheet(f"background-color: {clef_color}; color: white;")
                setattr(self, 'clef_color_value', clef_color)
                
                # Time signature settings
                self.time_sig_font_size.setValue(int(settings.value("notation/time_sig_font_size", 24)))
                self.time_sig_vertical.setValue(int(settings.value("notation/time_sig_vertical", 0)))
                self.time_sig_horizontal.setValue(int(settings.value("notation/time_sig_horizontal", 40)))
                self.time_sig_spacing.setValue(int(settings.value("notation/time_sig_spacing", 18)))
                time_sig_color = settings.value("notation/time_sig_font_color", "#000000")
                self.time_sig_font_color.setStyleSheet(f"background-color: {time_sig_color}; color: white;")
                setattr(self, 'time_sig_color_value', time_sig_color)
                
                # Key signature settings
                self.key_sig_font_size.setValue(int(settings.value("notation/key_sig_font_size", 14)))
                self.key_sig_vertical.setValue(int(settings.value("notation/key_sig_vertical", 0)))
                self.key_sig_horizontal.setValue(int(settings.value("notation/key_sig_horizontal", 75)))
                self.key_sig_accidental_spacing.setValue(int(settings.value("notation/key_sig_accidental_spacing", 12)))
                key_sig_color = settings.value("notation/key_sig_font_color", "#000000")
                self.key_sig_font_color.setStyleSheet(f"background-color: {key_sig_color}; color: white;")
                setattr(self, 'key_sig_color_value', key_sig_color)
                
                # Musical directions settings
                self.directions_font_size.setValue(int(settings.value("notation/directions_font_size", 10)))
                self.directions_vertical.setValue(int(settings.value("notation/directions_vertical", 0)))
                self.directions_horizontal.setValue(int(settings.value("notation/directions_horizontal", 0)))
                
                print("FULL_SCORE_OPTIONS: All settings reset to Preferences defaults")
                
            finally:
                # CRITICAL FIX: Reconnect value change signals
                self._connect_value_changed_signals()
            
            # Apply the reset settings immediately
            self.update_score()
            
            # Force immediate re-render by triggering temporal bridge signals
            try:
                if hasattr(self.parent(), 'staff_view') and hasattr(self.parent().staff_view, 'document'):
                    doc = self.parent().staff_view.document
                    # If temporal bridge exists, notify it
                    if hasattr(doc, 'temporal_bridge') and doc.temporal_bridge:
                        try:
                            doc.temporal_bridge.temporal_structure_changed.emit()
                            doc.temporal_bridge.measure_layout_changed.emit()
                        except Exception:
                            pass
                    # Also force staff view update
                    if hasattr(self.parent().staff_view, 'update'):
                        self.parent().staff_view.update()
            except Exception:
                pass
            
            # Show confirmation with Cancel button
            reply = QMessageBox.question(
                self,
                "Settings Reset",
                "All notation settings have been reset to the current Preferences defaults.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Ok
            )
            
            if reply != QMessageBox.StandardButton.Ok:
                print("RESET_TO_DEFAULTS: User cancelled confirmation")
                return

    def load_settings(self):
        """Load settings from document and QSettings"""
        if not self.document:
            return
        
        # Initialize settings
        from PyQt6.QtCore import QSettings
        qsettings = QSettings("ONOTE", "Preferences")
        
        # Helper function to get setting with precedence: document first, then QSettings, then default
        def get_setting_with_precedence(key, default_value):
            # First try document settings
            if hasattr(self.document, 'settings') and self.document.settings and key in self.document.settings:
                return self.document.settings[key]
            # Then try QSettings
            if qsettings.contains(key):
                return qsettings.value(key, default_value)
            # Finally use default
            return default_value
        
        try:
            # Load staff name settings
            self.staff_name_font_size.setValue(get_setting_with_precedence('notation/staff_name_font_size', 10))
            self.staff_name_vertical.setValue(get_setting_with_precedence('notation/staff_name_vertical', 0))
            self.staff_name_horizontal.setValue(get_setting_with_precedence('notation/staff_name_horizontal', 0))
            
            color = get_setting_with_precedence('notation/staff_name_font_color', '#000000')
            self.staff_name_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
            setattr(self, 'staff_name_color_value', color)
            
            # Load section name settings
            self.section_name_font_size.setValue(get_setting_with_precedence('notation/section_name_font_size', 10))
            self.section_name_vertical.setValue(get_setting_with_precedence('notation/section_name_vertical', 0))
            self.section_name_horizontal.setValue(get_setting_with_precedence('notation/section_name_horizontal', 0))
            
            color = get_setting_with_precedence('notation/section_name_font_color', '#000000')
            self.section_name_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
            setattr(self, 'section_name_color_value', color)
            
            # Load directions settings
            self.directions_font_size.setValue(get_setting_with_precedence('notation/directions_font_size', 10))
            self.directions_vertical.setValue(get_setting_with_precedence('notation/directions_vertical', 0))
            self.directions_horizontal.setValue(get_setting_with_precedence('notation/directions_horizontal', 0))
            
            # Load clef settings
            self.clef_font_size.setValue(get_setting_with_precedence('notation/clef_font_size', 10))
            self.clef_vertical.setValue(get_setting_with_precedence('notation/clef_vertical', 0))
            self.clef_horizontal.setValue(get_setting_with_precedence('notation/clef_horizontal', 0))
            
            color = get_setting_with_precedence('notation/clef_font_color', '#000000')
            print(f"LOAD_SETTINGS: Loading clef color: {color}")
            self.clef_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
            setattr(self, 'clef_color_value', color)
            
            # Load time signature settings
            self.time_sig_font_size.setValue(get_setting_with_precedence('notation/time_sig_font_size', 10))
            self.time_sig_vertical.setValue(get_setting_with_precedence('notation/time_sig_vertical', 0))
            self.time_sig_horizontal.setValue(get_setting_with_precedence('notation/time_sig_horizontal', 0))
            self.time_sig_spacing.setValue(get_setting_with_precedence('notation/time_sig_spacing', 0))
            
            color = get_setting_with_precedence('notation/time_sig_font_color', '#000000')
            print(f"LOAD_SETTINGS: Loading time_sig color: {color}")
            self.time_sig_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
            setattr(self, 'time_sig_color_value', color)
            
            # Load key signature settings
            self.key_sig_font_size.setValue(get_setting_with_precedence('notation/key_sig_font_size', 10))
            self.key_sig_vertical.setValue(get_setting_with_precedence('notation/key_sig_vertical', 0))
            self.key_sig_horizontal.setValue(get_setting_with_precedence('notation/key_sig_horizontal', 0))
            self.key_sig_accidental_spacing.setValue(get_setting_with_precedence('notation/key_sig_accidental_spacing', 0))
            
            color = get_setting_with_precedence('notation/key_sig_font_color', '#000000')
            print(f"LOAD_SETTINGS: Loading key_sig color: {color}")
            self.key_sig_font_color.setStyleSheet(f"background-color: {color}; color: {'white' if self.is_dark_color_hex(color) else 'black'};")
            setattr(self, 'key_sig_color_value', color)
            
            # Load layout settings
            self.notation_size_spin.setValue(get_setting_with_precedence('layout/notation_scale', 1.0))
            page_layout = get_setting_with_precedence('layout/page_layout', 'Single Page')
            if page_layout in ['Single Page', 'Facing Pages', 'Continuous Scroll']:
                self.page_layout_combo.setCurrentText(page_layout)
            self.measures_system_spin.setValue(get_setting_with_precedence('layout/measures_per_system', 5))
            self.doc_system_spacing.setValue(get_setting_with_precedence('layout/system_spacing', 80))
            self.doc_staff_spacing.setValue(get_setting_with_precedence('layout/staff_spacing', 40))
            self.doc_grand_staff_spacing.setValue(get_setting_with_precedence('layout/grand_staff_spacing', 32))
            
            # Note: Measure numbers and barline control settings are now handled in this dialog
            print("FULL_SCORE_OPTIONS: Loaded notation and layout settings from document and QSettings")
            
        except Exception as e:
            print(f"FULL_SCORE_OPTIONS: Error loading settings: {e}")
    
    def on_measure_numbers_frequency_changed(self, text):
        """Show/hide custom interval controls based on frequency selection"""
        if text == "Custom Interval":
            self.measure_numbers_custom_interval.setVisible(True)
        else:
            self.measure_numbers_custom_interval.setVisible(False) 

    def set_document(self, document):
        """Set the document for this dialog"""
        print(f"[DEBUG] Document set on dialog: {document}")
        self.document = document
        
        # Update the dialog title to include the filename
        self._update_title()
        
        # Load settings from the document
        self.load_current_settings()
    
    def _update_title(self):
        """Update the dialog title to include the filename if available"""
        if self.document and hasattr(self.document, 'filename') and self.document.filename:
            filename = os.path.basename(self.document.filename)
            self.setWindowTitle(f"Full Score Options - {filename}")
        else:
            self.setWindowTitle("Full Score Options")

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01) 

    def _get_staff_view(self):
        """Get staff view for score updates with comprehensive search"""
        parent_window = self.parent()
        if not parent_window:
            return None
        
        # Try multiple methods to find staff view
        if hasattr(parent_window, 'staff_view'):
            return parent_window.staff_view
        elif hasattr(parent_window, 'central_widget') and hasattr(parent_window.central_widget, 'staff_view'):
            return parent_window.central_widget.staff_view
        elif hasattr(parent_window, 'music_page') and hasattr(parent_window.music_page, 'staff_view'):
            return parent_window.music_page.staff_view
        
        # Fallback to ApplicationManager
        try:
            from ...application_manager import ApplicationManager
            app_manager = ApplicationManager()
            main_window = app_manager.get_main_window()
            if main_window and hasattr(main_window, 'staff_view'):
                return main_window.staff_view
            elif main_window and hasattr(main_window, 'central_widget') and hasattr(main_window.central_widget, 'staff_view'):
                return main_window.central_widget.staff_view
        except Exception:
            pass
        
        return None

    def _on_staff_name_font_size_changed(self, value):
        """Handle staff name font size change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_staff_name_font_size_changed: {value}")
        self._apply_single_parameter_change('staff_name_font_size', int(value))
    
    def _on_staff_name_vertical_changed(self, value):
        """Handle staff name vertical position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_staff_name_vertical_changed: {value}")
        self._apply_single_parameter_change('staff_name_vertical', int(value))
    
    def _on_staff_name_horizontal_changed(self, value):
        """Handle staff name horizontal position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_staff_name_horizontal_changed: {value}")
        self._apply_single_parameter_change('staff_name_horizontal', int(value))
    
    def _on_section_name_font_size_changed(self, value):
        """Handle section name font size change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_section_name_font_size_changed: {value}")
        self._apply_single_parameter_change('section_name_font_size', int(value))
    
    def _on_section_name_vertical_changed(self, value):
        """Handle section name vertical position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_section_name_vertical_changed: {value}")
        self._apply_single_parameter_change('section_name_vertical', int(value))
    
    def _on_section_name_horizontal_changed(self, value):
        """Handle section name horizontal position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_section_name_horizontal_changed: {value}")
        self._apply_single_parameter_change('section_name_horizontal', int(value))
    
    def _on_clef_font_size_changed(self, value):
        """Handle clef font size change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_clef_font_size_changed: {value}")
        self._apply_single_parameter_change('clef_font_size', int(value))
        
    def _on_clef_vertical_changed(self, value):
        """Handle clef vertical position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_clef_vertical_changed: {value}")
        self._apply_single_parameter_change('clef_vertical', int(value))
        
    def _on_clef_horizontal_changed(self, value):
        """Handle clef horizontal position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_clef_horizontal_changed: {value}")
        self._apply_single_parameter_change('clef_horizontal', int(value))
    
    def _on_time_sig_font_size_changed(self, value):
        """Handle time signature font size change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_time_sig_font_size_changed: {value}")
        self._apply_single_parameter_change('time_sig_font_size', int(value))
        
    def _on_time_sig_vertical_changed(self, value):
        """Handle time signature vertical position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_time_sig_vertical_changed: {value}")
        self._apply_single_parameter_change('time_sig_vertical', int(value))
        
    def _on_time_sig_horizontal_changed(self, value):
        """Handle time signature horizontal position change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_time_sig_horizontal_changed: {value}")
        self._apply_single_parameter_change('time_sig_horizontal', int(value))
        
    def _on_time_sig_spacing_changed(self, value):
        """Handle time signature spacing change in isolation"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_time_sig_spacing_changed: {value}")
        self._apply_single_parameter_change('time_sig_spacing', int(value))
    
    # CRITICAL FIX: Add missing isolated handlers for measure numbers
    def _on_show_measure_numbers_changed(self, checked):
        """Isolated handler for show measure numbers checkbox changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_show_measure_numbers_changed: {checked}")
        self._apply_single_parameter_change('show_measure_numbers', checked)
    
    def _on_measure_numbers_frequency_changed(self, text):
        """Isolated handler for measure numbers frequency changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_frequency_changed: {text}")
        self._apply_single_parameter_change('measure_numbers_frequency', text)
    
    def _on_measure_numbers_custom_interval_changed(self, value):
        """Isolated handler for measure numbers custom interval changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_custom_interval_changed: {value}")
        self._apply_single_parameter_change('measure_numbers_custom_interval', value)
    
    def _on_measure_numbers_position_changed(self, text):
        """Isolated handler for measure numbers position changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_position_changed: {text}")
        self._apply_single_parameter_change('measure_numbers_position', text)
    
    def _on_measure_numbers_vertical_changed(self, text):
        """Isolated handler for measure numbers vertical position changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_vertical_changed: {text}")
        self._apply_single_parameter_change('measure_numbers_vertical', text)
    
    def _on_measure_numbers_font_size_changed(self, value):
        """Isolated handler for measure numbers font size changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_font_size_changed: {value}")
        self._apply_single_parameter_change('measure_numbers_font_size', value)
    
    def _on_measure_numbers_vertical_offset_changed(self, value):
        """Isolated handler for measure numbers vertical offset changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_vertical_offset_changed: {value}")
        self._apply_single_parameter_change('measure_numbers_vertical_offset', value)
    
    def _on_measure_numbers_horizontal_offset_changed(self, value):
        """Isolated handler for measure numbers horizontal offset changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_measure_numbers_horizontal_offset_changed: {value}")
        self._apply_single_parameter_change('measure_numbers_horizontal_offset', value)
    
    # CRITICAL FIX: Add missing isolated handlers for barline controls
    def _on_max_measures_per_system_changed(self, value):
        """Isolated handler for max measures per system changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_max_measures_per_system_changed: {value}")
        self._apply_single_parameter_change('max_measures_per_system', value)
    
    def _on_barline_numbering_changed(self, checked):
        """Isolated handler for barline numbering checkbox changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_barline_numbering_changed: {checked}")
        self._apply_single_parameter_change('barline_numbering', checked)
    
    def _on_barline_number_font_size_changed(self, value):
        """Isolated handler for barline number font size changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_barline_number_font_size_changed: {value}")
        self._apply_single_parameter_change('barline_number_font_size', value)
    
    def _on_barline_number_vertical_offset_changed(self, value):
        """Isolated handler for barline number vertical offset changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_barline_number_vertical_offset_changed: {value}")
        self._apply_single_parameter_change('barline_number_vertical_offset', value)
    
    def _on_barline_number_horizontal_offset_changed(self, value):
        """Isolated handler for barline number horizontal offset changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_barline_number_horizontal_offset_changed: {value}")
        self._apply_single_parameter_change('barline_number_horizontal_offset', value)

    def _apply_single_parameter_change(self, parameter_key, value):
        """Apply a single parameter change without affecting others - COMPLETE ISOLATION"""
        # Push undo state for staff_name_font_size if not already pushed
        if parameter_key == 'staff_name_font_size':
            self._push_undo_state()
        print(f"ISOLATED_PARAM: Updating {parameter_key} = {value} with complete isolation")
        
        # Update snapshot after any setting change
        self._update_snapshot_after_change()
        
        # Save ONLY the specific parameter to document settings
        if hasattr(self, 'document') and self.document:
            if not hasattr(self.document, 'settings'):
                self.document.settings = {}
            
            # Save ONLY this specific parameter
            # Route layout-related parameters under the 'layout/' namespace
            layout_params = {'system_spacing', 'staff_spacing', 'measures_per_system'}
            key_namespace = 'layout' if parameter_key in layout_params else 'notation'
            full_key = f"{key_namespace}/{parameter_key}"
            old_value = self.document.settings.get(full_key, "not set")
            self.document.settings[full_key] = value
            print(f"ISOLATED_PARAM: Changed {full_key}: {old_value} -> {value}")
            
            # Mark document as modified
            if hasattr(self.document, 'set_modified'):
                self.document.set_modified(True)
            
            # Apply targeted renderer update WITHOUT full settings reload
            staff_view = self._get_staff_view()
            if staff_view and hasattr(staff_view, 'renderer') and staff_view.renderer:
                renderer = staff_view.renderer
                
                # CRITICAL FIX: Map dialog parameter keys to renderer attribute names
                # The renderer uses *_offset attributes for positions, not the exact parameter key
                parameter_mapping = {
                    # Staff name parameters
                    'staff_name_vertical': 'staff_name_vertical_offset',
                    'staff_name_horizontal': 'staff_name_horizontal_offset',
                    'staff_name_font_size': 'staff_name_font_size',
                    # Section name parameters  
                    'section_name_vertical': 'section_name_vertical_offset',
                    'section_name_horizontal': 'section_name_horizontal_offset',
                    'section_name_font_size': 'section_name_font_size',
                    # Clef parameters
                    'clef_vertical': 'clef_vertical_offset',
                    'clef_horizontal': 'clef_horizontal_offset', 
                    'clef_font_size': 'clef_font_size',
                    # Time signature parameters
                    'time_sig_vertical': 'time_sig_vertical_offset',
                    'time_sig_horizontal': 'time_sig_horizontal_offset',
                    'time_sig_font_size': 'time_sig_font_size',
                    'time_sig_spacing': 'time_sig_spacing',
                    # Key signature parameters
                    'key_sig_vertical': 'key_sig_vertical_offset',
                    'key_sig_horizontal': 'key_sig_horizontal_offset',
                    'key_sig_font_size': 'key_sig_font_size',
                    'key_sig_accidental_spacing': 'key_sig_accidental_spacing',
                    # Directions parameters
                    'directions_vertical': 'directions_vertical_offset',
                    'directions_horizontal': 'directions_horizontal_offset',
                    'directions_font_size': 'directions_font_size',
                    # Measure numbers parameters
                    'show_measure_numbers': 'show_measure_numbers',
                    'measure_numbers_frequency': 'measure_numbers_frequency',
                    'measure_numbers_custom_interval': 'measure_numbers_custom_interval',
                    'measure_numbers_position': 'measure_numbers_position',
                    'measure_numbers_vertical': 'measure_numbers_vertical',
                    'measure_numbers_font_size': 'measure_numbers_font_size',
                    'measure_numbers_vertical_offset': 'measure_numbers_vertical_offset',
                    'measure_numbers_horizontal_offset': 'measure_numbers_horizontal_offset',
                    # Barline control parameters
                    'max_measures_per_system': 'max_measures_per_system',
                    'barline_numbering': 'barline_numbering',
                    'barline_number_font_size': 'barline_number_font_size',
                    'barline_number_vertical_offset': 'barline_number_vertical_offset',
                    'barline_number_horizontal_offset': 'barline_number_horizontal_offset',
                    # Layout parameters
                    'notation_scale': 'notation_scale',
                    'page_layout': 'page_layout',
                    'measures_per_system': 'measures_per_system',
                    'system_spacing': 'system_spacing',
                    'staff_names': 'staff_names',
                    'title_display': 'title_display',
                    'notation_style': 'notation_style',
                    'barline_style': 'barline_style',
                    'beam_style': 'beam_style',
                    'justify_last_system': 'justify_last_system',
                    'hide_empty_staves': 'hide_empty_staves',
                    'optimize_page_turns': 'optimize_page_turns',
                    # Font parameters
                    'font_name': 'font_name',
                    'font_style': 'font_style',
                    'font_size': 'font_size',
                    'use_default_font': 'use_default_font',
                }
                
                # Get the correct renderer attribute name
                renderer_attribute = parameter_mapping.get(parameter_key, parameter_key)
                
                # CRITICAL FIX: Handle measure numbers settings specially
                if parameter_key.startswith('measure_numbers_') or parameter_key == 'show_measure_numbers':
                    # Measure numbers are managed by MeasureNumberManager, not direct renderer attributes
                    if hasattr(renderer, 'measure_number_manager') and renderer.measure_number_manager:
                        print(f"ISOLATED_PARAM: Refreshing measure number manager for {parameter_key}")
                        renderer.measure_number_manager.refresh_settings()
                    else:
                        print(f"ISOLATED_PARAM: No measure number manager found in renderer")
                else:
                    # Apply the parameter to the renderer attribute (if it exists)
                    if hasattr(renderer, renderer_attribute):
                        old_renderer_value = getattr(renderer, renderer_attribute, "not set")
                        setattr(renderer, renderer_attribute, value)
                        print(f"ISOLATED_PARAM: Changed renderer.{renderer_attribute}: {old_renderer_value} -> {value}")
                    else:
                        print(f"ISOLATED_PARAM: Renderer doesn't have attribute {renderer_attribute} (mapped from {parameter_key})")
                
                # For layout parameters, trigger a view refresh so spacing/wrapping updates immediately
                if parameter_key in layout_params:
                    # Update live layout object for immediate reflow where applicable
                    try:
                        if hasattr(self.document, 'layout') and self.document.layout:
                            layout_obj = self.document.layout
                            if parameter_key == 'staff_spacing' and hasattr(layout_obj, 'staff_spacing'):
                                setattr(layout_obj, 'staff_spacing', int(value))
                                if hasattr(layout_obj, '_update_positions'):
                                    layout_obj._update_positions()
                            if parameter_key == 'grand_staff_spacing' and hasattr(layout_obj, 'grand_staff_spacing'):
                                setattr(layout_obj, 'grand_staff_spacing', int(value))
                    except Exception as e:
                        print(f"ISOLATED_PARAM: Layout live update failed: {e}")
                    try:
                        staff_view.update()
                    except Exception:
                        pass
                # Force immediate visual refresh
                staff_view.update()
                print("ISOLATED_PARAM: Completed isolated parameter update and view refresh")
            else:
                print("ISOLATED_PARAM: No staff view found for immediate update")
        else:
            print("ISOLATED_PARAM: No document available")

    def _push_undo_state(self):
        """Push current state to undo stack."""
        if self._suppress_undo:
            print(f"[DEBUG] _push_undo_state: suppressed - dialog id: {id(self)}")
            return
        
        current_state = self._get_current_state()
        
        # Only push if different from last state
        if not self._undo_stack or self._undo_stack[-1] != current_state:
            self._undo_stack.append(copy.deepcopy(current_state))
            self._redo_stack.clear()  # Clear redo on new action
            print(f"[DEBUG] _push_undo_state: pushed, stack size now {len(self._undo_stack)} - dialog id: {id(self)}")
        else:
            print(f"[DEBUG] _push_undo_state: state unchanged, not pushed - dialog id: {id(self)}")

    def _undo(self):
        """Undo last action using proven working logic."""
        print(f"[DEBUG] _undo called - dialog id: {id(self)}")
        if len(self._undo_stack) < 2:
            print(f"[DEBUG] No undo states available (stack size: {len(self._undo_stack)})")
            return
        
        # Move current state to redo stack
        current_state = self._undo_stack.pop()
        self._redo_stack.append(current_state)
        
        # Restore previous state
        previous_state = self._undo_stack[-1]
        self._suppress_undo = True
        restored_count = self._set_state(previous_state)
        self._suppress_undo = False
        
        print(f"[DEBUG] Undo completed - restored {restored_count} controls")
        print(f"[DEBUG] Undo stack: {len(self._undo_stack)}, Redo stack: {len(self._redo_stack)}")

    def _redo(self):
        """Redo last undone action using proven working logic."""
        print(f"[DEBUG] _redo called - dialog id: {id(self)}")
        if not self._redo_stack:
            print(f"[DEBUG] No redo states available (stack size: {len(self._redo_stack)})")
            return
        
        # Move state from redo to undo stack
        state = self._redo_stack.pop()
        self._undo_stack.append(state)
        
        # Restore state
        self._suppress_undo = True
        restored_count = self._set_state(state)
        self._suppress_undo = False
        
        print(f"[DEBUG] Redo completed - restored {restored_count} controls")
        print(f"[DEBUG] Undo stack: {len(self._undo_stack)}, Redo stack: {len(self._redo_stack)}")

    def _mark_dirty(self):
        self._dirty = True

    def _get_current_state(self):
        # Return a dict of all relevant parameters
        return {
            # Staff name
            'staff_name_font_size': self.staff_name_font_size.value() if hasattr(self, 'staff_name_font_size') else None,
            'staff_name_vertical': self.staff_name_vertical.value() if hasattr(self, 'staff_name_vertical') else None,
            'staff_name_horizontal': self.staff_name_horizontal.value() if hasattr(self, 'staff_name_horizontal') else None,
            'staff_name_color_value': getattr(self, 'staff_name_color_value', None),
            # Section name
            'section_name_font_size': self.section_name_font_size.value() if hasattr(self, 'section_name_font_size') else None,
            'section_name_vertical': self.section_name_vertical.value() if hasattr(self, 'section_name_vertical') else None,
            'section_name_horizontal': self.section_name_horizontal.value() if hasattr(self, 'section_name_horizontal') else None,
            'section_name_color_value': getattr(self, 'section_name_color_value', None),
            # Directions
            'directions_font_size': self.directions_font_size.value() if hasattr(self, 'directions_font_size') else None,
            'directions_vertical': self.directions_vertical.value() if hasattr(self, 'directions_vertical') else None,
            'directions_horizontal': self.directions_horizontal.value() if hasattr(self, 'directions_horizontal') else None,
            # Clef
            'clef_font_size': self.clef_font_size.value() if hasattr(self, 'clef_font_size') else None,
            'clef_vertical': self.clef_vertical.value() if hasattr(self, 'clef_vertical') else None,
            'clef_horizontal': self.clef_horizontal.value() if hasattr(self, 'clef_horizontal') else None,
            'clef_color_value': getattr(self, 'clef_color_value', None),
            # Time signature
            'time_sig_font_size': self.time_sig_font_size.value() if hasattr(self, 'time_sig_font_size') else None,
            'time_sig_vertical': self.time_sig_vertical.value() if hasattr(self, 'time_sig_vertical') else None,
            'time_sig_horizontal': self.time_sig_horizontal.value() if hasattr(self, 'time_sig_horizontal') else None,
            'time_sig_spacing': self.time_sig_spacing.value() if hasattr(self, 'time_sig_spacing') else None,
            'time_sig_color_value': getattr(self, 'time_sig_color_value', None),
            # Key signature
            'key_sig_font_size': self.key_sig_font_size.value() if hasattr(self, 'key_sig_font_size') else None,
            'key_sig_vertical': self.key_sig_vertical.value() if hasattr(self, 'key_sig_vertical') else None,
            'key_sig_horizontal': self.key_sig_horizontal.value() if hasattr(self, 'key_sig_horizontal') else None,
            'key_sig_accidental_spacing': self.key_sig_accidental_spacing.value() if hasattr(self, 'key_sig_accidental_spacing') else None,
            'key_sig_color_value': getattr(self, 'key_sig_color_value', None),
            # Measure numbers
            'show_measure_numbers': self.show_measure_numbers.isChecked() if hasattr(self, 'show_measure_numbers') else None,
            'measure_numbers_frequency': self.measure_numbers_frequency.currentText() if hasattr(self, 'measure_numbers_frequency') else None,
            'measure_numbers_custom_interval': self.measure_numbers_custom_interval.value() if hasattr(self, 'measure_numbers_custom_interval') else None,
            'measure_numbers_position': self.measure_numbers_position.currentText() if hasattr(self, 'measure_numbers_position') else None,
            'measure_numbers_vertical': self.measure_numbers_vertical.currentText() if hasattr(self, 'measure_numbers_vertical') else None,
            'measure_numbers_font_size': self.measure_numbers_font_size.value() if hasattr(self, 'measure_numbers_font_size') else None,
            'measure_numbers_vertical_offset': self.measure_numbers_vertical_offset.value() if hasattr(self, 'measure_numbers_vertical_offset') else None,
            'measure_numbers_horizontal_offset': self.measure_numbers_horizontal_offset.value() if hasattr(self, 'measure_numbers_horizontal_offset') else None,
            'measure_numbers_color_value': getattr(self, 'measure_numbers_color_value', None),
            # Barline control
            'max_measures_per_system': self.max_measures_per_system.value() if hasattr(self, 'max_measures_per_system') else None,
            'barline_numbering': self.barline_numbering.isChecked() if hasattr(self, 'barline_numbering') else None,
            'barline_number_font_size': self.barline_number_font_size.value() if hasattr(self, 'barline_number_font_size') else None,
            'barline_number_vertical_offset': self.barline_number_vertical_offset.value() if hasattr(self, 'barline_number_vertical_offset') else None,
            'barline_number_horizontal_offset': self.barline_number_horizontal_offset.value() if hasattr(self, 'barline_number_horizontal_offset') else None,
            'barline_numbers_color_value': getattr(self, 'barline_numbers_color_value', None),
            # Layout parameters
            'notation_scale': self.notation_size_spin.value() if hasattr(self, 'notation_size_spin') else None,
            'page_layout': self.page_layout_combo.currentText() if hasattr(self, 'page_layout_combo') else None,
            'measures_per_system': self.measures_system_spin.value() if hasattr(self, 'measures_system_spin') else None,
            'system_spacing': self.doc_system_spacing.value() if hasattr(self, 'doc_system_spacing') else None,
            'staff_spacing': self.doc_staff_spacing.value() if hasattr(self, 'doc_staff_spacing') else None,
            'staff_names': self.staff_names_combo.currentText() if hasattr(self, 'staff_names_combo') else None,
            'title_display': self.title_display_combo.currentText() if hasattr(self, 'title_display_combo') else None,
            'notation_style': self.notation_style_combo.currentText() if hasattr(self, 'notation_style_combo') else None,
            'barline_style': self.barline_style_combo.currentText() if hasattr(self, 'barline_style_combo') else None,
            'beam_style': self.beam_style_combo.currentText() if hasattr(self, 'beam_style_combo') else None,
            'justify_last_system': self.justify_last_system.isChecked() if hasattr(self, 'justify_last_system') else None,
            'hide_empty_staves': self.hide_empty_staves.isChecked() if hasattr(self, 'hide_empty_staves') else None,
            'optimize_page_turns': self.optimize_page_turns.isChecked() if hasattr(self, 'optimize_page_turns') else None,
            # Font parameters
            'font_name': self.font_name_combo.currentText() if hasattr(self, 'font_name_combo') else None,
            'font_style': self.style_combo.currentText() if hasattr(self, 'style_combo') else None,
            'font_size': self.size_spin.value() if hasattr(self, 'size_spin') else None,
            'use_default_font': self.use_defaults_check.isChecked() if hasattr(self, 'use_defaults_check') else None,
        }



    def connect_undo_signals(self):
        """Connect all control change signals to the undo system."""
        print("[DEBUG] Connecting control signals to undo system...")
        
        # Connect all spinboxes, checkboxes, comboboxes to push undo states
        for widget in self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox)):
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self._push_undo_state)
            elif isinstance(widget, QCheckBox):
                widget.toggled.connect(self._push_undo_state)
            elif isinstance(widget, QComboBox):
                widget.currentIndexChanged.connect(self._push_undo_state)
        
        print(f"[DEBUG] Connected {len(self.findChildren((QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox)))} controls to undo system")

    def setup_undo_redo(self):
        """Set up undo/redo shortcuts using proven working approach."""
        print("[DEBUG] Setting up undo/redo shortcuts...")
        
        # Set up application-level event filter for both Ctrl+Z and Ctrl+Y (handles child widget focus issues)
        if hasattr(QApplication, 'instance') and QApplication.instance():
            QApplication.instance().installEventFilter(self)
            print("[DEBUG] Installed application-level event filter for both Ctrl+Z and Ctrl+Y")
        
        # Add manual test buttons for verification (you can remove these later)
        if hasattr(self, 'content_layout'):
            button_layout = QHBoxLayout()
            
            # Manual undo button for testing
            undo_button = QPushButton("Undo")
            undo_button.clicked.connect(self._undo)
            undo_button.setStyleSheet("background-color: #ff6b6b; color: white; padding: 5px; border-radius: 3px;")
            button_layout.addWidget(undo_button)
            
            # Manual redo button for testing
            redo_button = QPushButton("Redo")
            redo_button.clicked.connect(self._redo)
            redo_button.setStyleSheet("background-color: #4ecdc4; color: white; padding: 5px; border-radius: 3px;")
            button_layout.addWidget(redo_button)
            
            button_layout.addStretch()  # Push buttons to the left
            self.content_layout.addLayout(button_layout)
            
        print("[DEBUG] Undo/redo setup completed with manual test buttons and keyboard shortcuts")
    
    def eventFilter(self, obj, event):
        """Application-level event filter to catch keyboard shortcuts before other widgets."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.KeyPress:
            # Debug: Log key presses when Cmd or Ctrl is held
            if event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier):
                print(f"[DEBUG] eventFilter: Key={event.key()}, Modifiers={event.modifiers()}")
            
            # Handle Ctrl+Z for Undo (or Cmd+Z on Mac)
            if event.key() == Qt.Key.Key_Z and (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
                if not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    print("[DEBUG] Undo shortcut detected via eventFilter (Ctrl+Z or Cmd+Z)")
                    self._undo()
                    return True  # Consume the event
            
            # Handle Ctrl+Y for Redo (or Cmd+Y on Mac)
            if event.key() == Qt.Key.Key_Y and (event.modifiers() & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.MetaModifier)):
                print("[DEBUG] Redo shortcut detected via eventFilter (Ctrl+Y or Cmd+Y)")
                self._redo()
                return True  # Consume the event
                
        return super().eventFilter(obj, event)

    
    def _set_state(self, state):
        """Restore controls to a previous state."""
        print(f"[DEBUG] Restoring state with {len(state)} values")
        self._suppress_undo = True
        restored_count = 0
        
        try:
            # Restore each control by attribute name
            for attr_name, value in state.items():
                if value is not None and hasattr(self, attr_name):
                    widget = getattr(self, attr_name)
                    
                    # Skip color values for now (they need special handling)
                    if attr_name.endswith('_color_value'):
                        continue
                        
                    if hasattr(widget, 'setValue'):  # QSpinBox, QDoubleSpinBox
                        widget.setValue(value)
                        restored_count += 1
                    elif hasattr(widget, 'setChecked'):  # QCheckBox
                        widget.setChecked(value)
                        restored_count += 1
                    elif hasattr(widget, 'setCurrentText'):  # QComboBox with text values
                        widget.setCurrentText(value)
                        restored_count += 1
                    elif hasattr(widget, 'setCurrentIndex'):  # QComboBox with index values
                        widget.setCurrentIndex(value)
                        restored_count += 1
            
            # Update the score after restoring state
            if hasattr(self, 'update_score'):
                self.update_score()
                
        finally:
            self._suppress_undo = False
        
        print(f"[DEBUG] Restored {restored_count} controls")
        return restored_count

    # CRITICAL FIX: Add missing isolated handlers for directions and key signature
    def _on_directions_font_size_changed(self, value):
        """Isolated handler for directions font size changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_directions_font_size_changed: {value}")
        self._apply_single_parameter_change('directions_font_size', value)
    
    def _on_directions_vertical_changed(self, value):
        """Isolated handler for directions vertical changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_directions_vertical_changed: {value}")
        self._apply_single_parameter_change('directions_vertical', value)
    
    def _on_directions_horizontal_changed(self, value):
        """Isolated handler for directions horizontal changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_directions_horizontal_changed: {value}")
        self._apply_single_parameter_change('directions_horizontal', value)
    
    def _on_key_sig_font_size_changed(self, value):
        """Isolated handler for key signature font size changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_key_sig_font_size_changed: {value}")
        self._apply_single_parameter_change('key_sig_font_size', value)
    
    def _on_key_sig_vertical_changed(self, value):
        """Isolated handler for key signature vertical changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_key_sig_vertical_changed: {value}")
        self._apply_single_parameter_change('key_sig_vertical', value)
    
    def _on_key_sig_horizontal_changed(self, value):
        """Isolated handler for key signature horizontal changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_key_sig_horizontal_changed: {value}")
        self._apply_single_parameter_change('key_sig_horizontal', value)
    
    def _on_key_sig_accidental_spacing_changed(self, value):
        """Isolated handler for key signature accidental spacing changes"""
        if not getattr(self, '_suppress_undo', False):
            self._push_undo_state()
        print(f"[DEBUG] _on_key_sig_accidental_spacing_changed: {value}")
        self._apply_single_parameter_change('key_sig_accidental_spacing', value)

