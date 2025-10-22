from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QSplitter,
    QGroupBox,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QComboBox,
    QSlider,
    QSpinBox,
    QGridLayout,
    QTextEdit,
    QTabWidget,
    QScrollArea,
    QSizePolicy,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QSettings
from src.plugins.plugin_scanner import PluginScanner
from .add_staves_toolbar import AddStavesToolbar


class ScoreSetupWidget(QWidget):
    # Define signals at class level
    staff_added = pyqtSignal(str, str, int)  # instrument_id, staff_type, index
    staff_removed = pyqtSignal(int)  # index
    staff_visibility_changed = pyqtSignal(int, bool)  # index, is_visible
    staff_options_changed = pyqtSignal(int, dict)  # index, settings
    staff_reordered = pyqtSignal(int, int)  # from_index, to_index
    setup_completed = pyqtSignal()  # Signal emitted when setup is completed

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize state variables
        self.has_unapplied_changes = False
        self._updating_selection = False  # Flag to prevent recursion in selection changes
        
        # Setup the UI
        self.setup_ui()
        self.populate_instruments()
        
        # Connect signals to trigger immediate updates
        self.staff_list.itemChanged.connect(self._on_any_setting_changed)
        # Note: Signal connections to dialog handlers are made in ScoreSetupDialog.__init__
        
        # Update the count label
        self.update_staff_count_label()

    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)

        # Add a header with explanation
        header_label = QLabel("Add staves to your score:")
        header_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(header_label)

        # Create a horizontal layout for the main content
        main_layout = QHBoxLayout()
        
        # Left side - Staff addition and instrument browser
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Add staff type buttons at the top
        staff_buttons_group = QGroupBox("Add Staff")
        staff_buttons_layout = QVBoxLayout(staff_buttons_group)

        add_treble_btn = QPushButton("Add Treble Clef Staff")
        add_alto_btn = QPushButton("Add Alto Clef Staff")
        add_bass_btn = QPushButton("Add Bass Clef Staff")
        add_grand_btn = QPushButton("Add Grand Staff")
        add_percussion_btn = QPushButton("Add Percussion Clef Staff")

        add_treble_btn.clicked.connect(lambda: self.add_generic_staff("treble"))
        add_alto_btn.clicked.connect(lambda: self.add_generic_staff("alto"))
        add_bass_btn.clicked.connect(lambda: self.add_generic_staff("bass"))
        add_grand_btn.clicked.connect(lambda: self.add_generic_staff("grand"))
        add_percussion_btn.clicked.connect(lambda: self.add_generic_staff("percussion"))

        staff_buttons_layout.addWidget(add_treble_btn)
        staff_buttons_layout.addWidget(add_alto_btn)
        staff_buttons_layout.addWidget(add_bass_btn)
        staff_buttons_layout.addWidget(add_grand_btn)
        staff_buttons_layout.addWidget(add_percussion_btn)

        left_layout.addWidget(staff_buttons_group)
        
        # Instrument browser
        instrument_group = QGroupBox("Choose from instruments")
        instrument_layout = QVBoxLayout(instrument_group)

        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search instruments...")
        self.search_box.textChanged.connect(self.filter_instruments)
        instrument_layout.addWidget(self.search_box)
        
        # Available instruments tree
        self.instrument_tree = QTreeWidget()
        self.instrument_tree.setHeaderLabels(["Available Instruments"])
        self.instrument_tree.itemClicked.connect(
            self.on_instrument_clicked
        )  # Add single-click handler
        # Do NOT connect itemSelectionChanged as it duplicates functionality
        # and causes double-addition issues
        instrument_layout.addWidget(self.instrument_tree)

        left_layout.addWidget(instrument_group)
        
        # Right side - Added staves and management buttons
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Added staves list with headers
        staves_label = QLabel("Added Staves:")
        staves_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(staves_label)
        
        # Add staff count label
        self.staff_count_label = QLabel("Total staves: 0")
        right_layout.addWidget(self.staff_count_label)
        
        # Add selection status label for contiguous feedback
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 10px; padding: 2px;")
        right_layout.addWidget(self.status_label)

        self.staff_list = QTreeWidget()
        self.staff_list.setHeaderLabels(
            ["Name", "Staff Type", "Clef", "Section", "Plugin/Instrument"]
        )
        self.staff_list.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.staff_list.setColumnWidth(0, 180)
        self.staff_list.setColumnWidth(1, 120)
        self.staff_list.setColumnWidth(2, 80)
        self.staff_list.setColumnWidth(3, 120)
        self.staff_list.setColumnWidth(4, 120)
        self.staff_list.itemSelectionChanged.connect(self.on_staff_selection_changed)
        self.staff_list.itemChanged.connect(self.on_staff_changed)
        right_layout.addWidget(self.staff_list)
        
        # Staff management buttons
        button_layout = QHBoxLayout()
        
        # Lock selection checkbox - initialize properly
        self.lock_selection = QCheckBox("Lock Selection")
        self.lock_selection.setToolTip("Keep the same staves selected when reordering")
        self.lock_selection.setChecked(False)  # Default to unchecked
        
        # Connect lock selection change handler
        self.lock_selection.stateChanged.connect(self.on_lock_selection_changed)

        # Navigation and edit buttons
        up_btn = QPushButton("↑")
        down_btn = QPushButton("↓")
        remove_btn = QPushButton("Remove")
        attributes_btn = QPushButton("Staff Attributes")

        up_btn.clicked.connect(self.move_staff_up)
        down_btn.clicked.connect(self.move_staff_down)
        remove_btn.clicked.connect(self.remove_staff)
        attributes_btn.clicked.connect(self.show_staff_attributes_dialog)

        button_layout.addWidget(self.lock_selection)
        button_layout.addWidget(up_btn)
        button_layout.addWidget(down_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addWidget(attributes_btn)
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        
        # Set sizes for left and right panels
        left_panel.setMinimumWidth(300)
        right_panel.setMinimumWidth(400)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Add main layout to the widget
        layout.addLayout(main_layout)

        # Initialize layout settings
        self.layout_settings = {
            "staff_spacing": 40,
            "system_spacing": 60,
            "measures_per_system": 4
        }
        
        # Initialize plugin scanner
        self.plugin_scanner = PluginScanner()
        
        # Set the added_staves_list alias
        self.added_staves_list = self.staff_list

    def populate_instruments(self):
        """Populate the instrument tree with available instruments"""
        # Clear existing items
        self.instrument_tree.clear()

        # Add enabled plugins directly
        plugins = self.plugin_scanner.get_enabled_plugins()
        for plugin in plugins:
            plugin_item = QTreeWidgetItem(self.instrument_tree)
            plugin_item.setText(0, plugin.name)
            plugin_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {"type": "plugin", "id": plugin.id, "name": plugin.name},
            )

        # Add General MIDI instruments
        gm_item = QTreeWidgetItem(self.instrument_tree)
        gm_item.setText(0, "General MIDI")

        # Add GM instrument categories
        gm_categories = {
            "Piano": [
                "Acoustic Grand",
                "Bright Acoustic",
                "Electric Grand",
                "Honky-tonk",
                "Electric Piano 1",
                "Electric Piano 2",
                "Harpsichord",
                "Clavi",
            ],
            "Strings": [
                "Violin",
                "Viola",
                "Cello",
                "Contrabass",
                "Tremolo Strings",
                "Pizzicato Strings",
                "Orchestral Harp",
                "Timpani",
            ],
            "Woodwind": [
                "Flute",
                "Oboe",
                "Clarinet",
                "Bassoon",
                "Piccolo",
                "English Horn",
                "Bass Clarinet",
                "Contrabassoon",
            ],
            "Brass": [
                "Trumpet",
                "Trombone",
                "Tuba",
                "Muted Trumpet",
                "French Horn",
                "Brass Section",
                "Synth Brass 1",
                "Synth Brass 2",
            ],
            "Percussion": [
                "Timpani",
                "Snare Drum",
                "Bass Drum",
                "Cymbals",
                "Triangle",
                "Wood Block",
                "Tambourine",
                "Cowbell",
            ],
        }

        for category, instruments in gm_categories.items():
            category_item = QTreeWidgetItem(gm_item)
            category_item.setText(0, category)

            for instrument in instruments:
                instrument_item = QTreeWidgetItem(category_item)
                instrument_item.setText(0, instrument)
                instrument_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {"type": "gm_instrument", "name": instrument, "category": category},
                )

        # Expand all items
        self.instrument_tree.expandAll()

    def on_instrument_clicked(self, item, column):
        try:
            if item is None:
                print("[ERROR] on_instrument_clicked: item is None")
                return
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data.get("type") not in ["plugin", "gm_instrument"]:
                print(f"[ERROR] on_instrument_clicked: Not a valid instrument, data={data}")
                return
            print(f"[DEBUG] on_instrument_clicked called: item={item.text(0) if item else 'None'}, column={column}")
            # Check if this is an actual instrument (not a category)
            if not data or data["type"] not in ["plugin", "gm_instrument"]:
                print(f"[DEBUG] on_instrument_clicked: Not a valid instrument, data={data}")
                return

            # Get the instrument name
            instrument_name = data["name"]

            # Check if a staff is already selected
            selected_staff_items = self.staff_list.selectedItems()
            if selected_staff_items:
                # If a staff is selected, replace it with the clicked instrument
                selected_item = selected_staff_items[0]
                staff_index = self.staff_list.indexOfTopLevelItem(selected_item)

                # Get the current staff data to retain values
                current_staff_data = selected_item.data(0, Qt.ItemDataRole.UserRole)
                current_staff_type = current_staff_data.get("staff_type", "single_staff")
                
                # Get the current display name (preserve the part name)
                current_display_name = selected_item.text(0)

                # Determine staff type and clef for display
                staff_type_display = "Single Staff"
                clef = current_staff_data.get("clef", "treble")  # Get clef from current data with default
                
                if current_staff_type == "grand_staff":
                    staff_type_display = "Grand Staff"
                    clef_display = "Treble/Bass"
                else:
                    # Determine clef display from the clef value
                    if clef == "bass":
                        clef_display = "Bass"
                    elif clef == "alto":
                        clef_display = "Alto"
                    elif clef == "percussion":
                        clef_display = "Percussion"
                    else:
                        clef_display = "Treble"

                # Create new staff data, retaining existing staff type and section
                staff_data = {
                    "instrument_id": current_staff_data.get("instrument_id", "part"),  # PRESERVE original instrument_id
                    "instrument_name": current_staff_data.get("instrument_name", "Part"),  # Retain original instrument name
                    "instrument_abbr": current_staff_data.get("instrument_abbr", ""),  # Retain original abbreviation
                    "staff_type": current_staff_type,  # Retain existing staff type
                    "clef": clef,
                    "key": "C major / A minor (no sharps/flats)",
                    "time_signature": "4/4",
                    "section": current_staff_data.get("section", ""),  # Retain existing section
                    "plugin": instrument_name  # Set the plugin value to the instrument name
                }

                print(f"Replacing staff #{staff_index} with {instrument_name}")

                # Replace the staff item
                new_staff_item = QTreeWidgetItem()
                new_staff_item.setText(0, current_display_name)  # Keep the original display name
                new_staff_item.setText(1, staff_type_display)  # Keep the same staff type display
                new_staff_item.setText(2, clef_display)  # Keep the same clef display
                new_staff_item.setText(3, staff_data["section"])  # Retain section display
                new_staff_item.setText(4, instrument_name)  # Set Plugin/Instrument column
                new_staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                # Replace the old staff item with the new one
                self.staff_list.takeTopLevelItem(staff_index)
                self.staff_list.insertTopLevelItem(staff_index, new_staff_item)

                # Mark that there are unapplied changes
                self.has_unapplied_changes = True
                print(f"[DEBUG] ScoreSetupWidget emitting staff_removed signal: {staff_index}")
                self.staff_removed.emit(staff_index)
                print(f"[DEBUG] ScoreSetupWidget emitting staff_added signal: {staff_data['instrument_id']}, {staff_data['staff_type']}, {staff_index}")
                self.staff_added.emit(
                    staff_data["instrument_id"], staff_data["staff_type"], staff_index
                )
            else:
                # If no staff is selected, add a new one
                self.add_staff_from_item(item)
            self.instrument_tree.clearSelection()
            self.staff_list.clearSelection()
        except Exception as e:
            print(f"[CRASH] Exception in on_instrument_clicked: {e}")
            import traceback
            traceback.print_exc()

    def add_staff_from_item(self, item):
        try:
            if item is None:
                print("[ERROR] add_staff_from_item: item is None")
                return
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data.get("type") not in ["plugin", "gm_instrument"]:
                print(f"[ERROR] add_staff_from_item: Not a valid instrument, data={data}")
                return
            print(f"[DEBUG] add_staff_from_item called: item={item.text(0) if item else 'None'}")
            # Save state before making changes for undo/redo functionality
            if hasattr(self, 'parent_view') and hasattr(self.parent_view, 'document') and hasattr(self.parent_view.document, 'save_state'):
                self.parent_view.document._undo_context = "Add Staff"
                self.parent_view.document.save_state("Add Staff")
                print("UNDO: Saved state before adding staff")
                
            # Use the actual instrument name for the staff
            instrument_name = data["name"]
            staff_type_display = "Single Staff"  # Default display
            clef_display = "Treble"  # Default clef display

            # Determine appropriate clef based on instrument category if available
            clef = "treble"  # Default to treble
            if data["type"] == "gm_instrument" and "category" in data:
                category = data["category"]
                # Set bass clef for low-register instruments
                if category == "Piano":
                    # Piano should be grand staff
                    staff_type_display = "Grand Staff"
                    clef_display = "Treble/Bass"
                elif instrument_name in [
                    "Cello",
                    "Contrabass",
                    "Tuba",
                    "Bass Drum",
                    "Bassoon",
                    "Contrabassoon",
                ]:
                    clef = "bass"
                    clef_display = "Bass"

            # Determine staff_type internal representation
            internal_staff_type = staff_type_display.lower().replace(" ", "_")
            if "Grand" in staff_type_display:
                internal_staff_type = "grand_staff"
            else:
                internal_staff_type = "single_staff"

            # Create staff data with the actual instrument name
            staff_data = {
                "instrument_id": instrument_name.lower().replace(" ", "_"),
                "instrument_name": instrument_name,  # Use actual instrument name
                "instrument_abbr": instrument_name[:3].upper(),  # Create abbreviation from name
                "staff_type": internal_staff_type,
                "clef": clef,
                "key": "C major / A minor (no sharps/flats)",
                "time_signature": "4/4",
                "section": "",  # Add section field with empty string
                "actual_instrument": data["name"],  # Store the actual instrument
                "plugin": instrument_name  # Store the instrument name as the plugin value
            }

            # Add to list
            staff_item = QTreeWidgetItem(self.staff_list)
            staff_item.setText(0, self.get_new_instrument_name("part"))  # Use "Part" as the display name
            staff_item.setText(1, staff_type_display)  # Display staff type
            staff_item.setText(2, clef_display)  # Display clef
            staff_item.setText(3, "")  # Empty section
            staff_item.setText(4, instrument_name)  # Set Plugin/Instrument column
            staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

            # Set column widths
            self.staff_list.setColumnWidth(0, 180)  # Staff name
            self.staff_list.setColumnWidth(1, 120)  # Staff type
            self.staff_list.setColumnWidth(2, 80)  # Clef
            self.staff_list.setColumnWidth(3, 120)  # Section
            self.staff_list.setColumnWidth(4, 120)  # Plugin/Instrument

            # Mark that there are unapplied changes
            self.has_unapplied_changes = True
            index = self.staff_list.indexOfTopLevelItem(staff_item)
            print(f"[DEBUG] ScoreSetupWidget emitting staff_added signal: {staff_data['instrument_id']}, {staff_data['staff_type']}, {index}")
            print(f"[DEBUG] ScoreSetupWidget signal object: {self.staff_added}")
            print(f"[DEBUG] ScoreSetupWidget signal receivers: {self.staff_added.receivers()}")
            self.staff_added.emit(
                staff_data["instrument_id"],
                staff_data["staff_type"],
                index,
            )
            print(f"[DEBUG] ScoreSetupWidget staff_added signal emitted successfully")

            # Clear selections in both lists
            self.instrument_tree.clearSelection()
            self.staff_list.clearSelection()

            print(f"Added {instrument_name} staff")

            print(f"Added {instrument_name} staff")
        except Exception as e:
            print(f"[CRASH] Exception in add_staff_from_item: {e}")
            import traceback
            traceback.print_exc()

    def add_staff(self, instrument_id, staff_type, index=None):
        """Add a staff to the list"""
        print(f"[DEBUG] ScoreSetupWidget.add_staff called: {instrument_id}, {staff_type}, {index}")
        # ... existing code ...
        # Emit signal
        print(f"[DEBUG] ScoreSetupWidget emitting staff_added signal: {instrument_id}, {staff_type}, {index}")
        self.staff_added.emit(instrument_id, staff_type, index)
        # ... existing code ...

    def remove_staff(self, index):
        """Remove a staff from the list"""
        print(f"[DEBUG] ScoreSetupWidget.remove_staff called: {index}")
        
        # Get selected items
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return

        # Remove the selected items
        for item in selected_items:
            item_index = self.staff_list.indexOfTopLevelItem(item)
            if item_index >= 0:
                self.staff_list.takeTopLevelItem(item_index)
                print(f"[DEBUG] ScoreSetupWidget emitting staff_removed signal: {item_index}")
                self.staff_removed.emit(item_index)
        
        # Update the staff count label
        self.update_staff_count_label()
        
        # Mark that there are unapplied changes
        self.has_unapplied_changes = True

    def on_staff_visibility_changed(self, item, column):
        """Handle staff visibility checkbox changes"""
        print(f"[DEBUG] ScoreSetupWidget.on_staff_visibility_changed called: item={item}, column={column}")
        
        # Get the staff index
        index = self.staff_list.indexOfTopLevelItem(item)
        
        # Determine visibility (this would depend on the specific UI implementation)
        is_visible = True  # Default to visible
        
        # Mark that there are unapplied changes
        self.has_unapplied_changes = True
        
        # Emit signal
        print(f"[DEBUG] ScoreSetupWidget emitting staff_visibility_changed signal: {index}, {is_visible}")
        self.staff_visibility_changed.emit(index, is_visible)

    def on_staff_options_changed(self, item, column):
        """Handle staff options changes"""
        print(f"[DEBUG] ScoreSetupWidget.on_staff_options_changed called: item={item}, column={column}")
        
        # Get the staff index
        index = self.staff_list.indexOfTopLevelItem(item)
        
        # Get the staff data
        staff_data = item.data(0, Qt.ItemDataRole.UserRole)
        if staff_data:
            # Mark that there are unapplied changes
            self.has_unapplied_changes = True
            
            # Emit signal
            print(f"[DEBUG] ScoreSetupWidget emitting staff_options_changed signal: {index}, {staff_data}")
            self.staff_options_changed.emit(index, staff_data)

    def move_staff_up(self):
        """Move the selected staff up in the list, skipping complete sections"""
        print(f"[DEBUG] ScoreSetupWidget.move_staff_up called")
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return
        
        # Get the first selected item
        item = selected_items[0]
        current_index = self.staff_list.indexOfTopLevelItem(item)
        
        # Check if we can move up
        if current_index <= 0:
            return

        # Get current section
        current_section = item.text(3)  # Section is in column 3
        
        # Find the target index - skip complete sections
        target_index = current_index - 1
        
        # If we're in a section, find the section boundary
        if current_section:
            # Find the start of the current section
            section_start = current_index
            while section_start > 0:
                prev_item = self.staff_list.topLevelItem(section_start - 1)
                if prev_item.text(3) != current_section:
                    break
                section_start -= 1
            
            # If we're at the start of the section, move to the previous section's start
            if current_index == section_start:
                # Find the previous section's start
                target_index = section_start - 1
                while target_index > 0:
                    prev_item = self.staff_list.topLevelItem(target_index - 1)
                    if prev_item.text(3) and prev_item.text(3) != current_section:
                        # Found a different section, find its start
                        while target_index > 0:
                            prev_item = self.staff_list.topLevelItem(target_index - 1)
                            if prev_item.text(3) != prev_item.text(3):
                                break
                            target_index -= 1
                        break
                    target_index -= 1
            else:
                # We're inside a section, move to the previous staff in the same section
                target_index = current_index - 1
        
        # Ensure target index is valid
        if target_index < 0:
            target_index = 0
        
        # Calculate indices
        from_index = current_index
        to_index = target_index
        
        # Move the item
        self.staff_list.takeTopLevelItem(from_index)
        self.staff_list.insertTopLevelItem(to_index, item)
        
        # Select the moved item
        self.staff_list.setCurrentItem(item)
        
        # Mark that there are unapplied changes
        self.has_unapplied_changes = True

        # Emit signal
        print(f"[DEBUG] ScoreSetupWidget emitting staff_reordered signal: {from_index}, {to_index}")
        self.staff_reordered.emit(from_index, to_index)

    def move_staff_down(self):
        """Move the selected staff down in the list, skipping complete sections"""
        print(f"[DEBUG] ScoreSetupWidget.move_staff_down called")
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return

        # Get the first selected item
        item = selected_items[0]
        current_index = self.staff_list.indexOfTopLevelItem(item)
        
        # Check if we can move down
        if current_index >= self.staff_list.topLevelItemCount() - 1:
            return
        
        # Get current section
        current_section = item.text(3)  # Section is in column 3
        
        # Find the target index - skip complete sections
        target_index = current_index + 1
        
        # If we're in a section, find the section boundary
        if current_section:
            # Find the end of the current section
            section_end = current_index
            while section_end < self.staff_list.topLevelItemCount() - 1:
                next_item = self.staff_list.topLevelItem(section_end + 1)
                if next_item.text(3) != current_section:
                    break
                section_end += 1
            
            # If we're at the end of the section, move to the next section's start
            if current_index == section_end:
                # Find the next section's start
                target_index = section_end + 1
                while target_index < self.staff_list.topLevelItemCount():
                    next_item = self.staff_list.topLevelItem(target_index)
                    if next_item.text(3) and next_item.text(3) != current_section:
                        # Found a different section, this is the start
                        break
                    target_index += 1
                else:
                    # We're inside a section, move to the next staff in the same section
                    target_index = current_index + 1

        # Ensure target index is valid
        if target_index >= self.staff_list.topLevelItemCount():
            target_index = self.staff_list.topLevelItemCount() - 1
        
        # Calculate indices
        from_index = current_index
        to_index = target_index
        
        # Move the item
        self.staff_list.takeTopLevelItem(from_index)
        self.staff_list.insertTopLevelItem(to_index, item)
        
        # Select the moved item
        self.staff_list.setCurrentItem(item)
        
        # Mark that there are unapplied changes
        self.has_unapplied_changes = True

        # Emit signal
        print(f"[DEBUG] ScoreSetupWidget emitting staff_reordered signal: {from_index}, {to_index}")
        self.staff_reordered.emit(from_index, to_index)

    def on_instrument_selected(self):
        """Handle instrument selection change"""
        selected_items = self.instrument_tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data["type"] not in ["plugin", "gm_instrument"]:
            return

        # Get the selected staff in the Added Instruments list
        selected_staff_items = self.staff_list.selectedItems()
        if not selected_staff_items:
            # No staff selected, nothing to replace
            return

        # Get the index of the selected staff
        staff_index = self.staff_list.indexOfTopLevelItem(selected_staff_items[0])

        # Get the current staff data to retain values
        current_staff_data = selected_staff_items[0].data(0, Qt.ItemDataRole.UserRole)
        current_staff_type = current_staff_data.get("staff_type", "single_staff")
        
        # Get the current display name (preserve the part name)
        current_display_name = selected_staff_items[0].text(0)

        # Determine clef based on staff type and display text
        staff_type_display = selected_staff_items[0].text(1)
        clef_display = selected_staff_items[0].text(2)
        clef = "treble"  # Default

        if staff_type_display == "Single Staff":
            if clef_display == "Bass":
                clef = "bass"
            elif clef_display == "Alto":
                clef = "alto"
            elif clef_display == "Percussion":
                clef = "percussion"
            else:
                clef = "treble"

        # Preserve any existing notation_settings
        notation_settings = current_staff_data.get("notation_settings", None)

        # Create new staff data, retaining existing staff type and section
        instrument_name = data["name"]
        staff_data = {
            "instrument_id": current_staff_data.get("instrument_id", "part"),  # PRESERVE original instrument_id
            "instrument_name": current_staff_data.get("instrument_name", "Part"),  # Retain original instrument name
            "instrument_abbr": current_staff_data.get("instrument_abbr", ""),  # Retain original abbreviation 
            "staff_type": current_staff_type,  # Retain existing staff type
            "clef": clef,
            "key": "C major / A minor (no sharps/flats)",
            "time_signature": "4/4",
            "section": current_staff_data.get("section", ""),  # Retain existing section
            "plugin": instrument_name  # Set the plugin to the instrument name
        }

        # Restore notation settings if they existed
        if notation_settings:
            staff_data["notation_settings"] = notation_settings
            print(f"Preserved notation settings when replacing staff with {instrument_name}")

        print(f"Replacing staff #{staff_index} with {instrument_name}")

        # Replace the staff item
        new_staff_item = QTreeWidgetItem()
        new_staff_item.setText(0, current_display_name)  # Keep the original display name
        new_staff_item.setText(1, staff_type_display)  # Keep the same staff type display
        new_staff_item.setText(2, clef_display)  # Keep the same clef display
        new_staff_item.setText(3, staff_data["section"])  # Retain section display
        new_staff_item.setText(4, instrument_name)  # Set Plugin/Instrument column
        new_staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

        # Replace the old staff item with the new one - add null check
        old_item = self.staff_list.takeTopLevelItem(staff_index)
        if old_item is None:
            print(f"ERROR: Could not take item at index {staff_index}")
            return

        self.staff_list.insertTopLevelItem(staff_index, new_staff_item)

        # Mark that there are unapplied changes
        self.has_unapplied_changes = True
        self.staff_removed.emit(staff_index)
        self.staff_added.emit(staff_data["instrument_id"], staff_data["staff_type"], staff_index)

        # Apply changes immediately to show updates in pink mode
        print(
            "SETUP WIDGET: Applying changes immediately to show instrument replacement in setup mode"
        )
        options = self.get_setup_options()

        # Set a flag to force rendering in setup mode with 5 measures
        options["force_setup_mode"] = True
        options["measures_per_system"] = 5  # Force 5 measures for setup mode

        # DO NOT call self.apply_changes_immediate(options) directly!
        # Let the dialog's signal handlers handle immediate rendering
        # The staff_added and staff_removed signals will trigger the dialog's handlers

        # Clear selections in both lists
        self.instrument_tree.clearSelection()
        self.staff_list.clearSelection()

        print(f"Replaced staff with {instrument_name}")

    def on_staff_type_changed(self, staff_type):
        """Handle staff type change"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)

            # Preserve any existing notation_settings
            notation_settings = staff_data.get("notation_settings", None)

            # Store the formatted value in the data
            staff_data["staff_type"] = staff_type.lower().replace(" ", "_")

            # Update clef based on staff type
            if staff_type == "Single Staff":
                staff_data["clef"] = "treble"
            elif staff_type == "Grand Staff":
                staff_data["clef"] = "bass"

            # Restore notation settings if they existed
            if notation_settings:
                staff_data["notation_settings"] = notation_settings

            # Update the display - use the original staff_type with spaces
            item.setText(1, staff_type)  # Update the Staff Type column
            item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

            # Mark that there are unapplied changes
            self.has_unapplied_changes = True
            self.staff_options_changed.emit(self.staff_list.indexOfTopLevelItem(item), staff_data)

        # Apply changes immediately to show updates in pink mode
        print("SETUP WIDGET: Applying changes immediately to show staff type changes in setup mode")
        options = self.get_setup_options()

        # Set a flag to force rendering in setup mode with 5 measures
        options["force_setup_mode"] = True
        options["measures_per_system"] = 5  # Force 5 measures for setup mode

        # DO NOT call self.apply_changes_immediate(options) directly!
        # Let the dialog's signal handlers handle immediate rendering
        # The staff_options_changed signal will trigger the dialog's handler

        print(f"Changed staff type to {staff_type}")

    def is_selection_contiguous(self, selected_items):
        """Check if the selected items form a contiguous group in the staff list"""
        if not selected_items:
            return False
        
        # Get indices of selected items
        indices = []
        for item in selected_items:
            index = self.staff_list.indexOfTopLevelItem(item)
            indices.append(index)
        
        # Sort indices
        indices.sort()
        
        # Check if indices are consecutive
        for i in range(len(indices) - 1):
            if indices[i+1] - indices[i] != 1:
                return False
        
        return True
    
    def get_contiguous_groups(self, selected_items):
        """Split selected items into contiguous groups"""
        if not selected_items:
            return []
        
        # Get indices of selected items
        item_indices = []
        for item in selected_items:
            index = self.staff_list.indexOfTopLevelItem(item)
            item_indices.append((index, item))
        
        # Sort by index
        item_indices.sort(key=lambda x: x[0])
        
        # Group contiguous items
        groups = []
        current_group = [item_indices[0]]
        
        for i in range(1, len(item_indices)):
            current_index, current_item = item_indices[i]
            prev_index, prev_item = item_indices[i-1]
            
            if current_index - prev_index == 1:
                # Contiguous, add to current group
                current_group.append(item_indices[i])
            else:
                # Not contiguous, start new group
                groups.append([item[1] for item in current_group])  # Extract items only
                current_group = [item_indices[i]]
        
        # Add the last group
        groups.append([item[1] for item in current_group])
        
        return groups

    def on_new_section(self):
        """Handle new section creation with contiguous group validation"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select staves to create a section.")
            return

        # Check if selection is contiguous
        if not self.is_selection_contiguous(selected_items):
            # If not contiguous, offer to create multiple sections or show warning
            contiguous_groups = self.get_contiguous_groups(selected_items)
            
            if len(contiguous_groups) > 1:
                msg = QMessageBox(self)
                msg.setWindowTitle("Non-contiguous Selection")
                msg.setText(f"You have selected staves that are not adjacent.\n\n"
                           f"Found {len(contiguous_groups)} separate contiguous groups:\n"
                           + "\n".join([f"Group {i+1}: {len(group)} staves" 
                                       for i, group in enumerate(contiguous_groups)]))
                msg.setInformativeText("Sections can only be created from contiguous (adjacent) staves.\n\n"
                                     "Would you like to:")
                
                create_multiple_btn = msg.addButton("Create Multiple Sections", QMessageBox.ButtonRole.AcceptRole)
                select_first_btn = msg.addButton("Use First Group Only", QMessageBox.ButtonRole.ActionRole)
                cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg.setDefaultButton(create_multiple_btn)
                msg.exec()
                
                if msg.clickedButton() == create_multiple_btn:
                    # Create multiple sections from contiguous groups
                    for i, group in enumerate(contiguous_groups):
                        self._create_section_from_group(group, f"Section {i+1}")
                    return
                elif msg.clickedButton() == select_first_btn:
                    # Use only the first contiguous group
                    selected_items = contiguous_groups[0]
                else:
                    # Cancel
                    return
            else:
                QMessageBox.warning(self, "Invalid Selection", 
                                  "Please select contiguous (adjacent) staves to create a section.")
                return

        # Proceed with section creation for contiguous selection
        self._create_section_from_group(selected_items)

    def _create_section_from_group(self, selected_items, default_name=None):
        """Create a section from a group of contiguous staves"""
        # Create and show section name input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("New Section")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        # Add label and text input
        label = QLabel("Enter section name:")
        section_name_edit = QLineEdit()
        if default_name:
            section_name_edit.setText(default_name)
        layout.addWidget(label)
        layout.addWidget(section_name_edit)

        # Add info about the staves being grouped
        info_label = QLabel(f"Creating section with {len(selected_items)} contiguous staves:\n" +
                           "\n".join([f"• {item.text(0)}" for item in selected_items]))
        info_label.setStyleSheet("color: #666; font-size: 10px; margin: 10px 0;")
        layout.addWidget(info_label)

        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            section_name = section_name_edit.text().strip()
            if section_name:  # Only proceed if a name was entered
                # Update selected items with the new section
                for item in selected_items:
                    # Get the existing staff data to preserve all attributes
                    staff_data = item.data(0, Qt.ItemDataRole.UserRole)

                    # Important! Preserve ALL existing data, especially staff_type and clef
                    # Just update the section property
                    staff_data["section"] = section_name

                    # Keep track of existing staff type (internal format) and clef
                    staff_type = staff_data.get("staff_type", "")
                    clef = staff_data.get("clef", "")
                    
                    print(
                        f"NEW SECTION: Preserving staff type '{staff_type}' and clef '{clef}' for {item.text(0)} in section '{section_name}'"
                    )

                    # Update UI display - only change the section column
                    item.setText(3, section_name)  # Update the Section column

                    # Keep all other data intact
                    item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                    # Mark that there are unapplied changes
                    self.has_unapplied_changes = True
                    self.staff_options_changed.emit(
                        self.staff_list.indexOfTopLevelItem(item), staff_data
                    )

                # Update the section dialog button states
                if hasattr(self, "section_dialog") and self.section_dialog:
                    self.section_dialog.update_button_states()

                # The staff_options_changed signals will trigger the dialog's signal handlers
                # which will apply changes immediately

                print(
                    f"Created section '{section_name}' with {len(selected_items)} contiguous staves"
                )

    def on_add_to_section(self):
        """Handle adding to section with contiguous group validation"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select staves to add to a section.")
            return

        # Check if selection is contiguous
        if not self.is_selection_contiguous(selected_items):
            contiguous_groups = self.get_contiguous_groups(selected_items)
            
            if len(contiguous_groups) > 1:
                msg = QMessageBox(self)
                msg.setWindowTitle("Non-contiguous Selection")
                msg.setText(f"You have selected staves that are not adjacent.\n\n"
                           f"Found {len(contiguous_groups)} separate contiguous groups:\n"
                           + "\n".join([f"Group {i+1}: {len(group)} staves" 
                                       for i, group in enumerate(contiguous_groups)]))
                msg.setInformativeText("Only contiguous (adjacent) staves can be added to sections.\n\n"
                                     "Would you like to:")
                
                use_first_btn = msg.addButton("Use First Group Only", QMessageBox.ButtonRole.AcceptRole)
                cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
                
                msg.setDefaultButton(use_first_btn)
                msg.exec()
                
                if msg.clickedButton() == use_first_btn:
                    # Use only the first contiguous group
                    selected_items = contiguous_groups[0]
                else:
                    # Cancel
                    return
            else:
                QMessageBox.warning(self, "Invalid Selection", 
                                  "Please select contiguous (adjacent) staves to add to a section.")
            return

        # Get existing sections
        sections = self.get_unique_sections()
        if not sections:
            # If no sections exist, create a new one
            self.on_new_section()
            return

        # Create and show section selection dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Section")
        layout = QVBoxLayout(dialog)
        
        # Add info about the staves being added
        info_label = QLabel(f"Adding {len(selected_items)} contiguous staves:\n" +
                           "\n".join([f"• {item.text(0)}" for item in selected_items]))
        info_label.setStyleSheet("color: #666; font-size: 10px; margin: 10px 0;")
        layout.addWidget(info_label)
        
        combo = QComboBox()
        combo.addItems(sections)
        layout.addWidget(combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            section_name = combo.currentText()
            
            # Update selected items with the selected section
            for item in selected_items:
                # Get the existing staff data to preserve all attributes
                staff_data = item.data(0, Qt.ItemDataRole.UserRole)

                # Important! Preserve ALL existing data, especially staff_type and clef
                # Just update the section property
                staff_data["section"] = section_name

                # Keep track of existing staff type (internal format) and clef
                staff_type = staff_data.get("staff_type", "")
                clef = staff_data.get("clef", "")
                
                print(
                    f"ADD TO SECTION: Preserving staff type '{staff_type}' and clef '{clef}' for {item.text(0)} in section '{section_name}'"
                )

                # Update UI display - only change the section column
                item.setText(3, section_name)  # Update the Section column

                # Keep all other data intact
                item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                # Mark that there are unapplied changes
                self.has_unapplied_changes = True
                self.staff_options_changed.emit(
                    self.staff_list.indexOfTopLevelItem(item), staff_data
                )

            # The staff_options_changed signals will trigger the dialog's signal handlers
            # which will apply changes immediately

            print(
                f"Added {len(selected_items)} contiguous staves to section '{section_name}' while preserving all staff attributes"
            )

    def on_remove_from_section(self):
        """Handle removing from section"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return

        # Remove section from selected items
        for item in selected_items:
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            staff_data["section"] = ""
            item.setText(3, "")  # Clear the Section column
            item.setData(0, Qt.ItemDataRole.UserRole, staff_data)
            
            # Mark that there are unapplied changes
            self.has_unapplied_changes = True
            self.staff_options_changed.emit(self.staff_list.indexOfTopLevelItem(item), staff_data)

        # Update the section dialog button states
        if hasattr(self, "section_dialog") and self.section_dialog:
            self.section_dialog.update_button_states()

        # The staff_options_changed signals will trigger the dialog's signal handlers
        # which will apply changes immediately

        print("Removed staff(s) from section")

    def get_unique_sections(self):
        """Get list of unique sections"""
        sections = set()
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            if staff_data.get("section"):
                sections.add(staff_data["section"])
        return sorted(list(sections))

    def on_staff_selection_changed(self):
        """Handle staff selection change with contiguous selection feedback and section behavior"""
        # Prevent recursion when we're programmatically updating selection
        if self._updating_selection:
            return
            
        selected_items = self.staff_list.selectedItems()
        has_selection = bool(selected_items)

        if not has_selection:
            # Clear any selection indicators and status label
            self._clear_selection_indicators()
            if hasattr(self, 'status_label'):
                self.status_label.setText("")
            # DON'T reset lock checkbox - let user control it
            return
        
        # Check if any selected staff belongs to a section
        section_staves = {}  # Map section names to lists of staves in that section
        section_members = []  # All staves that belong to any section
        
        # First pass: identify all section memberships
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            section = item.text(3)  # Section column
            if section:  # If this staff belongs to a section
                if section not in section_staves:
                    section_staves[section] = []
                section_staves[section].append(item)
                section_members.append(item)
        
        # Check if any selected item is a section member
        selected_section_members = [item for item in selected_items if item in section_members]
        
        if selected_section_members:
            # Auto-select entire sections when any member is selected
            sections_to_select = set()
            for item in selected_section_members:
                section_name = item.text(3)
                if section_name:
                    sections_to_select.add(section_name)
            
            # Build the complete selection including all section members
            complete_selection = []
            section_info = []
            
            for section_name in sections_to_select:
                section_staves_list = section_staves[section_name]
                complete_selection.extend(section_staves_list)
                section_info.append(f"Section '{section_name}' ({len(section_staves_list)} staves)")
            
            # Add any non-section selected items
            for item in selected_items:
                if item not in section_members and item not in complete_selection:
                    complete_selection.append(item)
            
            # Update selection to include all section members (prevent recursion)
            if len(complete_selection) != len(selected_items) or set(complete_selection) != set(selected_items):
                # Disconnect signal to prevent recursion
                self._updating_selection = True
                self.staff_list.itemSelectionChanged.disconnect()
                try:
                    self.staff_list.clearSelection()
                    for item in complete_selection:
                        item.setSelected(True)
                    selected_items = complete_selection
                finally:
                    # Reconnect signal
                    self.staff_list.itemSelectionChanged.connect(self.on_staff_selection_changed)
                    self._updating_selection = False
            
            # Show lock checkbox as checked (sections behave as locked selections when selected)
            if hasattr(self, 'lock_selection'):
                self.lock_selection.setChecked(True)
            
            # Update status label for section behavior
            if hasattr(self, 'status_label'):
                if len(sections_to_select) == 1:
                    section_name = list(sections_to_select)[0]
                    section_size = len(section_staves[section_name])
                    self.status_label.setText(f"✓ Section '{section_name}' selected ({section_size} staves) - Locked Movement")
                    self.status_label.setStyleSheet("color: blue; font-size: 10px; padding: 2px;")
                else:
                    self.status_label.setText(f"✓ Multiple sections selected - Locked Movement")
                    self.status_label.setStyleSheet("color: blue; font-size: 10px; padding: 2px;")
            
            return
        
        # Handle single selection (no sections involved)
        if len(selected_items) == 1:
            # Clear indicators and status label for single selection
            self._clear_selection_indicators()
            if hasattr(self, 'status_label'):
                self.status_label.setText("")
            # DON'T reset lock checkbox - let user control it
            return
        
        # Handle multiple selection (no sections involved) - original contiguous logic
        if len(selected_items) > 1:
            is_contiguous = self.is_selection_contiguous(selected_items)
            contiguous_groups = self.get_contiguous_groups(selected_items)
            
            # Update selection style based on contiguity
            self._update_selection_indicators(selected_items, is_contiguous, contiguous_groups)
            
            # Update status label
            if hasattr(self, 'status_label'):
                if is_contiguous:
                    self.status_label.setText(f"✓ {len(selected_items)} contiguous staves selected (can create section)")
                    self.status_label.setStyleSheet("color: green; font-size: 10px; padding: 2px;")
                else:
                    self.status_label.setText(f"⚠ {len(contiguous_groups)} separate groups selected (non-contiguous)")
                    self.status_label.setStyleSheet("color: orange; font-size: 10px; padding: 2px;")
            
            # Don't auto-check lock for regular multiple selections - let user control it
            # The lock state should remain as the user set it

    def _update_selection_indicators(self, selected_items, is_contiguous, contiguous_groups):
        """Update visual indicators for selection contiguity"""
        # First clear all indicators
        self._clear_selection_indicators()
        
        if is_contiguous:
            # All selected items are contiguous - use standard selection color
            # Don't modify the background, let Qt handle standard selection
            pass
        else:
            # Multiple contiguous groups - color code them differently with very subtle colors
            colors = ["#FFFACD", "#F0F8FF", "#F5FFFA", "#FFFAF0", "#F8F8FF"]  # Very light subtle colors
            
            for group_idx, group in enumerate(contiguous_groups):
                color = colors[group_idx % len(colors)]
                for item in group:
                    # Only set background for the first column to be less intrusive
                    item.setBackground(0, QColor(color))

    def _clear_selection_indicators(self):
        """Clear all custom selection indicators"""
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            for col in range(self.staff_list.columnCount()):
                # Use transparent color instead of black
                item.setBackground(col, QColor(255, 255, 255, 0))  # Transparent white

    def on_staff_changed(self, item):
        """Handle staff change"""
        # Save state before making changes for undo/redo functionality
        if hasattr(self, 'parent_view') and hasattr(self.parent_view, 'document') and hasattr(self.parent_view.document, 'save_state'):
            self.parent_view.document._undo_context = "Change Staff Name"
            self.parent_view.document.save_state("Change Staff Name")
            print("UNDO: Saved state before changing staff name")
            
        # Handle name changes (column 0)
        # Get the staff data
        staff_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Update the staff data with the new name
        if staff_data:
            # Store the new name as custom_name to preserve original instrument name
            new_name = item.text(0)
            staff_data["custom_name"] = new_name
            item.setData(0, Qt.ItemDataRole.UserRole, staff_data)
            print(f"STAFF ATTRIBUTES: Updated staff name to '{new_name}'")

        # Mark that there are unapplied changes
        self.has_unapplied_changes = True
        if staff_data:
            # Emit signal to dialog handler
            index = self.staff_list.indexOfTopLevelItem(item)
            print(f"[DEBUG] ScoreSetupWidget emitting staff_options_changed signal: {index}, {staff_data}")
            self.staff_options_changed.emit(index, staff_data)
            
        # The staff_options_changed signal will trigger the dialog's on_staff_options_changed method

    def on_ok_clicked(self):
        """Handle OK button click"""
        # IMPORTANT: Don't apply changes automatically
        # Just emit the setup_completed signal - actual applying of changes
        # should only happen if Apply button is clicked
        print("OK clicked - signaling setup completion but NOT applying changes")
        self.setup_completed.emit()

    def filter_instruments(self, text):
        """Filter instruments based on search text"""
        # Get current selection if any
        current_item = self.instrument_tree.currentItem()
        selected_text = current_item.text(0) if current_item else None

        # Show/hide items based on search text
        for i in range(self.instrument_tree.topLevelItemCount()):
            item = self.instrument_tree.topLevelItem(i)
            if text.lower() in item.text(0).lower() or not text:
                item.setHidden(False)
        else:
            item.setHidden(True)

        # Restore selection if possible
        if selected_text:
            items = self.instrument_tree.findItems(selected_text, Qt.MatchFlag.MatchExactly)
            if items:
                self.instrument_tree.setCurrentItem(items[0])

    def apply_changes(self):
        """Apply all changes"""
        # Get all the latest settings and staves
        options = self.get_setup_options()
        options["has_unapplied_changes"] = False

        # Reset the has_unapplied_changes flag
        self.has_unapplied_changes = False

        print("SETUP WIDGET: Applying changes with the following staves:")
        if "added_staves" in options:
            for staff in options["added_staves"]:
                print(
                    f"  - {staff.get('instrument_name', 'Unknown')} with clef={staff.get('clef', 'treble')}"
                )

        # Debug section map
        if "section_map" in options:
            print(f"SETUP WIDGET: Section map contains {len(options['section_map'])} entries:")
            for instr, section in options["section_map"].items():
                print(f"  - {instr}: {section}")

        # Mark the options to force immediate application
        options["immediate_apply"] = True
        options["preserve_clefs"] = True  # Explicitly preserve clefs

        # Try multiple methods to apply changes to ensure they're all updated

        # 1. Apply to parent dialog if applicable
        if hasattr(self.parent(), "apply_setup_options"):
            print("SETUP WIDGET: Applying changes to parent dialog")
            self.parent().apply_setup_options(options)

        # 2. Apply to document through parent.staff_view
        if hasattr(self.parent(), "parent") and self.parent().parent():
            parent_window = self.parent().parent()
            if hasattr(parent_window, "staff_view"):
                print("SETUP WIDGET: Applying changes to parent window's staff_view")

                # Force a complete refresh to display the new structure
                parent_window.staff_view.apply_setup_options(options)
                parent_window.staff_view.dialog_settings = options

                # Save directly to document structure
                if hasattr(parent_window.staff_view, "document"):
                    doc = parent_window.staff_view.document

                    # Update section map in document
                    if not hasattr(doc, "section_map"):
                        doc.section_map = {}
                    if "section_map" in options:
                        doc.section_map.update(options["section_map"])
                        print(
                            f"SETUP WIDGET: Updated document.section_map with {len(options['section_map'])} entries"
                        )

                    # Ensure document layout is refreshed
                    if hasattr(doc, "apply_setup_options"):
                        print("SETUP WIDGET: Directly applying options to document")
                        doc.apply_setup_options(options)

                    # Force layout update
                    parent_window.staff_view.update()
                    print(
                        "SETUP WIDGET: Applied changes to document via parent window's staff_view"
                    )

        # 3. Apply to dialog.parent_view if available
        if hasattr(self.parent(), "parent_view") and self.parent().parent_view:
            if hasattr(self.parent().parent_view, "apply_setup_options"):
                print("SETUP WIDGET: Applying changes to parent_view")

                # Force a complete refresh
                self.parent().parent_view.apply_setup_options(options)
                self.parent().parent_view.dialog_settings = options

                # Save directly to document structure
                if hasattr(self.parent().parent_view, "document"):
                    doc = self.parent().parent_view.document

                    # Update section map in document
                    if not hasattr(doc, "section_map"):
                        doc.section_map = {}
                    if "section_map" in options:
                        doc.section_map.update(options["section_map"])
                        print(
                            f"SETUP WIDGET: Updated document.section_map with {len(options['section_map'])} entries"
                        )

                    # Ensure document layout is refreshed
                    if hasattr(doc, "apply_setup_options"):
                        print("SETUP WIDGET: Directly applying options to document")
                        doc.apply_setup_options(options)

                    # Force layout update
                    self.parent().parent_view.update()
                    print("SETUP WIDGET: Applied changes to document via parent_view")

        print("SETUP WIDGET: Completed applying all changes")

    def get_setup_options(self):
        """Get the current setup options as a dictionary"""
        # List to store staff data
        staves = []

        # Iterate through all items in the staff list
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)

            # Get instrument name and ID
            instrument_name = item.text(0)

            # Get staff data from item
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)

            # Get staff type from UI
            staff_type_display = item.text(1)

            # Get clef from UI
            clef_display = item.text(2)

            # Convert staff type display to internal format if needed
            if staff_type_display == "Grand Staff":
                staff_type = "grand_staff"
            else:
                staff_type = "single_staff"

            # CRITICAL FIX: Prioritize stored clef data over UI display
            # This preserves original clefs when creating sections
            if staff_data and "clef" in staff_data and staff_data["clef"]:
                # Use the stored clef data (preserves original clef)
                clef = staff_data["clef"]
                print(f"PRESERVE_CLEF: Using stored clef '{clef}' for {instrument_name} instead of display '{clef_display}'")
            else:
                # Fall back to converting UI display to internal format
                if clef_display == "Bass":
                    clef = "bass"
                elif clef_display == "Alto":
                    clef = "alto"
                elif clef_display == "Percussion":
                    clef = "percussion"
                elif clef_display == "Treble/Bass":
                    clef = "treble"  # For grand staff
                else:
                    clef = "treble"  # Default
                print(f"FALLBACK_CLEF: Using UI display clef '{clef}' for {instrument_name}")

            # Get or generate instrument ID
            if staff_data and "instrument_id" in staff_data:
                instrument_id = staff_data["instrument_id"]
            else:
                instrument_id = instrument_name.lower().replace(" ", "_")

            # Create staff entry
            staff_entry = {
                "instrument_id": instrument_id,
                "instrument_name": instrument_name,
                "staff_type": staff_type,
                "clef": clef,
                "staff_type_display": staff_type_display,
                "section": item.text(3),
            }

            # Update staff data based on UI values
            if staff_data:
                # Make a copy to avoid modifying the original data
                staff_data_copy = staff_data.copy()

                # Update with current UI values, but preserve stored clef
                staff_data_copy["staff_type"] = staff_type
                staff_data_copy["clef"] = clef  # Use the clef we determined above (preserves stored data)
                staff_data_copy["section"] = item.text(3)
                # Add plugin info from UI
                plugin_text = item.text(4)
                if plugin_text:
                    staff_data_copy["plugin"] = plugin_text

                # CRITICAL: Preserve custom_name and custom_abbr if they exist
                if "custom_name" in staff_data:
                    staff_data_copy["custom_name"] = staff_data["custom_name"]
                    print(f"GET_OPTIONS: Preserving custom_name '{staff_data['custom_name']}' for {instrument_name}")
                if "custom_abbr" in staff_data:
                    staff_data_copy["custom_abbr"] = staff_data["custom_abbr"]
                    print(f"GET_OPTIONS: Preserving custom_abbr '{staff_data['custom_abbr']}' for {instrument_name}")

                # Add staff data to the entry
                staff_entry["staff_data"] = staff_data_copy

            # Add to staves list
            staves.append(staff_entry)

        # Create section map
        section_map = {}
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            if staff_data and "instrument_id" in staff_data:
                section = item.text(3)
                if section:
                    section_map[staff_data["instrument_id"]] = section

        # Create clef map - CRITICAL FIX: Prioritize stored clef data
        clef_map = {}
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            if staff_data and "instrument_id" in staff_data:
                clef_display = item.text(2)

                # CRITICAL FIX: Use stored clef data if available
                if "clef" in staff_data and staff_data["clef"]:
                    clef = staff_data["clef"]
                    print(f"CLEF_MAP: Using stored clef '{clef}' for {staff_data['instrument_id']}")
                else:
                    # Fall back to converting display to internal format
                    if clef_display == "Bass":
                        clef = "bass"
                    elif clef_display == "Alto":
                        clef = "alto"
                    elif clef_display == "Percussion":
                        clef = "percussion"
                    elif clef_display == "Treble/Bass":
                        clef = "treble"  # For grand staff
                    else:
                        clef = "treble"  # Default
                    print(f"CLEF_MAP: Using display clef '{clef}' for {staff_data['instrument_id']}")

                clef_map[staff_data["instrument_id"]] = clef

        # Create staff type map
        staff_type_map = {}
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            if staff_data and "instrument_id" in staff_data:
                staff_type_display = item.text(1)
                if staff_type_display == "Grand Staff":
                    staff_type = "grand_staff"
                else:
                    staff_type = "single_staff"
                staff_type_map[staff_data["instrument_id"]] = staff_type

        # Create plugin map
        plugin_map = {}
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            staff_data = item.data(0, Qt.ItemDataRole.UserRole)
            if staff_data and "instrument_id" in staff_data:
                plugin = item.text(4) if item.text(4) else "Default"  # Get plugin from column 4
                plugin_map[staff_data["instrument_id"]] = plugin

        # Create section display order map
        section_display_order = {}
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            section = item.text(3)  # Section is in column 3
            if section and section not in section_display_order:
                section_display_order[section] = i
                print(f"GET_SETUP_OPTIONS: Section '{section}' first appears at index {i}")

        # Return options dictionary
        return {
            "added_staves": staves,
            "section_map": section_map,
            "clef_map": clef_map,
            "staff_type_map": staff_type_map,
            "plugin_map": plugin_map,
            "section_display_order": section_display_order,
            "has_unapplied_changes": self.has_unapplied_changes,
            "staff_spacing": self.layout_settings.get("staff_spacing", 40),
            "system_spacing": self.layout_settings.get("system_spacing", 60),
            "measures_per_system": self.layout_settings.get("measures_per_system", 4),
            "preserve_staff_types": True,
            "preserve_clefs": True,
        }

    def show_layout_dialog(self):
        """Show the layout settings dialog"""
        dialog = LayoutDialog(self)
        dialog.set_settings(self.layout_settings)

        if dialog.exec():
            self.layout_settings = dialog.get_settings()
            self.has_unapplied_changes = True
            if hasattr(self.parent(), "on_layout_changed"):
                self.parent().on_layout_changed()

    def show_staff_attributes_dialog(self):
        """Show a dialog for editing staff attributes including type and section"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            # ENHANCEMENT: Show user feedback if no staves are selected
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar.showMessage(
                    "Please select a staff to edit attributes", 3000
                )
            return

        # Get the first selected item to initialize the dialog
        first_item = selected_items[0]
        staff_data = first_item.data(0, Qt.ItemDataRole.UserRole)

        # Create and show a dialog with both staff type and section management
        dialog = QDialog(self)
        dialog.setWindowTitle("Staff Attributes")
        dialog.setModal(True)
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(300)

        layout = QVBoxLayout(dialog)

        # Create tab widget for the two types of attributes
        tabs = QTabWidget()

        # Staff Name tab (NEW)
        staff_name_tab = QWidget()
        staff_name_layout = QVBoxLayout(staff_name_tab)

        # Original instrument name display (non-editable)
        instrument_name = staff_data.get("instrument_name", "Part")
        staff_name_layout.addWidget(QLabel(f"Original Instrument: {instrument_name}"))

        # Custom Staff Name
        staff_name_layout.addWidget(QLabel("Custom Staff Name:"))
        custom_name_edit = QLineEdit()
        # Set current custom name if it exists
        if "custom_name" in staff_data:
            custom_name_edit.setText(staff_data["custom_name"])
        else:
            custom_name_edit.setPlaceholderText(f"Default: {instrument_name}")
        staff_name_layout.addWidget(custom_name_edit)

        # Custom Staff Abbreviation
        staff_name_layout.addWidget(QLabel("Custom Staff Abbreviation:"))
        custom_abbr_edit = QLineEdit()
        default_abbr = staff_data.get("instrument_abbr", instrument_name[:3].upper())
        # Set current custom abbreviation if it exists
        if "custom_abbr" in staff_data:
            custom_abbr_edit.setText(staff_data["custom_abbr"])
        else:
            custom_abbr_edit.setPlaceholderText(f"Default: {default_abbr}")
        staff_name_layout.addWidget(custom_abbr_edit)

        # Add a note about overriding
        note_label = QLabel(
            "Note: These custom values will override the defaults on the score, but won't change the instrument itself."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("font-style: italic; color: #666;")
        staff_name_layout.addWidget(note_label)

        staff_name_layout.addStretch()
        tabs.addTab(staff_name_tab, "Staff Name")

        # Staff Type tab
        staff_type_tab = QWidget()
        staff_type_layout = QVBoxLayout(staff_type_tab)

        staff_type_layout.addWidget(QLabel("Select staff type:"))
        staff_type_combo = QComboBox()
        staff_type_combo.addItems(["Single Staff", "Grand Staff"])

        # Get the current display type from the UI
        current_display_type = first_item.text(1)
        current_clef_display = first_item.text(2)

        index = staff_type_combo.findText(current_display_type)
        if index >= 0:
            staff_type_combo.setCurrentIndex(index)

        staff_type_layout.addWidget(staff_type_combo)

        # Add clef selection
        staff_type_layout.addWidget(QLabel("Select clef:"))
        clef_combo = QComboBox()
        if current_display_type == "Grand Staff":
            clef_combo.addItem("Treble/Bass")
            clef_combo.setEnabled(False)  # Grand staff always has treble/bass
        else:
            clef_combo.addItems(["Treble", "Bass", "Alto", "Percussion"])
            # Set current clef
            index = clef_combo.findText(current_clef_display)
            if index >= 0:
                clef_combo.setCurrentIndex(index)
            clef_combo.setEnabled(True)

        # Update clef combo when staff type changes
        def on_staff_type_changed(text):
            if text == "Grand Staff":
                clef_combo.clear()
                clef_combo.addItem("Treble/Bass")
                clef_combo.setEnabled(False)
            else:
                clef_combo.clear()
                clef_combo.addItems(["Treble", "Bass", "Alto", "Percussion"])
                clef_combo.setEnabled(True)

        staff_type_combo.currentTextChanged.connect(on_staff_type_changed)

        staff_type_layout.addWidget(clef_combo)
        staff_type_layout.addStretch()

        tabs.addTab(staff_type_tab, "Staff Type")

        # Section tab
        section_tab = QWidget()
        section_layout = QVBoxLayout(section_tab)

        section_layout.addWidget(QLabel("Current section:"))
        section_combo = QComboBox()
        section_combo.setEditable(True)

        # Add empty option and existing sections
        section_combo.addItem("")
        sections = self.get_unique_sections()
        if sections:
            section_combo.addItems(sections)

        # Set current section
        current_section = staff_data.get("section", "")
        if current_section:
            index = section_combo.findText(current_section)
            if index >= 0:
                section_combo.setCurrentIndex(index)
            else:
                section_combo.setEditText(current_section)

        section_layout.addWidget(section_combo)

        # Add buttons for section management
        section_btn_layout = QHBoxLayout()
        new_section_btn = QPushButton("New Section")
        remove_section_btn = QPushButton("Remove from Section")

        section_btn_layout.addWidget(new_section_btn)
        section_btn_layout.addWidget(remove_section_btn)
        section_layout.addLayout(section_btn_layout)
        section_layout.addStretch()

        tabs.addTab(section_tab, "Section")

        # Instrument tab (NEW)
        instrument_tab = QWidget()
        instrument_layout = QVBoxLayout(instrument_tab)

        instrument_layout.addWidget(QLabel("Select instrument sound:"))

        # GM instrument list
        instrument_combo = QComboBox()

        # Add General MIDI instrument categories
        instrument_combo.addItem("Default")  # Default option

        # Piano Family (1-8)
        instrument_combo.addItem("Acoustic Grand Piano")
        instrument_combo.addItem("Bright Acoustic Piano")
        instrument_combo.addItem("Electric Grand Piano")
        instrument_combo.addItem("Honky-tonk Piano")
        instrument_combo.addItem("Electric Piano 1")
        instrument_combo.addItem("Electric Piano 2")
        instrument_combo.addItem("Harpsichord")
        instrument_combo.addItem("Clavinet")

        # Chromatic Percussion (9-16)
        instrument_combo.addItem("Celesta")
        instrument_combo.addItem("Glockenspiel")
        instrument_combo.addItem("Music Box")
        instrument_combo.addItem("Vibraphone")
        instrument_combo.addItem("Marimba")
        instrument_combo.addItem("Xylophone")
        instrument_combo.addItem("Tubular Bells")
        instrument_combo.addItem("Dulcimer")

        # Organ Family (17-24)
        instrument_combo.addItem("Drawbar Organ")
        instrument_combo.addItem("Percussive Organ")
        instrument_combo.addItem("Rock Organ")
        instrument_combo.addItem("Church Organ")
        instrument_combo.addItem("Reed Organ")
        instrument_combo.addItem("Accordion")
        instrument_combo.addItem("Harmonica")
        instrument_combo.addItem("Tango Accordion")

        # Guitar Family (25-32)
        instrument_combo.addItem("Acoustic Guitar (nylon)")
        instrument_combo.addItem("Acoustic Guitar (steel)")
        instrument_combo.addItem("Electric Guitar (jazz)")
        instrument_combo.addItem("Electric Guitar (clean)")
        instrument_combo.addItem("Electric Guitar (muted)")
        instrument_combo.addItem("Overdriven Guitar")
        instrument_combo.addItem("Distortion Guitar")
        instrument_combo.addItem("Guitar harmonics")

        # Bass Family (33-40)
        instrument_combo.addItem("Acoustic Bass")
        instrument_combo.addItem("Electric Bass (finger)")
        instrument_combo.addItem("Electric Bass (pick)")
        instrument_combo.addItem("Fretless Bass")
        instrument_combo.addItem("Slap Bass 1")
        instrument_combo.addItem("Slap Bass 2")
        instrument_combo.addItem("Synth Bass 1")
        instrument_combo.addItem("Synth Bass 2")

        # Strings Family (41-48)
        instrument_combo.addItem("Violin")
        instrument_combo.addItem("Viola")
        instrument_combo.addItem("Cello")
        instrument_combo.addItem("Contrabass")
        instrument_combo.addItem("Tremolo Strings")
        instrument_combo.addItem("Pizzicato Strings")
        instrument_combo.addItem("Orchestral Harp")
        instrument_combo.addItem("Timpani")

        # Ensemble Family (49-56)
        instrument_combo.addItem("String Ensemble 1")
        instrument_combo.addItem("String Ensemble 2")
        instrument_combo.addItem("Synth Strings 1")
        instrument_combo.addItem("Synth Strings 2")
        instrument_combo.addItem("Choir Aahs")
        instrument_combo.addItem("Voice Oohs")
        instrument_combo.addItem("Synth Voice")
        instrument_combo.addItem("Orchestra Hit")

        # Brass Family (57-64)
        instrument_combo.addItem("Trumpet")
        instrument_combo.addItem("Trombone")
        instrument_combo.addItem("Tuba")
        instrument_combo.addItem("Muted Trumpet")
        instrument_combo.addItem("French Horn")
        instrument_combo.addItem("Brass Section")
        instrument_combo.addItem("Synth Brass 1")
        instrument_combo.addItem("Synth Brass 2")

        # Reed Family (65-72)
        instrument_combo.addItem("Soprano Sax")
        instrument_combo.addItem("Alto Sax")
        instrument_combo.addItem("Tenor Sax")
        instrument_combo.addItem("Baritone Sax")
        instrument_combo.addItem("Oboe")
        instrument_combo.addItem("English Horn")
        instrument_combo.addItem("Bassoon")
        instrument_combo.addItem("Clarinet")

        # Pipe Family (73-80)
        instrument_combo.addItem("Piccolo")
        instrument_combo.addItem("Flute")
        instrument_combo.addItem("Recorder")
        instrument_combo.addItem("Pan Flute")
        instrument_combo.addItem("Blown Bottle")
        instrument_combo.addItem("Shakuhachi")
        instrument_combo.addItem("Whistle")
        instrument_combo.addItem("Ocarina")

        # Synth Lead Family (81-88)
        instrument_combo.addItem("Lead 1 (square)")
        instrument_combo.addItem("Lead 2 (sawtooth)")
        instrument_combo.addItem("Lead 3 (calliope)")
        instrument_combo.addItem("Lead 4 (chiff)")
        instrument_combo.addItem("Lead 5 (charang)")
        instrument_combo.addItem("Lead 6 (voice)")
        instrument_combo.addItem("Lead 7 (fifths)")
        instrument_combo.addItem("Lead 8 (bass + lead)")

        # Synth Pad Family (89-96)
        instrument_combo.addItem("Pad 1 (new age)")
        instrument_combo.addItem("Pad 2 (warm)")
        instrument_combo.addItem("Pad 3 (polysynth)")
        instrument_combo.addItem("Pad 4 (choir)")
        instrument_combo.addItem("Pad 5 (bowed)")
        instrument_combo.addItem("Pad 6 (metallic)")
        instrument_combo.addItem("Pad 7 (halo)")
        instrument_combo.addItem("Pad 8 (sweep)")

        # Synth Effects Family (97-104)
        instrument_combo.addItem("FX 1 (rain)")
        instrument_combo.addItem("FX 2 (soundtrack)")
        instrument_combo.addItem("FX 3 (crystal)")
        instrument_combo.addItem("FX 4 (atmosphere)")
        instrument_combo.addItem("FX 5 (brightness)")
        instrument_combo.addItem("FX 6 (goblins)")
        instrument_combo.addItem("FX 7 (echoes)")
        instrument_combo.addItem("FX 8 (sci-fi)")

        # Ethnic Family (105-112)
        instrument_combo.addItem("Sitar")
        instrument_combo.addItem("Banjo")
        instrument_combo.addItem("Shamisen")
        instrument_combo.addItem("Koto")
        instrument_combo.addItem("Kalimba")
        instrument_combo.addItem("Bag pipe")
        instrument_combo.addItem("Fiddle")
        instrument_combo.addItem("Shanai")

        # Percussive Family (113-120)
        instrument_combo.addItem("Tinkle Bell")
        instrument_combo.addItem("Agogo")
        instrument_combo.addItem("Steel Drums")
        instrument_combo.addItem("Woodblock")
        instrument_combo.addItem("Taiko Drum")
        instrument_combo.addItem("Melodic Tom")
        instrument_combo.addItem("Synth Drum")
        instrument_combo.addItem("Reverse Cymbal")

        # Sound Effects Family (121-128)
        instrument_combo.addItem("Guitar Fret Noise")
        instrument_combo.addItem("Breath Noise")
        instrument_combo.addItem("Seashore")
        instrument_combo.addItem("Bird Tweet")
        instrument_combo.addItem("Telephone Ring")
        instrument_combo.addItem("Helicopter")
        instrument_combo.addItem("Applause")
        instrument_combo.addItem("Gunshot")

        # Get the current plugin/instrument if it exists
        current_plugin = ""
        if staff_data and "plugin" in staff_data:
            current_plugin = staff_data["plugin"]

        # Try to set the current selection
        if current_plugin:
            index = instrument_combo.findText(current_plugin)
            if index >= 0:
                instrument_combo.setCurrentIndex(index)

        instrument_layout.addWidget(instrument_combo)

        # Add note about instruments
        instrument_note = QLabel(
            "This setting determines which sound will be used when playing back this staff."
        )
        instrument_note.setWordWrap(True)
        instrument_note.setStyleSheet("font-style: italic; color: #666;")
        instrument_layout.addWidget(instrument_note)

        instrument_layout.addStretch()
        tabs.addTab(instrument_tab, "GM Instrument")

        layout.addWidget(tabs)

        # Add dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Connect section buttons
        def on_new_section():
            # Show dialog to create a new section
            section_dialog = QDialog(dialog)
            section_dialog.setWindowTitle("New Section")
            section_dialog.setModal(True)

            s_layout = QVBoxLayout(section_dialog)
            s_layout.addWidget(QLabel("Enter section name:"))

            section_name_edit = QLineEdit()
            s_layout.addWidget(section_name_edit)

            s_buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )
            s_buttons.accepted.connect(section_dialog.accept)
            s_buttons.rejected.connect(section_dialog.reject)
            s_layout.addWidget(s_buttons)

            if section_dialog.exec() == QDialog.DialogCode.Accepted:
                section_name = section_name_edit.text().strip()
                if section_name:
                    # Add to combo if not already there
                    if section_combo.findText(section_name) < 0:
                        section_combo.addItem(section_name)
                    # Select the new section
                    section_combo.setCurrentText(section_name)

        def on_remove_from_section():
            # Set empty selection
            section_combo.setCurrentIndex(0)

        new_section_btn.clicked.connect(on_new_section)
        remove_section_btn.clicked.connect(on_remove_from_section)

        # Make sure the Staff Name tab is selected by default
        tabs.setCurrentIndex(0)
        
        # Set focus to the custom name field after a short delay to ensure dialog is shown
        from PyQt6.QtCore import QTimer
        def set_focus():
            custom_name_edit.setFocus()
            custom_name_edit.selectAll()  # Also select all text for easier editing
        
        QTimer.singleShot(50, set_focus)  # Small delay to ensure dialog is fully shown

        # Show dialog and process result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the selected values
            new_staff_type_display = staff_type_combo.currentText()
            new_clef_display = clef_combo.currentText()
            new_section = section_combo.currentText()
            new_custom_name = custom_name_edit.text().strip()
            new_custom_abbr = custom_abbr_edit.text().strip()
            new_instrument = instrument_combo.currentText()  # Get the selected instrument

            # Convert display staff type to internal representation
            new_staff_type_internal = "single_staff"
            new_clef = "treble"

            if new_staff_type_display == "Grand Staff":
                new_staff_type_internal = "grand_staff"
                new_clef = "treble"  # Grand staff defaults to treble, but shows both
            else:
                # Map clef display to internal clef value
                if new_clef_display == "Bass":
                    new_clef = "bass"
                elif new_clef_display == "Alto":
                    new_clef = "alto"
                elif new_clef_display == "Percussion":
                    new_clef = "percussion"
                else:
                    new_clef = "treble"

            # Apply to all selected items
            num_updated = 0
            for item in selected_items:
                staff_data = item.data(0, Qt.ItemDataRole.UserRole)
                original_clef = staff_data.get("clef", "treble")  # Store original clef
                original_staff_type = staff_data.get("staff_type", "single_staff")  # Store original staff type

                # CRITICAL FIX: Only update staff type and clef if they were actually changed
                # Check if this is a multi-selection with mixed staff types/clefs
                is_multi_selection = len(selected_items) > 1
                
                # Only update staff type if it was explicitly changed or this is a single selection
                if not is_multi_selection or original_staff_type != new_staff_type_internal:
                    # Only update if the user intended to change it
                    if len(selected_items) == 1 or staff_type_combo.currentText() != first_item.text(1):
                        staff_data["staff_type"] = new_staff_type_internal
                        item.setText(1, new_staff_type_display)  # Display staff type
                        print(f"STAFF ATTRIBUTES: Updated staff type for {item.text(0)} from {original_staff_type} to {new_staff_type_internal}")
                
                # Only update clef if it was explicitly changed or this is a single selection
                if not is_multi_selection or original_clef != new_clef:
                    # Only update if the user intended to change it
                    if len(selected_items) == 1 or clef_combo.currentText() != first_item.text(2):
                        staff_data["clef"] = new_clef
                        staff_data["staff_data"] = staff_data.get("staff_data", {})
                        staff_data["staff_data"]["clef"] = new_clef
                        item.setText(2, new_clef_display)  # Display clef
                        print(f"STAFF ATTRIBUTES: Updated clef for {item.text(0)} from {original_clef} to {new_clef}")
                    else:
                        # Preserve original clef when not explicitly changed
                        print(f"STAFF ATTRIBUTES: Preserving original clef '{original_clef}' for {item.text(0)} in multi-selection")

                # Always update section regardless of selection size
                staff_data["section"] = new_section
                item.setText(3, new_section)
                
                # CRITICAL FIX: Only update plugin if it was explicitly changed or this is a single selection
                original_plugin = staff_data.get("plugin", "Default")
                # Only update plugin if the user actually changed it or if it's a single selection
                if len(selected_items) == 1 or (new_instrument and new_instrument != first_item.text(4)):
                    if new_instrument and new_instrument != "Default":
                        staff_data["plugin"] = new_instrument
                        item.setText(4, new_instrument)  # Update the Plugin/Instrument column
                        print(f"STAFF ATTRIBUTES: Updated plugin for {item.text(0)} from {original_plugin} to {new_instrument}")
                    else:
                        # Reset to default if explicitly cleared
                        staff_data["plugin"] = "Default"
                        item.setText(4, "Default")
                        print(f"STAFF ATTRIBUTES: Reset plugin for {item.text(0)} to Default")
                else:
                    # Preserve original plugin when not explicitly changed in multi-selection
                    print(f"STAFF ATTRIBUTES: Preserving original plugin '{original_plugin}' for {item.text(0)} in multi-selection")

                # CRITICAL FIX: Only update custom name if it was explicitly changed or this is a single selection
                original_name = item.text(0)  # Current display name
                # Only update name if the user actually changed it or if it's a single selection  
                if len(selected_items) == 1 or (new_custom_name and new_custom_name != first_item.text(0)):
                    if new_custom_name:
                        staff_data["custom_name"] = new_custom_name
                        # Also update the display name in the staff list
                        item.setText(0, new_custom_name)
                        print(f"STAFF ATTRIBUTES: Updated name for {original_name} to {new_custom_name}")
                    elif "custom_name" in staff_data:
                        # If the field was cleared, remove the custom name
                        del staff_data["custom_name"]
                        # Reset display name to instrument name
                        item.setText(0, staff_data.get("instrument_name", "Part"))
                        print(f"STAFF ATTRIBUTES: Reset name for {original_name} to default")
                else:
                    # Preserve original name when not explicitly changed in multi-selection
                    print(f"STAFF ATTRIBUTES: Preserving original name '{original_name}' in multi-selection")

                # CRITICAL FIX: Only update custom abbreviation if it was explicitly changed or this is a single selection
                original_abbr = staff_data.get("custom_abbr", "")
                # Only update abbreviation if the user actually changed it or if it's a single selection
                if len(selected_items) == 1 or (new_custom_abbr and new_custom_abbr != staff_data.get("custom_abbr", "")):
                    if new_custom_abbr:
                        staff_data["custom_abbr"] = new_custom_abbr
                        print(f"STAFF ATTRIBUTES: Updated abbreviation for {original_name} from '{original_abbr}' to '{new_custom_abbr}'")
                    elif "custom_abbr" in staff_data:
                        # If the field was cleared, remove the custom abbreviation
                        del staff_data["custom_abbr"]
                        print(f"STAFF ATTRIBUTES: Cleared abbreviation for {original_name}")
                else:
                    # Preserve original abbreviation when not explicitly changed in multi-selection
                    print(f"STAFF ATTRIBUTES: Preserving original abbreviation '{original_abbr}' for {original_name} in multi-selection")

                # Update the item data
                item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                # Mark that there are unapplied changes
                self.has_unapplied_changes = True
                self.staff_options_changed.emit(
                    self.staff_list.indexOfTopLevelItem(item), staff_data
                )

                num_updated += 1

            # The staff_options_changed signals will trigger the dialog's signal handlers
            # which will apply changes immediately

            print("Updated staff attributes")

            # ENHANCEMENT: Show user feedback about the update
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar.showMessage(
                    f"Updated attributes for {num_updated} staff items", 3000
                )

        # Only continue if we have valid staff data
        if not staff_data:
            print("ERROR: Could not get valid staff data for the selected staff")
            if hasattr(self.parent(), "statusBar"):
                self.parent().statusBar.showMessage("Error: Could not edit staff attributes", 3000)
            return

    def add_generic_staff(self, staff_type):
        """Add a generic staff of the specified type"""
        print(f"[DEBUG] add_generic_staff called: staff_type={staff_type}")
        print(f"[DEBUG] Button clicked - adding {staff_type} staff")
        # Create staff data
        if staff_type == "grand":
            # Add a grand staff
            display_type = "Grand Staff"
            internal_type = "grand_staff"
            clef = "treble"  # Grand staff has both treble and bass
            clef_display = "Treble/Bass"
            real_instrument_type = "Piano"  # Store the actual instrument type internally
        else:
            # Add a single staff with the specified clef
            internal_type = "single_staff"
            if staff_type == "treble":
                display_type = "Single Staff"
                clef = "treble"
                clef_display = "Treble"
                real_instrument_type = "Treble"
            elif staff_type == "bass":
                display_type = "Single Staff"
                clef = "bass"
                clef_display = "Bass"
                real_instrument_type = "Bass"
            elif staff_type == "alto":
                display_type = "Single Staff"
                clef = "alto"
                clef_display = "Alto"
                real_instrument_type = "Viola"
            elif staff_type == "percussion":
                display_type = "Single Staff"
                clef = "percussion"
                clef_display = "Percussion"
                real_instrument_type = "Percussion"

        # Generate a unique instrument name (always "Part")
        instr_name = self.get_new_instrument_name(staff_type)

        # Generate instrument ID from name (lowercase with underscores)
        instr_id = instr_name.lower().replace(" ", "_")

        # Create a new item for the staff list
        item = QTreeWidgetItem(self.staff_list)
        item.setText(0, instr_name)  # Name (always "Part" or "Part N")
        item.setText(1, display_type)  # Staff Type
        item.setText(2, clef_display)  # Clef
        item.setText(3, "")  # Section (empty by default)
        item.setText(4, "Default")  # Plugin/Instrument (default for generic staves)

        # Store staff data as user data
        staff_data = {
            "instrument_id": instr_id,
            "instrument_name": instr_name,
            "instrument_abbr": instr_name[:3].upper(),
            "staff_type": internal_type,
            "clef": clef,
            "key": "C major / A minor (no sharps/flats)",
            "time_signature": "4/4",
            "section": "",
            "plugin": "Default",
            "real_instrument_type": real_instrument_type  # Store actual instrument type internally
        }
        item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

        # Emit signal that staff was added
        index = self.staff_list.indexOfTopLevelItem(item)
        print(f"[DEBUG] add_generic_staff emitting staff_added signal: {instr_id}, {internal_type}, {index}")
        print(f"[DEBUG] About to emit staff_added signal from widget")
        self.staff_added.emit(instr_id, internal_type, index)
        print(f"[DEBUG] staff_added signal emitted successfully")

        # Update the staff count label
        self.update_staff_count_label()

        # Select the new staff
        self.staff_list.setCurrentItem(item)

        # Auto-scroll to the new item
        self.staff_list.scrollToItem(item)

        # Set unapplied changes flag
        self.has_unapplied_changes = True

        # Let the signal handlers handle immediate rendering
        # The staff_added signal will trigger the dialog's on_staff_added method

        return item

    def apply_changes_immediate(self, options):
        """
        Apply changes immediately while preserving setup mode.
        This is specifically for showing newly added staves in the pink setup mode.
        """
        # Make sure to keep setup mode
        print("SETUP WIDGET: Applying immediate changes and preserving setup mode")

        # Force setup mode flag
        options["has_unapplied_changes"] = False
        options["force_setup_mode"] = True
        options["immediate_apply"] = True
        options["force_render"] = True  # Ensure renderer is updated

        # Important: Ensure staff types and clefs are preserved
        if "preserve_staff_types" not in options:
            options["preserve_staff_types"] = True
        if "preserve_clefs" not in options:
            options["preserve_clefs"] = True

        print(
            f"SETUP WIDGET: preserve_staff_types = {options['preserve_staff_types']}, preserve_clefs = {options['preserve_clefs']}"
        )

        # CRITICAL FIX: Ensure section order is preserved when applying changes
        # Rebuild the section_display_order map to ensure it's fresh and accurate
        section_display_order = {}
        section_first_appearance = {}

        # First pass: build section_first_appearance to track the first occurrence of each section
        if self.staff_list:
            print("\nSETUP WIDGET: Rebuilding section display order from current UI state")
            for i in range(self.staff_list.topLevelItemCount()):
                item = self.staff_list.topLevelItem(i)
                section = item.text(3)  # Update section column index
                staff_type_display = item.text(1)
                clef_display = item.text(2)

                # If preserve_staff_types is enabled, make sure each staff's type is correctly preserved
                if options["preserve_staff_types"]:
                    staff_data = item.data(0, Qt.ItemDataRole.UserRole)
                    if staff_data:
                        # Ensure staff data correctly reflects UI state
                        instrument_id = staff_data.get(
                            "instrument_id", item.text(0).lower().replace(" ", "_")
                        )

                        # Create or update staff_type_map entry for this staff
                        if staff_type_display == "Grand Staff":
                            options["staff_type_map"][instrument_id] = "grand_staff"
                            print(
                                f"IMMEDIATE: Set {item.text(0)} to grand staff based on UI display"
                            )
                        else:  # Single Staff
                            options["staff_type_map"][instrument_id] = "single_staff"
                            # CRITICAL FIX: Only set clef based on display if preserve_clefs is False
                            # This prevents overriding stored clef data when sections are created
                            if not options.get("preserve_clefs", True):
                                # Set clef based on display
                                if clef_display == "Bass":
                                    staff_data["clef"] = "bass"
                                    print(
                                        f"IMMEDIATE: Set {item.text(0)} to bass clef based on UI display"
                                    )
                                elif clef_display == "Alto":
                                    staff_data["clef"] = "alto"
                                    print(
                                        f"IMMEDIATE: Set {item.text(0)} to alto clef based on UI display"
                                    )
                                elif clef_display == "Percussion":
                                    staff_data["clef"] = "percussion"
                                    print(
                                        f"IMMEDIATE: Set {item.text(0)} to percussion clef based on UI display"
                                    )
                                else:  # Default to treble
                                    staff_data["clef"] = "treble"
                                    print(
                                        f"IMMEDIATE: Set {item.text(0)} to treble clef based on UI display"
                                    )
                            else:
                                # Preserve existing clef data
                                existing_clef = staff_data.get("clef", "treble")
                                print(
                                    f"IMMEDIATE: Preserving existing clef '{existing_clef}' for {item.text(0)} (preserve_clefs=True)"
                                )

                if section and section not in section_first_appearance:
                    section_first_appearance[section] = i
                    section_display_order[section] = i
                    print(f"IMMEDIATE: Section '{section}' first appears at index {i}")

        # Always force-update the section_display_order
        options["section_display_order"] = section_display_order
        print(
            f"IMMEDIATE: Set section_display_order in options with {len(section_display_order)} sections"
        )

        # Add display_order_index to all staves and ensure section assignments are correct
        for i, staff_data in enumerate(options.get("added_staves", [])):
            # Set display order index for all staves to ensure proper ordering
            staff_data["display_order_index"] = i

            # Get the section name
            section_name = staff_data.get("section", "")

            # If the staff is in a section, store the section's display order
            if section_name and section_name in section_display_order:
                staff_data["section_display_order"] = section_display_order[section_name]
                print(
                    f"IMMEDIATE: Set staff '{staff_data.get('instrument_name', 'Unknown')}' in section '{section_name}' with order_index={i}"
                )
            else:
                # Clear any previous section data to avoid confusion
                if "section_display_order" in staff_data:
                    del staff_data["section_display_order"]

                if section_name:
                    print(
                        f"IMMEDIATE WARNING: Staff '{staff_data.get('instrument_name', 'Unknown')}' is in unknown section '{section_name}'"
                    )
                else:
                    print(
                        f"IMMEDIATE: Staff '{staff_data.get('instrument_name', 'Unknown')}' is not in any section, order_index={i}"
                    )

        # If preserve_staff_types is enabled, make one more pass to ensure staff types are synchronized
        # between the staff_type_map and the added_staves entries
        if (
            options["preserve_staff_types"]
            and "staff_type_map" in options
            and options["staff_type_map"]
        ):
            print(
                f"IMMEDIATE: Synchronizing staff types from staff_type_map to added_staves entries"
            )

            for staff_data in options.get("added_staves", []):
                instrument_id = staff_data.get("instrument_id", "")
                if instrument_id and instrument_id in options["staff_type_map"]:
                    staff_type = options["staff_type_map"][instrument_id]
                    instrument_name = staff_data.get("instrument_name", "Unknown")

                    # Check if the staff type needs to be updated
                    if staff_data.get("staff_type", "") != staff_type:
                        staff_data["staff_type"] = staff_type
                        print(
                            f"IMMEDIATE: Updated staff '{instrument_name}' to type={staff_type} from staff_type_map"
                        )

                    # Make sure clef is synchronized too
                    if "clef" in staff_data and instrument_id in options["staff_type_map"]:
                        clef = staff_data["clef"]
                        print(f"IMMEDIATE: Staff '{instrument_name}' has clef={clef}")

        # If preserve_clefs is enabled, make sure each staff's clef is correctly preserved
        if options["preserve_clefs"] and "clef_map" in options and options["clef_map"]:
            print(f"IMMEDIATE: Synchronizing clefs from clef_map to added_staves entries")

            for staff_data in options.get("added_staves", []):
                instrument_id = staff_data.get("instrument_id", "")
                if instrument_id and instrument_id in options["clef_map"]:
                    clef = options["clef_map"][instrument_id]
                    instrument_name = staff_data.get("instrument_name", "Unknown")

                    # Check if the clef needs to be updated
                    if staff_data.get("clef", "") != clef:
                        staff_data["clef"] = clef
                        print(
                            f"IMMEDIATE: Updated staff '{instrument_name}' clef to {clef} from clef_map"
                        )

                    # Also update staff_data.clef if it exists
                    if (
                        "staff_data" in staff_data
                        and staff_data["staff_data"].get("clef", "") != clef
                    ):
                        staff_data["staff_data"]["clef"] = clef
                        print(
                            f"IMMEDIATE: Updated staff_data.clef for '{instrument_name}' to {clef}"
                        )

        # Print detailed summary of what we're about to send to the renderer
        print("\nIMMEDIATE: Section display order summary being sent to renderer:")
        for section_name, order_index in section_display_order.items():
            print(f"  Section '{section_name}' with display_order_index = {order_index}")

        # Print detailed summary of staff section assignments
        print("\nIMMEDIATE: Staff section assignments summary:")
        section_staves = {}
        for i, staff_data in enumerate(options.get("added_staves", [])):
            section_name = staff_data.get("section", "")
            staff_type = staff_data.get("staff_type", "single_staff")
            clef = staff_data.get("clef", "treble")
            if section_name:
                if section_name not in section_staves:
                    section_staves[section_name] = []
                section_staves[section_name].append(
                    f"{staff_data.get('instrument_name', 'Unknown')} (type={staff_type}, clef={clef})"
                )
            else:
                print(
                    f"  Staff {i}: {staff_data.get('instrument_name', 'Unknown')} - Ungrouped (type={staff_type}, clef={clef})"
                )

        # Print section contents
        for section_name, staves in section_staves.items():
            print(f"  Section '{section_name}' contains {len(staves)} staves:")
            for i, staff_name in enumerate(staves):
                print(f"    {i}: {staff_name}")

        # Try to apply changes to the view and document
        applied = False

        # First try parent_view (most direct connection to the document)
        if hasattr(self.parent(), "parent_view") and self.parent().parent_view:
            parent_view = self.parent().parent_view

            if hasattr(parent_view, "apply_setup_options"):
                try:
                    print("IMMEDIATE: Applying to parent_view directly")
                    # Force setup mode in parent view
                    parent_view.is_setup_mode = True

                    # Apply the options
                    result = parent_view.apply_setup_options(options)
                    parent_view.dialog_settings = options
                    print(f"IMMEDIATE: parent_view.apply_setup_options result = {result}")

                    # Ensure document layout is in setup mode
                    if hasattr(parent_view, "document") and hasattr(parent_view.document, "layout"):
                        print("IMMEDIATE: Setting document layout to setup mode")
                        parent_view.document.layout.set_setup_mode(True)

                        # CRITICAL: Force _update_positions to be called to ensure correct layout
                        parent_view.document.layout._update_positions()
                        print("IMMEDIATE: Forced document layout _update_positions")

                    # Force renderer to update if available
                    if hasattr(parent_view, "renderer") and hasattr(
                        parent_view.renderer, "set_document"
                    ):
                        parent_view.renderer.set_document(parent_view.document)
                        print("IMMEDIATE: Updated renderer with document")

                    # Force update
                    parent_view.update()
                    applied = True
                except Exception as e:
                    print(f"ERROR applying changes to parent_view: {str(e)}")

        # Try parent window's staff_view as a fallback
        if not applied and hasattr(self.parent(), "parent") and self.parent().parent():
            try:
                parent_window = self.parent().parent()
                if hasattr(parent_window, "staff_view"):
                    staff_view = parent_window.staff_view
                    print("IMMEDIATE: Applying to parent window's staff_view")

                    # Force setup mode in staff view
                    staff_view.is_setup_mode = True

                    # Apply the options
                    result = staff_view.apply_setup_options(options)
                    staff_view.dialog_settings = options
                    print(f"IMMEDIATE: staff_view.apply_setup_options result = {result}")

                    # Ensure document layout is in setup mode
                    if hasattr(staff_view, "document") and hasattr(staff_view.document, "layout"):
                        print("IMMEDIATE: Setting document layout to setup mode")
                        staff_view.document.layout.set_setup_mode(True)

                        # CRITICAL: Force _update_positions to be called to ensure correct layout
                        staff_view.document.layout._update_positions()
                        print("IMMEDIATE: Forced document layout _update_positions")

                    # Force renderer to update if available
                    if hasattr(staff_view, "renderer") and hasattr(
                        staff_view.renderer, "set_document"
                    ):
                        staff_view.renderer.set_document(staff_view.document)
                        print("IMMEDIATE: Updated renderer with document")

                    # Force update
                    staff_view.update()
                    applied = True
            except Exception as e:
                print(f"ERROR applying changes to staff_view: {str(e)}")

        # If none of the above worked, try through parent dialog
        if not applied and hasattr(self.parent(), "apply_setup_options"):
            try:
                print("IMMEDIATE: Applying through parent dialog")
                result = self.parent().apply_setup_options(options)
                print(f"IMMEDIATE: parent.apply_setup_options result = {result}")

                # Try to ensure the parent dialog's view is updated
                if hasattr(self.parent(), "update"):
                    self.parent().update()

                # Try to update the renderer if available
                if hasattr(self.parent(), "renderer") and hasattr(
                    self.parent().renderer, "set_document"
                ):
                    self.parent().renderer.set_document(self.parent().document)
                    print("IMMEDIATE: Updated renderer through parent dialog")

                # CRITICAL: Try to force document layout update if possible
                if hasattr(self.parent(), "document") and hasattr(self.parent().document, "layout"):
                    self.parent().document.layout._update_positions()
                    print(
                        "IMMEDIATE: Forced document layout _update_positions through parent dialog"
                    )
            except Exception as e:
                print(f"ERROR applying changes through parent dialog: {str(e)}")

        print("IMMEDIATE: Applied changes with setup mode preserved")
        return True

    def populate_added_staves(self, dialog_settings):
        """Populate the staff list with staves from dialog settings"""
        if not hasattr(self, "staff_list") or not self.staff_list:
            print("ERROR: Staff list not initialized")
            return False

        # Clear existing items
        self.staff_list.clear()

        # Check if dialog_settings has added_staves
        if "added_staves" not in dialog_settings or not dialog_settings["added_staves"]:
            print("No staves found in dialog settings to populate")
            return False

        print(
            f"Populating staff list with {len(dialog_settings['added_staves'])} staves from dialog settings"
        )
        
        # Get section display order from dialog settings if available
        section_display_order = dialog_settings.get('section_display_order', {})
        print(f"POPULATE: Using section_display_order with {len(section_display_order)} entries")
        for section_name, order in section_display_order.items():
            print(f"  Section '{section_name}' order = {order}")
        
        # Sort staves to ensure proper ordering: ungrouped staves first, then sections in order
        sorted_staves = []
        ungrouped_staves = []
        section_staves = {}
        
        # Group staves by section
        for staff_data in dialog_settings["added_staves"]:
            section = staff_data.get("section", "")
            if section:
                if section not in section_staves:
                    section_staves[section] = []
                section_staves[section].append(staff_data)
            else:
                ungrouped_staves.append(staff_data)
        
        # Add ungrouped staves first (they should appear at the top)
        sorted_staves.extend(ungrouped_staves)
        print(f"POPULATE: Added {len(ungrouped_staves)} ungrouped staves")
        
        # Sort sections by their display order and add their staves
        sections_with_order = []
        for section_name, staves in section_staves.items():
            order = section_display_order.get(section_name, 999)  # Default high order for unknown sections
            sections_with_order.append((order, section_name, staves))
        
        # Sort by order index
        sections_with_order.sort(key=lambda x: x[0])
        
        # Add staves from sections in proper order
        for order, section_name, staves in sections_with_order:
            print(f"POPULATE: Adding {len(staves)} staves from section '{section_name}' (order={order})")
            sorted_staves.extend(staves)
        
        # Now add staves to the UI in the correct order
        for staff_data in sorted_staves:
            # Get basic staff info
            instrument_name = staff_data.get("instrument_name", "Unknown")
            staff_type = staff_data.get("staff_type", "single_staff")
            clef = staff_data.get("clef", "treble")
            section = staff_data.get("section", "")

            # Use custom_name if available, otherwise use instrument_name
            display_name = staff_data.get("custom_name", instrument_name)
            if "custom_name" in staff_data:
                print(f"POPULATE: Using custom_name '{display_name}' for {instrument_name}")
            if "custom_abbr" in staff_data:
                print(f"POPULATE: Preserving custom_abbr '{staff_data['custom_abbr']}' for {instrument_name}")

            # Determine display values for staff type and clef
            if staff_type == "grand_staff":
                staff_type_display = "Grand Staff"
                clef_display = "Treble/Bass"
            else:  # single_staff
                staff_type_display = "Single Staff"
                if clef == "bass":
                    clef_display = "Bass"
                elif clef == "alto":
                    clef_display = "Alto"
                elif clef == "percussion":
                    clef_display = "Percussion"
                else:
                    clef_display = "Treble"

            # Create list item with correct display values
            staff_item = QTreeWidgetItem(self.staff_list)
            staff_item.setText(0, display_name)  # Use custom_name if available
            staff_item.setText(1, staff_type_display)
            staff_item.setText(2, clef_display)
            staff_item.setText(3, section)

            # Set plugin value (default if not specified)
            plugin = staff_data.get("plugin", "Default")
            staff_item.setText(4, plugin)

            staff_item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

            print(
                f"Added {instrument_name} to staff list with type={staff_type_display}, clef={clef_display}"
            )

        # Set column widths
        self.staff_list.setColumnWidth(0, 180)  # Staff name
        self.staff_list.setColumnWidth(1, 120)  # Staff type
        self.staff_list.setColumnWidth(2, 80)  # Clef
        self.staff_list.setColumnWidth(3, 120)  # Section
        self.staff_list.setColumnWidth(4, 120)  # Plugin/Instrument
        
        self.has_unapplied_changes = False
        return True

    def get_new_instrument_name(self, staff_type):
        """Generate a unique instrument name based on staff type"""
        # Count existing staves to generate a unique number
        count = self.staff_list.topLevelItemCount() + 1

        # Always return "Part" regardless of staff type
        base_name = "Part"

        # Add a number if there are other parts
        for i in range(self.staff_list.topLevelItemCount()):
            item = self.staff_list.topLevelItem(i)
            if item.text(0).startswith(base_name):
                # Add a number suffix
                return f"{base_name} {count}"

        # Return base name if this is the first of its kind
        return base_name

    def update_staff_count_label(self):
        """Update the staff count label with the current number of staves"""
        count = self.staff_list.topLevelItemCount()
        if hasattr(self, "staff_count_label"):
            self.staff_count_label.setText(f"Total staves: {count}")
            print(f"STAFF_COUNT: Updated label to show {count} staves")

    def on_category_changed(self, current, previous):
        """Handle category list selection changes"""
        if current:
            category_name = current.text()
            self.filter_instruments(category_name)
        else:
            # Clear filter if no category selected
            self.filter_instruments("")

    def on_lock_selection_changed(self, state):
        """Handle changes to the lock selection checkbox"""
        is_checked = state == Qt.CheckState.Checked.value
        selected_items = self.staff_list.selectedItems()
        
        if not selected_items:
            return
        
        # Check if any selected items belong to sections
        section_members = []
        sections_involved = set()
        
        for item in selected_items:
            section = item.text(3)
            if section:
                section_members.append(item)
                sections_involved.add(section)
        
        # Update status label based on lock state and section involvement
        if hasattr(self, 'status_label') and section_members:
            if is_checked:
                # Locked state - sections behave normally
                if len(sections_involved) == 1:
                    section_name = list(sections_involved)[0]
                    self.status_label.setText(f"✓ Section '{section_name}' selected ({len(section_members)} staves) - Locked Movement")
                    self.status_label.setStyleSheet("color: blue; font-size: 10px; padding: 2px;")
                else:
                    self.status_label.setText(f"✓ Multiple sections selected - Locked Movement")
                    self.status_label.setStyleSheet("color: blue; font-size: 10px; padding: 2px;")
            else:
                # Unlocked state - sections open for editing
                if len(sections_involved) == 1:
                    section_name = list(sections_involved)[0]
                    self.status_label.setText(f"⚠ Section '{section_name}' - Open for Edit ({len(section_members)} staves)")
                    self.status_label.setStyleSheet("color: orange; font-size: 10px; padding: 2px;")
                else:
                    self.status_label.setText(f"⚠ Multiple sections - Open for Edit")
                    self.status_label.setStyleSheet("color: orange; font-size: 10px; padding: 2px;")
                    
    def refresh_from_document(self):
        """Refresh the setup widget from the current document state
        
        This is called when undo/redo operations change the document state
        and we need to update the UI to reflect those changes.
        """
        print("REFRESH: Starting refresh_from_document() - FORCE REFRESH MODE")
        
        # Get the current document from parent - try multiple paths
        document = None
        
        # Path 1: parent.staff_view.document (dialog -> main_window -> staff_view -> document)
        if hasattr(self.parent(), 'staff_view') and hasattr(self.parent().staff_view, 'document'):
            document = self.parent().staff_view.document
            print("REFRESH: Found document via parent.staff_view.document")
            
        # Path 2: parent_view.document (dialog -> staff_view -> document)  
        elif hasattr(self, 'parent_view') and hasattr(self.parent_view, 'document'):
            document = self.parent_view.document
            print("REFRESH: Found document via parent_view.document")
            
        # Path 3: parent.document (dialog -> staff_view -> document - direct)
        elif hasattr(self.parent(), 'document'):
            document = self.parent().document
            print("REFRESH: Found document via parent.document")
            
        # Path 4: Try to find via dialog parent
        elif hasattr(self.parent(), 'parent_view') and hasattr(self.parent().parent_view, 'document'):
            document = self.parent().parent_view.document
            print("REFRESH: Found document via parent.parent_view.document")
            
        else:
            print("REFRESH: No document available for refresh - ABORTING")
            return  # No document available
        
        print(f"REFRESH: Found document with {len(document.layout.ungrouped_staves)} ungrouped staves and {len(document.layout.sections)} sections")
        
        # STEP 1: FORCE clear ALL cached and UI state
        print("REFRESH: Step 1 - Forcibly clearing all cached state")
        self.staff_list.clear()
        
        # Clear any parent dialog settings that might interfere
        if hasattr(self.parent(), 'dialog_settings'):
            print("REFRESH: Clearing parent dialog_settings to force document refresh")
            self.parent().dialog_settings = None
            
        if hasattr(self.parent(), 'parent_view') and hasattr(self.parent().parent_view, 'dialog_settings'):
            print("REFRESH: Clearing parent_view dialog_settings to force document refresh")
            self.parent().parent_view.dialog_settings = None
        
        # Clear any cached dialog settings that might interfere  
        if hasattr(self, 'dialog_settings'):
            self.dialog_settings = None
            
        # Reset state flags
        self.has_unapplied_changes = False
        
        # STEP 2: Rebuild staff list from current document state
        staff_count = 0
        
        # First add ungrouped staves
        for i, staff in enumerate(document.layout.ungrouped_staves):
            try:
                self._add_staff_to_list(staff, section_name="")
                staff_count += 1
                print(f"REFRESH: Added ungrouped staff {i}: {getattr(staff, 'instrument_name', 'Unknown')}")
            except Exception as e:
                print(f"REFRESH: Error adding ungrouped staff {i}: {e}")
        
        # Then add staves from sections  
        for section in document.layout.sections:
            section_name = section.name
            for i, staff in enumerate(section.staves):
                try:
                    self._add_staff_to_list(staff, section_name=section_name)
                    staff_count += 1
                    print(f"REFRESH: Added section staff {i} from '{section_name}': {getattr(staff, 'instrument_name', 'Unknown')}")
                except Exception as e:
                    print(f"REFRESH: Error adding section staff {i}: {e}")
        
        # STEP 3: Update UI elements
        self.update_staff_count_label()
        print(f"REFRESH: Updated staff count label (total: {staff_count})")
        
        # STEP 4: Force complete UI refresh
        self.staff_list.update()
        self.staff_list.repaint()
        
        # Force refresh of any selection indicators
        self.on_staff_selection_changed()
        
        # Force refresh of any other UI elements that depend on staff data
        if hasattr(self, 'instrument_filter'):
            # Clear any active filters to show all current data
            self.instrument_filter.clear()
        
        # STEP 5: Schedule delayed refresh to catch any missed updates
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._delayed_refresh_check(staff_count))
        
        print("REFRESH: Completed refresh_from_document() - UI should now reflect current document state")

    def _delayed_refresh_check(self, expected_count):
        """Delayed check to ensure refresh completed correctly"""
        actual_count = self.staff_list.topLevelItemCount()
        if actual_count != expected_count:
            print(f"REFRESH: Delayed check found mismatch - expected {expected_count}, got {actual_count}")
            # Force another update
            self.staff_list.update()
            self.staff_list.repaint()
        else:
            print(f"REFRESH: Delayed check confirmed {actual_count} staves loaded correctly")

    def _add_staff_to_list(self, staff, section_name=""):
        """Helper method to add a staff to the staff list widget"""
        # Create the tree widget item
        item = QTreeWidgetItem(self.staff_list)
        
        # Get staff name with more robust fallbacks
        staff_name = getattr(staff, 'instrument_name', None)
        if not staff_name:
            staff_name = getattr(staff, 'name', None)
        if not staff_name:
            # Use instrument_id if available
            staff_name = getattr(staff, 'instrument_id', 'Unknown')
        
        item.setText(0, staff_name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        
        # Set staff type (column 1) with more robust detection
        staff_type = 'single_staff'  # Default
        if hasattr(staff, 'staff_type'):
            staff_type = staff.staff_type
        elif hasattr(staff, 'top_staff') and hasattr(staff, 'bottom_staff'):
            staff_type = 'grand_staff'
        elif hasattr(staff, '__class__') and 'Grand' in staff.__class__.__name__:
            staff_type = 'grand_staff'
        
        # Display staff type
        if staff_type == 'grand_staff':
            item.setText(1, "Grand Staff")
        else:
            item.setText(1, "Single Staff")
        
        # Set clef (column 2) with better detection
        clef = getattr(staff, 'clef', 'treble')
        
        # For grand staff, check both staves
        if staff_type == 'grand_staff':
            item.setText(2, "Treble/Bass")
        else:
            # Display clef properly
            if clef == 'bass':
                item.setText(2, "Bass")
            elif clef == 'alto':
                item.setText(2, "Alto") 
            elif clef == 'percussion':
                item.setText(2, "Percussion")
            else:
                item.setText(2, "Treble")
        
        # Set section (column 3)
        item.setText(3, section_name or "")
        
        # Set plugin/instrument (column 4)
        plugin = getattr(staff, 'plugin', 'Default')
        item.setText(4, plugin)
        
        # Generate instrument_id with better fallback
        instrument_id = getattr(staff, 'instrument_id', None)
        if not instrument_id:
            instrument_id = staff_name.lower().replace(' ', '_').replace('-', '_')
        
        # Store comprehensive staff data on the item for later retrieval
        staff_data = {
            'staff': staff,
            'instrument_id': instrument_id,
            'instrument_name': staff_name,
            'section': section_name or "",
            'staff_type': staff_type,
            'clef': clef,
            'plugin': plugin
        }
        
        item.setData(0, Qt.ItemDataRole.UserRole, staff_data)
        
        print(f"REFRESH: Added staff '{staff_name}' with instrument_id '{instrument_id}', clef '{clef}', section '{section_name or ''}'")
        return item

    def _on_any_setting_changed(self):
        """Called whenever any setting is changed in the setup widget."""
        print("SETUP WIDGET: _on_any_setting_changed called")
        
        # Mark that there are unapplied changes
        self.has_unapplied_changes = True
        
        # IMPORTANT: Let the dialog's signal handlers handle immediate rendering
        # The signal handlers will call the dialog's apply_changes_immediate method
        # which has access to the document and can force proper rendering updates
        
        print("SETUP WIDGET: Signal handlers will handle immediate rendering")


class StaffAttributesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setWindowTitle("Staff Attributes")
        self.setModal(True)
        self.setMinimumWidth(400)

        # Create main layout
        layout = QVBoxLayout(self)

        # Create tab widget to organize different attributes
        tabs = QTabWidget()

        # Staff Type tab
        staff_type_tab = QWidget()
        staff_type_layout = QVBoxLayout(staff_type_tab)

        # Staff type combo
        self.staff_type_label = QLabel("Staff Type:")
        self.staff_type = QComboBox()
        self.staff_type.addItems(["Single Staff", "Grand Staff"])
        staff_type_layout.addWidget(self.staff_type_label)
        staff_type_layout.addWidget(self.staff_type)
        staff_type_layout.addStretch()

        tabs.addTab(staff_type_tab, "Staff Type")

        # Section tab
        section_tab = QWidget()
        section_layout = QVBoxLayout(section_tab)

        # Section selection
        self.section_label = QLabel("Current Section:")
        self.section_combo = QComboBox()
        self.section_combo.setEditable(True)  # Allow entering new sections
        section_layout.addWidget(self.section_label)
        section_layout.addWidget(self.section_combo)

        # Section management
        self.new_section_btn = QPushButton("New Section")
        self.remove_section_btn = QPushButton("Remove from Section")

        self.new_section_btn.clicked.connect(self.on_new_section)
        self.remove_section_btn.clicked.connect(self.on_remove_from_section)

        section_layout.addWidget(self.new_section_btn)
        section_layout.addWidget(self.remove_section_btn)
        section_layout.addStretch()

        tabs.addTab(section_tab, "Section")

        layout.addWidget(tabs)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Initialize state
        self.selected_section = ""

    def set_staff_type(self, staff_type):
        """Set the current staff type"""
        index = self.staff_type.findText(staff_type)
        if index >= 0:
            self.staff_type.setCurrentIndex(index)

    def get_staff_type(self):
        """Get the selected staff type"""
        return self.staff_type.currentText()

    def set_section(self, section):
        """Set the current section"""
        self.selected_section = section
        index = self.section_combo.findText(section)
        if index >= 0:
            self.section_combo.setCurrentIndex(index)
        else:
            self.section_combo.setEditText(section)

    def get_section(self):
        """Get the selected section"""
        return self.section_combo.currentText()

    def populate_sections(self, sections):
        """Populate the section combo with existing sections"""
        self.section_combo.clear()
        self.section_combo.addItem("")  # Empty option for no section
        if sections:
            self.section_combo.addItems(sections)

    def on_new_section(self):
        """Handle new section creation"""
        selected_items = self.staff_list.selectedItems()
        if not selected_items:
            return

        # Create and show section name input dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("New Section")
        dialog.setModal(True)
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        # Add label and text input
        label = QLabel("Enter section name:")
        section_name_edit = QLineEdit()
        layout.addWidget(label)
        layout.addWidget(section_name_edit)

        # Add OK and Cancel buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            section_name = section_name_edit.text().strip()
            if section_name:  # Only proceed if a name was entered
                # Update selected items with the new section
                for item in selected_items:
                    # Get the existing staff data to preserve all attributes
                    staff_data = item.data(0, Qt.ItemDataRole.UserRole)

                    # Important! Preserve ALL existing data, especially staff_type and clef
                    # Just update the section property
                    staff_data["section"] = section_name

                    # Keep track of existing staff type (internal format) and clef
                    staff_type = staff_data.get("staff_type", "")
                    clef = staff_data.get("clef", "")

                    print(
                        f"NEW SECTION: Preserving staff type '{staff_type}' and clef '{clef}' for {item.text(0)} in section '{section_name}'"
                    )

                    # Update UI display - only change the section column
                    item.setText(3, section_name)  # Update the Section column

                    # Keep all other data intact
                    item.setData(0, Qt.ItemDataRole.UserRole, staff_data)

                    # Mark that there are unapplied changes
                    self.has_unapplied_changes = True
                    self.staff_options_changed.emit(
                        self.staff_list.indexOfTopLevelItem(item), staff_data
                    )

                # Update the section dialog button states
                if hasattr(self, "section_dialog") and self.section_dialog:
                    self.section_dialog.update_button_states()

                # Apply changes immediately to show updates in pink mode
                print(
                    "SETUP WIDGET: Applying changes immediately to show section updates in setup mode"
                )
                options = self.get_setup_options()

                # Set a flag to force rendering in setup mode with 5 measures
                options["force_setup_mode"] = True
                options["measures_per_system"] = 5  # Force 5 measures for setup mode
                options["preserve_staff_types"] = True  # Explicitly flag to preserve staff types

                # DO NOT call self.apply_changes_immediate(options) directly!
                # Let the dialog's signal handlers handle immediate rendering
                # The staff_options_changed signal will trigger the dialog's handler

                print(
                    f"Added staff(s) to section '{section_name}' while preserving all staff attributes"
                )

    def on_remove_from_section(self):
        """Handle removing from section"""
        # Simply set empty selection
        self.section_combo.setCurrentIndex(0)  # First item is empty


# Keep existing SectionDialog and StaffTypeDialog for backwards compatibility,
# but they're not used in the new workflow


class LayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Layout Settings")
        self.setModal(True)
        self.setMinimumWidth(300)

        # Create main layout
        layout = QVBoxLayout(self)

        # Create form layout for settings
        form_layout = QFormLayout()

        # Staff spacing
        self.staff_spacing = QSpinBox()
        self.staff_spacing.setRange(20, 100)
        self.staff_spacing.setValue(40)
        self.staff_spacing.setSuffix(" px")
        form_layout.addRow("Staff Spacing:", self.staff_spacing)

        # System spacing
        self.system_spacing = QSpinBox()
        self.system_spacing.setRange(40, 200)
        self.system_spacing.setValue(80)
        self.system_spacing.setSuffix(" px")
        form_layout.addRow("System Spacing:", self.system_spacing)

        # Measures per system
        self.measures_per_system = QSpinBox()
        self.measures_per_system.setRange(1, 8)
        self.measures_per_system.setValue(4)
        form_layout.addRow("Measures per System:", self.measures_per_system)

        layout.addLayout(form_layout)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self):
        """Get the current settings"""
        return {
            "staff_spacing": self.staff_spacing.value(),
            "system_spacing": self.system_spacing.value(),
            "measures_per_system": self.measures_per_system.value(),
        }

    def set_settings(self, settings):
        """Set the current settings"""
        self.staff_spacing.setValue(settings.get("staff_spacing", 40))
        self.system_spacing.setValue(settings.get("system_spacing", 80))
        self.measures_per_system.setValue(settings.get("measures_per_system", 4))


class StaffTypeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Staff Type")
        self.setModal(True)
        self.setMinimumWidth(300)

        # Create main layout
        layout = QVBoxLayout(self)

        # Create form layout for settings
        form_layout = QFormLayout()

        # Staff type combo
        self.staff_type = QComboBox()
        self.staff_type.addItems(["Single Staff", "Grand Staff"])
        form_layout.addRow("Staff Type:", self.staff_type)

        layout.addLayout(form_layout)

        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_staff_type(self):
        """Get the selected staff type"""
        return self.staff_type.currentText()


class SectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.setWindowTitle("Section Management")
        self.setModal(True)
        self.setMinimumWidth(300)

        # Create main layout
        layout = QVBoxLayout(self)

        # Create buttons for section actions
        new_section_btn = QPushButton("New Section")
        add_to_section_btn = QPushButton("Add to Section")
        remove_from_section_btn = QPushButton("Remove from Section")

        # Connect buttons to actions
        new_section_btn.clicked.connect(self.parent_widget.on_new_section)
        add_to_section_btn.clicked.connect(self.parent_widget.on_add_to_section)
        remove_from_section_btn.clicked.connect(self.parent_widget.on_remove_from_section)

        # Add buttons to layout
        layout.addWidget(new_section_btn)
        layout.addWidget(add_to_section_btn)
        layout.addWidget(remove_from_section_btn)
