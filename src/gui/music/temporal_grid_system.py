"""
ONOTE Temporal Grid System - Complete Reconstruction

This module implements the comprehensive temporal grid system according to the detailed specifications:

1. TEMPORAL GRID STRUCTURE:
   - Time signatures, tempo, PPQN, tick grid, quantization grid
   - Underlying timeline with tick-based positioning
   - Beat-alignment rules across multiple staves

2. NOTATION LAYER:
   - Notes entered visually into measures aligned with barlines
   - Symbolic durations that rely on temporal grid for spacing
   - Dynamic spacing based on notation density

3. CONTENT MERGING MODEL:
   - Measures are divisions of continuous temporal grid
   - "Deleting" barlines merges temporal content (never removes measures)
   - Consecutive renumbering after content merge operations

4. DYNAMIC LAYOUT FLOW:
   - Parse content → build temporal map → determine spacing demands
   - Adjust spacing grid → align vertically → render with justification
"""

from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import copy
import math
from PyQt6.QtCore import QObject, pyqtSignal, QSettings

from .temporal_measure_system import (
    TemporalMeasure, TemporalMeasureManager, 
    NotationElement, Note, Rest, Chord,
    NoteDuration, BeatPosition, TimeSignature
)
from .measure_object import MeasureObject


class TemporalGridResolution(Enum):
    """Standard PPQN resolutions for temporal grid"""
    PPQN_96 = 96      # Basic resolution
    PPQN_192 = 192    # Standard resolution  
    PPQN_480 = 480    # High resolution (recommended)
    PPQN_960 = 960    # Maximum resolution


@dataclass
class TemporalGridSettings:
    """Configuration for the temporal grid system"""
    ppqn: int = 480                    # Pulses per quarter note
    default_tempo: float = 120.0       # BPM
    default_time_signature: TimeSignature = field(default_factory=lambda: TimeSignature(4, 4))
    quantization_grid: float = 0.25    # Sixteenth note quantization
    
    # Spacing settings
    proportional_spacing: bool = True   # vs optical spacing
    minimum_measure_width: float = 80.0
    maximum_measure_width: float = 500.0
    beat_spacing_factor: float = 1.0    # Multiplier for beat spacing
    
    # Content density settings
    density_expansion_factor: float = 0.3  # How much dense content expands spacing
    collision_padding: float = 5.0         # Minimum space between elements
    
    # Justification settings
    auto_justify: bool = True
    system_width: float = 800.0
    measures_per_system: int = 4


@dataclass
class TemporalPosition:
    """Precise position within the temporal grid"""
    measure_number: int
    beat: float
    tick: int
    
    def __post_init__(self):
        # Validate values
        if self.measure_number < 1:
            self.measure_number = 1
        if self.beat < 0:
            self.beat = 0.0
        if self.tick < 0:
            self.tick = 0
    
    def to_absolute_ticks(self, ppqn: int, time_signature: TimeSignature) -> int:
        """Convert to absolute tick position from start of score"""
        ticks_per_measure = int(ppqn * time_signature.get_beats_per_measure())
        measure_ticks = (self.measure_number - 1) * ticks_per_measure
        beat_ticks = int(self.beat * ppqn)
        return measure_ticks + beat_ticks + self.tick
    
    @classmethod
    def from_absolute_ticks(cls, absolute_ticks: int, ppqn: int, time_signature: TimeSignature) -> 'TemporalPosition':
        """Create from absolute tick position"""
        ticks_per_measure = int(ppqn * time_signature.get_beats_per_measure())
        
        measure_number = (absolute_ticks // ticks_per_measure) + 1
        remaining_ticks = absolute_ticks % ticks_per_measure
        
        beat = remaining_ticks // ppqn
        tick = remaining_ticks % ppqn
        
        return cls(measure_number, float(beat), tick)


class TemporalGridMeasure(TemporalMeasure):
    """Enhanced temporal measure with grid-based positioning"""
    
    def __init__(self, measure_number: int = 1, time_signature: TimeSignature = None, grid_settings: TemporalGridSettings = None):
        super().__init__(measure_number, time_signature)
        
        self.grid_settings = grid_settings or TemporalGridSettings()
        self.temporal_content: List[Tuple[TemporalPosition, NotationElement]] = []
        
        # Grid-specific properties
        self.tick_positions: Dict[int, List[NotationElement]] = {}  # tick -> elements
        self.beat_grid: Dict[float, List[NotationElement]] = {}     # beat -> elements
        self.quantization_grid: Dict[float, List[NotationElement]] = {}  # quantized positions
        
        # Dynamic spacing properties
        self.content_complexity_score = 0.0
        self.spacing_demands: Dict[str, float] = {}  # type -> required width
        self.optical_adjustments: Dict[str, float] = {}  # special spacing adjustments
        
        # Layout calculation results
        self.calculated_natural_width = 0.0
        self.calculated_justified_width = 0.0
        self.element_positions: Dict[str, float] = {}  # element_id -> x_position
        
        # Merge tracking (for content merging operations)
        self.merged_from_measures: List[int] = []  # Track which measures were merged into this one
        self.content_sources: Dict[str, int] = {}  # element_id -> original measure number
    
    def add_temporal_content(self, temporal_pos: TemporalPosition, element: NotationElement) -> bool:
        """Add content at a specific temporal position"""
        # Validate position is within this measure
        if temporal_pos.measure_number != self.measure_number:
            return False
        
        # Check if position is available
        if not self._is_position_available(temporal_pos, element):
            return False
        
        # Add to temporal content
        self.temporal_content.append((temporal_pos, element))
        
        # Update grid structures
        self._update_grid_structures(temporal_pos, element)
        
        # Recalculate layout
        self._recalculate_content_complexity()
        self._recalculate_spacing_demands()
        self._recalculate_natural_width()
        
        return True
    
    def merge_content_from_measure(self, other_measure: 'TemporalGridMeasure') -> bool:
        """Merge temporal content from another measure"""
        print(f"TEMPORAL_GRID: Merging content from measure #{other_measure.measure_number} into measure #{self.measure_number}")
        
        # Track merge operation
        self.merged_from_measures.append(other_measure.measure_number)
        
        # Merge temporal content
        for temporal_pos, element in other_measure.temporal_content:
            # Adjust temporal position to this measure
            adjusted_pos = TemporalPosition(
                measure_number=self.measure_number,
                beat=temporal_pos.beat,
                tick=temporal_pos.tick
            )
            
            # Track source (use element id if available, otherwise generate one)
            element_id = element.id if element.id else f"element_{id(element)}"
            element.id = element_id  # Ensure element has an id
            self.content_sources[element_id] = other_measure.measure_number
            
            # Try to add content
            if not self.add_temporal_content(adjusted_pos, element):
                print(f"TEMPORAL_GRID: Warning - Could not merge element from measure #{other_measure.measure_number}")
        
        print(f"TEMPORAL_GRID: Merged {len(other_measure.temporal_content)} elements from measure #{other_measure.measure_number}")
        return True
    
    def _is_position_available(self, temporal_pos: TemporalPosition, element: NotationElement) -> bool:
        """Check if a temporal position is available for the given element"""
        element_end_beat = temporal_pos.beat + element.get_beat_duration()
        
        # Check against existing content
        for existing_pos, existing_element in self.temporal_content:
            existing_end_beat = existing_pos.beat + existing_element.get_beat_duration()
            
            # Check for overlap
            if not (element_end_beat <= existing_pos.beat or temporal_pos.beat >= existing_end_beat):
                return False
        
        # Check measure boundaries
        max_beats = self.time_signature.get_beats_per_measure()
        if element_end_beat > max_beats:
            return False
        
        return True
    
    def _update_grid_structures(self, temporal_pos: TemporalPosition, element: NotationElement):
        """Update internal grid structures with new element"""
        # Update tick positions
        absolute_tick = temporal_pos.to_absolute_ticks(self.grid_settings.ppqn, self.time_signature)
        if absolute_tick not in self.tick_positions:
            self.tick_positions[absolute_tick] = []
        self.tick_positions[absolute_tick].append(element)
        
        # Update beat grid
        if temporal_pos.beat not in self.beat_grid:
            self.beat_grid[temporal_pos.beat] = []
        self.beat_grid[temporal_pos.beat].append(element)
        
        # Update quantization grid
        quantized_beat = self._quantize_beat(temporal_pos.beat)
        if quantized_beat not in self.quantization_grid:
            self.quantization_grid[quantized_beat] = []
        self.quantization_grid[quantized_beat].append(element)
    
    def _quantize_beat(self, beat: float) -> float:
        """Quantize a beat to the grid resolution"""
        grid_resolution = self.grid_settings.quantization_grid
        return round(beat / grid_resolution) * grid_resolution
    
    def _recalculate_content_complexity(self):
        """Calculate content complexity score based on temporal content"""
        if not self.temporal_content:
            self.content_complexity_score = 0.0
            return
        
        # Factors contributing to complexity:
        # 1. Number of elements
        element_count_factor = len(self.temporal_content) / 8.0  # Normalized to 8 elements
        
        # 2. Rhythmic diversity (different durations)
        unique_durations = set(element.duration for _, element in self.temporal_content)
        duration_diversity_factor = len(unique_durations) / 6.0  # Normalized to 6 different durations
        
        # 3. Temporal density (how close elements are to each other)
        sorted_content = sorted(self.temporal_content, key=lambda x: x[0].beat)
        density_scores = []
        
        for i in range(len(sorted_content) - 1):
            current_pos = sorted_content[i][0]
            next_pos = sorted_content[i + 1][0]
            current_element = sorted_content[i][1]
            
            current_end = current_pos.beat + current_element.get_beat_duration()
            gap = next_pos.beat - current_end
            
            # Smaller gaps = higher density
            density_scores.append(max(0, 1.0 - gap))
        
        temporal_density_factor = sum(density_scores) / max(1, len(density_scores))
        
        # 4. Polyphonic complexity (overlapping elements)
        overlap_count = 0
        for i, (pos1, elem1) in enumerate(self.temporal_content):
            end1 = pos1.beat + elem1.get_beat_duration()
            for j, (pos2, elem2) in enumerate(self.temporal_content):
                if i != j:
                    end2 = pos2.beat + elem2.get_beat_duration()
                    if not (end1 <= pos2.beat or pos1.beat >= end2):
                        overlap_count += 1
        
        polyphonic_factor = overlap_count / max(1, len(self.temporal_content))
        
        # Combine factors
        self.content_complexity_score = min(1.0, (
            element_count_factor * 0.3 +
            duration_diversity_factor * 0.2 +
            temporal_density_factor * 0.3 +
            polyphonic_factor * 0.2
        ))
        
        print(f"TEMPORAL_GRID: Measure #{self.measure_number} complexity score: {self.content_complexity_score:.3f}")
    
    def _recalculate_spacing_demands(self):
        """Calculate spacing demands based on content types"""
        self.spacing_demands.clear()
        
        # Base spacing requirements
        base_spacing = 20.0  # Base space per element
        
        # Analyze content for special spacing needs
        for temporal_pos, element in self.temporal_content:
            element_type = element.__class__.__name__
            
            # Duration-based spacing
            duration_multiplier = self._get_duration_spacing_multiplier(element.duration)
            required_space = base_spacing * duration_multiplier
            
            # Type-specific adjustments
            if isinstance(element, Note):
                # Check for accidentals (need more space)
                if hasattr(element, 'accidental') and element.accidental:
                    required_space *= 1.3
                
                # Check for articulations
                if hasattr(element, 'articulation') and element.articulation:
                    required_space *= 1.1
            
            elif isinstance(element, Chord):
                # Chords need more space
                required_space *= 1.4
            
            elif isinstance(element, Rest):
                # Rests can be more compact
                required_space *= 0.8
            
            # Store spacing demand
            element_id = element.id if element.id else f"element_{id(element)}"
            element.id = element_id  # Ensure element has an id
            self.spacing_demands[element_id] = required_space
        
        # Calculate optical adjustments
        self._calculate_optical_adjustments()
    
    def _get_duration_spacing_multiplier(self, duration: NoteDuration) -> float:
        """Get spacing multiplier based on note duration"""
        duration_multipliers = {
            NoteDuration.WHOLE: 2.0,
            NoteDuration.HALF: 1.5,
            NoteDuration.QUARTER: 1.0,
            NoteDuration.EIGHTH: 0.8,
            NoteDuration.SIXTEENTH: 0.7,
            NoteDuration.THIRTY_SECOND: 0.6,
            NoteDuration.SIXTY_FOURTH: 0.5,
            NoteDuration.DOTTED_HALF: 1.8,
            NoteDuration.DOTTED_QUARTER: 1.2,
            NoteDuration.DOTTED_EIGHTH: 0.9,
            NoteDuration.DOTTED_SIXTEENTH: 0.8,
            NoteDuration.QUARTER_TRIPLET: 0.9,
            NoteDuration.EIGHTH_TRIPLET: 0.7,
            NoteDuration.SIXTEENTH_TRIPLET: 0.6,
        }
        return duration_multipliers.get(duration, 1.0)
    
    def _calculate_optical_adjustments(self):
        """Calculate optical spacing adjustments for readability"""
        self.optical_adjustments.clear()
        
        # Sort content by beat position
        sorted_content = sorted(self.temporal_content, key=lambda x: x[0].beat)
        
        for i, (temporal_pos, element) in enumerate(sorted_content):
            adjustments = 0.0
            
            # Check preceding element
            if i > 0:
                prev_pos, prev_element = sorted_content[i - 1]
                prev_end = prev_pos.beat + prev_element.get_beat_duration()
                gap = temporal_pos.beat - prev_end
                
                # If gap is very small, add optical space
                if gap < 0.25:  # Less than sixteenth note
                    adjustments += 10.0
            
            # Check following element
            if i < len(sorted_content) - 1:
                next_pos, next_element = sorted_content[i + 1]
                element_end = temporal_pos.beat + element.get_beat_duration()
                gap = next_pos.beat - element_end
                
                # If gap is very small, add optical space
                if gap < 0.25:
                    adjustments += 10.0
            
            # Store adjustment
            if adjustments > 0:
                element_id = element.id if element.id else f"element_{id(element)}"
                element.id = element_id  # Ensure element has an id
                self.optical_adjustments[element_id] = adjustments
    
    def _recalculate_natural_width(self):
        """Calculate the natural width required for this measure"""
        if not self.temporal_content:
            self.calculated_natural_width = self.grid_settings.minimum_measure_width
            return
        
        # Base width calculation
        base_width = self.left_margin + self.right_margin
        
        # Add spacing demands
        total_spacing_demand = sum(self.spacing_demands.values())
        
        # Add optical adjustments
        total_optical_adjustment = sum(self.optical_adjustments.values())
        
        # Add complexity expansion
        complexity_expansion = self.content_complexity_score * self.grid_settings.density_expansion_factor * 100
        
        # Calculate final width
        content_width = total_spacing_demand + total_optical_adjustment + complexity_expansion
        natural_width = base_width + content_width
        
        # Apply bounds
        self.calculated_natural_width = max(
            self.grid_settings.minimum_measure_width,
            min(natural_width, self.grid_settings.maximum_measure_width)
        )
        
        print(f"TEMPORAL_GRID: Measure #{self.measure_number} natural width: {self.calculated_natural_width:.1f}px")
        print(f"  - Base: {base_width:.1f}px, Content: {content_width:.1f}px, Complexity: {complexity_expansion:.1f}px")
    
    def set_justified_width(self, width: float):
        """Set justified width and recalculate element positions"""
        super().set_justified_width(width)
        self.calculated_justified_width = width
        self._recalculate_element_positions()
    
    def _recalculate_element_positions(self):
        """Calculate precise x positions for all elements"""
        self.element_positions.clear()
        
        if not self.temporal_content:
            return
        
        # Available space for content
        available_width = self.calculated_justified_width - self.left_margin - self.right_margin
        
        # Sort content by beat position
        sorted_content = sorted(self.temporal_content, key=lambda x: x[0].beat)
        
        if self.grid_settings.proportional_spacing:
            # Proportional spacing based on beat positions
            max_beats = self.time_signature.get_beats_per_measure()
            
            for temporal_pos, element in sorted_content:
                beat_ratio = temporal_pos.beat / max_beats
                base_x = self.left_margin + (beat_ratio * available_width)
                
                # Apply optical adjustments
                element_id = element.id if element.id else f"element_{id(element)}"
                element.id = element_id  # Ensure element has an id
                adjustment = self.optical_adjustments.get(element_id, 0.0)
                
                final_x = base_x + adjustment
                self.element_positions[element_id] = final_x
        else:
            # Content-based spacing
            total_spacing_demand = sum(self.spacing_demands.values())
            
            if total_spacing_demand > 0:
                current_x = self.left_margin
                
                for temporal_pos, element in sorted_content:
                    element_id = element.id if element.id else f"element_{id(element)}"
                    element.id = element_id  # Ensure element has an id
                    required_space = self.spacing_demands.get(element_id, 20.0)
                    
                    # Scale spacing to fit available width
                    scaled_space = (required_space / total_spacing_demand) * available_width
                    
                    self.element_positions[element_id] = current_x
                    current_x += scaled_space
    
    def get_element_at_position(self, x_position: float) -> Optional[NotationElement]:
        """Find element at specific x position"""
        for element_id, element_x in self.element_positions.items():
            element_width = self.spacing_demands.get(element_id, 20.0)
            if element_x <= x_position <= element_x + element_width:
                # Find the element object with this ID
                for temporal_pos, element in self.temporal_content:
                    if element.id == element_id:
                        return element
        return None
    
    def get_temporal_position_at_x(self, x_position: float) -> TemporalPosition:
        """Get temporal position at specific x coordinate"""
        if x_position <= self.left_margin:
            return TemporalPosition(self.measure_number, 0.0, 0)
        
        available_width = self.calculated_justified_width - self.left_margin - self.right_margin
        if x_position >= self.left_margin + available_width:
            max_beats = self.time_signature.get_beats_per_measure()
            return TemporalPosition(self.measure_number, max_beats, 0)
        
        # Calculate beat position proportionally
        relative_x = x_position - self.left_margin
        beat_ratio = relative_x / available_width
        beat = beat_ratio * self.time_signature.get_beats_per_measure()
        
        # Quantize to grid
        quantized_beat = self._quantize_beat(beat)
        
        # Calculate tick within beat
        beat_fraction = beat - int(beat)
        tick = int(beat_fraction * self.grid_settings.ppqn)
        
        return TemporalPosition(self.measure_number, quantized_beat, tick)


class TemporalGridSystem(QObject):
    """Complete temporal grid system managing the timeline and measures"""
    
    # Signals
    temporal_structure_changed = pyqtSignal()
    content_merged = pyqtSignal(int, int)  # source_measure, target_measure
    measure_layout_changed = pyqtSignal()
    grid_settings_changed = pyqtSignal()
    
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        self.grid_settings = TemporalGridSettings()
        
        # Temporal grid state
        self.measures: Dict[int, TemporalGridMeasure] = {}
        self.global_timeline: Dict[int, List[NotationElement]] = {}  # absolute_tick -> elements
        self.tempo_changes: Dict[int, float] = {0: 120.0}  # tick -> BPM
        
        # Layout state
        self.systems: List[List[int]] = []  # List of measure number lists
        self.justified_system_widths: Dict[int, float] = {}  # system_index -> width
        
        # Load settings
        self._load_settings()
        
        print("TEMPORAL_GRID: Initialized temporal grid system")
        print(f"  - PPQN: {self.grid_settings.ppqn}")
        print(f"  - Default tempo: {self.grid_settings.default_tempo} BPM")
        print(f"  - Quantization: {self.grid_settings.quantization_grid} beats")
    
    def create_initial_measure(self) -> TemporalGridMeasure:
        """Create the initial measure for an empty score"""
        measure = TemporalGridMeasure(1, self.grid_settings.default_time_signature, self.grid_settings)
        self.measures[1] = measure
        
        # Initialize layout
        self._recalculate_systems()
        
        print("TEMPORAL_GRID: Created initial measure #1")
        return measure
    
    def insert_barline_at_position(self, x_position: float, barline_type: str = "single") -> Optional[TemporalGridMeasure]:
        """Insert barline using temporal grid model - splits measures without removing content"""
        print(f"TEMPORAL_GRID: Insert barline at x={x_position}, type={barline_type}")
        
        # Handle empty score
        if not self.measures:
            return self.create_initial_measure()
        
        # Find target measure
        target_measure = self._find_measure_at_position(x_position)
        if not target_measure:
            print("TEMPORAL_GRID: No measure found at position, creating new measure")
            return self._create_measure_at_end(barline_type)
        
        # Split the target measure
        return self._split_measure(target_measure, x_position, barline_type)
    
    def remove_barline_at_measure(self, measure_number: int) -> bool:
        """Remove barline by merging content with adjacent measure"""
        print(f"TEMPORAL_GRID: Remove barline at measure #{measure_number}")
        
        if measure_number not in self.measures:
            print(f"TEMPORAL_GRID: Measure #{measure_number} not found")
            return False
        
        # Cannot remove the last remaining measure
        if len(self.measures) == 1:
            print("TEMPORAL_GRID: Cannot remove the last measure")
            return False
        
        # Find adjacent measure to merge with
        target_measure = self.measures[measure_number]
        
        # Try to merge with previous measure first
        if measure_number > 1 and (measure_number - 1) in self.measures:
            prev_measure = self.measures[measure_number - 1]
            return self._merge_measures(prev_measure, target_measure)
        
        # Otherwise merge with next measure
        elif (measure_number + 1) in self.measures:
            next_measure = self.measures[measure_number + 1]
            return self._merge_measures(target_measure, next_measure)
        
        print(f"TEMPORAL_GRID: No adjacent measure found to merge with #{measure_number}")
        return False
    
    def _find_measure_at_position(self, x_position: float) -> Optional[TemporalGridMeasure]:
        """Find measure containing the given x position"""
        current_x = 0.0
        
        for measure_num in sorted(self.measures.keys()):
            measure = self.measures[measure_num]
            measure_width = measure.calculated_justified_width or measure.calculated_natural_width
            
            if current_x <= x_position < current_x + measure_width:
                return measure
            
            current_x += measure_width
        
        return None
    
    def _create_measure_at_end(self, barline_type: str) -> TemporalGridMeasure:
        """Create a new measure at the end of the score"""
        new_measure_number = max(self.measures.keys()) + 1
        measure = TemporalGridMeasure(new_measure_number, self.grid_settings.default_time_signature, self.grid_settings)
        measure.barline_type = barline_type
        
        self.measures[new_measure_number] = measure
        self._recalculate_systems()
        
        print(f"TEMPORAL_GRID: Created measure #{new_measure_number} at end")
        return measure
    
    def _split_measure(self, target_measure: TemporalGridMeasure, x_position: float, barline_type: str) -> TemporalGridMeasure:
        """
        Split a measure at the given position.
        
        ONOTE SPECIFICATION - Rule 2:
        - New barline index = barline_to_left.index + 1
        - Measure to the left retains its index
        - All measures/barlines to the right are incremented
        - Click position determines WHICH measure to split, but actual positions
          are recalculated by Rule 1 (equal division) after splitting
        """
        target_number = target_measure.measure_number
        
        print(f"TEMPORAL_GRID: Splitting measure #{target_number} at x={x_position}")
        
        # Calculate split point in temporal terms (for content division)
        # Note: Actual barline positions will be recalculated by Rule 1 after splitting
        split_temporal_pos = target_measure.get_temporal_position_at_x(x_position)
        split_beat = split_temporal_pos.beat
        
        print(f"TEMPORAL_GRID: Split at beat {split_beat}")
        
        # Rule 2: New barline index = barline_to_left.index + 1
        # The barline to the left is at target_number, so new barline is target_number + 1
        new_measure_number = target_number + 1
        
        # Rule 2: Shift all measures after target to make room (increment all to the right)
        self._shift_measures_after(target_number)
        
        # Create new measure
        new_measure = TemporalGridMeasure(new_measure_number, target_measure.time_signature, self.grid_settings)
        new_measure.barline_type = barline_type
        
        # Split temporal content
        left_content = []
        right_content = []
        
        for temporal_pos, element in target_measure.temporal_content:
            element_end = temporal_pos.beat + element.get_beat_duration()
            
            if temporal_pos.beat < split_beat:
                # Element starts before split
                if element_end <= split_beat:
                    # Element ends before split - goes to left
                    left_content.append((temporal_pos, element))
                else:
                    # Element crosses split - need to handle this case
                    # For now, put in left measure (could be improved to split the element)
                    left_content.append((temporal_pos, element))
                    print(f"TEMPORAL_GRID: Element crosses split point - keeping in left measure")
            else:
                # Element starts after split - goes to right
                # Adjust temporal position for new measure
                adjusted_pos = TemporalPosition(
                    new_measure_number,
                    temporal_pos.beat - split_beat,
                    temporal_pos.tick
                )
                right_content.append((adjusted_pos, element))
        
        # Update target measure content
        target_measure.temporal_content = left_content
        target_measure._recalculate_content_complexity()
        target_measure._recalculate_spacing_demands()
        target_measure._recalculate_natural_width()
        
        # Set new measure content
        new_measure.temporal_content = right_content
        new_measure._recalculate_content_complexity()
        new_measure._recalculate_spacing_demands()
        new_measure._recalculate_natural_width()
        
        # Add to measures
        self.measures[new_measure_number] = new_measure
        
        print(f"TEMPORAL_GRID: Split complete - {len(left_content)} elements in left, {len(right_content)} elements in right")
        
        # Recalculate layout
        self._recalculate_systems()
        
        # Emit signals
        self.temporal_structure_changed.emit()
        self.measure_layout_changed.emit()
        
        return new_measure
    
    def _merge_measures(self, target_measure: TemporalGridMeasure, source_measure: TemporalGridMeasure) -> bool:
        """Merge source measure content into target measure"""
        target_number = target_measure.measure_number
        source_number = source_measure.measure_number
        
        print(f"TEMPORAL_GRID: Merging measure #{source_number} into measure #{target_number}")
        
        # Merge content
        success = target_measure.merge_content_from_measure(source_measure)
        
        if success:
            # Remove source measure
            del self.measures[source_number]
            
            # Renumber measures to maintain sequence
            self._renumber_measures_consecutively()
            
            # Recalculate layout
            self._recalculate_systems()
            
            # Emit signals
            self.content_merged.emit(source_number, target_number)
            self.temporal_structure_changed.emit()
            self.measure_layout_changed.emit()
            
            print(f"TEMPORAL_GRID: Successfully merged measures")
            return True
        
        print(f"TEMPORAL_GRID: Failed to merge measures")
        return False
    
    def _shift_measures_after(self, after_measure: int):
        """Shift all measures after the given number by +1"""
        measures_to_shift = [num for num in self.measures.keys() if num > after_measure]
        measures_to_shift.sort(reverse=True)  # Process in reverse order to avoid conflicts
        
        for old_num in measures_to_shift:
            new_num = old_num + 1
            measure = self.measures[old_num]
            measure.measure_number = new_num
            
            # Update dictionary
            self.measures[new_num] = measure
            del self.measures[old_num]
            
            print(f"TEMPORAL_GRID: Shifted measure #{old_num} → #{new_num}")
    
    def _renumber_measures_consecutively(self):
        """Renumber all measures consecutively starting from 1"""
        sorted_measures = sorted(self.measures.values(), key=lambda m: m.measure_number)
        new_measures = {}
        
        for i, measure in enumerate(sorted_measures):
            new_number = i + 1
            old_number = measure.measure_number
            
            measure.measure_number = new_number
            new_measures[new_number] = measure
            
            if old_number != new_number:
                print(f"TEMPORAL_GRID: Renumbered measure #{old_number} → #{new_number}")
        
        self.measures = new_measures
        print(f"TEMPORAL_GRID: Renumbering complete - {len(self.measures)} measures")
    
    def _recalculate_systems(self):
        """
        Recalculate system layout with justification.
        
        ONOTE SPECIFICATION: System wrapping treats the full score (all nested systems)
        as one "thick" line unit. When measures_per_system is exceeded, all staves
        in all systems wrap together to the next line.
        """
        if not self.measures:
            self.systems = []
            return
        
        # Group measures into systems based on measures_per_system constraint
        # ONOTE SPEC: Full score wraps as one unit - all staves wrap together
        self.systems = []
        current_system = []
        
        for measure_num in sorted(self.measures.keys()):
            measure = self.measures[measure_num]
            current_system.append(measure_num)
            
            # ONOTE SPEC: Wrap when MPS exceeded or when encountering final/double barline
            # This forces all staves in the score to wrap together (treating score as "thick" line)
            if (len(current_system) >= self.grid_settings.measures_per_system or 
                measure.barline_type in ["final", "double"]):
                
                self.systems.append(current_system)
                current_system = []
        
        # Add remaining measures to last system
        if current_system:
            self.systems.append(current_system)
        
        # Justify each system
        for system_index, system_measures in enumerate(self.systems):
            self._justify_system(system_measures, system_index)
        
        print(f"TEMPORAL_GRID: Recalculated {len(self.systems)} systems")
    
    def _justify_system(self, measure_numbers: List[int], system_index: int):
        """Justify measures within a system"""
        if not measure_numbers:
            return
        
        measures = [self.measures[num] for num in measure_numbers]
        
        # Calculate total natural width
        total_natural_width = sum(m.calculated_natural_width for m in measures)
        
        # Available width for this system
        available_width = self.grid_settings.system_width
        
        if self.grid_settings.auto_justify:
            if total_natural_width <= available_width:
                # Distribute extra space proportionally
                extra_space = available_width - total_natural_width
                
                for measure in measures:
                    if total_natural_width > 0:
                        proportion = measure.calculated_natural_width / total_natural_width
                        additional_width = extra_space * proportion
                        justified_width = measure.calculated_natural_width + additional_width
                    else:
                        justified_width = available_width / len(measures)
                    
                    measure.set_justified_width(justified_width)
            else:
                # Compress proportionally
                compression_ratio = available_width / total_natural_width
                
                for measure in measures:
                    compressed_width = measure.calculated_natural_width * compression_ratio
                    # Don't compress below minimum
                    final_width = max(compressed_width, self.grid_settings.minimum_measure_width)
                    measure.set_justified_width(final_width)
        else:
            # No justification - use natural widths
            for measure in measures:
                measure.set_justified_width(measure.calculated_natural_width)
        
        # Store system width
        self.justified_system_widths[system_index] = sum(m.calculated_justified_width for m in measures)
    
    def get_measures_for_document(self) -> Dict[int, MeasureObject]:
        """Convert temporal grid measures to document measure objects"""
        document_measures = {}
        
        for measure_num, temporal_measure in self.measures.items():
            # Create MeasureObject for document compatibility
            measure_obj = MeasureObject(
                measure_number=measure_num,
                end_x=temporal_measure.calculated_justified_width,
                document=self.document,
                barline_type=temporal_measure.barline_type
            )
            
            # Copy relevant properties
            measure_obj.width = temporal_measure.calculated_justified_width
            measure_obj.x_position = 0.0  # Will be set by layout system
            
            document_measures[measure_num] = measure_obj
        
        return document_measures
    
    def sync_from_document(self, document_measures: Dict[int, MeasureObject]):
        """Sync temporal grid from document measures (for compatibility)"""
        print("TEMPORAL_GRID: Syncing from document measures")
        
        for measure_num, measure_obj in document_measures.items():
            if measure_num not in self.measures:
                # Create new temporal measure
                temporal_measure = TemporalGridMeasure(
                    measure_number=measure_num,
                    time_signature=self.grid_settings.default_time_signature,
                    grid_settings=self.grid_settings
                )
                temporal_measure.barline_type = getattr(measure_obj, 'barline_type', 'single')
                self.measures[measure_num] = temporal_measure
                
                print(f"TEMPORAL_GRID: Created temporal measure #{measure_num} from document")
        
        # Recalculate layout
        self._recalculate_systems()
    
    def _load_settings(self):
        """Load grid settings from QSettings"""
        settings = QSettings()
        
        # Load PPQN
        ppqn_value = settings.value("temporal_grid/ppqn", self.grid_settings.ppqn)
        self.grid_settings.ppqn = int(ppqn_value)
        
        # Load tempo
        tempo_value = settings.value("temporal_grid/default_tempo", self.grid_settings.default_tempo)
        self.grid_settings.default_tempo = float(tempo_value)
        
        # Load time signature
        ts_num = settings.value("temporal_grid/time_signature_numerator", 4)
        ts_den = settings.value("temporal_grid/time_signature_denominator", 4)
        self.grid_settings.default_time_signature = TimeSignature(int(ts_num), int(ts_den))
        
        # Load spacing settings
        self.grid_settings.minimum_measure_width = float(settings.value("temporal_grid/minimum_measure_width", 80.0))
        self.grid_settings.maximum_measure_width = float(settings.value("temporal_grid/maximum_measure_width", 500.0))
        self.grid_settings.system_width = float(settings.value("temporal_grid/system_width", 800.0))
        self.grid_settings.measures_per_system = int(settings.value("temporal_grid/measures_per_system", 4))
        
        print("TEMPORAL_GRID: Loaded settings from QSettings")
    
    def save_settings(self):
        """Save grid settings to QSettings"""
        settings = QSettings()
        
        settings.setValue("temporal_grid/ppqn", self.grid_settings.ppqn)
        settings.setValue("temporal_grid/default_tempo", self.grid_settings.default_tempo)
        settings.setValue("temporal_grid/time_signature_numerator", self.grid_settings.default_time_signature.numerator)
        settings.setValue("temporal_grid/time_signature_denominator", self.grid_settings.default_time_signature.denominator)
        settings.setValue("temporal_grid/minimum_measure_width", self.grid_settings.minimum_measure_width)
        settings.setValue("temporal_grid/maximum_measure_width", self.grid_settings.maximum_measure_width)
        settings.setValue("temporal_grid/system_width", self.grid_settings.system_width)
        settings.setValue("temporal_grid/measures_per_system", self.grid_settings.measures_per_system)
        
        print("TEMPORAL_GRID: Saved settings to QSettings")
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information about the temporal grid state"""
        return {
            "measure_count": len(self.measures),
            "system_count": len(self.systems),
            "measures": {
                num: {
                    "content_count": len(measure.temporal_content),
                    "complexity_score": measure.content_complexity_score,
                    "natural_width": measure.calculated_natural_width,
                    "justified_width": measure.calculated_justified_width,
                    "merged_from": measure.merged_from_measures
                }
                for num, measure in self.measures.items()
            },
            "systems": self.systems,
            "grid_settings": {
                "ppqn": self.grid_settings.ppqn,
                "tempo": self.grid_settings.default_tempo,
                "time_signature": f"{self.grid_settings.default_time_signature.numerator}/{self.grid_settings.default_time_signature.denominator}",
                "measures_per_system": self.grid_settings.measures_per_system
            }
        } 