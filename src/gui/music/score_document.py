from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple, Union
from PyQt6.QtCore import QPointF, QObject, QSettings
from .staff_types import StaffType, StaffBase, SingleStaff, GrandStaff, SectionGroup, ScoreLayout
from .measure_object import MeasureObject
import copy

@dataclass
class ScoreDocument:
    """Class to manage the score document state"""
    layout: ScoreLayout
    filename: Optional[str] = None
    is_modified: bool = False
    view_mode: str = "page"  # "page", "continuous", "page_across", "page_down"
    zoom_level: float = 1.0
    
    def __init__(self):
        self.layout = ScoreLayout()
        self.layout.set_setup_mode(True)  # Start in setup mode
        self.section_map = {}  # Initialize section_map to store instrument-to-section mapping
        
        # Initialize measure system
        self.measures = {}  # FIXED: Dict of MeasureObject instances {measure_number: MeasureObject}
        self.num_measures = 32  # Default number of measures
        self.measures_per_system = 4  # Default measures per system for layout
        
        # Initialize undo/redo system
        self.undo_stack = []  # Stack of previous document states
        self.redo_stack = []  # Stack of future document states
        self.max_undo_steps = 50  # Maximum number of undo steps
        
        # Initialize graphical dashed barlines collection
        if not hasattr(self, 'graphical_dashed_barlines'):
            self.graphical_dashed_barlines = []
        
        # Load settings from QSettings for new documents
        qsettings = QSettings("ONOTE", "Preferences")
        self.settings = {}
        # List of relevant keys to copy from QSettings
        keys = [
            ('notation/max_measures_per_system', 4),
            ('layout/default_measures_per_system', 4),
            ('notation/show_measure_numbers', True),
            ('notation/measure_number_frequency', 'Every Measure'),
            ('notation/measure_number_position', 'Center'),
            ('notation/measure_numbers_vertical', 'Above System'),
            ('notation/measure_numbers_custom_interval', 1),
            ('notation/measure_numbers_font_size', 10),
            ('notation/measure_numbers_vertical_offset', -20),
            ('notation/measure_numbers_horizontal_offset', -34),
            ('notation/measure_numbers_font_color', '#000000'),
            ('notation/barline_numbering', False),
            ('notation/barline_number_font_size', 8),
            ('notation/barline_number_vertical_offset', -3),
            ('notation/barline_number_horizontal_offset', -3),
            ('notation/barline_numbers_font_color', '#800080'),
            # Layout settings are now handled by Preferences dialog
        ]
        for key, default in keys:
            value = qsettings.value(key, default)
            # CRITICAL FIX: Convert values to proper types
            if isinstance(default, bool):
                value = bool(value) if value is not None else default
            elif isinstance(default, int):
                value = int(value) if value is not None else default
            elif isinstance(default, float):
                value = float(value) if value is not None else default
            self.settings[key] = value
            print(f"DOCUMENT_INIT: Loaded {key} = {value} (type: {type(value).__name__})")
        
        # DEBUG: Check specific barline settings
        print(f"DOCUMENT_INIT: Barline color from QSettings: {qsettings.value('notation/barline_numbers_font_color', 'NOT_FOUND')}")
        print(f"DOCUMENT_INIT: Barline vertical offset from QSettings: {qsettings.value('notation/barline_number_vertical_offset', 'NOT_FOUND')}")
        print(f"DOCUMENT_INIT: Barline horizontal offset from QSettings: {qsettings.value('notation/barline_number_horizontal_offset', 'NOT_FOUND')}")
        # --- NEW: Apply page layout defaults from Preferences to self.layout ---
        # Read defaults from Preferences (not last-used Page Setup state)
        left_margin = float(qsettings.value('layout/default_left_margin', 25.0))
        right_margin = float(qsettings.value('layout/default_right_margin', 25.0))
        top_margin = float(qsettings.value('layout/default_top_margin', 20.0))
        bottom_margin = float(qsettings.value('layout/default_bottom_margin', 20.0))
        # Page size and orientation (robust to different keys and casing)
        page_type = qsettings.value('layout/default_page_size', None)
        if page_type is None:
            page_type = qsettings.value('layout/default_page_type', 'A4')
        orientation = str(qsettings.value('layout/default_orientation', 'Portrait'))
        orientation = 'Landscape' if str(orientation).lower().startswith('land') else 'Portrait'
        # Set layout margins (convert mm to pixels: 1mm ≈ 3.78px)
        MM_TO_PIXELS = 3.78
        self.layout.left_margin = int(left_margin * MM_TO_PIXELS)
        self.layout.right_margin = int(right_margin * MM_TO_PIXELS)
        self.layout.top_margin = int(top_margin * MM_TO_PIXELS)
        self.layout.bottom_margin = int(bottom_margin * MM_TO_PIXELS)
        # Set page size based on type and orientation
        if 'A4' in str(page_type):
            width_mm, height_mm = 210, 297
        elif 'A3' in str(page_type):
            width_mm, height_mm = 297, 420
        elif 'Letter' in str(page_type):
            width_mm, height_mm = 215.9, 279.4
        elif 'Legal' in str(page_type):
            width_mm, height_mm = 215.9, 355.6
        elif 'Tabloid' in str(page_type):
            width_mm, height_mm = 279.4, 431.8
        else:
            width_mm, height_mm = 210, 297  # Default to A4
        if orientation == 'Landscape':
            width_mm, height_mm = height_mm, width_mm
        self.layout.page_width = int(width_mm * MM_TO_PIXELS)
        self.layout.page_height = int(height_mm * MM_TO_PIXELS)
        print("DOCUMENT: Initialized empty document - no automatic measures and loaded settings from QSettings")
        # Ensure layout positions reflect the loaded margins and page size
        try:
            if hasattr(self.layout, '_update_positions'):
                self.layout._update_positions()
                print("DOCUMENT_INIT: Applied layout._update_positions() with preferences-based margins and page size")
        except Exception as e:
            print(f"DOCUMENT_INIT: _update_positions error: {e}")
        
    def _initialize_default_content(self):
        """Initialize the document with a default staff (directly under Score, not in a section)"""
        # Create a default single staff part
        default_instrument_id = "part"
        default_instrument_name = "Part"
        default_instrument_abbr = "Pt."
        
        # Create a single staff with treble clef
        default_staff = SingleStaff(
            instrument_id=default_instrument_id,
            instrument_name=default_instrument_name,
            instrument_abbr=default_instrument_abbr,
            clef="treble",
            key="C major / A minor (no sharps/flats)",
            time_signature="4/4"
        )
        
        # Explicitly set section to empty string to ensure no "Default" section is created
        default_staff.section = ""
        
        # Add staff directly to the score (not in any section)
        self.layout.add_staff(default_staff)
        
        # Store in section_map as an empty string (no section)
        self.section_map[default_instrument_id] = ""
        
        print(f"Initialized document with default {default_instrument_name} directly under Score (not in a section)")
        
        # Save initial state for undo/redo
        self.save_state("Initialize document with default content")
        
    def set_filename(self, filename: str):
        """Set the document filename"""
        self.filename = filename
        self.is_modified = False
        
    def set_modified(self, modified: bool):
        """Set the modified flag"""
        self.is_modified = modified
        
    def set_view_mode(self, mode: str):
        """Set the view mode"""
        if mode in ["page", "continuous", "page_across", "page_down"]:
            self.view_mode = mode
            
    def set_zoom_level(self, level: float):
        """Set the zoom level"""
        if 0.25 <= level <= 4.0:  # Limit zoom range
            self.zoom_level = level
            
    def add_section(self, section: SectionGroup):
        """Add a section to the score"""
        self.layout.add_section(section)
        self.is_modified = True
        
    def remove_section(self, index: int, keep_staves: bool = False):
        """Remove a section from the score
           If keep_staves is True, staves are moved to ungrouped_staves instead of being deleted"""
        if 0 <= index < len(self.layout.sections):
            section = self.layout.sections[index]
            self.layout.remove_section(section.name, keep_staves)
            self.is_modified = True
            
    def get_section(self, index: int) -> Optional[SectionGroup]:
        """Get a section by index"""
        if 0 <= index < len(self.layout.sections):
            return self.layout.sections[index]
        return None
        
    def get_section_count(self) -> int:
        """Get the number of sections"""
        return len(self.layout.sections)
        
    def get_ungrouped_staff_count(self) -> int:
        """Get the number of ungrouped staves (directly under Score)"""
        return len(self.layout.ungrouped_staves)
        
    def get_total_staff_count(self) -> int:
        """Get the total number of staves (both in sections and ungrouped)"""
        count = 0
        # Count staves in sections
        for section in self.layout.sections:
            count += len(section.staves)
        # Add ungrouped staves
        count += len(self.layout.ungrouped_staves)
        return count
        
    def get_staff_system_count(self) -> int:
        """Get the total number of staff systems, counting each grand staff as one"""
        return self.get_total_staff_count()  # Each entry in our staves list is one system
        
    def get_ungrouped_staff_at(self, index: int) -> Optional[Union[StaffBase, GrandStaff]]:
        """Get an ungrouped staff by index"""
        if 0 <= index < len(self.layout.ungrouped_staves):
            return self.layout.ungrouped_staves[index]
        return None
        
    def get_staff_at(self, section_index: int, staff_index: int) -> Optional[Union[StaffBase, GrandStaff]]:
        """Get a staff by section and staff indices"""
        section = self.get_section(section_index)
        if section and 0 <= staff_index < len(section.staves):
            return section.staves[staff_index]
        return None
        
    def update_staff(self, section_index: int, staff_index: int, staff: StaffBase):
        """Update a staff in a section"""
        section = self.get_section(section_index)
        if section and 0 <= staff_index < len(section.staves):
            section.staves[staff_index] = staff
            self.layout._update_positions()
            self.is_modified = True
            
    def update_ungrouped_staff(self, index: int, staff: StaffBase):
        """Update an ungrouped staff"""
        if 0 <= index < len(self.layout.ungrouped_staves):
            self.layout.ungrouped_staves[index] = staff
            self.layout._update_positions()
            self.is_modified = True
            
    def add_staff_to_section(self, staff: StaffBase, section_name: str):
        """Add a staff to a specific section"""
        self.layout.add_staff_to_section(staff, section_name)
        self.is_modified = True
        
    def add_ungrouped_staff(self, staff: StaffBase):
        """Add a staff directly to the score (not in any section)"""
        self.layout.add_staff(staff)
        self.is_modified = True
            
    def toggle_setup_mode(self):
        """Toggle between setup and edit modes"""
        self.layout.set_setup_mode(not self.layout.is_setup_mode)
        
    def get_background_color(self) -> str:
        """Get the background color based on mode"""
        return self.layout.background_color
        
    def apply_setup_options(self, options):
        print(f"[DEBUG] ScoreDocument.apply_setup_options called with options: {list(options.keys())}")
        # Apply options to the layout
        self.layout.apply_setup_options(options)
        
        # Save section map for future reference
        if 'section_map' in options:
            self.section_map = options['section_map']
            
        # Mark as modified
        self.is_modified = True
        
    def to_dict(self) -> dict:
        """Convert the document to a dictionary for serialization
        
        This is used to preserve the document state when switching modes.
        """
        data = {
            'filename': self.filename,
            'is_modified': self.is_modified,
            'view_mode': self.view_mode,
            'zoom_level': self.zoom_level,
            'section_map': self.section_map,
            # Store staves data
            'ungrouped_staves': [],
            'sections': []
        }
        
        # Include plugin_map if it exists
        if hasattr(self, 'plugin_map'):
            data['plugin_map'] = self.plugin_map
        
        # Include section_display_order if it exists
        if hasattr(self, 'section_display_order'):
            data['section_display_order'] = self.section_display_order
        
        # Store layout data
        if hasattr(self.layout, 'ungrouped_staves'):
            for staff in self.layout.ungrouped_staves:
                if hasattr(staff, 'to_dict'):
                    data['ungrouped_staves'].append(staff.to_dict())
                else:
                    # Fallback for staves without to_dict
                    staff_dict = {
                        'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                        'instrument_id': getattr(staff, 'instrument_id', ''),
                        'instrument_name': getattr(staff, 'instrument_name', ''),
                        'instrument_abbr': getattr(staff, 'instrument_abbr', ''),
                        'clef': getattr(staff, 'clef', 'treble'),
                        'key': getattr(staff, 'key', 'C major / A minor (no sharps/flats)'),
                        'time_signature': getattr(staff, 'time_signature', '4/4')
                    }
                    # Add plugin information if available
                    if hasattr(staff, 'plugin'):
                        staff_dict['plugin'] = staff.plugin
                    data['ungrouped_staves'].append(staff_dict)
        
        # Store sections data
        if hasattr(self.layout, 'sections'):
            for section in self.layout.sections:
                section_data = {
                    'name': getattr(section, 'name', ''),
                    'staves': []
                }
                
                # Include display_order_index if available
                if hasattr(section, 'display_order_index'):
                    section_data['display_order_index'] = section.display_order_index
                
                for staff in section.staves:
                    if hasattr(staff, 'to_dict'):
                        section_data['staves'].append(staff.to_dict())
                    else:
                        # Fallback for staves without to_dict
                        staff_dict = {
                            'staff_type': 'single_staff' if isinstance(staff, SingleStaff) else 'grand_staff',
                            'instrument_id': getattr(staff, 'instrument_id', ''),
                            'instrument_name': getattr(staff, 'instrument_name', ''),
                            'instrument_abbr': getattr(staff, 'instrument_abbr', ''),
                            'clef': getattr(staff, 'clef', 'treble'),
                            'key': getattr(staff, 'key', 'C major / A minor (no sharps/flats)'),
                            'time_signature': getattr(staff, 'time_signature', '4/4')
                        }
                        # Add plugin information if available
                        if hasattr(staff, 'plugin'):
                            staff_dict['plugin'] = staff.plugin
                        section_data['staves'].append(staff_dict)
                
                data['sections'].append(section_data)
        
        # Include notation data if present
        if hasattr(self, 'notation'):
            data['notation'] = self.notation
            
        # CRITICAL FIX: Include document settings (notation parameters, colors, etc.)
        if hasattr(self, 'settings') and self.settings:
            data['settings'] = self.settings
            print(f"DOCUMENT_SAVE: Saving {len(self.settings)} document settings with file")
            
        # Include measures data if present (serialize properly)
        if hasattr(self, 'measures') and self.measures:
            if isinstance(self.measures, dict):
                # Convert dict of measures to serializable format
                data['measures'] = {}
                for key, measure in self.measures.items():
                    if hasattr(measure, 'to_dict'):
                        data['measures'][str(key)] = measure.to_dict()
                    else:
                        # Basic measure data
                        data['measures'][str(key)] = {
                            'measure_number': getattr(measure, 'measure_number', key),
                            'end_x': getattr(measure, 'end_x', 160),
                            'barline_type': getattr(measure, 'barline_type', 'single'),
                            'selected': getattr(measure, 'selected', False),
                            'is_repeat_start': getattr(measure, 'is_repeat_start', False),
                            'is_repeat_end': getattr(measure, 'is_repeat_end', False),
                            'repeat_count': getattr(measure, 'repeat_count', None)
                        }
            else:
                # Convert list of measures to serializable format
                data['measures'] = []
                for measure in self.measures:
                    if hasattr(measure, 'to_dict'):
                        data['measures'].append(measure.to_dict())
                    else:
                        # Basic measure data
                        data['measures'].append({
                            'measure_number': getattr(measure, 'measure_number', 1),
                            'end_x': getattr(measure, 'end_x', 160),
                            'barline_type': getattr(measure, 'barline_type', 'single'),
                            'selected': getattr(measure, 'selected', False),
                            'is_repeat_start': getattr(measure, 'is_repeat_start', False),
                            'is_repeat_end': getattr(measure, 'is_repeat_end', False),
                            'repeat_count': getattr(measure, 'repeat_count', None)
                        })
        
        # Include graphical_dashed_barlines if they exist
        if hasattr(self, 'graphical_dashed_barlines') and self.graphical_dashed_barlines:
            data['graphical_dashed_barlines'] = []
            for dashed_barline in self.graphical_dashed_barlines:
                dashed_data = {
                    'x_position': getattr(dashed_barline, 'x_position', 0),
                    'barline_type': getattr(dashed_barline, 'barline_type', 'dashed'),
                    'measure_number': getattr(dashed_barline, 'measure_number', 'dashed_0'),
                    'selected': getattr(dashed_barline, 'selected', False),
                    'is_graphical_dashed': getattr(dashed_barline, 'is_graphical_dashed', True)
                }
                data['graphical_dashed_barlines'].append(dashed_data)
            
        return data
        
    @classmethod
    def from_dict(cls, data: dict) -> 'ScoreDocument':
        """Create a ScoreDocument from a dictionary
        
        This is used to restore the document state when switching modes.
        """
        document = cls()
        
        # Restore basic properties
        document.filename = data.get('filename')
        document.is_modified = data.get('is_modified', False)
        document.view_mode = data.get('view_mode', 'page')
        document.zoom_level = data.get('zoom_level', 1.0)
        document.section_map = data.get('section_map', {})
        
        # Restore plugin_map if available
        if 'plugin_map' in data:
            document.plugin_map = data['plugin_map']
        
        # Restore section_display_order if available
        if 'section_display_order' in data:
            document.section_display_order = data['section_display_order']
        
        # Clear the initial default content
        document.layout.ungrouped_staves = []
        document.layout.sections = []
        
        # Restore ungrouped staves
        for staff_index, staff_data in enumerate(data.get('ungrouped_staves', [])):
            staff_type = staff_data.get('staff_type', 'single_staff')
            
            if staff_type == 'single_staff':
                staff = SingleStaff(
                    instrument_id=staff_data.get('instrument_id', ''),
                    instrument_name=staff_data.get('instrument_name', ''),
                    instrument_abbr=staff_data.get('instrument_abbr', ''),
                    clef=staff_data.get('clef', 'treble'),
                    key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                    time_signature=staff_data.get('time_signature', '4/4')
                )
                # Set plugin if available
                if 'plugin' in staff_data:
                    staff.plugin = staff_data['plugin']
                
                # CRITICAL FIX: Assign display_order_index based on file position
                # This ensures ungrouped staves maintain their original order relative to sections
                if 'display_order_index' in staff_data:
                    staff.display_order_index = staff_data['display_order_index']
                    print(f"FILE_LOADING: Restored ungrouped staff '{staff.instrument_name}' with saved display_order_index = {staff.display_order_index}")
                else:
                    # For older files without explicit display_order_index, assign based on file position
                    staff.display_order_index = staff_index
                    print(f"FILE_LOADING: Assigned ungrouped staff '{staff.instrument_name}' display_order_index = {staff_index} (file order fallback)")
                
                document.layout.add_staff(staff)
            elif staff_type == 'grand_staff':
                # Handle grand staff
                top_staff = SingleStaff(
                    instrument_id=staff_data.get('instrument_id', ''),
                    instrument_name=staff_data.get('instrument_name', ''),
                    instrument_abbr=staff_data.get('instrument_abbr', ''),
                    clef='treble',
                    key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                    time_signature=staff_data.get('time_signature', '4/4')
                )
                
                bottom_staff = SingleStaff(
                    instrument_id=staff_data.get('instrument_id', ''),
                    instrument_name=staff_data.get('instrument_name', ''),
                    instrument_abbr=staff_data.get('instrument_abbr', ''),
                    clef='bass',
                    key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                    time_signature=staff_data.get('time_signature', '4/4')
                )
                
                grand_staff = GrandStaff(
                    instrument_id=staff_data.get('instrument_id', ''),
                    instrument_name=staff_data.get('instrument_name', ''),
                    instrument_abbr=staff_data.get('instrument_abbr', ''),
                    clef=staff_data.get('clef', 'treble'),  # Grand staff default clef
                    key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                    time_signature=staff_data.get('time_signature', '4/4'),
                    top_staff=top_staff,
                    bottom_staff=bottom_staff
                )
                
                # Set plugin if available
                if 'plugin' in staff_data:
                    grand_staff.plugin = staff_data['plugin']
                    top_staff.plugin = staff_data['plugin']
                    bottom_staff.plugin = staff_data['plugin']
                
                # CRITICAL FIX: Assign display_order_index based on file position
                # This ensures ungrouped grand staves maintain their original order relative to sections
                if 'display_order_index' in staff_data:
                    grand_staff.display_order_index = staff_data['display_order_index']
                    print(f"FILE_LOADING: Restored ungrouped grand staff '{grand_staff.instrument_name}' with saved display_order_index = {grand_staff.display_order_index}")
                else:
                    # For older files without explicit display_order_index, assign based on file position
                    grand_staff.display_order_index = staff_index
                    print(f"FILE_LOADING: Assigned ungrouped grand staff '{grand_staff.instrument_name}' display_order_index = {staff_index} (file order fallback)")
                
                document.layout.add_staff(grand_staff)
        
        # Restore sections
        for section_index, section_data in enumerate(data.get('sections', [])):
            section_name = section_data.get('name', '')
            
            # Create section
            section = SectionGroup(section_name)
            # Restore display_order_index if available, otherwise assign based on file order
            if 'display_order_index' in section_data:
                section.display_order_index = section_data['display_order_index']
                print(f"FILE_LOADING: Restored section '{section_name}' with saved display_order_index = {section.display_order_index}")
            else:
                # CRITICAL FIX: If no display_order_index is saved, assign based on file order
                # This preserves the original section ordering when loading older files
                section.display_order_index = section_index
                print(f"FILE_LOADING: Assigned section '{section_name}' display_order_index = {section_index} (file order fallback)")
            document.layout.add_section(section)
            
            # Add staves to section
            for staff_data in section_data.get('staves', []):
                staff_type = staff_data.get('staff_type', 'single_staff')
                
                if staff_type == 'single_staff':
                    staff = SingleStaff(
                        instrument_id=staff_data.get('instrument_id', ''),
                        instrument_name=staff_data.get('instrument_name', ''),
                        instrument_abbr=staff_data.get('instrument_abbr', ''),
                        clef=staff_data.get('clef', 'treble'),
                        key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    # Set plugin if available
                    if 'plugin' in staff_data:
                        staff.plugin = staff_data['plugin']
                    document.layout.add_staff_to_section(staff, section_name)
                elif staff_type == 'grand_staff':
                    # Handle grand staff
                    top_staff = SingleStaff(
                        instrument_id=staff_data.get('instrument_id', ''),
                        instrument_name=staff_data.get('instrument_name', ''),
                        instrument_abbr=staff_data.get('instrument_abbr', ''),
                        clef='treble',
                        key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    
                    bottom_staff = SingleStaff(
                        instrument_id=staff_data.get('instrument_id', ''),
                        instrument_name=staff_data.get('instrument_name', ''),
                        instrument_abbr=staff_data.get('instrument_abbr', ''),
                        clef='bass',
                        key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    
                    grand_staff = GrandStaff(
                        instrument_id=staff_data.get('instrument_id', ''),
                        instrument_name=staff_data.get('instrument_name', ''),
                        instrument_abbr=staff_data.get('instrument_abbr', ''),
                        clef=staff_data.get('clef', 'treble'),  # Grand staff default clef
                        key=staff_data.get('key', 'C major / A minor (no sharps/flats)'),
                        time_signature=staff_data.get('time_signature', '4/4'),
                        top_staff=top_staff,
                        bottom_staff=bottom_staff
                    )
                    
                    # Set plugin if available
                    if 'plugin' in staff_data:
                        grand_staff.plugin = staff_data['plugin']
                        top_staff.plugin = staff_data['plugin']
                        bottom_staff.plugin = staff_data['plugin']
                    
                    document.layout.add_staff_to_section(grand_staff, section_name)
        
        # Restore notation data if present
        if 'notation' in data:
            document.notation = data['notation']
            
        # CRITICAL FIX: Restore document settings (notation parameters, colors, etc.)
        if 'settings' in data:
            document.settings = data['settings']
            print(f"DOCUMENT_LOAD: Restored {len(document.settings)} document settings from file")
        else:
            # If settings missing, load from QSettings
            from PyQt6.QtCore import QSettings
            qsettings = QSettings("ONOTE", "Preferences")
            document.settings = {}
            keys = [
                ('notation/max_measures_per_system', 4),
                ('layout/default_measures_per_system', 4),
                ('notation/show_measure_numbers', True),
                ('notation/measure_number_frequency', 'Every Measure'),
                ('notation/measure_number_position', 'Center'),
                ('notation/measure_numbers_vertical', 'Above System'),
                ('notation/measure_numbers_custom_interval', 1),
                ('notation/measure_numbers_font_size', 10),
                ('notation/measure_numbers_vertical_offset', -20),
                ('notation/measure_numbers_horizontal_offset', -34),
                ('notation/measure_numbers_font_color', '#000000'),
                ('notation/barline_numbering', False),
                ('notation/barline_number_font_size', 8),
                ('notation/barline_number_vertical_offset', -3),
                ('notation/barline_number_horizontal_offset', -3),
                ('notation/barline_numbers_font_color', '#800080'),
                # Layout settings are now handled by Preferences dialog
            ]
            for key, default in keys:
                document.settings[key] = qsettings.value(key, default)
            print("DOCUMENT_LOAD: No settings in file, loaded defaults from QSettings")
        
        # Restore measures data if present
        if 'measures' in data:
            measures_data = data['measures']
            if isinstance(measures_data, dict):
                # Restore dict format measures
                document.measures = {}
                for key, measure_data in measures_data.items():
                    from .measure_object import MeasureObject
                    if isinstance(measure_data, dict):
                        measure = MeasureObject.from_dict(measure_data)
                    else:
                        # Fallback for simple data
                        measure = MeasureObject(int(key) if key.isdigit() else 1)
                    document.measures[int(key) if key.isdigit() else key] = measure
            elif isinstance(measures_data, list):
                # Restore list format measures as dictionary
                document.measures = {}
                for i, measure_data in enumerate(measures_data):
                    from .measure_object import MeasureObject
                    if isinstance(measure_data, dict):
                        measure = MeasureObject.from_dict(measure_data)
                    else:
                        # Fallback for simple data
                        measure = MeasureObject(1)
                    document.measures[i + 1] = measure
            else:
                # Fallback for other formats
                document.measures = {}
        
        # Restore graphical_dashed_barlines if present
        if 'graphical_dashed_barlines' in data:
            document.graphical_dashed_barlines = []
            for dashed_data in data['graphical_dashed_barlines']:
                # Create graphical dashed barline object
                class GraphicalDashedBarline:
                    def __init__(self, data):
                        self.x_position = data.get('x_position', 0)
                        self.barline_type = data.get('barline_type', 'dashed')
                        self.measure_number = data.get('measure_number', 'dashed_0')
                        self.selected = data.get('selected', False)
                        self.is_graphical_dashed = data.get('is_graphical_dashed', True)
                        
                    def contains_x_position(self, x_pos):
                        """Check if this barline contains the given x position"""
                        return abs(self.x_position - x_pos) < 50  # Tolerance for selection
                        
                    def set_selected(self, selected):
                        self.selected = selected
                
                dashed_barline = GraphicalDashedBarline(dashed_data)
                document.graphical_dashed_barlines.append(dashed_barline)
            
        # Update layout positions - will correctly sort sections internally
        document.layout._update_positions()
        
        return document 

    def is_in_setup_mode(self) -> bool:
        """Check if the score is in setup mode"""
        return self.layout.is_setup_mode 

    # Measure Management Methods
    def set_measures(self, measures):
        """Set measure objects, accepting list/dict of MeasureObject or dicts.
        Normalizes to a dict keyed by measure_number → MeasureObject.
        """
        normalized = {}
        try:
            from .measure_object import MeasureObject
        except Exception:
            MeasureObject = None

        if isinstance(measures, dict):
            # Ensure values are MeasureObject-like
            for k, v in measures.items():
                if isinstance(v, dict) and MeasureObject is not None:
                    mnum = int(v.get('measure_number', k))
                    m = MeasureObject(mnum)
                    if 'barline_type' in v:
                        m.barline_type = v['barline_type']
                    if 'end_x' in v:
                        m.end_x = v['end_x']
                    if 'x_position' in v:
                        m.x_position = v['x_position']
                    normalized[int(mnum)] = m
                else:
                    num = int(getattr(v, 'measure_number', k))
                    normalized[num] = v
        elif isinstance(measures, list):
            for i, item in enumerate(measures, start=1):
                if hasattr(item, 'measure_number'):
                    num = int(getattr(item, 'measure_number', i))
                    normalized[num] = item
                else:
                    # Dict or unknown payload
                    if isinstance(item, dict) and MeasureObject is not None:
                        num = int(item.get('measure_number', i))
                        m = MeasureObject(num)
                        if 'barline_type' in item:
                            m.barline_type = item['barline_type']
                        if 'end_x' in item:
                            m.end_x = item['end_x']
                        if 'x_position' in item:
                            m.x_position = item['x_position']
                        normalized[num] = m
                    else:
                        # Fallback: store as-is under enumerated key
                        normalized[i] = item
        else:
            print(f"[WARN] set_measures received unsupported type: {type(measures)}; keeping existing measures")
            normalized = getattr(self, 'measures', {}) or {}

        self.measures = normalized
        self.num_measures = len(self.measures)
        self.is_modified = True
        print(f"Document updated with {self.num_measures} measure objects (normalized dict)")
        
    def get_measures(self):
        """Get all measure objects as a list in measure_number order"""
        if isinstance(self.measures, dict):
            return [self.measures[k] for k in sorted(self.measures.keys())]
        return list(self.measures) if self.measures else []
        
    def get_measure_count(self):
        """Get the current number of measures"""
        if isinstance(self.measures, dict):
            return len(self.measures)
        return len(self.measures) if self.measures else int(getattr(self, 'num_measures', 0))
        
    def get_measure_at_index(self, index):
        """Get measure object at specific 0-based index in order"""
        measures = self.get_measures()
        if 0 <= index < len(measures):
            return measures[index]
        return None
        
    def update_measure(self, measure_number, properties):
        """Update a specific measure with new properties"""
        if isinstance(self.measures, dict):
            m = self.measures.get(int(measure_number))
            if m is None:
                return False
            for prop, value in properties.items():
                if hasattr(m, prop):
                    setattr(m, prop, value)
            self.is_modified = True
            print(f"Updated measure {measure_number}: {properties}")
            return True
        else:
            for measure in (self.measures or []):
                if hasattr(measure, 'measure_number') and int(measure.measure_number) == int(measure_number):
                    for prop, value in properties.items():
                        if hasattr(measure, prop):
                            setattr(measure, prop, value)
                    self.is_modified = True
                    print(f"Updated measure {measure_number}: {properties}")
                    return True
        return False
        
    def get_measures_in_range(self, start_measure, end_measure):
        """Get measures in a specific range (inclusive)"""
        result = []
        for measure in self.measures:
            if hasattr(measure, 'measure_number'):
                measure_num = measure.measure_number
                if start_measure <= measure_num <= end_measure:
                    result.append(measure)
        return sorted(result, key=lambda m: m.measure_number)
        
    def add_measure(self, measure):
        """Add a measure to the document in the correct position"""
        if not hasattr(self, 'measures') or self.measures is None:
            self.measures = []
            
        # Find the correct position to insert based on measure end_x or measure_number
        insert_index = len(self.measures)
        
        if hasattr(measure, 'end_x'):
            # Insert based on x position
            for i, existing_measure in enumerate(self.measures):
                if hasattr(existing_measure, 'end_x') and existing_measure.end_x > measure.end_x:
                    insert_index = i
                    break
        elif hasattr(measure, 'measure_number'):
            # Insert based on measure number
            for i, existing_measure in enumerate(self.measures):
                if hasattr(existing_measure, 'measure_number') and existing_measure.measure_number > measure.measure_number:
                    insert_index = i
                    break
        
        # Insert the measure at the correct position
        self.measures.insert(insert_index, measure)
        
        # Renumber measures after insertion
        for i, m in enumerate(self.measures):
            if hasattr(m, 'measure_number'):
                m.measure_number = i + 1
                
        self.is_modified = True
        print(f"DOCUMENT: Added measure at position {insert_index}, total measures: {len(self.measures)}")
        
    def remove_measure(self, measure_index):
        """Remove a measure by index"""
        if 0 <= measure_index < len(self.measures):
            removed_measure = self.measures.pop(measure_index)
            
            # Renumber remaining measures
            for i, m in enumerate(self.measures):
                if hasattr(m, 'measure_number'):
                    m.measure_number = i + 1
                    
            self.is_modified = True
            print(f"DOCUMENT: Removed measure at index {measure_index}, total measures: {len(self.measures)}")
            return removed_measure
        return None

    def calculate_measure_positions(self, system_idx=0):
        """Calculate the x-positions of measures for coordinate system and selection"""
        # Use renderer constants for consistent positioning
        # This method provides the coordinate system that the selection system will use
        
        # Get basic layout constants
        page_width = 800  # TODO: Get from renderer
        left_margin = 50  # TODO: Get from renderer  
        right_margin = 50  # TODO: Get from renderer
        barline_0_offset = 100  # TODO: Get from renderer's dynamic offset
        
        # Calculate available width for measures
        staff_left_x = left_margin + barline_0_offset
        staff_right_x = page_width - right_margin
        available_width = staff_right_x - staff_left_x
        
        # Calculate measure positions (6 measures per system)
        measures_per_system = 6
        measure_width = available_width / measures_per_system
        
        measure_positions = []
        start_measure_idx = system_idx * measures_per_system
        
        for i in range(measures_per_system):
            measure_idx = start_measure_idx + i
            if measure_idx >= len(self.measures):
                break
                
            # Calculate measure boundaries
            left_x = staff_left_x + (i * measure_width)
            right_x = left_x + measure_width
            
            measure_positions.append({
                'measure_index': measure_idx,
                'measure_number': measure_idx + 1,
                'left_x': left_x,
                'right_x': right_x,
                'center_x': (left_x + right_x) / 2,
                'width': measure_width
            })
            
        return measure_positions 

    def find_closest_barline(self, point: QPointF, threshold: float = 10.0) -> Optional[MeasureObject]:
        """Find the closest barline to the given point"""
        closest_barline = None
        min_distance = float('inf')
        
        for measure in self.measures:
            # Calculate distance to barline
            distance = abs(measure.end_x - point.x())
            if distance < min_distance and distance < threshold:
                min_distance = distance
                closest_barline = measure
        
        return closest_barline

    def find_selected_barline(self) -> Optional[MeasureObject]:
        """Find the currently selected barline"""
        for measure in self.measures:
            if measure.selected:
                return measure
        return None

    def deselect_all_barlines(self):
        """Deselect all barlines"""
        for measure in self.measures:
            measure.selected = False

    def remove_barline(self, barline: MeasureObject):
        """Remove a barline and merge measures if necessary"""
        if barline in self.measures:
            index = self.measures.index(barline)
            if index > 0:  # Don't remove the first barline
                # Merge the current measure with the previous one
                prev_measure = self.measures[index - 1]
                prev_measure.end_x = barline.end_x
                prev_measure.width = barline.end_x - prev_measure.end_x
                
                # Remove the current measure
                self.measures.pop(index)
                
                # Update measure numbers
                self.update_measure_numbers()

    def update_measure_numbers(self):
        """Update measure numbers after changes"""
        for i, measure in enumerate(self.measures):
            measure.measure_number = i + 1
    
    def save_state(self, operation_description="Document operation"):
        """Save the current document state for undo/redo
        
        Args:
            operation_description: Description of the operation being performed
        """
        try:
            # Create a safe copy of the current state using safe attribute copying
            current_state = {
                'operation_description': operation_description,
                'layout': self._safe_copy_layout(),
                'measures': self._safe_copy_measures(),
                'graphical_dashed_barlines': copy.deepcopy(getattr(self, 'graphical_dashed_barlines', [])),
                'section_map': copy.deepcopy(self.section_map),
                'num_measures': int(self.num_measures),
                'measures_per_system': int(self.measures_per_system),
                'filename': str(self.filename) if self.filename else None,
                'is_modified': bool(self.is_modified),
                'view_mode': str(self.view_mode),
                'zoom_level': float(self.zoom_level)
            }
            
            # Add to undo stack
            self.undo_stack.append(current_state)
            
            # Clear redo stack when new operation is performed
            self.redo_stack.clear()
            
            # Limit undo stack size
            if len(self.undo_stack) > self.max_undo_steps:
                self.undo_stack.pop(0)
            
            print(f"UNDO_SYSTEM: Saved state - {operation_description} (Stack size: {len(self.undo_stack)})")
            return True
            
        except Exception as e:
            print(f"UNDO_SYSTEM: Failed to save state - {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def undo(self):
        """Undo the last operation
        
        Returns:
            bool: True if undo was successful, False otherwise
        """
        if not self.undo_stack:
            print("UNDO: No undo states available")
            return False
        
        try:
            # Save current state to redo stack before undoing
            current_state = {
                'operation_description': "Current state before undo",
                'layout': self._safe_copy_layout(),
                'measures': self._safe_copy_measures(),
                'graphical_dashed_barlines': copy.deepcopy(getattr(self, 'graphical_dashed_barlines', [])),
                'section_map': copy.deepcopy(self.section_map),
                'num_measures': int(self.num_measures),
                'measures_per_system': int(self.measures_per_system),
                'filename': str(self.filename) if self.filename else None,
                'is_modified': bool(self.is_modified),
                'view_mode': str(self.view_mode),
                'zoom_level': float(self.zoom_level)
            }
            self.redo_stack.append(current_state)
            
            # Get the previous state
            previous_state = self.undo_stack.pop()
            
            # Restore the previous state
            self._restore_state(previous_state)
            
            print(f"UNDO: Successfully restored state - {previous_state['operation_description']}")
            return True
            
        except Exception as e:
            print(f"UNDO: Failed to undo - {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def redo(self):
        """Redo the next operation
        
        Returns:
            bool: True if redo was successful, False otherwise
        """
        if not self.redo_stack:
            print("REDO: No redo states available")
            return False
        
        try:
            # Get the next state from redo stack
            next_state = self.redo_stack.pop()
            
            # Save current state to undo stack BEFORE restoring
            # This allows proper undo of the redo operation
            current_state = {
                'operation_description': f"State before redo: {next_state.get('operation_description', 'Unknown')}",
                'layout': self._safe_copy_layout(),
                'measures': self._safe_copy_measures(),
                'graphical_dashed_barlines': copy.deepcopy(getattr(self, 'graphical_dashed_barlines', [])),
                'section_map': copy.deepcopy(self.section_map),
                'num_measures': int(self.num_measures),
                'measures_per_system': int(self.measures_per_system),
                'filename': str(self.filename) if self.filename else None,
                'is_modified': bool(self.is_modified),
                'view_mode': str(self.view_mode),
                'zoom_level': float(self.zoom_level)
            }
            self.undo_stack.append(current_state)
            
            # Restore the next state
            self._restore_state(next_state)
            
            print(f"REDO: Successfully restored state - {next_state['operation_description']}")
            print(f"REDO: Undo stack size: {len(self.undo_stack)}, Redo stack size: {len(self.redo_stack)}")
            return True
            
        except Exception as e:
            print(f"REDO: Failed to redo - {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _safe_copy_layout(self):
        """Safely copy the layout object avoiding problematic references"""
        try:
            return copy.deepcopy(self.layout)
        except Exception as e:
            print(f"UNDO_SYSTEM: Failed to deep copy layout, using fallback: {e}")
            # Fallback: create a new layout and copy basic properties
            from .score_layout import ScoreLayout
            new_layout = ScoreLayout()
            
            # Copy basic properties
            if hasattr(self.layout, 'is_setup_mode'):
                new_layout.is_setup_mode = self.layout.is_setup_mode
            if hasattr(self.layout, 'background_color'):
                new_layout.background_color = self.layout.background_color
            
            # Copy staves and sections with safe copying
            if hasattr(self.layout, 'ungrouped_staves'):
                new_layout.ungrouped_staves = copy.deepcopy(self.layout.ungrouped_staves)
            if hasattr(self.layout, 'sections'):
                new_layout.sections = copy.deepcopy(self.layout.sections)
                
            return new_layout
    
    def _safe_copy_measures(self):
        """Safely copy the measures list avoiding problematic references"""
        try:
            if not hasattr(self, 'measures') or not self.measures:
                return []
            return copy.deepcopy(self.measures)
        except Exception as e:
            print(f"UNDO_SYSTEM: Failed to deep copy measures, using fallback: {e}")
            # Fallback: manually copy each measure
            safe_measures = []
            for measure in self.measures:
                try:
                    safe_measures.append(copy.deepcopy(measure))
                except Exception as measure_error:
                    print(f"UNDO_SYSTEM: Skipping problematic measure: {measure_error}")
                    continue
            return safe_measures

    def _restore_state(self, state):
        """Restore the document to a previous state
        
        Args:
            state: Dictionary containing the document state to restore
        """
        # Restore layout
        self.layout = state['layout']
        
        # Restore measures
        self.measures = state.get('measures', [])
        
        # Restore graphical dashed barlines
        if 'graphical_dashed_barlines' in state:
            self.graphical_dashed_barlines = state['graphical_dashed_barlines']
        else:
            self.graphical_dashed_barlines = []
        
        # Restore other properties
        self.section_map = state.get('section_map', {})
        self.num_measures = state.get('num_measures', 32)
        self.measures_per_system = state.get('measures_per_system', 4)
        self.filename = state.get('filename')
        self.is_modified = state.get('is_modified', False)
        self.view_mode = state.get('view_mode', 'page')
        self.zoom_level = state.get('zoom_level', 1.0)
        
        print(f"UNDO_SYSTEM: Restored document state with {len(self.measures)} measures and {len(getattr(self, 'graphical_dashed_barlines', []))} dashed barlines")
    
    def can_undo(self):
        """Check if undo is available
        
        Returns:
            bool: True if undo is available, False otherwise
        """
        return len(self.undo_stack) > 0
    
    def can_redo(self):
        """Check if redo is available
        
        Returns:
            bool: True if redo is available, False otherwise
        """
        return len(self.redo_stack) > 0
    
    def get_undo_description(self):
        """Get description of the next undo operation
        
        Returns:
            str: Description of the operation that would be undone
        """
        if self.undo_stack:
            return self.undo_stack[-1].get('operation_description', 'Unknown operation')
        return None
    
    def get_redo_description(self):
        """Get description of the next redo operation
        
        Returns:
            str: Description of the operation that would be redone
        """
        if self.redo_stack:
            return self.redo_stack[-1].get('operation_description', 'Unknown operation')
        return None 