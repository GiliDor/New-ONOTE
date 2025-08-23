from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QListWidget, QTabWidget,
                             QPushButton, QDialogButtonBox, QSpinBox, QDoubleSpinBox,
                             QGroupBox, QScrollArea, QWidget, QListWidgetItem,
                             QCheckBox, QSlider, QGridLayout, QToolBar, QToolButton, QMenu)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class NotationSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Notation Setup")
        self.setModal(False)  # Make modeless
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.dialog_zoom = 1.0

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

        self.setup_ui()

        # Instead of self.setLayout(main_layout), do:
        main_layout = QVBoxLayout()
        main_layout.addWidget(zoom_toolbar)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        self.scroll_area.setWidget(self.content_widget)
        self._set_dialog_zoom(1.0)

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01)

    def setup_ui(self):
        """Set up the dialog UI with tabs for different notation elements"""
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs for different notation elements
        self.clefs_tab = QWidget()
        self.time_signatures_tab = QWidget()
        self.accidentals_tab = QWidget()
        self.key_signatures_tab = QWidget()
        self.dynamics_tab = QWidget()
        self.tempo_tab = QWidget()
        self.form_tab = QWidget()
        self.misc_tab = QWidget()
        
        # Setup each tab
        self.setup_clefs_tab()
        self.setup_time_signatures_tab()
        self.setup_accidentals_tab()
        self.setup_key_signatures_tab()
        self.setup_dynamics_tab()
        self.setup_tempo_tab()
        self.setup_form_tab()
        self.setup_misc_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.clefs_tab, "Clefs")
        self.tab_widget.addTab(self.time_signatures_tab, "Time Signatures")
        self.tab_widget.addTab(self.accidentals_tab, "Accidentals")
        self.tab_widget.addTab(self.key_signatures_tab, "Key Signatures")
        self.tab_widget.addTab(self.dynamics_tab, "Dynamics")
        self.tab_widget.addTab(self.tempo_tab, "Tempo")
        self.tab_widget.addTab(self.form_tab, "Form")
        self.tab_widget.addTab(self.misc_tab, "Misc")
        
        # Add tab widget to main layout
        main_layout.addWidget(self.tab_widget)
        
        # Add standard dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def setup_common_adjustment_panel(self, parent_layout):
        """Setup common adjustment controls (size, position nudging)"""
        adjustment_group = QGroupBox("Adjustments")
        adjustment_layout = QGridLayout(adjustment_group)
        
        # Size adjustment
        size_label = QLabel("Size:")
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.5, 2.0)
        self.size_spin.setValue(1.0)
        self.size_spin.setSingleStep(0.1)
        
        # Vertical position adjustment
        v_pos_label = QLabel("Vertical Position:")
        self.v_pos_spin = QSpinBox()
        self.v_pos_spin.setRange(-20, 20)
        self.v_pos_spin.setValue(0)
        
        # Horizontal position adjustment
        h_pos_label = QLabel("Horizontal Position:")
        self.h_pos_spin = QSpinBox()
        self.h_pos_spin.setRange(-20, 20)
        self.h_pos_spin.setValue(0)
        
        # Set as default button
        self.set_default_button = QPushButton("Set as Default")
        self.set_default_button.clicked.connect(self.on_set_default)
        
        # Add to layout
        adjustment_layout.addWidget(size_label, 0, 0)
        adjustment_layout.addWidget(self.size_spin, 0, 1)
        adjustment_layout.addWidget(v_pos_label, 1, 0)
        adjustment_layout.addWidget(self.v_pos_spin, 1, 1)
        adjustment_layout.addWidget(h_pos_label, 2, 0)
        adjustment_layout.addWidget(self.h_pos_spin, 2, 1)
        adjustment_layout.addWidget(self.set_default_button, 3, 0, 1, 2)
        
        parent_layout.addWidget(adjustment_group)
        
    def setup_clefs_tab(self):
        """Set up the Clefs tab"""
        layout = QVBoxLayout(self.clefs_tab)
        
        # Clef selection
        clefs_group = QGroupBox("Clef Type")
        clefs_layout = QVBoxLayout(clefs_group)
        
        self.clefs_list = QListWidget()
        self.clefs_list.addItems([
            "Treble (G clef)",
            "Bass (F clef)",
            "Alto (C clef)",
            "Tenor (C clef)",
            "Percussion (Neutral clef)",
            "TAB (Tablature)"
        ])
        clefs_layout.addWidget(self.clefs_list)
        layout.addWidget(clefs_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_time_signatures_tab(self):
        """Set up the Time Signatures tab"""
        layout = QVBoxLayout(self.time_signatures_tab)
        
        # Time signature configuration
        time_sig_group = QGroupBox("Time Signature")
        time_sig_layout = QGridLayout(time_sig_group)
        
        # Numerator (beat number)
        beat_label = QLabel("Beats:")
        self.beat_spin = QSpinBox()
        self.beat_spin.setRange(1, 32)
        self.beat_spin.setValue(4)
        
        # Denominator (unit value)
        unit_label = QLabel("Beat Unit:")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["1", "2", "4", "8", "16", "32"])
        self.unit_combo.setCurrentText("4")
        
        # Beam grouping checkbox
        self.auto_beam_check = QCheckBox("Automatic Beam Grouping")
        self.auto_beam_check.setChecked(True)
        
        # Add to layout
        time_sig_layout.addWidget(beat_label, 0, 0)
        time_sig_layout.addWidget(self.beat_spin, 0, 1)
        time_sig_layout.addWidget(unit_label, 1, 0)
        time_sig_layout.addWidget(self.unit_combo, 1, 1)
        time_sig_layout.addWidget(self.auto_beam_check, 2, 0, 1, 2)
        
        layout.addWidget(time_sig_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_accidentals_tab(self):
        """Set up the Accidentals tab"""
        layout = QVBoxLayout(self.accidentals_tab)
        
        # Accidental selection
        accidentals_group = QGroupBox("Accidental Type")
        accidentals_layout = QVBoxLayout(accidentals_group)
        
        self.accidentals_list = QListWidget()
        self.accidentals_list.addItems([
            "Sharp (♯)",
            "Flat (♭)",
            "Natural (♮)",
            "Double Sharp (𝄪)",
            "Double Flat (𝄫)"
        ])
        accidentals_layout.addWidget(self.accidentals_list)
        layout.addWidget(accidentals_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_key_signatures_tab(self):
        """Set up the Key Signatures tab"""
        layout = QVBoxLayout(self.key_signatures_tab)
        
        # Key selection
        keys_group = QGroupBox("Key")
        keys_layout = QGridLayout(keys_group)
        
        # Major/minor radio buttons can be added here
        
        # Key selection
        key_label = QLabel("Key:")
        self.key_combo = QComboBox()
        self.key_combo.addItems([
            "C major / A minor (no accidentals)",
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
        
        keys_layout.addWidget(key_label, 0, 0)
        keys_layout.addWidget(self.key_combo, 0, 1)
        
        layout.addWidget(keys_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_dynamics_tab(self):
        """Set up the Dynamics tab"""
        layout = QVBoxLayout(self.dynamics_tab)
        
        # Dynamic marking selection
        dynamics_group = QGroupBox("Dynamic Markings")
        dynamics_layout = QVBoxLayout(dynamics_group)
        
        self.dynamics_list = QListWidget()
        self.dynamics_list.addItems([
            "fff (Fortississimo)",
            "ff (Fortissimo)",
            "f (Forte)",
            "mf (Mezzo Forte)",
            "mp (Mezzo Piano)",
            "p (Piano)",
            "pp (Pianissimo)",
            "ppp (Pianississimo)",
            "Crescendo Hairpin",
            "Diminuendo Hairpin",
            "sfz (Sforzando)",
            "fp (Forte-piano)"
        ])
        dynamics_layout.addWidget(self.dynamics_list)
        layout.addWidget(dynamics_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_tempo_tab(self):
        """Set up the Tempo tab"""
        layout = QVBoxLayout(self.tempo_tab)
        
        # Tempo marking selection
        tempo_group = QGroupBox("Tempo Markings")
        tempo_layout = QVBoxLayout(tempo_group)
        
        self.tempo_list = QListWidget()
        self.tempo_list.addItems([
            "Adagio",
            "Andante",
            "Moderato",
            "Allegro",
            "Presto",
            "accel. (accelerando)",
            "rit. (ritardando)",
            "a tempo",
            "Metronome marking"
        ])
        tempo_layout.addWidget(self.tempo_list)
        layout.addWidget(tempo_group)
        
        # Metronome marking
        metronome_group = QGroupBox("Metronome Marking")
        metronome_layout = QHBoxLayout(metronome_group)
        
        self.metronome_spin = QSpinBox()
        self.metronome_spin.setRange(40, 240)
        self.metronome_spin.setValue(120)
        
        self.beat_unit_combo = QComboBox()
        self.beat_unit_combo.addItems(["♩", "♪", "♩.", "𝅗𝅥"])
        
        metronome_layout.addWidget(QLabel("BPM:"))
        metronome_layout.addWidget(self.metronome_spin)
        metronome_layout.addWidget(QLabel("="))
        metronome_layout.addWidget(self.beat_unit_combo)
        
        layout.addWidget(metronome_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_form_tab(self):
        """Set up the Form tab"""
        layout = QVBoxLayout(self.form_tab)
        
        # Form marking selection
        form_group = QGroupBox("Form Markings")
        form_layout = QVBoxLayout(form_group)
        
        self.form_list = QListWidget()
        self.form_list.addItems([
            "Repeat Barline (start/end)",
            "D.S. (Dal Segno)",
            "D.C. (Da Capo)",
            "D.S. al Coda",
            "D.S. al Fine",
            "D.C. al Coda",
            "D.C. al Fine",
            "Segno",
            "Coda",
            "Fine"
        ])
        form_layout.addWidget(self.form_list)
        layout.addWidget(form_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def setup_misc_tab(self):
        """Set up the Miscellaneous tab"""
        layout = QVBoxLayout(self.misc_tab)
        
        # Music fonts
        fonts_group = QGroupBox("Music Fonts")
        fonts_layout = QVBoxLayout(fonts_group)
        
        self.fonts_combo = QComboBox()
        self.fonts_combo.addItems([
            "Default",
            "Bravura",
            "Gonville",
            "Petaluma",
            "Emmentaler",
            "Leipzig"
        ])
        fonts_layout.addWidget(self.fonts_combo)
        layout.addWidget(fonts_group)
        
        # Staff line thickness
        staff_line_group = QGroupBox("Staff Line Thickness")
        staff_line_layout = QVBoxLayout(staff_line_group)
        
        self.staff_line_spin = QDoubleSpinBox()
        self.staff_line_spin.setRange(0.5, 2.0)
        self.staff_line_spin.setValue(1.0)
        self.staff_line_spin.setSingleStep(0.1)
        staff_line_layout.addWidget(self.staff_line_spin)
        layout.addWidget(staff_line_group)
        
        # Add common adjustment panel
        self.setup_common_adjustment_panel(layout)
        
        # Add spacing
        layout.addStretch()
    
    def on_set_default(self):
        """Handle 'Set as Default' button click"""
        # Get the currently selected tab
        current_tab = self.tab_widget.currentWidget()
        current_tab_name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        
        # Get the currently selected item in the tab's list (if applicable)
        selected_item = None
        if current_tab == self.clefs_tab and self.clefs_list.currentItem():
            selected_item = self.clefs_list.currentItem().text()
        elif current_tab == self.accidentals_tab and self.accidentals_list.currentItem():
            selected_item = self.accidentals_list.currentItem().text()
        elif current_tab == self.dynamics_tab and self.dynamics_list.currentItem():
            selected_item = self.dynamics_list.currentItem().text()
        elif current_tab == self.tempo_tab and self.tempo_list.currentItem():
            selected_item = self.tempo_list.currentItem().text()
        elif current_tab == self.form_tab and self.form_list.currentItem():
            selected_item = self.form_list.currentItem().text()
        
        # For time signatures and key signatures, get the current settings
        if current_tab == self.time_signatures_tab:
            selected_item = f"{self.beat_spin.value()}/{self.unit_combo.currentText()}"
        elif current_tab == self.key_signatures_tab:
            selected_item = self.key_combo.currentText()
            
        # For the misc tab, use the font selection
        if current_tab == self.misc_tab:
            selected_item = self.fonts_combo.currentText()
        
        # Get the adjustment values
        size = self.size_spin.value()
        v_pos = self.v_pos_spin.value()
        h_pos = self.h_pos_spin.value()
        
        # Save these as default settings (would be implemented to save to config)
        print(f"Setting default for {current_tab_name}: {selected_item}")
        print(f"Size: {size}, Vertical: {v_pos}, Horizontal: {h_pos}")
        
    def get_notation_settings(self):
        """Get all notation settings from the dialog"""
        settings = {
            'clefs': {
                'selected': self.clefs_list.currentItem().text() if self.clefs_list.currentItem() else None,
                'size': self.size_spin.value(),
                'v_pos': self.v_pos_spin.value(),
                'h_pos': self.h_pos_spin.value()
            },
            'time_signatures': {
                'beats': self.beat_spin.value(),
                'unit': self.unit_combo.currentText(),
                'auto_beam': self.auto_beam_check.isChecked(),
                'size': self.size_spin.value(),
                'v_pos': self.v_pos_spin.value(),
                'h_pos': self.h_pos_spin.value()
            },
            # Add other tab settings similarly
            'misc': {
                'font': self.fonts_combo.currentText(),
                'staff_line_thickness': self.staff_line_spin.value(),
                'size': self.size_spin.value(),
                'v_pos': self.v_pos_spin.value(),
                'h_pos': self.h_pos_spin.value()
            }
        }
        return settings 