from dataclasses import dataclass
from typing import Optional, Dict, Any

from .notation_constants import (
    BARLINE_CONSTANTS, MUSICAL_DIRECTION_CONSTANTS, FORM_LAYOUT_CONSTANTS,
    MUSIC_FONTS, FONT_SIZES, POSITION_CONSTANTS, SYMBOL_MAP
)

@dataclass
class MeasureLayoutInfo:
    """Layout information for a measure during positioning and justification"""
    x_position: float = 0.0
    justified_width: float = 160.0
    base_width: float = 160.0
    content_density: float = 1.0
    system_number: int = 1
    page_number: int = 1
    is_justified: bool = False

class MeasureObject:
    """Enhanced measure object with comprehensive properties"""
    
    def __init__(self, measure_number: int = 1, end_x: float = 160, document=None, barline_type: str = "single"):
        self.measure_number = measure_number
        self.end_x = end_x  # X position where this measure ends (barline position)
        self.width = 160    # Dynamic width based on content density
        self.x_position = 0.0  # X position where this measure starts
        
        # Store reference to document if provided
        self.document = document
        
        # Layout information
        self.layout_info = MeasureLayoutInfo()
        
        # Barline properties
        self.barline_type = barline_type  # Underlying structural barline (single)
        self.overlay_type: Optional[str] = None  # Visual overlay: final/double/repeat_*
        self.barline_thickness = 1
        self.selected = False  # Track selection state
        
        # Repeat properties
        self.repeat_count = 2
        self.is_repeat_start = False
        self.is_repeat_end = False
        
        # Ending properties
        self.ending_type = None  # "1st", "2nd", "3rd", "1st-2nd", etc.
        self.ending_text = ""
        
        # Musical directions
        self.musical_direction = None
        self.has_segno = False
        self.has_coda = False
        self.has_fine = False
        self.direction_text = ""
        
        # Measure attributes
        self.time_signature = None
        self.key_signature = None
        self.tempo_marking = None
        self.rehearsal_letter = None
        
        # Layout properties
        self.force_system_break = False
        self.custom_width = None
        self.is_removable = True  # Whether this measure can be removed (measure 1 is not removable)
        
    def get_base_width(self) -> float:
        """Get the base width of this measure"""
        return self.layout_info.base_width if hasattr(self, 'layout_info') else self.width
        
    def get_visual_width(self) -> float:
        """Get the visual width of this measure (after justification)"""
        return self.layout_info.justified_width if hasattr(self, 'layout_info') else self.width
        
    def get_content_density(self) -> float:
        """Get the content density of this measure"""
        return self.layout_info.content_density if hasattr(self, 'layout_info') else 1.0

    def get_barline_symbol(self):
        """Get the SMuFL symbol for this measure's barline"""
        barline_info = BARLINE_CONSTANTS.get(self.barline_type, BARLINE_CONSTANTS["single"])
        return barline_info.get("smufl", "|")
        
    def get_direction_symbol(self):
        """Get the SMuFL symbol for musical direction if any"""
        if self.musical_direction:
            direction_info = MUSICAL_DIRECTION_CONSTANTS.get(self.musical_direction)
            if direction_info:
                return direction_info.get("smufl", "")
        return ""
        
    def to_dict(self):
        """Convert measure to dictionary for serialization"""
        return {
            'measure_number': self.measure_number,
            'end_x': self.end_x,
            'width': self.width,
            'x_position': self.x_position,
            'barline_type': self.barline_type,
            'barline_thickness': self.barline_thickness,
            'overlay_type': self.overlay_type,
            'selected': self.selected,
            'repeat_count': self.repeat_count,
            'is_repeat_start': self.is_repeat_start,
            'is_repeat_end': self.is_repeat_end,
            'ending_type': self.ending_type,
            'ending_text': self.ending_text,
            'musical_direction': self.musical_direction,
            'has_segno': self.has_segno,
            'has_coda': self.has_coda,
            'has_fine': self.has_fine,
            'direction_text': self.direction_text,
            'time_signature': self.time_signature,
            'key_signature': self.key_signature,
            'tempo_marking': self.tempo_marking,
            'rehearsal_letter': self.rehearsal_letter,
            'force_system_break': self.force_system_break,
            'custom_width': self.custom_width,
            'is_removable': self.is_removable,
            'layout_info': {
                'x_position': self.layout_info.x_position,
                'justified_width': self.layout_info.justified_width,
                'base_width': self.layout_info.base_width,
                'content_density': self.layout_info.content_density,
                'system_number': self.layout_info.system_number,
                'page_number': self.layout_info.page_number,
                'is_justified': self.layout_info.is_justified
            } if hasattr(self, 'layout_info') else {}
        }
        
    @classmethod
    def from_dict(cls, data):
        """Create measure from dictionary"""
        measure = cls(data.get('measure_number', 1), data.get('end_x', 160))
        measure.width = data.get('width', 160)
        measure.x_position = data.get('x_position', 0.0)
        measure.barline_type = data.get('barline_type', 'single')
        measure.barline_thickness = data.get('barline_thickness', 1)
        measure.overlay_type = data.get('overlay_type')
        measure.selected = data.get('selected', False)
        measure.repeat_count = data.get('repeat_count', 2)
        measure.is_repeat_start = data.get('is_repeat_start', False)
        measure.is_repeat_end = data.get('is_repeat_end', False)
        measure.ending_type = data.get('ending_type')
        measure.ending_text = data.get('ending_text', '')
        measure.musical_direction = data.get('musical_direction')
        measure.has_segno = data.get('has_segno', False)
        measure.has_coda = data.get('has_coda', False)
        measure.has_fine = data.get('has_fine', False)
        measure.direction_text = data.get('direction_text', '')
        measure.time_signature = data.get('time_signature')
        measure.key_signature = data.get('key_signature')
        measure.tempo_marking = data.get('tempo_marking')
        measure.rehearsal_letter = data.get('rehearsal_letter')
        measure.force_system_break = data.get('force_system_break', False)
        measure.custom_width = data.get('custom_width')
        measure.is_removable = data.get('is_removable', True)
        
        # Load layout info if present
        layout_data = data.get('layout_info', {})
        if layout_data:
            measure.layout_info = MeasureLayoutInfo(
                x_position=layout_data.get('x_position', 0.0),
                justified_width=layout_data.get('justified_width', 160.0),
                base_width=layout_data.get('base_width', 160.0),
                content_density=layout_data.get('content_density', 1.0),
                system_number=layout_data.get('system_number', 1),
                page_number=layout_data.get('page_number', 1),
                is_justified=layout_data.get('is_justified', False)
            )
        
        return measure 

    def contains_x_position(self, x_pos: float, tolerance: float = 20.0) -> bool:
        """Check if this measure contains the given x position"""
        # Check if position is within the measure boundaries with tolerance
        left_boundary = self.get_left_boundary_x()
        right_boundary = self.get_right_boundary_x()
        return left_boundary <= x_pos <= right_boundary or abs(right_boundary - x_pos) < tolerance

    def get_left_boundary_x(self) -> float:
        """Get the left boundary x position of this measure"""
        return getattr(self, 'x_position', 0.0)
    
    def get_right_boundary_x(self) -> float:
        """Get the right boundary x position of this measure (barline position)"""
        return self.end_x
    
    def applies_to_staff(self, staff_id: str) -> bool:
        """Check if this measure applies to the given staff"""
        # For now, measures apply to all staves (this could be enhanced for staff-specific measures)
        return True 