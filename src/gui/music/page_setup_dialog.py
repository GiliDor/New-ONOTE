from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QComboBox, QGroupBox, QSpinBox, QCheckBox, 
                            QFormLayout, QTabWidget, QWidget, QDialogButtonBox,
                            QDoubleSpinBox, QSlider, QFrame, QGridLayout, QButtonGroup,
                            QRadioButton, QSizePolicy, QScrollArea, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen
from src.core.settings_manager import settings

class PagePreviewWidget(QWidget):
    """Widget to show a preview of the page layout"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(200, 280)
        self.setMaximumSize(200, 280)
        self.page_type = "A4"
        self.orientation = "Portrait"
        self.margins = {'top': 20, 'bottom': 20, 'left': 25, 'right': 25}
        
    def set_page_settings(self, page_type, orientation, margins):
        """Update page settings and refresh preview"""
        self.page_type = page_type
        self.orientation = orientation
        self.margins = margins.copy()
        self.update()
        
    def paintEvent(self, event):
        """Draw the page preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate preview dimensions
        preview_rect = self.rect().adjusted(10, 10, -10, -10)
        
        # Determine page aspect ratio
        page_ratios = {
            "A4": (1.0, 1.414),
            "A3": (1.414, 1.0),
            "Letter": (1.0, 1.294),
            "Legal": (1.0, 1.647),
            "Tabloid": (1.294, 1.0)
        }
        
        ratio = page_ratios.get(self.page_type, (1.0, 1.414))
        if self.orientation == "Landscape":
            ratio = (ratio[1], ratio[0])
            
        # Calculate actual preview size
        if ratio[0] / ratio[1] > preview_rect.width() / preview_rect.height():
            # Width-constrained
            width = preview_rect.width()
            height = int(width * ratio[1] / ratio[0])
        else:
            # Height-constrained
            height = preview_rect.height()
            width = int(height * ratio[0] / ratio[1])
            
        # Center the preview
        x = (self.width() - width) // 2
        y = (self.height() - height) // 2
        
        # Draw page background
        painter.fillRect(x, y, width, height, QColor(255, 255, 255))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(x, y, width, height)
        
        # Draw margins
        margin_left = int(width * self.margins['left'] / 100)
        margin_right = int(width * self.margins['right'] / 100)
        margin_top = int(height * self.margins['top'] / 100)
        margin_bottom = int(height * self.margins['bottom'] / 100)
        
        painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.PenStyle.DashLine))
        painter.drawRect(x + margin_left, y + margin_top, 
                        width - margin_left - margin_right,
                        height - margin_top - margin_bottom)
        
        # Draw some staff lines to represent content
        content_rect = (x + margin_left + 10, y + margin_top + 10,
                       width - margin_left - margin_right - 20,
                       height - margin_top - margin_bottom - 20)
        
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        staff_count = 4
        staff_spacing = content_rect[3] // (staff_count + 1)
        
        for i in range(staff_count):
            staff_y = content_rect[1] + (i + 1) * staff_spacing
            for line in range(5):
                line_y = staff_y + line * 2
                painter.drawLine(content_rect[0], line_y, 
                               content_rect[0] + content_rect[2], line_y)

class PageSetupDialog(QDialog):
    """Enhanced page setup dialog with comprehensive options"""
    
    settings_changed = pyqtSignal(dict)  # Signal emitted when settings change
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Page Setup")
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        self.setup_ui()
        self.load_settings()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the dialog UI with tabs and comprehensive options"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Left side: Settings tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Page tab
        self.page_tab = QWidget()
        self.setup_page_tab()
        self.tab_widget.addTab(self.page_tab, "Page")
        
        # Margins tab
        self.margins_tab = QWidget()
        self.setup_margins_tab()
        self.tab_widget.addTab(self.margins_tab, "Margins")
        
        # Print Options tab
        self.print_tab = QWidget()
        self.setup_print_tab()
        self.tab_widget.addTab(self.print_tab, "Print Options")
        
        left_layout.addWidget(self.tab_widget)
        
        # Dialog buttons (Close only; changes apply immediately)
        button_box = QDialogButtonBox()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept_settings)
        button_box.addButton(close_button, QDialogButtonBox.ButtonRole.RejectRole)
        left_layout.addWidget(button_box)
        
        main_layout.addWidget(left_widget, 2)
        
        # Right side: Preview
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        preview_label = QLabel("Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(preview_label)
        
        self.preview_widget = PagePreviewWidget()
        right_layout.addWidget(self.preview_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Add defaults button
        defaults_button = QPushButton("Set as Default")
        defaults_button.clicked.connect(self.save_as_defaults)
        right_layout.addWidget(defaults_button)
        
        right_layout.addStretch()
        
        main_layout.addWidget(right_widget, 1)
        
    def setup_page_tab(self):
        """Setup the Page tab with page size and orientation options"""
        layout = QVBoxLayout(self.page_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Page Size group
        size_group = QGroupBox("Page Size")
        size_layout = QFormLayout(size_group)
        size_layout.setSpacing(10)
        
        # Standard page sizes
        self.page_type_combo = QComboBox()
        self.page_type_combo.addItems([
            "A4 (210 × 297 mm)",
            "A3 (297 × 420 mm)", 
            "Letter (8.5 × 11 in)",
            "Legal (8.5 × 14 in)",
            "Tabloid (11 × 17 in)"
        ])
        self.page_type_combo.setCurrentText("A4 (210 × 297 mm)")
        size_layout.addRow("Paper Size:", self.page_type_combo)
        
        # Custom size option (for future expansion)
        self.custom_width = QDoubleSpinBox()
        self.custom_width.setRange(50.0, 500.0)
        self.custom_width.setValue(210.0)
        self.custom_width.setSuffix(" mm")
        self.custom_width.setEnabled(False)
        size_layout.addRow("Custom Width:", self.custom_width)
        
        self.custom_height = QDoubleSpinBox()
        self.custom_height.setRange(50.0, 700.0)
        self.custom_height.setValue(297.0)
        self.custom_height.setSuffix(" mm")
        self.custom_height.setEnabled(False)
        size_layout.addRow("Custom Height:", self.custom_height)
        
        layout.addWidget(size_group)
        
        # Orientation group
        orientation_group = QGroupBox("Orientation")
        orientation_layout = QVBoxLayout(orientation_group)
        
        self.orientation_group = QButtonGroup()
        
        self.portrait_radio = QRadioButton("Portrait")
        self.portrait_radio.setChecked(True)
        self.orientation_group.addButton(self.portrait_radio)
        orientation_layout.addWidget(self.portrait_radio)
        
        self.landscape_radio = QRadioButton("Landscape")
        self.orientation_group.addButton(self.landscape_radio)
        orientation_layout.addWidget(self.landscape_radio)
        
        layout.addWidget(orientation_group)
        
        # Scale group
        scale_group = QGroupBox("Scale")
        scale_layout = QFormLayout(scale_group)
        scale_layout.setSpacing(10)
        
        self.scale_spinbox = QSpinBox()
        self.scale_spinbox.setRange(25, 400)
        self.scale_spinbox.setValue(100)
        self.scale_spinbox.setSuffix("%")
        scale_layout.addRow("Scale Factor:", self.scale_spinbox)
        
        # Scale to fit option
        self.scale_to_fit = QCheckBox("Scale to fit page")
        scale_layout.addRow("", self.scale_to_fit)
        
        layout.addWidget(scale_group)
        
        layout.addStretch()
        
    def setup_margins_tab(self):
        """Setup the Margins tab with margin controls"""
        layout = QVBoxLayout(self.margins_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Units selection
        units_group = QGroupBox("Units")
        units_layout = QHBoxLayout(units_group)
        
        self.units_group = QButtonGroup()
        
        self.mm_radio = QRadioButton("Millimeters (mm)")
        self.mm_radio.setChecked(True)
        self.units_group.addButton(self.mm_radio)
        units_layout.addWidget(self.mm_radio)
        
        self.inches_radio = QRadioButton("Inches (in)")
        self.units_group.addButton(self.inches_radio)
        units_layout.addWidget(self.inches_radio)
        
        layout.addWidget(units_group)
        
        # Margins group
        margins_group = QGroupBox("Margins")
        margins_layout = QFormLayout(margins_group)
        margins_layout.setSpacing(12)
        
        # Create margin controls
        self.top_margin = QDoubleSpinBox()
        self.top_margin.setRange(0.0, 100.0)
        self.top_margin.setValue(20.0)
        self.top_margin.setSingleStep(0.5)
        self.top_margin.setDecimals(2)
        self.top_margin.setKeyboardTracking(True)
        self.top_margin.setAccelerated(True)
        self.top_margin.setReadOnly(False)
        self.top_margin.setSuffix(" mm")
        margins_layout.addRow("Top:", self.top_margin)
        
        self.bottom_margin = QDoubleSpinBox()
        self.bottom_margin.setRange(0.0, 100.0)
        self.bottom_margin.setValue(20.0)
        self.bottom_margin.setSingleStep(0.5)
        self.bottom_margin.setDecimals(2)
        self.bottom_margin.setKeyboardTracking(True)
        self.bottom_margin.setAccelerated(True)
        self.bottom_margin.setReadOnly(False)
        self.bottom_margin.setSuffix(" mm")
        margins_layout.addRow("Bottom:", self.bottom_margin)
        
        self.left_margin = QDoubleSpinBox()
        self.left_margin.setRange(0.0, 100.0)
        self.left_margin.setValue(25.0)
        self.left_margin.setSingleStep(0.5)
        self.left_margin.setDecimals(2)
        self.left_margin.setKeyboardTracking(True)
        self.left_margin.setAccelerated(True)
        self.left_margin.setReadOnly(False)
        self.left_margin.setSuffix(" mm")
        margins_layout.addRow("Left:", self.left_margin)
        
        self.right_margin = QDoubleSpinBox()
        self.right_margin.setRange(0.0, 100.0)
        self.right_margin.setValue(25.0)
        self.right_margin.setSingleStep(0.5)
        self.right_margin.setDecimals(2)
        self.right_margin.setKeyboardTracking(True)
        self.right_margin.setAccelerated(True)
        self.right_margin.setReadOnly(False)
        self.right_margin.setSuffix(" mm")
        margins_layout.addRow("Right:", self.right_margin)
        
        layout.addWidget(margins_group)
        
        # Preset margins
        presets_group = QGroupBox("Margin Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_buttons_layout = QGridLayout()
        
        # Preset buttons with exclusive selection
        self.preset_group = QButtonGroup(self)
        self.preset_group.setExclusive(True)
        self.normal_btn = QPushButton("Normal (25mm)")
        self.normal_btn.setCheckable(True)
        self.normal_btn.setAutoDefault(False)
        self.normal_btn.setDefault(False)
        self.normal_btn.clicked.connect(lambda: self._apply_preset(self.normal_btn, 25, 25, 20, 20))
        self.preset_group.addButton(self.normal_btn)
        preset_buttons_layout.addWidget(self.normal_btn, 0, 0)
        
        self.narrow_btn = QPushButton("Narrow (15mm)")
        self.narrow_btn.setCheckable(True)
        self.narrow_btn.setAutoDefault(False)
        self.narrow_btn.setDefault(False)
        self.narrow_btn.clicked.connect(lambda: self._apply_preset(self.narrow_btn, 15, 15, 15, 15))
        self.preset_group.addButton(self.narrow_btn)
        preset_buttons_layout.addWidget(self.narrow_btn, 0, 1)
        
        self.wide_btn = QPushButton("Wide (35mm)")
        self.wide_btn.setCheckable(True)
        self.wide_btn.setAutoDefault(False)
        self.wide_btn.setDefault(False)
        self.wide_btn.clicked.connect(lambda: self._apply_preset(self.wide_btn, 35, 35, 30, 30))
        self.preset_group.addButton(self.wide_btn)
        preset_buttons_layout.addWidget(self.wide_btn, 1, 0)
        
        self.minimal_btn = QPushButton("Minimal (10mm)")
        self.minimal_btn.setCheckable(True)
        self.minimal_btn.setAutoDefault(False)
        self.minimal_btn.setDefault(False)
        self.minimal_btn.clicked.connect(lambda: self._apply_preset(self.minimal_btn, 10, 10, 10, 10))
        self.preset_group.addButton(self.minimal_btn)
        preset_buttons_layout.addWidget(self.minimal_btn, 1, 1)
        
        presets_layout.addLayout(preset_buttons_layout)
        layout.addWidget(presets_group)
        
        # Mirror margins option
        self.mirror_margins = QCheckBox("Mirror margins for duplex printing")
        layout.addWidget(self.mirror_margins)
        
        layout.addStretch()
        
    def setup_print_tab(self):
        """Setup the Print Options tab"""
        layout = QVBoxLayout(self.print_tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # Print Quality group
        quality_group = QGroupBox("Print Quality")
        quality_layout = QFormLayout(quality_group)
        
        self.print_quality = QComboBox()
        self.print_quality.addItems(["Draft", "Normal", "High", "Best"])
        self.print_quality.setCurrentText("Normal")
        quality_layout.addRow("Quality:", self.print_quality)
        
        self.print_resolution = QComboBox()
        self.print_resolution.addItems(["300 DPI", "600 DPI", "1200 DPI"])
        self.print_resolution.setCurrentText("600 DPI")
        quality_layout.addRow("Resolution:", self.print_resolution)
        
        layout.addWidget(quality_group)
        
        # Print Layout group
        print_layout_group = QGroupBox("Print Layout")
        print_layout_layout = QFormLayout(print_layout_group)
        
        # Pages per sheet
        self.pages_per_sheet = QComboBox()
        self.pages_per_sheet.addItems(["1", "2", "4", "6", "9", "16"])
        self.pages_per_sheet.setCurrentText("1")
        print_layout_layout.addRow("Pages per Sheet:", self.pages_per_sheet)
        
        # Duplex printing
        self.duplex_printing = QCheckBox("Duplex (two-sided) printing")
        print_layout_layout.addRow("", self.duplex_printing)
        
        # Collation
        self.collate_copies = QCheckBox("Collate copies")
        self.collate_copies.setChecked(True)
        print_layout_layout.addRow("", self.collate_copies)
        
        layout.addWidget(print_layout_group)
        
        # Page Range group
        range_group = QGroupBox("Page Range")
        range_layout = QFormLayout(range_group)
        
        self.print_all_pages = QRadioButton("All pages")
        self.print_all_pages.setChecked(True)
        range_layout.addRow("", self.print_all_pages)
        
        self.print_current_page = QRadioButton("Current page only")
        range_layout.addRow("", self.print_current_page)
        
        self.print_page_range = QRadioButton("Page range:")
        range_layout.addRow("", self.print_page_range)
        
        self.page_range_input = QLineEdit()
        self.page_range_input.setPlaceholderText("e.g., 1-5, 8, 11-15")
        self.page_range_input.setEnabled(False)
        range_layout.addRow("", self.page_range_input)
        
        # Connect page range radio to enable/disable input
        self.print_page_range.toggled.connect(self.page_range_input.setEnabled)
        
        layout.addWidget(range_group)
        
        # Additional Options group
        options_group = QGroupBox("Additional Options")
        options_layout = QVBoxLayout(options_group)
        
        self.print_page_numbers = QCheckBox("Print page numbers")
        self.print_page_numbers.setChecked(True)
        options_layout.addWidget(self.print_page_numbers)
        
        self.print_staff_names = QCheckBox("Print staff names")
        self.print_staff_names.setChecked(True)
        options_layout.addWidget(self.print_staff_names)
        
        self.print_title = QCheckBox("Print title and composer")
        self.print_title.setChecked(True)
        options_layout.addWidget(self.print_title)
        
        self.print_copyright = QCheckBox("Print copyright notice")
        self.print_copyright.setChecked(True)
        options_layout.addWidget(self.print_copyright)
        
        layout.addWidget(options_group)
        
        layout.addStretch()
        
    def set_margin_preset(self, left, right, top, bottom):
        """Set margin values from preset"""
        self.left_margin.setValue(left)
        self.right_margin.setValue(right)
        self.top_margin.setValue(top)
        self.bottom_margin.setValue(bottom)
        self.update_preview()

    def _apply_preset(self, button, left, right, top, bottom):
        """Apply preset margins and visually mark the active preset"""
        self.set_margin_preset(left, right, top, bottom)
        # Mark selection accurately
        self._update_preset_highlight(active_button=button)
        # Persist to dialog state immediately
        self.apply_settings()

    def _margins_tuple(self):
        return (
            round(self.left_margin.value(), 2),
            round(self.right_margin.value(), 2),
            round(self.top_margin.value(), 2),
            round(self.bottom_margin.value(), 2),
        )

    def _update_preset_highlight(self, active_button=None):
        """Update which preset button appears selected based on current margins."""
        # Clear checks first
        for b in self.preset_group.buttons():
            b.setChecked(False)
        if active_button is not None:
            active_button.setChecked(True)
            return
        margins = self._margins_tuple()
        presets = {
            (25.0, 25.0, 20.0, 20.0): self.normal_btn,
            (15.0, 15.0, 15.0, 15.0): self.narrow_btn,
            (35.0, 35.0, 30.0, 30.0): self.wide_btn,
            (10.0, 10.0, 10.0, 10.0): self.minimal_btn,
        }
        btn = presets.get(margins)
        if btn:
            btn.setChecked(True)
        
    def connect_signals(self):
        """Connect signals to update preview and apply settings immediately"""
        # Page size and orientation changes
        self.page_type_combo.currentTextChanged.connect(self._apply_page_size_change)
        self.page_type_combo.currentTextChanged.connect(self.apply_settings)
        self.page_type_combo.currentTextChanged.connect(self.update_preview)
        self.portrait_radio.toggled.connect(self._apply_page_size_change)
        self.portrait_radio.toggled.connect(self.apply_settings)
        self.portrait_radio.toggled.connect(self.update_preview)
        self.landscape_radio.toggled.connect(self._apply_page_size_change)
        self.landscape_radio.toggled.connect(self.apply_settings)
        self.landscape_radio.toggled.connect(self.update_preview)
        
        # Margin changes - apply immediately
        self.top_margin.valueChanged.connect(self._apply_margin_change)
        self.top_margin.valueChanged.connect(self.apply_settings)
        self.top_margin.valueChanged.connect(self.update_preview)
        self.bottom_margin.valueChanged.connect(self._apply_margin_change)
        self.bottom_margin.valueChanged.connect(self.apply_settings)
        self.bottom_margin.valueChanged.connect(self.update_preview)
        self.left_margin.valueChanged.connect(self._apply_margin_change)
        self.left_margin.valueChanged.connect(self.apply_settings)
        self.left_margin.valueChanged.connect(self.update_preview)
        self.right_margin.valueChanged.connect(self._apply_margin_change)
        self.right_margin.valueChanged.connect(self.apply_settings)
        self.right_margin.valueChanged.connect(self.update_preview)
        
        # Unit changes
        self.mm_radio.toggled.connect(self.update_units)
        self.inches_radio.toggled.connect(self.update_units)
        
    def update_units(self):
        """Update margin controls when units change"""
        if self.mm_radio.isChecked():
            # Convert from inches to mm
            if self.top_margin.suffix() == " in":
                self.top_margin.setValue(self.top_margin.value() * 25.4)
                self.bottom_margin.setValue(self.bottom_margin.value() * 25.4)
                self.left_margin.setValue(self.left_margin.value() * 25.4)
                self.right_margin.setValue(self.right_margin.value() * 25.4)
            
            for margin in [self.top_margin, self.bottom_margin, self.left_margin, self.right_margin]:
                margin.setSuffix(" mm")
                margin.setRange(0.0, 100.0)
                margin.setSingleStep(0.5)
        else:
            # Convert from mm to inches
            if self.top_margin.suffix() == " mm":
                self.top_margin.setValue(self.top_margin.value() / 25.4)
                self.bottom_margin.setValue(self.bottom_margin.value() / 25.4)
                self.left_margin.setValue(self.left_margin.value() / 25.4)
                self.right_margin.setValue(self.right_margin.value() / 25.4)
            
            for margin in [self.top_margin, self.bottom_margin, self.left_margin, self.right_margin]:
                margin.setSuffix(" in")
                margin.setRange(0.0, 4.0)
                margin.setSingleStep(0.1)
        
        self.update_preview()
        
    def update_preview(self):
        """Update the page preview"""
        page_type = self.page_type_combo.currentText().split(" ")[0]  # Extract just "A4", "Letter", etc.
        orientation = "Portrait" if self.portrait_radio.isChecked() else "Landscape"
        
        # Convert margins to percentage for preview
        margins = {
            'top': self.top_margin.value() * 0.3,  # Scale for preview
            'bottom': self.bottom_margin.value() * 0.3,
            'left': self.left_margin.value() * 0.3,
            'right': self.right_margin.value() * 0.3
        }
        
        self.preview_widget.set_page_settings(page_type, orientation, margins)
        
    def load_settings(self):
        """Load settings from QSettings (fallback to Preferences defaults)."""
        # Page settings: prefer Preferences defaults for new sessions
        page_type = settings.settings.value(
            "page_setup/page_type",
            settings.settings.value("layout/default_page_size", "A4 (210 × 297 mm)")
        )
        self.page_type_combo.setCurrentText(page_type)
        
        orientation = settings.settings.value(
            "page_setup/orientation",
            settings.settings.value("layout/default_orientation", "Portrait")
        )
        if orientation == "Portrait":
            self.portrait_radio.setChecked(True)
        else:
            self.landscape_radio.setChecked(True)
            
        # Scale settings
        scale = int(settings.settings.value("page_setup/scale", 100))
        self.scale_spinbox.setValue(scale)
        
        scale_to_fit = settings.settings.value("page_setup/scale_to_fit", False, type=bool)
        self.scale_to_fit.setChecked(scale_to_fit)
        
        # Margin settings
        units = settings.settings.value("page_setup/units", "mm")
        if units == "mm":
            self.mm_radio.setChecked(True)
        else:
            self.inches_radio.setChecked(True)
            
        # Load margins based on units
        if units == "mm":
            # Prefer Preferences layout/*; fallback to any last page_setup values
            self.top_margin.setValue(float(settings.settings.value("layout/default_top_margin", settings.settings.value("page_setup/top_margin_mm", 20.0))))
            self.bottom_margin.setValue(float(settings.settings.value("layout/default_bottom_margin", settings.settings.value("page_setup/bottom_margin_mm", 20.0))))
            self.left_margin.setValue(float(settings.settings.value("layout/default_left_margin", settings.settings.value("page_setup/left_margin_mm", 25.0))))
            self.right_margin.setValue(float(settings.settings.value("layout/default_right_margin", settings.settings.value("page_setup/right_margin_mm", 25.0))))
        else:
            self.top_margin.setValue(float(settings.settings.value("layout/default_top_margin", settings.settings.value("page_setup/top_margin_in", 0.79)*25.4))/25.4)
            self.bottom_margin.setValue(float(settings.settings.value("layout/default_bottom_margin", settings.settings.value("page_setup/bottom_margin_in", 0.79)*25.4))/25.4)
            self.left_margin.setValue(float(settings.settings.value("layout/default_left_margin", settings.settings.value("page_setup/left_margin_in", 0.98)*25.4))/25.4)
            self.right_margin.setValue(float(settings.settings.value("layout/default_right_margin", settings.settings.value("page_setup/right_margin_in", 0.98)*25.4))/25.4)
            
        self.mirror_margins.setChecked(settings.settings.value("page_setup/mirror_margins", False, type=bool))
        
        # Print settings
        self.print_quality.setCurrentText(settings.settings.value("page_setup/print_quality", "Normal"))
        self.print_resolution.setCurrentText(settings.settings.value("page_setup/print_resolution", "600 DPI"))
        self.pages_per_sheet.setCurrentText(settings.settings.value("page_setup/pages_per_sheet", "1"))
        self.duplex_printing.setChecked(settings.settings.value("page_setup/duplex_printing", False, type=bool))
        self.collate_copies.setChecked(settings.settings.value("page_setup/collate_copies", True, type=bool))
        
        self.print_page_numbers.setChecked(settings.settings.value("page_setup/print_page_numbers", True, type=bool))
        self.print_staff_names.setChecked(settings.settings.value("page_setup/print_staff_names", True, type=bool))
        self.print_title.setChecked(settings.settings.value("page_setup/print_title", True, type=bool))
        self.print_copyright.setChecked(settings.settings.value("page_setup/print_copyright", True, type=bool))
        
        # Update units after loading
        self.update_units()
        self.update_preview()
        # Highlight preset according to current margins
        self._update_preset_highlight()
        
    def save_settings(self):
        """Save settings to QSettings"""
        # Page settings
        settings.settings.setValue("page_setup/page_type", self.page_type_combo.currentText())
        settings.settings.setValue("page_setup/orientation", "Portrait" if self.portrait_radio.isChecked() else "Landscape")
        settings.settings.setValue("page_setup/scale", self.scale_spinbox.value())
        settings.settings.setValue("page_setup/scale_to_fit", self.scale_to_fit.isChecked())
        
        # Units and margins
        units = "mm" if self.mm_radio.isChecked() else "in"
        settings.settings.setValue("page_setup/units", units)
        
        if units == "mm":
            settings.settings.setValue("page_setup/top_margin_mm", self.top_margin.value())
            settings.settings.setValue("page_setup/bottom_margin_mm", self.bottom_margin.value())
            settings.settings.setValue("page_setup/left_margin_mm", self.left_margin.value())
            settings.settings.setValue("page_setup/right_margin_mm", self.right_margin.value())
        else:
            settings.settings.setValue("page_setup/top_margin_in", self.top_margin.value())
            settings.settings.setValue("page_setup/bottom_margin_in", self.bottom_margin.value())
            settings.settings.setValue("page_setup/left_margin_in", self.left_margin.value())
            settings.settings.setValue("page_setup/right_margin_in", self.right_margin.value())
            
        settings.settings.setValue("page_setup/mirror_margins", self.mirror_margins.isChecked())
        
        # Print settings
        settings.settings.setValue("page_setup/print_quality", self.print_quality.currentText())
        settings.settings.setValue("page_setup/print_resolution", self.print_resolution.currentText())
        settings.settings.setValue("page_setup/pages_per_sheet", self.pages_per_sheet.currentText())
        settings.settings.setValue("page_setup/duplex_printing", self.duplex_printing.isChecked())
        settings.settings.setValue("page_setup/collate_copies", self.collate_copies.isChecked())
        
        settings.settings.setValue("page_setup/print_page_numbers", self.print_page_numbers.isChecked())
        settings.settings.setValue("page_setup/print_staff_names", self.print_staff_names.isChecked())
        settings.settings.setValue("page_setup/print_title", self.print_title.isChecked())
        settings.settings.setValue("page_setup/print_copyright", self.print_copyright.isChecked())
        
    def save_as_defaults(self):
        """Save current settings as defaults and export to Preferences"""
        self.save_settings()
        
        # Export to Preferences / Page Layout tab
        from PyQt6.QtCore import QSettings
        qsettings = QSettings("ONOTE", "Preferences")
        
        # Save page layout settings to Preferences
        qsettings.setValue("layout/default_top_margin", self.top_margin.value())
        qsettings.setValue("layout/default_bottom_margin", self.bottom_margin.value())
        qsettings.setValue("layout/default_left_margin", self.left_margin.value())
        qsettings.setValue("layout/default_right_margin", self.right_margin.value())
        
        # Save page size and orientation
        page_type = self.page_type_combo.currentText().split(" ")[0]  # Extract just "A4", "Letter", etc.
        qsettings.setValue("layout/default_page_type", page_type)
        orientation = "Portrait" if self.portrait_radio.isChecked() else "Landscape"
        qsettings.setValue("layout/default_orientation", orientation)
        
        # Save units
        units = "mm" if self.mm_radio.isChecked() else "in"
        qsettings.setValue("layout/default_units", units)
        
        # Emit settings_changed with set_as_defaults=True so main_window can update QSettings
        page_options = self.get_page_options()
        page_options['set_as_defaults'] = True
        self.settings_changed.emit(page_options)
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Page Setup", "Current settings saved as defaults and exported to Preferences.")
        
    def apply_settings(self):
        """Apply settings immediately (kept for internal calls)"""
        self.save_settings()
        page_options = self.get_page_options()
        self.settings_changed.emit(page_options)
        
    def accept_settings(self):
        """Accept and apply settings"""
        try:
            self.save_settings()
            # Call the parent accept method to properly close the dialog
            super().accept()
        except Exception as e:
            print(f"Error in accept_settings: {e}")
            import traceback
            traceback.print_exc()
            # Still try to close the dialog even if there's an error
            super().accept()
        
    def get_page_options(self):
        """Get the current page setup options"""
        page_type = self.page_type_combo.currentText().split(" ")[0]  # Extract just "A4", "Letter", etc.
        orientation = "Portrait" if self.portrait_radio.isChecked() else "Landscape"
        units = "mm" if self.mm_radio.isChecked() else "in"
        
        return {
            # Page settings
            'page_type': page_type,
            'orientation': orientation,
            'scale': self.scale_spinbox.value(),
            'scale_to_fit': self.scale_to_fit.isChecked(),
            
            # Margin settings
            'units': units,
            'top_margin': self.top_margin.value(),
            'bottom_margin': self.bottom_margin.value(),
            'left_margin': self.left_margin.value(),
            'right_margin': self.right_margin.value(),
            'mirror_margins': self.mirror_margins.isChecked(),
            
            # Print settings
            'print_quality': self.print_quality.currentText(),
            'print_resolution': self.print_resolution.currentText(),
            'pages_per_sheet': int(self.pages_per_sheet.currentText()),
            'duplex_printing': self.duplex_printing.isChecked(),
            'collate_copies': self.collate_copies.isChecked(),
            
            # Print content options
            'print_page_numbers': self.print_page_numbers.isChecked(),
            'print_staff_names': self.print_staff_names.isChecked(),
            'print_title': self.print_title.isChecked(),
            'print_copyright': self.print_copyright.isChecked(),
            
            # Page range (for future use)
            'print_all_pages': self.print_all_pages.isChecked(),
            'print_current_page': self.print_current_page.isChecked(),
            'page_range': self.page_range_input.text() if self.print_page_range.isChecked() else ""
        } 

    def _apply_margin_change(self, value=None):
        """Immediately apply margin changes to the current document and re-render"""
        if self.parent() and hasattr(self.parent(), 'staff_view') and self.parent().staff_view and hasattr(self.parent().staff_view, 'document'):
            doc = self.parent().staff_view.document
            MM_TO_PIXELS = 3.78
            doc.layout.top_margin = int(self.top_margin.value() * MM_TO_PIXELS)
            doc.layout.bottom_margin = int(self.bottom_margin.value() * MM_TO_PIXELS)
            doc.layout.left_margin = int(self.left_margin.value() * MM_TO_PIXELS)
            doc.layout.right_margin = int(self.right_margin.value() * MM_TO_PIXELS)
            # Recompute staff and section positions when margins change
            if hasattr(doc.layout, '_update_positions'):
                doc.layout._update_positions()
            if hasattr(self.parent().staff_view, 'renderer'):
                self.parent().staff_view.renderer.set_margins({
                    'top': doc.layout.top_margin,
                    'bottom': doc.layout.bottom_margin,
                    'left': doc.layout.left_margin,
                    'right': doc.layout.right_margin
                })
                self.parent().staff_view.update()

    def _apply_page_size_change(self, value=None):
        """Immediately apply page size changes to the current document and re-render"""
        if self.parent() and hasattr(self.parent(), 'staff_view') and self.parent().staff_view and hasattr(self.parent().staff_view, 'document'):
            doc = self.parent().staff_view.document
            MM_TO_PIXELS = 3.78
            page_type = self.page_type_combo.currentText()
            orientation = 'Portrait' if self.portrait_radio.isChecked() else 'Landscape'
            if 'A4' in page_type:
                width_mm, height_mm = 210, 297
            elif 'A3' in page_type:
                width_mm, height_mm = 297, 420
            elif 'Letter' in page_type:
                width_mm, height_mm = 215.9, 279.4
            elif 'Legal' in page_type:
                width_mm, height_mm = 215.9, 355.6
            elif 'Tabloid' in page_type:
                width_mm, height_mm = 279.4, 431.8
            else:
                width_mm, height_mm = 210, 297
            if orientation == 'Landscape':
                width_mm, height_mm = height_mm, width_mm
            doc.layout.page_width = int(width_mm * MM_TO_PIXELS)
            doc.layout.page_height = int(height_mm * MM_TO_PIXELS)
            if hasattr(self.parent().staff_view, 'renderer'):
                self.parent().staff_view.renderer.page_width = doc.layout.page_width
                self.parent().staff_view.renderer.page_height = doc.layout.page_height
                self.parent().staff_view.update() 