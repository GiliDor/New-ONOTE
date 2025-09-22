"""
Barline Temporal Bridge for ONOTE - REFINED MODEL

This module implements the refined ONOTE barline and measure model:
1. Initial staff is one unbounded "giant measure #1" 
2. Barline insertion splits measures using practical notation space
3. Uniform visual spacing based on leftmost note position to right barline
4. Proper index shuffling when measures are split
"""

from typing import List, Dict, Optional, Tuple, Any
from PyQt6.QtCore import QObject, pyqtSignal

from .temporal_measure_system import (
    TemporalMeasure, TemporalMeasureManager, 
    NotationElement, Note, Rest, Chord,
    NoteDuration, BeatPosition, TimeSignature
)
from .measure_object import MeasureObject


class BarlineTemporalBridge(QObject):
    """Bridge implementing the refined ONOTE barline and measure model"""
    
    # Signals
    temporal_structure_changed = pyqtSignal()
    notation_element_added = pyqtSignal(int, NotationElement)  # measure_number, element
    notation_element_removed = pyqtSignal(int, NotationElement)
    measure_layout_changed = pyqtSignal()
    
    def __init__(self, document=None, parent=None):
        super().__init__(parent)
        self.document = document
        self.temporal_manager = TemporalMeasureManager()
        
        # INTEGRATION: Get MeasureManager for proper layout instead of hardcoded positions
        self.measure_manager = None
        if document and hasattr(document, 'staff_view') and hasattr(document.staff_view, 'measure_manager'):
            self.measure_manager = document.staff_view.measure_manager
            print("BRIDGE: Connected to existing MeasureManager for proper layout")
        
        # Store document reference for measure management
        self.document = document
        
        # Layout constants (justified positioning system)
        self.SYSTEM_BARLINE_X = 100.0     # Barline 0 (initial system barline)
        # Reduce post-time-signature pad to maximize notation space. This is the unified
        # leftmost position for notes across all systems (clef/key/time + minimal pad)
        self.LEFTMOST_NOTE_X = 210.0
        
        # CRITICAL FIX: Calculate staff end position dynamically instead of hardcoding 1136px
        # The staff end should be calculated from page width and margins
        self.END_BARLINE_X = self._calculate_staff_end_position()
        
        print(f"BRIDGE: Using dynamic END_BARLINE_X = {self.END_BARLINE_X} for barline alignment")
            
        self.default_practical_space = 180.0  # Default practical space per measure
        
        # Load layout preferences
        self._load_layout_preferences()
        
        # Initialize temporal manager with document
        if self.document:
            self.temporal_manager.document = self.document
        
        # SPECIFICATION COMPLIANCE: No automatic measure creation during initialization
        # Score starts with no measures and no barlines except barline 0 at the very left
        print("BRIDGE: Score starts with NO measures (only barline 0) - per ONOTE specification")
        print("BRIDGE: Measures will be created when user first inserts a barline")
        
        print("BRIDGE: BarlineTemporalBridge initialized - ready for user barline creation")
    
    def _load_layout_preferences(self):
        """Load layout preferences for measure spacing"""
        from PyQt6.QtCore import QSettings
        settings = QSettings("ONOTE", "Preferences")

        # Try to read from document settings first, then fallback to QSettings
        measures_per_system = 4
        if self.document and hasattr(self.document, 'settings') and self.document.settings:
            # Preferred document-specific key
            value = self.document.settings.get('layout/measures_per_system', None)
            if value is None:
                # Legacy/compatibility key sometimes used for a cap
                value = self.document.settings.get('notation/max_measures_per_system', None)
            try:
                measures_per_system = int(value) if value is not None else 4
            except Exception:
                measures_per_system = 4
        else:
            # Fallback to application defaults (Preferences)
            try:
                pref_val = settings.value('layout/default_measures_per_system', 4)
                measures_per_system = int(pref_val)
            except Exception:
                measures_per_system = 4
        self.measures_per_system = measures_per_system
        print(f"BRIDGE: Loaded measures per system: {measures_per_system}")

        # Load layout settings from preferences (moved from form widget)
        self.auto_justify = settings.value('layout/auto_justify', True, type=bool)
        self.dynamic_width = settings.value('layout/dynamic_width', False, type=bool)
        self.force_system_break = settings.value('layout/force_system_break', False, type=bool)
        self.custom_measure_width = settings.value('layout/custom_measure_width', False, type=bool)
        self.custom_width_value = float(settings.value('layout/custom_width_value', 120.0))
        self.truncate_empty_measures = settings.value('layout/truncate_empty_measures', False, type=bool)
        
        print(f"BRIDGE: Loaded layout settings - auto_justify: {self.auto_justify}, dynamic_width: {self.dynamic_width}")

        # Minimum practical spacing
        self.minimum_practical_space = int(settings.value("layout/minimum_practical_space", 120))
    
    def reload_layout_preferences(self):
        """Public method to force reload layout preferences from QSettings"""
        print("BRIDGE: Forcing reload of layout preferences")
        self._load_layout_preferences()
        print(f"BRIDGE: Reloaded measures per system: {self.measures_per_system}")
    
    def _force_recalculate_measure_positions(self):
        """
        CRITICAL FIX: Force recalculation of all existing measure positions
        to ensure they use the correct coordinate system.
        """
        # Always reload layout preferences to get latest measures per system
        self._load_layout_preferences()
        if not self.document or not hasattr(self.document, 'measures'):
            return
        
        measures = self._get_current_measures()
        if not measures:
            return
        
        print(f"BRIDGE: Force recalculating positions for {len(measures)} existing measures")
        
        # Calculate justified positions using the correct coordinate system
        total_measures = len(measures)
        justified_positions = self._calculate_justified_positions(total_measures)
        
        # Apply the corrected positions to all measures
        for i, measure in enumerate(measures):
            if i < len(justified_positions):
                old_end = getattr(measure, 'end_x', 0)
                measure.end_x = justified_positions[i]
                measure_num = getattr(measure, 'measure_number', i + 1)
                print(f"BRIDGE: FIXED measure #{measure_num}: end_x {old_end} → {measure.end_x}")
        
        print("BRIDGE: All existing measures repositioned with correct coordinate system")
    
    def _ensure_initial_measure(self):
        """DEPRECATED: This method is no longer used per ONOTE specification.
        Score starts with NO measures and no barlines except barline 0.
        Measures are created only when user first inserts a barline."""
        print("BRIDGE: _ensure_initial_measure called but DISABLED per ONOTE specification")
        print("BRIDGE: Score should start empty - measures created only on user barline insertion")
        return
    
    def _ensure_initial_measure_via_manager(self):
        """DEPRECATED: This method is no longer used per ONOTE specification.
        Score starts with NO measures and no barlines except barline 0.
        Measures are created only when user first inserts a barline."""
        print("BRIDGE: _ensure_initial_measure_via_manager called but DISABLED per ONOTE specification")
        print("BRIDGE: Score should start empty - measures created only on user barline insertion")
        return
    
    def create_initial_measure(self):
        """Create initial measure #1 with single barline (final barline is added automatically at rendering time)"""
        if hasattr(self.document, 'measures') and self.document.measures:
            # Return the existing first measure if it exists
            if 1 in self.document.measures:
                print("BRIDGE: Document already has measures - returning existing measure #1")
                return self.document.measures[1]
            else:
                print("BRIDGE: Document has measures but no measure #1 - creating it")
        else:
            print("BRIDGE: Document has no measures - creating initial measure #1")

        # Get current END_BARLINE_X position (accounts for page setup changes)
        end_barline_x = self.get_current_end_barline_x()
        
        # CRITICAL FIX: Create measure #1 with JUSTIFIED POSITIONING from the start
        # Use justified positioning even for single measure to ensure consistency
        justified_positions = self._calculate_justified_positions(1)  # Single measure justified position
        if justified_positions:
            measure_1_end_x = justified_positions[0]
        else:
            measure_1_end_x = end_barline_x  # Fallback to full width
        
        measure_1 = self._create_measure_object(
            measure_number=1,
            x_position=self.LEFTMOST_NOTE_X,  # Start at leftmost note position (265px)
            end_x=measure_1_end_x,           # FIXED: Use justified position, not full width
            barline_type='single'  # SIMPLIFIED: Always start with single barline
        )

        # Initialize document measures if needed
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}

        # Store the measure
        self.document.measures[1] = measure_1
        
        print(f"BRIDGE: Created initial measure #1 - x_position={self.LEFTMOST_NOTE_X}, end_x={measure_1_end_x}, type=single")
        print(f"BRIDGE: Initial measure spans from leftmost note position to right margin ({measure_1_end_x - self.LEFTMOST_NOTE_X}px notation space)")
        print(f"BRIDGE: Final barline will be applied automatically at rendering time")
        
        return measure_1
    
    def _create_measure_object(self, measure_number: int, x_position: float, end_x: float, barline_type: str = "single") -> MeasureObject:
        """Create a MeasureObject with the specified properties"""
        from .measure_object import MeasureObject
        
        measure = MeasureObject(
            measure_number=measure_number,
            end_x=end_x,
            document=self.document,
            barline_type=barline_type
        )
        
        # Set the x_position (start position of the measure)
        measure.x_position = x_position
        
        # Calculate width
        measure.width = end_x - x_position
        
        print(f"BRIDGE: Created measure object #{measure_number}: x_position={x_position}, end_x={end_x}, width={measure.width}, type={barline_type}")
        return measure
    
    def calculate_leftmost_note_position(self, staff=None) -> float:
        """
        Calculate the leftmost position where a note can be placed.
        This accounts for clef, key signature, time signature, and minimal spacing.
        
        Returns:
            float: X position of leftmost note position (practical notation space start)
        """
        # Use the fixed calculated position for consistency
        return self.LEFTMOST_NOTE_X
    
    def calculate_practical_notation_space(self, start_x: float, end_x: float) -> float:
        """
        Calculate the practical notation space between leftmost note position and right barline.
        
        Args:
            start_x: Left boundary (typically leftmost note position)
            end_x: Right boundary (barline position)
            
        Returns:
            float: Available practical notation space
        """
        return max(0, end_x - start_x)
    
    def create_barline_at_position(self, x_position: float, barline_type: str = "single") -> Optional[MeasureObject]:
        """
        ENHANCED: Create a barline using MeasureManager for proper layout when available,
        with fallback to ATOMIC operations for compatibility
        """
        print(f"\n=== BARLINE CREATION ===")
        print(f"Click position: {x_position}, type: {barline_type}")

        # SPECIAL CASE: Graphical dashed barline does NOT create a measure
        if str(barline_type).lower() == "dashed":
            try:
                # Ensure storage exists on document
                if not hasattr(self.document, 'graphical_dashed_barlines'):
                    self.document.graphical_dashed_barlines = []
                # Minimal dashed barline structure used by StaffView selection logic
                class GraphicalDashedBarline:
                    def __init__(self, x):
                        self.x_position = float(x)
                        self.barline_type = 'dashed'
                        self.selected = False
                        self.is_graphical_dashed = True
                    def contains_x_position(self, x):
                        return abs(self.x_position - float(x)) < 5.0
                dashed = GraphicalDashedBarline(x_position)
                self.document.graphical_dashed_barlines.append(dashed)
                print(f"BRIDGE: Added graphical dashed barline at x={x_position}; no measure created")
                # Notify view to repaint if available
                if hasattr(self.document, 'staff_view') and self.document.staff_view:
                    self.document.staff_view.update()
                return dashed
            except Exception as e:
                print(f"BRIDGE: Error creating graphical dashed barline: {e}")
                return None

        # Always reload layout preferences to get latest measures per system
        self._load_layout_preferences()
        
        # INTEGRATION: Use MeasureManager if available for proper responsive layout
        if self.measure_manager:
            return self._create_barline_via_manager(x_position, barline_type)
        else:
            return self._create_barline_atomic(x_position, barline_type)

    def insert_measures_batch(self, count: int, insertion_after_measure: Optional[int] = None) -> list:
        """Insert multiple measures in a batch.
        - If insertion_after_measure is None, append at end of score.
        - Otherwise, insert after the given measure number by repeatedly splitting to the right of it.
        Returns list of created MeasureObjects.
        """
        created: list = []
        try:
            self._load_layout_preferences()
            current = self._get_current_measures() or []
            if not current:
                # Create the very first measure, then keep appending
                first = self.create_initial_measure()
                if first:
                    created.append(first)
                current = self._get_current_measures() or []

            def _rightmost_end_x(measures):
                return max(float(getattr(m, 'end_x', 0.0)) for m in measures if hasattr(m, 'end_x'))

            # Compute base x for insertion loop
            if insertion_after_measure is None:
                base_x = _rightmost_end_x(current) + 1.0
            else:
                # Insert after a specific measure: click just to the right of its end
                m = next((m for m in current if getattr(m, 'measure_number', -1) == insertion_after_measure), None)
                base_x = float(getattr(m, 'end_x', _rightmost_end_x(current))) + 1.0

            for i in range(int(max(0, count))):
                m = self._create_barline_atomic(base_x, 'single')
                if m:
                    created.append(m)
                # Advance base_x to the new rightmost after each add
                cur = self._get_current_measures() or []
                base_x = _rightmost_end_x(cur) + 1.0

            # Normalize barline types so only the last is 'final'
            try:
                ordered = sorted([k for k in self.document.measures.keys() if isinstance(k, int)])
                if ordered:
                    last_num = ordered[-1]
                    for num in ordered:
                        m = self.document.measures.get(num)
                        if not m:
                            continue
                        m.barline_type = 'final' if num == last_num else 'single'
            except Exception:
                pass

            # Trigger refresh
            self._force_form_widget_sync()
            self.temporal_structure_changed.emit()
            self.measure_layout_changed.emit()
            return created
        except Exception as e:
            print(f"BRIDGE: insert_measures_batch error: {e}")
            return created
    
    def _create_barline_via_manager(self, x_position: float, barline_type: str) -> Optional[MeasureObject]:
        """
        Create barline using MeasureManager implementing ONOTE index inheritance model.
        
        ONOTE SPECIFICATION - RULE 2:
        "Check the index of the bar line to the left, and increment it by 1"
        
        Implementation:
        - New barline inherits index of barline to its right (splits existing measure)
        - Target measure gets the new barline type  
        - All measures to the right are incremented (Rule 2 compliance)
        - Final barline type is preserved on the rightmost measure
        - Positioning follows Rule 1 (equal division regardless of click position)
        """
        print("BRIDGE: Using MeasureManager for barline creation (ONOTE index inheritance model)")
        
        # STEP 0: System limit no longer blocks creation; wrapping handled by renderer
        current_measures = self._get_current_measures()
        
        # STEP 1: Handle initial state - create first measure if none exist
        if not current_measures:
            print("BRIDGE: No measures exist - creating first measure (ONOTE specification compliance)")
            first_measure = self.create_initial_measure()
            return first_measure
        
        # STEP 2: Find target measure using current position - WITH TYPE VALIDATION
        current_measures = self._get_current_measures()
        
        # CRITICAL FIX: Validate that all measures are actually MeasureObject instances
        validated_measures = []
        for measure in current_measures:
            if hasattr(measure, 'measure_number') and hasattr(measure, 'barline_type'):
                validated_measures.append(measure)
            else:
                print(f"BRIDGE: WARNING - Invalid measure object found: {type(measure)}, skipping")
                print(f"BRIDGE: Measure has measure_number: {hasattr(measure, 'measure_number')}")
                print(f"BRIDGE: Measure has barline_type: {hasattr(measure, 'barline_type')}")
        
        if not validated_measures:
            print("BRIDGE: ERROR - No valid MeasureObject instances found")
            return None
        
        print(f"BRIDGE: Found {len(validated_measures)} valid measures for position finding")
        
        # Allow clicks anywhere on staff: left of first measure -> split first; right of last -> append
        first_measure_start = self._get_measure_start_x(validated_measures[0])
        last_end = getattr(validated_measures[-1], 'end_x', first_measure_start)
        if x_position < first_measure_start:
            target_measure = validated_measures[0]
            print(f"BRIDGE: Click left of first measure; targeting measure #1 for split")
        else:
            target_measure = self._find_measure_containing_position(x_position, validated_measures)
        
        if not target_measure:
            print(f"BRIDGE: No existing measure contains position {x_position} - creating new measure at end")
            # Create a new measure at the end when clicking beyond existing measures
            current_measure_count = len(validated_measures)
            new_measure_number = current_measure_count + 1
            
            print(f"RULE2: New measure #{new_measure_number} = last measure index ({current_measure_count}) + 1")
            
            # Create the new measure with single barline type
            new_measure = MeasureObject(
                measure_number=new_measure_number,
                end_x=x_position,  # Position where user clicked (will be recalculated per Rule 1)
                document=self.document,
                barline_type='single'
            )
            
            # Add to document (ensure dict)
            if not isinstance(getattr(self.document, 'measures', {}), dict):
                try:
                    self.document.set_measures(self.document.get_measures())
                except Exception:
                    self.document.measures = {}
            self.document.measures[new_measure_number] = new_measure
            print(f"BRIDGE: Created new measure #{new_measure_number} at position {x_position}")
            
            # RULE 1: Recalculate layout with justified positioning (ignores click position)
            try:
                if hasattr(self.measure_manager, 'recalculate_complete_layout'):
                    self.measure_manager.recalculate_complete_layout()
                    print(f"BRIDGE: MeasureManager handled layout for new measure")
                else:
                    self._ensure_all_measures_justified()
            except Exception as e:
                print(f"BRIDGE: Layout error: {e} - using justified positioning")
                self._ensure_all_measures_justified()
            
            # Force form widget sync and emit signals
            self._force_form_widget_sync()
            self.temporal_structure_changed.emit()
            self.measure_layout_changed.emit()
            
            return new_measure
        
        # CRITICAL FIX: Validate that target_measure is a proper MeasureObject
        if not hasattr(target_measure, 'measure_number'):
            print(f"BRIDGE: ERROR - target_measure is not a valid MeasureObject: {type(target_measure)}")
            print(f"BRIDGE: Has measure_number: {hasattr(target_measure, 'measure_number')}")
            print(f"BRIDGE: Has barline_type: {hasattr(target_measure, 'barline_type')}")
            return None
        
        target_number = getattr(target_measure, 'measure_number', 1)
        print(f"Target measure: #{target_number}")
        
        # STEP 3: ONOTE Model - Implement proper index inheritance per Rule 2
        try:
            # CRITICAL: Store the original barline type of the target measure (will be pushed right)
            original_target_barline_type = getattr(target_measure, 'barline_type', 'single')
            print(f"BRIDGE: Original target measure #{target_number} barline type: '{original_target_barline_type}'")
            
            # STEP 3: CORRECT ONOTE MODEL - Split the target measure in place
            print(f"BRIDGE: SPLITTING measure #{target_number} in place (ONOTE model)")
            print(f"RULE2: Click in measure #{target_number} creates new measure #{target_number + 1}")
            
            # STEP 3a: SIMPLIFIED - Left part always gets 'single' barline type
            target_measure.barline_type = 'single'
            print(f"BRIDGE: Left part: measure #{target_number} gets 'single' barline type")
            
            # STEP 3b: Implement proper shuffle insertion per RULE 2
            # "All measures to the right until the end of the score will be incremented"
            existing_measures = sorted([num for num in self.document.measures.keys() if isinstance(num, int)])
            
            # Shuffle all measures with numbers > target_number to make room
            measures_to_shuffle = [num for num in existing_measures if num > target_number]
            print(f"RULE2: Measures to increment: {measures_to_shuffle}")
            
            # Create a new measures dict to replace the old one
            new_measures_dict = {}
            
            # Copy all measures up to and including target
            for num in existing_measures:
                if num <= target_number:
                    new_measures_dict[num] = self.document.measures[num]
            
            # RULE 2: Create the new measure (inherits target_number + 1)
            new_measure_number = target_number + 1
            new_measure = MeasureObject(
                measure_number=new_measure_number,
                end_x=0,  # Will be set by Rule 1 positioning (justified layout)
                document=self.document,
                barline_type='single'  # SIMPLIFIED: Always use single barlines
            )
            new_measures_dict[new_measure_number] = new_measure
            print(f"RULE2: Created new measure #{new_measure_number} (target + 1)")
            
            # RULE 2: Shuffle all measures that were after target to the right
            # "All measures and bar lines to the right until the end of the score will be incremented"
            for old_num in measures_to_shuffle:
                old_measure = self.document.measures[old_num]
                new_num = old_num + 1
                old_measure.measure_number = new_num  # Update the measure's internal number
                new_measures_dict[new_num] = old_measure
                print(f"RULE2: Incremented measure #{old_num} → #{new_num}")
            
            # Replace the document's measures dict
            self.document.measures = new_measures_dict
            
            print(f"RULE2: ✓ Index inheritance complete: split #{target_number}, inserted #{new_measure_number}, incremented {len(measures_to_shuffle)} measures")
            
            # STEP 4: Apply Rule 1 - Use justified positioning regardless of click position
            try:
                print("RULE1: Starting equal division layout recalculation")
                if hasattr(self.measure_manager, 'recalculate_complete_layout'):
                    self.measure_manager.recalculate_complete_layout()
                    print(f"BRIDGE: MeasureManager handled Rule 1 layout - responsive system with pagination")
                else:
                    print("BRIDGE: MeasureManager missing recalculate_complete_layout method - using atomic positioning")
                    self._apply_atomic_positioning()
                    
                # CRITICAL FIX: Ensure ALL measures (including existing ones) use justified positioning per Rule 1
                self._ensure_all_measures_justified()
                
            except AttributeError as e:
                print(f"BRIDGE: MeasureManager layout error: {e} - using atomic positioning")
                self._apply_atomic_positioning()
                self._ensure_all_measures_justified()
            
            # STEP 5: SIMPLIFIED - Ensure ALL measures use 'single' barlines consistently
            # Final barlines should only be applied at rendering time, not stored in measure objects
            for num in sorted(self.document.measures.keys()):
                if isinstance(num, int):
                    measure = self.document.measures[num]
                    if hasattr(measure, 'barline_type') and measure.barline_type != 'single':
                        measure.barline_type = 'single'
                        print(f"BRIDGE: Forced measure #{num} to use 'single' barline type")
            
            print("BRIDGE: All measures now use 'single' barlines - final barline applied only at rendering")
            
            # STEP 6: Verify the final result
            print("BRIDGE: Verifying ONOTE Rules implementation:")
            final_measures = sorted([num for num in self.document.measures.keys() if isinstance(num, int)])
            print(f"BRIDGE: Final measure sequence: {final_measures}")
            
            # Force form widget sync and emit signals
            self._force_form_widget_sync()
            self.temporal_structure_changed.emit()
            self.measure_layout_changed.emit()
            
            return new_measure
            
        except Exception as e:
            print(f"BRIDGE: Error in ONOTE model implementation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _apply_atomic_positioning(self):
        """Apply atomic positioning when MeasureManager is unavailable or incomplete"""
        print("BRIDGE: Applying atomic positioning fallback")
        
        measures = self._get_current_measures()
        total_measures = len(measures)
        # Compact-single override: skip justification entirely
        if total_measures == 1 and getattr(measures[0], 'keep_compact', False):
            print("BRIDGE: Compact single measure detected - skipping justification pass")
            return
        justified_positions = self._calculate_justified_positions(total_measures)
        
    def _ensure_all_measures_justified(self):
        """Ensure ALL measures in the document use consistent justified positioning"""
        print("BRIDGE: Ensuring all measures use justified positioning")
        
        measures = self._get_current_measures()
        if not measures:
            print("BRIDGE: No measures to justify")
            return
        
        total_measures = len(measures)
        # Compact-single override: skip justification entirely
        if total_measures == 1 and getattr(measures[0], 'keep_compact', False):
            print("BRIDGE: Compact single measure detected - skipping _ensure_all_measures_justified")
            return
        print(f"BRIDGE: Justifying {total_measures} measures")
        
        justified_positions = self._calculate_justified_positions(total_measures)
        if not justified_positions:
            print("BRIDGE: No justified positions calculated")
            return
        
        # Sort measures by measure number to ensure consistent ordering
        sorted_measures = sorted(measures, key=lambda m: getattr(m, 'measure_number', 0))

        # Defensive fix: if any supplied end_x would be non-monotonic, ignore and fall back to grid
        def is_monotonic(values):
            prev = float('-inf')
            for v in values:
                if v < prev:
                    return False
                prev = v
            return True
        existing_positions = [getattr(m, 'end_x', 0.0) for m in sorted_measures]
        if not is_monotonic(existing_positions):
            print(f"BRIDGE: Detected non-monotonic end_x sequence {existing_positions} → enforcing justified grid")
        
        # Apply justified positions to ALL measures with EQUAL NOTATION SPACE
        for i, measure in enumerate(sorted_measures):
            if i < len(justified_positions):
                old_end_x = getattr(measure, 'end_x', 0)
                measure.end_x = justified_positions[i]
                
                # CRITICAL FIX: All measures start from LEFTMOST_NOTE_X (notation space start)
                # This ensures equal notation space for all measures, regardless of initial elements
                if i == 0:
                    # First measure: notation space starts after clef/key/time elements
                    start_x = self.LEFTMOST_NOTE_X
                else:
                    # Subsequent measures: start immediately after previous barline
                    start_x = justified_positions[i-1]
                
                # Calculate notation space width (equal for all measures when justified)
                notation_width = measure.end_x - start_x
                
                measure.x_position = start_x
                measure.width = notation_width
                
                measure_num = getattr(measure, 'measure_number', i+1)
                print(f"BRIDGE: Updated measure #{measure_num} - end_x: {old_end_x} → {measure.end_x}, notation_width: {notation_width}")
            else:
                print(f"BRIDGE: WARNING - No justified position for measure #{getattr(measure, 'measure_number', i+1)}")
        
        print(f"BRIDGE: Justified positioning applied to {len(sorted_measures)} measures")
    
    def _create_barline_atomic(self, x_position: float, barline_type: str) -> Optional[MeasureObject]:
        """
        Create barline using atomic ONOTE model with proper index inheritance.
        
        ONOTE SPECIFICATION - RULE 2:
        "Check the index of the bar line to the left, and increment it by 1"
        
        Implementation:
        - New barline inherits index of barline to its right (splits existing measure)
        - Target measure gets the new barline type  
        - All measures to the right are incremented (Rule 2 compliance)
        - Final barline type is preserved on the rightmost measure
        - Positioning follows Rule 1 (equal division regardless of click position)
        """
        print("\\n=== ATOMIC BARLINE CREATION ===")
        print(f"Click position: {x_position}, type: {barline_type}")
        
        # STEP 0: Validate document state
        if not self.document or not hasattr(self.document, 'measures'):
            print("BRIDGE: No document or measures collection - creating initial measure")
            if not hasattr(self.document, 'measures'):
                self.document.measures = {}
            first_measure = self.create_initial_measure()
            return first_measure
        
        # STEP 1: Get and validate current measures
        current_measures = self._get_current_measures()
        print(f"BRIDGE: Found {len(current_measures)} valid measures")
        
        # STEP 2: System limit no longer blocks creation; wrapping handled by renderer
        
        # STEP 3: Handle initial state - create first measure if none exist
        if not current_measures:
            print("BRIDGE: No measures exist - creating first measure (ONOTE specification compliance)")
            first_measure = self.create_initial_measure()
            return first_measure
        
        # STEP 4: Find target measure using current position
        sorted_measures = sorted(current_measures, key=lambda m: getattr(m, 'measure_number', 999))
        measure_numbers = [getattr(m, 'measure_number', 0) for m in sorted_measures]
        print(f"BRIDGE: Measure numbers in order: {measure_numbers}")
        
        print(f"BRIDGE: Finding measure containing position {x_position} among {len(sorted_measures)} measures:")
        target_measure = None
        
        for measure in sorted_measures:
            measure_num = getattr(measure, 'measure_number', 0)
            measure_start = self._get_measure_start_x(measure)
            measure_end = getattr(measure, 'end_x', 0)
            
            print(f"  Checking measure #{measure_num}: x={measure_start} to {measure_end}")
            
            if measure_start <= x_position < measure_end:
                target_measure = measure
                print(f"BRIDGE: ✓ Position {x_position} is in measure #{measure_num} (x={measure_start} to {measure_end})")
                break
            else:
                print(f"BRIDGE: ✗ Position {x_position} NOT in measure #{measure_num} (x={measure_start} to {measure_end})")
        
        # STEP 5: Handle position beyond existing measures, and clamp left-of-first to first
        if not target_measure:
            if sorted_measures:
                first_start = self._get_measure_start_x(sorted_measures[0])
                rightmost_measure = sorted_measures[-1]
                rightmost_end = getattr(rightmost_measure, 'end_x', 0)
                if x_position < first_start:
                    target_measure = sorted_measures[0]
                    print(f"BRIDGE: Click left of first measure; targeting measure #1 for split")
                elif x_position >= rightmost_end:
                    print(f"BRIDGE: Position {x_position} is beyond rightmost measure (end={rightmost_end})")
                    print(f"BRIDGE: Creating new measure at end")
                    
                    # Create a new measure at the end
                    new_measure_number = len(sorted_measures) + 1
                    new_measure = self._create_measure_object(
                        measure_number=new_measure_number,
                        x_position=rightmost_end,
                        end_x=x_position,
                        barline_type='single'
                    )
                    
                    # Add to document (ensure dict)
                    if not isinstance(getattr(self.document, 'measures', {}), dict):
                        try:
                            self.document.set_measures(self.document.get_measures())
                        except Exception:
                            self.document.measures = {}
                    self.document.measures[new_measure_number] = new_measure
                    print(f"BRIDGE: Created new measure #{new_measure_number} at position {x_position}")
                    
                    # Apply justified positioning across all systems
                    self._ensure_all_measures_justified()
                    
                    # Normalize barline types so only the last measure is 'final'
                    try:
                        ordered = sorted([k for k in self.document.measures.keys() if isinstance(k, int)])
                        if ordered:
                            last_num = ordered[-1]
                            for num in ordered:
                                m = self.document.measures.get(num)
                                if m is None:
                                    continue
                                if num == last_num:
                                    m.barline_type = 'final'
                                else:
                                    if getattr(m, 'barline_type', 'single') == 'final':
                                        m.barline_type = 'single'
                            print(f"BRIDGE: Normalized barline types so only measure #{last_num} is 'final' after append")
                    except Exception as e:
                        print(f"BRIDGE: Error normalizing barline types after append: {e}")
                    
                    # Force updates
                    self._force_form_widget_sync()
                    self.temporal_structure_changed.emit()
                    self.measure_layout_changed.emit()
                    
                    return new_measure
            
            print(f"BRIDGE: No existing measure contains position {x_position} - invalid position")
            return None
        
        # STEP 6: ONOTE Model - Split the target measure
        target_number = getattr(target_measure, 'measure_number', 1)
        print(f"Target measure: #{target_number}")
        
        print("\\n--- SPLITTING MEASURE (ONOTE Index Inheritance) ---")
        
        # Store original barline type
        original_target_barline_type = getattr(target_measure, 'barline_type', 'single')
        print(f"BRIDGE: Target measure #{target_number} original barline type: '{original_target_barline_type}'")
        
        # STEP 6a: Update target measure (left part)
        # If the target was 'final', demote it to 'single' and move 'final' to the new rightmost later
        if getattr(target_measure, 'barline_type', 'single') == 'final':
            print(f"BRIDGE: Demoting target measure #{target_number} barline from 'final' to 'single' prior to split")
        target_measure.barline_type = 'single'
        print(f"BRIDGE: Left part: measure #{target_number} gets 'single' barline type")
        
        # STEP 6b: Create new measure (right part)
        new_measure_number = target_number + 1
        new_measure = self._create_measure_object(
            measure_number=new_measure_number,
            x_position=0,  # Will be set by justified positioning
            end_x=0,       # Will be set by justified positioning
            barline_type='single'
        )
        
        # STEP 6c: Increment all measures to the right
        measures_to_increment = [num for num in self.document.measures.keys() if isinstance(num, int) and num > target_number]
        print(f"RULE2: Measures to increment: {measures_to_increment}")
        
        # Create new measures dict
        new_measures_dict = {}
        
        # Copy measures up to and including target
        for num in sorted(self.document.measures.keys()):
            if isinstance(num, int) and num <= target_number:
                new_measures_dict[num] = self.document.measures[num]
        
        # Add new measure
        new_measures_dict[new_measure_number] = new_measure
        print(f"RULE2: Created new measure #{new_measure_number}")
        
        # Increment measures to the right
        for old_num in measures_to_increment:
            old_measure = self.document.measures[old_num]
            new_num = old_num + 1
            old_measure.measure_number = new_num
            new_measures_dict[new_num] = old_measure
            print(f"RULE2: Incremented measure #{old_num} → #{new_num}")
        
        # Replace document measures
        self.document.measures = new_measures_dict
        
        print(f"BRIDGE: ✓ Split complete: measure #{target_number} + measure #{new_measure_number}")
        print(f"BRIDGE: Document now has {len(new_measures_dict)} measures")
        
        # STEP 7: Apply Rule 1 - Justified positioning
        print("RULE1: Applying justified positioning")
        self._ensure_all_measures_justified()
        
        # STEP 7b: Ensure only the last measure has 'final' barline after the split
        try:
            ordered = sorted([k for k in self.document.measures.keys() if isinstance(k, int)])
            if ordered:
                last_num = ordered[-1]
                for num in ordered:
                    m = self.document.measures.get(num)
                    if m is None:
                        continue
                    if num == last_num:
                        m.barline_type = 'final'
                    else:
                        if getattr(m, 'barline_type', 'single') == 'final':
                            m.barline_type = 'single'
                print(f"BRIDGE: Normalized barline types so only measure #{last_num} is 'final'")
        except Exception as e:
            print(f"BRIDGE: Error normalizing barline types: {e}")
        
        # STEP 8: Verify result
        final_measures = sorted([num for num in self.document.measures.keys() if isinstance(num, int)])
        print(f"BRIDGE: Final measure sequence: {final_measures}")
        
        # Force updates
        self._force_form_widget_sync()
        self.temporal_structure_changed.emit()
        self.measure_layout_changed.emit()
        
        return new_measure
    
    def _find_measure_containing_position(self, x_position: float, measures: List[MeasureObject]) -> Optional[MeasureObject]:
        """
        FIXED: Find which measure contains the given x position
        Uses proper boundary detection logic with support for extending the rightmost measure
        """
        print(f"BRIDGE: Finding measure containing position {x_position} among {len(measures)} measures:")
        
        if not measures:
            print("BRIDGE: No measures available")
            return None
        
        # Sort measures by measure number to ensure proper order
        sorted_measures = sorted(measures, key=lambda m: getattr(m, 'measure_number', 0))
        
        # Check if position is before the first measure
        if x_position < self.LEFTMOST_NOTE_X:
            print(f"BRIDGE: Position {x_position} is before notation area (starts at {self.LEFTMOST_NOTE_X})")
            return None
        
        tolerance = 8.0  # pixels; allow slight overshoot/undershoot to still count as inside
        for i, measure in enumerate(sorted_measures):
            measure_num = getattr(measure, 'measure_number', 1)
            
            # Calculate measure boundaries
            if measure_num == 1:
                start_x = self.LEFTMOST_NOTE_X  # First measure starts at notation area
            else:
                # Find previous measure's end position
                prev_measure = sorted_measures[i-1] if i > 0 else None
                start_x = getattr(prev_measure, 'end_x', self.LEFTMOST_NOTE_X) if prev_measure else self.LEFTMOST_NOTE_X
            
            end_x = getattr(measure, 'end_x', self.END_BARLINE_X)
            
            print(f"  Checking measure #{measure_num}: x={start_x} to {end_x}")
            
            # Position is in measure if start_x <= position <= end_x
            if (start_x - tolerance) <= x_position <= (end_x + tolerance):
                print(f"BRIDGE: ✓ Position {x_position} is in measure #{measure_num} (x={start_x} to {end_x})")
                return measure
            else:
                print(f"BRIDGE: ✗ Position {x_position} NOT in measure #{measure_num} (x={start_x} to {end_x})")
        
        # CRITICAL FIX: Do NOT append at end via clicking; require split inside measure
        rightmost_measure = sorted_measures[-1]
        rightmost_end = getattr(rightmost_measure, 'end_x', self.END_BARLINE_X)
        
        if (rightmost_end + tolerance) < x_position:
            print(f"BRIDGE: Position {x_position} is beyond rightmost (end={rightmost_end}); per spec, no append on click. Returning None.")
            return None
        
        print(f"BRIDGE: Position {x_position} is not within any measure boundaries or reasonable staff bounds")
        return None
    
    def _get_current_measures(self):
        """Get current measures from document with type validation and proper sorting"""
        if not self.document or not hasattr(self.document, 'measures'):
            return []

        measures = self.document.measures
        if isinstance(measures, dict):
            # CRITICAL FIX: Filter out invalid measures and sort by measure number
            valid_measures = []
            invalid_keys = []
            
            for key, measure in measures.items():
                # Only include measures that are proper MeasureObject instances
                if (isinstance(measure, object) and 
                    hasattr(measure, 'measure_number') and 
                    hasattr(measure, 'end_x') and 
                    hasattr(measure, 'barline_type')):
                    
                    # Additional validation: ensure measure_number is valid
                    measure_num = getattr(measure, 'measure_number', None)
                    if measure_num is not None and isinstance(measure_num, (int, float)) and measure_num > 0:
                        valid_measures.append(measure)
                    else:
                        print(f"BRIDGE: Filtered out measure with invalid number at key {key}: {measure_num}")
                        invalid_keys.append(key)
                else:
                    print(f"BRIDGE: Filtered out invalid measure at key {key}: {type(measure)}")
                    print(f"  Has measure_number: {hasattr(measure, 'measure_number')}")
                    print(f"  Has end_x: {hasattr(measure, 'end_x')}")
                    print(f"  Has barline_type: {hasattr(measure, 'barline_type')}")
                    invalid_keys.append(key)
            
            # Remove invalid measures from document
            for key in invalid_keys:
                if key in measures:
                    del measures[key]
                    print(f"BRIDGE: Removed invalid measure at key {key}")
            
            # CRITICAL FIX: Sort measures by measure_number to ensure consistent ordering
            valid_measures.sort(key=lambda m: getattr(m, 'measure_number', 0))
            
            # DEFENSIVE CORRECTION: Ensure end_x positions are strictly non-decreasing.
            # If not, enforce justified positions immediately to repair state before rendering.
            try:
                end_positions = [float(getattr(m, 'end_x', 0.0)) for m in valid_measures]
                non_monotonic = False
                prev_pos = float('-inf')
                for pos in end_positions:
                    if pos < prev_pos:
                        non_monotonic = True
                        break
                    prev_pos = pos
                if non_monotonic:
                    print(f"BRIDGE: Detected non-monotonic measure positions {end_positions} — enforcing justified grid")
                    justified_positions = self._calculate_justified_positions(len(valid_measures))
                    for i, measure in enumerate(valid_measures):
                        old_end = getattr(measure, 'end_x', 0.0)
                        new_end = justified_positions[i] if i < len(justified_positions) else old_end
                        measure.end_x = new_end
                        # Update start/width coherently
                        start_x = self.LEFTMOST_NOTE_X if i == 0 else justified_positions[i - 1]
                        measure.x_position = start_x
                        measure.width = max(0.0, new_end - start_x)
                        print(f"BRIDGE: Repaired measure #{getattr(measure, 'measure_number', i+1)} end_x {old_end} → {new_end}")
            except Exception as e:
                print(f"BRIDGE: Error during monotonic repair in _get_current_measures: {e}")

            # Check for duplicate measure numbers
            measure_numbers = [getattr(m, 'measure_number', 0) for m in valid_measures]
            if len(measure_numbers) != len(set(measure_numbers)):
                print(f"BRIDGE: WARNING - Duplicate measure numbers detected: {measure_numbers}")
                # Keep only the first occurrence of each measure number
                seen_numbers = set()
                unique_measures = []
                for measure in valid_measures:
                    num = getattr(measure, 'measure_number', 0)
                    if num not in seen_numbers:
                        seen_numbers.add(num)
                        unique_measures.append(measure)
                    else:
                        print(f"BRIDGE: Removed duplicate measure #{num}")
                valid_measures = unique_measures
            
            print(f"BRIDGE: _get_current_measures found {len(valid_measures)} valid measures out of {len(measures)} total items")
            print(f"BRIDGE: Measure numbers in order: {[getattr(m, 'measure_number', 'unknown') for m in valid_measures]}")
            return valid_measures
        else:
            # Handle list case with validation
            if isinstance(measures, list):
                valid_measures = []
                for i, measure in enumerate(measures):
                    if (isinstance(measure, object) and 
                        hasattr(measure, 'measure_number') and 
                        hasattr(measure, 'end_x') and 
                        hasattr(measure, 'barline_type')):
                        
                        # Additional validation
                        measure_num = getattr(measure, 'measure_number', None)
                        if measure_num is not None and isinstance(measure_num, (int, float)) and measure_num > 0:
                            valid_measures.append(measure)
                        else:
                            print(f"BRIDGE: Filtered out measure with invalid number at index {i}: {measure_num}")
                    else:
                        print(f"BRIDGE: Filtered out invalid measure at index {i}: {type(measure)}")
                
                # CRITICAL FIX: Sort measures by measure_number
                valid_measures.sort(key=lambda m: getattr(m, 'measure_number', 0))
                
                print(f"BRIDGE: _get_current_measures found {len(valid_measures)} valid measures out of {len(measures)} total items")
                print(f"BRIDGE: Measure numbers in order: {[getattr(m, 'measure_number', 'unknown') for m in valid_measures]}")
                return valid_measures
            else:
                print(f"BRIDGE: Unexpected measures type: {type(measures)}")
                return []
    
    def _ensure_coordinates_are_correct(self, measures_list):
        """
        CRITICAL FIX: Ensure all measures use the correct refined model coordinates.
        This detects measures with old/wrong coordinates and fixes them.
        """
        if not measures_list:
            return
            
        # Check if any measures have coordinates that don't match the refined model
        needs_fixing = False
        total_measures = len(measures_list)
        
        print(f"BRIDGE: Checking {total_measures} measures for coordinate correctness...")
        
        for i, measure in enumerate(measures_list):
            if hasattr(measure, 'end_x'):
                current_end_x = measure.end_x
                
                # Calculate what the end_x SHOULD be using the refined model
                expected_positions = self._calculate_justified_positions(total_measures)
                if i < len(expected_positions):
                    expected_end_x = expected_positions[i]
                    
                    # Check if the current position is significantly different from expected
                    difference = abs(current_end_x - expected_end_x)
                    
                    if difference > 5.0:  # More than 5px difference indicates wrong coordinates
                        print(f"BRIDGE: Measure #{i+1} has wrong end_x: {current_end_x} (expected: {expected_end_x}, difference: {difference}px)")
                        needs_fixing = True
                    else:
                        print(f"BRIDGE: Measure #{i+1} has correct end_x: {current_end_x} (expected: {expected_end_x})")
        
        if needs_fixing:
            print("BRIDGE: Detected measures with wrong coordinates - force fixing...")
            
            # Calculate the correct justified positions for all measures
            correct_positions = self._calculate_justified_positions(total_measures)
            
            # Fix each measure's coordinates
            for i, measure in enumerate(measures_list):
                if i < len(correct_positions) and hasattr(measure, 'end_x'):
                    old_end_x = measure.end_x
                    new_end_x = correct_positions[i]
                    
                    if abs(old_end_x - new_end_x) > 5.0:  # Only fix if significantly different
                        # Update the measure coordinates
                        measure.end_x = new_end_x
                        
                        # Also update other position-related attributes
                        if i == 0:
                            # First measure starts at leftmost note position
                            measure.x_position = self.LEFTMOST_NOTE_X
                            measure.width = new_end_x - self.LEFTMOST_NOTE_X
                        else:
                            # Subsequent measures start where previous measure ended
                            prev_end_x = correct_positions[i-1]
                            measure.x_position = prev_end_x + self.BARLINE_SPACING
                            measure.width = new_end_x - measure.x_position
                        
                        print(f"BRIDGE: FORCE FIXED measure #{i+1}: end_x {old_end_x} → {new_end_x}")
            
            print("BRIDGE: Force fix complete - all measures now have correct coordinates")
        else:
            print("BRIDGE: All measures already have correct coordinates")
    
    def _calculate_justified_positions(self, total_measures):
        """
        Calculate justified positions for measures using ONOTE's justified grid system.
        
        ENHANCED: Now includes system wrapping based on measures per system preference.
        
        ONOTE SPECIFICATION - RULE 1:
        "Inserting a bar line anywhere in the staff equally divides the full page wide 
        staff length from margin to margin by the score's last barline index"
        
        SYSTEM WRAPPING:
        - Respects "measures per system" preference (default: 4)
        - Creates new systems when measure count exceeds the limit
        - Each system gets its own justified positioning
        """
        if total_measures <= 0:
            return []
        
        # Get current END_BARLINE_X (dynamically updated)
        end_barline_x = self.get_current_end_barline_x()
        
        # Get measures per system from preferences
        measures_per_system = self.measures_per_system
        print(f"SYSTEM_WRAP: Using {measures_per_system} measures per system")
        
        if total_measures == 1:
            # Compact mode support: if the single measure was marked compact, keep its own end_x
            try:
                if hasattr(self.document, 'measures') and isinstance(self.document.measures, dict) and self.document.measures:
                    m = self.document.measures.get(1)
                    if m is not None and getattr(m, 'keep_compact', False):
                        compact_end = float(getattr(m, 'compact_end_x', getattr(m, 'end_x', end_barline_x)))
                        print(f"RULE1-OVERRIDE: Single compact measure keeps end_x at {compact_end}")
                        return [compact_end]
            except Exception:
                pass
            # Default: single measure spans full width - from leftmost to end barline
            print(f"RULE1: Single measure spans full notation space to end barline at {end_barline_x}")
            return [end_barline_x]
        
        # Calculate how many systems we need
        systems_needed = (total_measures + measures_per_system - 1) // measures_per_system
        print(f"SYSTEM_WRAP: Need {systems_needed} systems for {total_measures} measures")
        
        justified_positions = []
        current_measure = 0
        
        for system_index in range(systems_needed):
            # Calculate measures in this system
            measures_in_this_system = min(measures_per_system, total_measures - current_measure)
            print(f"SYSTEM_WRAP: System {system_index + 1} will have {measures_in_this_system} measures")
            
            if measures_in_this_system <= 0:
                break
            
            # Calculate justified positions for this system
            system_positions = self._calculate_system_justified_positions(
                measures_in_this_system, 
                end_barline_x,
                system_index
            )
            
            justified_positions.extend(system_positions)
            current_measure += measures_in_this_system
            
            print(f"SYSTEM_WRAP: System {system_index + 1} positions: {[f'{pos:.1f}' for pos in system_positions]}")
        
        print(f"SYSTEM_WRAP: ✓ Calculated {len(justified_positions)} total positions across {systems_needed} systems")
        return justified_positions
    
    def _calculate_system_justified_positions(self, measures_in_system: int, end_barline_x: float, system_index: int):
        """
        Calculate justified positions for measures within a single system.
        
        Args:
            measures_in_system: Number of measures in this system
            end_barline_x: End position for this system
            system_index: Index of this system (0-based)
        """
        if measures_in_system <= 0:
            return []
        
        # Available notation space for this system (full width from leftmost to right margin)
        leftmost_x = self.calculate_leftmost_note_position()
        total_notation_space = end_barline_x - leftmost_x

        # IMPORTANT: Do not stretch incomplete final systems to the full width.
        # Use unit width based on max measures per system, so a freshly wrapped line
        # grows one-measure at a time as measures are added.
        max_per_system = max(1, int(getattr(self, 'measures_per_system', measures_in_system)))
        notation_space_per_measure = total_notation_space / max_per_system
        
        print(f"SYSTEM_{system_index + 1}: Equal space per measure: {notation_space_per_measure}px")
        
        system_positions = []
        for i in range(measures_in_system):
            # RULE 1: Each barline positioned at unit intervals; final bar does NOT fill entire line
            barline_position = leftmost_x + (i + 1) * notation_space_per_measure
            system_positions.append(barline_position)
            
            # Debug: Verify equal spacing implementation
            measure_start = leftmost_x if i == 0 else system_positions[i-1]
            measure_notation_space = barline_position - measure_start
            print(f"SYSTEM_{system_index + 1}: Measure {i+1} barline at {barline_position:.1f}px - notation space: {measure_notation_space:.1f}px")
        
        # Tag measures that belong to this system with system_index if already created
        try:
            if hasattr(self.document, 'measures') and isinstance(self.document.measures, dict):
                ordered = sorted([k for k in self.document.measures.keys() if isinstance(k, int)])
                max_per_system = max(1, int(getattr(self, 'measures_per_system', measures_in_system)))
                start_idx = system_index * max_per_system
                end_idx = start_idx + measures_in_system
                slice_keys = ordered[start_idx:end_idx]
                for key in slice_keys:
                    m = self.document.measures.get(key)
                    if m is not None:
                        setattr(m, 'system_index', system_index)
        except Exception:
            pass
        
        return system_positions
    
    def _apply_justified_positioning(self, justified_positions: List[float]):
        """Apply justified positioning to all measures"""
        measures = self._get_current_measures()
        
        for i, measure in enumerate(measures):
            if i < len(justified_positions):
                old_end = getattr(measure, 'end_x', 0)
                measure.end_x = justified_positions[i]
                print(f"BRIDGE: Updated measure #{getattr(measure, 'measure_number', i+1)}: end_x {old_end} → {measure.end_x}")
    
    def _get_measure_start_x(self, measure: MeasureObject) -> float:
        """Get the starting x position of a measure"""
        measure_number = getattr(measure, 'measure_number', 1)
        
        if measure_number == 1:
            return self.SYSTEM_BARLINE_X
        
        # Find the previous measure's end position
        measures = self._get_current_measures()
        for i, m in enumerate(measures):
            if getattr(m, 'measure_number', 0) == measure_number and i > 0:
                return getattr(measures[i-1], 'end_x', self.SYSTEM_BARLINE_X)
        
        return self.SYSTEM_BARLINE_X
    
    def _insert_new_measure(self, new_measure: MeasureObject):
        """Insert a new measure into the document's measures collection"""
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}
        
        # Ensure measures is a dictionary for proper indexing
        if isinstance(self.document.measures, list):
            measure_dict = {}
            for measure in self.document.measures:
                if hasattr(measure, 'measure_number'):
                    measure_dict[measure.measure_number] = measure
            self.document.measures = measure_dict
        
        # Add the new measure
        new_number = getattr(new_measure, 'measure_number', 1)
        self.document.measures[new_number] = new_measure
        
        print(f"Inserted new measure #{new_number} into document")
    
    def _shuffle_measure_indices(self, start_from: int):
        """
        Shuffle measure indices: increment all measures with numbers >= start_from by 1.
        This maintains proper sequential numbering after barline insertions.
        
        This method ensures that when inserting a barline in measure X:
        - All measures with numbers >= (X+1) get incremented by 1
        - This makes room for the new measure at position (X+1)
        """
        if not hasattr(self.document, 'measures') or not self.document.measures:
            return
        
        measures = self.document.measures
        
        if isinstance(measures, dict):
            # Get measures that need to be shifted (in descending order to avoid conflicts)
            measures_to_shift = []
            for num, measure in measures.items():
                if isinstance(num, int) and num >= start_from:
                    measures_to_shift.append((num, measure))
            
            # Sort in descending order and shift (to avoid key conflicts)
            measures_to_shift.sort(key=lambda x: x[0], reverse=True)
            
            for old_num, measure in measures_to_shift:
                new_num = old_num + 1
                
                # Update measure object
                measure.measure_number = new_num
                
                # Update dictionary
                del measures[old_num]
                measures[new_num] = measure
                
                print(f"BRIDGE: Shuffled measure {old_num} → {new_num}")
    
    def _recalculate_uniform_spacing(self):
        """
        SIMPLIFIED: Recalculate all measure positions using justified grid positioning.
        This replaces the complex spacing logic with simple justified positioning.
        """
        print("\n=== RECALCULATING UNIFORM SPACING ===")
        
        measures = self._get_current_measures()
        if not measures:
            return
        
        total_measures = len(measures)
        justified_positions = self._calculate_justified_positions(total_measures)
        
        # Apply justified positioning
        self._apply_justified_positioning(justified_positions)
        
        print("BRIDGE: Uniform spacing recalculation complete")
    
    def remove_barline(self, measure_number: int) -> bool:
        """
        ATOMIC BARLINE REMOVAL: Remove a barline and recalculate positions
        Fixes duplicate measure issues by using atomic operations
        """
        print(f"\n=== ATOMIC BARLINE REMOVAL ===")
        print(f"Removing measure #{measure_number}")
        
        # Get current measures with validation
        current_measures = self._get_current_measures()
        if not current_measures:
            print("No measures to remove")
            return False
        
        # CRITICAL FIX: Validate all measures are proper MeasureObject instances
        validated_measures = []
        for measure in current_measures:
            if hasattr(measure, 'measure_number') and hasattr(measure, 'end_x'):
                validated_measures.append(measure)
            else:
                print(f"BRIDGE: WARNING - Invalid measure found during removal: {type(measure)}")
        
        if not validated_measures:
            print("BRIDGE: ERROR - No valid measures found for removal")
            return False
        
        print(f"BRIDGE: Found {len(validated_measures)} valid measures before removal")
        
        # Check if measure exists
        measure_to_remove = None
        for measure in validated_measures:
            if getattr(measure, 'measure_number', 0) == measure_number:
                measure_to_remove = measure
                break
        
        if not measure_to_remove:
            print(f"Measure #{measure_number} not found in validated measures")
            # List available measures for debugging
            available_measures = [getattr(m, 'measure_number', 'unknown') for m in validated_measures]
            print(f"Available measures: {available_measures}")
            return False
        
        print(f"BRIDGE: Found measure #{measure_number} to remove")
        
        # ATOMIC OPERATION: Create new measure collection without the target measure
        print(f"\n--- Creating New Measure Collection (without #{measure_number}) ---")
        new_measures = {}
        
        # CRITICAL FIX: Get ALL remaining measures and renumber them consecutively
        remaining_measures = [m for m in validated_measures if getattr(m, 'measure_number', 0) != measure_number]
        
        # Sort remaining measures by their original measure numbers to maintain order
        remaining_measures.sort(key=lambda m: getattr(m, 'measure_number', 0))
        
        print(f"BRIDGE: {len(remaining_measures)} measures remaining after removal")
        
        # Renumber ALL remaining measures consecutively starting from 1
        for i, measure in enumerate(remaining_measures):
            old_num = getattr(measure, 'measure_number', 1)
            new_num = i + 1  # Consecutive numbering starting from 1
            
            # CRITICAL: Update the measure object's internal number
            measure.measure_number = new_num
            new_measures[new_num] = measure
            
            print(f"  RENUMBERED measure #{old_num} → #{new_num}")
        
        print(f"RULE2: ✓ All {len(remaining_measures)} remaining measures renumbered consecutively from 1")
        
        # Recalculate justified positions for remaining measures
        total_measures = len(new_measures)
        if total_measures > 0:
            justified_positions = self._calculate_justified_positions(total_measures)
            print(f"  Justified positions for {total_measures} measures: {justified_positions}")
            
            # Apply positions to remaining measures
            for i, measure_num in enumerate(sorted(new_measures.keys())):
                if i < len(justified_positions):
                    old_end_x = getattr(new_measures[measure_num], 'end_x', 'unknown')
                    new_measures[measure_num].end_x = justified_positions[i]
                    print(f"  Measure #{measure_num}: end_x {old_end_x} → {justified_positions[i]}")
        else:
            print("  No measures remaining - document will be empty")
        
        # ATOMIC REPLACEMENT: Replace entire measures collection
        self.document.measures = new_measures
        
        print(f"\n--- ATOMIC REMOVAL COMPLETE ---")
        print(f"Document now has {len(new_measures)} measures:")
        for num in sorted(new_measures.keys()):
            measure = new_measures[num]
            measure_num = getattr(measure, 'measure_number', 'unknown')
            end_x = getattr(measure, 'end_x', 'unknown')
            barline_type = getattr(measure, 'barline_type', 'unknown')
            print(f"  Measure #{measure_num}: end_x={end_x}, type='{barline_type}'")
        
        # CRITICAL FIX: Verify final state is correct
        if new_measures:
            expected_numbers = list(range(1, len(new_measures) + 1))
            actual_numbers = sorted([getattr(m, 'measure_number', 0) for m in new_measures.values()])
            
            if actual_numbers != expected_numbers:
                print(f"BRIDGE: ERROR - Measure numbering is incorrect!")
                print(f"  Expected: {expected_numbers}")
                print(f"  Actual: {actual_numbers}")
                
                # FORCE CORRECTION: Fix any numbering issues
                corrected_measures = {}
                for i, (key, measure) in enumerate(sorted(new_measures.items())):
                    correct_num = i + 1
                    measure.measure_number = correct_num
                    corrected_measures[correct_num] = measure
                    print(f"  FORCE CORRECTED: Key {key} → Measure #{correct_num}")
                
                self.document.measures = corrected_measures
                print("BRIDGE: ✓ Forced correction of measure numbering")
            else:
                print("BRIDGE: ✓ Measure numbering is correct")
        
        # CRITICAL FIX: Force form widget to sync from document
        self._force_form_widget_sync()
        
        # Emit signals
        self.temporal_structure_changed.emit()
        self.measure_layout_changed.emit()
        
        # Mark document as modified
        if hasattr(self.document, 'set_modified'):
            self.document.set_modified(True)
        
        print("Atomic barline removal complete")
        return True
    
    def modify_barline_type(self, measure_obj: MeasureObject, new_type: str):
        """Modify the barline type of an existing measure"""
        if hasattr(measure_obj, 'barline_type'):
            old_type = measure_obj.barline_type
            measure_obj.barline_type = new_type
            
            # Update repeat properties based on type
            if new_type == "repeat_start":
                measure_obj.is_repeat_start = True
                measure_obj.is_repeat_end = False
            elif new_type == "repeat_end":
                measure_obj.is_repeat_start = False
                measure_obj.is_repeat_end = True
            elif new_type == "repeat_both":
                measure_obj.is_repeat_start = True
                measure_obj.is_repeat_end = True
            else:
                measure_obj.is_repeat_start = False
                measure_obj.is_repeat_end = False
            
            print(f"Modified measure #{getattr(measure_obj, 'measure_number', 'unknown')} barline type: {old_type} → {new_type}")
    
    # Legacy compatibility methods
    def get_temporal_measures(self) -> List[TemporalMeasure]:
        """Get all temporal measures for compatibility"""
        return []
    
    def get_measure_objects(self) -> List[MeasureObject]:
        """Get all measure objects"""
        measures = self._get_current_measures()
        return measures

    def _force_form_widget_sync(self):
        """
        CRITICAL FIX: Force form widget to sync from document after temporal bridge operations
        This ensures that the form widget shows the correct updated measure count
        """
        try:
            # Look for form widget in the application hierarchy
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                for widget in app.allWidgets():
                    if hasattr(widget, '_sync_from_document_to_form_widget'):
                        # Found a form widget - force sync from document
                        widget._sync_from_document_to_form_widget()
                        print("BRIDGE: Forced form widget to sync from document")
                        return
            
            print("BRIDGE: No form widget found to sync")
        except Exception as e:
            print(f"BRIDGE: Error forcing form widget sync: {e}")
            # Don't let sync errors break the operation

    def _force_layout_refresh(self):
        """Force refresh of layout calculations after page setup changes"""
        print(f"BRIDGE: Forcing layout refresh...")
        
        # DYNAMIC PROPORTIONAL SYSTEM: Calculate page dimensions dynamically
        page_width = self._get_dynamic_page_width()
        right_margin = self._get_dynamic_right_margin()
        
        # Calculate proportional staff end position
        old_end_x = self.END_BARLINE_X
        self.END_BARLINE_X = page_width - right_margin
        
        print(f"BRIDGE: Updated END_BARLINE_X from {old_end_x} to {self.END_BARLINE_X} (page_width={page_width} - right_margin={right_margin})")
        
        # CRITICAL FIX: Recalculate all measure positions when page size changes
        if hasattr(self.document, 'measures') and self.document.measures:
            print(f"BRIDGE: Recalculating {len(self.document.measures)} measures for new page layout (dynamic justification)")
            
            # Get all measures sorted by measure number
            sorted_measures = []
            for measure_num, measure in self.document.measures.items():
                if isinstance(measure_num, int) and hasattr(measure, 'measure_number'):
                    sorted_measures.append((measure_num, measure))
            
            sorted_measures.sort(key=lambda x: x[0])
            measures_list = [m for _, m in sorted_measures]

            # Calculate justified grid positions for all barlines using dynamic proportions
            leftmost_x = self.calculate_leftmost_note_position()
            rightmost_x = self.get_current_end_barline_x()
            total_measures = len(measures_list)
            
            if total_measures == 1:
                # Only one measure: span from leftmost to rightmost
                measures_list[0].start_x = leftmost_x
                measures_list[0].end_x = rightmost_x
                measures_list[0].width = rightmost_x - leftmost_x
                print(f"BRIDGE: Single measure justified from {leftmost_x} to {rightmost_x}")
            else:
                # Multiple measures: distribute barlines evenly using proportional spacing
                grid = [leftmost_x]
                available_width = rightmost_x - leftmost_x
                for i in range(1, total_measures):
                    grid.append(leftmost_x + i * available_width / total_measures)
                grid.append(rightmost_x)
                for i, measure in enumerate(measures_list):
                    measure.start_x = grid[i]
                    measure.end_x = grid[i+1]
                    measure.width = grid[i+1] - grid[i]
                    print(f"BRIDGE: Measure {i+1} justified from {grid[i]} to {grid[i+1]}")
            
            # Emit signals and force UI update
            self.measure_layout_changed.emit()
            self.temporal_structure_changed.emit()
            if hasattr(self.document, 'staff_view') and self.document.staff_view:
                self.document.staff_view.update()
                print(f"BRIDGE: Forced staff view update after layout refresh")
        
        # Trigger recalculation of all measure positions
        if hasattr(self, 'measure_manager') and self.measure_manager:
            self.measure_manager.recalculate_complete_layout()
            print(f"BRIDGE: Triggered measure manager layout recalculation")
        
        # CRITICAL FIX: Force staff view update to reflect layout changes
        if hasattr(self.document, 'staff_view') and self.document.staff_view:
            self.document.staff_view.update()
            print(f"BRIDGE: Forced staff view update")
        
        # Emit signals to notify other components of layout changes
        self.temporal_structure_changed.emit()
        self.measure_layout_changed.emit()
        print(f"BRIDGE: Emitted layout change signals")
    
    def _get_dynamic_page_width(self):
        """Get the current page width dynamically from the actual layout"""
        # Try multiple sources in order of preference
        page_width = 800.0  # Default fallback
        
        if self.document:
            # 1. Try to get from document's renderer (most accurate)
            if hasattr(self.document, 'renderer') and self.document.renderer:
                page_width = getattr(self.document.renderer, 'page_width', page_width)
                print(f"BRIDGE: Got page_width from renderer: {page_width}")
            # 2. Try to get from staff view's renderer
            elif (hasattr(self.document, 'staff_view') and self.document.staff_view and 
                  hasattr(self.document.staff_view, 'renderer') and self.document.staff_view.renderer):
                page_width = getattr(self.document.staff_view.renderer, 'page_width', page_width)
                print(f"BRIDGE: Got page_width from staff_view renderer: {page_width}")
            # 3. Try to get from document's layout
            elif hasattr(self.document, 'layout') and self.document.layout:
                page_width = getattr(self.document.layout, 'page_width', page_width)
                print(f"BRIDGE: Got page_width from document layout: {page_width}")
            # 4. Try to get from staff view's actual width (most dynamic)
            elif (hasattr(self.document, 'staff_view') and self.document.staff_view and 
                  hasattr(self.document.staff_view, 'width')):
                # Convert widget width to page width using zoom factor
                widget_width = self.document.staff_view.width()
                zoom_factor = getattr(self.document.staff_view, 'zoom_factor', 1.0)
                page_width = widget_width / zoom_factor
                print(f"BRIDGE: Calculated page_width from widget width: {widget_width} / {zoom_factor} = {page_width}")
        
        return float(page_width)
    
    def _get_dynamic_right_margin(self):
        """Get the current right margin dynamically from the actual layout"""
        right_margin = 50.0  # Default fallback
        
        if self.document:
            # 1. Try to get from document's renderer margins
            if hasattr(self.document, 'renderer') and self.document.renderer:
                margins = getattr(self.document.renderer, 'margins', {'right': right_margin})
                right_margin = margins.get('right', right_margin)
                print(f"BRIDGE: Got right_margin from renderer: {right_margin}")
            # 2. Try to get from document's layout
            elif hasattr(self.document, 'layout') and self.document.layout:
                right_margin = getattr(self.document.layout, 'right_margin', right_margin)
                print(f"BRIDGE: Got right_margin from document layout: {right_margin}")
        
        return float(right_margin)
    
    def get_current_end_barline_x(self):
        """Get the current END_BARLINE_X position using dynamic proportional calculation"""
        # Always calculate dynamically based on current page dimensions
        page_width = self._get_dynamic_page_width()
        right_margin = self._get_dynamic_right_margin()
        calculated_end_x = page_width - right_margin
        
        # Update if different (allows for dynamic changes)
        if abs(calculated_end_x - self.END_BARLINE_X) > 0.1:
            print(f"BRIDGE: Dynamically updating END_BARLINE_X from {self.END_BARLINE_X} to {calculated_end_x}")
            self.END_BARLINE_X = calculated_end_x
        
        return self.END_BARLINE_X

    def _calculate_staff_end_position(self):
        """Calculate the staff end position based on page width and margins"""
        # Default fallback values
        default_page_width = 800
        default_right_margin = 50
        
        # Try to get actual values from document/renderer
        page_width = default_page_width
        right_margin = default_right_margin
        
        if self.document:
            # Try to get from document's renderer
            if hasattr(self.document, 'renderer') and self.document.renderer:
                page_width = getattr(self.document.renderer, 'page_width', default_page_width)
                margins = getattr(self.document.renderer, 'margins', {'right': default_right_margin})
                right_margin = margins.get('right', default_right_margin)
            # Try to get from document's layout
            elif hasattr(self.document, 'layout') and self.document.layout:
                page_width = getattr(self.document.layout, 'page_width', default_page_width)
                right_margin = getattr(self.document.layout, 'right_margin', default_right_margin)
        
        # Calculate staff end position: page width minus right margin
        staff_end_x = page_width - right_margin
        
        print(f"BRIDGE: Calculated staff end position - page_width={page_width}, right_margin={right_margin}, staff_end={staff_end_x}")
        
        return float(staff_end_x)

    def update_staff_end_position(self):
        """Update the staff end position when page layout changes"""
        old_end_x = self.END_BARLINE_X
        self.END_BARLINE_X = self._calculate_staff_end_position()
        
        if abs(old_end_x - self.END_BARLINE_X) > 0.1:  # Only log if there's a significant change
            print(f"BRIDGE: Updated staff end position from {old_end_x} to {self.END_BARLINE_X}")

    def enter_edit_mode(self):
        """
        Enter Edit mode with optional initial batch fill based on Preferences.
        """
        print("\n=== ENTERING EDIT MODE ===")
        from PyQt6.QtCore import QSettings
        settings = QSettings("ONOTE", "Preferences")
        initial_mps = settings.value('layout/initial_mps_enabled', True, type=bool)
        print(f"Creating initial measures: initial_mps_enabled={initial_mps}")

        # Always reload layout preferences to get latest measures per system
        self._load_layout_preferences()
        
        # Initialize measures container if missing
        if not hasattr(self.document, 'measures'):
            self.document.measures = {}

        if initial_mps:
            # Clear any existing measures to start fresh
            self.document.measures = {}
            # Determine the end position for the first system and create equal-width measures
            staff_end_x = self.get_current_end_barline_x()
            mps = max(1, int(getattr(self, 'measures_per_system', 4)))
            print(f"EDIT_MODE: Initial system end at x={staff_end_x}; measures per system={mps}")
            # Calculate equal barline positions for the first system
            system_positions = self._calculate_system_justified_positions(mps, staff_end_x, 0)
            # Create measures 1..mps with equal widths across the first system
            prev_end = self.LEFTMOST_NOTE_X
            for i, end_x in enumerate(system_positions, start=1):
                measure = self._create_measure_object(
                    measure_number=i,
                    x_position=prev_end,
                    end_x=end_x,
                    barline_type='single'
                )
                try:
                    measure.system_index = 0
                except Exception:
                    pass
                self.document.measures[i] = measure
                prev_end = end_x
                print(f"EDIT_MODE: Created initial measure #{i}: start={measure.x_position}, end={measure.end_x}")
        else:
            # Only one compact measure with a final barline visually at its right edge
            self.document.measures = {}
            single_measure = self._create_measure_object(
                measure_number=1,
                x_position=self.LEFTMOST_NOTE_X,
                end_x=self.LEFTMOST_NOTE_X + max(80.0, self.minimum_practical_space / 2),
                barline_type='single'
            )
            # Mark as compact to avoid page-wide justification
            try:
                setattr(single_measure, 'keep_compact', True)
                setattr(single_measure, 'compact_end_x', float(getattr(single_measure, 'end_x', self.LEFTMOST_NOTE_X + 120.0)))
            except Exception:
                pass
            # Mark barline type as final for edit mode visual behavior
            try:
                single_measure.barline_type = 'final'
            except Exception:
                pass
            self.document.measures[1] = single_measure
            print(f"EDIT_MODE: Created single compact initial measure: start={single_measure.x_position}, end={single_measure.end_x}")
            # Do not run layout refresh that would justify the single measure to the full width
            return
        
        # CRITICAL FIX: Force layout refresh to enable dynamic resizing
        print("EDIT_MODE: Forcing layout refresh to enable dynamic resizing")
        self._force_layout_refresh()
        
        # Force form widget sync to show the new measure
        self._force_form_widget_sync()
        
        # Emit signals to update the UI
        self.temporal_structure_changed.emit()
        self.measure_layout_changed.emit()
        
        print("EDIT_MODE: Initial batch creation complete")
        print("EDIT_MODE: Ready for user to create additional measures by clicking on staff")
        print("EDIT_MODE: Dynamic resizing is now enabled")
        print("=== EDIT MODE ENTRY COMPLETE ===\n")

    def update_barline_0_visibility(self):
        """
        Update the visibility of barline 0 based on the number of staff systems.
        """
        if self.document and hasattr(self.document, 'staff_systems'):
            staff_systems = self.document.staff_systems
            if len(staff_systems) == 1 and len(staff_systems[0].staves) == 1:
                print("Single-staff system detected - hiding barline 0")
                self.set_barline_0_visibility(False)
            else:
                print("Multiple staff systems detected - showing barline 0")
                self.set_barline_0_visibility(True)


# Helper functions for integration
def integrate_bridge_with_staff_view(staff_view, bridge: BarlineTemporalBridge):
    """Integrate the bridge with an existing staff view"""
    # Connect bridge signals to staff view updates
    bridge.temporal_structure_changed.connect(staff_view.update)
    bridge.measure_layout_changed.connect(staff_view.update)
    
    # Store bridge reference in staff view
    staff_view.temporal_bridge = bridge
    
    print("BRIDGE: Integrated with staff view using refined model")


def integrate_bridge_with_form_widget(form_widget, bridge: BarlineTemporalBridge):
    """Integrate the bridge with form widget for rhythm input"""
    # Store bridge reference
    form_widget.temporal_bridge = bridge
    
    print("BRIDGE: Integrated with form widget") 