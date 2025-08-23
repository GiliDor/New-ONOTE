"""
Comprehensive measure number display system for ONOTE.
Handles frequency, positioning, and rendering of measure numbers.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QPainter, QFont, QFontMetrics
from PyQt6.QtCore import Qt
from src.core.settings_manager import SettingsManager


class MeasureNumberFrequency(Enum):
    """Enumeration for measure number display frequencies"""
    NONE = "None"
    EVERY_SYSTEM = "Every System"
    EVERY_MEASURE = "Every Measure"
    EVERY_2_MEASURES = "Every 2 Measures"
    EVERY_5_MEASURES = "Every 5 Measures"
    EVERY_10_MEASURES = "Every 10 Measures"
    CUSTOM_INTERVAL = "Custom Interval"


class MeasureNumberPosition(Enum):
    """Enumeration for horizontal position of measure numbers"""
    BEGINNING = "Beginning"
    CENTER = "Center" 
    END = "End"


class MeasureNumberVerticalPosition(Enum):
    """Enumeration for vertical position of measure numbers"""
    ABOVE_STAFF = "Above Staff"
    ABOVE_SYSTEM = "Above System"
    BELOW_STAFF = "Below Staff"
    BELOW_SYSTEM = "Below System"


@dataclass
class MeasureNumberSettings:
    """Settings for measure number display"""
    frequency: MeasureNumberFrequency = MeasureNumberFrequency.EVERY_MEASURE
    custom_interval: int = 5
    position: MeasureNumberPosition = MeasureNumberPosition.CENTER
    vertical_position: MeasureNumberVerticalPosition = MeasureNumberVerticalPosition.ABOVE_SYSTEM
    vertical_offset: int = -20  # NEW: Fine vertical adjustment in pixels (negative = above)
    horizontal_offset: int = 0  # NEW: Fine horizontal adjustment in pixels
    font_size: int = 10
    font_color: str = "#000000"  # CRITICAL FIX: Add color support
    enabled: bool = True
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary for serialization"""
        return {
            'frequency': self.frequency.value,
            'custom_interval': self.custom_interval,
            'position': self.position.value,
            'vertical_position': self.vertical_position.value,
            'vertical_offset': self.vertical_offset,
            'horizontal_offset': self.horizontal_offset,
            'font_size': self.font_size,
            'font_color': self.font_color,
            'enabled': self.enabled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeasureNumberSettings':
        """Create settings from dictionary"""
        return cls(
            frequency=MeasureNumberFrequency(data.get('frequency', MeasureNumberFrequency.EVERY_SYSTEM.value)),
            custom_interval=data.get('custom_interval', 5),
            position=MeasureNumberPosition(data.get('position', MeasureNumberPosition.CENTER.value)),
            vertical_position=MeasureNumberVerticalPosition(data.get('vertical_position', MeasureNumberVerticalPosition.ABOVE_SYSTEM.value)),
            vertical_offset=data.get('vertical_offset', -20),
            horizontal_offset=data.get('horizontal_offset', 0),
            font_size=data.get('font_size', 10),
            font_color=data.get('font_color', "#000000"),
            enabled=data.get('enabled', True)
        )


class MeasureNumberRenderer:
    """Handles rendering of measure numbers"""
    
    def __init__(self, settings: MeasureNumberSettings):
        self.settings = settings
        
    def should_display_number(self, measure_number: int, system_start_measure: int) -> bool:
        """Determine if a measure number should be displayed"""
        if not self.settings.enabled or self.settings.frequency == MeasureNumberFrequency.NONE:
            print(f"MEASURE_NUMBERS: Should display measure {measure_number}: False (disabled or none)")
            return False
            
        print(f"MEASURE_NUMBERS: Checking measure {measure_number}, system_start={system_start_measure}, frequency={self.settings.frequency.value}")
        
        if self.settings.frequency == MeasureNumberFrequency.EVERY_SYSTEM:
            # FIXED: Show the first measure of each system
            # For single-system scores, this means only measure 1 is shown
            # But we need to properly identify the first measure of each system
            result = measure_number == system_start_measure
            print(f"MEASURE_NUMBERS: Every System mode, measure {measure_number} == system_start {system_start_measure}: {result}")
            return result
        elif self.settings.frequency == MeasureNumberFrequency.EVERY_MEASURE:
            # FIXED: Show every measure number - this should always return True
            print(f"MEASURE_NUMBERS: Every Measure mode, measure {measure_number}: True")
            return True
        elif self.settings.frequency == MeasureNumberFrequency.EVERY_2_MEASURES:
            # Show measures 1, 3, 5, 7, etc.
            result = measure_number % 2 == 1
            print(f"MEASURE_NUMBERS: Every 2 Measures mode, measure {measure_number} % 2 == 1: {result}")
            return result
        elif self.settings.frequency == MeasureNumberFrequency.EVERY_5_MEASURES:
            # Show measures 1, 6, 11, 16, etc. (every 5th starting from 1)
            result = (measure_number - 1) % 5 == 0
            print(f"MEASURE_NUMBERS: Every 5 Measures mode, (measure {measure_number} - 1) % 5 == 0: {result}")
            return result
        elif self.settings.frequency == MeasureNumberFrequency.EVERY_10_MEASURES:
            # Show measures 1, 11, 21, 31, etc. (every 10th starting from 1)
            result = (measure_number - 1) % 10 == 0
            print(f"MEASURE_NUMBERS: Every 10 Measures mode, (measure {measure_number} - 1) % 10 == 0: {result}")
            return result
        elif self.settings.frequency == MeasureNumberFrequency.CUSTOM_INTERVAL:
            # Show measures based on custom interval starting from 1
            result = (measure_number - 1) % self.settings.custom_interval == 0
            print(f"MEASURE_NUMBERS: Custom Interval mode, (measure {measure_number} - 1) % {self.settings.custom_interval} == 0: {result}")
            return result
            
        return False
    
    def calculate_position(self, measure_x: float, measure_width: float, staff_y: float, measure_number: int = 1) -> Tuple[float, float]:
        """Calculate the position for a measure number"""
        # CRITICAL FIX: The measure_x parameter represents the START of the measure (where the measure begins)
        # The position setting determines where within the measure the number appears
        
        # Calculate horizontal position based on position setting
        if self.settings.position == MeasureNumberPosition.BEGINNING:
            # Position at the beginning of the measure (after barline)
            # For measure 1, position relative to first note position
            if measure_number == 1:
                x = measure_x + self.settings.horizontal_offset
                print(f"MEASURE_NUMBERS: Measure {measure_number} positioned relative to first note at x={measure_x}, offset: {self.settings.horizontal_offset}, final_x: {x}")
            else:
                # For other measures, position after the barline
                x = measure_x + self.settings.horizontal_offset
                print(f"MEASURE_NUMBERS: Measure {measure_number} positioned after barline at x={measure_x}, final_x: {x}")
        elif self.settings.position == MeasureNumberPosition.CENTER:
            # CRITICAL FIX: Position at the center of the measure's effective notation area
            # measure_x is the start of the measure, measure_width is the width of the measure
            # Center = start + (width / 2)
            center_x = measure_x + (measure_width / 2)
            x = center_x + self.settings.horizontal_offset
            print(f"MEASURE_NUMBERS: Measure {measure_number} positioned at CENTER: x={measure_x} + width/2={measure_width/2} + offset={self.settings.horizontal_offset} = {x}")
        elif self.settings.position == MeasureNumberPosition.END:
            # CRITICAL FIX: Position at the end of the measure (before the next barline)
            # For END position, we want to position just before the measure ends
            # Use 90% of the measure width to ensure it's visible
            end_x = measure_x + (measure_width * 0.9)
            x = end_x + self.settings.horizontal_offset
            print(f"MEASURE_NUMBERS: Measure {measure_number} positioned at END: x={measure_x} + width*0.9={measure_width*0.9} + offset={self.settings.horizontal_offset} = {x}")
        else:
            # Fallback to beginning
            x = measure_x + self.settings.horizontal_offset
            print(f"MEASURE_NUMBERS: Measure {measure_number} positioned at FALLBACK BEGINNING: x={x}")
            
        # CRITICAL FIX: Vertical position - ensure measure numbers are always visible
        if self.settings.vertical_position == MeasureNumberVerticalPosition.ABOVE_STAFF:
            y = staff_y - 15  # Closer to staff for visibility
        elif self.settings.vertical_position == MeasureNumberVerticalPosition.ABOVE_SYSTEM:
            y = staff_y - 30  # Higher above system, more visible
        elif self.settings.vertical_position == MeasureNumberVerticalPosition.BELOW_STAFF:
            y = staff_y + 45  # Below staff line
        else:  # BELOW_SYSTEM
            y = staff_y + 65  # Below entire system
            
        # Apply vertical offset (negative values move up, positive move down)
        y += self.settings.vertical_offset
        
        # CRITICAL FIX: Only ensure measure numbers are never positioned above y=30 (visible area)
        # REMOVED the y > 400 limit that was causing measure numbers to overlap on lower staves
        if y < 30:
            print(f"MEASURE_NUMBERS: Adjusting y position from {y} to 30 for visibility")
            y = 30  # Minimum visible position
            
        print(f"MEASURE_NUMBERS: Calculated position ({x}, {y}) for measure {measure_number} at x={measure_x}, width={measure_width}, staff_y={staff_y} with position={self.settings.position.value}, offsets H:{self.settings.horizontal_offset}, V:{self.settings.vertical_offset}")
        return x, y
    
    def render_measure_numbers_for_system(self, painter: QPainter, measures: List[Tuple[int, float, float]], 
                                        staff_y: float, system_start_measure: int):
        """Render measure numbers for a system"""
        if not measures:
            return
            
        print(f"MEASURE_NUMBERS: render_measure_numbers_for_system called with {len(measures)} measures")
        print(f"MEASURE_NUMBERS: Settings - frequency: {self.settings.frequency.value}, position: {self.settings.position.value}")
        print(f"MEASURE_NUMBERS: System start measure: {system_start_measure}, total measures: {len(measures)}")
        
        # Set up font and color for visibility
        font = QFont("Arial", self.settings.font_size, QFont.Weight.Bold)
        painter.setFont(font)
        # CRITICAL FIX: Use color from settings with document precedence
        from PyQt6.QtGui import QColor
        
        # CRITICAL FIX: Save the current pen state before changing color
        original_pen = painter.pen()
        measure_color = QColor(self.settings.font_color)
        painter.setPen(measure_color)
        print(f"MEASURE_NUMBERS: Using color {self.settings.font_color} for measure numbers")
        
        for measure_number, measure_x, measure_width in measures:
            print(f"MEASURE_NUMBERS: Processing measure {measure_number}")
            
            if self.should_display_number(measure_number, system_start_measure):
                print(f"MEASURE_NUMBERS: Should display measure {measure_number}: True")
                x, y = self.calculate_position(measure_x, measure_width, staff_y, measure_number)
                
                # Draw the measure number
                text = str(measure_number)
                metrics = QFontMetrics(font)
                text_width = metrics.horizontalAdvance(text)
                
                # Center the text horizontally if needed
                if self.settings.position == MeasureNumberPosition.CENTER:
                    x -= text_width / 2
                elif self.settings.position == MeasureNumberPosition.END:
                    x -= text_width
                    
                print(f"MEASURE_NUMBERS: Rendering measure {measure_number} at position ({x}, {y})")
                painter.drawText(int(x), int(y), text)
            else:
                print(f"MEASURE_NUMBERS: Should display measure {measure_number}: False")
        
        # CRITICAL FIX: Restore the original pen state after drawing measure numbers
        painter.setPen(original_pen)


class MeasureNumberManager:
    """Manages measure number settings and rendering for a document"""
    
    def __init__(self, document=None):
        self.document = document
        self.settings = MeasureNumberSettings()
        self.renderer = MeasureNumberRenderer(self.settings)
        
        # Load settings with proper precedence
        self._load_settings(document)
        
    def _load_settings(self, document=None):
        """Load measure number settings with proper precedence using notation/ prefix"""
        print(f"MEASURE_NUMBERS: Loading settings with document: {document is not None}")
        
        # CRITICAL FIX: Always use QSettings directly to ensure we get the latest values
        # This fixes the issue where measure number settings are not being applied properly
        def get_setting_with_precedence(key, default_value):
            """Get setting with document precedence over preferences"""
            # CRITICAL FIX: Check document settings first, then QSettings
            if document and hasattr(document, 'settings') and document.settings and key in document.settings:
                value = document.settings[key]
                print(f"MEASURE_NUMBERS: Using document setting for {key} = {value}")
                return value
            
            # Fall back to QSettings
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            value = settings.value(key, default_value)
            print(f"MEASURE_NUMBERS: Using QSettings for {key} = {value} (default: {default_value})")
            return value
        
        # Load all settings using notation/ prefix (same as Full Score Options dialog)
        
        # Enable/disable measure numbers
        self.settings.enabled = get_setting_with_precedence("notation/show_measure_numbers", True) in [True, 'true', 'True', '1', 1]
        
        # Frequency setting
        frequency_str = get_setting_with_precedence("notation/measure_numbers_frequency", "Every Measure")
        try:
            self.settings.frequency = MeasureNumberFrequency(frequency_str)
            print(f"MEASURE_NUMBERS: Set frequency to: {self.settings.frequency.value}")
        except ValueError:
            print(f"MEASURE_NUMBERS: Invalid frequency '{frequency_str}', using Every Measure")
            self.settings.frequency = MeasureNumberFrequency.EVERY_MEASURE
        
        # Custom interval
        self.settings.custom_interval = int(get_setting_with_precedence("notation/measure_numbers_custom_interval", 5))
        
        # Position setting
        position_str = get_setting_with_precedence("notation/measure_numbers_position", "Center")
        try:
            self.settings.position = MeasureNumberPosition(position_str)
            print(f"MEASURE_NUMBERS: Set position to: {self.settings.position.value}")
        except ValueError:
            print(f"MEASURE_NUMBERS: Invalid position '{position_str}', using Center")
            self.settings.position = MeasureNumberPosition.CENTER
        
        # Vertical position setting
        vertical_str = get_setting_with_precedence("notation/measure_numbers_vertical", "Above System")
        try:
            self.settings.vertical_position = MeasureNumberVerticalPosition(vertical_str)
            print(f"MEASURE_NUMBERS: Set vertical position to: {self.settings.vertical_position.value}")
        except ValueError:
            print(f"MEASURE_NUMBERS: Invalid vertical position '{vertical_str}', using Above System")
            self.settings.vertical_position = MeasureNumberVerticalPosition.ABOVE_SYSTEM
        
        # Font size
        self.settings.font_size = int(get_setting_with_precedence("notation/measure_numbers_font_size", 10))
        
        # Offset settings
        self.settings.vertical_offset = int(get_setting_with_precedence("notation/measure_numbers_vertical_offset", -20))
        self.settings.horizontal_offset = int(get_setting_with_precedence("notation/measure_numbers_horizontal_offset", 0))
        
        # CRITICAL FIX: Color setting
        self.settings.font_color = get_setting_with_precedence("notation/measure_numbers_font_color", "#000000")
        
        print(f"MEASURE_NUMBERS: Final settings - enabled: {self.settings.enabled}, freq: {self.settings.frequency.value}, pos: {self.settings.position.value}, v_pos: {self.settings.vertical_position.value}, font_size: {self.settings.font_size}, color: {self.settings.font_color}, h_offset: {self.settings.horizontal_offset}, v_offset: {self.settings.vertical_offset}")
        
        # CRITICAL FIX: Update the renderer with the new settings
        self.renderer = MeasureNumberRenderer(self.settings)
        
    def load_settings_from_preferences(self):
        """DEPRECATED: Use load_settings_with_precedence instead"""
        print("MEASURE_NUMBERS: Warning - using deprecated load_settings_from_preferences")
        self._load_settings()
        
    def update_settings(self, new_settings: MeasureNumberSettings):
        """Update measure number settings and refresh the renderer"""
        self.settings = new_settings
        self.renderer = MeasureNumberRenderer(self.settings)
        print(f"MEASURE_NUMBERS: Updated settings: {self.settings}")
        
        # Save to document settings if document is available
        if self.document and hasattr(self.document, 'settings'):
            # CRITICAL FIX: Use notation/ prefix to match Full Score Options dialog
            self.document.settings.update({
                'notation/measure_numbers_frequency': self.settings.frequency.value,
                'notation/measure_numbers_position': self.settings.position.value,
                'notation/measure_numbers_vertical': self.settings.vertical_position.value,
                'notation/measure_numbers_custom_interval': self.settings.custom_interval,
                'notation/measure_numbers_font_size': self.settings.font_size,
                'notation/measure_numbers_vertical_offset': self.settings.vertical_offset,
                'notation/measure_numbers_horizontal_offset': self.settings.horizontal_offset,
                'notation/measure_numbers_font_color': self.settings.font_color,
                'notation/show_measure_numbers': self.settings.enabled
            })
            print("MEASURE_NUMBERS: Saved updated settings to document")
        
    def get_settings(self) -> MeasureNumberSettings:
        """Get current settings"""
        return self.settings
        
    def refresh_settings(self):
        """Force refresh settings from QSettings - used when settings change"""
        print("MEASURE_NUMBERS: Force refreshing settings from QSettings")
        self._load_settings(self.document)
        print(f"MEASURE_NUMBERS: Refreshed settings - enabled: {self.settings.enabled}, freq: {self.settings.frequency.value}, pos: {self.settings.position.value}, v_pos: {self.settings.vertical_position.value}, font_size: {self.settings.font_size}, color: {self.settings.font_color}, h_offset: {self.settings.horizontal_offset}, v_offset: {self.settings.vertical_offset}")
        
    def render_for_staff(self, painter: QPainter, staff_name: str, measures: List, staff_y: float, system_index: int = 0):
        """Render measure numbers for a specific staff using LIVE document coordinates"""
        # RESTRUCTURE: Skip rendering if no measures exist (empty document)
        if not measures:
            print(f"MEASURE_NUMBERS: No measures in document - skipping (empty document)")
            return
            
        print(f"MEASURE_NUMBERS: Called for staff {staff_name}, system {system_index}")
        print(f"MEASURE_NUMBERS: Found {len(measures)} measures")
        print(f"MEASURE_NUMBERS: Current settings - frequency: {self.settings.frequency.value}")
        
        # CRITICAL FIX: Find the actual top staff position instead of using passed staff_y
        # This ensures measure numbers are positioned relative to the actual top staff in the score
        if staff_y is None:
            # Use None to indicate we should find the actual top staff position
            actual_top_staff_y = self._find_actual_top_staff_position()
            print(f"MEASURE_NUMBERS: Using actual top staff position: {actual_top_staff_y} (staff_y was None)")
        else:
            # Use the passed staff_y parameter (for backward compatibility)
            actual_top_staff_y = staff_y
            print(f"MEASURE_NUMBERS: Using passed staff_y position: {actual_top_staff_y}")
        
        # Convert measures to format expected by renderer using LIVE DOCUMENT COORDINATES
        measure_data = []
        system_start_measure = 1
        
        # CRITICAL FIX: Use LIVE document coordinates from temporal bridge instead of cached calculations
        if measures:
            print(f"MEASURE_NUMBERS: System {system_index} has {len(measures)} measures (indices {0}-{len(measures)-1})")
            
            # Sort measures by measure number to ensure proper order
            sorted_measures = sorted(measures, key=lambda m: getattr(m, 'measure_number', 999))
            
            for i, measure in enumerate(sorted_measures):
                measure_number = getattr(measure, 'measure_number', i + 1)
                
                # FIXED: Use the LIVE coordinates from the document's temporal bridge
                measure_end_x = getattr(measure, 'end_x', 0)
                
                # CRITICAL FIX: Calculate measure start position from LIVE document state
                # This ensures measure numbers respond immediately to layout changes
                if measure_number == 1:
                    # First measure starts at the system barline (barline 0), not the notation space
                    # The system barline is at x=100.0 (from the temporal bridge constants)
                    measure_start_x = 100.0  # System barline position (barline 0)
                else:
                    # Find the previous measure's end position from LIVE document
                    prev_measure = None
                    for m in sorted_measures:
                        if getattr(m, 'measure_number', 0) == measure_number - 1:
                            prev_measure = m
                            break
                    
                    if prev_measure:
                        # CRITICAL FIX: Use previous measure's LIVE end_x as this measure's start_x
                        measure_start_x = getattr(prev_measure, 'end_x', 100.0)
                    else:
                        # Fallback for malformed document state
                        measure_start_x = 100.0
                
                # CRITICAL FIX: Calculate LIVE notation width based on current document positions
                measure_width = measure_end_x - measure_start_x
                if measure_width <= 0:
                    # If measure width is invalid, use a reasonable default based on measure number
                    measure_width = max(180.0, 200.0 + (measure_number * 10))  # Progressive width
                    print(f"MEASURE_NUMBERS: Invalid width for measure {measure_number}, using default: {measure_width}")
                else:
                    print(f"MEASURE_NUMBERS: Valid width for measure {measure_number}: {measure_width}")
                
                print(f"MEASURE_NUMBERS: Measure {measure_number} at x={measure_start_x} (start={measure_start_x}, end={measure_end_x}, width={measure_width})")
                
                # CRITICAL FIX: Use LIVE start position for measure data (renderer will calculate final position)
                # This ensures measure numbers appear in the correct measure boundaries and respond immediately
                measure_data.append((measure_number, measure_start_x, measure_width))
        
        if measure_data:
            print(f"MEASURE_NUMBERS: Calling renderer with {len(measure_data)} measures - LIVE coordinates")
            self.renderer.render_measure_numbers_for_system(
                painter, measure_data, actual_top_staff_y, system_start_measure
            )
    
    def _find_actual_top_staff_position(self) -> float:
        """Find the actual top staff position in the score"""
        if not self.document:
            return 40.0  # Fallback default
        
        # Get all staves from the document layout
        all_staves = []
        
        # Add ungrouped staves
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'ungrouped_staves'):
            for staff in self.document.layout.ungrouped_staves:
                if hasattr(staff, 'y_position'):
                    all_staves.append(staff.y_position)
        
        # Add staves from sections
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                if hasattr(section, 'staves'):
                    for staff in section.staves:
                        if hasattr(staff, 'y_position'):
                            all_staves.append(staff.y_position)
        
        # Find the minimum y position (topmost staff)
        if all_staves:
            top_staff_y = min(all_staves)
            print(f"MEASURE_NUMBERS: Found {len(all_staves)} staves, top staff at y={top_staff_y}")
            return top_staff_y
        else:
            print(f"MEASURE_NUMBERS: No staves found, using default y=40")
            return 40.0  # Fallback default 