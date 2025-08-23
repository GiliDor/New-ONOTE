"""
Temporal Measure System for ONOTE

This module implements the core temporal architecture that reconciles:
1. Musical time (beats, rhythms, note durations) 
2. Graphical layout (staff width, line breaks, page flow)
3. Notation elements (notes, rests, articulations)
4. Dynamic spacing and justification

Key Concepts:
- Measures are temporal containers with beat positions
- Notes/rests occupy specific beat positions within measures
- Graphical width is calculated from temporal content
- Automatic justification and system breaking
- Content-aware spacing based on notation density
"""

from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import copy
from PyQt6.QtCore import QSettings

# Import existing classes
from .measure_object import MeasureObject, MeasureLayoutInfo
from .notation_constants import BARLINE_CONSTANTS


class NoteDuration(Enum):
    """Standard note durations with their beat values"""
    WHOLE = 4.0
    HALF = 2.0
    QUARTER = 1.0
    EIGHTH = 0.5
    SIXTEENTH = 0.25
    THIRTY_SECOND = 0.125
    SIXTY_FOURTH = 0.0625
    
    # Dotted notes (1.5x the base value)
    DOTTED_HALF = 3.0
    DOTTED_QUARTER = 1.5
    DOTTED_EIGHTH = 0.75
    DOTTED_SIXTEENTH = 0.375
    
    # Triplets (2/3 of the base value)
    QUARTER_TRIPLET = 2.0/3.0
    EIGHTH_TRIPLET = 1.0/3.0
    SIXTEENTH_TRIPLET = 1.0/6.0


@dataclass
class BeatPosition:
    """Represents a specific beat position within a measure"""
    beat: float  # Beat number (1.0, 1.5, 2.0, etc.)
    subdivision: int = 1  # Subdivision level (1=quarter, 2=eighth, 4=sixteenth)
    
    def __post_init__(self):
        # Ensure beat is positive
        if self.beat < 0:
            self.beat = 0.0
    
    def __lt__(self, other):
        return self.beat < other.beat
    
    def __eq__(self, other):
        return abs(self.beat - other.beat) < 0.001  # Floating point tolerance


@dataclass
class NotationElement:
    """Base class for all notation elements that occupy temporal space"""
    duration: NoteDuration
    beat_position: BeatPosition
    graphical_width: float = 0.0  # Calculated width in pixels
    id: str = ""
    
    def __post_init__(self):
        """Base post-initialization for all notation elements"""
        # Ensure graphical_width is set if not provided
        if self.graphical_width == 0.0:
            self.graphical_width = 20.0  # Default width
    
    def get_beat_duration(self) -> float:
        """Get the duration in beats"""
        return self.duration.value
    
    def get_end_beat(self) -> float:
        """Get the beat position where this element ends"""
        return self.beat_position.beat + self.get_beat_duration()


@dataclass
class Note(NotationElement):
    """A musical note with pitch and duration"""
    pitch: str = "C4"  # Scientific pitch notation
    accidental: Optional[str] = None  # "sharp", "flat", "natural"
    articulation: Optional[str] = None  # "staccato", "accent", etc.
    tie_start: bool = False
    tie_end: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        # Calculate graphical width based on duration and articulations
        self.graphical_width = self._calculate_width()
    
    def _calculate_width(self) -> float:
        """Calculate the graphical width needed for this note"""
        base_width = 20.0  # Base notehead width
        
        # Add width for accidentals
        if self.accidental:
            base_width += 15.0
        
        # Add width for articulations
        if self.articulation:
            base_width += 5.0
        
        # Shorter notes need more spacing for readability
        if self.duration in [NoteDuration.SIXTEENTH, NoteDuration.THIRTY_SECOND]:
            base_width += 10.0
        
        return base_width


@dataclass
class Rest(NotationElement):
    """A musical rest with duration"""
    
    def __post_init__(self):
        super().__post_init__()
        # Calculate graphical width based on duration
        self.graphical_width = self._calculate_width()
    
    def _calculate_width(self) -> float:
        """Calculate the graphical width needed for this rest"""
        # Rests generally need less space than notes
        base_width = 15.0
        
        # Whole and half rests need more space
        if self.duration in [NoteDuration.WHOLE, NoteDuration.HALF]:
            base_width = 25.0
        
        return base_width


@dataclass
class Chord(NotationElement):
    """A chord with multiple pitches"""
    pitches: List[str] = field(default_factory=list)
    accidentals: Dict[str, str] = field(default_factory=dict)  # pitch -> accidental
    
    def __post_init__(self):
        super().__post_init__()
        self.graphical_width = self._calculate_width()
    
    def _calculate_width(self) -> float:
        """Calculate width for chord (slightly wider than single note)"""
        base_width = 25.0
        
        # Add width for accidentals
        accidental_count = len(self.accidentals)
        base_width += accidental_count * 12.0
        
        return base_width


@dataclass
class TimeSignature:
    """Time signature information"""
    numerator: int = 4
    denominator: int = 4
    
    def get_beats_per_measure(self) -> float:
        """Get the number of beats per measure"""
        return float(self.numerator)
    
    def get_beat_unit(self) -> float:
        """Get the note value that gets one beat"""
        return 4.0 / float(self.denominator)  # Quarter note = 1.0


class TemporalMeasure(MeasureObject):
    """Enhanced measure with temporal content and automatic layout"""
    
    def __init__(self, measure_number: int = 1, time_signature: TimeSignature = None):
        super().__init__(measure_number, 160.0)  # Default width, will be recalculated
        
        # Temporal properties
        self.time_signature = time_signature or TimeSignature()
        self.notation_elements: List[NotationElement] = []
        self.content_density = 0.0  # Calculated from notation elements
        
        # Layout properties
        self.minimum_width = 80.0
        self.maximum_width = 400.0
        self.justified_width = 160.0
        self.system_position = 0  # Which system this measure is on
        
        # Spacing properties
        self.left_margin = 10.0   # Space before first element
        self.right_margin = 10.0  # Space after last element
        self.inter_element_spacing = 5.0  # Minimum space between elements
        
    def add_notation_element(self, element: NotationElement) -> bool:
        """Add a notation element at a specific beat position"""
        # Validate that the element fits within the measure
        if not self._can_fit_element(element):
            return False
        
        # Insert in chronological order
        insert_index = 0
        for i, existing in enumerate(self.notation_elements):
            if element.beat_position < existing.beat_position:
                insert_index = i
                break
            insert_index = i + 1
        
        self.notation_elements.insert(insert_index, element)
        
        # Recalculate layout
        self._recalculate_content_density()
        self._recalculate_width()
        
        return True
    
    def remove_notation_element(self, element: NotationElement) -> bool:
        """Remove a notation element"""
        if element in self.notation_elements:
            self.notation_elements.remove(element)
            self._recalculate_content_density()
            self._recalculate_width()
            return True
        return False
    
    def get_elements_at_beat(self, beat: float, tolerance: float = 0.001) -> List[NotationElement]:
        """Get all elements at a specific beat position"""
        return [elem for elem in self.notation_elements 
                if abs(elem.beat_position.beat - beat) < tolerance]
    
    def get_elements_in_range(self, start_beat: float, end_beat: float) -> List[NotationElement]:
        """Get all elements within a beat range"""
        return [elem for elem in self.notation_elements 
                if start_beat <= elem.beat_position.beat < end_beat]
    
    def is_beat_occupied(self, beat: float, tolerance: float = 0.001) -> bool:
        """Check if a beat position is already occupied"""
        return len(self.get_elements_at_beat(beat, tolerance)) > 0
    
    def get_next_available_beat(self, after_beat: float = 0.0) -> float:
        """Find the next available beat position"""
        occupied_beats = sorted([elem.beat_position.beat for elem in self.notation_elements])
        
        current_beat = after_beat
        beat_increment = 0.25  # Sixteenth note resolution
        max_beats = self.time_signature.get_beats_per_measure()
        
        while current_beat < max_beats:
            if not any(abs(current_beat - occupied) < 0.001 for occupied in occupied_beats):
                return current_beat
            current_beat += beat_increment
        
        return max_beats  # Return end of measure if no space
    
    def _can_fit_element(self, element: NotationElement) -> bool:
        """Check if an element can fit in this measure"""
        element_end = element.get_end_beat()
        max_beats = self.time_signature.get_beats_per_measure()
        
        # Check if element extends beyond measure
        if element_end > max_beats + 0.001:  # Small tolerance for floating point
            return False
        
        # Check for overlaps with existing elements
        for existing in self.notation_elements:
            existing_start = existing.beat_position.beat
            existing_end = existing.get_end_beat()
            element_start = element.beat_position.beat
            
            # Check for overlap
            if not (element_end <= existing_start or element_start >= existing_end):
                return False
        
        return True
    
    def _recalculate_content_density(self):
        """Calculate content density based on notation elements"""
        if not self.notation_elements:
            self.content_density = 0.0
            return
        
        # Calculate density based on number of elements and their complexity
        element_count = len(self.notation_elements)
        total_graphical_width = sum(elem.graphical_width for elem in self.notation_elements)
        
        # Normalize to 0.0-1.0 range
        # More elements and wider elements = higher density
        base_density = min(element_count / 8.0, 1.0)  # 8 elements = max density
        width_density = min(total_graphical_width / 200.0, 1.0)  # 200px = max density
        
        self.content_density = (base_density + width_density) / 2.0
    
    def _recalculate_width(self):
        """Calculate the natural width needed for this measure"""
        if not self.notation_elements:
            self.width = self.minimum_width
            return
        
        # Calculate required width based on content
        total_element_width = sum(elem.graphical_width for elem in self.notation_elements)
        spacing_width = max(0, len(self.notation_elements) - 1) * self.inter_element_spacing
        content_width = total_element_width + spacing_width + self.left_margin + self.right_margin
        
        # Apply density-based expansion for readability
        density_multiplier = 1.0 + (self.content_density * 0.5)  # Up to 50% expansion
        final_width = content_width * density_multiplier
        
        # Clamp to reasonable bounds
        self.width = max(self.minimum_width, min(final_width, self.maximum_width))
    
    def set_justified_width(self, width: float):
        """Set the justified width for this measure (system layout)"""
        self.justified_width = max(width, self.minimum_width)
    
    def get_element_positions(self) -> Dict[NotationElement, float]:
        """Calculate x positions for all elements within this measure"""
        positions = {}
        
        if not self.notation_elements:
            return positions
        
        # Use justified width if available, otherwise natural width
        available_width = self.justified_width - self.left_margin - self.right_margin
        
        # Calculate total content width
        total_element_width = sum(elem.graphical_width for elem in self.notation_elements)
        
        if total_element_width >= available_width:
            # Tight spacing - just fit elements
            current_x = self.left_margin
            for element in sorted(self.notation_elements, key=lambda e: e.beat_position.beat):
                positions[element] = current_x
                current_x += element.graphical_width
        else:
            # Proportional spacing based on beat positions
            max_beats = self.time_signature.get_beats_per_measure()
            
            for element in self.notation_elements:
                # Calculate proportional position within the measure
                beat_ratio = element.beat_position.beat / max_beats
                element_x = self.left_margin + (beat_ratio * available_width)
                positions[element] = element_x
        
        return positions
    
    def get_beat_position_x(self, beat: float) -> float:
        """Get the x position for a specific beat within this measure"""
        max_beats = self.time_signature.get_beats_per_measure()
        available_width = self.justified_width - self.left_margin - self.right_margin
        beat_ratio = beat / max_beats
        return self.left_margin + (beat_ratio * available_width)
    
    def find_beat_at_x(self, x_position: float) -> float:
        """Find the beat position at a given x coordinate within the measure"""
        if x_position <= self.left_margin:
            return 0.0
        
        available_width = self.justified_width - self.left_margin - self.right_margin
        if x_position >= self.left_margin + available_width:
            return self.time_signature.get_beats_per_measure()
        
        # Calculate beat position proportionally
        relative_x = x_position - self.left_margin
        beat_ratio = relative_x / available_width
        return beat_ratio * self.time_signature.get_beats_per_measure()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize temporal measure to dictionary"""
        base_dict = super().to_dict()
        
        # Add temporal-specific data
        base_dict.update({
            'time_signature': {
                'numerator': self.time_signature.numerator,
                'denominator': self.time_signature.denominator
            },
            'notation_elements': [self._serialize_element(elem) for elem in self.notation_elements],
            'content_density': self.content_density,
            'justified_width': self.justified_width,
            'system_position': self.system_position,
            'minimum_width': self.minimum_width,
            'maximum_width': self.maximum_width
        })
        
        return base_dict
    
    def _serialize_element(self, element: NotationElement) -> Dict[str, Any]:
        """Serialize a notation element"""
        base_data = {
            'type': element.__class__.__name__,
            'duration': element.duration.name,
            'beat_position': {
                'beat': element.beat_position.beat,
                'subdivision': element.beat_position.subdivision
            },
            'graphical_width': element.graphical_width,
            'id': element.id
        }
        
        # Add type-specific data
        if isinstance(element, Note):
            base_data.update({
                'pitch': element.pitch,
                'accidental': element.accidental,
                'articulation': element.articulation,
                'tie_start': element.tie_start,
                'tie_end': element.tie_end
            })
        elif isinstance(element, Chord):
            base_data.update({
                'pitches': element.pitches,
                'accidentals': element.accidentals
            })
        
        return base_data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemporalMeasure':
        """Create temporal measure from dictionary"""
        # Create time signature
        ts_data = data.get('time_signature', {})
        time_sig = TimeSignature(
            numerator=ts_data.get('numerator', 4),
            denominator=ts_data.get('denominator', 4)
        )
        
        # Create measure
        measure = cls(
            measure_number=data.get('measure_number', 1),
            time_signature=time_sig
        )
        
        # Restore basic properties
        measure.end_x = data.get('end_x', 160.0)
        measure.width = data.get('width', 160.0)
        measure.barline_type = data.get('barline_type', 'single')
        measure.content_density = data.get('content_density', 0.0)
        measure.justified_width = data.get('justified_width', 160.0)
        measure.system_position = data.get('system_position', 0)
        measure.minimum_width = data.get('minimum_width', 80.0)
        measure.maximum_width = data.get('maximum_width', 400.0)
        
        # Restore notation elements
        for elem_data in data.get('notation_elements', []):
            element = cls._deserialize_element(elem_data)
            if element:
                measure.notation_elements.append(element)
        
        return measure
    
    @classmethod
    def _deserialize_element(cls, data: Dict[str, Any]) -> Optional[NotationElement]:
        """Deserialize a notation element"""
        try:
            # Create beat position
            bp_data = data.get('beat_position', {})
            beat_pos = BeatPosition(
                beat=bp_data.get('beat', 0.0),
                subdivision=bp_data.get('subdivision', 1)
            )
            
            # Get duration
            duration = NoteDuration[data.get('duration', 'QUARTER')]
            
            # Create element based on type
            element_type = data.get('type', 'Note')
            
            if element_type == 'Note':
                element = Note(
                    duration=duration,
                    beat_position=beat_pos,
                    pitch=data.get('pitch', 'C4'),
                    accidental=data.get('accidental'),
                    articulation=data.get('articulation'),
                    tie_start=data.get('tie_start', False),
                    tie_end=data.get('tie_end', False),
                    id=data.get('id', '')
                )
            elif element_type == 'Rest':
                element = Rest(
                    duration=duration,
                    beat_position=beat_pos,
                    id=data.get('id', '')
                )
            elif element_type == 'Chord':
                element = Chord(
                    duration=duration,
                    beat_position=beat_pos,
                    pitches=data.get('pitches', []),
                    accidentals=data.get('accidentals', {}),
                    id=data.get('id', '')
                )
            else:
                return None
            
            element.graphical_width = data.get('graphical_width', element.graphical_width)
            return element
            
        except Exception as e:
            print(f"Error deserializing notation element: {e}")
            return None


class TemporalMeasureManager:
    """Enhanced measure manager with temporal capabilities"""
    
    def __init__(self, document=None):
        self.document = document
        self.measures: List[TemporalMeasure] = []
        self.settings = QSettings()
        
        # Layout settings
        self.measures_per_system = 4
        self.system_width = 800.0
        self.auto_justify = True
        
        # Default time signature
        self.default_time_signature = TimeSignature(4, 4)
    
    def create_measure(self, barline_type: str = "single", 
                      time_signature: TimeSignature = None) -> TemporalMeasure:
        """Create a new temporal measure"""
        measure_number = len(self.measures) + 1
        time_sig = time_signature or self.default_time_signature
        
        measure = TemporalMeasure(measure_number, time_sig)
        measure.barline_type = barline_type
        
        self.measures.append(measure)
        self._recalculate_layout()
        
        return measure
    
    def insert_measure_at_position(self, position: int, barline_type: str = "single") -> TemporalMeasure:
        """Insert a measure at a specific position"""
        time_sig = self.default_time_signature
        measure = TemporalMeasure(position + 1, time_sig)
        measure.barline_type = barline_type
        
        self.measures.insert(position, measure)
        
        # Renumber measures
        for i, m in enumerate(self.measures):
            m.measure_number = i + 1
        
        self._recalculate_layout()
        return measure
    
    def remove_measure(self, measure_number: int) -> bool:
        """Remove a measure by number"""
        if 1 <= measure_number <= len(self.measures):
            self.measures.pop(measure_number - 1)
            
            # Renumber remaining measures
            for i, m in enumerate(self.measures):
                m.measure_number = i + 1
            
            self._recalculate_layout()
            return True
        return False
    
    def add_note_to_measure(self, measure_number: int, note: Note) -> bool:
        """Add a note to a specific measure"""
        if 1 <= measure_number <= len(self.measures):
            measure = self.measures[measure_number - 1]
            return measure.add_notation_element(note)
        return False
    
    def add_rest_to_measure(self, measure_number: int, rest: Rest) -> bool:
        """Add a rest to a specific measure"""
        if 1 <= measure_number <= len(self.measures):
            measure = self.measures[measure_number - 1]
            return measure.add_notation_element(rest)
        return False
    
    def get_measure(self, measure_number: int) -> Optional[TemporalMeasure]:
        """Get a measure by number"""
        if 1 <= measure_number <= len(self.measures):
            return self.measures[measure_number - 1]
        return None
    
    def find_measure_at_x(self, x_position: float) -> Optional[TemporalMeasure]:
        """Find the measure at a given x position"""
        current_x = 0.0
        
        for measure in self.measures:
            if current_x <= x_position < current_x + measure.justified_width:
                return measure
            current_x += measure.justified_width
        
        return None
    
    def _recalculate_layout(self):
        """Recalculate the layout of all measures"""
        if not self.measures:
            return
        
        # Group measures into systems
        systems = []
        current_system = []
        
        for measure in self.measures:
            current_system.append(measure)
            
            # Check if we should start a new system
            if (len(current_system) >= self.measures_per_system or 
                measure.barline_type in ["final", "double"] or
                hasattr(measure, 'force_system_break') and measure.force_system_break):
                
                systems.append(current_system)
                current_system = []
        
        # Add remaining measures to last system
        if current_system:
            systems.append(current_system)
        
        # Justify each system
        for system_index, system_measures in enumerate(systems):
            self._justify_system(system_measures, system_index)
    
    def _justify_system(self, measures: List[TemporalMeasure], system_index: int):
        """Justify measures within a system"""
        if not measures or not self.auto_justify:
            return
        
        # Calculate total natural width
        total_natural_width = sum(m.width for m in measures)
        
        # Calculate available width
        available_width = self.system_width
        
        if total_natural_width <= available_width:
            # Distribute extra space proportionally
            extra_space = available_width - total_natural_width
            
            for measure in measures:
                proportion = measure.width / total_natural_width
                additional_width = extra_space * proportion
                measure.set_justified_width(measure.width + additional_width)
        else:
            # Compress measures to fit
            compression_ratio = available_width / total_natural_width
            
            for measure in measures:
                compressed_width = measure.width * compression_ratio
                # Don't compress below minimum width
                final_width = max(compressed_width, measure.minimum_width)
                measure.set_justified_width(final_width)
        
        # Update system positions
        for measure in measures:
            measure.system_position = system_index
    
    def get_total_width(self) -> float:
        """Get the total width of all measures"""
        return sum(m.justified_width for m in self.measures)
    
    def get_system_count(self) -> int:
        """Get the number of systems"""
        if not self.measures:
            return 0
        return max(m.system_position for m in self.measures) + 1
    
    def clear_all(self):
        """Clear all measures"""
        self.measures.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'measures': [m.to_dict() for m in self.measures],
            'measures_per_system': self.measures_per_system,
            'system_width': self.system_width,
            'auto_justify': self.auto_justify,
            'default_time_signature': {
                'numerator': self.default_time_signature.numerator,
                'denominator': self.default_time_signature.denominator
            }
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Restore from dictionary"""
        self.measures.clear()
        
        # Restore measures
        for m_data in data.get('measures', []):
            measure = TemporalMeasure.from_dict(m_data)
            self.measures.append(measure)
        
        # Restore settings
        self.measures_per_system = data.get('measures_per_system', 4)
        self.system_width = data.get('system_width', 800.0)
        self.auto_justify = data.get('auto_justify', True)
        
        # Restore default time signature
        ts_data = data.get('default_time_signature', {})
        self.default_time_signature = TimeSignature(
            numerator=ts_data.get('numerator', 4),
            denominator=ts_data.get('denominator', 4)
        )
        
        # Recalculate layout
        self._recalculate_layout()


# Helper functions for rhythm input
def create_note(pitch: str, duration: NoteDuration, beat: float) -> Note:
    """Helper function to create a note"""
    return Note(
        duration=duration,
        beat_position=BeatPosition(beat),
        pitch=pitch
    )

def create_rest(duration: NoteDuration, beat: float) -> Rest:
    """Helper function to create a rest"""
    return Rest(
        duration=duration,
        beat_position=BeatPosition(beat)
    )

def create_chord(pitches: List[str], duration: NoteDuration, beat: float) -> Chord:
    """Helper function to create a chord"""
    return Chord(
        duration=duration,
        beat_position=BeatPosition(beat),
        pitches=pitches
    ) 