"""
Core classes for representing score structure.
"""
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .base import MusicElement


class ScoreFormat(Enum):
    """Enum for different score format types."""
    STANDARD = "standard"
    OPEN = "open"
    LEAD_SHEET = "lead_sheet"
    TABLATURE = "tablature"
    PERCUSSION = "percussion"


class Score(MusicElement):
    """
    Represents a complete musical score.
    
    A Score is the top-level container for all musical content.
    It can contain sections and staff systems directly, or have
    hybrid organization with some sections and some ungrouped staves.
    """
    
    def __init__(
        self, 
        title: Optional[str] = None,
        composer: Optional[str] = None,
        format_type: ScoreFormat = ScoreFormat.STANDARD,
        id: Optional[str] = None
    ):
        """
        Initialize a Score.
        
        Args:
            title: The title of the score.
            composer: The composer of the score.
            format_type: The score format type.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.title = title
        self.composer = composer
        self.format_type = format_type
        self._sections: List[Section] = []
        self._ungrouped_staves: List['StaffSystem'] = []
        
    @property
    def sections(self) -> List['Section']:
        """Get all sections in this score."""
        return self._sections.copy()
    
    @property
    def ungrouped_staves(self) -> List['StaffSystem']:
        """Get all ungrouped staves in this score."""
        return self._ungrouped_staves.copy()
    
    def add_section(self, section: 'Section') -> 'Section':
        """
        Add a section to this score.
        
        Args:
            section: The section to add.
            
        Returns:
            The added section for method chaining.
        """
        self._sections.append(section)
        self.add_child(section)
        return section
    
    def add_staff_system(self, staff_system: 'StaffSystem') -> 'StaffSystem':
        """
        Add an ungrouped staff system to this score.
        
        Args:
            staff_system: The staff system to add.
            
        Returns:
            The added staff system for method chaining.
        """
        self._ungrouped_staves.append(staff_system)
        self.add_child(staff_system)
        return staff_system
    
    def remove_section(self, section: 'Section') -> None:
        """
        Remove a section from this score.
        
        Args:
            section: The section to remove.
        """
        if section in self._sections:
            self._sections.remove(section)
            self.remove_child(section)
    
    def remove_staff_system(self, staff_system: 'StaffSystem') -> None:
        """
        Remove an ungrouped staff system from this score.
        
        Args:
            staff_system: The staff system to remove.
        """
        if staff_system in self._ungrouped_staves:
            self._ungrouped_staves.remove(staff_system)
            self.remove_child(staff_system)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'title': self.title,
            'composer': self.composer,
            'format_type': self.format_type.value,
            'sections': [section.to_dict() for section in self._sections],
            'ungrouped_staves': [staff.to_dict() for staff in self._ungrouped_staves]
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Score':
        """Create from dictionary representation."""
        from ..serialization import deserialize_element
        
        score = cls(
            title=data.get('title'),
            composer=data.get('composer'),
            format_type=ScoreFormat(data.get('format_type', 'standard')),
            id=data.get('id')
        )
        score.attributes = data.get('attributes', {}).copy()
        
        # Process ungrouped_staves
        for staff_data in data.get('ungrouped_staves', []):
            # Create a staff system directly
            if staff_data.get('type') == 'SingleStaff':
                from .staves import SingleStaff
                staff = SingleStaff.from_dict(staff_data)
                score.add_staff_system(staff)
            elif staff_data.get('type') == 'GrandStaff':
                from .staves import GrandStaff
                staff = GrandStaff.from_dict(staff_data)
                score.add_staff_system(staff)
        
        # Process sections
        for section_data in data.get('sections', []):
            section = Section.from_dict(section_data)
            score.add_section(section)
        
        return score


class Section(MusicElement):
    """
    Represents a section in a score.
    
    A Section is a logical grouping of staff systems, which may have
    a name or designation (like "Strings", "Woodwinds", "Chorus").
    """
    
    def __init__(self, name: str, display_order_index: int = 0, id: Optional[str] = None):
        """
        Initialize a Section.
        
        Args:
            name: The name of the section.
            display_order_index: The order index for positioning this section.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.name = name
        self.display_order_index = display_order_index
        self._staves: List['StaffSystem'] = []
        self.section_brackets = True  # Whether to draw section brackets
        self.section_name_visible = True  # Whether to show section name
        self.section_name_y = 0  # Y position of section name for rendering
        
    @property
    def staves(self) -> List['StaffSystem']:
        """Get all staves in this section."""
        return self._staves.copy()
    
    def add_staff_system(self, staff_system: 'StaffSystem') -> 'StaffSystem':
        """
        Add a staff system to this section.
        
        Args:
            staff_system: The staff system to add.
            
        Returns:
            The added staff system for method chaining.
        """
        self._staves.append(staff_system)
        self.add_child(staff_system)
        return staff_system
    
    def remove_staff_system(self, staff_system: 'StaffSystem') -> None:
        """
        Remove a staff system from this section.
        
        Args:
            staff_system: The staff system to remove.
        """
        if staff_system in self._staves:
            self._staves.remove(staff_system)
            self.remove_child(staff_system)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'name': self.name,
            'display_order_index': self.display_order_index,
            'section_brackets': self.section_brackets,
            'section_name_visible': self.section_name_visible,
            'section_name_y': self.section_name_y,
            'staves': [staff.to_dict() for staff in self._staves]
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Section':
        """Create from dictionary representation."""
        section = cls(
            name=data.get('name', 'Unnamed Section'),
            display_order_index=data.get('display_order_index', 0),
            id=data.get('id')
        )
        section.attributes = data.get('attributes', {}).copy()
        section.section_brackets = data.get('section_brackets', True)
        section.section_name_visible = data.get('section_name_visible', True)
        section.section_name_y = data.get('section_name_y', 0)
        
        # Process staves
        for staff_data in data.get('staves', []):
            # Create a staff system directly
            if staff_data.get('type') == 'SingleStaff':
                from .staves import SingleStaff
                staff = SingleStaff.from_dict(staff_data)
                section.add_staff_system(staff)
            elif staff_data.get('type') == 'GrandStaff':
                from .staves import GrandStaff
                staff = GrandStaff.from_dict(staff_data)
                section.add_staff_system(staff)
        
        return section


class StaffSystem(MusicElement):
    """
    Abstract base class for staff systems.
    
    A StaffSystem represents a grouping of one or more staves that
    are treated as a single unit. Concrete subclasses include
    SingleStaff and GrandStaff.
    """
    
    def __init__(
        self,
        instrument_name: str,
        instrument_abbr: Optional[str] = None,
        instrument_id: Optional[str] = None,
        display_order_index: int = 0,
        id: Optional[str] = None
    ):
        """
        Initialize a StaffSystem.
        
        Args:
            instrument_name: The name of the instrument.
            instrument_abbr: The abbreviated name of the instrument.
            instrument_id: The identifier for the instrument.
            display_order_index: The order index for positioning this staff.
            id: Optional unique identifier for this element.
        """
        super().__init__(id=id)
        self.instrument_name = instrument_name
        self.instrument_abbr = instrument_abbr or instrument_name
        self.instrument_id = instrument_id or instrument_name.lower().replace(' ', '_')
        self.display_order_index = display_order_index
        
        # Visual properties
        self.y_position = 0  # Y position for rendering
        self.visible = True  # Whether this staff is visible 
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'instrument_name': self.instrument_name,
            'instrument_abbr': self.instrument_abbr,
            'instrument_id': self.instrument_id,
            'display_order_index': self.display_order_index,
            'y_position': self.y_position,
            'visible': self.visible
        })
        return result 