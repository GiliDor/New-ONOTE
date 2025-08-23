"""
Classes for representing various types of staves in a score.
"""
from typing import Dict, List, Optional, Any, Union

from .base import MusicElement
from .score import StaffSystem


class Staff(MusicElement):
    """
    Base class for a single staff, containing music notation.
    
    A Staff contains actual musical content (notes, rests, etc.).
    """
    
    def __init__(
        self,
        clef: str = "treble",
        key: str = "C",
        time_signature: str = "4/4",
        id: Optional[str] = None
    ):
        """
        Initialize a Staff.
        
        Args:
            clef: The initial clef for this staff.
            key: The initial key signature for this staff.
            time_signature: The initial time signature for this staff.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.clef = clef
        self.key = key
        self.time_signature = time_signature
        self._measures: List['Measure'] = []  # Will be defined later
        
        # Visual properties
        self.line_count = 5  # Number of staff lines
        self.spacing = 8  # Spacing between staff lines in pixels
        self.visible = True
    
    @property
    def measures(self) -> List:
        """Get all measures in this staff."""
        return self._measures.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'clef': self.clef,
            'key': self.key,
            'time_signature': self.time_signature,
            'line_count': self.line_count,
            'spacing': self.spacing,
            'visible': self.visible,
        })
        return result


class SingleStaff(StaffSystem):
    """
    Represents a single staff system.
    
    A SingleStaff is a StaffSystem containing exactly one Staff.
    It is used for instruments that use a single staff.
    """
    
    def __init__(
        self,
        instrument_name: str,
        instrument_abbr: Optional[str] = None,
        instrument_id: Optional[str] = None,
        display_order_index: int = 0,
        clef: str = "treble",
        key: str = "C",
        time_signature: str = "4/4",
        id: Optional[str] = None
    ):
        """
        Initialize a SingleStaff.
        
        Args:
            instrument_name: The name of the instrument.
            instrument_abbr: The abbreviated name of the instrument.
            instrument_id: The identifier for the instrument.
            display_order_index: The order index for positioning this staff.
            clef: The initial clef for this staff.
            key: The initial key signature for this staff.
            time_signature: The initial time signature for this staff.
            id: Optional unique identifier.
        """
        super().__init__(
            instrument_name=instrument_name,
            instrument_abbr=instrument_abbr,
            instrument_id=instrument_id,
            display_order_index=display_order_index,
            id=id
        )
        self.staff = Staff(
            clef=clef, 
            key=key, 
            time_signature=time_signature
        )
        self.add_child(self.staff)
    
    @property
    def clef(self) -> str:
        """Get the clef of this staff."""
        return self.staff.clef
    
    @clef.setter
    def clef(self, value: str):
        """Set the clef of this staff."""
        self.staff.clef = value
    
    @property
    def key(self) -> str:
        """Get the key signature of this staff."""
        return self.staff.key
    
    @key.setter
    def key(self, value: str):
        """Set the key signature of this staff."""
        self.staff.key = value
    
    @property
    def time_signature(self) -> str:
        """Get the time signature of this staff."""
        return self.staff.time_signature
    
    @time_signature.setter
    def time_signature(self, value: str):
        """Set the time signature of this staff."""
        self.staff.time_signature = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'staff_type': 'single_staff',
            'staff': self.staff.to_dict()
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SingleStaff':
        """Create from dictionary representation."""
        staff_system = cls(
            instrument_name=data.get('instrument_name', 'Unnamed Instrument'),
            instrument_abbr=data.get('instrument_abbr'),
            instrument_id=data.get('instrument_id'),
            display_order_index=data.get('display_order_index', 0),
            id=data.get('id')
        )
        
        staff_system.attributes = data.get('attributes', {}).copy()
        staff_system.y_position = data.get('y_position', 0)
        staff_system.visible = data.get('visible', True)
        
        # Process staff data
        staff_data = data.get('staff', {})
        staff_system.staff.clef = staff_data.get('clef', 'treble')
        staff_system.staff.key = staff_data.get('key', 'C')
        staff_system.staff.time_signature = staff_data.get('time_signature', '4/4')
        staff_system.staff.line_count = staff_data.get('line_count', 5)
        staff_system.staff.spacing = staff_data.get('spacing', 8)
        staff_system.staff.visible = staff_data.get('visible', True)
        
        return staff_system


class GrandStaff(StaffSystem):
    """
    Represents a grand staff system.
    
    A GrandStaff is a StaffSystem containing exactly two staves,
    typically used for piano or other keyboard instruments.
    """
    
    def __init__(
        self,
        instrument_name: str,
        instrument_abbr: Optional[str] = None,
        instrument_id: Optional[str] = None,
        display_order_index: int = 0,
        upper_clef: str = "treble",
        lower_clef: str = "bass",
        key: str = "C",
        time_signature: str = "4/4",
        id: Optional[str] = None
    ):
        """
        Initialize a GrandStaff.
        
        Args:
            instrument_name: The name of the instrument.
            instrument_abbr: The abbreviated name of the instrument.
            instrument_id: The identifier for the instrument.
            display_order_index: The order index for positioning this staff.
            upper_clef: The initial clef for the upper staff.
            lower_clef: The initial clef for the lower staff.
            key: The initial key signature for both staves.
            time_signature: The initial time signature for both staves.
            id: Optional unique identifier.
        """
        super().__init__(
            instrument_name=instrument_name,
            instrument_abbr=instrument_abbr,
            instrument_id=instrument_id,
            display_order_index=display_order_index,
            id=id
        )
        self.upper_staff = Staff(
            clef=upper_clef,
            key=key,
            time_signature=time_signature
        )
        self.lower_staff = Staff(
            clef=lower_clef,
            key=key,
            time_signature=time_signature
        )
        self.add_child(self.upper_staff)
        self.add_child(self.lower_staff)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'staff_type': 'grand_staff',
            'upper_staff': self.upper_staff.to_dict(),
            'lower_staff': self.lower_staff.to_dict()
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GrandStaff':
        """Create from dictionary representation."""
        staff_system = cls(
            instrument_name=data.get('instrument_name', 'Unnamed Instrument'),
            instrument_abbr=data.get('instrument_abbr'),
            instrument_id=data.get('instrument_id'),
            display_order_index=data.get('display_order_index', 0),
            id=data.get('id')
        )
        
        staff_system.attributes = data.get('attributes', {}).copy()
        staff_system.y_position = data.get('y_position', 0)
        staff_system.visible = data.get('visible', True)
        
        # Process upper staff data
        upper_staff_data = data.get('upper_staff', {})
        staff_system.upper_staff.clef = upper_staff_data.get('clef', 'treble')
        staff_system.upper_staff.key = upper_staff_data.get('key', 'C')
        staff_system.upper_staff.time_signature = upper_staff_data.get('time_signature', '4/4')
        staff_system.upper_staff.line_count = upper_staff_data.get('line_count', 5)
        staff_system.upper_staff.spacing = upper_staff_data.get('spacing', 8)
        staff_system.upper_staff.visible = upper_staff_data.get('visible', True)
        
        # Process lower staff data
        lower_staff_data = data.get('lower_staff', {})
        staff_system.lower_staff.clef = lower_staff_data.get('clef', 'bass')
        staff_system.lower_staff.key = lower_staff_data.get('key', 'C')
        staff_system.lower_staff.time_signature = lower_staff_data.get('time_signature', '4/4')
        staff_system.lower_staff.line_count = lower_staff_data.get('line_count', 5)
        staff_system.lower_staff.spacing = lower_staff_data.get('spacing', 8)
        staff_system.lower_staff.visible = lower_staff_data.get('visible', True)
        
        return staff_system 