from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QSpinBox,
    QCheckBox,
    QLineEdit,
    QWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QFormLayout,
    QDialogButtonBox,
    QMessageBox,
    QToolBar,
    QToolButton,
    QMenu,
    QScrollArea,
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from .staff_types import StaffType, StaffBase, SingleStaff, GrandStaff, SectionGroup
# Import PluginScanner with fallback for different execution contexts
try:
    from src.plugins.plugin_scanner import PluginScanner
except ImportError:
    try:
        from ...plugins.plugin_scanner import PluginScanner
    except ImportError:
        try:
            from plugins.plugin_scanner import PluginScanner
        except ImportError:
            # Final fallback - add project root to path
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(current_dir, '..', '..')
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            from plugins.plugin_scanner import PluginScanner
from .score_setup_widget import ScoreSetupWidget


class ScoreSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        print(f"[DEBUG] ScoreSetupDialog __init__ called, id={id(self)}")
        print("=== SCORE_SETUP_DIALOG: Constructor called ===")
        print(f"=== SCORE_SETUP_DIALOG: Parent type: {type(parent)} ===")
        # Always stay on top of the desktop
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle("Score Setup")
        self.setModal(False)  # Make modeless so multiple dialogs can be open
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.plugin_scanner = PluginScanner()
        self.selected_section = None
        self.has_unapplied_changes = False
        self.parent_view = parent

        # --- Zoom state for dialog ---
        self.dialog_zoom = 1.0

        # Create main layout
        layout = QVBoxLayout()

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
        # Manual zoom dropdown
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
        layout.addWidget(zoom_toolbar)

        # --- Main content in a scroll area for scalable zoom ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        # Add header with mode indication
        header_layout = QHBoxLayout()
        mode_label = QLabel("Score Setup Mode (Pink Mode)")
        mode_label.setStyleSheet("font-weight: bold; color: #990000;")
        header_layout.addWidget(mode_label)

        # Add helpful instruction text
        instruction_label = QLabel(
            "Add staves to build your score and organize them into sections."
        )
        instruction_label.setStyleSheet("font-style: italic;")
        header_layout.addWidget(instruction_label)
        header_layout.addStretch()

        self.content_layout.addLayout(header_layout)

        # Create the score setup widget
        self.setup_widget = ScoreSetupWidget(self)
        print(f"[DEBUG] Connecting signals for ScoreSetupWidget id={id(self.setup_widget)}")
        print(f"[DEBUG] Dialog id: {id(self)}")
        print(f"[DEBUG] Dialog on_staff_added method: {self.on_staff_added}")
        self.setup_widget.staff_added.connect(self.on_staff_added)
        print("[DEBUG] Connected staff_added signal")
        print(f"[DEBUG] staff_added signal connected successfully")
        self.setup_widget.staff_removed.connect(self.on_staff_removed)
        print("[DEBUG] Connected staff_removed signal")
        self.setup_widget.staff_visibility_changed.connect(self.on_staff_visibility_changed)
        print("[DEBUG] Connected staff_visibility_changed signal")
        self.setup_widget.staff_options_changed.connect(self.on_staff_options_changed)
        print("[DEBUG] Connected staff_options_changed signal")
        self.setup_widget.staff_reordered.connect(self.on_staff_reordered)
        print("[DEBUG] Connected staff_reordered signal")
        self.setup_widget.setup_completed.connect(self.accept)
        print("[DEBUG] Connected setup_completed signal")

        self.content_layout.addWidget(self.setup_widget)

        # Create button box
        button_box = QDialogButtonBox()
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.setDefault(True)
        self.apply_btn.clicked.connect(self.toggle_apply_setup)
        button_box.addButton(self.apply_btn, QDialogButtonBox.ButtonRole.ApplyRole)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_box.addButton(close_btn, QDialogButtonBox.ButtonRole.RejectRole)
        self.content_layout.addWidget(button_box)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

        # --- Zoom logic ---
        self._set_dialog_zoom(1.0)

        # IMPORTANT: First try to simply use populate_from_document which now handles both
        # dialog_settings and document-based population
        print("Dialog init: Starting staff population")
        self.populate_from_document()
        print(
            f"Dialog init: Population complete, staff count = {self.setup_widget.staff_list.topLevelItemCount()}"
        )
        print(f"[DEBUG] ScoreSetupDialog __init__ complete, id={id(self)}")

    def _set_dialog_zoom(self, zoom_level):
        self.dialog_zoom = max(0.5, min(zoom_level, 2.0))
        self.content_widget.setStyleSheet(f"font-size: {int(14 * self.dialog_zoom)}px;")
        self.content_widget.resize(self.content_widget.sizeHint() * self.dialog_zoom)
        for act, value in self.zoom_actions:
            act.setChecked(abs(self.dialog_zoom - value) < 0.01)

    def populate_from_document(self):
        """Populate the staff list from the document structure"""
        # Clear the staff list first
        self.setup_widget.staff_list.clear()

        # First check if we already have staves in dialog_settings
        parent_has_settings = False
        if hasattr(self.parent(), "dialog_settings") and self.parent().dialog_settings:
            settings = self.parent().dialog_settings
            if "added_staves" in settings and settings["added_staves"]:
                print("POPULATE: Found staves in direct parent dialog_settings")
                for staff in settings["added_staves"]:
                    print(
                        f"  POPULATE: Found staff {staff.get('instrument_name', 'Unknown')} in parent dialog_settings"
                    )
                self.populate_added_staves(settings)
                parent_has_settings = True
                return
        # Also check parent.staff_view
        elif (
            hasattr(self.parent(), "staff_view")
            and self.parent().staff_view
            and hasattr(self.parent().staff_view, "dialog_settings")
        ):
            settings = self.parent().staff_view.dialog_settings
            if settings and "added_staves" in settings and settings["added_staves"]:
                print("POPULATE: Found staves in parent.staff_view dialog_settings")
                for staff in settings["added_staves"]:
                    print(
                        f"  POPULATE: Found staff {staff.get('instrument_name', 'Unknown')} in parent.staff_view dialog_settings"
                    )
                self.populate_added_staves(settings)
                parent_has_settings = True
                return

        if parent_has_settings:
            print("POPULATE: Used existing dialog_settings, skipping document scan")
            return

        print(
            "POPULATE: No staves found in dialog_settings, attempting to populate from document structure"
        )

        # Get document from desktop window's music page
        doc = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, get document from music page
            if hasattr(self.parent().music_page, "staff_view") and self.parent().music_page.staff_view:
                doc = self.parent().music_page.staff_view.document
                print("POPULATE: Got document from desktop window's music page staff view")
        elif hasattr(self.parent(), "document") and hasattr(self.parent(), "is_setup_mode"):
            # Parent is likely StaffView directly
            doc = self.parent().document
            print("POPULATE: Got document from direct StaffView parent")
        elif (
            hasattr(self.parent(), "staff_view")
            and self.parent().staff_view
            and self.parent().staff_view.document
        ):
            # Parent has staff_view with document
            doc = self.parent().staff_view.document
            print("POPULATE: Got document from parent.staff_view")

        if not doc:
            print("POPULATE: No document found, creating empty staff list")
            return

        section_map = {}
        staff_type_map = {}

        print("Populating staff list from document structure...")

        # First try to get section map from document
        if hasattr(doc, "section_map"):
            section_map = doc.section_map
            print(f"Retrieved {len(section_map)} sections from document")
            for instr, section in section_map.items():
                print(f"  Doc section: {instr}: {section}")

        # Process ungrouped staves first
        if hasattr(doc.layout, "ungrouped_staves"):
            for staff in doc.layout.ungrouped_staves:
                # CRITICAL FIX: Get plugin from document.plugin_map if available, otherwise from staff.plugin
                plugin = 'Default'
                if hasattr(doc, 'plugin_map') and staff.instrument_id in doc.plugin_map:
                    plugin = doc.plugin_map[staff.instrument_id]
                    print(f"POPULATE: Using plugin '{plugin}' from document plugin_map for {staff.instrument_name}")
                else:
                    plugin = getattr(staff, 'plugin', 'Default')
                    print(f"POPULATE: Using plugin '{plugin}' from staff attribute for {staff.instrument_name}")
                
                # Create staff data
                staff_data = {
                    "instrument_id": staff.instrument_id,
                    "instrument_name": staff.instrument_name,
                    "instrument_abbr": staff.instrument_abbr,
                    "staff_type": "single_staff"
                    if isinstance(staff, SingleStaff)
                    else "grand_staff",
                    "clef": staff.clef,
                    "key": staff.key,
                    "time_signature": staff.time_signature,
                    "section": "",  # No section for ungrouped staves
                    "plugin": plugin,  # Use the plugin from document or staff
                }
                
                # Load custom_name and custom_abbr if they exist on the staff object
                if hasattr(staff, 'custom_name') and staff.custom_name:
                    staff_data["custom_name"] = staff.custom_name
                    print(f"POPULATE: Loaded custom_name '{staff.custom_name}' for {staff.instrument_name}")
                if hasattr(staff, 'custom_abbr') and staff.custom_abbr:
                    staff_data["custom_abbr"] = staff.custom_abbr
                    print(f"POPULATE: Loaded custom_abbr '{staff.custom_abbr}' for {staff.instrument_name}")

                # Create staff item
                staff_item = QTreeWidgetItem(self.setup_widget.staff_list)
                # Use custom_name if available, otherwise default instrument_name
                display_name = staff_data.get("custom_name", staff.instrument_name)
                staff_item.setText(0, display_name)
                staff_item.setText(
                    1, "Single Staff" if isinstance(staff, SingleStaff) else "Grand Staff"
                )
                staff_item.setText(2, "")  # No section
                staff_item.setText(3, "")  # Section column for consistency
                staff_item.setText(4, plugin)  # Plugin column
                staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                print(f"Added ungrouped staff: {staff.instrument_name} with plugin: {plugin}")

        # Then process sections and their staves
        for section in doc.layout.sections:
            for staff in section.staves:
                # CRITICAL FIX: Get plugin from document.plugin_map if available, otherwise from staff.plugin  
                plugin = 'Default'
                if hasattr(doc, 'plugin_map') and staff.instrument_id in doc.plugin_map:
                    plugin = doc.plugin_map[staff.instrument_id]
                    print(f"POPULATE: Using plugin '{plugin}' from document plugin_map for {staff.instrument_name}")
                else:
                    plugin = getattr(staff, 'plugin', 'Default')
                    print(f"POPULATE: Using plugin '{plugin}' from staff attribute for {staff.instrument_name}")
                    
                # Create staff data
                staff_data = {
                    "instrument_id": staff.instrument_id,
                    "instrument_name": staff.instrument_name,
                    "instrument_abbr": staff.instrument_abbr,
                    "staff_type": "single_staff"
                    if isinstance(staff, SingleStaff)
                    else "grand_staff",
                    "clef": staff.clef,
                    "key": staff.key,
                    "time_signature": staff.time_signature,
                    "section": section.name,  # Set section from the group
                    "plugin": plugin,  # Use the plugin from document or staff
                }
                
                # Load custom_name and custom_abbr if they exist on the staff object
                if hasattr(staff, 'custom_name') and staff.custom_name:
                    staff_data["custom_name"] = staff.custom_name
                    print(f"POPULATE: Loaded custom_name '{staff.custom_name}' for {staff.instrument_name}")
                if hasattr(staff, 'custom_abbr') and staff.custom_abbr:
                    staff_data["custom_abbr"] = staff.custom_abbr
                    print(f"POPULATE: Loaded custom_abbr '{staff.custom_abbr}' for {staff.instrument_name}")

                # Create staff item
                staff_item = QTreeWidgetItem(self.setup_widget.staff_list)
                # Use custom_name if available, otherwise default instrument_name
                display_name = staff_data.get("custom_name", staff.instrument_name)
                staff_item.setText(0, display_name)
                staff_item.setText(
                    1, "Single Staff" if isinstance(staff, SingleStaff) else "Grand Staff"
                )
                staff_item.setText(2, "Treble" if staff.clef == "treble" else ("Bass" if staff.clef == "bass" else staff.clef.title()))  # Clef column
                staff_item.setText(3, section.name)  # Section column
                staff_item.setText(4, plugin)  # Plugin column
                staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                print(f"Added staff {staff.instrument_name} from section '{section.name}' with plugin: {plugin}")

                # Update section_map if not already there
                if staff.instrument_id not in section_map:
                    section_map[staff.instrument_id] = section.name

                # Update staff_type_map
                staff_type_map[staff.instrument_id] = (
                    "single_staff" if isinstance(staff, SingleStaff) else "grand_staff"
                )

        # Set initial column widths
        self.setup_widget.staff_list.setColumnWidth(0, 180)  # Instrument name
        self.setup_widget.staff_list.setColumnWidth(1, 120)  # Staff type
        self.setup_widget.staff_list.setColumnWidth(2, 80)   # Clef
        self.setup_widget.staff_list.setColumnWidth(3, 120)  # Section
        self.setup_widget.staff_list.setColumnWidth(4, 120)  # Plugin

    def populate_added_staves(self, settings):
        """Populate the Added Staves list from saved settings"""
        print("POPULATE_ADDED_STAVES: Starting populating staves from settings")

        # Don't clear the list if no added_staves in settings
        if "added_staves" not in settings or not settings["added_staves"]:
            print("POPULATE_ADDED_STAVES: No added_staves found in settings")
            return

        # Clear the staff list first
        self.setup_widget.staff_list.clear()

        # Get existing section map from the document
        existing_section_map = {}
        existing_staff_type_map = {}
        existing_clef_map = {}

        # First check if parent is a StaffView directly
        if hasattr(self.parent(), "document") and hasattr(self.parent(), "is_setup_mode"):
            # Parent is likely a StaffView directly
            doc = self.parent().document
            if hasattr(doc, "section_map"):
                existing_section_map = doc.section_map
                print(
                    f"POPULATE_ADDED_STAVES: Retrieved {len(existing_section_map)} sections from direct document"
                )
                for instr, section in existing_section_map.items():
                    print(f"  Doc section: {instr}: {section}")
        # Then check with parent.staff_view as before
        elif (
            hasattr(self.parent(), "staff_view")
            and self.parent().staff_view
            and self.parent().staff_view.document
        ):
            doc = self.parent().staff_view.document
            if hasattr(doc, "section_map"):
                existing_section_map = doc.section_map
                print(
                    f"POPULATE_ADDED_STAVES: Retrieved {len(existing_section_map)} sections from document via parent.staff_view"
                )
                for instr, section in existing_section_map.items():
                    print(f"  Doc section: {instr}: {section}")

        # Try to restore from dialog settings
        if "section_map" in settings:
            existing_section_map.update(settings["section_map"])
            print(
                f"POPULATE_ADDED_STAVES: Updated with {len(settings['section_map'])} sections from dialog settings"
            )

        if "staff_type_map" in settings:
            existing_staff_type_map.update(settings["staff_type_map"])

        if "clef_map" in settings:
            existing_clef_map.update(settings["clef_map"])
            print(
                f"POPULATE_ADDED_STAVES: Updated with {len(settings.get('clef_map', {}))} clefs from dialog settings"
            )

        print(f"POPULATE_ADDED_STAVES: Final section_map has {len(existing_section_map)} entries")

        # Now populate the UI from the saved staves
        staves_added = 0
        if "added_staves" in settings and settings["added_staves"]:
            for staff_data in settings["added_staves"]:
                instrument_name = staff_data.get("instrument_name", "")
                if not instrument_name:
                    print(f"POPULATE_ADDED_STAVES: Skipping staff with missing instrument_name")
                    continue

                instrument_id = staff_data.get(
                    "instrument_id", instrument_name.lower().replace(" ", "_")
                )

                # Try to get section for this instrument
                section = ""
                if instrument_id in existing_section_map:
                    section = existing_section_map[instrument_id]
                    print(f"POPULATE_ADDED_STAVES: Using section '{section}' for {instrument_id}")
                elif "section" in staff_data and staff_data["section"]:
                    section = staff_data["section"]
                    print(
                        f"POPULATE_ADDED_STAVES: Using section '{section}' from staff_data for {instrument_id}"
                    )

                # Try to get staff type for this instrument
                staff_type_display = "Single Staff"  # Default
                staff_type = staff_data.get("staff_type", "")
                if not staff_type and instrument_id in existing_staff_type_map:
                    staff_type = existing_staff_type_map[instrument_id]
                    print(
                        f"POPULATE_ADDED_STAVES: Using staff type '{staff_type}' for {instrument_id}"
                    )

                if staff_type == "grand_staff":
                    staff_type_display = "Grand Staff"
                    clef_display = "Treble/Bass"
                else:
                    # Determine clef display based on the clef value
                    clef = staff_data.get("clef", "")
                    if not clef and instrument_id in existing_clef_map:
                        clef = existing_clef_map[instrument_id]
                        print(f"POPULATE_ADDED_STAVES: Using clef '{clef}' for {instrument_id}")

                    # Set default if still not found
                    if not clef:
                        clef = "treble"

                    # Map clef to display text
                    if clef == "bass":
                        clef_display = "Bass"
                    elif clef == "alto":
                        clef_display = "Alto"
                    elif clef == "percussion":
                        clef_display = "Percussion"
                    else:
                        clef_display = "Treble"  # Default for single staff

                # --- ROBUST REPOPULATION LOGIC ---
                # The complete data is usually in a nested 'staff_data' dictionary.
                item_data_source = staff_data.get("staff_data", staff_data)

                # Use custom_name for display if it exists, otherwise fall back to instrument_name.
                display_name = item_data_source.get("custom_name", instrument_name)

                # Create and populate the tree widget item.
                staff_item = QTreeWidgetItem(self.setup_widget.staff_list)
                staff_item.setText(0, display_name)
                staff_item.setText(1, staff_type_display)
                staff_item.setText(2, clef_display)
                staff_item.setText(3, section)

                # Get plugin information - try multiple sources
                plugin = "Default"
                if "plugin" in staff_data and staff_data["plugin"] != "Default":
                    plugin = staff_data["plugin"]
                elif "staff_data" in staff_data and isinstance(staff_data.get("staff_data"), dict) and "plugin" in staff_data["staff_data"]:
                    plugin = staff_data["staff_data"]["plugin"]
                elif "plugin_map" in settings and instrument_id in settings["plugin_map"]:
                    plugin = settings["plugin_map"][instrument_id]
                
                staff_item.setText(4, plugin)

                # Build the item_data to be stored on the widget item, ensuring all custom fields are preserved.
                item_data = item_data_source.copy()
                
                # Ensure all required fields are present in the final item_data.
                item_data.setdefault("instrument_id", instrument_id)
                item_data.setdefault("instrument_name", instrument_name)
                # If a custom_abbr exists, prefer it for instrument_abbr
                preferred_abbr = item_data.get("custom_abbr", item_data.get("instrument_abbr", instrument_name[:3].upper()))
                item_data["instrument_abbr"] = preferred_abbr
                item_data.setdefault("clef", clef if staff_type != "grand_staff" else "treble")
                item_data.setdefault("plugin", plugin)
                item_data["section"] = section
                item_data["staff_type"] = staff_type

                staff_item.setData(0, Qt.ItemDataRole.UserRole, item_data)
                staves_added += 1

                print(f"POPULATE_ADDED_STAVES: Added staff: {display_name}, section: '{section}', staff_type: {staff_type_display}, clef: {clef_display}")

        # Set initial column widths
        self.setup_widget.staff_list.setColumnWidth(0, 180)  # Instrument name
        self.setup_widget.staff_list.setColumnWidth(1, 120)  # Staff type
        self.setup_widget.staff_list.setColumnWidth(2, 80)  # Clef
        self.setup_widget.staff_list.setColumnWidth(3, 120)  # Section
        self.setup_widget.staff_list.setColumnWidth(4, 120)  # Plugin

        # Restore unapplied changes state
        if "has_unapplied_changes" in settings:
            self.has_unapplied_changes = settings.get("has_unapplied_changes", False)
            self.setup_widget.has_unapplied_changes = self.has_unapplied_changes
            print(
                f"POPULATE_ADDED_STAVES: Set has_unapplied_changes to {self.has_unapplied_changes}"
            )

        print(f"POPULATE_ADDED_STAVES: Successfully added {staves_added} staves to the UI")

    def apply_settings(self):
        """Apply settings without closing the dialog"""
        print("===== APPLY_SETTINGS: Starting apply process without closing =====")
        
        # Get the latest options
        options = self.get_setup_options()

        # Apply changes
        print("===== APPLY_SETTINGS: Applying changes =====")
        self.setup_widget.apply_changes()

        # Update options to reflect that changes have been applied
        options["has_unapplied_changes"] = False
        
        # **ALWAYS SWITCH TO EDIT MODE when Apply is clicked**
        print("===== APPLY_SETTINGS: Always switching to edit mode =====")
        
        # Apply to parent based on type
        if hasattr(self.parent(), "apply_setup_options"):
            # Parent has direct apply method
            print("===== APPLY_SETTINGS: Applying changes to parent directly =====")
            self.parent().apply_setup_options(options)
            
            # Switch to edit mode
            if hasattr(self.parent(), "_enter_edit_mode"):
                print("===== APPLY_SETTINGS: Switching to edit mode =====")
                self.parent()._enter_edit_mode()
                print("===== APPLY_SETTINGS: Edit mode activated =====")
            elif hasattr(self.parent(), "enter_edit_mode"):
                print("===== APPLY_SETTINGS: Switching to edit mode =====")
                self.parent().enter_edit_mode()
                print("===== APPLY_SETTINGS: Edit mode activated =====")
                
        elif hasattr(self.parent(), "staff_view"):
            # Parent is likely MainWindow with staff_view attribute
            print("===== APPLY_SETTINGS: Applying changes to parent.staff_view and switching to edit mode =====")
            # Ensure parent.staff_view applies the dialog settings
            if hasattr(self.parent().staff_view, "apply_setup_options"):
                self.parent().staff_view.apply_setup_options(options)
                self.parent().staff_view.dialog_settings = options

            # Switch to edit mode immediately
            if hasattr(self.parent().staff_view, "enter_edit_mode"):
                print("===== APPLY_SETTINGS: Switching to edit mode =====")
                self.parent().staff_view.enter_edit_mode()
                print("===== APPLY_SETTINGS: Edit mode activated =====")
            else:
                # Fallback: Manually set mode flags
                self.parent().staff_view.is_setup_mode = False
                if hasattr(self.parent().staff_view, "document") and hasattr(
                    self.parent().staff_view.document, "layout"
                ):
                    self.parent().staff_view.document.layout.set_setup_mode(False)
                print("===== APPLY_SETTINGS: Manually set mode to edit mode =====")

            # Update the UI
            self.parent().staff_view.update()

            # If parent is MainWindow, update the toggle mode action text
            if hasattr(self.parent(), "toggle_mode_action"):
                self.parent().toggle_mode_action.setText("Score Setup")
                print("===== APPLY_SETTINGS: Updated toggle button text to 'Score Setup' =====")
        
        print("===== APPLY_SETTINGS: Apply process completed - dialog remains open =====")
        
    def toggle_apply_setup(self):
        """Toggle between Apply and Setup modes."""
        print("===== TOGGLE_APPLY_SETUP: Starting toggle operation =====")
        
        # Determine current mode from parent or fallback
        mode = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, check music_page mode
            if hasattr(self.parent().music_page, "mode"):
                mode = self.parent().music_page.mode
        elif hasattr(self.parent(), "is_setup_mode"):
            mode = "setup" if self.parent().is_setup_mode else "edit"
        elif hasattr(self.parent(), "staff_view") and hasattr(self.parent().staff_view, "is_setup_mode"):
            mode = "setup" if self.parent().staff_view.is_setup_mode else "edit"
        # Fallback: default to setup
        if mode is None:
            mode = "setup"

        print(f"===== TOGGLE_APPLY_SETUP: Current mode detected as '{mode}' =====")

        if mode == "setup":
            # Currently in setup mode, apply changes and switch to edit mode
            print("===== TOGGLE_APPLY_SETUP: In setup mode - applying changes and switching to edit mode =====")
            self.apply_settings()
            
            # Try to switch parent to edit mode
            if hasattr(self.parent(), "_enter_edit_mode"):
                self.parent()._enter_edit_mode()
            elif hasattr(self.parent(), "enter_edit_mode"):
                self.parent().enter_edit_mode()
            elif hasattr(self.parent(), "staff_view") and hasattr(self.parent().staff_view, "enter_edit_mode"):
                self.parent().staff_view.enter_edit_mode()
            
            # Update button text and tooltip
            self.apply_btn.setText("Setup")
            self.apply_btn.setStatusTip("Switch back to setup mode")
            print("===== TOGGLE_APPLY_SETUP: Switched to edit mode, button now shows 'Setup' =====")
        else:
            # Currently in edit mode, switch back to setup mode
            print("===== TOGGLE_APPLY_SETUP: In edit mode - switching back to setup mode =====")
            
            if hasattr(self.parent(), "_enter_setup_mode"):
                self.parent()._enter_setup_mode()
            elif hasattr(self.parent(), "enter_setup_mode"):
                self.parent().enter_setup_mode()
            elif hasattr(self.parent(), "staff_view") and hasattr(self.parent().staff_view, "enter_setup_mode"):
                self.parent().staff_view.enter_setup_mode()
            
            # Update button text and tooltip
            self.apply_btn.setText("Apply")
            self.apply_btn.setStatusTip("Apply changes and switch to edit mode")
            print("===== TOGGLE_APPLY_SETUP: Switched back to setup mode, button now shows 'Apply' =====")

    def accept(self):
        """Override accept to handle dialog closing"""
        print("===== ACCEPT: Dialog closing - applying changes and closing =====")
        
        # Apply settings one final time before closing
        self.apply_settings()
        
        # Close the dialog
        super().accept()

    def reject(self):
        """Handle dialog rejection"""
        if self.setup_widget.has_unapplied_changes:
            response = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unapplied changes. Do you want to discard these changes?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if response == QMessageBox.StandardButton.No:
                return  # Don't close the dialog

        super().reject()

    def on_staff_added(self, instrument_id, staff_type, index):
        print("[DEBUG] on_staff_added called")
        print(f"[DEBUG] Dialog id: {id(self)}")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        print(f"[DEBUG] Dialog parent type: {type(self.parent())}")
        print(f"[DEBUG] Received signal: instrument_id={instrument_id}, staff_type={staff_type}, index={index}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print(f"ADDED: Staff {instrument_id} of type {staff_type} at index {index}")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score using dialog's method
        self.apply_changes_immediate(options)

    def on_staff_removed(self, index):
        print("[DEBUG] on_staff_removed called")
        print(f"[DEBUG] Received signal: index={index}")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print(f"REMOVED: Staff at index {index}")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score using dialog's method
        self.apply_changes_immediate(options)

    def on_staff_visibility_changed(self, index, is_visible):
        print("[DEBUG] on_staff_visibility_changed called")
        print(f"[DEBUG] Received signal: index={index}, is_visible={is_visible}")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print(f"VISIBILITY CHANGED: Staff at index {index} is now {'visible' if is_visible else 'hidden'}")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score using dialog's method
        self.apply_changes_immediate(options)

    def on_staff_options_changed(self, index, settings):
        print("[DEBUG] on_staff_options_changed called")
        print(f"[DEBUG] Received signal: index={index}, settings={settings}")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print(f"OPTIONS CHANGED: Staff at index {index} settings updated: {settings}")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score
        self.apply_changes_immediate(options)

    def on_staff_reordered(self, from_index, to_index):
        print("[DEBUG] on_staff_reordered called")
        print(f"[DEBUG] Received signal: from_index={from_index}, to_index={to_index}")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print("REORDERED: Staff order changed")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score
        self.apply_changes_immediate(options)

    def on_layout_changed(self):
        print("[DEBUG] on_layout_changed called")
        print(f"[DEBUG] Dialog parent: {self.parent()}")
        if hasattr(self.parent(), 'staff_view'):
            print(f"[DEBUG] Dialog parent.staff_view: {self.parent().staff_view}")
        self.has_unapplied_changes = True
        self.setup_widget.has_unapplied_changes = True
        print("LAYOUT CHANGED: Layout settings changed")
        options = self.setup_widget.get_setup_options()
        # Apply changes immediately to the score
        self.apply_changes_immediate(options)

    def apply_changes_immediate(self, options):
        """Apply changes immediately to the score for live preview"""
        print("===== APPLY_CHANGES_IMMEDIATE: Applying changes immediately =====")
        
        # Get document reference
        doc = None
        staff_view = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, get document from music page
            if hasattr(self.parent().music_page, "staff_view") and self.parent().music_page.staff_view:
                doc = self.parent().music_page.staff_view.document
                staff_view = self.parent().music_page.staff_view
                print("IMMEDIATE: Got document from desktop window's music page staff view")
        elif hasattr(self.parent(), "document"):
            # Direct parent is StaffView
            doc = self.parent().document
            staff_view = self.parent()
            print("IMMEDIATE: Got document from direct StaffView parent")
        elif hasattr(self.parent(), "staff_view") and hasattr(self.parent().staff_view, "document"):
            # Parent has staff_view attribute
            doc = self.parent().staff_view.document
            staff_view = self.parent().staff_view
            print("IMMEDIATE: Got document from parent.staff_view")

        if doc:
            # Apply the options to the document
            self._apply_options_to_document(doc, options)
            
            # CRITICAL: Also apply options to the staff view and force setup mode
            if staff_view and hasattr(staff_view, "apply_setup_options"):
                print("IMMEDIATE: Forcing staff view to apply setup options and enter setup mode")
                options["force_setup_mode"] = True
                staff_view.apply_setup_options(options)
                staff_view.is_setup_mode = True
                if hasattr(staff_view, "update"):
                    staff_view.update()
                    print("IMMEDIATE: Forced staff view update (setup mode)")
            else:
                # Fallback: just update parent
                if hasattr(self.parent(), "update"):
                    self.parent().update()
                    print("IMMEDIATE: Forced parent update")
        
        print("===== APPLY_CHANGES_IMMEDIATE: Changes applied =====")

    def _apply_options_to_document(self, doc, options):
        """Apply options to document for immediate rendering"""
        # Extract section and staff type maps
        section_map = options.get("section_map", {})
        staff_type_map = options.get("staff_type_map", {})
        plugin_map = options.get("plugin_map", {})
        section_display_order = options.get("section_display_order", {})
        
        # Store the maps in the document
        if not hasattr(doc, "section_map"):
            doc.section_map = {}
        doc.section_map.update(section_map)
        
        if not hasattr(doc, "section_display_order"):
            doc.section_display_order = {}
        doc.section_display_order.update(section_display_order)
        
        if not hasattr(doc, "plugin_map"):
            doc.plugin_map = {}
        doc.plugin_map.update(plugin_map)
        
        # Update staff data
        for staff in options.get("added_staves", []):
            instrument_id = staff.get("instrument_id", "")
            if instrument_id in section_map:
                staff["section"] = section_map[instrument_id]
            if instrument_id in staff_type_map:
                staff["staff_type"] = staff_type_map[instrument_id]
            if instrument_id in plugin_map:
                staff["plugin"] = plugin_map[instrument_id]
        
        # Update document with new staff configuration
        doc.staves = options.get("added_staves", [])
        print(f"IMMEDIATE: Updated document with {len(doc.staves)} staves")

    def apply_changes(self):
        """Apply changes to the setup widget and document"""
        # Get options from the setup widget
        options = self.setup_widget.get_setup_options()

        # Get document reference
        doc = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, get document from music page
            if hasattr(self.parent().music_page, "staff_view") and self.parent().music_page.staff_view:
                doc = self.parent().music_page.staff_view.document
                print("APPLY: Got document from desktop window's music page staff view")
        elif hasattr(self.parent(), "document"):
            # Direct parent is StaffView
            doc = self.parent().document
            print("APPLY: Got document from direct StaffView parent")
        elif hasattr(self.parent(), "staff_view") and hasattr(self.parent().staff_view, "document"):
            # Parent has staff_view attribute
            doc = self.parent().staff_view.document
            print("APPLY: Got document from parent.staff_view")

        if doc:
            # Create section and staff type maps
            section_map = {}
            staff_type_map = {}
            plugin_map = {}
            # NEW: Create explicit section display order tracking
            section_display_order = {}
            
            # CRITICAL: First, extract section data directly from the UI
            print("APPLY: Extracting section, plugin, and staff type data directly from UI")
            # NEW: Track which sections we've seen and their positions
            seen_sections = set()
            section_positions = {}

            for i in range(self.setup_widget.staff_list.topLevelItemCount()):
                item = self.setup_widget.staff_list.topLevelItem(i)
                instrument_name = item.text(0)
                instrument_id = item.data(0, Qt.ItemDataRole.UserRole).get('instrument_id', instrument_name.lower().replace(" ", "_"))
                plugin_text = item.text(4)  # Plugin is in column 4
                section_text = item.text(3)  # Section is in column 3
                staff_type_text = item.text(1)

                print(
                    f"APPLY: UI shows - {instrument_name} ({instrument_id}): section='{section_text}', plugin='{plugin_text}', staff_type='{staff_type_text}'"
                )

                # NEW: Track section positions based on first occurrence in tree
                if section_text and section_text not in seen_sections:
                    seen_sections.add(section_text)
                    # Use the item index directly as display order
                    section_positions[section_text] = i
                    # Set explicit section display order
                    section_display_order[section_text] = i
                    print(f"APPLY: Section '{section_text}' first appears at position {i}")

                # Get staff data from the item
                staff_data = item.data(0, Qt.ItemDataRole.UserRole)
                if staff_data:
                    # Always synchronize staff_data with UI
                    if section_text:
                        staff_data["section"] = section_text
                        section_map[instrument_id] = section_text
                        print(
                            f"APPLY: Setting section '{section_text}' for '{instrument_id}' from UI"
                        )

                    # Sync plugin data
                    if plugin_text:
                        staff_data["plugin"] = plugin_text
                        plugin_map[instrument_id] = plugin_text
                        print(
                            f"APPLY: Setting plugin '{plugin_text}' for '{instrument_id}' from UI"
                        )

                    # Convert displayed staff type to internal format
                    if staff_type_text:
                        staff_type = staff_type_text.lower().replace(" ", "_")
                        staff_data["staff_type"] = staff_type
                        staff_type_map[instrument_id] = staff_type

                    # Preserve custom_name and custom_abbr if they exist
                    # The item text (column 0) is the display name
                    if "custom_name" in staff_data:
                        print(f"APPLY: Preserving custom_name '{staff_data['custom_name']}' for '{instrument_id}'")
                    if "custom_abbr" in staff_data:
                        print(f"APPLY: Preserving custom_abbr '{staff_data['custom_abbr']}' for '{instrument_id}'")

                    # Update the item's data
                    item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

            # NEW: Debug section display order from UI
            print(f"APPLY: Extracted section_display_order from UI:")
            for section_name, display_order in section_display_order.items():
                print(f"  Section '{section_name}' display_order = {display_order}")

            # Verify against what's in the options
            print(
                f"APPLY: Verifying against options with {len(options.get('added_staves', []))} staves"
            )
            for staff in options.get("added_staves", []):
                instrument_id = staff.get("instrument_id", "")
                if not instrument_id and "instrument_name" in staff:
                    instrument_name = staff["instrument_name"]
                    instrument_id = instrument_name.lower().replace(" ", "_")

                # Skip if we already have this instrument in the maps
                if instrument_id in section_map:
                    continue

                if instrument_id:
                    # Get section from staff data
                    section = staff.get("section", "")
                    if not section and "staff_data" in staff and "section" in staff["staff_data"]:
                        section = staff["staff_data"]["section"]

                    if section:
                        section_map[instrument_id] = section
                        print(
                            f"APPLY: Added missing section '{section}' for '{instrument_id}' from options"
                        )

                    # Get plugin from staff data
                    plugin = staff.get("plugin", "")
                    if not plugin and "staff_data" in staff and "plugin" in staff["staff_data"]:
                        plugin = staff["staff_data"]["plugin"]

                    if plugin:
                        plugin_map[instrument_id] = plugin
                        print(
                            f"APPLY: Added missing plugin '{plugin}' for '{instrument_id}' from options"
                        )

                    # Get staff type if not already set
                    if instrument_id not in staff_type_map:
                        staff_type = staff.get("staff_type", "")
                        if staff_type:
                            staff_type_map[instrument_id] = staff_type

            # Store the section map in the document for future use
            if not hasattr(doc, "section_map"):
                doc.section_map = {}

            print(f"APPLY: Updating document section_map with {len(section_map)} entries")
            for instr, section in section_map.items():
                print(f"APPLY: Setting section '{section}' for '{instr}' in document")
            doc.section_map.update(section_map)

            # NEW: Store the section display order in the document
            if not hasattr(doc, "section_display_order"):
                doc.section_display_order = {}
            
            print(f"APPLY: Updating document section_display_order with {len(section_display_order)} entries")
            for section_name, display_order in section_display_order.items():
                print(f"APPLY: Setting section '{section_name}' display_order to {display_order} in document")
            doc.section_display_order.update(section_display_order)

            # Store the plugin map in the document for future use
            if not hasattr(doc, "plugin_map"):
                doc.plugin_map = {}

            print(f"APPLY: Updating document plugin_map with {len(plugin_map)} entries")
            for instr, plugin in plugin_map.items():
                print(f"APPLY: Setting plugin '{plugin}' for '{instr}' in document")
            doc.plugin_map.update(plugin_map)

            # Explicitly update the options with our most accurate section_map, plugin_map, and staff_type_map
            options["section_map"] = section_map
            options["plugin_map"] = plugin_map
            options["staff_type_map"] = staff_type_map
            # NEW: Also add section_display_order to options
            options["section_display_order"] = section_display_order

            # Update all staff data in options
            for staff_entry in options["added_staves"]:
                instrument_id = staff_entry.get("instrument_id", "")
                if instrument_id in section_map:
                    section = section_map[instrument_id]
                    staff_entry["section"] = section
                    if "staff_data" in staff_entry:
                        staff_entry["staff_data"]["section"] = section

                if instrument_id in plugin_map:
                    plugin = plugin_map[instrument_id]
                    staff_entry["plugin"] = plugin
                    if "staff_data" in staff_entry:
                        staff_entry["staff_data"]["plugin"] = plugin

                # Also preserve custom_name and custom_abbr from the UI item's staff_data
                for i in range(self.setup_widget.staff_list.topLevelItemCount()):
                    item = self.setup_widget.staff_list.topLevelItem(i)
                    item_data = item.data(0, Qt.ItemDataRole.UserRole)
                    if item_data and item_data.get('instrument_id') == instrument_id:
                        if "custom_name" in item_data:
                            staff_entry["custom_name"] = item_data["custom_name"]
                            if "staff_data" in staff_entry:
                                staff_entry["staff_data"]["custom_name"] = item_data["custom_name"]
                            print(f"APPLY: Saved custom_name '{item_data['custom_name']}' for '{instrument_id}'")
                        if "custom_abbr" in item_data:
                            staff_entry["custom_abbr"] = item_data["custom_abbr"]
                            if "staff_data" in staff_entry:
                                staff_entry["staff_data"]["custom_abbr"] = item_data["custom_abbr"]
                            print(f"APPLY: Saved custom_abbr '{item_data['custom_abbr']}' for '{instrument_id}'")
                        break

            # Debug check of options
            print("APPLY: Final options structure:")
            for staff_entry in options["added_staves"]:
                name = staff_entry.get("instrument_name", "")
                section = staff_entry.get("section", "")
                plugin = staff_entry.get("plugin", "Default")
                print(f"APPLY: {name}: section='{section}', plugin='{plugin}'")

        # Apply changes using the widget's method
        self.setup_widget.apply_changes()

        # Clear unapplied changes states
        self.has_unapplied_changes = False
        self.setup_widget.has_unapplied_changes = False
        options["has_unapplied_changes"] = False

        print("APPLY: All changes have been applied")

        # Store dialog settings immediately to ensure they're available when returning to setup mode
        # Try different parent structures to find the staff view
        staff_view = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, get staff view from music page
            if hasattr(self.parent().music_page, "staff_view"):
                staff_view = self.parent().music_page.staff_view
                print("APPLY: Got staff view from desktop window's music page")
        elif hasattr(self.parent(), "staff_view"):
            # Parent has staff_view attribute
            staff_view = self.parent().staff_view
            print("APPLY: Got staff view from parent.staff_view")
        elif hasattr(self.parent(), "document"):
            # Parent is StaffView directly
            staff_view = self.parent()
            print("APPLY: Parent is StaffView directly")

        if staff_view:
            staff_view.dialog_settings = options
            print(
                f"APPLY: Saved dialog settings with {len(options.get('section_map', {}))} sections and {len(options.get('plugin_map', {}))} plugins"
            )
            # NEW: Debug section display order in dialog settings
            print(f"APPLY: Saved section_display_order with {len(options.get('section_display_order', {}))} entries")
            for section_name, display_order in options.get('section_display_order', {}).items():
                print(f"  Section '{section_name}' display_order = {display_order}")
        else:
            print("APPLY: Warning - could not find staff view to save dialog settings")

    def get_setup_options(self):
        """Get the setup options from the widget"""
        # Retrieve options from the setup widget
        options = self.setup_widget.get_setup_options()

        # Check if we have a document to add additional data from
        doc = None
        if hasattr(self.parent(), "music_page") and self.parent().music_page:
            # Parent is DesktopWindow, get document from music page
            if hasattr(self.parent().music_page, "staff_view") and self.parent().music_page.staff_view:
                doc = self.parent().music_page.staff_view.document
                print("GET_OPTIONS: Got document from desktop window's music page staff view")
        elif hasattr(self.parent(), "document"):
            # Direct parent is StaffView
            doc = self.parent().document
            print("GET_OPTIONS: Got document from direct StaffView parent")
        elif hasattr(self.parent(), "staff_view") and self.parent().staff_view:
            # Parent has staff_view attribute
            doc = self.parent().staff_view.document
            print("GET_OPTIONS: Got document from parent.staff_view")

        if doc:
            # Get section data from document
            if hasattr(doc, "section_map"):
                # Count existing sections and add them to the options
                print(f"Retrieved {len(doc.section_map)} sections from document for options")
                for instrument_id, section in doc.section_map.items():
                    if instrument_id not in options["section_map"] and section:
                        options["section_map"][instrument_id] = section

            # Get plugin data from document
            if hasattr(doc, "plugin_map"):
                # Count existing plugins and add them to the options
                print(f"Retrieved {len(doc.plugin_map)} plugins from document for options")
                for instrument_id, plugin in doc.plugin_map.items():
                    if instrument_id not in options["plugin_map"] and plugin:
                        options["plugin_map"][instrument_id] = plugin

        print(
            f"Created options with {len(options['section_map'])} sections and {len(options['plugin_map'])} plugins"
        )
        return options

    def done(self, result):
        """Custom handler for OK button clicks to guarantee changes are applied"""
        print(f"===== DIALOG DONE: Handling dialog completion with result {result} =====")

        # Check if we're already processing from apply_and_close to avoid double processing
        if hasattr(self, '_applying_changes') and self._applying_changes:
            print("===== DIALOG DONE: Skipping processing - already handled by apply_and_close =====")
            # Clear the flag and call parent done to close properly
            self._applying_changes = False
            super().done(result)
            return

        # Only proceed with applying changes if the dialog was accepted (OK button was clicked)
        if result == QDialog.DialogCode.Accepted.value:
            print("===== DIALOG DONE: Dialog was ACCEPTED, applying changes =====")

            # Make sure we have the latest options
            options = self.get_setup_options()

            # Apply changes before closing
            print("===== DIALOG DONE: Ensuring changes are applied before closing =====")
            self.setup_widget.apply_changes()

            # Update options to reflect that changes have been applied
            options["has_unapplied_changes"] = False

            # Apply the changes to the parent and switch to edit mode when OK is clicked
            if hasattr(self.parent(), "is_setup_mode"):
                print(
                    "===== DIALOG DONE: Applying changes to parent and switching to edit mode ====="
                )
                # Ensure parent applies the dialog settings
                if hasattr(self.parent(), "apply_setup_options"):
                    self.parent().apply_setup_options(options)
                    self.parent().dialog_settings = options

                # Switch to edit mode immediately
                if hasattr(self.parent(), "enter_edit_mode"):
                    print("===== DIALOG DONE: Switching to edit mode =====")
                    self.parent().enter_edit_mode()
                    print("===== DIALOG DONE: Edit mode activated =====")
                else:
                    # Fallback: Manually set mode flags
                    self.parent().is_setup_mode = False
                    if hasattr(self.parent(), "document") and hasattr(
                        self.parent().document, "layout"
                    ):
                        self.parent().document.layout.set_setup_mode(False)
                    print("===== DIALOG DONE: Manually set mode to edit mode =====")

                # Update the UI
                self.parent().update()
            elif hasattr(self.parent(), "staff_view"):
                # Parent is likely MainWindow with staff_view attribute
                print(
                    "===== DIALOG DONE: Applying changes to parent.staff_view and switching to edit mode ====="
                )
                # Ensure parent.staff_view applies the dialog settings
                if hasattr(self.parent().staff_view, "apply_setup_options"):
                    self.parent().staff_view.apply_setup_options(options)
                    self.parent().staff_view.dialog_settings = options

                # Switch to edit mode immediately
                if hasattr(self.parent().staff_view, "enter_edit_mode"):
                    print("===== DIALOG DONE: Switching to edit mode =====")
                    self.parent().staff_view.enter_edit_mode()
                    print("===== DIALOG DONE: Edit mode activated =====")
                else:
                    # Fallback: Manually set mode flags
                    self.parent().staff_view.is_setup_mode = False
                    if hasattr(self.parent().staff_view, "document") and hasattr(
                        self.parent().staff_view.document, "layout"
                    ):
                        self.parent().staff_view.document.layout.set_setup_mode(False)
                    print("===== DIALOG DONE: Manually set mode to edit mode =====")

                # Update the UI
                self.parent().staff_view.update()

                # If parent is MainWindow, update the toggle mode action text
                if hasattr(self.parent(), "toggle_mode_action"):
                    self.parent().toggle_mode_action.setText("Score Setup")
                    print("===== DIALOG DONE: Updated toggle button text to 'Score Setup' =====")
        else:
            print("===== DIALOG DONE: Dialog was REJECTED, keeping setup mode =====")

        # Call the parent class's done method to properly close the dialog
        super().done(result)

    def apply_and_close(self):
        """Custom method to apply changes and ensure mode switching to edit mode"""
        print("===== APPLY_AND_CLOSE: Starting apply and close process =====")
        
        # Set a flag to indicate this is coming from apply_and_close to avoid double processing
        self._applying_changes = True
        
        # Get the latest options
        options = self.get_setup_options()

        # Apply changes before closing
        print("===== APPLY_AND_CLOSE: Applying changes =====")
        self.setup_widget.apply_changes()

        # Update options to reflect that changes have been applied
        options["has_unapplied_changes"] = False
        
        # **ALWAYS SWITCH TO EDIT MODE when Apply is clicked**
        print("===== APPLY_AND_CLOSE: Always switching to edit mode =====")
        
        # Apply changes to parent first
        if hasattr(self.parent(), "is_setup_mode"):
            print("===== APPLY_AND_CLOSE: Applying changes to direct parent =====")
            # Ensure parent applies the dialog settings
            if hasattr(self.parent(), "apply_setup_options"):
                self.parent().apply_setup_options(options)
                self.parent().dialog_settings = options

            # Switch to edit mode immediately
            if hasattr(self.parent(), "enter_edit_mode"):
                print("===== APPLY_AND_CLOSE: Switching to edit mode via enter_edit_mode =====")
                self.parent().enter_edit_mode()
                print("===== APPLY_AND_CLOSE: Edit mode activated =====")

            # Update the UI
            self.parent().update()
            
            # CRITICAL FIX: Update toggle button text for main window if accessible
            # Try multiple paths to reach MainWindow's update_mode_interface_text
            main_window_updated = False
            
            # Path 1: Direct parent has parent with update method
            if hasattr(self.parent(), "parent") and hasattr(self.parent().parent(), "update_mode_interface_text"):
                self.parent().parent().update_mode_interface_text()
                print("===== APPLY_AND_CLOSE: Updated main window interface text via parent.parent =====")
                main_window_updated = True
                
            # Path 2: Check if parent itself has main window reference
            if not main_window_updated and hasattr(self.parent(), "main_window") and hasattr(self.parent().main_window, "update_mode_interface_text"):
                self.parent().main_window.update_mode_interface_text()
                print("===== APPLY_AND_CLOSE: Updated main window interface text via parent.main_window =====")
                main_window_updated = True
                
            if not main_window_updated:
                print("===== APPLY_AND_CLOSE: WARNING - Could not find main window to update interface =====")
                print(f"===== APPLY_AND_CLOSE: Parent type: {type(self.parent())} =====")
                if hasattr(self.parent(), "parent"):
                    print(f"===== APPLY_AND_CLOSE: Parent.parent type: {type(self.parent().parent())} =====")
            
        elif hasattr(self.parent(), "staff_view"):
            # Parent is likely MainWindow with staff_view attribute
            print("===== APPLY_AND_CLOSE: Applying changes to parent.staff_view =====")
            # Ensure parent.staff_view applies the dialog settings
            if hasattr(self.parent().staff_view, "apply_setup_options"):
                self.parent().staff_view.apply_setup_options(options)
                self.parent().staff_view.dialog_settings = options

            # Switch to edit mode immediately
            if hasattr(self.parent().staff_view, "enter_edit_mode"):
                print("===== APPLY_AND_CLOSE: Switching to edit mode via staff_view.enter_edit_mode =====")
                self.parent().staff_view.enter_edit_mode()
                print("===== APPLY_AND_CLOSE: Edit mode activated =====")

            # Update the UI
            self.parent().staff_view.update()

            # CRITICAL FIX: Update toggle button and menu text - this is the MainWindow path
            interface_updated = False
            if hasattr(self.parent(), "update_mode_interface_text"):
                try:
                    self.parent().update_mode_interface_text()
                    print("===== APPLY_AND_CLOSE: Updated main window interface text via MainWindow =====")
                    interface_updated = True
                except Exception as e:
                    print(f"===== APPLY_AND_CLOSE: ERROR calling parent.update_mode_interface_text: {e} =====")
            
            # Backup method: Try to find MainWindow through QApplication
            if not interface_updated:
                try:
                    from PyQt6.QtWidgets import QApplication
                    app = QApplication.instance()
                    if app:
                        main_windows = [w for w in app.topLevelWidgets() if w.__class__.__name__ == 'MainWindow']
                        if main_windows:
                            main_window = main_windows[0]
                            if hasattr(main_window, 'update_mode_interface_text'):
                                main_window.update_mode_interface_text()
                                print("===== APPLY_AND_CLOSE: Updated main window interface text via QApplication search =====")
                                interface_updated = True
                except Exception as e:
                    print(f"===== APPLY_AND_CLOSE: ERROR with QApplication search: {e} =====")
            
            if not interface_updated:
                print("===== APPLY_AND_CLOSE: WARNING - Could not update main window interface through any method =====")

        # Clear unapplied changes flags
        self.has_unapplied_changes = False
        self.setup_widget.has_unapplied_changes = False
        
        print("===== APPLY_AND_CLOSE: Mode switching completed, accepting dialog =====")
        
        # Now accept the dialog properly to ensure it closes with accepted status
        # The done() method will be called but won't do double processing due to our flag
        self.accept()

    def refresh_from_document(self):
        """Refresh the dialog from the current document state - delegates to setup widget"""
        print("DIALOG: refresh_from_document() called - delegating to setup_widget")
        if hasattr(self.setup_widget, 'refresh_from_document'):
            self.setup_widget.refresh_from_document()
        else:
            print("DIALOG: setup_widget doesn't have refresh_from_document method")
