from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import uuid

class StaffType(Enum):
    """Types of staff systems available in the score"""
    SINGLE = "single_staff"
    GRAND = "grand_staff"

class StaffBase:
    """Base class for all staff types"""
    
    def __init__(self, instrument_id="", instrument_name="", instrument_abbr=""):
        """Initialize a staff base object"""
        # Generate a unique ID (needed for notation settings persistence)
        self.id = str(uuid.uuid4())
        
        # Store instrument information
        self.instrument_id = instrument_id or instrument_name.lower().replace(' ', '_')
        self.instrument_name = instrument_name
        self.instrument_abbr = instrument_abbr or instrument_name[:3].upper()
        
        # Initialize required attributes
        self.clef = "treble"  # Default clef
        self.key = "C major / A minor (no sharps/flats)"  # Default key
        self.time_signature = "4/4"  # Default time signature
        self.type = None  # Will be set by subclasses
        self.is_visible = True
        self.y_position = 0
        self.height = 32  # STAFF_HEIGHT
        self.spacing = 50  # STAFF_SPACING
        self.section = ""  # Name of the section this staff belongs to, empty if directly under Score
        self.plugin = "Default"  # Default plugin/instrument sound
        
        # CRITICAL FIX: Initialize display_order_index to 0 instead of letting it default to 999999
        self.display_order_index = 0
        
        # Store instance type
        self.is_single_staff = False
        self.is_grand_staff = False
        
        # Initialize notation settings
        self.notation_settings = {}
        
    def copy_notation_settings(self, other_staff):
        """Copy notation settings from another staff"""
        if hasattr(other_staff, 'notation_settings') and other_staff.notation_settings:
            self.notation_settings = {}
            # Deep copy the notation settings to ensure independence
            import copy
            self.notation_settings = copy.deepcopy(other_staff.notation_settings)
            print(f"Copied notation settings from staff {other_staff.instrument_name} to {self.instrument_name}")
            
    def to_dict(self):
        """Convert staff to dictionary for serialization"""
        data = {
            'id': self.id,
            'instrument_id': self.instrument_id,
            'instrument_name': self.instrument_name,
            'instrument_abbr': self.instrument_abbr,
            'clef': self.clef if hasattr(self, 'clef') else 'treble',
            'key': self.key if hasattr(self, 'key') else 'C major / A minor (no sharps/flats)',
            'time_signature': self.time_signature if hasattr(self, 'time_signature') else '4/4',
            'is_visible': self.is_visible,
            'section': self.section,
            'plugin': self.plugin  # Include plugin information
        }
        
        # Add notation settings if present
        if hasattr(self, 'notation_settings') and self.notation_settings:
            import copy
            data['notation_settings'] = copy.deepcopy(self.notation_settings)
        
        return data

class SingleStaff(StaffBase):
    """Single staff for instruments like flute, violin, etc."""
    
    def __init__(self, instrument_id="", instrument_name="", instrument_abbr="", 
                clef="treble", key="C major / A minor (no sharps/flats)", 
                time_signature="4/4", section=None):
        """Initialize a single staff"""
        super().__init__(instrument_id, instrument_name, instrument_abbr)
        
        # Set the type
        self.type = StaffType.SINGLE
        
        # Set number of lines
        self.num_lines = 5
        
        # Debug output for bass clef detection
        if clef == "bass":
            print(f"CREATING BASS CLEF STAFF: '{instrument_name}' (ID: {instrument_id})")
        
        # Store the instrument and clef information
        self.clef = clef
        self.key = key
        self.time_signature = time_signature
        self.section = section  # Name of the section this staff belongs to
        
        # Y-position and height (will be set during layout)
        self.y_position = 0
        self.height = 32  # Default height in pixels for a single staff
        
        # Flag this as a single staff
        self.is_single_staff = True
        
    @classmethod
    def from_dict(cls, data):
        """Create a SingleStaff from a dictionary"""
        staff = cls(
            instrument_id=data.get('instrument_id', ''),
            instrument_name=data.get('instrument_name', ''),
            instrument_abbr=data.get('instrument_abbr', ''),
            clef=data.get('clef', 'treble'),
            key=data.get('key', 'C major / A minor (no sharps/flats)'),
            time_signature=data.get('time_signature', '4/4'),
            section=data.get('section', None)
        )
        
        # Preserve ID if provided
        if 'id' in data:
            staff.id = data['id']
        
        # Set plugin if provided
        if 'plugin' in data:
            staff.plugin = data['plugin']
            
        # Copy notation settings if present
        if 'notation_settings' in data:
            import copy
            staff.notation_settings = copy.deepcopy(data['notation_settings'])
            print(f"Restored notation settings for {staff.instrument_name} from dictionary")
            
        return staff

class GrandStaff(StaffBase):
    """Grand staff for keyboard instruments"""
    
    def __init__(self, instrument_id="", instrument_name="", instrument_abbr="", 
                clef="", key="C major / A minor (no sharps/flats)", 
                time_signature="4/4", section=None, 
                top_staff=None, bottom_staff=None):
        """Initialize a grand staff"""
        super().__init__(instrument_id, instrument_name, instrument_abbr)
        
        # Set the type
        self.type = StaffType.GRAND
        
        # Store the music information (key and time signature are shared)
        self.key = key
        self.time_signature = time_signature
        self.section = section  # Name of the section this staff belongs to
        
        # Initialize grand staff specific attributes
        self.is_visible = True
        self.y_position = 0
        self.height = 96  # 2 * 32 staff height + 32 inner spacing
        self.spacing = 50  # Normal spacing (same as single staves)
        self.brace_y_start = 0
        self.brace_y_end = 0
        self.instrument_name_y = 0
        
        # Create top and bottom staves if not provided
        if top_staff is None:
            self.top_staff = SingleStaff(
                instrument_id=instrument_id,
                instrument_name=instrument_name,
                instrument_abbr=instrument_abbr,
                clef="treble",
                key=key,
                time_signature=time_signature,
                section=section
            )
        else:
            self.top_staff = top_staff
            
        if bottom_staff is None:
            self.bottom_staff = SingleStaff(
                instrument_id=instrument_id,
                instrument_name=instrument_name,
                instrument_abbr=instrument_abbr,
                clef="bass",
                key=key,
                time_signature=time_signature,
                section=section
            )
        else:
            self.bottom_staff = bottom_staff
        
        # The grand staff has a reference to shared clef, but it's not used for rendering
        self.clef = clef or "grand_staff"
        
        # Flag this as a grand staff
        self.is_grand_staff = True
        
    @classmethod
    def from_dict(cls, data):
        """Create a GrandStaff from a dictionary"""
        # Create the top and bottom staves first
        top_data = data.get('top_staff', {})
        top_data.update({
            'instrument_id': data.get('instrument_id', ''),
            'instrument_name': data.get('instrument_name', ''),
            'instrument_abbr': data.get('instrument_abbr', ''),
            'clef': 'treble',
            'key': data.get('key', 'C major / A minor (no sharps/flats)'),
            'time_signature': data.get('time_signature', '4/4'),
            'section': data.get('section', None)
        })
        top_staff = SingleStaff.from_dict(top_data)
        
        bottom_data = data.get('bottom_staff', {})
        bottom_data.update({
            'instrument_id': data.get('instrument_id', ''),
            'instrument_name': data.get('instrument_name', ''),
            'instrument_abbr': data.get('instrument_abbr', ''),
            'clef': 'bass',
            'key': data.get('key', 'C major / A minor (no sharps/flats)'),
            'time_signature': data.get('time_signature', '4/4'),
            'section': data.get('section', None)
        })
        bottom_staff = SingleStaff.from_dict(bottom_data)
        
        # Create the grand staff
        grand_staff = cls(
            instrument_id=data.get('instrument_id', ''),
            instrument_name=data.get('instrument_name', ''),
            instrument_abbr=data.get('instrument_abbr', ''),
            clef=data.get('clef', 'grand_staff'),
            key=data.get('key', 'C major / A minor (no sharps/flats)'),
            time_signature=data.get('time_signature', '4/4'),
            section=data.get('section', None),
            top_staff=top_staff,
            bottom_staff=bottom_staff
        )
        
        # Preserve ID if provided
        if 'id' in data:
            grand_staff.id = data['id']
            
        # Copy notation settings if present
        if 'notation_settings' in data:
            import copy
            grand_staff.notation_settings = copy.deepcopy(data['notation_settings'])
            print(f"Restored notation settings for {grand_staff.instrument_name} (grand staff) from dictionary")
            
            # Also apply to component staves
            if hasattr(grand_staff, 'top_staff'):
                grand_staff.top_staff.notation_settings = copy.deepcopy(data['notation_settings'])
            if hasattr(grand_staff, 'bottom_staff'):
                grand_staff.bottom_staff.notation_settings = copy.deepcopy(data['notation_settings'])
            
        return grand_staff
        
    def to_dict(self):
        """Convert grand staff to dictionary for serialization"""
        # Get base data from parent class
        data = super().to_dict()
        
        # Add grand staff specific data
        data['staff_type'] = 'grand_staff'
        
        # Include component staves if available
        if hasattr(self, 'top_staff'):
            data['top_staff'] = self.top_staff.to_dict()
            # Ensure plugin info is set on top staff
            if hasattr(self, 'plugin'):
                data['top_staff']['plugin'] = self.plugin
        
        if hasattr(self, 'bottom_staff'):
            data['bottom_staff'] = self.bottom_staff.to_dict()
            # Ensure plugin info is set on bottom staff
            if hasattr(self, 'plugin'):
                data['bottom_staff']['plugin'] = self.plugin
        
        return data

class SectionGroup:
    """Group of staves for sections like strings, woodwinds, etc."""
    
    def __init__(self, name="", staves=None):
        """Initialize a section group with a name and list of staves
        
        Args:
            name: The name of the section
            staves: List of staves in this section
        """
        self.name = name
        self.staves = staves or []
        self.bracket_y_start = 0
        self.bracket_y_end = 0
        self.section_name_y = 0
        
        # CRITICAL FIX: Initialize display_order_index to 0 instead of letting it default to 999999
        self.display_order_index = 0  # Start with 0 for the first section
        print(f"SectionGroup: Set {name} order index to {self.display_order_index}")
        
        # Remove the problematic try/except block that might interfere with initialization

class ScoreLayout:
    """Manages the overall score layout including sections and directly-attached staves"""
    def __init__(self):
        self.sections: List[SectionGroup] = []  # Sections with their contained staves
        self.ungrouped_staves: List[StaffBase or GrandStaff] = []  # Staves directly under the Score (not in any section)
        self.left_margin: int = 80
        self.right_margin: int = 50  # CRITICAL FIX: Match renderer margin for consistency
        self.top_margin: int = 40
        self.staff_height: int = 32
        self.staff_spacing: int = 50
        self.is_setup_mode: bool = True
        self.background_color: str = "#fff0f0"  # Light pink for setup mode
        self.measure_count: int = 5  # Default to 5 measures in setup mode
        
        # View options
        self.continuous_view: bool = False
        self.page_across: bool = False
        self.page_down: bool = False
        
    def set_setup_mode(self, is_setup: bool):
        """Switch between setup and edit modes"""
        self.is_setup_mode = is_setup
        self.background_color = "#fff0f0" if is_setup else "#FFFFFF"  # Light pink for setup mode, white for edit mode
        
        # In setup mode, force 5 measures
        if is_setup:
            self.measure_count = 5
            
    def set_measure_count(self, count: int):
        """Set the number of measures to display"""
        self.measure_count = count
        
    def get_measure_count(self) -> int:
        """Get the current measure count"""
        # In setup mode, always return 5 measures
        if self.is_setup_mode:
            return 5
        return self.measure_count
        
    def get_all_staves(self):
        """Get all staves from both sections and ungrouped staves"""
        all_staves = []
        
        # Add ungrouped staves
        all_staves.extend(self.ungrouped_staves)
        
        # Add staves from sections
        for section in self.sections:
            all_staves.extend(section.staves)
            
        return all_staves
        
    def add_section(self, section: SectionGroup):
        """Add a new section to the score"""
        # Set a proper display_order_index based on the current sections count
        # This ensures that new sections are placed in order of creation
        if not hasattr(section, 'display_order_index') or section.display_order_index is None:
            # Assign an order index based on the current sections count
            section.display_order_index = len(self.sections)
            print(f"ADD_SECTION: Setting new section '{section.name}' display_order_index to {section.display_order_index}")
        
        self.sections.append(section)
        self._update_positions()
        
    def add_staff_to_section(self, staff: StaffBase or GrandStaff, section_name: str):
        """Add a staff to a specific section"""
        # Set the section property on the staff
        if hasattr(staff, 'section'):
            staff.section = section_name
            
        # Find the section and add the staff
        for section in self.sections:
            if section.name == section_name:
                section.staves.append(staff)
                self._update_positions()
                return True
                
        # Section not found, create it with a proper display_order_index
        new_section = SectionGroup(name=section_name, staves=[staff])
        # Assign display order based on current section count
        new_section.display_order_index = len(self.sections)
        print(f"ADD_STAFF_TO_SECTION: Created new section '{section_name}' with display_order_index {new_section.display_order_index}")
        
        self.sections.append(new_section)
        self._update_positions()
        return True
        
    def add_staff(self, staff: StaffBase or GrandStaff):
        """Add a staff directly to the score (not in any section)"""
        # Clear any section association
        if hasattr(staff, 'section'):
            staff.section = ""
            
        self.ungrouped_staves.append(staff)
        self._update_positions()
        
    def remove_staff(self, staff_to_remove: StaffBase or GrandStaff):
        """Remove a staff from the score or any section it's in"""
        # Check if staff is in ungrouped staves
        for i, staff in enumerate(self.ungrouped_staves):
            if staff == staff_to_remove:
                self.ungrouped_staves.pop(i)
                self._update_positions()
                return True
                
        # Check if staff is in any section
        for section in self.sections:
            for i, staff in enumerate(section.staves):
                if staff == staff_to_remove:
                    section.staves.pop(i)
                    # Remove empty sections
                    if not section.staves:
                        self.sections.remove(section)
                    self._update_positions()
                    return True
                    
        return False  # Staff not found
        
    def remove_section(self, section_name: str, keep_staves: bool = False):
        """Remove a section from the score
           If keep_staves is True, move staves to ungrouped_staves"""
        for i, section in enumerate(self.sections):
            if section.name == section_name:
                if keep_staves:
                    # Move staves to ungrouped
                    for staff in section.staves:
                        if hasattr(staff, 'section'):
                            staff.section = ""
                        self.ungrouped_staves.append(staff)
                self.sections.pop(i)
                self._update_positions()
                return True
                
        return False  # Section not found
        
    def _update_positions(self):
        """Update positions of all staves and sections"""
        # Calculate grand staff heights first
        for staff in self.ungrouped_staves:
            if isinstance(staff, GrandStaff):
                # Calculate total height as top staff height + spacing + bottom staff height
                inter_staff_spacing = 40  # Space between the two staves of a grand staff
                staff.height = staff.top_staff.height + inter_staff_spacing + staff.bottom_staff.height
                
        # Do the same for staves in sections
        for section in self.sections:
            for staff in section.staves:
                if isinstance(staff, GrandStaff):
                    inter_staff_spacing = 40
                    staff.height = staff.top_staff.height + inter_staff_spacing + staff.bottom_staff.height
                    
        # CRITICAL FIX: Sort sections based on their display_order_index before positioning them
        # This ensures sections appear in the same order as in the score setup dialog
        # If display_order_index is missing, use the section's current index to preserve file order
        def get_sort_key(section_with_index):
            section, original_index = section_with_index
            return getattr(section, 'display_order_index', original_index)
        
        # Create list of (section, original_index) tuples to preserve file order when display_order_index is missing
        sections_with_indices = [(section, idx) for idx, section in enumerate(self.sections)]
        sorted_sections_with_indices = sorted(sections_with_indices, key=get_sort_key)
        sorted_sections = [section for section, _ in sorted_sections_with_indices]
        
        # Create a combined list of all elements (ungrouped staves and sections)
        # to position them in the correct order based on their display_order_index
        combined_elements = []
        
        # Debug section order before sorting
        print(f"LAYOUT: Sections before sorting:")
        for idx, section in enumerate(self.sections):
            print(f"  {idx}. {section.name} - Order index: {getattr(section, 'display_order_index', 0)}")
        
        # Debug section order after sorting
        print(f"LAYOUT: Sorted sections for rendering:")
        for idx, section in enumerate(sorted_sections):
            print(f"  {idx}. {section.name} - Order index: {getattr(section, 'display_order_index', 0)}")
        
        # Add ungrouped staves with their display_order_index
        for staff in self.ungrouped_staves:
            # Use the stored display_order_index if available, otherwise default to 0
            # This ensures ungrouped staves appear BEFORE sections by default
            display_order = getattr(staff, 'display_order_index', 0)
            combined_elements.append({
                'type': 'staff',
                'element': staff,
                'order_index': display_order
            })
        
        # Add sections with their display_order_index
        for section in sorted_sections:
            # Skip empty sections
            if not section.staves:
                print(f"_update_positions: Skipping empty section {section.name}")
                continue
                
            display_order = getattr(section, 'display_order_index', 0)
            combined_elements.append({
                'type': 'section',
                'element': section,
                'order_index': display_order
            })
        
        # Sort all elements by their order_index
        combined_elements.sort(key=lambda e: e['order_index'])
        
        # Debug the combined and sorted elements
        print(f"LAYOUT: Combined elements for rendering in order:")
        for idx, elem in enumerate(combined_elements):
            if elem['type'] == 'staff':
                print(f"  {idx}. Staff: {elem['element'].instrument_name} - Order: {elem['order_index']}")
            else:
                print(f"  {idx}. Section: {elem['element'].name} - Order: {elem['order_index']}")
        
        # Now position all elements in the correct order
        y = self.top_margin
        
        # ENHANCEMENT: Track section positions for debugging
        section_positions = {}
        
        for elem in combined_elements:
            if elem['type'] == 'staff':
                # Position this ungrouped staff
                staff = elem['element']
                staff.y_position = y
                
                # If this is a grand staff, set the positions of its components
                if isinstance(staff, GrandStaff):
                    staff.top_staff.y_position = y
                    staff.bottom_staff.y_position = y + staff.top_staff.height + 40  # 40px spacing between staves
                    
                    # Also set the brace positions
                    staff.brace_y_start = y
                    staff.brace_y_end = staff.bottom_staff.y_position + staff.bottom_staff.height
                    staff.brace_height = staff.brace_y_end - staff.brace_y_start
                    
                    # Update instrument name y position
                    staff.instrument_name_y = y + (staff.height / 2)
                
                # Increment y for next element
                y += staff.height + self.staff_spacing
                
            else:
                # Position this section and all its staves
                section = elem['element']
                section_start_y = y
                
                # Track section's vertical position for debugging
                section_positions[section.name] = y
                
                # Set section name y position - position above the first staff
                if section.staves:
                    first_staff = section.staves[0]
                    # Position the section name above the first staff (15px above the staff's top line)
                    section.section_name_y = y - 15
                else:
                    section.section_name_y = y - 15
                    
                # Position staves in this section
                for i, staff in enumerate(section.staves):
                    # Position this staff
                    staff.y_position = y
                    
                    # Mark this staff as being in a section
                    staff.is_in_section = True
                    
                    # If this is a grand staff, set the positions of its components
                    if isinstance(staff, GrandStaff):
                        staff.top_staff.y_position = y
                        staff.bottom_staff.y_position = y + staff.top_staff.height + 40  # 40px spacing between staves
                        
                        # Also set the brace positions
                        staff.brace_y_start = y
                        staff.brace_y_end = staff.bottom_staff.y_position + staff.bottom_staff.height
                        staff.brace_height = staff.brace_y_end - staff.brace_y_start
                        
                        # Update instrument name y position
                        staff.instrument_name_y = y + (staff.height / 2)
                    
                    # Increment y for next staff
                    y += staff.height + self.staff_spacing
                    
                # If there are staves in this section, set the bracket positions
                if section.staves:
                    section.bracket_y_start = section_start_y
                    # CRITICAL FIX: Ensure bracket extends to the bottom of the last staff
                    last_staff = section.staves[-1]
                    if isinstance(last_staff, GrandStaff):
                        # For grand staff, extend to the bottom of the bottom staff
                        section.bracket_y_end = last_staff.y_position + last_staff.height
                    else:
                        # For single staff, extend to the bottom of the staff
                        section.bracket_y_end = last_staff.y_position + last_staff.height
                        
                    # Print debug info for bracket positioning
                    print(f"Section {section.name} bracket: y_start={section.bracket_y_start}, y_end={section.bracket_y_end}")
                
                # Add some extra space after the section
                y += 10  # Extra 10px after each section
            
        # DEBUG: Print final section positions
        print(f"LAYOUT: Final section positions after layout:")
        for section_name, y_pos in section_positions.items():
            print(f"  Section '{section_name}' positioned at y={y_pos}")
        
        # DEBUG: Print final rendering order
        print(f"LAYOUT: Final rendering order:")
        for idx, elem in enumerate(combined_elements):
            if elem['type'] == 'staff':
                print(f"  {idx}. Staff: {elem['element'].instrument_name} at y={elem['element'].y_position}")
            else:
                print(f"  {idx}. Section: {elem['element'].name} at y={elem['element'].bracket_y_start}")
        
    def apply_setup_options(self, options):
        print(f"[DEBUG] ScoreLayout.apply_setup_options called with options: {list(options.keys())}")
        # Get section map if available
        section_map = options.get('section_map', {})
        
        # Get section display order if available
        section_display_order = options.get('section_display_order', {})
        
        # Debug the input section display order
        print(f"LAYOUT: Received section_display_order with {len(section_display_order) if section_display_order else 0} entries")
        if section_display_order:
            for section_name, order_index in section_display_order.items():
                print(f"LAYOUT INPUT: Section '{section_name}' has display_order_index = {order_index}")
        
        # If we're getting new data from options, recreate sections based on the section map
        if 'added_staves' in options and options['added_staves']:
            # Store custom notation settings from existing staves before clearing them
            existing_notation_settings = {}
            
            # Collect notation settings from ungrouped staves
            for staff in self.ungrouped_staves:
                if hasattr(staff, 'notation_settings'):
                    existing_notation_settings[staff.instrument_id] = getattr(staff, 'notation_settings')
            
            # Collect notation settings from staves in sections
            for section in self.sections:
                for staff in section.staves:
                    if hasattr(staff, 'notation_settings'):
                        existing_notation_settings[staff.instrument_id] = getattr(staff, 'notation_settings')
            
            print(f"Preserved notation settings for {len(existing_notation_settings)} staves before rebuild")
            
            # Clear existing staves and sections
            self.sections = []
            self.ungrouped_staves = []
            section_staves = {}  # Group staves by section to maintain ordering
            
            # Track the original display order to maintain the correct staff order
            staff_order_index = 0
            
            # Create a dictionary to track section order based on first staff appearance
            section_first_appearance = {}
            
            # If we have section_display_order from the UI, use that directly
            if section_display_order:
                print(f"LAYOUT: Using explicit section_display_order from UI with {len(section_display_order)} sections")
                section_first_appearance.update(section_display_order)
            
            # Process each staff data and create staff objects
            for staff_data in options['added_staves']:
                # Get all necessary data from staff_data
                instrument_name = staff_data.get('instrument_name', 'Part')
                instrument_id = staff_data.get('instrument_id', '')
                staff_type = staff_data.get('staff_type', 'single_staff')
                
                # Get section name (try multiple possible keys)
                section_name = ""
                if 'section' in staff_data:
                    section_name = staff_data['section']
                # If not found, try staff_data['section']
                elif 'section' in staff_data:
                    section_name = staff_data['section']
                # Finally check staff_data.get('staff_data', {}).get('section', '')
                elif 'staff_data' in staff_data and 'section' in staff_data['staff_data']:
                    section_name = staff_data['staff_data']['section']
                    
                # If this is a new section and we don't have its order from the UI,
                # track its first appearance index
                if section_name and section_name not in section_first_appearance:
                    section_first_appearance[section_name] = staff_order_index
                    print(f"LAYOUT: Section {section_name} first appears at index {staff_order_index}")
                
                # Create the staff object based on staff_type
                staff = None
                
                # Retrieve visibility setting if available
                is_visible = staff_data.get('is_visible', True)
                
                if staff_type == 'grand_staff':
                    # Create a grand staff with treble and bass clef staves
                    top_staff = SingleStaff(
                        instrument_name=instrument_name,
                        instrument_id=instrument_id,
                        clef='treble',
                        key=staff_data.get('key', ''),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    bottom_staff = SingleStaff(
                        instrument_name=instrument_name,
                        instrument_id=instrument_id,
                        clef='bass',
                        key=staff_data.get('key', ''),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    
                    staff = GrandStaff(
                        instrument_name=instrument_name,
                        instrument_id=instrument_id,
                        top_staff=top_staff,
                        bottom_staff=bottom_staff
                    )
                    staff.is_visible = is_visible
                    
                    # Set custom name if provided
                    if 'custom_name' in staff_data:
                        staff.custom_name = staff_data['custom_name']
                        top_staff.custom_name = staff_data['custom_name']
                        bottom_staff.custom_name = staff_data['custom_name']
                    
                    # Set instrument abbreviation if provided
                    if 'instrument_abbr' in staff_data:
                        staff.instrument_abbr = staff_data['instrument_abbr']
                        top_staff.instrument_abbr = staff_data['instrument_abbr']
                        bottom_staff.instrument_abbr = staff_data['instrument_abbr']
                        
                else:
                    # Create a single staff - Enhanced clef detection
                    # Try multiple locations for clef information to avoid defaulting to treble incorrectly
                    clef = 'treble'  # Default fallback
                    
                    # Check direct clef field first
                    if 'clef' in staff_data and staff_data['clef']:
                        clef = staff_data['clef']
                        print(f"LAYOUT: Found clef '{clef}' for {instrument_name} in staff_data.clef")
                    # Check nested staff_data.staff_data.clef
                    elif 'staff_data' in staff_data and isinstance(staff_data['staff_data'], dict) and 'clef' in staff_data['staff_data']:
                        clef = staff_data['staff_data']['clef']
                        print(f"LAYOUT: Found clef '{clef}' for {instrument_name} in staff_data.staff_data.clef")
                    # Check clef_map if available
                    elif 'clef_map' in options and instrument_id in options['clef_map']:
                        clef = options['clef_map'][instrument_id]
                        print(f"LAYOUT: Found clef '{clef}' for {instrument_name} in clef_map")
                    else:
                        print(f"LAYOUT: Using default clef '{clef}' for {instrument_name} - no clef information found")
                    
                    staff = SingleStaff(
                        instrument_name=instrument_name,
                        instrument_id=instrument_id,
                        clef=clef,
                        key=staff_data.get('key', ''),
                        time_signature=staff_data.get('time_signature', '4/4')
                    )
                    staff.is_visible = is_visible
                    
                    # Set custom name if provided
                    if 'custom_name' in staff_data:
                        staff.custom_name = staff_data['custom_name']
                    
                    # Set instrument abbreviation if provided
                    if 'instrument_abbr' in staff_data:
                        staff.instrument_abbr = staff_data['instrument_abbr']
                
                # Set staff spacing from options if available
                if 'staff_spacing' in options:
                    staff.spacing = options['staff_spacing']
                
                # Restore notation settings if available
                if instrument_id in existing_notation_settings:
                    setattr(staff, 'notation_settings', existing_notation_settings[instrument_id])
                    print(f"Restored notation settings for {instrument_name}")
                    
                # Store the display order index on the staff
                staff.display_order_index = staff_order_index
                
                # Also store section display order if available
                if 'section_display_order' in staff_data:
                    staff.section_display_order = staff_data['section_display_order']
                    
                # Assign the section to the staff object
                if section_name:
                    staff.section = section_name
                
                # Set plugin information if available
                if 'plugin' in staff_data:
                    staff.plugin = staff_data['plugin']
                    # For grand staves, apply to individual staves too
                    if staff_type == 'grand_staff':
                        top_staff.plugin = staff_data['plugin']
                        bottom_staff.plugin = staff_data['plugin']
                
                # Update the staff order index for the next staff
                staff_order_index += 1
                
                # Add to the appropriate section or directly to the score
                if section_name:
                    # Initialize the section list if it doesn't exist
                    if section_name not in section_staves:
                        section_staves[section_name] = []
                    # Add the staff to this section
                    section_staves[section_name].append(staff)
                else:
                    # Add directly to score (ungrouped)
                    self.ungrouped_staves.append(staff)
            
            # Debug the section staves before sorting and creating section objects
            print("\nLAYOUT: Section staves before creating section objects:")
            for section_name, staves in section_staves.items():
                expected_order = section_first_appearance.get(section_name, -1)
                print(f"  Section '{section_name}' with {len(staves)} staves, expected order = {expected_order}")
                for i, staff in enumerate(staves):
                    print(f"    Staff {i}: {staff.instrument_name}, index = {getattr(staff, 'display_order_index', -1)}")
            
            # Create sections from the grouped staves and sort them by display order
            for section_name, staves in section_staves.items():
                # Sort staves in this section by their display order to match UI order
                staves.sort(key=lambda s: getattr(s, 'display_order_index', 0))
                section = SectionGroup(name=section_name, staves=staves)
                
                # CRITICAL FIX: Assign display_order_index from section_display_order if available
                if section_name in section_display_order:
                    # Use explicit section order from options
                    section.display_order_index = section_display_order[section_name]
                    print(f"LAYOUT: Setting section {section_name} display_order_index to {section.display_order_index} from section_display_order")
                else:
                    # Fallback to section's first appearance order if not found in options
                    section.display_order_index = section_first_appearance.get(section_name, len(self.sections))
                    print(f"LAYOUT: Fallback - Setting section {section_name} display_order_index to {section.display_order_index} from first appearance")
                
                self.sections.append(section)
            
            # Debug the sections after creation before sorting
            print("\nLAYOUT: Created sections before sorting:")
            for i, section in enumerate(self.sections):
                print(f"  {i}. Section '{section.name}', display_order_index = {getattr(section, 'display_order_index', -1)}")
            
            # ENHANCEMENT: Always sort sections by their display_order_index to match UI order
            self.sections.sort(key=lambda s: getattr(s, 'display_order_index', 0))
            
            # Debug the sections after sorting
            print("\nLAYOUT: Sections after sorting:")
            for i, section in enumerate(self.sections):
                print(f"  {i}. Section '{section.name}', display_order_index = {getattr(section, 'display_order_index', -1)}")
            
            # Debug output to validate section ordering
            print(f"LAYOUT: Section order before _update_positions:")
            for idx, section in enumerate(self.sections):
                print(f"  {idx}. Section: {section.name}, Order: {getattr(section, 'display_order_index', -1)}")
            
            # Sort ungrouped staves by their display order to match UI order
            self.ungrouped_staves.sort(key=lambda s: getattr(s, 'display_order_index', 0))
            
            # Apply spacing options
            if 'staff_spacing' in options:
                self.staff_spacing = options['staff_spacing']
            if 'system_spacing' in options:
                self.system_spacing = options['system_spacing']
            
            # ENHANCEMENT: Create a sorted lookup to verify final ordering
            section_ordering_lookup = {}
            for i, section in enumerate(self.sections):
                section_ordering_lookup[section.name] = {
                    'display_order_index': getattr(section, 'display_order_index', 0),
                    'rendering_position': i,
                    'staves_count': len(section.staves)
                }
            
            print(f"\nLAYOUT: Final section order verification:")
            for section_name, info in section_ordering_lookup.items():
                print(f"  Section '{section_name}': display_order_index={info['display_order_index']}, rendering_position={info['rendering_position']}, staves={info['staves_count']}")
            
            # Recalculate layout positions to ensure correct rendering
            self._update_positions()
            print("[DEBUG] ScoreLayout: _update_positions called")
        
        # Apply immediate rendering flag if requested
        if options.get('immediate_apply', False) or options.get('force_render', False):
            print("LAYOUT: Forcing immediate render in apply_setup_options")
            # Signal that a render is needed
            self.is_modified = True
        
        # Set setup mode if specified
        if 'force_setup_mode' in options:
            self.set_setup_mode(options['force_setup_mode'])
            print(f"LAYOUT: Set setup mode to {options['force_setup_mode']}")
        
        # Update positions and return success
        self._update_positions()
        print("[DEBUG] ScoreLayout: _update_positions called")
        return True 