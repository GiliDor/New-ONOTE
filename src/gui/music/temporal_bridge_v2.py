"""
ONOTE Temporal Bridge V2 - Grid-Based Implementation

This module replaces the old barline_temporal_bridge.py with a complete temporal grid-based
implementation that follows the ONOTE specifications:

1. CONTENT MERGING MODEL:
   - Measures are divisions of continuous temporal grid
   - "Deleting" barlines merges temporal content (never removes measures)
   - Consecutive renumbering after content merge operations

2. TEMPORAL GRID INTEGRATION:
   - All operations use the temporal grid system
   - Dynamic spacing based on content complexity
   - Beat-alignment across multiple staves

3. LAYOUT FLOW:
   - Parse content → build temporal map → determine spacing demands
   - Adjust spacing grid → align vertically → render with justification
"""

from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtCore import QObject, pyqtSignal

from .temporal_grid_system import (
    TemporalGridSystem, TemporalGridMeasure, TemporalGridSettings,
    TemporalPosition, NotationElement, Note, Rest, Chord
)
from .measure_object import MeasureObject


class TemporalBridgeV2(QObject):
    """Enhanced temporal bridge using the temporal grid system"""
    
    # Signals
    temporal_structure_changed = pyqtSignal()
    content_merged = pyqtSignal(int, int)  # source_measure, target_measure
    measure_layout_changed = pyqtSignal()
    barline_created = pyqtSignal(int)  # measure_number
    barline_removed = pyqtSignal(int)  # measure_number
    
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        
        # Core temporal grid system
        self.temporal_grid = TemporalGridSystem(document, self)
        
        # Connect signals
        self.temporal_grid.temporal_structure_changed.connect(self.temporal_structure_changed)
        self.temporal_grid.content_merged.connect(self.content_merged)
        self.temporal_grid.measure_layout_changed.connect(self.measure_layout_changed)
        
        # Layout constants (for integration with existing UI)
        self.SYSTEM_BARLINE_X = 100.0     # Barline 0 (initial system barline)
        self.LEFTMOST_NOTE_X = 225.0      # CRITICAL FIX: Reduced from 265.0 to 225.0 for smaller padding from time signature
        self.END_BARLINE_X = self._calculate_staff_end_position()
        
        # Integration with existing measure manager
        self.measure_manager = None
        if document and hasattr(document, 'staff_view') and hasattr(document.staff_view, 'measure_manager'):
            self.measure_manager = document.staff_view.measure_manager
            print("TEMPORAL_BRIDGE_V2: Connected to existing MeasureManager")
        
        # Load preferences
        self._load_layout_preferences()
        
        print("TEMPORAL_BRIDGE_V2: Initialized with temporal grid system")
        print(f"  - Grid PPQN: {self.temporal_grid.grid_settings.ppqn}")
        print(f"  - Grid tempo: {self.temporal_grid.grid_settings.default_tempo} BPM")
        print(f"  - Measures per system: {self.temporal_grid.grid_settings.measures_per_system}")
    
    def create_barline_at_position(self, x_position: float, barline_type: str = "single") -> Optional[MeasureObject]:
        """
        Create a barline using temporal grid system.
        
        ONOTE SPECIFICATION IMPLEMENTATION:
        - Rule 1: Equal division of staff length regardless of click position
        - Rule 2: Index inheritance with proper measure shuffling
        - Content preservation: No measure deletion, only content division
        """
        print(f"\\n=== TEMPORAL GRID BARLINE CREATION ===")
        print(f"Click position: {x_position}, type: {barline_type}")
        
        # Check constraints
        if not self._check_creation_constraints():
            return None
        
        # Create barline using temporal grid
        temporal_measure = self.temporal_grid.insert_barline_at_position(x_position, barline_type)
        
        if temporal_measure:
            # Convert to document-compatible measure object
            document_measure = self._convert_to_document_measure(temporal_measure)
            
            # Update document
            self._sync_to_document()
            
            # Force UI updates
            self._force_ui_sync()
            
            # Emit signals
            self.barline_created.emit(temporal_measure.measure_number)
            
            print(f"TEMPORAL_BRIDGE_V2: Created barline for measure #{temporal_measure.measure_number}")
            return document_measure
        
        print("TEMPORAL_BRIDGE_V2: Failed to create barline")
        return None
    
    def remove_barline(self, measure_number: int) -> bool:
        """
        Remove a barline using content merging model.
        
        ONOTE SPECIFICATION IMPLEMENTATION:
        - NEVER removes measures from the score
        - Merges temporal content into adjacent measure
        - Renumbers all measures consecutively starting from 1
        - Preserves all notation content (no data loss)
        """
        print(f"\\n=== TEMPORAL GRID BARLINE REMOVAL ===")
        print(f"Target measure: #{measure_number}")
        
        # Use temporal grid's content merging
        success = self.temporal_grid.remove_barline_at_measure(measure_number)
        
        if success:
            # Update document with merged content
            self._sync_to_document()
            
            # Force UI updates
            self._force_ui_sync()
            
            # Emit signals
            self.barline_removed.emit(measure_number)
            
            print(f"TEMPORAL_BRIDGE_V2: Successfully merged content from measure #{measure_number}")
            print(f"  - Total measures now: {len(self.temporal_grid.measures)}")
            print(f"  - Measures renumbered consecutively: {sorted(self.temporal_grid.measures.keys())}")
            
            return True
        
        print(f"TEMPORAL_BRIDGE_V2: Failed to merge content from measure #{measure_number}")
        return False
    
    def modify_barline_type(self, measure_number: int, new_type: str) -> bool:
        """Modify the barline type of an existing measure"""
        if measure_number in self.temporal_grid.measures:
            temporal_measure = self.temporal_grid.measures[measure_number]
            old_type = temporal_measure.barline_type
            temporal_measure.barline_type = new_type
            
            # Update document
            self._sync_to_document()
            
            print(f"TEMPORAL_BRIDGE_V2: Modified measure #{measure_number} barline type: {old_type} → {new_type}")
            return True
        
        return False
    
    def add_notation_element(self, measure_number: int, element: NotationElement, beat_position: float) -> bool:
        """Add a notation element to a specific measure at a beat position"""
        if measure_number not in self.temporal_grid.measures:
            print(f"TEMPORAL_BRIDGE_V2: Measure #{measure_number} not found")
            return False
        
        temporal_measure = self.temporal_grid.measures[measure_number]
        temporal_pos = TemporalPosition(measure_number, beat_position, 0)
        
        success = temporal_measure.add_temporal_content(temporal_pos, element)
        
        if success:
            # Update document
            self._sync_to_document()
            
            print(f"TEMPORAL_BRIDGE_V2: Added {element.__class__.__name__} to measure #{measure_number} at beat {beat_position}")
            return True
        
        print(f"TEMPORAL_BRIDGE_V2: Failed to add element to measure #{measure_number}")
        return False
    
    def get_measure_at_position(self, x_position: float) -> Optional[MeasureObject]:
        """Find measure at given x position"""
        temporal_measure = self.temporal_grid._find_measure_at_position(x_position)
        
        if temporal_measure:
            return self._convert_to_document_measure(temporal_measure)
        
        return None
    
    def get_all_measures(self) -> Dict[int, MeasureObject]:
        """Get all measures as document-compatible objects"""
        return self.temporal_grid.get_measures_for_document()
    
    def get_temporal_position_at_x(self, x_position: float) -> Optional[TemporalPosition]:
        """Get temporal position at specific x coordinate"""
        temporal_measure = self.temporal_grid._find_measure_at_position(x_position)
        
        if temporal_measure:
            # Calculate relative position within the measure
            current_x = 0.0
            for measure_num in sorted(self.temporal_grid.measures.keys()):
                if measure_num == temporal_measure.measure_number:
                    break
                current_x += self.temporal_grid.measures[measure_num].calculated_justified_width
            
            relative_x = x_position - current_x
            return temporal_measure.get_temporal_position_at_x(relative_x)
        
        return None
    
    def _check_creation_constraints(self) -> bool:
        """
        Check if new barlines can be created.
        
        ONOTE SPECIFICATION: Measures per system constraint should force wrapping,
        not prevent creation. When MPS is exceeded, the system should wrap to the
        next line automatically. This method now always allows creation - wrapping
        is handled by _recalculate_systems().
        """
        # Always allow creation - wrapping will be handled automatically by system recalculation
        # The temporal grid's _recalculate_systems() will group measures into systems
        # based on measures_per_system, forcing wrapping when exceeded
        return True
    
    def _convert_to_document_measure(self, temporal_measure: TemporalGridMeasure) -> MeasureObject:
        """Convert temporal grid measure to document measure object"""
        measure_obj = MeasureObject(
            measure_number=temporal_measure.measure_number,
            end_x=temporal_measure.calculated_justified_width,
            document=self.document,
            barline_type=temporal_measure.barline_type
        )
        
        # Copy properties
        measure_obj.width = temporal_measure.calculated_justified_width
        measure_obj.x_position = 0.0  # Will be calculated by layout system
        
        # Copy additional properties for compatibility
        if hasattr(temporal_measure, 'is_repeat_start'):
            measure_obj.is_repeat_start = temporal_measure.is_repeat_start
        if hasattr(temporal_measure, 'is_repeat_end'):
            measure_obj.is_repeat_end = temporal_measure.is_repeat_end
        
        return measure_obj
    
    def _sync_to_document(self):
        """Sync temporal grid state to document measures"""
        if not self.document:
            return
        
        # Get document-compatible measures
        document_measures = self.temporal_grid.get_measures_for_document()
        
        # Calculate justified positions using ONOTE Rule 1
        self._apply_justified_positions(document_measures)
        
        # Update document
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        
        self.document.measures = document_measures
        
        print(f"TEMPORAL_BRIDGE_V2: Synced {len(document_measures)} measures to document")
        
        # Debug output
        for num in sorted(document_measures.keys()):
            measure = document_measures[num]
            print(f"  Measure #{num}: end_x={getattr(measure, 'end_x', 'unknown')}, type={getattr(measure, 'barline_type', 'unknown')}")
    
    def _apply_justified_positions(self, document_measures: Dict[int, MeasureObject]):
        """Apply ONOTE Rule 1: Equal division of staff length"""
        if not document_measures:
            return
        
        total_measures = len(document_measures)
        justified_positions = self._calculate_justified_positions(total_measures)
        
        print(f"TEMPORAL_BRIDGE_V2: Applying justified positions per ONOTE Rule 1")
        print(f"  Total measures: {total_measures}")
        print(f"  Staff length: {self.LEFTMOST_NOTE_X} to {self.END_BARLINE_X}")
        print(f"  Equal spacing positions: {[f'{pos:.1f}' for pos in justified_positions]}")
        
        # Apply positions
        for i, measure_num in enumerate(sorted(document_measures.keys())):
            if i < len(justified_positions):
                measure = document_measures[measure_num]
                measure.end_x = justified_positions[i]
                
                # Calculate width and start position
                if i == 0:
                    measure.x_position = self.LEFTMOST_NOTE_X
                    measure.width = measure.end_x - self.LEFTMOST_NOTE_X
                else:
                    prev_end = justified_positions[i-1]
                    measure.x_position = prev_end
                    measure.width = measure.end_x - measure.x_position
                
                print(f"    Measure #{measure_num}: x_position={measure.x_position:.1f}, end_x={measure.end_x:.1f}, width={measure.width:.1f}")
    
    def _calculate_justified_positions(self, total_measures: int) -> List[float]:
        """
        Calculate justified positions implementing ONOTE Rule 1:
        "Inserting a bar line anywhere in the staff equally divides the full page wide 
        staff length from margin to margin by the score's last barline index"
        
        ONOTE SPECIFICATION - Rule 1:
        - ENS (Effective Notation Space) = Staff length - (clef + key signature + time signature offsets)
        - Measure width = ENS / highest_barline_index
        - Equal division regardless of click position within measure
        """
        if total_measures <= 0:
            return []
        
        if total_measures == 1:
            return [self.END_BARLINE_X]
        
        # Calculate ENS (Effective Notation Space)
        # ENS starts after clef/key/time signature offsets (LEFTMOST_NOTE_X)
        # and ends at staff end (END_BARLINE_X)
        ens_start = self.LEFTMOST_NOTE_X
        ens_end = self.END_BARLINE_X
        total_ens = ens_end - ens_start
        
        # Rule 1: Equal division - divide ENS equally by total number of measures
        # The highest barline index equals total_measures (since we number from 1)
        ens_per_measure = total_ens / total_measures
        
        positions = []
        for i in range(total_measures):
            # Position barline i+1 at: ENS_start + (i+1) * ENS_per_measure
            position = ens_start + (i + 1) * ens_per_measure
            positions.append(position)
        
        print(f"TEMPORAL_BRIDGE_V2: Rule 1 - ENS={total_ens:.1f}, measures={total_measures}, ENS_per_measure={ens_per_measure:.1f}")
        
        return positions
    
    def _force_ui_sync(self):
        """Force UI components to sync with updated temporal state"""
        try:
            # Force form widget sync
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if hasattr(widget, '_sync_from_document_to_form_widget'):
                        widget._sync_from_document_to_form_widget()
                        print("TEMPORAL_BRIDGE_V2: Forced form widget sync")
                        break
        except Exception as e:
            print(f"TEMPORAL_BRIDGE_V2: Error forcing UI sync: {e}")
    
    def _load_layout_preferences(self):
        """Load layout preferences for temporal grid"""
        from PyQt6.QtCore import QSettings
        settings = QSettings()
        
        # Update temporal grid settings from preferences
        self.temporal_grid.grid_settings.measures_per_system = int(
            settings.value("notation/max_measures_per_system", 4)
        )
        self.temporal_grid.grid_settings.system_width = float(
            settings.value("layout/system_width", 800.0)
        )
        
        print(f"TEMPORAL_BRIDGE_V2: Loaded preferences - measures_per_system: {self.temporal_grid.grid_settings.measures_per_system}")
    
    def _calculate_staff_end_position(self) -> float:
        """Calculate staff end position from document layout"""
        default_end = 800.0
        
        if self.document:
            if hasattr(self.document, 'renderer') and self.document.renderer:
                page_width = getattr(self.document.renderer, 'page_width', default_end)
                margins = getattr(self.document.renderer, 'margins', {'right': 50})
                return page_width - margins.get('right', 50)
            elif hasattr(self.document, 'layout') and self.document.layout:
                page_width = getattr(self.document.layout, 'page_width', default_end)
                right_margin = getattr(self.document.layout, 'right_margin', 50)
                return page_width - right_margin
        
        return default_end
    
    def sync_from_document_measures(self, document_measures: Dict[int, MeasureObject]):
        """Sync temporal grid from existing document measures (for migration)"""
        print("TEMPORAL_BRIDGE_V2: Syncing temporal grid from document measures")
        
        # Clear existing temporal measures
        self.temporal_grid.measures.clear()
        
        # Create temporal measures from document measures
        for measure_num, measure_obj in document_measures.items():
            temporal_measure = TemporalGridMeasure(
                measure_number=measure_num,
                time_signature=self.temporal_grid.grid_settings.default_time_signature,
                grid_settings=self.temporal_grid.grid_settings
            )
            
            # Copy properties
            temporal_measure.barline_type = getattr(measure_obj, 'barline_type', 'single')
            temporal_measure.calculated_justified_width = getattr(measure_obj, 'width', 160.0)
            temporal_measure.calculated_natural_width = temporal_measure.calculated_justified_width
            
            self.temporal_grid.measures[measure_num] = temporal_measure
            
            print(f"  Created temporal measure #{measure_num} from document")
        
        # Recalculate layout
        self.temporal_grid._recalculate_systems()
        
        print(f"TEMPORAL_BRIDGE_V2: Synced {len(self.temporal_grid.measures)} measures from document")
    
    def create_initial_measure(self) -> MeasureObject:
        """Create initial measure using temporal grid"""
        temporal_measure = self.temporal_grid.create_initial_measure()
        
        # Sync to document
        self._sync_to_document()
        
        return self._convert_to_document_measure(temporal_measure)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get comprehensive debug information"""
        temporal_info = self.temporal_grid.get_debug_info()
        
        bridge_info = {
            "bridge_type": "TemporalBridgeV2",
            "document_measures": len(getattr(self.document, 'measures', {})) if self.document else 0,
            "layout_constants": {
                "SYSTEM_BARLINE_X": self.SYSTEM_BARLINE_X,
                "LEFTMOST_NOTE_X": self.LEFTMOST_NOTE_X,
                "END_BARLINE_X": self.END_BARLINE_X,
            },
            "measure_manager_connected": self.measure_manager is not None
        }
        
        return {
            "temporal_grid": temporal_info,
            "bridge": bridge_info
        }
    
    # Legacy compatibility methods for existing code
    def get_temporal_measures(self) -> List:
        """Legacy compatibility - return empty list"""
        return []
    
    def get_measure_objects(self) -> List[MeasureObject]:
        """Legacy compatibility - return document measures"""
        return list(self.get_all_measures().values())
    
    def _get_current_measures(self) -> List[MeasureObject]:
        """Legacy compatibility - return document measures as list"""
        return list(self.get_all_measures().values())
    
    def temporal_structure_changed_emit(self):
        """Legacy compatibility - emit structure changed signal"""
        self.temporal_structure_changed.emit()
    
    def measure_layout_changed_emit(self):
        """Legacy compatibility - emit layout changed signal"""
        self.measure_layout_changed.emit() 