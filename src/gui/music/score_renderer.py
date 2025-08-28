"""
Score renderer module for drawing musical notation elements.
This module contains classes for rendering music notation elements
in a standardized way based on established music engraving practices.
"""

from PyQt6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QFont,
    QFontMetrics,
    QPainterPath,
    QTransform,
    QPalette,
    QFontInfo,
    QBrush,
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QRect, QLineF
import copy
import math

from .constants import CLEF_WIDTH, CLEF_HEIGHT, SYMBOLS

from .notation_constants import (
    STAFF_LINE_COUNT,
    STAFF_LINE_SPACING,
    STAFF_LINE_THICKNESS,
    STAFF_HEIGHT,
    DEFAULT_PAGE_MARGINS,
    CLEF_POSITIONS,
    BARLINE_CONSTANTS,
    TIME_SIGNATURE_CONSTANTS,
    KEY_SIGNATURE_CONSTANTS,
    SYMBOL_MAP,
    FONT_SIZES,
    MUSIC_FONTS,
    BRACE_CONSTANTS,
    BRACKET_CONSTANTS,
    CLEF_CONSTANTS,
)
from .staff_types import StaffBase, SingleStaff, GrandStaff, SectionGroup, ScoreLayout


class ScoreRenderer:
    """
    Handles rendering of score elements according to standardized practices.

    This class is responsible for drawing all musical notation elements
    including staves, clefs, key signatures, time signatures, etc.
    """

    def __init__(self, document=None):
        """Initialize the renderer with an optional document."""
        # Explicitly import constants at initialization time to ensure freshest values
        from .notation_constants import (
            STAFF_LINE_COUNT,
            STAFF_LINE_SPACING,
            STAFF_LINE_THICKNESS,
            STAFF_HEIGHT,
            DEFAULT_PAGE_MARGINS,
            CLEF_POSITIONS,
            BARLINE_CONSTANTS,
            TIME_SIGNATURE_CONSTANTS,
            KEY_SIGNATURE_CONSTANTS,
            SYMBOL_MAP,
            FONT_SIZES,
            MUSIC_FONTS,
            BRACE_CONSTANTS,
            BRACKET_CONSTANTS,
            CLEF_CONSTANTS,
        )

        # CRITICAL FIX: Use the same constants as staff_view.py for consistency
        # Staff lines are actually drawn with 8px spacing, not 10px
        self.STAFF_LINE_COUNT = 5
        self.STAFF_LINE_SPACING = 8  # Match staff_view.py
        self.STAFF_LINE_THICKNESS = STAFF_LINE_THICKNESS
        self.STAFF_HEIGHT = 32  # (5-1) * 8 = 32, match staff_view.py
        self.DEFAULT_PAGE_MARGINS = DEFAULT_PAGE_MARGINS.copy()
        self.CLEF_POSITIONS = self._copy_nested_dict(CLEF_POSITIONS)
        self.BARLINE_CONSTANTS = self._copy_nested_dict(BARLINE_CONSTANTS)
        self.TIME_SIGNATURE_CONSTANTS = TIME_SIGNATURE_CONSTANTS.copy()
        self.KEY_SIGNATURE_CONSTANTS = KEY_SIGNATURE_CONSTANTS.copy()
        self.SYMBOL_MAP = SYMBOL_MAP.copy()

        # Ensure brace symbol is correctly defined
        if "brace" not in self.SYMBOL_MAP or self.SYMBOL_MAP["brace"] != "\uE000":
            self.SYMBOL_MAP["brace"] = "\uE000"  # SMuFL code point for brace
            
        # Ensure percussion clef symbol is correctly defined
        if "percussionClef" not in self.SYMBOL_MAP:
            self.SYMBOL_MAP["percussionClef"] = "\uE069"  # SMuFL code point for percussion clef

        self.FONT_SIZES = FONT_SIZES.copy()
        self.MUSIC_FONTS = MUSIC_FONTS.copy()

        # Ensure we have a fallback for bravura
        if "bravura" not in self.MUSIC_FONTS:
            self.MUSIC_FONTS["bravura"] = "Bravura"

        self.BRACE_CONSTANTS = BRACE_CONSTANTS.copy()
        self.BRACKET_CONSTANTS = BRACKET_CONSTANTS.copy()
        self.CLEF_CONSTANTS = self._copy_nested_dict(CLEF_CONSTANTS)

        self.document = document
        
        # A4 page dimensions: 210 x 297 mm
        A4_WIDTH_MM = 210
        A4_HEIGHT_MM = 297
        MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI
        
        # Set default A4 page dimensions in pixels
        self.page_width = int(A4_WIDTH_MM * MM_TO_PIXELS)   # ≈ 794 pixels
        self.page_height = int(A4_HEIGHT_MM * MM_TO_PIXELS)  # ≈ 1123 pixels
        
        # A4 standard margins: 25mm left/right, 20mm top/bottom
        A4_MARGIN_LEFT_MM = 25
        A4_MARGIN_RIGHT_MM = 25
        A4_MARGIN_TOP_MM = 20
        A4_MARGIN_BOTTOM_MM = 20
        
        # Set A4 margins in pixels
        self.margins = {
            'left': int(A4_MARGIN_LEFT_MM * MM_TO_PIXELS),    # ≈ 95 pixels
            'right': int(A4_MARGIN_RIGHT_MM * MM_TO_PIXELS),  # ≈ 95 pixels
            'top': int(A4_MARGIN_TOP_MM * MM_TO_PIXELS),      # ≈ 76 pixels
            'bottom': int(A4_MARGIN_BOTTOM_MM * MM_TO_PIXELS) # ≈ 76 pixels
        }
        
        # View mode settings
        self.view_mode = "page_down"  # Default view mode
        self.page_across_mode = False
        self.page_down_mode = True
        self.continuous_mode = False
        
        self._setup_fonts()
        
        # Initialize system-specific staff offsets
        self.first_system_offset = 0
        self.continuation_system_offset = 0
        # Staff spacing for systems in multi-system rendering
        self.staff_spacing = 120  # Default vertical spacing between systems
        
        # Initialize configurable notation settings with defaults
        # These can be overridden by preferences
        self.staff_name_font_size = 10
        self.staff_name_vertical_offset = -8
        self.staff_name_horizontal_offset = -50
        self.section_name_font_size = 12
        self.section_name_vertical_offset = -25
        self.section_name_horizontal_offset = -60
        self.clef_font_size = 32
        self.clef_vertical_offset = 0
        self.clef_horizontal_offset = 0
        self.time_sig_font_size = 24
        self.time_sig_vertical_offset = 0
        self.time_sig_horizontal_offset = 40
        self.time_sig_spacing = 18
        self.key_sig_font_size = 14
        self.key_sig_vertical_offset = 0
        self.key_sig_horizontal_offset = 75
        self.key_sig_accidental_spacing = 12
        self.directions_font_size = 11
        self.directions_vertical_offset = 30
        
        # Load settings from preferences
        self.load_notation_settings()
        
        # Initialize measure number manager
        self.measure_number_manager = None
        self._initialize_measure_number_manager()

        # Add or update these attributes in __init__
        self.staff_name_font_color = '#000000'
        self.section_name_font_color = '#000000'
        self.clef_font_color = '#000000'
        self.time_sig_font_color = '#000000'
        self.key_sig_font_color = '#000000'
        self.staff_name_font_size = 10
        self.staff_name_vertical = 0
        self.staff_name_horizontal = 0
        self.section_name_font_size = 10
        self.section_name_vertical = 0
        self.section_name_horizontal = 0
        self.clef_font_size = 10
        self.clef_vertical = 0
        self.clef_horizontal = 0
        self.time_sig_font_size = 10
        self.time_sig_vertical = 0
        self.time_sig_horizontal = 0
        self.time_sig_spacing = 8
        self.key_sig_font_size = 10
        self.key_sig_vertical = 0
        self.key_sig_horizontal = 0
        self.key_sig_accidental_spacing = 8
        self.directions_font_size = 10
        self.directions_vertical = 0
        self.directions_horizontal = 0

    def _copy_nested_dict(self, d):
        """Create a deep copy of a nested dictionary"""
        if not isinstance(d, dict):
            return d
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._copy_nested_dict(v)
            else:
                result[k] = v
        return result

    def _setup_fonts(self):
        """Set up the required fonts for music notation."""
        self.music_font = QFont(self.MUSIC_FONTS["default"])
        self.text_font = QFont(self.MUSIC_FONTS["text"])
        
        # CRITICAL FIX: Initialize Bravura font for SMuFL glyphs (end bars, etc.)
        from PyQt6.QtGui import QFontDatabase
        font_id = QFontDatabase.addApplicationFont("fonts/Bravura.otf")
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.bravura_font = QFont(font_families[0])
                print(f"RENDERER: Successfully loaded Bravura font: {font_families[0]}")
            else:
                print("RENDERER: Warning - Bravura font loaded but no families found")
                self.bravura_font = None
        else:
            print("RENDERER: Warning - Could not load Bravura font from fonts/Bravura.otf")
            self.bravura_font = None

    def set_page_across_mode(self, enabled: bool):
        """Set page across view mode"""
        self.page_across_mode = enabled
        self.page_down_mode = not enabled and not self.continuous_mode
        self.view_mode = "page_across" if enabled else ("continuous" if self.continuous_mode else "page_down")
        print(f"RENDERER: Set page across mode to {enabled}, view mode: {self.view_mode}")
        
    def set_page_down_mode(self, enabled: bool):
        """Set page down view mode"""
        self.page_down_mode = enabled
        self.page_across_mode = not enabled and not self.continuous_mode  
        self.view_mode = "page_down" if enabled else ("continuous" if self.continuous_mode else "page_across")
        print(f"RENDERER: Set page down mode to {enabled}, view mode: {self.view_mode}")
        
    def set_continuous_mode(self, enabled: bool):
        """Set continuous view mode"""
        self.continuous_mode = enabled
        self.page_across_mode = not enabled
        self.page_down_mode = not enabled
        self.view_mode = "continuous" if enabled else "page_down"
        print(f"RENDERER: Set continuous mode to {enabled}, view mode: {self.view_mode}")
        
    def get_view_mode(self) -> str:
        """Get the current view mode"""
        return self.view_mode

    def set_document(self, document):
        """Set the document to be rendered."""
        self.document = document
        
        # CRITICAL FIX: Refresh measure number manager when document changes
        # This ensures saved scores get the correct measure number settings
        if hasattr(self, 'measure_number_manager') and self.measure_number_manager:
            self.measure_number_manager.document = document
            self.measure_number_manager.refresh_settings()
            print(f"RENDERER: Refreshed measure number settings for new document")

        # Apply document page layout to renderer immediately
        try:
            if hasattr(self.document, 'layout') and self.document.layout:
                layout = self.document.layout
                # Update page size if present
                if hasattr(layout, 'page_width') and hasattr(layout, 'page_height'):
                    self.set_page_size(int(layout.page_width), int(layout.page_height))
                # Update margins
                margins = {}
                if hasattr(layout, 'left_margin'): margins['left'] = int(layout.left_margin)
                if hasattr(layout, 'right_margin'): margins['right'] = int(layout.right_margin)
                if hasattr(layout, 'top_margin'): margins['top'] = int(layout.top_margin)
                if hasattr(layout, 'bottom_margin'): margins['bottom'] = int(layout.bottom_margin)
                if margins:
                    self.set_margins(margins)
                print(f"RENDERER: Applied document layout to renderer (size {getattr(layout,'page_width',self.page_width)}x{getattr(layout,'page_height',self.page_height)}, margins={self.margins})")
        except Exception as e:
            print(f"RENDERER: Error applying document layout: {e}")

    def set_page_size(self, width, height):
        """Set the page size for rendering with dynamic layout refresh."""
        old_width = self.page_width
        old_height = self.page_height
        
        self.page_width = width
        self.page_height = height
        
        # If page width changed significantly, trigger layout refresh
        if abs(old_width - width) > 1.0:  # More than 1px change
            print(f"RENDERER: Page width changed from {old_width} to {width} - triggering layout refresh")
            
            # Trigger layout refresh if we have a document with temporal bridge
            if (hasattr(self, 'document') and self.document and 
                hasattr(self.document, 'staff_view') and self.document.staff_view and
                hasattr(self.document.staff_view, 'temporal_bridge') and self.document.staff_view.temporal_bridge):
                
                try:
                    self.document.staff_view.temporal_bridge._force_layout_refresh()
                    print(f"RENDERER: Triggered layout refresh for page width change")
                except Exception as e:
                    print(f"RENDERER: Error triggering layout refresh: {e}")
            
            # Force document update if available
            if hasattr(self, 'document') and self.document:
                try:
                    self.document.update()
                    print(f"RENDERER: Forced document update for page width change")
                except Exception as e:
                    print(f"RENDERER: Error updating document: {e}")
        
        print(f"RENDERER: Updated page size to {width}x{height}")

    def set_margins(self, margins):
        """Set the page margins and trigger layout refresh if changed."""
        try:
            old_margins = self.margins.copy()
        except Exception:
            old_margins = {}
        
        self.margins.update(margins)
        
        # If margins changed, trigger layout/content refresh similar to page size
        try:
            if old_margins != self.margins and hasattr(self, 'document') and self.document:
                # Trigger layout refresh via temporal bridge if available
                if (hasattr(self.document, 'staff_view') and self.document.staff_view and
                    hasattr(self.document.staff_view, 'temporal_bridge') and self.document.staff_view.temporal_bridge):
                    try:
                        self.document.staff_view.temporal_bridge._force_layout_refresh()
                        print("RENDERER: Triggered layout refresh for margin change")
                    except Exception as e:
                        print(f"RENDERER: Error triggering layout refresh on margin change: {e}")
                
                # Request document/view update
                try:
                    if hasattr(self.document, 'update'):
                        self.document.update()
                except Exception:
                    pass
        except Exception as e:
            print(f"RENDERER: set_margins error: {e}")
        
    def load_notation_settings(self):
        """Load notation settings with document precedence over preferences."""
        from PyQt6.QtCore import QSettings
        
        print(f"RENDERER: load_notation_settings() called, document: {self.document}")
        
        # Initialize QSettings for preferences
        settings = QSettings("ONOTE", "Preferences")
        
        # Get document settings if available
        document_settings = {}
        if self.document and hasattr(self.document, 'settings'):
            document_settings = self.document.settings
            print(f"RENDERER: Found document settings: {list(document_settings.keys())}")
        
        # Helper function to get setting with precedence: document -> preferences -> default
        def get_setting_with_precedence(key, default_value):
            # First check document settings
            if key in document_settings:
                value = document_settings[key]
                print(f"RENDERER: Using document setting {key} = {value}")
                return value
            
            # Then check preferences
            pref_value = settings.value(key, default_value)
            print(f"RENDERER: Using preference setting {key} = {pref_value} (default: {default_value})")
            return pref_value
        
        # Load settings with precedence
        self.staff_name_font_size = int(get_setting_with_precedence("notation/staff_name_font_size", 10))
        self.staff_name_vertical_offset = int(get_setting_with_precedence("notation/staff_name_vertical", -8))
        self.staff_name_horizontal_offset = int(get_setting_with_precedence("notation/staff_name_horizontal", -50))
        self.staff_name_font_color = get_setting_with_precedence("notation/staff_name_font_color", "#000000")
        
        self.section_name_font_size = int(get_setting_with_precedence("notation/section_name_font_size", 12))
        self.section_name_vertical_offset = int(get_setting_with_precedence("notation/section_name_vertical", -10))
        self.section_name_horizontal_offset = int(get_setting_with_precedence("notation/section_name_horizontal", -60))
        self.section_name_font_color = get_setting_with_precedence("notation/section_name_font_color", "#000000")
        
        self.clef_font_size = int(get_setting_with_precedence("notation/clef_font_size", 32))
        self.clef_vertical_offset = int(get_setting_with_precedence("notation/clef_vertical", 0))
        self.clef_horizontal_offset = int(get_setting_with_precedence("notation/clef_horizontal", 0))
        self.clef_font_color = get_setting_with_precedence("notation/clef_font_color", "#000000")
        
        self.time_sig_font_size = int(get_setting_with_precedence("notation/time_sig_font_size", 24))
        self.time_sig_vertical_offset = int(get_setting_with_precedence("notation/time_sig_vertical", 0))
        self.time_sig_horizontal_offset = int(get_setting_with_precedence("notation/time_sig_horizontal", 40))
        self.time_sig_spacing = int(get_setting_with_precedence("notation/time_sig_spacing", 18))
        self.time_sig_font_color = get_setting_with_precedence("notation/time_sig_font_color", "#000000")
        
        self.key_sig_font_size = int(get_setting_with_precedence("notation/key_sig_font_size", 14))
        self.key_sig_vertical_offset = int(get_setting_with_precedence("notation/key_sig_vertical", 0))
        self.key_sig_horizontal_offset = int(get_setting_with_precedence("notation/key_sig_horizontal", 75))
        self.key_sig_accidental_spacing = int(get_setting_with_precedence("notation/key_sig_accidental_spacing", 12))
        self.key_sig_font_color = get_setting_with_precedence("notation/key_sig_font_color", "#000000")
        
        self.directions_font_size = int(get_setting_with_precedence("notation/directions_font_size", 11))
        self.directions_vertical_offset = int(get_setting_with_precedence("notation/directions_vertical", 30))
        
        self.measure_numbers_font_size = int(get_setting_with_precedence("notation/measure_numbers_font_size", 8))
        self.measure_numbers_font_color = get_setting_with_precedence("notation/measure_numbers_font_color", "#000000")
        
        self.barline_number_font_size = int(get_setting_with_precedence("notation/barline_number_font_size", 7))
        self.barline_number_font_color = get_setting_with_precedence("notation/barline_numbers_font_color", "#000000")
        
        print(f"RENDERER: Loaded notation settings - staff_name_color: {self.staff_name_font_color}, section_name_color: {self.section_name_font_color}, clef_color: {self.clef_font_color}, time_sig_color: {self.time_sig_font_color}, key_sig_color: {self.key_sig_font_color}")
        print(f"RENDERER: Color settings loaded - clef: {self.clef_font_color}, time_sig: {self.time_sig_font_color}, key_sig: {self.key_sig_font_color}")
        print(f"RENDERER: Document settings available: {list(document_settings.keys()) if document_settings else 'None'}")
        
        # CRITICAL DEBUG: Check if we actually have the right colors
        if hasattr(self, 'staff_name_font_color'):
            print(f"RENDERER DEBUG: staff_name_font_color attribute exists: {self.staff_name_font_color}")
        if hasattr(self, 'section_name_font_color'):
            print(f"RENDERER DEBUG: section_name_font_color attribute exists: {self.section_name_font_color}")
        
        # Initialize measure number manager if available
        self._initialize_measure_number_manager()

    def _initialize_measure_number_manager(self):
        """Initialize the measure number manager with default settings."""
        try:
            from .measure_numbers import MeasureNumberManager
            # CRITICAL FIX: Pass the document parameter for proper settings precedence
            self.measure_number_manager = MeasureNumberManager(self.document)
            print(f"RENDERER: Initialized measure number manager with document: {self.document}")
            print(f"RENDERER: Settings loaded: {self.measure_number_manager.get_settings()}")
            
            # CRITICAL FIX: Force refresh settings to ensure we get the latest values
            # This is especially important for saved scores
            self.measure_number_manager.refresh_settings()
            print(f"RENDERER: Settings after refresh: {self.measure_number_manager.get_settings()}")
        except ImportError as e:
            print(f"RENDERER: Warning: Could not import MeasureNumberManager: {e}")
            self.measure_number_manager = None
        except Exception as e:
            print(f"RENDERER: Warning: Could not initialize measure number manager: {e}")
            self.measure_number_manager = None

    def render_score(self, painter, viewport_rect=None, mode="edit"):
        """Render the entire score with all its elements."""
        try:
            if not self.document or not hasattr(self.document, "layout"):
                return

            # Ensure measure numbers reflect the latest settings immediately
            if hasattr(self, 'measure_number_manager') and self.measure_number_manager:
                try:
                    self.measure_number_manager.refresh_settings()
                except Exception:
                    pass

            # NEW: Clear selectable elements at start of rendering
            if hasattr(self.document, 'staff_view') and hasattr(self.document.staff_view, 'element_selection'):
                self.document.staff_view.element_selection.clear_all_elements()

            # Calculate dynamic staff offsets based on the staff name lengths
            self._calculate_dynamic_staff_offsets(painter)

            # Resolve mode and viewport safely
            current_mode = 'setup' if (hasattr(self.document.layout, 'is_setup_mode') and self.document.layout.is_setup_mode) else 'edit'
            safe_viewport = QRect(0, 0, self.page_width, self.page_height)

            # Draw background based on mode
            if current_mode == 'setup':
                print("RENDERER: Drawing setup mode pink background")
                painter.fillRect(safe_viewport, QColor("#fff0f0"))
            else:
                print("RENDERER: Drawing edit mode white background")
                painter.fillRect(safe_viewport, QColor("#ffffff"))

            print("\nRENDERER: Beginning score rendering")
            
            # Draw all ungrouped staves and sections in the correct order
            # This relies on the ScoreLayout._update_positions method to set correct positions
            
            # First determine if we even have sections to render
            has_sections = hasattr(self.document.layout, 'sections') and self.document.layout.sections
            
            if has_sections:
                # Debug original section order before sorting
                print(f"\nRENDERER: Original section order from document:")
                for idx, section in enumerate(self.document.layout.sections):
                    print(f"  {idx}. Section: {section.name}, Order: {getattr(section, 'display_order_index', 0)}")
                    
                # CRITICAL FIX: Sort sections based on their display_order_index before rendering them
                # This ensures sections appear in the same order as in the setup dialog
                sorted_sections = sorted(self.document.layout.sections, 
                                         key=lambda s: getattr(s, 'display_order_index', 0))
                    
                # Debug section order after sorting
                print(f"\nRENDERER: Sections AFTER SORTING for rendering:")
                for idx, section in enumerate(sorted_sections):
                    print(f"  {idx}. Section: {section.name}, Order: {getattr(section, 'display_order_index', 0)}")
                    # Print the staves in this section
                    for i, staff in enumerate(section.staves):
                        print(f"    Staff {i}: {staff.instrument_name}, y_position={staff.y_position}")
            else:
                print("\nRENDERER: No sections found in document, only rendering ungrouped staves")
                sorted_sections = []
            
            # Debug ungrouped staves
            print(f"\nRENDERER: Ungrouped staves:")
            for idx, staff in enumerate(self.document.layout.ungrouped_staves):
                print(f"  {idx}. Staff: {staff.instrument_name}, y_position={staff.y_position}")
                
            # Draw all elements in their final positions
            # For correct rendering order, we need to render elements in order of ascending y_position
            
            # Create a combined list of all elements (ungrouped staves and sections)
            combined_elements = []
            
            # Add ungrouped staves
            for staff in self.document.layout.ungrouped_staves:
                combined_elements.append({
                    'type': 'staff',
                    'element': staff,
                    'y_pos': staff.y_position,
                    'name': staff.instrument_name
                })
            
            # Add sections
            for section in sorted_sections:
                # Skip empty sections
                if not section.staves:
                    print(f"RENDERER: Skipping empty section {section.name}")
                    continue
                    
                combined_elements.append({
                    'type': 'section',
                    'element': section,
                    'y_pos': section.bracket_y_start if hasattr(section, 'bracket_y_start') else getattr(section.staves[0], 'y_position', 0),
                    'name': section.name
                })
            
            # Sort all elements by their y_position for proper rendering order
            combined_elements.sort(key=lambda e: e['y_pos'])
            
            # Debug the rendering order based on y positions
            print(f"\nRENDERER: Final rendering order based on y_position:")
            for idx, elem in enumerate(combined_elements):
                print(f"  {idx}. {elem['type'].capitalize()}: {elem['name']}, y_pos={elem['y_pos']}")
            
            # Now render all elements in y_position order
            for elem in combined_elements:
                if elem['type'] == 'staff':
                    self._render_staff(painter, elem['element'])
                else:
                    self._render_section(painter, elem['element'])

            # --- CRITICAL: Draw barline 0 and barline 1 (and their numbers) ---
            self._render_connecting_barlines(painter)

            # NEW: Render measure numbers after barlines/layout repair so positions are correct
            try:
                if self.measure_number_manager and not (hasattr(self.document, 'layout') and self.document.layout.is_setup_mode):
                    measures = []
                    if hasattr(self.document, 'measures') and self.document.measures:
                        if isinstance(self.document.measures, dict):
                            ordered_keys = sorted([k for k in self.document.measures.keys() if isinstance(k, int)])
                            measures = [self.document.measures[k] for k in ordered_keys]
                        else:
                            measures = self.document.measures
                    staff_name = 'ScoreTop'
                    self.measure_number_manager.render_for_staff(painter, staff_name, measures, None, 0)
            except Exception as e:
                print(f"RENDERER: Error in post-barlines measure number pass: {e}")

            print("RENDERER: Score rendering completed successfully")
            
        except Exception as e:
            print(f"Error rendering score: {e}")
            import traceback
            traceback.print_exc()

    def _calculate_dynamic_staff_offsets(self, painter):
        """Calculate separate dynamic offsets for first system and continuation systems"""
        try:
            # Minimum offset to ensure sufficient space for rendering
            # This is essentially the minimum space for clef, key, and time signature
            min_offset = 5  # Reduced to allow tighter layout
            part_name_padding_left = 1  # Space between left page edge and start of part name
            part_name_padding_right = 20  # Space between part name and barline 0
            
            # Check if document is ready and has staves
            if not self.document or not hasattr(self.document, "layout"):
                # Use safe defaults
                self.first_system_offset = min_offset
                self.continuation_system_offset = min_offset
                return

            # Collect all instrument names and abbreviations
            longest_name = ""
            longest_name_width = 0
            longest_abbr = ""
            longest_abbr_width = 0

            # Collect section names
            longest_section_name = ""
            longest_section_name_width = 0

            # Save current font settings
            original_font = painter.font()

            # Set font for measuring instrument names
            name_font_size = 10
            if "instrumentName" in FONT_SIZES:
                name_font_size = FONT_SIZES["instrumentName"]

            try:
                name_font = QFont(MUSIC_FONTS["text"], name_font_size)
            except Exception as e:
                # Fallback to a generic font if specific fonts not available
                name_font = QFont("Arial", name_font_size)
                print(f"Error loading font: {e}")

            painter.setFont(name_font)

            # Measure all staves' instrument names and abbreviations
            staves_to_check = []

            # Get ungrouped staves
            if hasattr(self.document.layout, "ungrouped_staves"):
                staves_to_check.extend(self.document.layout.ungrouped_staves)

            # Get staves from sections and also measure section names
            sections_to_check = []
            if hasattr(self.document.layout, "sections"):
                for section in self.document.layout.sections:
                    sections_to_check.append(section)
                    if hasattr(section, "staves"):
                        staves_to_check.extend(section.staves)

            # Set font for measuring section names (slightly larger than instrument names)
            section_font_size = 12
            if "sectionName" in FONT_SIZES:
                section_font_size = FONT_SIZES["sectionName"]

            try:
                section_font = QFont(MUSIC_FONTS["text"], section_font_size)
                painter.setFont(section_font)

                # Measure all section names
                for section in sections_to_check:
                    if hasattr(section, "name") and section.name:
                        section_name_width = painter.fontMetrics().horizontalAdvance(section.name)
                        if section_name_width > longest_section_name_width:
                            longest_section_name = section.name
                            longest_section_name_width = section_name_width
            except Exception as e:
                print(f"Error measuring section names: {e}")

            # Switch back to instrument name font for measuring instrument names
            painter.setFont(name_font)

            # Check each staff for name and abbreviation
            for staff in staves_to_check:
                if hasattr(staff, "instrument_name") and staff.instrument_name:
                    name_width = painter.fontMetrics().horizontalAdvance(staff.instrument_name)
                    if name_width > longest_name_width:
                        longest_name = staff.instrument_name
                        longest_name_width = name_width

                if hasattr(staff, "instrument_abbr") and staff.instrument_abbr:
                    abbr_width = painter.fontMetrics().horizontalAdvance(staff.instrument_abbr)
                    if abbr_width > longest_abbr_width:
                        longest_abbr = staff.instrument_abbr
                        longest_abbr_width = abbr_width

            # Calculate space needed for names plus padding
            first_system_name_space = longest_name_width + part_name_padding_left + part_name_padding_right
            continuation_system_name_space = longest_abbr_width + part_name_padding_left + part_name_padding_right
            
            # For sections, we need slightly more space
            section_name_space = longest_section_name_width + part_name_padding_left + part_name_padding_right
            
            # Calculate the maximum space needed but override for testing
            # Temporarily force a small value to test left margin
            max_name_space = first_system_name_space
            # Override with a fixed small value 
            max_name_space = 50
            
            # Store values for use in rendering
            self.name_offset = max_name_space
            self.abbr_offset = max(continuation_system_name_space, min_offset + 20)
            
            # Now set the barline 0 position based on the calculated offsets
            # This ensures there's enough space for the names
            self.barline_0_offset = self.name_offset
            
            # For staff content, we use the same offset as barline 0
            # This ensures everything aligns properly
            self.first_system_offset = self.barline_0_offset
            self.continuation_system_offset = min_offset

            # Debug info with additional details
            print(
                f"Dynamic offsets: Name space: {self.name_offset}px, Barline 0: {self.barline_0_offset}px (longest name: '{longest_name}' {longest_name_width}px, longest section: '{longest_section_name}' {longest_section_name_width}px)"
            )

            # Restore original font
            painter.setFont(original_font)
                
        except Exception as e:
            print(f"Error calculating dynamic offsets: {e}")
            # Use reduced defaults
            self.first_system_offset = min_offset
            self.continuation_system_offset = min_offset
            self.name_offset = min_offset + 50
            self.abbr_offset = min_offset + 20
            self.barline_0_offset = min_offset + 50

    def _render_section(self, painter, section):
        """Render a section group including all of its staves and a bracket.
        
        This method relies on the positions already being correctly set by _update_positions
        in the ScoreLayout class. It respects the proper display order of the sections.
        """
        # Skip empty sections
        if not section.staves:
            print(f"RENDERER: Skipping empty section {section.name}")
            return
            
        # Debug the section rendering
        print(f"RENDERER: Rendering section {section.name} with {len(section.staves)} staves")
        print(f"  Section display_order_index: {getattr(section, 'display_order_index', 0)}")
        print(f"  Section bracket: y_start={section.bracket_y_start}, y_end={section.bracket_y_end}")
        
        # Verify bracket positions are valid
        has_valid_bracket = (
            hasattr(section, 'bracket_y_start') and
            hasattr(section, 'bracket_y_end') and
            section.bracket_y_end > section.bracket_y_start
        )
        
        if not has_valid_bracket:
            print(f"RENDERER WARNING: Section {section.name} has invalid bracket positions! Start={getattr(section, 'bracket_y_start', 'N/A')}, End={getattr(section, 'bracket_y_end', 'N/A')}")
        
        # Render all staves in this section
        # Important: Use the pre-calculated positions from ScoreLayout._update_positions
        for staff in section.staves:
            if isinstance(staff, GrandStaff):
                self._render_grand_staff(painter, staff)
            else:
                # Single staff
                self._render_single_staff(painter, staff)
                
        # After all staves are rendered, draw a bracket and section name
        if has_valid_bracket:
            self._render_section_bracket(painter, section)
        else:
            print(f"RENDERER ERROR: Skipping bracket rendering for section {section.name} due to invalid positions")
            
        # Draw section name at its calculated y_position
        if hasattr(section, "section_name_y"):
            # Set up proper text font for section names using configurable settings
            section_font = QFont(self.MUSIC_FONTS["text"], self.section_name_font_size)
            section_font.setBold(True)  # Make section names bold
            painter.setFont(section_font)
            
            # NEW: Set text color from document settings - FIXED to match clef/time sig approach
            from PyQt6.QtGui import QColor
            section_name_color = getattr(self, 'section_name_font_color', '#000000')
            print(f"RENDERER: Using section name color: {section_name_color}")
            
            # CRITICAL FIX: Save the current pen state before changing color
            original_pen = painter.pen()
            
            # Set the pen color for text drawing
            painter.setPen(QColor(section_name_color))
            
            # Calculate text width and center position
            name_width = painter.fontMetrics().horizontalAdvance(section.name)
            
            # Position text using configurable horizontal offset
            x = self.margins["left"] + self.section_name_horizontal_offset
            
            # Use the pre-calculated section_name_y position from _update_positions
            # Apply configurable vertical offset
            y = section.section_name_y + self.section_name_vertical_offset
            
            # Draw text horizontally (no rotation)
            painter.drawText(QPointF(x, y), section.name)
            print(f"RENDERER: Drew section name '{section.name}' at x={x}, y={y}, color={section_name_color}")
            
            # CRITICAL FIX: Restore the original pen state after drawing section name
            painter.setPen(original_pen)

    def _render_section_bracket(self, painter, section):
        """Render the bracket for a section using SMuFL glyphs with top, middle, and bottom components."""
        try:
            # Calculate bracket positions - adjust to start at the top line of first staff
            bracket_y_start = section.bracket_y_start
            bracket_y_end = section.bracket_y_end

            # Print debug info
            print(f"SECTION_BRACKET: Positions - top: {bracket_y_start}, bottom: {bracket_y_end}")
            print(f"SECTION_BRACKET: Height: {bracket_y_end - bracket_y_start}")

            if bracket_y_end <= bracket_y_start:
                print(
                    f"SECTION_BRACKET ERROR: Invalid bracket height {bracket_y_end - bracket_y_start}"
                )
                return

            # Calculate height including extensions
            bracket_height = bracket_y_end - bracket_y_start

            # Position bracket to the left of the initial barline
            bracket_offset = self.BRACKET_CONSTANTS["inset"]
            # Use the dynamic barline_0_offset for positioning
            bracket_x = float(self.margins["left"] + self.barline_0_offset - bracket_offset)

            # Save the painter state
            painter.save()

            try:
                # Use correct SMuFL bracket glyphs that open to the right
                # Standard section bracket glyphs from SMuFL
                bracket_top = "\uE003"  # bracketTop
                bracket_bottom = "\uE004"  # bracketBottom

                # Set font for the bracket - explicitly use Bravura font
                bracket_font_size = 24.0  # Base font size
                bracket_font = QFont("Bravura")
                bracket_font.setPointSizeF(bracket_font_size)
                painter.setFont(bracket_font)

                # Get font metrics for measurements
                metrics = painter.fontMetrics()

                # STEP 1: Position the top bracket glyph precisely at the first line of the top staff
                # Draw the top part at the top position (exactly at y_top)
                painter.drawText(QPointF(bracket_x, bracket_y_start), bracket_top)
                print(f"SECTION_BRACKET: Top bracket positioned at y={bracket_y_start}")

                # STEP 2: Position the bottom bracket glyph precisely at the fifth line of the bottom staff
                # Draw the bottom part at the bottom position (exactly at y_bottom) + 1px for precise alignment
                # Since the bottom bracket is currently between lines 4 and 5, we'll position it exactly on line 5
                bracket_bottom_y = bracket_y_end + 5  # Add 5 pixels to position on the bottom line
                painter.drawText(QPointF(bracket_x, bracket_bottom_y), bracket_bottom)
                print(
                    f"SECTION_BRACKET: Bottom bracket positioned at y={bracket_bottom_y} (adjusted to align with line 5)"
                )

                # STEP 3: Fill the space between top and bottom brackets with a single stretched vertical line
                # Use a simple vertical line instead of multiple glyph segments
                # This creates a cleaner, more consistent appearance

                try:
                    # Calculate the vertical space between the brackets with minimal gaps
                    # Start just below the top bracket with minimal gap (2px - just 0.25 staff line)
                    vertical_start = bracket_y_start + 2

                    # End just above the bottom bracket with minimal gap (2px - just 0.25 staff line)
                    vertical_end = bracket_bottom_y - 2

                    # Calculate the total height to fill
                    vertical_height = vertical_end - vertical_start

                    if vertical_height <= 0:
                        print(
                            f"SECTION_BRACKET WARNING: Insufficient vertical space between brackets ({vertical_height}px), using fallback method"
                        )
                        raise ValueError("Insufficient vertical space for stretching")

                    print(
                        f"SECTION_BRACKET: Using stretched vertical line from y={vertical_start} to y={vertical_end}"
                    )
                    print(f"SECTION_BRACKET: Total height to fill: {vertical_height}px")

                    # Save painter state
                    painter.save()

                    # Set pen for drawing the vertical line - slightly thicker (2.0) for better visual match with bracket glyphs
                    pen = QPen(Qt.GlobalColor.black, 2.0, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)

                    # Draw a simple vertical line connecting the brackets with precise endpoints
                    painter.drawLine(QLineF(bracket_x, vertical_start, bracket_x, vertical_end))

                    # Restore painter state
                    painter.restore()

                    print(
                        f"SECTION_BRACKET: Drew vertical line connecting brackets from y={vertical_start} to y={vertical_end}"
                    )
                    print(
                        f"SECTION_BRACKET: All three steps completed - Full bracket rendered from {bracket_y_start} to {bracket_bottom_y}"
                    )
                    return

                except Exception as scale_error:
                    print(f"SECTION_BRACKET: Vertical line drawing failed: {scale_error}")

                    # Fallback if vertical line drawing fails - use multi-segment approach
                    print("SECTION_BRACKET: Falling back to multi-segment approach")

                    # Calculate section height for positioning
                    section_height = bracket_bottom_y - bracket_y_start

                    # Calculate the space to fill
                    bracket_middle = "\uE034"  # Use the original middle bracket glyph for fallback
                    middle_glyph_height = metrics.height()

                    # For medium/large sections, use 10 segments minimum with 40% overlap
                    overlap_factor = 0.40
                    effective_segment_height = middle_glyph_height * (1 - overlap_factor)

                    # Start 15% down from top bracket, end 15% up from bottom
                    usable_space_start = bracket_y_start + (section_height * 0.15)
                    usable_space_end = bracket_bottom_y - (section_height * 0.15)
                    usable_space = usable_space_end - usable_space_start

                    # Calculate number of segments (minimum 10)
                    segments_needed = math.ceil(usable_space / effective_segment_height)
                    segments_needed = max(10, segments_needed)

                    # Calculate step size for even distribution
                    step_size = (
                        usable_space / (segments_needed - 1)
                        if segments_needed > 1
                        else usable_space
                    )

                    print(
                        f"SECTION_BRACKET: Using fallback with {segments_needed} middle segments with {overlap_factor*100}% overlap"
                    )

                    # Draw the fallback middle segments
                    for i in range(segments_needed):
                        y_pos = usable_space_start + (i * step_size)
                        painter.drawText(QPointF(bracket_x, y_pos), bracket_middle)
                        print(
                            f"SECTION_BRACKET: Middle segment {i+1}/{segments_needed} at y={y_pos}"
                        )

                print(
                    f"SECTION_BRACKET: All three steps completed - Full bracket rendered from {bracket_y_start} to {bracket_bottom_y}"
                )

            except Exception as font_error:
                # If SMuFL glyph fails, try using StaffGroupRenderer's custom drawing which draws brackets correctly
                print(
                    f"SECTION_BRACKET: SMuFL bracket rendering failed: {font_error}, trying StaffGroupRenderer"
                )

                try:
                    # Try using the custom bracket renderer from StaffGroupRenderer
                    from .score_layout import StaffGroupRenderer

                    StaffGroupRenderer.custom_render_section_bracket(
                        painter, bracket_x, bracket_y_start, bracket_y_end
                    )
                    print("SECTION_BRACKET: Used StaffGroupRenderer custom bracket drawing")

                except Exception as renderer_error:
                    print(
                        f"SECTION_BRACKET: StaffGroupRenderer failed: {renderer_error}, using simple lines"
                    )

                    # Final fallback: draw using simple lines
                    # Derive pen width from BRACKET_CONSTANTS
                    # Use a thicker pen for the fallback bracket
                    pen = QPen(Qt.GlobalColor.black, self.BRACKET_CONSTANTS["thickness"] / 3)
                    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                    painter.setPen(pen)

                    # Draw the vertical line first (on the right side)
                    painter.drawLine(bracket_x, bracket_y_start, bracket_x, bracket_y_end)

                    # Draw the horizontal lines for the bracket caps
                    # Make them open to the right, like a normal bracket
                    horizontal_offset = 12  # Horizontal width of the bracket ends

                    # Top horizontal line
                    painter.drawLine(
                        bracket_x, bracket_y_start, bracket_x + horizontal_offset, bracket_y_start
                    )

                    # Bottom horizontal line
                    painter.drawLine(
                        bracket_x, bracket_y_end, bracket_x + horizontal_offset, bracket_y_end
                    )

                    print(
                        "SECTION_BRACKET: Used simple lines fallback method with correct orientation"
                    )

            # Restore painter state
            painter.restore()

        except Exception as e:
            print(f"SECTION_BRACKET ERROR: Failed to render bracket: {e}")
            # Continue without bracket if it fails

    def _render_staff(self, painter, staff):
        """Render a single staff or grand staff based on its type with basic system wrapping for single-staff scores."""
        # Determine measures per system from preferences
        try:
            from PyQt6.QtCore import QSettings
            mps = int(QSettings("ONOTE", "Preferences").value("layout/default_measures_per_system", 4))
            mps = max(1, min(32, mps))
        except Exception:
            mps = 4

        # Count measures available
        measure_count = 0
        if hasattr(self.document, 'measures') and isinstance(self.document.measures, dict):
            measure_count = len(self.document.measures)

        # For now, only wrap for non-grand single staff; grand staff will be handled as a unit later
        if not isinstance(staff, GrandStaff) and measure_count > 0:
            total_systems = (measure_count + mps - 1) // mps
            for system_idx in range(total_systems):
                self._render_single_staff(painter, staff, selected=False, system_idx=system_idx, is_multi_staff=False)
        else:
            if isinstance(staff, GrandStaff):
                self._render_grand_staff(painter, staff)
            else:
                self._render_single_staff(painter, staff)

    def _render_grand_staff(self, painter, staff):
        """Render a grand staff with brace, staves, and instrument name."""
        print("GRAND_STAFF: Starting to render grand staff")
        try:
            # Safety checks to ensure the grand staff has valid top and bottom staves
            if not hasattr(staff, "top_staff"):
                print("GRAND_STAFF ERROR: No top_staff attribute")
                self._render_single_staff(painter, staff)
                return

            if not staff.top_staff:
                print("GRAND_STAFF ERROR: top_staff is None")
                self._render_single_staff(painter, staff)
                return

            if not hasattr(staff, "bottom_staff"):
                print("GRAND_STAFF ERROR: No bottom_staff attribute")
                self._render_single_staff(painter, staff)
                return

            if not staff.bottom_staff:
                print("GRAND_STAFF ERROR: bottom_staff is None")
                self._render_single_staff(painter, staff)
                return

            print(
                f"GRAND_STAFF: Top staff type: {type(staff.top_staff).__name__}, Bottom staff type: {type(staff.bottom_staff).__name__}"
            )

            # Store original positions
            try:
                top_staff_original_y = staff.top_staff.y_position
                bottom_staff_original_y = staff.bottom_staff.y_position
                print(
                    f"GRAND_STAFF: Original positions - top: {top_staff_original_y}, bottom: {bottom_staff_original_y}"
                )
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Couldn't access position attributes: {e}")
                self._render_single_staff(painter, staff)
                return

            # Space grand staff staves exactly 4 staff lines apart
            # Each staff line spacing is STAFF_LINE_SPACING
            grand_staff_spacing = STAFF_LINE_SPACING * 4  # Exactly 4 staff lines of space
            print(f"GRAND_STAFF: Using spacing of {grand_staff_spacing}px (4 staff lines)")

            # Update top staff position (keep it at the grand staff's y_position)
            try:
                staff.top_staff.y_position = staff.y_position
                print(f"GRAND_STAFF: Set top staff position to {staff.y_position}")

                # Update bottom staff position with 4-line spacing
                staff.bottom_staff.y_position = (
                    staff.top_staff.y_position + staff.top_staff.height + grand_staff_spacing
                )
                print(
                    f"GRAND_STAFF: Set bottom staff position to {staff.bottom_staff.y_position} with spacing {grand_staff_spacing}"
                )

                # Update brace positions
                staff.brace_y_start = staff.y_position
                staff.brace_y_end = staff.bottom_staff.y_position + staff.bottom_staff.height
                print(
                    f"GRAND_STAFF: Brace positions - start: {staff.brace_y_start}, end: {staff.brace_y_end}"
                )

                # Update instrument name y position (centered between staves)
                staff.instrument_name_y = staff.y_position + (
                    (staff.brace_y_end - staff.brace_y_start) / 2
                )
                print(f"GRAND_STAFF: Instrument name y position: {staff.instrument_name_y}")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Couldn't update positions: {e}")
                # Restore original positions if possible
                try:
                    staff.top_staff.y_position = top_staff_original_y
                    staff.bottom_staff.y_position = bottom_staff_original_y
                except Exception as inner_e:
                    print(f"GRAND_STAFF ERROR: Failed to restore positions: {inner_e}")
                self._render_single_staff(painter, staff)
                return

            # Skip drawing instrument name directly here - will be drawn differently
            # This prevents the "floating barline" effect

            # Draw brace first - ensure it appears
            try:
                print("GRAND_STAFF: Drawing brace")
                self._render_brace(painter, staff)
                print("GRAND_STAFF: Brace drawn successfully")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Brace rendering failed: {e}")
                # Continue even if brace fails

            # Draw staves - pass system_idx=0 for both, is_multi_staff=True to indicate part of multi-staff system
            print("GRAND_STAFF: Rendering top staff")
            try:
                self._render_single_staff(
                    painter, staff.top_staff, selected=False, system_idx=0, is_multi_staff=True
                )
                print("GRAND_STAFF: Top staff rendered successfully")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Top staff rendering failed: {e}")
                # Restore original positions
                try:
                    staff.top_staff.y_position = top_staff_original_y
                    staff.bottom_staff.y_position = bottom_staff_original_y
                except Exception as inner_e:
                    print(f"GRAND_STAFF ERROR: Failed to restore positions: {inner_e}")
                return

            print("GRAND_STAFF: Rendering bottom staff")
            try:
                self._render_single_staff(
                    painter, staff.bottom_staff, selected=False, system_idx=0, is_multi_staff=True
                )
                print("GRAND_STAFF: Bottom staff rendered successfully")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Bottom staff rendering failed: {e}")
                # Restore original positions
                try:
                    staff.top_staff.y_position = top_staff_original_y
                    staff.bottom_staff.y_position = bottom_staff_original_y
                except Exception as inner_e:
                    print(f"GRAND_STAFF ERROR: Failed to restore positions: {inner_e}")
                return

            # Draw instrument name only once, centered between the staves
            # This is drawn after the staves to ensure proper positioning
            try:
                print("GRAND_STAFF: Drawing instrument name")
                
                # Set font for instrument name using configurable settings
                try:
                    name_font = QFont(self.MUSIC_FONTS["text"], self.staff_name_font_size)
                    painter.setFont(name_font)
                except Exception as e:
                    # Fallback to a generic font
                    painter.setFont(QFont("Arial", self.staff_name_font_size))
                    print(f"Error setting instrument name font: {e}")

                # NEW: Set text color from document settings - FIXED to match clef/time sig approach
                from PyQt6.QtGui import QColor
                staff_name_color = getattr(self, 'staff_name_font_color', '#000000')
                print(f"RENDERER: Using staff name color: {staff_name_color}")
                
                # CRITICAL FIX: Save the current pen state before changing color
                original_pen = painter.pen()
                
                # Set the pen color for text drawing
                painter.setPen(QColor(staff_name_color))

                # Calculate barline 0 position using the dynamic offset
                barline_0_x = self.margins["left"] + self.barline_0_offset
                
                # Position name using configurable offsets
                # Calculate base position from left margin
                base_x = self.margins["left"] + self.staff_name_horizontal_offset
                
                # Measure the width of the name
                display_name = staff.instrument_name
                if hasattr(staff, "custom_name") and staff.custom_name:
                    display_name = staff.custom_name
                    
                # Truncate very long names if necessary with ellipsis
                max_name_length = 35  # Increased character limit for names
                if len(display_name) > max_name_length:
                    display_name = display_name[:max_name_length-3] + "..."
                        
                name_width = painter.fontMetrics().horizontalAdvance(display_name)
                
                # Use configurable horizontal offset
                name_x = base_x

                # Use the pre-calculated vertical position with configurable vertical offset
                point = QPointF(name_x, staff.instrument_name_y + self.staff_name_vertical_offset)

                painter.drawText(point, display_name)
                print(
                    f"GRAND_STAFF: Instrument name '{display_name}' drawn at position x={point.x()}, y={point.y()}, width={name_width}px, barline0={barline_0_x}, color={staff_name_color}"
                )
                
                # CRITICAL FIX: Restore the original pen state after drawing staff name
                painter.setPen(original_pen)
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Instrument name rendering failed: {e}")
                # Continue even if name fails

            # Always call ensure_grand_staff_final_barline
            # It will only draw in edit mode due to internal check
            try:
                self._ensure_grand_staff_final_barline(painter, staff)
                print("GRAND_STAFF: Added final barline")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Failed to add final barline: {e}")

            # Restore original positions
            try:
                staff.top_staff.y_position = top_staff_original_y
                staff.bottom_staff.y_position = bottom_staff_original_y
                print("GRAND_STAFF: Original positions restored")
            except Exception as e:
                print(f"GRAND_STAFF ERROR: Failed to restore positions: {e}")

            print("GRAND_STAFF: Rendering completed successfully")

        except Exception as e:
            print(f"GRAND_STAFF CRITICAL ERROR: {e}")
            # Attempt to render as a single staff as fallback
            try:
                self._render_single_staff(painter, staff)
                print("GRAND_STAFF: Fallback to single staff rendering succeeded")
            except:
                print("GRAND_STAFF: Fallback to single staff rendering also failed")

    def _render_brace(self, painter, staff):
        """Render the brace symbol for grand staff."""
        try:
            # Safety check for grand staff
            if not hasattr(staff, "is_grand_staff") or not staff.is_grand_staff:
                return

            if not hasattr(staff, "top_staff") or not hasattr(staff, "bottom_staff"):
                print("GRAND_STAFF ERROR: Missing top or bottom staff")
                return

            # Calculate brace positions relative to the actual staff lines
            # Keep the inset at 1.0 for consistent placement
            brace_inset = self.BRACE_CONSTANTS["inset"] * 1.0  # Keep at 1.0 (already working well)
            # Use the dynamic barline_0_offset for positioning
            brace_x = self.margins["left"] + self.barline_0_offset - brace_inset

            # Get the exact top line of the top staff and bottom line of the bottom staff
            # For top, extend 2 lines above the top line of the treble staff
            top_line_y = staff.top_staff.y_position - (
                2 * self.STAFF_LINE_SPACING
            )  # 2 lines above top line
            # For bottom, use line 5 (bottom line) of the bass staff
            bottom_line_y = (
                staff.bottom_staff.y_position
                + (self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING
            )

            # Add small extension beyond the staff lines
            # For top, align exactly with the top line (no extension)
            brace_y_start = top_line_y
            # For bottom, add just a tiny extension
            brace_y_end = bottom_line_y + self.BRACE_CONSTANTS["extension"] * 0.5
            brace_height = brace_y_end - brace_y_start

            print(
                f"GRAND_STAFF DEBUG: Brace positions - top: {top_line_y}, bottom: {bottom_line_y}"
            )
            print(f"GRAND_STAFF DEBUG: Brace height: {brace_height}")

            if brace_height <= 0:
                print(f"GRAND_STAFF ERROR: Invalid brace height {brace_height}")
                return

            # Save the painter state
            painter.save()

            # CRITICAL FIX: Ensure black color for brace
            painter.setPen(QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine))

            # Use approach from original implementation but with refined positioning
            try:
                # Calculate appropriate font size based on the brace height
                # Keep scaling factor at 0.85 (already working well)
                font_size = brace_height * 0.85

                # Set font for the brace - explicitly use Bravura font
                brace_font = QFont("Bravura")
                brace_font.setPointSizeF(font_size)
                painter.setFont(brace_font)

                # Use the brace character directly - uniE000 from Bravura font
                brace_char = "\uE000"  # SMuFL code for curly brace

                # Clear debug information to see what's happening
                print(
                    f"GRAND_STAFF DEBUG: Drawing brace at position ({brace_x}, {brace_y_end}) with font size {font_size}"
                )

                # Position the brace with y_end as the reference point (bottom of the brace)
                painter.drawText(QPointF(brace_x, brace_y_end), brace_char)

                print(f"GRAND_STAFF: Brace rendered using SMuFL glyph")
            except Exception as font_error:
                # If SMuFL glyph fails, use fallback custom drawing
                print(f"GRAND_STAFF: SMuFL brace rendering failed: {font_error}, using fallback")

                # Use a thick pen for the brace - CRITICAL: Ensure black color
                pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine)
                painter.setPen(pen)

                # Draw the main vertical line
                vertical_line = QLineF(
                    brace_x + 5, brace_y_start + 10, brace_x + 5, brace_y_end - 10
                )
                painter.drawLine(vertical_line)

                # Draw the curved parts using QPainterPath
                # Top curve
                top_path = QPainterPath()
                top_path.moveTo(brace_x + 5, brace_y_start + 10)
                top_path.quadTo(
                    brace_x - 8,
                    brace_y_start + 25,  # control point
                    brace_x,
                    brace_y_start + 40,  # end point
                )
                painter.drawPath(top_path)

                # Bottom curve
                bottom_path = QPainterPath()
                bottom_path.moveTo(brace_x + 5, brace_y_end - 10)
                bottom_path.quadTo(
                    brace_x - 8,
                    brace_y_end - 25,  # control point
                    brace_x,
                    brace_y_end - 40,  # end point
                )
                painter.drawPath(bottom_path)

                print("GRAND_STAFF: Brace rendered using fallback drawing")
            except Exception as e:
                print(f"Error rendering brace: {e}")

            # Restore painter state
            painter.restore()
            print("GRAND_STAFF: Brace rendering completed")
        except Exception as e:
            print(f"Error rendering brace: {e}")
            # Don't throw an exception, continue without the brace

    def _render_single_staff(
        self, painter, staff, selected=False, system_idx=0, is_multi_staff=False
    ):
        """Render a single staff with all its elements."""
        # Get the calculated offset for proper staff positioning
        staff_offset = self.first_system_offset if system_idx == 0 else self.continuation_system_offset
        
        # Calculate barline 0 position using the dynamic offset
        barline_0_x = self.margins["left"] + (self.barline_0_offset if system_idx == 0 else 0)
        
        # Highlight selected staff if in setup mode and selected
        if selected:
            painter.fillRect(
                QRectF(
                    barline_0_x,  # Start exactly at barline 0
                    staff.y_position,
                    self.page_width - barline_0_x - self.margins["right"],
                    staff.height,
                ),
                QColor(200, 200, 255, 100),
            )

        # Draw staff lines with a consistent thickness
        pen = QPen(Qt.GlobalColor.black, self.STAFF_LINE_THICKNESS)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)  # Use flat caps for clean edges
        painter.setPen(pen)

        # Calculate the precise position for each staff line - start at barline 0
        for i in range(self.STAFF_LINE_COUNT):
            y = float(staff.y_position + (i * self.STAFF_LINE_SPACING))
            line = QLineF(
                float(barline_0_x),  # Start at the dynamically calculated barline 0 position
                y,
                float(self.page_width - self.margins["right"]),
                y,
            )
            painter.drawLine(line)

        # Draw instrument name for first staff (only on first system)
        # Skip drawing instrument name if this staff is part of a multi-staff system (like grand staff)
        if hasattr(staff, "instrument_name") and staff.instrument_name and not is_multi_staff:
            # Set font for instrument name using configurable settings
            try:
                name_font = QFont(self.MUSIC_FONTS["text"], self.staff_name_font_size)
                painter.setFont(name_font)
            except Exception as e:
                # Fallback to a generic font
                painter.setFont(QFont("Arial", self.staff_name_font_size))
                print(f"Error setting instrument name font: {e}")

            # NEW: Set text color from document settings - FIXED to match clef/time sig approach
            from PyQt6.QtGui import QColor
            staff_name_color = getattr(self, 'staff_name_font_color', '#000000')
            print(f"RENDERER: Using staff name color: {staff_name_color}")
            
            # CRITICAL FIX: Save the current pen state before changing color
            original_pen = painter.pen()
            
            # Set the pen color for text drawing
            painter.setPen(QColor(staff_name_color))

            # Position name using configurable offsets
            # Calculate base position from left margin
            base_x = self.margins["left"] + self.staff_name_horizontal_offset
            
            # Measure the width of the name
            display_name = staff.instrument_name
            if hasattr(staff, "custom_name") and staff.custom_name:
                display_name = staff.custom_name
                
            # Truncate very long names if necessary with ellipsis
            max_name_length = 35  # Increased character limit for names
            if len(display_name) > max_name_length:
                display_name = display_name[:max_name_length-3] + "..."
                
            name_width = painter.fontMetrics().horizontalAdvance(display_name)
            
            # Use configurable horizontal offset
            name_x = base_x
            
            # Center vertically at the middle staff line with configurable vertical offset
            staff_center = float(
                staff.y_position + ((self.STAFF_LINE_COUNT - 1) / 2) * self.STAFF_LINE_SPACING
            )
            name_y = staff_center + self.staff_name_vertical_offset

            painter.drawText(QPointF(name_x, name_y), display_name)
            print(f"Drawing instrument name '{display_name}' at x={name_x}, y={name_y}, width={name_width}px, barline0={barline_0_x}, color={staff_name_color}")
            
            # CRITICAL FIX: Restore the original pen state after drawing staff name
            painter.setPen(original_pen)
            
            # NEW: Register this staff name as a selectable element
            if hasattr(self.document, 'staff_view') and hasattr(self.document.staff_view, 'element_selection'):
                self.document.staff_view.element_selection.create_staff_name_element(
                    staff, name_x, name_y, display_name, name_width
                )

        # Calculate initial elements width - needed for both modes
        initial_elements_width = self._calculate_initial_elements_width(staff)

        # Check if we're in edit mode
        is_setup_mode = hasattr(self.document, "layout") and self.document.layout.is_setup_mode

        # Draw clef with consistent positioning - starting from barline 0 + offset
        clef_x_base = barline_0_x
        staff.clef_x = clef_x_base + self.CLEF_POSITIONS[staff.clef]["x_offset"]
        self._render_clef(painter, staff, is_first_system=(system_idx == 0))

        # Draw key signature with consistent positioning
        staff.key_sig_x = clef_x_base + 50  # Position for key signature
        self._render_key_signature(painter, staff, is_first_system=(system_idx == 0))

        # Calculate time signature position based on key signature
        # Check if key has accidentals
        key = getattr(staff, "key", "C major / A minor (no sharps/flats)")
        if key != "C major / A minor (no sharps/flats)" and key:
            # Regular spacing for keys with accidentals
            time_sig_spacing = 50
        else:
            # Reduced spacing for C major / A minor
            time_sig_spacing = 0
            
        # Set time signature position - after key signature with appropriate spacing
        staff.time_sig_x = staff.key_sig_x + time_sig_spacing  
        print(f"Setting time_sig_x={staff.time_sig_x} with spacing={time_sig_spacing} for key={key}")
        self._render_time_signature(painter, staff, is_first_system=(system_idx == 0))

        # Get measure count from document
        if is_setup_mode:
            measure_count = 5
        else:
            try:
                if hasattr(self.document, 'measures') and self.document.measures:
                    if isinstance(self.document.measures, dict):
                        measure_count = len([k for k in self.document.measures.keys() if isinstance(k, int)])
                    else:
                        measure_count = len(self.document.measures)
                else:
                    measure_count = 0
            except Exception:
                measure_count = 0

        # Calculate system information
        try:
            from PyQt6.QtCore import QSettings
            measures_per_line = int(QSettings("ONOTE", "Preferences").value("layout/default_measures_per_system", 4))
            measures_per_line = max(1, min(32, measures_per_line))
        except Exception:
            measures_per_line = 4

        total_systems_needed = (measure_count + measures_per_line - 1) // measures_per_line
        is_final_system = system_idx == total_systems_needed - 1

        # Call the appropriate measure rendering implementation
        self._render_measures_impl(painter, staff, system_idx, False, is_final_system)
        
        # Measure numbers are rendered in a dedicated pass AFTER connecting barlines
        # to ensure layout repairs have been applied before positioning

    def _render_clef(self, painter, staff, is_first_system=False):
        """
        Render the clef for a staff using SMuFL symbols from Bravura font.
        """
        # Debug flag to track if custom settings are used
        using_custom_settings = False

        # First, verify that staff has a clef attribute and it's a valid string
        if not hasattr(staff, "clef") or not isinstance(staff.clef, str):
            print(
                f"[CLEF RENDER ERROR] Staff {staff.instrument_name} has no clef attribute or invalid clef type"
            )
            # Default to treble as fallback
            staff.clef = "treble"

        # CRITICAL DEBUG: Add a highly visible debug output for bass clef detection
        if hasattr(staff, "clef") and staff.clef == "bass":
            print(f"!!!!! BASS CLEF DETECTED for {staff.instrument_name} !!!!!")
            print(f"!!!!! Staff object ID: {id(staff)} !!!!!")
            if hasattr(staff, "instrument_id"):
                print(f"!!!!! Instrument ID: {staff.instrument_id} !!!!!")
        else:
            print(f"[CLEF DEBUG] Staff {staff.instrument_name} has clef type '{staff.clef}'")

        # Force debug output to check current clef setting
        print(
            f"[CLEF DEBUG] Rendering clef for {staff.instrument_name}, clef type is '{staff.clef}'"
        )

        # Check if staff has custom notation settings for clef
        custom_clef_constants = None
        custom_clef_positions = None

        if hasattr(staff, "notation_settings"):
            # Log the availability of notation_settings
            print(f"[DEBUG] Found notation_settings on staff {staff.instrument_name}")

            # Check for clef_constants
            if (
                "clef_constants" in staff.notation_settings
                and staff.clef in staff.notation_settings["clef_constants"]
            ):
                custom_clef_constants = staff.notation_settings["clef_constants"][staff.clef]
                print(
                    f"[CLEF RENDER] Using CUSTOM CONSTANTS for {staff.instrument_name} ({staff.clef}): {custom_clef_constants}"
                )
                using_custom_settings = True

            # Check for clef_positions
            if (
                "clef_positions" in staff.notation_settings
                and staff.clef in staff.notation_settings["clef_positions"]
            ):
                custom_clef_positions = staff.notation_settings["clef_positions"][staff.clef]
                print(
                    f"[CLEF RENDER] Using CUSTOM POSITIONS for {staff.instrument_name} ({staff.clef}): {custom_clef_positions}"
                )
                using_custom_settings = True

        # Use the clef_x position if it exists on the staff, otherwise calculate from barline 0
        if hasattr(staff, "clef_x"):
            clef_x = staff.clef_x + self.clef_horizontal_offset
            print(f"[CLEF RENDER] Using pre-calculated clef position: {clef_x} (with horizontal offset: {self.clef_horizontal_offset})")
        else:
            # Traditional approach - calculate from left margin
            barline_0_x = float(self.margins["left"])
            if hasattr(self, "first_system_offset") and is_first_system:
                barline_0_x += self.first_system_offset
            clef_x = barline_0_x + self.CLEF_CONSTANTS[staff.clef]["offset"] + self.clef_horizontal_offset
            print(f"[CLEF RENDER] Calculated clef position: {clef_x} (from barline 0 at {barline_0_x}, with horizontal offset: {self.clef_horizontal_offset})")

        # Check if we have this clef type in the constants, otherwise use treble as fallback
        if staff.clef not in self.CLEF_CONSTANTS:
            print(f"[CLEF RENDER WARNING] Unknown clef type '{staff.clef}', falling back to treble")
            staff.clef = "treble"

        # HARDCODED VERTICAL POSITIONING - completely override any constants
        # Apply vertical offset to all clef positions
        if staff.clef == "treble":
            # Position the G clef on the 4th line from the top (2nd line from bottom)
            # Calculate line positions (5 lines, 0-indexed from top)
            # Line 0 (top line): staff.y_position + 0 * STAFF_LINE_SPACING
            # Line 1: staff.y_position + 1 * STAFF_LINE_SPACING
            # Line 2: staff.y_position + 2 * STAFF_LINE_SPACING
            # Line 3 (4th from top): staff.y_position + 3 * STAFF_LINE_SPACING
            # Line 4 (bottom line): staff.y_position + 4 * STAFF_LINE_SPACING

            # Center the G clef symbol on the 4th line from top plus 0.5 line spacing
            line_y = staff.y_position + 3.5 * self.STAFF_LINE_SPACING

            # Add a slight vertical adjustment for visual centering of the clef on the line
            visual_adjustment = -7  # Pixels to shift up for visual centering
            clef_y = line_y + visual_adjustment + self.clef_vertical_offset

            print(
                f"[CLEF RENDER] Positioned treble clef 0.5 lines below 4th line from top: y={clef_y} (with vertical offset: {self.clef_vertical_offset})"
            )
        elif staff.clef == "bass":
            # Position the F clef on the 2nd line from the top plus 0.5 lines
            # Calculate line positions (5 lines, 0-indexed from top)
            # Line 0 (top line): staff.y_position + 0 * STAFF_LINE_SPACING
            # Line 1 (2nd line from top): staff.y_position + 1 * STAFF_LINE_SPACING
            # Line 2 (middle line): staff.y_position + 2 * STAFF_LINE_SPACING
            # Line 3: staff.y_position + 3 * STAFF_LINE_SPACING
            # Line 4 (bottom line): staff.y_position + 4 * STAFF_LINE_SPACING

            # Center the F clef between 2nd and middle line (line index 1.5)
            line_y = staff.y_position + 1.5 * self.STAFF_LINE_SPACING

            # Add a slight vertical adjustment for visual centering of the clef
            visual_adjustment = -5  # Pixels to shift up for visual centering
            clef_y = line_y + visual_adjustment + self.clef_vertical_offset

            print(
                f"[CLEF RENDER] Positioned bass clef 0.5 lines below 2nd line from top: y={clef_y} (with vertical offset: {self.clef_vertical_offset})"
            )
        elif staff.clef == "alto":
            # Position the Alto C clef exactly on the middle (3rd) line
            # Calculate line positions (5 lines, 0-indexed from top)
            # Line 0 (top line): staff.y_position + 0 * STAFF_LINE_SPACING
            # Line 1: staff.y_position + 1 * STAFF_LINE_SPACING
            # Line 2 (middle line): staff.y_position + 2 * STAFF_LINE_SPACING
            # Line 3: staff.y_position + 3 * STAFF_LINE_SPACING
            # Line 4 (bottom line): staff.y_position + 4 * STAFF_LINE_SPACING

            # Center the C clef on the middle line (line index 2) plus a half staff space
            line_y = staff.y_position + 2.5 * self.STAFF_LINE_SPACING

            # Add a slight vertical adjustment for visual centering of the clef
            visual_adjustment = -4  # Pixels to shift up for visual centering
            clef_y = line_y + visual_adjustment + self.clef_vertical_offset

            print(
                f"[CLEF RENDER] Positioned alto clef half a space below middle line: y={clef_y} (with vertical offset: {self.clef_vertical_offset})"
            )
        elif staff.clef == "percussion":
            # Position the percussion clef on the middle (3rd) line plus a half staff space
            # Calculate line positions (5 lines, 0-indexed from top)
            # Line 0 (top line): staff.y_position + 0 * STAFF_LINE_SPACING
            # Line 1: staff.y_position + 1 * STAFF_LINE_SPACING
            # Line 2 (middle line): staff.y_position + 2 * STAFF_LINE_SPACING
            # Line 3: staff.y_position + 3 * STAFF_LINE_SPACING
            # Line 4 (bottom line): staff.y_position + 4 * STAFF_LINE_SPACING

            # Center the percussion clef half a staff space below the middle line (line index 2.5)
            line_y = staff.y_position + 2.5 * self.STAFF_LINE_SPACING

            # Add a slight vertical adjustment for visual centering of the clef
            visual_adjustment = -4  # Pixels to shift up for visual centering
            clef_y = line_y + visual_adjustment + self.clef_vertical_offset

            print(
                f"[CLEF RENDER] Positioned percussion clef half a space below middle line: y={clef_y} (with vertical offset: {self.clef_vertical_offset})"
            )
        else:
            # Use constants for other clef types
            clef_y = staff.y_position + self.CLEF_CONSTANTS[staff.clef]["y_offset"] + self.clef_vertical_offset

        # Debug output
        print(
            f"[CLEF RENDER] Rendering clef {staff.clef} at x={clef_x}, y={clef_y} for staff {staff.instrument_name}"
        )

        # NEW: Register this clef as a selectable element
        if hasattr(self.document, 'staff_view') and hasattr(self.document.staff_view, 'element_selection'):
            self.document.staff_view.element_selection.create_clef_element(
                staff, clef_x, clef_y, width=30, height=40
            )

        # Draw the clef using SMuFL symbols from Bravura font
        painter.save()

        # Set font for clef rendering with fallbacks
        music_font_name = self.MUSIC_FONTS["default"]
        clef_font = QFont(music_font_name, self.clef_font_size)
        
        # Check if the music font is available, use fallbacks if not
        font_info = QFontInfo(clef_font)
        if font_info.family() != music_font_name:
            # Try common music fonts as fallbacks
            fallback_fonts = ["Bravura", "MuseScore", "FreeSerif", "Times New Roman", "Arial"]
            for fallback in fallback_fonts:
                test_font = QFont(fallback, self.clef_font_size)
                if QFontInfo(test_font).family() == fallback:
                    clef_font = test_font
                    print(f"[FONT] Using fallback font: {fallback}")
                    break
        
        painter.setFont(clef_font)
        
        # Set color for clef rendering
        from PyQt6.QtGui import QColor
        clef_color = getattr(self, 'clef_font_color', '#000000')
        print(f"[CLEF RENDER] Using color {clef_color} for clef")
        painter.setPen(QColor(clef_color))

        # Get the appropriate clef symbol
        clef_symbol = ""
        if staff.clef == "treble":
            clef_symbol = self.SYMBOL_MAP.get("trebleClef", "")
            # Fallback to Unicode symbol if SMuFL symbol is empty
            if not clef_symbol:
                clef_symbol = "𝄞"  # Unicode treble clef
        elif staff.clef == "bass":
            clef_symbol = self.SYMBOL_MAP.get("bassClef", "")
            # Fallback to Unicode symbol if SMuFL symbol is empty
            if not clef_symbol:
                clef_symbol = "𝄢"  # Unicode bass clef
        elif staff.clef == "alto":
            clef_symbol = self.SYMBOL_MAP.get("altoClef", "")
            # Fallback to Unicode symbol if SMuFL symbol is empty
            if not clef_symbol:
                clef_symbol = "𝄡"  # Unicode alto clef
        elif staff.clef == "tenor":
            clef_symbol = self.SYMBOL_MAP.get("tenorClef", "")
            # Fallback to Unicode symbol if SMuFL symbol is empty
            if not clef_symbol:
                clef_symbol = "𝄡"  # Unicode tenor clef (same as alto)
        elif staff.clef == "percussion":
            clef_symbol = self.SYMBOL_MAP.get("percussionClef", "")
            # Fallback to Unicode symbol if SMuFL symbol is empty
            if not clef_symbol:
                clef_symbol = "𝄥"  # Unicode percussion clef
        else:
            # Fallback to treble clef if unknown clef type
            print(f"[CLEF ERROR] Unknown clef type '{staff.clef}', using treble clef symbol")
            clef_symbol = self.SYMBOL_MAP.get("trebleClef", "𝄞")

        # Draw the clef symbol
        print(f"[CLEF RENDER] Drawing clef symbol: '{clef_symbol}' for clef type '{staff.clef}'")
        painter.drawText(QPointF(clef_x, clef_y), clef_symbol)

        # Restore original painter state
        painter.restore()

    def _render_key_signature(self, painter, staff, is_first_system=True):
        """Render the key signature for a staff."""
        painter.setFont(QFont(self.MUSIC_FONTS["default"], self.key_sig_font_size))
        
        # Set color for key signature rendering
        from PyQt6.QtGui import QColor
        key_sig_color = getattr(self, 'key_sig_font_color', '#000000')
        print(f"[KEY SIG RENDER] Using color {key_sig_color} for key signature")
        painter.setPen(QColor(key_sig_color))

        # Get key information
        key = staff.key

        # Use the key_sig_x position if it exists on the staff, otherwise calculate from barline 0
        if hasattr(staff, "key_sig_x"):
            x_start = staff.key_sig_x + self.key_sig_horizontal_offset
            print(f"[KEY SIG RENDER] Using pre-calculated key signature position: {x_start} (with horizontal offset: {self.key_sig_horizontal_offset})")
        else:
            # Traditional approach - calculate from left margin
            barline_0_x = float(self.margins["left"])
            if hasattr(self, "first_system_offset") and is_first_system:
                barline_0_x += self.first_system_offset
            
            # Position key signature after the clef with consistent spacing
            clef_width = self.CLEF_POSITIONS[staff.clef]["x_offset"] + 30  # Estimate clef width + spacing
            x_start = barline_0_x + clef_width + self.key_sig_horizontal_offset
            print(f"[KEY SIG RENDER] Calculated key position: {x_start} (from barline 0 at {barline_0_x}, with horizontal offset: {self.key_sig_horizontal_offset})")

        staff_center = float(
            staff.y_position + ((self.STAFF_LINE_COUNT - 1) / 2) * self.STAFF_LINE_SPACING
        ) + self.key_sig_vertical_offset
        
        # Parse key to determine sharps/flats
        sharp_keys = {
            "G major / E minor (1 sharp)": 1,
            "D major / B minor (2 sharps)": 2,
            "A major / F# minor (3 sharps)": 3,
            "E major / C# minor (4 sharps)": 4,
            "B major / G# minor (5 sharps)": 5,
            "F# major / D# minor (6 sharps)": 6,
            "C# major / A# minor (7 sharps)": 7,
        }

        flat_keys = {
            "F major / D minor (1 flat)": 1,
            "Bb major / G minor (2 flats)": 2,
            "Eb major / C minor (3 flats)": 3,
            "Ab major / F minor (4 flats)": 4,
            "Db major / Bb minor (5 flats)": 5,
            "Gb major / Eb minor (6 flats)": 6,
            "Cb major / Ab minor (7 flats)": 7,
        }

        # No sharps/flats for C major / A minor
        if key == "C major / A minor (no sharps/flats)" or not key:
            return

        # Draw sharps
        if key in sharp_keys:
            num_sharps = sharp_keys[key]
            # Order of sharps: F C G D A E B
            sharp_positions = [
                {"line": 1.5, "offset": 0},  # F sharp (top line of treble clef)
                {"line": -0.5, "offset": 0},  # C sharp (middle line of treble clef)
                {"line": 2, "offset": 0},  # G sharp
                {"line": 0, "offset": 0},  # D sharp
                {"line": 2.5, "offset": 0},  # A sharp
                {"line": 0.5, "offset": 0},  # E sharp
                {"line": 3, "offset": 0},  # B sharp
            ]

            # Adjust positions based on clef
            if staff.clef == "bass":
                for pos in sharp_positions:
                    pos["line"] += 2  # Shift up by two lines for bass clef
            elif staff.clef == "alto" or staff.clef == "tenor":
                for pos in sharp_positions:
                    pos["line"] += 1  # Shift up by one line for alto/tenor clef

            # Draw each sharp
            x = x_start
            for i in range(num_sharps):
                pos = sharp_positions[i]
                # Calculate y position based on line position (each line is STAFF_LINE_SPACING apart)
                y = staff.y_position + (
                    (self.STAFF_LINE_COUNT - 1 - pos["line"]) * self.STAFF_LINE_SPACING
                )
                # Draw the sharp symbol
                painter.drawText(QPointF(x, y), self.SYMBOL_MAP["sharp"])
                # Move to next position using configurable spacing
                x += self.key_sig_accidental_spacing

        # Draw flats
        elif key in flat_keys:
            num_flats = flat_keys[key]
            # Order of flats: B E A D G C F
            flat_positions = [
                {"line": 0, "offset": 0},  # B flat (middle line of treble clef)
                {"line": 2, "offset": 0},  # E flat (bottom line of treble clef)
                {"line": -0.5, "offset": 0},  # A flat
                {"line": 1.5, "offset": 0},  # D flat
                {"line": -1, "offset": 0},  # G flat
                {"line": 1, "offset": 0},  # C flat
                {"line": -1.5, "offset": 0},  # F flat
            ]

            # Adjust positions based on clef
            if staff.clef == "bass":
                for pos in flat_positions:
                    pos["line"] += 2  # Shift up by two lines for bass clef
            elif staff.clef == "alto" or staff.clef == "tenor":
                for pos in flat_positions:
                    pos["line"] += 1  # Shift up by one line for alto/tenor clef

            # Draw each flat
            x = x_start
            for i in range(num_flats):
                pos = flat_positions[i]
                # Calculate y position based on line position
                y = staff.y_position + (
                    (self.STAFF_LINE_COUNT - 1 - pos["line"]) * self.STAFF_LINE_SPACING
                )
                # Draw the flat symbol
                painter.drawText(QPointF(x, y), self.SYMBOL_MAP["flat"])
                # Move to next position using configurable spacing
                x += self.key_sig_accidental_spacing

        # NEW: Register this key signature as a selectable element (for both sharps and flats)
        if hasattr(self.document, 'staff_view') and hasattr(self.document.staff_view, 'element_selection'):
            # Calculate the bounds of the key signature area using configurable spacing
            key_width = 0
            if key in sharp_keys:
                num_sharps = sharp_keys[key]
                key_width = num_sharps * self.key_sig_accidental_spacing
            elif key in flat_keys:
                num_flats = flat_keys[key]
                key_width = num_flats * self.key_sig_accidental_spacing
            
            if key_width > 0:  # Only register if there are actually accidentals
                self.document.staff_view.element_selection.create_key_signature_element(
                    staff, x_start, staff_center, key_width
                )

    def _render_time_signature(self, painter, staff, is_first_system=True):
        """Render the time signature for a staff."""
        # Set font for music symbols using configurable font size
        painter.setFont(QFont(self.MUSIC_FONTS["default"], self.time_sig_font_size))
        
        # Set color for time signature rendering
        from PyQt6.QtGui import QColor
        time_sig_color = getattr(self, 'time_sig_font_color', '#000000')
        print(f"[TIME SIG RENDER] Using color {time_sig_color} for time signature")
        painter.setPen(QColor(time_sig_color))

        # Use the time_sig_x position if it exists on the staff, otherwise calculate from barline 0
        if hasattr(staff, "time_sig_x"):
            x = staff.time_sig_x + self.time_sig_horizontal_offset
            print(f"[TIME SIG RENDER] Using pre-calculated time signature position: {x} (with horizontal offset: {self.time_sig_horizontal_offset})")
        else:
            # Traditional approach - calculate from left margin
            barline_0_x = float(self.margins["left"])
            if hasattr(self, "first_system_offset") and is_first_system:
                barline_0_x += self.first_system_offset

            # Adjust position based on key signature width if present
            key = getattr(staff, "key", "C major / A minor (no sharps/flats)")
            print(f"[TIME SIG RENDER] Staff key: {key}")
            key_width = 0
            
            # Position clef first
            clef_width = self.CLEF_POSITIONS[staff.clef]["x_offset"] + 30  # Estimate clef width + spacing
            
            # If key has sharps or flats, calculate additional space needed
            if key != "C major / A minor (no sharps/flats)" and key:
                # Parse key to determine sharps/flats count
                sharp_keys = {
                    "G major / E minor (1 sharp)": 1,
                    "D major / B minor (2 sharps)": 2,
                    "A major / F# minor (3 sharps)": 3,
                    "E major / C# minor (4 sharps)": 4,
                    "B major / G# minor (5 sharps)": 5,
                    "F# major / D# minor (6 sharps)": 6,
                    "C# major / A# minor (7 sharps)": 7,
                }
                
                flat_keys = {
                    "F major / D minor (1 flat)": 1,
                    "Bb major / G minor (2 flats)": 2,
                    "Eb major / C minor (3 flats)": 3,
                    "Ab major / F minor (4 flats)": 4,
                    "Db major / Bb minor (5 flats)": 5,
                    "Gb major / Eb minor (6 flats)": 6,
                    "Cb major / Ab minor (7 flats)": 7,
                }
                
                # Calculate width based on number of accidentals
                accidental_count = 0
                if key in sharp_keys:
                    accidental_count = sharp_keys[key]
                elif key in flat_keys:
                    accidental_count = flat_keys[key]
                
                # Each accidental takes up space plus configurable spacing
                key_width = accidental_count * self.key_sig_accidental_spacing
                
                # Regular spacing after key signature with accidentals
                additional_spacing = 50  # Much larger spacing - 50px for keys with accidentals
            else:
                # Reduced spacing when there are no accidentals (C major / A minor)
                additional_spacing = 0  # No additional spacing at all - put time sig right after clef

            # Apply key signature width to position with appropriate spacing
            # Add configurable horizontal offset
            x = barline_0_x + clef_width + key_width + additional_spacing + self.time_sig_horizontal_offset
            print(f"[TIME SIG RENDER] Calculated time signature position: {x} (from barline 0 at {barline_0_x}, with additional spacing: {additional_spacing}, horizontal offset: {self.time_sig_horizontal_offset})")

        # Calculate the vertical center of the staff for positioning the time signature
        # Apply configurable vertical offset
        staff_center = float(
            staff.y_position + ((self.STAFF_LINE_COUNT - 1) / 2) * self.STAFF_LINE_SPACING
        ) + self.time_sig_vertical_offset

        # Parse time signature
        time_sig = staff.time_signature

        # Always use stacked numerals for all time signatures
        try:
            if "/" in time_sig:
                numerator, denominator = time_sig.split("/")
                numerator = numerator.strip()
                denominator = denominator.strip()

                # Use configurable spacing for numerator/denominator
                vertical_spacing = self.time_sig_spacing

                # Calculate positions with configurable separation
                # Move the numerator slightly higher
                numerator_y = staff_center - self.STAFF_LINE_SPACING / 4

                # Move the denominator lower with configurable spacing
                denominator_y = staff_center + self.STAFF_LINE_SPACING / 4 + vertical_spacing

                # Draw numerator (positioned above the 3rd line)
                painter.drawText(QPointF(x, numerator_y), numerator)

                # Draw denominator (positioned further below the 3rd line)
                painter.drawText(QPointF(x, denominator_y), denominator)
            else:
                # Single number time signature or invalid format
                painter.drawText(QPointF(x, staff_center), time_sig)
        except Exception as e:
            print(f"Error rendering time signature: {e}")
            # Fallback for any parsing errors
            painter.drawText(QPointF(x, staff_center), str(time_sig))

        # NEW: Register this time signature as a selectable element
        if hasattr(self.document, 'staff_view') and hasattr(self.document.staff_view, 'element_selection'):
            self.document.staff_view.element_selection.create_time_signature_element(
                staff, x, staff_center
            )

    def _render_initial_barline(self, painter, staff):
        """
        Initial barline rendering is now handled by _render_connecting_barlines.
        This method is kept for compatibility but does nothing.
        """
        # Simply return - all barlines are handled by _render_connecting_barlines
        return

    def _render_measures_impl(
        self, painter, staff, system_idx, is_continuation=False, is_final_system=False
    ):
        """Render a staff's measures with proper barlines."""
        # Get constants and settings for rendering
        page_width = self.page_width - self.margins["left"] - self.margins["right"]
        try:
            from PyQt6.QtCore import QSettings
            measures_per_line = int(QSettings("ONOTE", "Preferences").value("layout/default_measures_per_system", 4))
            measures_per_line = max(1, min(32, measures_per_line))
        except Exception:
            measures_per_line = 4

        # Determine if we're in setup mode
        is_setup_mode = hasattr(self.document, "layout") and self.document.layout.is_setup_mode

        # Calculate staff positions - CONSISTENT for both modes
        # Use the same positioning logic for both setup and edit modes
        staff_left_x = self.margins["left"]
        if system_idx == 0:  # First system
            # Use the dynamic offset for barline 0
            staff_left_x += self.barline_0_offset
        else:  # Continuation systems
            staff_left_x += self.continuation_system_offset

        # Compute vertical offset per wrapped system using Preferences
        try:
            from PyQt6.QtCore import QSettings
            qsettings = QSettings("ONOTE", "Preferences")
            # Per clarified nomenclature: use System Spacing for distance between wrapped systems
            spacing_pref = int(qsettings.value("layout/default_system_spacing", 80))
        except Exception:
            spacing_pref = getattr(self, 'staff_spacing', 120)

        staff_y = staff.y_position + (system_idx * spacing_pref)

        # Calculate initial elements width - needed for both modes
        initial_elements_width = self._calculate_initial_elements_width(staff)

        # Calculate the positions of the first measure barline (after clef, key, time)
        # This is NOT barline 0, which is now at the exact left margin in edit mode
        first_measure_barline_x = staff_left_x + initial_elements_width

        # SETUP MODE RENDERING - NO MEASURES
        if is_setup_mode:
            # In setup mode, draw staff lines and basic elements WITHOUT measures
            pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)

            # Draw staff lines only across the essential width (clef + key + time sig area)
            staff_content_width = initial_elements_width + 100  # Just enough for clef/key/time
            
            for i in range(5):  # 5 lines in a staff
                line_y = staff.y_position + i * self.STAFF_LINE_SPACING
                # Draw shorter staff lines in setup mode - just for essential elements
                painter.drawLine(QLineF(staff_left_x, line_y, staff_left_x + staff_content_width, line_y))

            # Add clef in setup mode
            self._render_clef(painter, staff, system_idx == 0)

            # Add key signature in setup mode
            self._render_key_signature(painter, staff, system_idx == 0)

            # Add time signature in setup mode
            self._render_time_signature(painter, staff, system_idx == 0)

            # NO BARLINES in setup mode - handled by _render_connecting_barlines
            return

        # EDIT MODE RENDERING - Handle empty document gracefully
        # RESTRUCTURE: Check if document has any user-created measures
        doc_measure_count = 0
        if hasattr(self.document, 'measures') and self.document.measures:
            doc_measure_count = len(self.document.measures)
            print(f"RENDERER: Found {doc_measure_count} user-created measures to render")
        else:
            print("RENDERER: No measures found - rendering empty staff (user will create measures on click)")
            doc_measure_count = 0
        
        # RESTRUCTURE: If no measures exist, render empty staff (ready for first click)
        if doc_measure_count <= 0:
            print("RENDERER: Rendering empty staff - ready for user to create first measure")
            
            # Draw staff lines from barline 0 to the end area (ready for first barline)
            pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            # Calculate the end position - where first barline will be created (dynamic)
            right_edge_x = self.page_width - self.margins["right"]
            # CRITICAL FIX: Use dynamic positioning instead of hardcoded offset
            end_barline_x = right_edge_x  # Use actual calculated right edge
            
            # Draw staff lines extending from barline 0 position to potential barline area
            barline_0_x = self.margins["left"] + self.barline_0_offset
            
            for i in range(5):  # 5 lines in a staff
                line_y = staff.y_position + i * self.STAFF_LINE_SPACING
                # Draw full-width staff lines - ready for first measure creation
                painter.drawLine(QLineF(barline_0_x, line_y, end_barline_x, line_y))

            # Add essential elements (clef, key signature, time signature)
            self._render_clef(painter, staff, system_idx == 0)
            self._render_key_signature(painter, staff, system_idx == 0)
            self._render_time_signature(painter, staff, system_idx == 0)
            
            print(f"RENDERER: Empty staff rendered - first barline will be created at x={end_barline_x}")
            # No barlines yet - only barline 0 will be drawn by _render_connecting_barlines
            return

        # EDIT MODE WITH MEASURES - Normal measure rendering
        # Right edge of the staff (available space)
        right_edge_x = self.page_width - self.margins["right"]

        # Calculate equal unit width for this system
        available_width = right_edge_x - first_measure_barline_x
        unit_width = available_width / max(1, measures_per_line)

        # Get the starting measure index for this system
        start_measure_idx = system_idx * measures_per_line

        # Calculate how many measures to render in this system
        remaining = max(0, doc_measure_count - start_measure_idx)
        if is_final_system:
            # Final system - render remaining measures (at least 1)
            num_measures_to_render = max(1, remaining)
        else:
            # Regular system - clamp to remaining
            num_measures_to_render = min(measures_per_line, max(1, remaining))

        # Draw staff lines across the entire system width
        pen = QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Calculate the staff end position using equal unit width
        staff_end_x = first_measure_barline_x + (unit_width * num_measures_to_render)
        
        # CRITICAL FIX: If no measures exist, extend staff lines to match where barlines will be positioned
        if doc_measure_count == 0:
            # For empty staff, extend to right edge to match barline positioning
            staff_end_x = right_edge_x

        # Draw the staff lines (5 lines per staff)
        for i in range(5):
            line_y = staff_y + i * self.STAFF_LINE_SPACING
            # Use QLineF to ensure correct types
            painter.drawLine(QLineF(staff_left_x, line_y, staff_end_x, line_y))

        # System-spanning final barlines are drawn in _render_connecting_barlines.
        # Avoid drawing a per-staff final bar here so the overlay connects across all staves.
        if is_final_system:
            pass

        # Barlines are handled by _render_connecting_barlines
        return

    def render_notes(self, painter, staff, notes):
        """Render notes on a staff."""
        # To be implemented: Draw notes
        pass

    def _render_connecting_barlines(self, painter):
        """
        Render barlines that connect multiple staves in the document.
        This is critical for proper score appearance - barlines should connect
        vertically across staves in a system, spanning all staves.
        """
        # Skip if document or layout is not available
        if not hasattr(self, 'document') or not hasattr(self.document, 'layout'):
            return
            
        # Debug info
        print("BARLINES: Rendering connecting barlines")
        
        # Get all staves from the document - FIXED: Ensure ALL staves are included
        all_staves = []
        
        # CRITICAL FIX: Start by collecting ALL staves from the document layout
        # This ensures we don't miss any staves that might not be in ungrouped_staves or sections
        if hasattr(self.document.layout, 'staves'):
            # Primary source: all staves in the layout
            all_staves.extend(self.document.layout.staves)
        
        # Add ungrouped staves (if not already included)
        if hasattr(self.document.layout, 'ungrouped_staves'):
            for staff in self.document.layout.ungrouped_staves:
                if staff not in all_staves:
                    all_staves.append(staff)
                
        # Add staves from sections (if not already included)
        if hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                if hasattr(section, 'staves'):
                    for staff in section.staves:
                        if staff not in all_staves:
                            all_staves.append(staff)
        
        # Sort staves by vertical position to ensure correct barline drawing order
        all_staves.sort(key=lambda staff: staff.y_position)
        
        # Count total staves for determining if we need to draw connecting barlines
        # A single staff doesn't need connecting barlines
        total_actual_staves = 0
        
        # ENHANCEMENT: Keep track of section boundaries for possibly rendering section barlines
        section_boundaries = []
        last_section = ""
        
        # Calculate total staves and identify grand staves for special handling
        grand_staves = []

        for idx, staff in enumerate(all_staves):
            if hasattr(staff, "is_grand_staff") and staff.is_grand_staff:
                # Count a grand staff as 2 staves for barline purposes
                total_actual_staves += 2
                grand_staves.append(staff)
            else:
                total_actual_staves += 1
                
            # ENHANCEMENT: Track section boundaries
            current_section = getattr(staff, 'section', "")
            if idx > 0 and current_section != last_section:
                # We've found a section boundary between the previous staff and this one
                if current_section:  # Only add if we're moving to a named section
                    section_boundaries.append((idx-1, idx))
                    print(f"BARLINES: Found section boundary between indices {idx-1} and {idx}")
            last_section = current_section

        # If no staves, nothing to do
        if not all_staves:
            return

        # Determine if we're in setup mode
        is_setup_mode = hasattr(self.document, "layout") and self.document.layout.is_setup_mode

        # Calculate key positions and dimensions
        # Helper to compute system vertical span (handles GrandStaff objects)
        def compute_system_span(staves_list):
            if not staves_list:
                return 0, self.page_height
            # Top
            first = staves_list[0]
            if hasattr(first, 'is_grand_staff') and getattr(first, 'is_grand_staff', False) and hasattr(first, 'top_staff'):
                top_y_val = first.top_staff.y_position
            else:
                top_y_val = first.y_position
            # Bottom
            last = staves_list[-1]
            if hasattr(last, 'is_grand_staff') and getattr(last, 'is_grand_staff', False) and hasattr(last, 'bottom_staff'):
                bottom_base = last.bottom_staff.y_position
            else:
                bottom_base = last.y_position
            bottom_y_val = bottom_base + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
            return top_y_val, bottom_y_val

        # Calculate position for the LEFT edge of the staves - for precise barline 0 alignment
        staff_left_edge = float(self.margins["left"])

        # Barline 0 is positioned using the dynamic offset
        barline_0_x = staff_left_edge + self.barline_0_offset

        # Calculate position for first measure barline (after clef, key sig, time sig)
        first_staff = all_staves[0]
        initial_elements_width = self._calculate_initial_elements_width(first_staff)

        # For the first measure barline, we need to account for the offset in edit mode
        if is_setup_mode:
            first_measure_barline_x = staff_left_edge + initial_elements_width
        else:
            # In edit mode, add the first_system_offset for the first measure barline
            # This is different from barline 0 which should be at the exact left margin
            first_measure_barline_x = (
                float(self.margins["left"] + self.first_system_offset) + initial_elements_width
            )

        # Get right edge position for calculating measure widths and final barline
        right_edge_x = self.page_width - self.margins["right"]

        # Standardize barline thickness using constants
        normal_thickness = self.BARLINE_CONSTANTS["normal"]["thickness"]

        # Function to draw normal barline with specified parameters
        def draw_normal_barline(x, y_top, y_bottom, extension=0, color_override=None):
            """Draw a single barline with top and bottom extensions"""
            # Extend top and bottom
            actual_y_top = float(y_top) - extension
            actual_y_bottom = float(y_bottom) + extension
            
            # Use consistent pen settings
            pen_color = color_override if color_override is not None else Qt.GlobalColor.black
            pen = QPen(pen_color, normal_thickness)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)  # ENHANCEMENT: Use flat cap for clean edges
            painter.setPen(pen)
            
            # Draw barline
            line = QLineF(x, actual_y_top, x, actual_y_bottom)
            painter.drawLine(line)
            
            return line  # ENHANCEMENT: Return the line for debugging or further use

        # Function to draw system-spanning final barline (connected across all staves)
        def draw_system_final_barline(x, y_top, y_bottom):
            # Draw thin line then thick line at x across the full system span
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawLine(int(x - 6), int(y_top), int(x - 6), int(y_bottom))
            painter.setPen(QPen(QColor(0, 0, 0), 4))
            painter.drawLine(int(x), int(y_top), int(x), int(y_bottom))
            print(f"BARLINES: Drew connected final bar (system) at x={x} (y={y_top} to {y_bottom})")

        # Decide whether to draw automatic system end bars here.
        # We now let _render_measures_impl draw the end bar at the computed staff width for the LAST system.
        auto_system_end_bars = False
        final_barline_x = float(self.page_width - self.margins["right"])  # fallback if ever needed
        if auto_system_end_bars:
            print(f"BARLINES: Final barline positioned at x={final_barline_x} (page_width={self.page_width}, right_margin={self.margins['right']})")

        # Only draw barline 0 if there are multiple staves or a grand staff
        if total_actual_staves > 1:
            # CRITICAL FIX: Always get the bounds from the full sorted list of staves
            # The top staff is the first one in the sorted list
            top_staff = all_staves[0]
            # The bottom staff is the last one in the sorted list
            bottom_staff = all_staves[-1]

            # Handle case where top or bottom might be a grand staff
            if (
                hasattr(top_staff, "is_grand_staff")
                and top_staff.is_grand_staff
                and hasattr(top_staff, "top_staff")
            ):
                top_y = top_staff.top_staff.y_position
            else:
                top_y = top_staff.y_position

            if (
                hasattr(bottom_staff, "is_grand_staff")
                and bottom_staff.is_grand_staff
                and hasattr(bottom_staff, "bottom_staff")
            ):
                bottom_y = bottom_staff.bottom_staff.y_position + (
                    (self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING
                )
            else:
                bottom_y = bottom_staff.y_position + (
                    (self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING
                )

            # Now draw barline 0 with precise alignment
            barline_extension = 0  # No extension for perfect alignment
            print(f"BARLINES: Drawing barline 0 at x={barline_0_x} from y={top_y} to y={bottom_y}")
            draw_normal_barline(barline_0_x, top_y, bottom_y)
            
            # Draw barline number for barline 0 if enabled
            self._render_barline_0_number(painter, barline_0_x, all_staves)

        # Always draw a proper final barline at the right edge for the current system
        # This ensures the initial measure shows the final bar at the system end
        if auto_system_end_bars and (not is_setup_mode) and all_staves:
            try:
                top_y, bottom_y = compute_system_span(all_staves)
                draw_system_final_barline(final_barline_x, top_y, bottom_y)
                print(f"BARLINES: Drew system final barline at x={final_barline_x} (y={top_y} to {bottom_y})")
            except Exception:
                pass

            if False:
                # NOTE: This code block is permanently disabled
                
                # CRITICAL FIX: Always use "final" for the end barline regardless of user measures
                # The end barline is a separate system element, not related to user-created barlines
                last_measure_barline_type = "final"  # Always "final" for proper end bar
                
                # EXPLANATION: User-created barlines are internal to the score, while the end barline
                # is a structural element that should always terminate the score properly
                print(f"BARLINES: Using fixed 'final' type for end barline (system element)")
                
                # Calculate the proper final barline position
                # For end bars (final), position should be at the thick barline element
                final_barline_x = right_edge_x
                print(f"BARLINES: End bar - positioning at thick element: x={final_barline_x}")
                
                # For end bars, use selective connection logic
                print("BARLINES: Drawing end bars with selective connection")
                
                # Process each staff and determine connection behavior
                i = 0
                while i < len(all_staves):
                    current_staff = all_staves[i]
                    
                    # Check if this is a grand staff
                    if hasattr(current_staff, 'is_grand_staff') and current_staff.is_grand_staff:
                        # Draw connected end bar for grand staff
                        if hasattr(current_staff, 'top_staff') and hasattr(current_staff, 'bottom_staff'):
                            top_y = current_staff.top_staff.y_position
                            bottom_y = current_staff.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                            draw_final_barline(final_barline_x, top_y, bottom_y)
                            print(f"BARLINES: Drew connected end bar for grand staff '{current_staff.instrument_name}' at x={final_barline_x} (y={top_y} to {bottom_y})")
                        i += 1
                        continue
                    
                    # Check if this staff is part of a section (should connect with other section staves)
                    if hasattr(current_staff, 'section') and current_staff.section:
                        # Find all consecutive staves in the same section
                        section_name = current_staff.section
                        section_staves = [current_staff]
                        j = i + 1
                        while j < len(all_staves):
                            next_staff = all_staves[j]
                            if hasattr(next_staff, 'section') and next_staff.section == section_name:
                                section_staves.append(next_staff)
                                j += 1
                            else:
                                break
                        
                        # Draw connected end bar for the entire section
                        if len(section_staves) > 1:
                            first_staff = section_staves[0]
                            last_staff = section_staves[-1]
                            top_y = first_staff.y_position
                            bottom_y = last_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                            draw_final_barline(final_barline_x, top_y, bottom_y)
                            section_staff_names = [staff.instrument_name for staff in section_staves]
                            print(f"BARLINES: Drew connected end bar for section '{section_name}' staves {section_staff_names} at x={final_barline_x} (y={top_y} to {bottom_y})")
                        else:
                            # Single staff in section, draw individual end bar
                            staff_y_top = current_staff.y_position
                            staff_y_bottom = current_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                            draw_final_barline(final_barline_x, staff_y_top, staff_y_bottom)
                            print(f"BARLINES: Drew individual end bar for single section staff '{current_staff.instrument_name}' at x={final_barline_x} (y={staff_y_top} to {staff_y_bottom})")
                        
                        # Skip all section staves we just processed
                        i = j
                        continue
                    
                    # This is a single ungrouped staff - draw individual end bar
                    staff_y_top = current_staff.y_position
                    staff_y_bottom = current_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                    draw_final_barline(final_barline_x, staff_y_top, staff_y_bottom)
                    print(f"BARLINES: Drew individual end bar for single staff '{current_staff.instrument_name}' at x={final_barline_x} (y={staff_y_top} to {staff_y_bottom})")
                    i += 1
            else:
                print(f"BARLINES: Automatic system end bars permanently disabled - user controls all barlines")

        # LEGACY PATH DISABLED: Older pass that drew user barlines immediately from
        # self.document.measures caused duplicate/early barlines on first frame.
        # We keep only the deduplicated temporal-bridge path below.
        if False:
            try:
                if hasattr(self.document, 'measures') and self.document.measures:
                    groups = []
                    if hasattr(self.document.layout, 'ungrouped_staves'):
                        for s in self.document.layout.ungrouped_staves:
                            groups.append(s)
                    if hasattr(self.document.layout, 'sections'):
                        for sec in self.document.layout.sections:
                            groups.append(sec)
                    groups.sort(key=lambda e: getattr(e, 'y_position', 0))

                    for measure in self.document.measures.values():
                        if not hasattr(measure, 'end_x'):
                            continue
                        x = float(measure.end_x)
                        bar_type = str(getattr(measure, 'barline_type', 'single')).lower()
                        is_selected = bool(getattr(measure, 'selected', False))
                        color = QColor(255,165,0) if is_selected else None

                        for g in groups:
                            if hasattr(g, 'staves') and g.staves:
                                top_y = g.staves[0].y_position
                                bottom_y = g.staves[-1].y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                            elif hasattr(g, 'is_grand_staff') and getattr(g, 'is_grand_staff', False) and hasattr(g, 'top_staff') and hasattr(g, 'bottom_staff'):
                                top_y = g.top_staff.y_position
                                bottom_y = g.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                            else:
                                top_y = g.y_position
                                bottom_y = g.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)

                            if bar_type == 'final':
                                draw_system_final_barline(x, top_y, bottom_y)
                            else:
                                draw_normal_barline(x, top_y, bottom_y, 0, color_override=color)
            except Exception:
                pass

        # ENHANCEMENT: Draw graphical dashed barlines
        try:
            if hasattr(self.document, 'graphical_dashed_barlines'):
                pen = QPen(QColor(120, 120, 120), normal_thickness, Qt.PenStyle.DashLine)
                for dashed in self.document.graphical_dashed_barlines:
                    # Orange when selected
                    if getattr(dashed, 'selected', False):
                        pen = QPen(QColor(255,165,0), normal_thickness, Qt.PenStyle.DashLine)
                    else:
                        pen = QPen(QColor(120, 120, 120), normal_thickness, Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    x = float(getattr(dashed, 'x_position', 0))
                    top_y_any = all_staves[0].y_position if all_staves else 0
                    bottom_y_any = (all_staves[-1].y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)) if all_staves else self.page_height
                    painter.drawLine(QLineF(x, top_y_any, x, bottom_y_any))
        except Exception:
            pass

        # ENHANCEMENT: Draw barlines at section boundaries if needed and in edit mode
        # DISABLED: This was causing unwanted vertical barlines next to section names
        # if section_boundaries and not is_setup_mode:
        if False:  # Disabled section boundary barlines
            for boundary in section_boundaries:
                top_idx, bottom_idx = boundary
                if 0 <= top_idx < len(all_staves) and 0 <= bottom_idx < len(all_staves):
                    top_staff = all_staves[top_idx]
                    bottom_staff = all_staves[bottom_idx]
                    
                    # Calculate the top Y coordinate (bottom of the top staff)
                    if hasattr(top_staff, "is_grand_staff") and top_staff.is_grand_staff and hasattr(top_staff, "bottom_staff"):
                        top_y = top_staff.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                    else:
                        top_y = top_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                        
                    # Calculate the bottom Y coordinate (top of the bottom staff)
                    if hasattr(bottom_staff, "is_grand_staff") and bottom_staff.is_grand_staff and hasattr(bottom_staff, "top_staff"):
                        bottom_y = bottom_staff.top_staff.y_position
                    else:
                        bottom_y = bottom_staff.y_position
                    
                    # Calculate midpoint between staves
                    mid_y = top_y + ((bottom_y - top_y) / 2)
                    
                    # Calculate spacing between section barlines for clarity
                    section_spacing = 10
                    
                    # Draw a system barline at the left margin (matching barline 0)
                    left_section_x = barline_0_x
                    section_line = draw_normal_barline(left_section_x, mid_y - section_spacing, mid_y + section_spacing, 0)
                    print(f"BARLINES: Drew section boundary at x={left_section_x}, y={mid_y} between {top_staff.instrument_name} and {bottom_staff.instrument_name}")
                    
                    # Draw a system barline at the first measure barline (matching measure 1)
                    first_section_x = first_measure_barline_x
                    section_line = draw_normal_barline(first_section_x, mid_y - section_spacing, mid_y + section_spacing, 0)
                    print(f"BARLINES: Drew section boundary at x={first_section_x}, y={mid_y} between {top_staff.instrument_name} and {bottom_staff.instrument_name}")

        # NEW: Draw individual measure barlines created by clicking
        if not is_setup_mode and hasattr(self.document, 'measures') and self.document.measures:
            # CRITICAL FIX: Access measures through temporal bridge to ensure coordinate correctness
            measures = None
            if hasattr(self.document, 'temporal_bridge') and self.document.temporal_bridge:
                # Use temporal bridge to get measures with correct coordinates
                measures = self.document.temporal_bridge._get_current_measures()
                print(f"BARLINES: Using temporal bridge, got {len(measures)} measures:")
                for i, measure in enumerate(measures):
                    print(f"  Measure #{getattr(measure, 'measure_number', i+1)}: end_x={getattr(measure, 'end_x', 'unknown')}")
            else:
                # Fallback: direct access
                measures = self.document.measures
                if isinstance(measures, dict):
                    measures = measures.values()
                print(f"BARLINES: Using direct access, got {len(list(measures))} measures")
            
            # De-duplicate barline x positions (guards against double-pass rendering on first frame)
            unique_positions = []
            eps = 0.5
            for m in measures:
                if hasattr(m, 'end_x'):
                    x = float(getattr(m, 'end_x', final_barline_x))
                    if not any(abs(x - ux) < eps for ux in unique_positions):
                        unique_positions.append(x)
            # Keep association of x to one representative measure for numbering/type
            rep_for_x = {}
            for m in measures:
                if hasattr(m, 'end_x'):
                    x = float(getattr(m, 'end_x', final_barline_x))
                    for ux in unique_positions:
                        if abs(x - ux) < eps and ux not in rep_for_x:
                            rep_for_x[ux] = m
                            break

            # Determine the current system's final barline x based on measures
            # Use the maximum end_x from existing measures; fallback to page right edge
            if unique_positions:
                current_system_final_x = max(unique_positions)
            else:
                current_system_final_x = float(self.page_width - self.margins["right"])  # fallback

            # Build top-level rendering order once
            rendering_order = []
            if hasattr(self.document.layout, 'ungrouped_staves'):
                for staff in self.document.layout.ungrouped_staves:
                    rendering_order.append(staff)
            if hasattr(self.document.layout, 'sections'):
                for section in self.document.layout.sections:
                    rendering_order.append(section)
            rendering_order.sort(key=lambda element: getattr(element, 'y_position', 0))

            for x in unique_positions:
                measure = rep_for_x.get(x)
                barline_x = x
                barline_type = getattr(measure, 'barline_type', 'single') if measure else 'single'

                # Draw barlines for each group separately
                self._draw_grouped_barlines(painter, barline_x, barline_type, rendering_order)

                # Render barline numbers for every measure when enabled
                if measure is not None:
                    self._render_barline_numbers(painter, measure, barline_x, rendering_order)

                print(f"BARLINES: Drew user-created {barline_type} barline at x={barline_x}")

            # Automatically overlay a FINAL barline at the last measure position for the current system
            try:
                if unique_positions:
                    last_x = max(unique_positions)
                    self._draw_grouped_barlines(painter, last_x, 'final', rendering_order)
                    print(f"BARLINES: Drew automatic FINAL overlay at x={last_x}")
            except Exception:
                pass

        # Draw system barlines per top-level group (single staff, grand staff, or section)
        staff_left_edge = float(self.margins["left"])
        barline_0_x = staff_left_edge + self.barline_0_offset
        # Prefer the computed current system final x if available
        try:
            final_barline_x = current_system_final_x
        except Exception:
            final_barline_x = float(self.page_width - self.margins["right"])  # fallback

        # Build top-level groups in vertical order
        top_level_groups = []
        if hasattr(self.document.layout, 'ungrouped_staves'):
            for item in self.document.layout.ungrouped_staves:
                top_level_groups.append(item)
        if hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                top_level_groups.append(section)
        top_level_groups.sort(key=lambda g: getattr(g, 'y_position', 0))

        barline0_number_drawn = False
        for group in top_level_groups:
            # Compute top/bottom y for this group
            if hasattr(group, 'staves') and group.staves:
                # Section group
                g_top = group.staves[0]
                g_bottom = group.staves[-1]
                top_y = g_top.y_position
                bottom_y = g_bottom.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
            elif hasattr(group, 'is_grand_staff') and getattr(group, 'is_grand_staff', False) and hasattr(group, 'top_staff') and hasattr(group, 'bottom_staff'):
                # Grand staff group
                top_y = group.top_staff.y_position
                bottom_y = group.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
            else:
                # Single staff
                top_y = group.y_position
                bottom_y = group.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)

            if is_setup_mode:
                draw_normal_barline(barline_0_x, top_y, bottom_y)
                if not barline0_number_drawn:
                    self._render_barline_0_number(painter, barline_0_x, [group])
                    barline0_number_drawn = True
            else:
                draw_normal_barline(barline_0_x, top_y, bottom_y)
                if not barline0_number_drawn:
                    self._render_barline_0_number(painter, barline_0_x, [group])
                    barline0_number_drawn = True
                # Final overlay is drawn once at the last measure position above

        # Optional: draw preview barline following cursor (per group)
        if hasattr(self, 'preview_barline_x') and self.preview_barline_x is not None:
            x_preview = float(self.preview_barline_x)
            for group in top_level_groups:
                if hasattr(group, 'staves') and group.staves:
                    g_top = group.staves[0]
                    g_bottom = group.staves[-1]
                    top_y = g_top.y_position
                    bottom_y = g_bottom.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                elif hasattr(group, 'is_grand_staff') and getattr(group, 'is_grand_staff', False) and hasattr(group, 'top_staff') and hasattr(group, 'bottom_staff'):
                    top_y = group.top_staff.y_position
                    bottom_y = group.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                else:
                    top_y = group.y_position
                    bottom_y = group.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                painter.save()
                pen = QPen(Qt.GlobalColor.darkGray, 1, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(QLineF(x_preview, top_y, x_preview, bottom_y))
                painter.restore()
        # Remove any duplicate unconditional barline 0/1 drawing after this block

    def _ensure_grand_staff_final_barline(self, painter, staff):
        """
        Ensure a grand staff has a consistent final barline that connects both staves.
        Called after rendering both staves of a grand staff.

        This is only drawn in edit mode, not in setup mode.
        """
        # Skip in setup mode
        is_setup_mode = hasattr(self.document, "layout") and self.document.layout.is_setup_mode
        if is_setup_mode:
            return

        if not hasattr(staff, "top_staff") or not hasattr(staff, "bottom_staff"):
            return

        # Skip if we already drew this in _render_connecting_barlines
        if (
            hasattr(staff, "_already_rendered_final_barline")
            and staff._already_rendered_final_barline
        ):
            return

        try:
            # Get the actual barline type from the last measure instead of hardcoding final barline
            last_measure_barline_type = "single"  # Default fallback
            
            # Find the actual last measure and get its barline type
            if hasattr(self.document, 'measures') and self.document.measures:
                if isinstance(self.document.measures, dict):
                    # Find the measure with highest number
                    if self.document.measures:
                        last_measure_num = max(self.document.measures.keys())
                        last_measure = self.document.measures[last_measure_num]
                        last_measure_barline_type = getattr(last_measure, 'barline_type', 'single')
                else:
                    # List format - get the last measure
                    if self.document.measures:
                        last_measure = self.document.measures[-1]
                        last_measure_barline_type = getattr(last_measure, 'barline_type', 'single')
            
            # Position for the end barline - FIXED: Use dynamic positioning based on page layout
            final_x = float(self.page_width - self.margins.get('right', 50))  # Dynamic calculation

            # Use exact top of top staff (no extension)
            y_top = float(staff.top_staff.y_position)

            # Helper function to calculate exact bottom position for a staff
            def get_exact_staff_bottom(s):
                # Bottom line is at y_position + (STAFF_LINE_COUNT - 1) * STAFF_LINE_SPACING
                return s.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)

            # Ensure barlines reach exactly to the bottom line of the bottom staff (no extension)
            y_bottom = float(get_exact_staff_bottom(staff.bottom_staff))

            # Debug info
            print(
                f"Grand staff final barline height check in _ensure_grand_staff_final_barline: top={y_top}, bottom={y_bottom}, height={y_bottom-y_top}"
            )

            # Draw the appropriate barline type based on the last measure
            if last_measure_barline_type == "final":
                # Draw the thin line
                thin_pen = QPen(Qt.GlobalColor.black, self.BARLINE_CONSTANTS["final"]["thicknessThin"])
                painter.setPen(thin_pen)
                thin_line = QLineF(final_x, y_top, final_x, y_bottom)
                painter.drawLine(thin_line)

                # Calculate the thick line position
                thick_x = final_x + self.BARLINE_CONSTANTS["final"]["spacing"]

                # Draw the thick line
                thick_pen = QPen(
                    Qt.GlobalColor.black, self.BARLINE_CONSTANTS["final"]["thicknessThick"]
                )
                painter.setPen(thick_pen)
                thick_line = QLineF(thick_x, y_top, thick_x, y_bottom)
                painter.drawLine(thick_line)

                print("GRAND_STAFF: Drew connecting final barline successfully")
            elif last_measure_barline_type == "double":
                # Draw double barline (two thin lines)
                pen = QPen(Qt.GlobalColor.black, 1)
                painter.setPen(pen)
                painter.drawLine(QLineF(final_x, y_top, final_x, y_bottom))
                painter.drawLine(QLineF(final_x + 4, y_top, final_x + 4, y_bottom))
                print("GRAND_STAFF: Drew connecting double barline successfully")
            else:
                # Draw single barline (default for single, repeat types, etc.)
                pen = QPen(Qt.GlobalColor.black, 1)
                painter.setPen(pen)
                painter.drawLine(QLineF(final_x, y_top, final_x, y_bottom))
                print("GRAND_STAFF: Drew connecting single barline successfully")

            # Mark as rendered
            staff._already_rendered_final_barline = True
        except Exception as e:
            print(f"GRAND_STAFF ERROR: Could not draw connecting final barline: {e}")

    def _calculate_initial_elements_width(self, staff):
        """Calculate the width needed for initial elements (clef, key signature, time signature) dynamically."""
        # Base width for clef
        width = 50  # Start with space for clef

        # Add space for key signature based on number of accidentals
        key = staff.key

        # Parse key to determine sharps/flats
        sharp_keys = {
            "G major / E minor (1 sharp)": 1,
            "D major / B minor (2 sharps)": 2,
            "A major / F# minor (3 sharps)": 3,
            "E major / C# minor (4 sharps)": 4,
            "B major / G# minor (5 sharps)": 5,
            "F# major / D# minor (6 sharps)": 6,
            "C# major / A# minor (7 sharps)": 7,
        }

        flat_keys = {
            "F major / D minor (1 flat)": 1,
            "Bb major / G minor (2 flats)": 2,
            "Eb major / C minor (3 flats)": 3,
            "Ab major / F minor (4 flats)": 4,
            "Db major / Bb minor (5 flats)": 5,
            "Gb major / Eb minor (6 flats)": 6,
            "Cb major / Ab minor (7 flats)": 7,
        }

        # Calculate additional width for key signature
        if key in sharp_keys:
            width += sharp_keys[key] * self.KEY_SIGNATURE_CONSTANTS["interAccidentalSpacing"] * 1.5
            # Regular spacing after key signature with accidentals
            additional_spacing = 50  # Much larger spacing - 50px for keys with accidentals
        elif key in flat_keys:
            width += flat_keys[key] * self.KEY_SIGNATURE_CONSTANTS["interAccidentalSpacing"] * 1.5
            # Regular spacing after key signature with accidentals
            additional_spacing = 50  # Much larger spacing - 50px for keys with accidentals
        else:
            # Reduced spacing when there are no accidentals (C major / A minor)
            additional_spacing = 0  # No additional spacing at all - put time sig right after clef

        # Add space for time signature with appropriate spacing
        width += 40 + additional_spacing  # Space for time signature plus spacing

        # Add a small buffer
        width += 15 - additional_spacing  # Adjust buffer to maintain consistent total width

        print(f"Calculated initial elements width: {width}px for key: {key}, with additional spacing: {additional_spacing}")
        return width

    def _get_dynamic_offset(self, staff):
        """
        Calculate dynamic horizontal offset for a staff based on part name length.
        This ensures that all staves are properly aligned while maintaining clear margins.

        Args:
            staff: The staff to calculate the offset for

        Returns:
            float: The dynamic horizontal offset
        """
        # Return consistent offset (0.0) for both setup and edit mode
        # This ensures clef and time signature appear at the same position in both modes
        return 0.0

    def paintEvent(self, event):
        """Handle paint events for the score view"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # === TEMPORARY TEST MARKER - REMOVE WHEN FIXES CONFIRMED ===
        # Draw a bright red rectangle and text to confirm our changes are active
        painter.fillRect(10, 10, 400, 60, QColor(255, 0, 0))  # Bright red background
        painter.setPen(QColor(255, 255, 255))  # White text
        font = painter.font()
        font.setPointSize(16)
        # CRITICAL FIX: Remove debug text that was causing orange "2345" anomaly
        # font.setBold(True)
        # painter.setFont(font)
        # painter.drawText(20, 35, "🔥 CODE CHANGES ACTIVE - FIXES APPLIED! 🔥")
        # painter.drawText(20, 55, f"Order fix test: StaffBase default = 0")
        # === END TEMPORARY TEST MARKER ===
        
        try:
            if not self.document or not hasattr(self.document, "layout"):
                return

            # Calculate dynamic staff offsets based on the staff name lengths
            self._calculate_dynamic_staff_offsets(painter)

            # Resolve mode and viewport safely
            current_mode = 'setup' if (hasattr(self.document.layout, 'is_setup_mode') and self.document.layout.is_setup_mode) else 'edit'
            safe_viewport = QRect(0, 0, self.page_width, self.page_height)

            # Draw background based on mode
            if current_mode == 'setup':
                print("RENDERER: Drawing setup mode pink background")
                painter.fillRect(safe_viewport, QColor("#fff0f0"))
            else:
                print("RENDERER: Drawing edit mode white background")
                painter.fillRect(safe_viewport, QColor("#ffffff"))

            print("\nRENDERER: Beginning score rendering")
            
            # Draw all ungrouped staves and sections in the correct order
            # This relies on the ScoreLayout._update_positions method to set correct positions
            
            # First determine if we even have sections to render
            has_sections = hasattr(self.document.layout, 'sections') and self.document.layout.sections
            
            if has_sections:
                # Debug original section order before sorting
                print(f"\nRENDERER: Original section order from document:")
                for idx, section in enumerate(self.document.layout.sections):
                    print(f"  {idx}. Section: {section.name}, Order: {getattr(section, 'display_order_index', 0)}")
                    
                # CRITICAL FIX: Sort sections based on their display_order_index before rendering them
                # This ensures sections appear in the same order as in the setup dialog
                sorted_sections = sorted(self.document.layout.sections, 
                                         key=lambda s: getattr(s, 'display_order_index', 0))
                    
                # Debug section order after sorting
                print(f"\nRENDERER: Sections AFTER SORTING for rendering:")
                for idx, section in enumerate(sorted_sections):
                    print(f"  {idx}. Section: {section.name}, Order: {getattr(section, 'display_order_index', 0)}")
                    # Print the staves in this section
                    for i, staff in enumerate(section.staves):
                        print(f"    Staff {i}: {staff.instrument_name}, y_position={staff.y_position}")
            else:
                print("\nRENDERER: No sections found in document, only rendering ungrouped staves")
                sorted_sections = []
            
            # Debug ungrouped staves
            print(f"\nRENDERER: Ungrouped staves:")
            for idx, staff in enumerate(self.document.layout.ungrouped_staves):
                print(f"  {idx}. Staff: {staff.instrument_name}, y_position={staff.y_position}")
                
            # Draw all elements in their final positions
            # For correct rendering order, we need to render elements in order of ascending y_position
            
            # Create a combined list of all elements (ungrouped staves and sections)
            combined_elements = []
            
            # Add ungrouped staves
            for staff in self.document.layout.ungrouped_staves:
                combined_elements.append({
                    'type': 'staff',
                    'element': staff,
                    'y_pos': staff.y_position,
                    'name': staff.instrument_name
                })
            
            # Add sections
            for section in sorted_sections:
                # Skip empty sections
                if not section.staves:
                    print(f"RENDERER: Skipping empty section {section.name}")
                    continue
                    
                combined_elements.append({
                    'type': 'section',
                    'element': section,
                    'y_pos': section.bracket_y_start if hasattr(section, 'bracket_y_start') else getattr(section.staves[0], 'y_position', 0),
                    'name': section.name
                })
            
            # Sort all elements by their y_position for proper rendering order
            combined_elements.sort(key=lambda e: e['y_pos'])
            
            # Debug the rendering order based on y positions
            print(f"\nRENDERER: Final rendering order based on y_position:")
            for idx, elem in enumerate(combined_elements):
                print(f"  {idx}. {elem['type'].capitalize()}: {elem['name']}, y_pos={elem['y_pos']}")
            
            # Now render all elements in y_position order
            for elem in combined_elements:
                if elem['type'] == 'staff':
                    self._render_staff(painter, elem['element'])
                else:
                    self._render_section(painter, elem['element'])

            # --- CRITICAL: Draw barline 0 and barline 1 (and their numbers) ---
            self._render_connecting_barlines(painter)

            print("RENDERER: Score rendering completed successfully")
            
        except Exception as e:
            print(f"Error rendering score: {e}")
            import traceback
            traceback.print_exc()

    def _draw_repeat_dots_for_barline(self, painter, barline_x, barline_type, top_y, bottom_y):
        """Draw repeat dots for repeat barlines - one pair per staff"""
        painter.save()
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        
        # Get ALL staves in the score (both section staves and ungrouped staves)
        all_staves = []
        
        # First, add staves from sections
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'sections'):
            for section in self.document.layout.sections:
                if hasattr(section, 'staves'):
                    all_staves.extend(section.staves)
        
        # Then, add ungrouped staves
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'ungrouped_staves'):
            all_staves.extend(self.document.layout.ungrouped_staves)
        
        # Fallback: if no layout system, create representation from top_y to bottom_y
        if not all_staves:
            # Calculate number of staves based on y range
            staff_height = (self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING  # 32px
            total_height = bottom_y - top_y
            estimated_staves = max(1, int(total_height / (staff_height + self.STAFF_LINE_SPACING)))
            
            for i in range(estimated_staves):
                staff_y = top_y + (i * (staff_height + self.STAFF_LINE_SPACING))
                all_staves.append(type('Staff', (), {'y_position': staff_y}))
        
        dot_radius = 2.0
        
        # Draw dots for each staff individually
        for staff in all_staves:
            # Check if this is a grand staff - if so, draw dots on both treble and bass parts
            if hasattr(staff, "is_grand_staff") and staff.is_grand_staff:
                # Grand staff has two physical staves: treble (top) and bass (bottom)
                # The staff.y_position is the top staff position
                treble_y_start = staff.y_position
                
                # Calculate bass staff position (typically 40px below treble for grand staff)
                bass_y_start = treble_y_start + 72  # Standard grand staff spacing
                
                # Draw dots on treble staff
                self._draw_dots_for_single_staff(painter, barline_x, barline_type, treble_y_start, dot_radius)
                
                # Draw dots on bass staff
                self._draw_dots_for_single_staff(painter, barline_x, barline_type, bass_y_start, dot_radius)
            else:
                # Regular single staff
                staff_y_start = staff.y_position
                self._draw_dots_for_single_staff(painter, barline_x, barline_type, staff_y_start, dot_radius)
        
        painter.restore()

    def _draw_dots_for_single_staff(self, painter, barline_x, barline_type, staff_y_start, dot_radius):
        """Draw repeat dots for a single staff at the given y position"""
        # Calculate dot positions within this staff:
        # Top dot: in 2nd space (between 2nd and 3rd lines)
        # Bottom dot: in 3rd space (between 3rd and 4th lines)
        line_spacing = self.STAFF_LINE_SPACING  # 8px
        
        # Top dot: middle of space between 2nd and 3rd lines
        dot1_y = staff_y_start + line_spacing + (line_spacing / 2)  # y + 8 + 4 = y + 12
        # Bottom dot: middle of space between 3rd and 4th lines  
        dot2_y = staff_y_start + (2 * line_spacing) + (line_spacing / 2)  # y + 16 + 4 = y + 20
        
        if barline_type == "repeat_start":
            # Dots go to the RIGHT of the barline
            dot_x = barline_x + 8
            painter.drawEllipse(QPointF(dot_x, dot1_y), dot_radius, dot_radius)
            painter.drawEllipse(QPointF(dot_x, dot2_y), dot_radius, dot_radius)
        elif barline_type == "repeat_end":
            # Dots go to the LEFT of the barline
            dot_x = barline_x - 8
            painter.drawEllipse(QPointF(dot_x, dot1_y), dot_radius, dot_radius)
            painter.drawEllipse(QPointF(dot_x, dot2_y), dot_radius, dot_radius)
        elif barline_type == "repeat_both":
            # Dots on BOTH sides of the barline
            # Left dots (for repeat end)
            left_dot_x = barline_x - 8
            painter.drawEllipse(QPointF(left_dot_x, dot1_y), dot_radius, dot_radius)
            painter.drawEllipse(QPointF(left_dot_x, dot2_y), dot_radius, dot_radius)
            # Right dots (for repeat start)
            right_dot_x = barline_x + 8
            painter.drawEllipse(QPointF(right_dot_x, dot1_y), dot_radius, dot_radius)
            painter.drawEllipse(QPointF(right_dot_x, dot2_y), dot_radius, dot_radius)

    def _draw_grouped_barlines(self, painter, barline_x, barline_type, rendering_order):
        """Draw barlines grouped by sections, grand staves, and individual single staves"""
        
        def draw_normal_barline(x, y_top, y_bottom, extension=0):
            """Helper function to draw a normal barline"""
            pen = QPen(Qt.GlobalColor.black, 1)
            painter.setPen(pen)
            line = QLineF(x, y_top - extension, x, y_bottom + extension)
            painter.drawLine(line)
            return line
            
        def draw_final_barline(x, y_top, y_bottom):
            # Use SMuFL glyph uniE032 for end bar (final barline)
            if hasattr(self, 'bravura_font') and self.bravura_font:
                # Calculate the center position for the glyph
                center_y = (y_top + y_bottom) / 2
                barline_height = y_bottom - y_top
                
                # Set font and draw the SMuFL glyph
                painter.setFont(self.bravura_font)
                
                # Scale the font size based on the staff height
                font_size = int(barline_height * 0.8)  # Adjust scale factor as needed
                font = QFont(self.bravura_font)
                font.setPointSize(font_size)
                painter.setFont(font)
                
                # Position adjustment: For end bar (uniE032), the thick line should be at x
                # The glyph has a thin line on the left and thick line on the right
                # We need to position the glyph so the thick line (right side) is at x
                glyph_width_estimate = font_size * 0.3  # Estimated glyph width
                adjusted_x = x - glyph_width_estimate  # Move glyph left so thick line is at x
                
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawText(QPointF(adjusted_x, center_y + font_size/4), '\uE032')  # SMuFL final barline
                print(f"BARLINES: Drew SMuFL end bar glyph at x={adjusted_x} (thick line at x={x}), center_y={center_y}")
            else:
                # Fallback: Draw manual final barline
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawLine(x - 6, y_top, x - 6, y_bottom)  # Thin line
                painter.setPen(QPen(QColor(0, 0, 0), 4))
                painter.drawLine(x, y_top, x, y_bottom)  # Thick line at specified x
                print(f"BARLINES: Drew manual end bar at x={x} (thick line), thin at x={x-6}")

        # Draw user-created barlines THROUGH EACH TOP-LEVEL GROUP (single, grand, section)
        # This ensures barlines pause between unrelated systems and fully span grand staves
        if rendering_order:
            for element in rendering_order:
                if hasattr(element, 'staves') and element.staves:
                    # Section: span from first to last staff
                    top_staff = element.staves[0]
                    bottom_staff = element.staves[-1]
                    top_y = top_staff.y_position
                    bottom_y = bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                    self._draw_single_barline(painter, barline_x, barline_type, top_y, bottom_y)
                    print(f"BARLINES: Drew {barline_type} barline across SECTION at x={barline_x} (y={top_y}→{bottom_y})")
                elif hasattr(element, 'is_grand_staff') and getattr(element, 'is_grand_staff', False) and hasattr(element, 'top_staff') and hasattr(element, 'bottom_staff'):
                    # Grand staff: span both staves
                    top_y = element.top_staff.y_position
                    bottom_y = element.bottom_staff.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                    self._draw_single_barline(painter, barline_x, barline_type, top_y, bottom_y)
                    print(f"BARLINES: Drew {barline_type} barline across GRAND STAFF at x={barline_x} (y={top_y}→{bottom_y})")
                else:
                    # Single staff
                    top_y = element.y_position
                    bottom_y = element.y_position + ((self.STAFF_LINE_COUNT - 1) * self.STAFF_LINE_SPACING)
                    self._draw_single_barline(painter, barline_x, barline_type, top_y, bottom_y)
                    print(f"BARLINES: Drew {barline_type} barline on SINGLE STAFF at x={barline_x} (y={top_y}→{bottom_y})")

    def _draw_single_barline(self, painter, barline_x, barline_type, top_y, bottom_y):
        """Draw a single barline of the specified type between the given y coordinates"""
        
        def draw_normal_barline(x, y_top, y_bottom, extension=0):
            """Helper function to draw a normal barline"""
            pen = QPen(Qt.GlobalColor.black, 1)
            painter.setPen(pen)
            line = QLineF(x, y_top - extension, x, y_bottom + extension)
            painter.drawLine(line)
            return line
            
        def draw_final_barline(x, y_top, y_bottom):
            # Always draw precise connecting final barline as two lines spanning the full group.
            # This guarantees the barline runs through both staves of a grand staff or all staves of a section.
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawLine(int(x - 6), int(y_top), int(x - 6), int(y_bottom))  # Thin line
            painter.setPen(QPen(QColor(0, 0, 0), 4))
            painter.drawLine(int(x), int(y_top), int(x), int(y_bottom))  # Thick line at specified x
            print(f"BARLINES: Drew manual end bar at x={x} (thick line), thin at x={x-6}")

        if barline_type == 'single':
            draw_normal_barline(barline_x, top_y, bottom_y)
        elif barline_type == 'double':
            # Draw two thin lines close together
            draw_normal_barline(barline_x - 2, top_y, bottom_y)
            draw_normal_barline(barline_x + 2, top_y, bottom_y)
        elif barline_type == 'final':
            draw_final_barline(barline_x, top_y, bottom_y)
        elif barline_type == 'dashed':
            # Draw dashed barline
            painter.save()
            pen = QPen(Qt.GlobalColor.black, 1)
            pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawLine(QLineF(barline_x, top_y, barline_x, bottom_y))
            painter.restore()
        elif barline_type == 'repeat_start':
            # Draw repeat start barline: thick line + thin line + dots (left to right)
            # Draw thick line first (leftmost)
            painter.save()
            thick_pen = QPen(Qt.GlobalColor.black, 3)
            painter.setPen(thick_pen)
            painter.drawLine(QLineF(barline_x, top_y, barline_x, bottom_y))
            painter.restore()
            # Draw thin line to the right
            draw_normal_barline(barline_x + 3, top_y, bottom_y)
            # Draw dots (will be handled by repeat dots rendering)
        elif barline_type == 'repeat_end':
            # Draw repeat end barline: dots + thin line + thick line (left to right)
            # Draw thin line first (leftmost)
            draw_normal_barline(barline_x - 3, top_y, bottom_y)
            # Draw thick line to the right
            painter.save()
            thick_pen = QPen(Qt.GlobalColor.black, 3)
            painter.setPen(thick_pen)
            painter.drawLine(QLineF(barline_x, top_y, barline_x, bottom_y))
            painter.restore()
            # Draw dots (will be handled by repeat dots rendering)
        elif barline_type == 'repeat_both':
            # Draw both repeat start and end with overlapping thick lines
            # The thick parts should completely overlap in the center
            
            # Draw the central thick line (overlapped thick parts)
            painter.save()
            thick_pen = QPen(Qt.GlobalColor.black, 3)
            painter.setPen(thick_pen)
            painter.drawLine(QLineF(barline_x, top_y, barline_x, bottom_y))
            painter.restore()
            
            # Draw thin line on the left (for repeat end)
            draw_normal_barline(barline_x - 3, top_y, bottom_y)
            
            # Draw thin line on the right (for repeat start)
            draw_normal_barline(barline_x + 3, top_y, bottom_y)
            
            # Draw dots (will be handled by repeat dots rendering)
        
        # Handle repeat dots for repeat barlines
        if barline_type in ['repeat_start', 'repeat_end', 'repeat_both']:
            self._draw_repeat_dots_for_barline(painter, barline_x, barline_type, top_y, bottom_y)

    def _render_barline_numbers(self, painter, measure, barline_x, rendering_order):
        """
        Render barline numbers if enabled in settings.
        
        Args:
            painter: QPainter instance
            measure: The measure object containing the barline
            barline_x: X position of the barline
            rendering_order: List of staves/sections for positioning
        """
        # CRITICAL FIX: Remove hardcoded color and properly load settings
        # Get settings with document precedence
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_numbering_enabled = self.document.settings.get("notation/barline_numbering", False)
            barline_font_size = int(self.document.settings.get("notation/barline_number_font_size", 8))
            barline_font_color = self.document.settings.get("notation/barline_numbers_font_color", "#666666")
            print(f"BARLINE_NUMBERS: Using DOCUMENT settings - enabled: {barline_numbering_enabled}, font_size: {barline_font_size}, color: {barline_font_color}")
        else:
            # Fallback to application preferences
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_numbering_enabled = settings.value("notation/barline_numbering", False, type=bool)
            barline_font_size = int(settings.value("notation/barline_number_font_size", 8))
            barline_font_color = settings.value("notation/barline_numbers_font_color", "#666666")
            print(f"BARLINE_NUMBERS: Using QSETTINGS fallback - enabled: {barline_numbering_enabled}, font_size: {barline_font_size}, color: {barline_font_color}")
        
        # DEBUG: Check what QSettings actually contains
        from PyQt6.QtCore import QSettings
        debug_settings = QSettings()
        actual_color = debug_settings.value("notation/barline_numbers_font_color", "NOT_FOUND")
        print(f"BARLINE_NUMBERS: QSettings actual color value: {actual_color}")
        
        # Skip if barline numbering is disabled
        if not barline_numbering_enabled:
            return
            
        # Get the barline number (measure number)
        barline_number = getattr(measure, 'measure_number', 1)
        
        # Skip barline 0 (system barline) - only show numbered barlines
        if barline_number == 0:
            return
            
        # Set up font for barline numbers
        painter.save()
        
        # Create font for barline numbers
        font = painter.font()
        font.setPointSize(barline_font_size)
        font.setBold(True)  # Make barline numbers bold for visibility
        painter.setFont(font)
        
        # Set color for barline numbers
        from PyQt6.QtGui import QColor
        painter.setPen(QColor(barline_font_color))
        
        # CRITICAL FIX: Position barline numbers at the same level as barline 0 and measure numbers
        # Use the same positioning logic as barline 0 number for consistency
        # ALWAYS use the actual top staff of the entire score system, not the top element in rendering order
        if hasattr(self.document, 'layout') and self.document.layout:
            # Get all staves to find the actual top staff
            all_staves = []
            
            # Add ungrouped staves
            if hasattr(self.document.layout, 'ungrouped_staves'):
                all_staves.extend(self.document.layout.ungrouped_staves)
            
            # Add staves from sections
            if hasattr(self.document.layout, 'sections'):
                for section in self.document.layout.sections:
                    if hasattr(section, 'staves'):
                        all_staves.extend(section.staves)
            
            if all_staves:
                # Find the actual top staff of the entire score system
                top_staff_y = min(staff.y_position for staff in all_staves if hasattr(staff, 'y_position'))
            else:
                # Fallback - use a reasonable default
                top_staff_y = 40
        else:
            # Fallback - use a reasonable default
            top_staff_y = 40
        
        # CRITICAL FIX: Use settings for barline number positioning
        # Get barline number offset settings with document precedence
        barline_number_vertical_offset = 0
        barline_number_horizontal_offset = 3
        
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_number_vertical_offset = self.document.settings.get("notation/barline_number_vertical_offset", 0)
            barline_number_horizontal_offset = self.document.settings.get("notation/barline_number_horizontal_offset", 3)
        else:
            # Fallback to application preferences
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_number_vertical_offset = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            barline_number_horizontal_offset = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
        
        # CRITICAL FIX: Force refresh settings from QSettings to ensure we get the latest values
        # This ensures barline numbers use the correct settings even if document settings are not set
        if barline_number_vertical_offset == 0 and barline_number_horizontal_offset == 3:
            # Try to get the actual values from QSettings
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            actual_vertical = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            actual_horizontal = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
            if actual_vertical != 0 or actual_horizontal != 3:
                barline_number_vertical_offset = actual_vertical
                barline_number_horizontal_offset = actual_horizontal
                print(f"BARLINE_NUMBERS: Refreshed settings from QSettings - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        
        # CRITICAL FIX: Use document settings first, then fall back to QSettings
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_number_vertical_offset = self.document.settings.get("notation/barline_number_vertical_offset", 0)
            barline_number_horizontal_offset = self.document.settings.get("notation/barline_number_horizontal_offset", 3)
            print(f"BARLINE_NUMBERS: Using document settings - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        else:
            # Fallback to QSettings
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_number_vertical_offset = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            barline_number_horizontal_offset = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
            print(f"BARLINE_NUMBERS: Using QSettings values - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        
        # Apply offset settings
        number_x = barline_x + barline_number_horizontal_offset
        # CRITICAL FIX: User's offset completely controls positioning relative to staff
        # No fixed offset - user controls everything through the offset spinners
        number_y = top_staff_y + barline_number_vertical_offset  # User's offset controls positioning
        
        print(f"BARLINE_NUMBERS: Using offsets - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        print(f"BARLINE_NUMBERS: Positioned barline number {barline_number} at ({number_x}, {number_y})")
        
        # Draw the barline number
        painter.drawText(int(number_x), int(number_y), str(barline_number))
        
        print(f"BARLINE_NUMBERS: Drew barline number {barline_number} at position ({number_x}, {number_y}) - same level as barline 0")
        
        painter.restore()

    def _render_barline_0_number(self, painter, barline_x, all_staves):
        """
        Render barline number 0 (system barline) if enabled in settings.
        
        Args:
            painter: QPainter instance
            barline_x: X position of barline 0
            all_staves: List of all staves for positioning
        """
        # CRITICAL FIX: Remove hardcoded color and properly load settings
        # Get settings with document precedence
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_numbering_enabled = self.document.settings.get("notation/barline_numbering", False)
            barline_font_size = int(self.document.settings.get("notation/barline_number_font_size", 8))
            barline_font_color = self.document.settings.get("notation/barline_numbers_font_color", "#666666")
        else:
            # Fallback to application preferences
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_numbering_enabled = settings.value("notation/barline_numbering", False, type=bool)
            barline_font_size = int(settings.value("notation/barline_number_font_size", 8))
            barline_font_color = settings.value("notation/barline_numbers_font_color", "#666666")
        
        print(f"BARLINE_0_NUMBERS: Settings loaded - enabled: {barline_numbering_enabled}, font_size: {barline_font_size}, color: {barline_font_color}")
        
        # Skip if barline numbering is disabled
        if not barline_numbering_enabled:
            return
            
        # Set up font for barline numbers
        painter.save()
        
        # Create font for barline numbers
        font = painter.font()
        font.setPointSize(barline_font_size)
        font.setBold(True)  # Make barline numbers bold for visibility
        painter.setFont(font)
        
        # Set color for barline numbers
        from PyQt6.QtGui import QColor
        painter.setPen(QColor(barline_font_color))
        
        # Calculate positioning for barline 0 number
        # Place number above the topmost staff ONLY; do not repeat for each system.
        # If we were passed multiple staves (grouped), still use the global topmost staff.
        if hasattr(self.document, 'layout') and hasattr(self.document.layout, 'staves') and self.document.layout.staves:
            global_top = self.document.layout.staves[0]
            if hasattr(global_top, 'is_grand_staff') and getattr(global_top, 'is_grand_staff', False) and hasattr(global_top, 'top_staff'):
                top_staff_y = global_top.top_staff.y_position
            else:
                top_staff_y = global_top.y_position
        else:
            # Fallback to the first provided staff
            if all_staves:
                top_staff = all_staves[0]
                if hasattr(top_staff, 'is_grand_staff') and top_staff.is_grand_staff and hasattr(top_staff, 'top_staff'):
                    top_staff_y = top_staff.top_staff.y_position
                else:
                    top_staff_y = top_staff.y_position
            else:
                top_staff_y = 40
        
        # CRITICAL FIX: Use settings for barline 0 number positioning
        # Get barline number offset settings with document precedence
        barline_number_vertical_offset = 0
        barline_number_horizontal_offset = 3
        
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_number_vertical_offset = self.document.settings.get("notation/barline_number_vertical_offset", 0)
            barline_number_horizontal_offset = self.document.settings.get("notation/barline_number_horizontal_offset", 3)
        else:
            # Fallback to application preferences
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_number_vertical_offset = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            barline_number_horizontal_offset = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
        
        # CRITICAL FIX: Force refresh settings from QSettings to ensure we get the latest values
        # This ensures barline numbers use the correct settings even if document settings are not set
        if barline_number_vertical_offset == 0 and barline_number_horizontal_offset == 3:
            # Try to get the actual values from QSettings
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            actual_vertical = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            actual_horizontal = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
            print(f"BARLINE_0_NUMBERS: QSettings values - vertical: {actual_vertical}, horizontal: {actual_horizontal}")
            if actual_vertical != 0 or actual_horizontal != 3:
                barline_number_vertical_offset = actual_vertical
                barline_number_horizontal_offset = actual_horizontal
                print(f"BARLINE_0_NUMBERS: Refreshed settings from QSettings - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        
        # CRITICAL FIX: Use document settings first, then fall back to QSettings
        if hasattr(self.document, 'settings') and self.document.settings:
            barline_number_vertical_offset = self.document.settings.get("notation/barline_number_vertical_offset", 0)
            barline_number_horizontal_offset = self.document.settings.get("notation/barline_number_horizontal_offset", 3)
            print(f"BARLINE_0_NUMBERS: Using document settings - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        else:
            # Fallback to QSettings
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            barline_number_vertical_offset = settings.value("notation/barline_number_vertical_offset", 0, type=int)
            barline_number_horizontal_offset = settings.value("notation/barline_number_horizontal_offset", 3, type=int)
            print(f"BARLINE_0_NUMBERS: Using QSettings values - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        
        # Apply offset settings
        number_x = barline_x + barline_number_horizontal_offset
        # CRITICAL FIX: User's offset completely controls positioning relative to staff
        # No fixed offset - user controls everything through the offset spinners
        number_y = top_staff_y + barline_number_vertical_offset  # User's offset controls positioning
        
        # Draw the barline number "0"
        painter.drawText(int(number_x), int(number_y), "0")
        
        print(f"BARLINE_NUMBERS: Drew barline number 0 at position ({number_x}, {number_y}) using offsets - vertical: {barline_number_vertical_offset}, horizontal: {barline_number_horizontal_offset}")
        
        painter.restore()
