"""
Comprehensive Measure Management System for ONOTE

This module implements the proper measure-based architecture where:
1. Barlines are boundaries of measures, not independent visual elements
2. Measures have dynamic width based on content density  
3. Measures are automatically justified and paginated across staff systems
4. Adding a barline creates a new measure in a growing stack
5. Proper wrapping to new systems based on "measures per staff" setting
6. Page-aware layout with margins and pagination
7. Support for both continuous and paginated view modes

Key concepts:
- Measures are the fundamental building blocks
- Barlines delimit measure boundaries (left and right)
- Automatic justification distributes measures evenly across available width
- Smart pagination with "measures per system" calculation
- Content-aware dynamic sizing based on notation density
- Proper wrapping to next line/system when needed
- Page boundaries and margins respected
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from .measure_object import MeasureObject, MeasureLayoutInfo
import copy
from PyQt6.QtCore import QSettings


@dataclass
class PageLayout:
    """Page layout configuration"""
    page_width: float = 800.0  # Match ScoreRenderer page_width
    page_height: float = 1200.0
    left_margin: float = 50.0  # Match ScoreRenderer DEFAULT_PAGE_MARGINS
    right_margin: float = 50.0  # Match ScoreRenderer DEFAULT_PAGE_MARGINS
    top_margin: float = 80.0
    bottom_margin: float = 80.0
    system_spacing: float = 100.0  # Space between staff systems
    
    @property
    def available_width(self) -> float:
        """Calculate available width for measures"""
        return self.page_width - self.left_margin - self.right_margin
    
    @property
    def available_height(self) -> float:
        """Calculate available height for systems"""
        return self.page_height - self.top_margin - self.bottom_margin


@dataclass
class StaffSystemInfo:
    """Information about a staff system's measures and layout"""
    system_number: int
    page_number: int
    y_position: float
    measures: List[MeasureObject]
    max_measures: int = 4  # Default measures per system
    justified: bool = False
    is_last_system_on_page: bool = False
    
    def __post_init__(self):
        self.total_width = 0.0
    
    def get_content_width(self) -> float:
        """Calculate total content width of measures (before justification)"""
        return sum(measure.get_base_width() for measure in self.measures)
        
    def get_justified_width(self) -> float:
        """Calculate total width after justification"""
        return sum(measure.get_visual_width() for measure in self.measures)
    
    def can_fit_measure(self, measure: MeasureObject, page_layout: PageLayout) -> bool:
        """Check if there's space for another measure in this system"""
        # Check measure count limit first (this is the primary constraint)
        if len(self.measures) >= self.max_measures:
            print(f"SYSTEM_WRAP: System {self.system_number} full ({len(self.measures)}/{self.max_measures} measures)")
            return False
        
        # Check if adding this measure would exceed available width
        current_content_width = self.get_content_width()
        new_content_width = current_content_width + measure.get_base_width()
        
        # Allow some buffer for justification
        width_ok = new_content_width <= (page_layout.available_width * 0.9)
        if not width_ok:
            print(f"SYSTEM_WRAP: System {self.system_number} width exceeded ({new_content_width} > {page_layout.available_width * 0.9})")
        
        return width_ok
    
    def justify_measures(self, page_layout: PageLayout):
        """Distribute measures evenly across the available width"""
        if len(self.measures) == 0:
            return
            
        available_width = page_layout.available_width
        content_width = self.get_content_width()
        
        if len(self.measures) == 1:
            # Single measure takes available width
            self.measures[0].layout_info.justified_width = available_width
            self.measures[0].x_position = page_layout.left_margin
            self.measures[0].end_x = page_layout.left_margin + available_width
        else:
            # Distribute extra space proportionally
            extra_space = available_width - content_width
            
            if extra_space > 0:
                # Calculate proportional distribution
                total_weight = sum(measure.get_content_density() for measure in self.measures)
                
                current_x = page_layout.left_margin
                for measure in self.measures:
                    measure.x_position = current_x
                    
                    # Base width + proportional extra space
                    base_width = measure.get_base_width()
                    weight = measure.get_content_density()
                    proportional_extra = (weight / total_weight) * extra_space if total_weight > 0 else extra_space / len(self.measures)
                    
                    justified_width = base_width + proportional_extra
                    measure.layout_info.justified_width = justified_width
                    
                    measure.end_x = current_x + justified_width
                    
                    current_x += justified_width
            else:
                # Content is too wide, compress proportionally
                compression_ratio = available_width / content_width
                current_x = page_layout.left_margin
                
                for measure in self.measures:
                    measure.x_position = current_x
                    compressed_width = measure.get_base_width() * compression_ratio
                    measure.layout_info.justified_width = compressed_width
                    
                    measure.end_x = current_x + compressed_width
                    
                    current_x += compressed_width
        
        self.justified = True
        print(f"JUSTIFY: System {self.system_number} justified {len(self.measures)} measures across {available_width}px")
        
        # Log the synchronized end_x positions for verification
        for measure in self.measures:
            print(f"JUSTIFY: Measure {measure.measure_number} - start_x={measure.x_position}, end_x={measure.end_x}, width={measure.layout_info.justified_width}")


class MeasureManager:
    """
    Manages measure indexing, barline insertion, and system layout according to ONOTE's 
    measure/barline model where:
    - Barline 0 is the initial system barline (multi-staff, not editable)
    - Measure 1 spans from barline 0 to barline 1 (initial measure)
    - Barline 1 is the initial end bar (editable, cannot be removed)
    - Inserting barlines inherits index to the right, creating proper shuffling
    - Dashed barlines are purely graphical (no indexing impact)
    """
    
    def __init__(self, document, page_layout: Optional[PageLayout] = None):
        """Initialize measure manager with document integration"""
        self.document = document
        
        # Try to get page layout from document/renderer first, fall back to defaults
        if page_layout:
            self.page_layout = page_layout
        else:
            # Check if document has renderer with applied margins (from Page Setup)
            if (hasattr(document, 'layout') and hasattr(document.layout, 'right_margin') and 
                hasattr(document.layout, 'left_margin')):
                # Use document layout settings (applied from Page Setup)
                doc_layout = document.layout
                # Page width should be retrieved from renderer if available
                page_width = 800.0  # Default, may be overridden below
                
                # Try to get page width from renderer if available
                if hasattr(document, 'renderer') or (hasattr(document, 'staff_view') and 
                                                    hasattr(document.staff_view, 'renderer')):
                    renderer = getattr(document, 'renderer', None) or getattr(document.staff_view, 'renderer', None)
                    if renderer and hasattr(renderer, 'page_width'):
                        page_width = renderer.page_width
                
                self.page_layout = PageLayout(
                    page_width=page_width,
                    left_margin=getattr(doc_layout, 'left_margin', 50.0),
                    right_margin=getattr(doc_layout, 'right_margin', 50.0),
                    top_margin=getattr(doc_layout, 'top_margin', 80.0),
                    bottom_margin=getattr(doc_layout, 'bottom_margin', 80.0)
                )
                print(f"MEASURE_MANAGER: Using document layout - page_width={page_width}, right_margin={self.page_layout.right_margin}")
            else:
                # Fall back to default values
                self.page_layout = PageLayout()
                print(f"MEASURE_MANAGER: Using default layout - page_width={self.page_layout.page_width}, right_margin={self.page_layout.right_margin}")
        
        # Initialize internal attributes (measures property is defined below)
        self._internal_measures: Dict[int, MeasureObject] = {}
        self.view_mode = "page"  # "page" or "continuous"
        self.measures_per_system = 4  # Default measures per staff line
        
        # Initialize layout attributes
        self.staff_systems: List[StaffSystemInfo] = []  # List of staff systems for layout
        self.current_staff_ids: List[str] = []  # List of current staff IDs
        
        print(f"MEASURE_MANAGER: Initializing with document: {document}")
        print(f"MEASURE_MANAGER: Available width: {self.page_layout.available_width}px (page={self.page_layout.page_width}, margins=L{self.page_layout.left_margin}+R{self.page_layout.right_margin})")
        
        # Sync with existing document measures if they exist
        if hasattr(document, 'measures') and document.measures:
            print(f"MEASURE_MANAGER: Document has measures attribute: True")
            print(f"MEASURE_MANAGER: Document measures: {document.measures}")
            self.sync_measures_from_document()
        else:
            print(f"MEASURE_MANAGER: Document already has measures or document is None")
    
    @property
    def measures(self) -> List[MeasureObject]:
        """Get measures from document as a list for processing"""
        if not self.document or not hasattr(self.document, 'measures'):
            return []
        
        if isinstance(self.document.measures, dict):
            # Return sorted list by measure number
            return [self.document.measures[key] for key in sorted(self.document.measures.keys()) 
                   if isinstance(key, int)]  # Skip dashed barlines
        else:
            return self.document.measures if self.document.measures else []
    
    def _has_measures(self) -> bool:
        """Check if document has any measures"""
        if not hasattr(self.document, 'measures'):
            return False
        
        if isinstance(self.document.measures, dict):
            return len(self.document.measures) > 0
        else:
            return len(self.document.measures) > 0 if self.document.measures else False
    
    def _initialize_default_measure(self):
        """RESTRUCTURE: No automatic measure initialization"""
        print("MEASURE_MANAGER: No automatic measures - created on first user click only")
        
        # Ensure measures attribute exists but is empty
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        
        print("MEASURE_MANAGER: Ready for user-created measures")
    
    def get_measures_per_system(self) -> int:
        """Get measures per system from preferences"""
        return int(self.settings.value("layout/default_measures_per_system", 4))
    
    def _get_available_staff_width(self) -> float:
        """Calculate available width for measures on staff"""
        # Constants for layout calculation
        LEFT_MARGIN = 50
        RIGHT_MARGIN = 50
        STAFF_WIDTH = 1000  # Default staff width
        INITIAL_CONTENT_WIDTH = 200  # Space for clef, key, time sig
        
        return STAFF_WIDTH - LEFT_MARGIN - RIGHT_MARGIN - INITIAL_CONTENT_WIDTH
    
    def _get_initial_content_x(self) -> float:
        """Get x position where measures start (after clef, key, time sig)"""
        LEFT_MARGIN = 50
        INITIAL_CONTENT_WIDTH = 200
        return LEFT_MARGIN + INITIAL_CONTENT_WIDTH
    
    def insert_barline_at_position(self, x_position: float, barline_type: str = "single") -> Optional[MeasureObject]:
        """
        Insert a new barline at the given position, implementing proper measure shuffling.
        The inserted barline inherits the index of the barline to its right.
        """
        print(f"MEASURE_MANAGER: Inserting {barline_type} barline at x={x_position}")
        
        # Don't allow insertion before initial content
        if x_position < self._get_initial_content_x():
            print("MEASURE_MANAGER: Cannot insert barline before initial content area")
            return None
        
        # Handle dashed barlines separately (purely graphical)
        if barline_type == "dashed":
            return self._create_dashed_barline(x_position)
        
        # Find the measure that contains this x position
        containing_measure_num = self._find_measure_containing_x(x_position)
        
        if containing_measure_num is None:
            # Position is beyond all existing measures - extend to new measure
            return self._extend_with_new_measure(x_position, barline_type)
        
        # Split the containing measure
        result = self._split_measure_at_position(containing_measure_num, x_position, barline_type)
        
        # After inserting, check if we need to recalculate layout due to measures per system limits
        self._check_and_enforce_system_limits()
        
        return result
    
    def _create_dashed_barline(self, x_position: float):
        """Create a purely graphical dashed barline"""
        if not hasattr(self.document, 'graphical_dashed_barlines'):
            self.document.graphical_dashed_barlines = []
        
        class GraphicalDashedBarline:
            def __init__(self, x_pos):
                self.x_position = x_pos
                self.barline_type = "dashed"
                self.measure_number = f"dashed_{int(x_pos)}"
                self.selected = False
                self.is_graphical_dashed = True
                
            def contains_x_position(self, x_pos):
                return abs(self.x_position - x_pos) < 25
        
        dashed_barline = GraphicalDashedBarline(x_position)
        self.document.graphical_dashed_barlines.append(dashed_barline)
        
        print(f"MEASURE_MANAGER: Created dashed barline at x={x_position} (graphical only)")
        return dashed_barline
    
    def _find_measure_containing_x(self, x_position: float) -> Optional[int]:
        """Find which measure contains the given x position"""
        if not hasattr(self.document, 'measures'):
            return None
        
        measures = self.document.measures
        if isinstance(measures, dict):
            # Sort measures by number
            sorted_measures = sorted(measures.items(), key=lambda x: x[0])
        else:
            sorted_measures = [(i+1, measure) for i, measure in enumerate(measures)]
        
        start_x = self._get_initial_content_x()
        
        for measure_num, measure in sorted_measures:
            end_x = measure.end_x
            
            if start_x <= x_position < end_x:
                return measure_num
            
            start_x = end_x
        
        return None
    
    def _split_measure_at_position(self, measure_num: int, x_position: float, barline_type: str) -> MeasureObject:
        """Split a measure at the given position, creating proper index shuffling"""
        print(f"MEASURE_MANAGER: Splitting measure {measure_num} at x={x_position}")
        
        # Get existing measure
        if isinstance(self.document.measures, dict):
            existing_measure = self.document.measures[measure_num]
        else:
            existing_measure = self.document.measures[measure_num - 1]
        
        # The new barline becomes the end of the current measure
        original_end_x = existing_measure.end_x
        existing_measure.end_x = x_position
        existing_measure.barline_type = barline_type
        existing_measure.width = x_position - self._get_measure_start_x(measure_num)
        
        # Create new measure that inherits the original end position
        new_measure_num = measure_num + 1
        new_measure = MeasureObject(measure_number=new_measure_num)
        new_measure.end_x = original_end_x
        new_measure.barline_type = "single"  # New measures get single barlines by default
        new_measure.width = original_end_x - x_position
        new_measure.selected = False
        
        # Shuffle all measures with numbers >= new_measure_num
        self._shuffle_measures_right(new_measure_num)
        
        # Insert the new measure
        if isinstance(self.document.measures, dict):
            self.document.measures[new_measure_num] = new_measure
        else:
            self.document.measures.insert(new_measure_num - 1, new_measure)
        
        print(f"MEASURE_MANAGER: Created new measure {new_measure_num} from x={x_position} to x={original_end_x}")
        return existing_measure  # Return the modified existing measure (with new barline)
    
    def _extend_with_new_measure(self, x_position: float, barline_type: str) -> MeasureObject:
        """Extend the score with a new measure at the given position"""
        print(f"MEASURE_MANAGER: Extending score with new measure at x={x_position}")
        
        # Get the last measure number
        last_measure_num = self._get_last_measure_number()
        new_measure_num = last_measure_num + 1
        
        # Calculate default width based on measures per system
        measures_per_system = self.get_measures_per_system()
        available_width = self._get_available_staff_width()
        default_width = available_width / measures_per_system
        
        # Create new measure
        new_measure = MeasureObject(measure_number=new_measure_num)
        new_measure.end_x = x_position
        new_measure.barline_type = barline_type
        new_measure.width = default_width
        new_measure.selected = False
        
        # Add to measures collection
        if isinstance(self.document.measures, dict):
            self.document.measures[new_measure_num] = new_measure
        else:
            self.document.measures.append(new_measure)
        
        print(f"MEASURE_MANAGER: Created new measure {new_measure_num} ending at x={x_position}")
        return new_measure
    
    def _shuffle_measures_right(self, start_measure: int):
        """Shuffle all measures with numbers >= start_measure to the right by 1"""
        print(f"MEASURE_MANAGER: Shuffling measures from {start_measure} to the right")
        
        if isinstance(self.document.measures, dict):
            # Get all measure numbers >= start_measure in descending order
            measures_to_shuffle = sorted(
                [num for num in self.document.measures.keys() if isinstance(num, int) and num >= start_measure],
                reverse=True
            )
            
            # Move each measure to its new number
            for old_num in measures_to_shuffle:
                measure = self.document.measures[old_num]
                new_num = old_num + 1
                measure.measure_number = new_num
                self.document.measures[new_num] = measure
                del self.document.measures[old_num]
                print(f"MEASURE_MANAGER: Moved measure {old_num} to {new_num}")
        else:
            # List format - insert at position and renumber
            for i in range(start_measure - 1, len(self.document.measures)):
                self.document.measures[i].measure_number += 1

    def _check_and_enforce_system_limits(self):
        """Check if measures exceed system limits and trigger layout recalculation"""
        measures_per_system = self.get_measures_per_system()
        
        if not hasattr(self.document, 'measures'):
            return
        
        measures = self.document.measures
        if isinstance(measures, dict):
            measure_count = len([k for k in measures.keys() if isinstance(k, int)])
        else:
            measure_count = len(measures)
        
        # Calculate how many systems we need
        systems_needed = (measure_count + measures_per_system - 1) // measures_per_system
        
        print(f"MEASURE_MANAGER: Have {measure_count} measures, need {systems_needed} systems with {measures_per_system} measures per system")
        
        # If we've exceeded the current system capacity, trigger layout recalculation
        if hasattr(self, '_last_system_count'):
            if systems_needed > self._last_system_count:
                print(f"MEASURE_MANAGER: System count increased from {self._last_system_count} to {systems_needed}, recalculating layout")
                self._recalculate_measure_layout()
        
        self._last_system_count = systems_needed

    def _recalculate_measure_layout(self):
        """Recalculate measure positions based on current measures per system setting"""
        measures_per_system = self.get_measures_per_system()
        available_width = self._get_available_staff_width()
        measure_width = available_width / measures_per_system
        
        print(f"MEASURE_MANAGER: Recalculating layout with {measure_width}px per measure")
        
        if not hasattr(self.document, 'measures'):
            return
        
        measures = self.document.measures
        if isinstance(measures, dict):
            # Sort measures by number
            sorted_measures = sorted(measures.items(), key=lambda x: x[0] if isinstance(x[0], int) else 999)
        else:
            sorted_measures = [(i+1, measure) for i, measure in enumerate(measures)]
        
        current_system = 0
        measure_in_system = 0
        base_x = self._get_initial_content_x()
        
        for measure_num, measure in sorted_measures:
            if isinstance(measure_num, int):  # Skip dashed barlines
                # Check if we need to wrap to next system
                if measure_in_system >= measures_per_system:
                    current_system += 1
                    measure_in_system = 0
                
                # Calculate position in current system
                x_offset = measure_in_system * measure_width
                measure.end_x = base_x + x_offset + measure_width
                measure.width = measure_width
                
                print(f"MEASURE_MANAGER: Positioned measure {measure_num} at x={measure.end_x} (system {current_system}, position {measure_in_system})")
                
                measure_in_system += 1
    
    def insert_measures_batch(self, count: int, at_position: Optional[int] = None) -> List[MeasureObject]:
        """
        Insert multiple measures at once in a batch operation.
        This is more efficient than inserting one at a time.
        
        Args:
            count: Number of measures to insert
            at_position: Position to insert at (None = at end)
        
        Returns:
            List of created measures
        """
        print(f"MEASURE_MANAGER: Batch inserting {count} measures at position {at_position}")
        
        if count <= 0:
            return []
        
        created_measures = []
        
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        
        measures = self.document.measures
        
        # Determine insertion position
        if at_position is None:
            # Insert at end
            if isinstance(measures, dict):
                insert_position = max([k for k in measures.keys() if isinstance(k, int)]) + 1 if measures else 1
            else:
                insert_position = len(measures) + 1
        else:
            insert_position = at_position
        
        # Make room for the new measures by shuffling existing ones
        if insert_position <= self._get_last_measure_number():
            self._shuffle_measures_right_by_count(insert_position, count)
        
        # Create new measures
        measures_per_system = self.get_measures_per_system()
        available_width = self._get_available_staff_width()
        default_width = available_width / measures_per_system
        
        for i in range(count):
            measure_num = insert_position + i
            new_measure = MeasureObject(measure_number=measure_num)
            new_measure.width = default_width
            new_measure.barline_type = "single"
            new_measure.selected = False
            
            # Calculate position (will be refined by layout recalculation)
            base_x = self._get_initial_content_x()
            new_measure.end_x = base_x + (measure_num * default_width)
            
            # Store the measure
            if isinstance(measures, dict):
                measures[measure_num] = new_measure
            else:
                measures.insert(measure_num - 1, new_measure)
            
            created_measures.append(new_measure)
            print(f"MEASURE_MANAGER: Created batch measure {measure_num}")
        
        # Recalculate layout after batch insertion
        self._check_and_enforce_system_limits()
        
        print(f"MEASURE_MANAGER: Batch insertion complete - created {len(created_measures)} measures")
        return created_measures

    def _shuffle_measures_right_by_count(self, start_measure: int, count: int):
        """Shuffle measures to the right by the specified count"""
        print(f"MEASURE_MANAGER: Shuffling measures from {start_measure} right by {count} positions")
        
        if isinstance(self.document.measures, dict):
            # Get all measure numbers >= start_measure in descending order
            measures_to_shuffle = sorted(
                [num for num in self.document.measures.keys() if isinstance(num, int) and num >= start_measure],
                reverse=True
            )
            
            # Move each measure to its new number
            for old_num in measures_to_shuffle:
                measure = self.document.measures[old_num]
                new_num = old_num + count
                measure.measure_number = new_num
                self.document.measures[new_num] = measure
                del self.document.measures[old_num]
                print(f"MEASURE_MANAGER: Moved measure {old_num} to {new_num}")
        else:
            # List format - adjust indices
            for i in range(start_measure - 1, len(self.document.measures)):
                self.document.measures[i].measure_number += count

    def _get_last_measure_number(self) -> int:
        """Get the highest measure number"""
        if not hasattr(self.document, 'measures'):
            return 0
        
        measures = self.document.measures
        if isinstance(measures, dict):
            int_keys = [k for k in measures.keys() if isinstance(k, int)]
            return max(int_keys) if int_keys else 0
        else:
            return len(measures) if measures else 0
    
    def calculate_system_layout(self) -> List[Dict]:
        """Calculate how measures should be laid out across systems"""
        measures_per_system = self.get_measures_per_system()
        
        if not hasattr(self.document, 'measures'):
            return []
        
        measures = self.document.measures
        if isinstance(measures, dict):
            sorted_measures = sorted(measures.items(), key=lambda x: x[0])
            measure_list = [measure for _, measure in sorted_measures]
        else:
            measure_list = measures if measures else []
        
        systems = []
        current_system = []
        
        for measure in measure_list:
            current_system.append(measure)
            
            # Check if we should start a new system
            if (len(current_system) >= measures_per_system or 
                getattr(measure, 'force_system_break', False)):
                
                systems.append({
                    'measures': current_system.copy(),
                    'start_measure': current_system[0].measure_number,
                    'end_measure': current_system[-1].measure_number,
                    'measure_count': len(current_system)
                })
                current_system = []
        
        # Add remaining measures as final system
        if current_system:
            systems.append({
                'measures': current_system.copy(),
                'start_measure': current_system[0].measure_number,
                'end_measure': current_system[-1].measure_number,
                'measure_count': len(current_system)
            })
        
        print(f"MEASURE_MANAGER: Calculated {len(systems)} systems with {measures_per_system} measures per system")
        return systems
    
    def get_measure_positions(self) -> Dict[int, Tuple[float, float]]:
        """Get start and end x positions for all measures"""
        positions = {}
        
        if not hasattr(self.document, 'measures'):
            return positions
        
        start_x = self._get_initial_content_x()
        
        measures = self.document.measures
        if isinstance(measures, dict):
            sorted_measures = sorted(measures.items(), key=lambda x: x[0])
        else:
            sorted_measures = [(i+1, measure) for i, measure in enumerate(measures)]
        
        for measure_num, measure in sorted_measures:
            end_x = measure.end_x
            positions[measure_num] = (start_x, end_x)
            start_x = end_x
        
        return positions
    
    def remove_measure(self, measure_num: int) -> bool:
        """Remove a measure and shuffle indices accordingly"""
        # Check if this is the ultimate end measure of the score
        is_ultimate_end_measure = self._is_ultimate_end_measure(measure_num)
        
        if is_ultimate_end_measure:
            print(f"MEASURE_MANAGER: Cannot remove ultimate end measure {measure_num} - changing to single barline instead")
            if hasattr(self.document, 'measures') and self.document.measures:
                if isinstance(self.document.measures, dict):
                    if measure_num in self.document.measures:
                        ultimate_measure = self.document.measures[measure_num]
                        ultimate_measure.barline_type = "single"
                        print(f"MEASURE_MANAGER: Changed ultimate end measure {measure_num} from {ultimate_measure.barline_type} to single")
                        return True
            return False
        
        # Regular removal for non-ultimate measures
        print(f"MEASURE_MANAGER: Removing measure {measure_num}")
        
        if not hasattr(self.document, 'measures') or not self.document.measures:
            return False
        
        measures = self.document.measures
        if isinstance(measures, dict):
            if measure_num not in measures:
                return False
            
            # Remove the measure
            del measures[measure_num]
            
            # Shuffle remaining measures left
            measures_to_shuffle = sorted([num for num in measures.keys() if isinstance(num, int) and num > measure_num])
            for old_num in measures_to_shuffle:
                measure = measures[old_num]
                new_num = old_num - 1
                measures[new_num] = measure
                measure.measure_number = new_num
                del measures[old_num]
            
            print(f"MEASURE_MANAGER: Successfully removed measure {measure_num} and shuffled remaining measures")
            return True
        
        return False
    
    def _is_ultimate_end_measure(self, measure_num: int) -> bool:
        """Check if this measure is the ultimate end measure of the entire score"""
        if not hasattr(self.document, 'measures') or not self.document.measures:
            return False
        
        measures = self.document.measures
        if isinstance(measures, dict):
            # Find the highest measure number - that's the ultimate end measure
            if measures:
                highest_measure_num = max(num for num in measures.keys() if isinstance(num, int))
                return measure_num == highest_measure_num
        
        return False
    
    def can_remove_barline(self, barline) -> bool:
        """
        Check if a barline can be removed.
        CRITICAL FIX: All barlines can now be removed to maintain consistency
        with user-created single barline system from the start.
        """
        if hasattr(barline, 'measure_number'):
            # FIXED: Allow removal of any barline - user controls all barlines now
            print(f"MEASURE_MANAGER: Allowing removal of barline {barline.measure_number}")
            return True
        
        # FIXED: Allow removal of any barline - no special structural restrictions
        print("MEASURE_MANAGER: Allowing barline removal - user controls all barlines")
        return True
    
    def update_measure_widths(self):
        """Update measure widths based on current measures per system setting"""
        measures_per_system = self.get_measures_per_system()
        available_width = self._get_available_staff_width()
        default_width = available_width / measures_per_system
        
        if not hasattr(self.document, 'measures'):
            return
        
        measures = self.document.measures
        if isinstance(measures, dict):
            for measure in measures.values():
                if not hasattr(measure, 'custom_width') or measure.custom_width is None:
                    measure.width = default_width
        else:
            for measure in measures:
                if not hasattr(measure, 'custom_width') or measure.custom_width is None:
                    measure.width = default_width
        
        print(f"MEASURE_MANAGER: Updated measure widths to {default_width} based on {measures_per_system} measures per system")
        
    def set_page_layout(self, page_layout: PageLayout):
        """Update page layout settings and recalculate"""
        self.page_layout = page_layout
        self.recalculate_complete_layout()
        
    def set_measures_per_system(self, measures_per_system: int):
        """Set the default number of measures per staff system"""
        self.measures_per_system = max(1, measures_per_system)
        self.recalculate_complete_layout()
        
    def set_view_mode(self, mode: str):
        """Set view mode: 'paginated' or 'continuous'"""
        if mode in ["paginated", "continuous"]:
            self.view_mode = mode
            self.recalculate_complete_layout()
            
    def set_current_staff_ids(self, staff_ids: List[str]):
        """Set which staves new measures should apply to"""
        self.current_staff_ids = staff_ids.copy()
        
    def add_measure_at_sequence_position(self, insert_after_measure: int = -1, barline_type: str = "single") -> MeasureObject:
        """
        Add a new measure at a specific position in the sequence.
        This replaces the old position-based method with sequence-based insertion.
        
        Args:
            insert_after_measure: Measure number to insert after (-1 for end)
            barline_type: Type of right barline for this measure
        """
        # Create the new measure
        new_measure = MeasureObject(
            measure_number=self.measure_counter
        )
        
        # Set the right barline type (this measure's ending boundary)
        new_measure.right_barline_type = barline_type
        
        # Assign to current staves
        new_measure.set_staff_ids(self.current_staff_ids)
        
        # Set base content properties
        new_measure.set_content_density(0.5)  # Medium density by default
        
        # Calculate base width (before justification)
        base_width = self._calculate_base_width(new_measure)
        new_measure.layout_info.base_width = base_width
        
        # Find insertion position
        if insert_after_measure == -1 or insert_after_measure >= len(self.measures):
            # Insert at end
            self.measures.append(new_measure)
            insert_index = len(self.measures) - 1
        else:
            # Insert after specified measure
            insert_index = insert_after_measure
            self.measures.insert(insert_index, new_measure)
        
        self.measure_counter += 1
        
        # Renumber measures
        self._renumber_measures(insert_index)
        
        # Recalculate complete layout
        self.recalculate_complete_layout()
        
        print(f"MEASURE_MANAGER: Added measure {new_measure.measure_number} (type={barline_type}) at sequence position {insert_index}")
        return new_measure
    
    def add_measure_at_position(self, x_position: float, barline_type: str = "single") -> MeasureObject:
        """
        Legacy method for adding measures based on x position.
        This now converts position to sequence-based insertion.
        """
        # Find which measure this position would be after
        insert_after = -1
        for i, measure in enumerate(self.measures):
            if x_position > measure.x_position + measure.get_visual_width():
                insert_after = i
            else:
                break
        
        return self.add_measure_at_sequence_position(insert_after, barline_type)
        
    def modify_measure_barline(self, measure: MeasureObject, new_barline_type: str):
        """Modify the barline type of an existing measure"""
        old_type = measure.right_barline_type
        measure.barline_type = new_barline_type  # Uses the property setter
        
        # Recalculate base width since barline type affects width
        base_width = self._calculate_base_width(measure)
        measure.layout_info.base_width = base_width
        
        # Recalculate layout
        self.recalculate_complete_layout()
        
        print(f"MEASURE_MANAGER: Modified measure {measure.measure_number} barline: {old_type} -> {new_barline_type}")
        
    def recalculate_complete_layout(self):
        """
        Recalculate the complete layout including pagination and justification.
        This is the main layout engine that implements proper musical layout.
        """
        print("LAYOUT_ENGINE: Starting complete layout recalculation")
        
        # Clear existing layout
        self.staff_systems.clear()
        
        if not self.measures:
            print("LAYOUT_ENGINE: No measures to layout")
            return
        
        if self.view_mode == "continuous":
            self._layout_continuous_mode()
        else:
            self._layout_paginated_mode()
            
        print(f"LAYOUT_ENGINE: Complete layout calculated - {len(self.staff_systems)} systems, {len(self.measures)} measures")
        
    def _layout_continuous_mode(self):
        """Layout measures in continuous (scrollable) mode"""
        current_system = None
        
        # Get measures from document using the property
        document_measures = self.measures
        
        # Filter out dashed barlines from justification - they maintain their original positions
        justifiable_measures = [measure for measure in document_measures 
                               if not getattr(measure, 'bypass_justification', False)]
        
        print(f"LAYOUT_ENGINE: Processing {len(justifiable_measures)} justifiable measures (filtered out {len(document_measures) - len(justifiable_measures)} dashed barlines)")
        
        for measure in justifiable_measures:
            # Create new system if needed
            if (current_system is None or 
                not current_system.can_fit_measure(measure, self.page_layout)):
                
                # Justify and save current system
                if current_system is not None:
                    current_system.justify_measures(self.page_layout)
                    self.staff_systems.append(current_system)
                    print(f"SYSTEM_CREATE: Completed system {current_system.system_number} with {len(current_system.measures)} measures")
                
                # Create new system
                system_number = len(self.staff_systems)
                current_system = StaffSystemInfo(
                    system_number=system_number,
                    page_number=0,  # All on same "page" in continuous mode
                    y_position=self.page_layout.top_margin + (system_number * self.page_layout.system_spacing),
                    measures=[],
                    max_measures=self.measures_per_system
                )
                print(f"SYSTEM_CREATE: Created new system {system_number} (max {self.measures_per_system} measures)")
            
            # Add measure to current system
            current_system.measures.append(measure)
            print(f"SYSTEM_ADD: Added measure {measure.measure_number} to system {current_system.system_number} ({len(current_system.measures)}/{current_system.max_measures})")
        
        # Add final system
        if current_system is not None and current_system.measures:
            current_system.justify_measures(self.page_layout)
            self.staff_systems.append(current_system)
            print(f"SYSTEM_CREATE: Completed final system {current_system.system_number} with {len(current_system.measures)} measures")
        
        # Update measure positions (only for justifiable measures)
        self._update_measure_positions()
            
    def _layout_paginated_mode(self):
        """Layout measures with proper pagination"""
        current_page = 0
        current_y = self.page_layout.top_margin
        current_system = None
        
        # Get measures from document using the property
        document_measures = self.measures
        
        # Filter out dashed barlines from justification - they maintain their original positions
        justifiable_measures = [measure for measure in document_measures 
                               if not getattr(measure, 'bypass_justification', False)]
        
        print(f"LAYOUT_ENGINE: Processing {len(justifiable_measures)} justifiable measures (filtered out {len(document_measures) - len(justifiable_measures)} dashed barlines)")
        
        for measure in justifiable_measures:
            # Create new system if needed
            if (current_system is None or 
                not current_system.can_fit_measure(measure, self.page_layout)):
                
                # Justify and save current system
                if current_system is not None:
                    current_system.justify_measures(self.page_layout)
                    self.staff_systems.append(current_system)
                    current_y += self.page_layout.system_spacing
                
                # Check if we need a new page
                if current_y + self.page_layout.system_spacing > self.page_layout.available_height:
                    current_page += 1
                    current_y = self.page_layout.top_margin
                
                # Create new system
                current_system = StaffSystemInfo(
                    system_number=len(self.staff_systems),
                    page_number=current_page,
                    y_position=current_y,
                    measures=[],
                    max_measures=self.measures_per_system
                )
            
            # Add measure to current system
            current_system.measures.append(measure)
        
        # Add final system
        if current_system is not None and current_system.measures:
            current_system.justify_measures(self.page_layout)
            current_system.is_last_system_on_page = True
            self.staff_systems.append(current_system)
        
        # Update measure positions
        self._update_measure_positions()
        
    def _update_measure_positions(self):
        """Update measure positions based on justified layout"""
        for system in self.staff_systems:
            for measure in system.measures:
                # Position is set during justification
                # Update measure's system assignment using layout_info
                if hasattr(measure, 'layout_info'):
                    measure.layout_info.system_number = system.system_number
                    measure.layout_info.page_number = system.page_number
                    measure.layout_info.x_position = getattr(measure, 'x_position', 0.0)
                    measure.layout_info.is_justified = True
                    print(f"LAYOUT: Updated measure {measure.measure_number} to system {system.system_number}, page {system.page_number}")
                else:
                    print(f"LAYOUT: Warning - measure {measure.measure_number} has no layout_info")
        
        # CRITICAL FIX: Sync justified positions back to document
        self._sync_measures_to_document()
    
    def _calculate_base_width(self, measure: MeasureObject) -> float:
        """Calculate base width for a measure before justification"""
        base_width = self.base_measure_width
        
        # Adjust for content density
        density_factor = measure.get_content_density()
        base_width *= (0.7 + 0.6 * density_factor)  # Range: 70% to 130%
        
        # Adjust for barline types
        if measure.right_barline_type in ["double", "final"]:
            base_width += 10
        elif measure.right_barline_type in ["repeat_start", "repeat_end", "repeat_both"]:
            base_width += 20
        
        # Clamp to reasonable bounds
        return max(self.min_measure_width, min(base_width, self.max_measure_width))
    
    def find_measure_at_position(self, x_position: float, y_position: float = 0) -> Optional[MeasureObject]:
        """Find the measure that contains the given position"""
        # For barline selection, we're more flexible with y position
        # First try to find by x position across all measures
        for measure in self.measures:
            if measure.contains_x_position(x_position):
                print(f"MEASURE_FIND: Found measure {measure.measure_number} at x={x_position}")
                return measure
        
        # If no exact match, find the closest measure by x position
        closest_measure = None
        min_distance = float('inf')
        
        for measure in self.measures:
            left_boundary = measure.get_left_boundary_x()
            right_boundary = measure.get_right_boundary_x()
            
            # Calculate distance to closest boundary
            if x_position < left_boundary:
                distance = left_boundary - x_position
            elif x_position > right_boundary:
                distance = x_position - right_boundary
            else:
                distance = 0  # Inside the measure
            
            if distance < min_distance:
                min_distance = distance
                closest_measure = measure
        
        # Return closest measure if within reasonable tolerance
        if closest_measure and min_distance < 30:  # 30 pixel tolerance
            print(f"MEASURE_FIND: Found closest measure {closest_measure.measure_number} at distance {min_distance}px")
            return closest_measure
        
        print(f"MEASURE_FIND: No measure found at x={x_position}, y={y_position}")
        return None
        
    def get_measures_for_staff(self, staff_id: str) -> List[MeasureObject]:
        """Get all measures that apply to a specific staff"""
        return [measure for measure in self.measures if measure.applies_to_staff(staff_id)]
        
    def get_system_at_position(self, y_position: float) -> Optional[StaffSystemInfo]:
        """Get the staff system at the given y position"""
        for system in self.staff_systems:
            if abs(system.y_position - y_position) < self.page_layout.system_spacing / 2:
                return system
        return None
    
    def get_measures_in_system(self, system_number: int) -> List[MeasureObject]:
        """Get all measures in a specific staff system"""
        if 0 <= system_number < len(self.staff_systems):
            return self.staff_systems[system_number].measures.copy()
        return []
    
    def force_system_break_after_measure(self, measure: MeasureObject):
        """Force a system break after the specified measure"""
        measure.breaks_system = True
        self.recalculate_complete_layout()
        
    def set_measure_content_density(self, measure: MeasureObject, density: float):
        """Set content density for a measure and recalculate layout"""
        measure.set_content_density(density)
        
        # Recalculate base width
        base_width = self._calculate_base_width(measure)
        measure.layout_info.base_width = base_width
        
        self.recalculate_complete_layout()
        
    def clear_all_measures(self):
        """Clear all measures (for new document or reset)"""
        self.measures.clear()
        self.staff_systems.clear()
        self.measure_counter = 1
        
    def get_page_count(self) -> int:
        """Get total number of pages"""
        if not self.staff_systems:
            return 1
        return max(system.page_number for system in self.staff_systems) + 1
        
    def get_systems_on_page(self, page_number: int) -> List[StaffSystemInfo]:
        """Get all systems on a specific page"""
        return [system for system in self.staff_systems if system.page_number == page_number]
        
    def _find_insertion_index(self, x_position: float) -> int:
        """Find the index where a new measure should be inserted based on x position"""
        for i, measure in enumerate(self.measures):
            if x_position < measure.x_position:
                return i
        return len(self.measures)  # Insert at end
        
    def _renumber_measures(self, start_index: int = 0):
        """Renumber measures starting from the given index"""
        for i in range(start_index, len(self.measures)):
            self.measures[i].measure_number = i + 1
            
    def get_measure_count(self) -> int:
        """Get total number of measures"""
        return len(self.measures)
        
    def get_system_count(self) -> int:
        """Get number of staff systems"""
        return len(self.staff_systems)
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize measure manager state to dictionary"""
        return {
            'measures': [measure.to_dict() for measure in self.measures],
            'measure_counter': self.measure_counter,
            'page_layout': {
                'page_width': self.page_layout.page_width,
                'page_height': self.page_layout.page_height,
                'left_margin': self.page_layout.left_margin,
                'right_margin': self.page_layout.right_margin,
                'top_margin': self.page_layout.top_margin,
                'bottom_margin': self.page_layout.bottom_margin,
                'system_spacing': self.page_layout.system_spacing
            },
            'measures_per_system': self.measures_per_system,
            'view_mode': self.view_mode,
            'current_staff_ids': self.current_staff_ids
        }
        
    def from_dict(self, data: Dict[str, Any]):
        """Restore measure manager state from dictionary"""
        self.measures.clear()
        
        # Restore measures
        for measure_data in data.get('measures', []):
            measure = MeasureObject.from_dict(measure_data)
            self.measures.append(measure)
            
        # Restore settings
        self.measure_counter = data.get('measure_counter', 1)
        
        # Restore page layout
        layout_data = data.get('page_layout', {})
        self.page_layout = PageLayout(
            page_width=layout_data.get('page_width', 800.0),
            page_height=layout_data.get('page_height', 1200.0),
            left_margin=layout_data.get('left_margin', 50.0),
            right_margin=layout_data.get('right_margin', 50.0),
            top_margin=layout_data.get('top_margin', 80.0),
            bottom_margin=layout_data.get('bottom_margin', 80.0),
            system_spacing=layout_data.get('system_spacing', 100.0)
        )
        
        self.measures_per_system = data.get('measures_per_system', 4)
        self.view_mode = data.get('view_mode', 'paginated')
        self.current_staff_ids = data.get('current_staff_ids', ['part'])
        
        # Recalculate complete layout
        self.recalculate_complete_layout()
        
    def get_layout_info(self) -> Dict[str, Any]:
        """Get comprehensive layout information for rendering"""
        return {
            'staff_systems': [
                {
                    'system_number': system.system_number,
                    'page_number': system.page_number,
                    'y_position': system.y_position,
                    'justified': system.justified,
                    'measures': [
                        {
                            'measure_number': measure.measure_number,
                            'x_position': measure.x_position,
                            'base_width': measure.get_base_width(),
                            'justified_width': measure.get_visual_width(),
                            'left_barline': measure.left_barline_type,
                            'right_barline': measure.right_barline_type,
                            'staff_ids': measure.staff_ids,
                            'content_density': measure.get_content_density()
                        }
                        for measure in system.measures
                    ],
                    'content_width': system.get_content_width(),
                    'justified_width': system.get_justified_width()
                }
                for system in self.staff_systems
            ],
            'total_measures': len(self.measures),
            'total_systems': len(self.staff_systems),
            'total_pages': self.get_page_count(),
            'view_mode': self.view_mode,
            'page_layout': {
                'page_width': self.page_layout.page_width,
                'page_height': self.page_layout.page_height,
                'available_width': self.page_layout.available_width,
                'available_height': self.page_layout.available_height,
                'left_margin': self.page_layout.left_margin,
                'right_margin': self.page_layout.right_margin,
                'top_margin': self.page_layout.top_margin,
                'bottom_margin': self.page_layout.bottom_margin
            }
        } 

    def _get_measure_start_x(self, measure_num: int) -> float:
        """Get the starting x position of a measure based on its number"""
        if measure_num <= 1:
            return self._get_initial_content_x()
        
        # Calculate start based on previous measures
        if isinstance(self.document.measures, dict):
            # Find all measures before this one
            start_x = self._get_initial_content_x()
            for i in range(1, measure_num):
                if i in self.document.measures:
                    measure = self.document.measures[i]
                    # Use the end_x of previous measure as start of current
                    start_x = measure.end_x
                else:
                    break
            return start_x
        else:
            # List format
            start_x = self._get_initial_content_x()
            for i in range(measure_num - 1):
                if i < len(self.document.measures):
                    start_x = self.document.measures[i].end_x
                else:
                    break
            return start_x 

    def _sync_measures_to_document(self):
        """Sync justified measures back to the document"""
        if not self.document or not hasattr(self.document, 'measures'):
            print("LAYOUT: No document or measures to sync")
            return
            
        print(f"LAYOUT: Syncing {len(self.measures)} measures back to document")
        
        # Update document measures with justified positions
        if isinstance(self.document.measures, dict):
            # Document uses dict format
            for measure in self.measures:
                measure_key = measure.measure_number
                self.document.measures[measure_key] = measure
                print(f"LAYOUT: Synced measure {measure.measure_number} (end_x={measure.end_x}) to document dict")
        elif isinstance(self.document.measures, list):
            # Document uses list format
            self.document.measures = self.measures.copy()
            print(f"LAYOUT: Synced all measures to document list")
        else:
            print(f"LAYOUT: Unknown document measures format: {type(self.document.measures)}") 

    def sync_measures_from_document(self):
        """Sync measures from document into manager"""
        if not self.document or not hasattr(self.document, 'measures'):
            return
            
        if isinstance(self.document.measures, dict):
            # Document has measures in dict format
            measure_count = len([k for k in self.document.measures.keys() if isinstance(k, int)])
            print(f"MEASURE_MANAGER: Synced {measure_count} measures from document")
        else:
            print(f"MEASURE_MANAGER: Document measures in unexpected format: {type(self.document.measures)}") 