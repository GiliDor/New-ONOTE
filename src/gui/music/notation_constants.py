"""
Notation Constants - Musical notation constants for ONOTE

This module contains all the constants used for musical notation rendering,
including barline types, clef types, fonts, and sizing information.
"""

import json
import os
from pathlib import Path

# Units: all measurements in pixels unless specified

# Staff dimensions
STAFF_LINE_COUNT = 5
STAFF_LINE_SPACING = 10  # pixels between staff lines
STAFF_LINE_THICKNESS = 1.0  # pixels
STAFF_HEIGHT = (STAFF_LINE_COUNT - 1) * STAFF_LINE_SPACING  # height from bottom to top line

# A4 page dimensions and margins
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
MM_TO_PIXELS = 3.78  # Standard conversion at 96 DPI

# A4 page dimensions in pixels
A4_WIDTH_PIXELS = int(A4_WIDTH_MM * MM_TO_PIXELS)   # ≈ 794 pixels
A4_HEIGHT_PIXELS = int(A4_HEIGHT_MM * MM_TO_PIXELS)  # ≈ 1123 pixels

# A4 standard margins: 25mm left/right, 20mm top/bottom
A4_MARGIN_LEFT_MM = 25
A4_MARGIN_RIGHT_MM = 25
A4_MARGIN_TOP_MM = 20
A4_MARGIN_BOTTOM_MM = 20

# Page margins (in pixels) - A4 standard
DEFAULT_PAGE_MARGINS = {
    'left': int(A4_MARGIN_LEFT_MM * MM_TO_PIXELS),    # ≈ 95 pixels
    'right': int(A4_MARGIN_RIGHT_MM * MM_TO_PIXELS),  # ≈ 95 pixels
    'top': int(A4_MARGIN_TOP_MM * MM_TO_PIXELS),      # ≈ 76 pixels
    'bottom': int(A4_MARGIN_BOTTOM_MM * MM_TO_PIXELS) # ≈ 76 pixels
}

# Font settings
MUSIC_FONTS = {
    "default": "Bravura",  # Keep legacy key for compatibility
    "primary": "Bravura",
    "fallback": ["MusGlyphs", "Maestro", "Arial Unicode MS", "Arial"],
    "text": "Times New Roman",
    "monospace": "Courier New"
}

FONT_SIZES = {
    "staff": 20,          # Staff line text
    "measure": 12,        # Measure numbers
    "clef": 36,          # Clef symbols (increased from 24 for better visibility)
    "time": 24,          # Time signatures (increased from 16 for better visibility)
    "timeSignature": 24,  # Time signatures (alternative name, increased from 16)
    "key": 14,           # Key signatures
    "keySignature": 14,   # Key signatures (alternative name)
    "note": 18,          # Note heads
    "accidental": 14,    # Sharps, flats, naturals
    "dynamic": 12,       # Dynamic markings
    "tempo": 11,         # Tempo markings
    "text": 10,          # General text
    "title": 18,         # Score title
    "subtitle": 14,      # Score subtitle
    "composer": 12,      # Composer name
    "rehearsal": 14,     # Rehearsal letters/numbers
    "instrumentName": 10, # Instrument names
    "sectionName": 12,    # Section names (enhanced)
    "staffName": 10,      # Staff names (enhanced)
    "barline": 16,        # Barline symbols
    "musicalDirection": 11, # Musical direction text (D.C., D.S., etc.)
    "jump": 14            # Jump markings (segno, coda)
}

# Enhanced position constants for staff elements (NEW)
POSITION_CONSTANTS = {
    "staffName": {
        "fontSize": 10,
        "verticalOffset": -8,      # Pixels above staff
        "horizontalOffset": -50,   # Pixels left of staff start
        "fontWeight": "normal",
        "fontStyle": "normal"
    },
    "sectionName": {
        "fontSize": 12,
        "verticalOffset": -25,     # Pixels above staff group
        "horizontalOffset": -60,   # Pixels left of staff start
        "fontWeight": "bold",
        "fontStyle": "normal"
    },
    "timeSignature": {
        "fontSize": 24,
        "verticalOffset": 0,       # Centered on staff
        "horizontalOffset": 40,    # Pixels from left margin
        "numeratorOffset": 10,     # Pixels above center line
        "denominatorOffset": -10,  # Pixels below center line
        "spacing": 18              # Vertical spacing between numerator and denominator
    },
    "keySignature": {
        "fontSize": 14,
        "verticalOffset": 0,       # Centered on staff
        "horizontalOffset": 75,    # Pixels from left margin (after time sig)
        "accidentalSpacing": 12    # Horizontal spacing between accidentals
    },
    "barline": {
        "thickness": 1,
        "heightExtension": 2,      # Pixels above/below staff lines
        "spacing": 4               # For double barlines
    },
    "musicalDirection": {
        "fontSize": 11,
        "verticalOffset": 30,      # Pixels below staff
        "horizontalAlignment": "center",
        "fontWeight": "italic"
    }
}

# Symbol map for SMuFL-compatible fonts
SYMBOL_MAP = {
    # Clefs
    'trebleClef': '\uE050',
    'bassClef': '\uE062',
    'altoClef': '\uE05C',
    'tenorClef': '\uE05C',  # Same symbol as alto, different position
    'percussionClef': '\uE069',  # Percussion clef
    
    # Accidentals
    'sharp': '\uE262',
    'flat': '\uE260',
    'natural': '\uE261',
    'doubleSharp': '\uE263',
    'doubleFlat': '\uE264',
    
    # Staff brackets and braces
    'brace': '\uE000',  # Curly brace for grand staff
    'bracket': '\uE002',  # System bracket
    
    # Time signatures
    'commonTime': '\uE08A',  # C for 4/4
    'cutTime': '\uE08B',     # C with vertical line for 2/2
    '0': '\uE080',
    '1': '\uE081',
    '2': '\uE082',
    '3': '\uE083',
    '4': '\uE084',
    '5': '\uE085',
    '6': '\uE086',
    '7': '\uE087',
    '8': '\uE088',
    '9': '\uE089',
    
    # Noteheads
    'noteheadBlack': '\uE0A4',
    'noteheadHalf': '\uE0A3',
    'noteheadWhole': '\uE0A2',
    'noteheadDoubleWhole': '\uE0A1',
    
    # Rests
    'restWhole': '\uE4E3',
    'restHalf': '\uE4E4',
    'restQuarter': '\uE4E5',
    'rest8th': '\uE4E6',
    'rest16th': '\uE4E7',
    'rest32nd': '\uE4E8',
    'rest64th': '\uE4E9',
    
    # Flags
    'flag8thUp': '\uE240',
    'flag16thUp': '\uE242',
    'flag32ndUp': '\uE244',
    'flag64thUp': '\uE246',
    'flag8thDown': '\uE241',
    'flag16thDown': '\uE243',
    'flag32ndDown': '\uE245',
    'flag64thDown': '\uE247',
    
    # Dynamics
    'dynamicPiano': '\uE520',
    'dynamicMezzoPiano': '\uE521',
    'dynamicForte': '\uE522',
    'dynamicMezzoForte': '\uE523',
    'dynamicFortissimo': '\uE525',
    'dynamicPianissimo': '\uE526',
    'dynamicSforzando': '\uE527',
    
    # Articulations
    'articulationStaccato': '\uE4A0',
    'articulationAccent': '\uE4A2',
    'articulationTenuto': '\uE4A4',
    'articulationStaccatissimo': '\uE4A8',
    'articulationMarcato': '\uE4AC',
    
    # Barlines (Updated with proper SMuFL symbols)
    'barlineSingle': '\uE030',      # Single bar line
    'barlineDouble': '\uE031',      # Double bar line
    'barlineFinal': '\uE032',       # End bar
    'barlineDotted': '\uE036',      # Dotted bar line
    'barlineRepeatLeft': '\uE040',  # Repeat Start
    'barlineRepeatRight': '\uE041', # Repeat End
    'barlineRepeatBoth': '\uE042',  # Repeat End & Start
    
    # Musical directions and jumps (New additions)
    'segno': '\uE045',              # Segno symbol
    'coda': '\uE048',               # Coda symbol
    'dalSegno': '\uE045',           # D.S. (uses segno symbol)
    'daCapo': '\uE046',             # D.C.
    
    # Miscellaneous
    'tremolo1': '\uE220',
    'tremolo2': '\uE221',
    'tremolo3': '\uE222'
}

# Clef constants for positioning and rendering
CLEF_CONSTANTS = {
    "treble": {
        "symbol": "\U0001D11E",  # Unicode treble clef
        "position": 2,           # Staff line position (0=bottom)
        "name": "Treble Clef",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": 1.0          # Vertical offset for positioning
    },
    "bass": {
        "symbol": "\U0001D122",  # Unicode bass clef
        "position": 6,           # Staff line position
        "name": "Bass Clef",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": -1.0         # Vertical offset for positioning
    },
    "alto": {
        "symbol": "\U0001D11F",  # Unicode alto clef  
        "position": 4,           # Staff line position
        "name": "Alto Clef",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": 0.5          # Vertical offset for positioning
    },
    "tenor": {
        "symbol": "\U0001D120",  # Unicode tenor clef
        "position": 3,           # Staff line position
        "name": "Tenor Clef",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": 1.0          # Vertical offset for positioning
    },
    "percussion": {
        "symbol": "\U0001D125",  # Unicode percussion clef
        "position": 4,           # Staff line position
        "name": "Percussion Clef",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": 0.5          # Vertical offset for positioning
    },
    "grand": {
        "symbol": "",            # No single symbol for grand staff
        "position": 0,           # Special case
        "name": "Grand Staff",
        "offset": 10,            # Horizontal offset for positioning
        "y_offset": 0.0          # Vertical offset for positioning
    }
}

# Clef positioning data
CLEF_POSITIONS = {
    'treble': {
        'x_offset': 10,
        'y_offset': 1.0   # G clef centered on 4th line from bottom (where G sits)
    },
    'bass': {
        'x_offset': 10,
        'y_offset': -1.0  # F clef centered on 3rd line from bottom
    },
    'alto': {
        'x_offset': 10,
        'y_offset': 0.5   # C clef centered half a space below middle line
    },
    'tenor': {
        'x_offset': 10,
        'y_offset': 1.0   # C clef centered on 2nd line from top
    },
    'percussion': {
        'x_offset': 10,
        'y_offset': 0.5   # Percussion clef centered half a space below middle line
    }
}

# Barline constants (Enhanced with SMuFL symbols and form support)
BARLINE_CONSTANTS = {
    "normal": {  # Keep legacy key for compatibility
        "name": "Normal Barline", 
        "thickness": 1,
        "symbol": "|",
        "smufl": "\uE030",
        "description": "Standard normal barline"
    },
    "single": {
        "name": "Single Barline", 
        "thickness": 1,
        "symbol": "|",
        "smufl": "\uE030",
        "description": "Standard single barline"
    },
    "double": {
        "name": "Double Barline",
        "thickness": 2, 
        "symbol": "||",
        "smufl": "\uE031",
        "description": "Double barline for section ends"
    },
    "final": {
        "name": "Final Barline",
        "thickness": 3,
        "thicknessThin": 1,      # Thin line thickness for final barline
        "thicknessThick": 3,     # Thick line thickness for final barline
        "spacing": 4,            # Spacing between the two lines in final barline
        "symbol": "||:",
        "smufl": "\uE032",
        "description": "Final double barline at score end"
    },
    "dotted": {
        "name": "Dotted Barline",
        "thickness": 1,
        "symbol": ":",
        "smufl": "\uE036",
        "description": "Dotted barline for subdivisions"
    },
    "repeat_start": {
        "name": "Repeat Start",
        "thickness": 2,
        "symbol": "|:",
        "smufl": "\uE040",
        "description": "Start of repeated section"
    },
    "repeat_end": {
        "name": "Repeat End", 
        "thickness": 2,
        "symbol": ":|",
        "smufl": "\uE041",
        "description": "End of repeated section"
    },
    "repeat_both": {
        "name": "Repeat End & Start",
        "thickness": 2,
        "symbol": ":|:",
        "smufl": "\uE042", 
        "description": "End of one repeat and start of another"
    }
}

# Musical direction constants for jumps and navigation
MUSICAL_DIRECTION_CONSTANTS = {
    "segno": {
        "name": "Segno",
        "symbol": "𝄋",
        "smufl": "\uE045",
        "description": "Segno mark for D.S. references"
    },
    "coda": {
        "name": "Coda",
        "symbol": "𝄌",
        "smufl": "\uE048", 
        "description": "Coda mark for structural navigation"
    },
    "ds": {
        "name": "D.S.",
        "symbol": "D.S.",
        "smufl": "\uE045",  # Uses segno symbol
        "description": "Dal Segno - return to segno mark"
    },
    "dc": {
        "name": "D.C.", 
        "symbol": "D.C.",
        "smufl": "\uE046",
        "description": "Da Capo - return to beginning"
    },
    "fine": {
        "name": "Fine",
        "symbol": "Fine",
        "smufl": "",  # Text only
        "description": "End of piece marker"
    },
    "al_fine": {
        "name": "al Fine", 
        "symbol": "al Fine",
        "smufl": "",  # Text only
        "description": "Continue until Fine marking"
    },
    "al_coda": {
        "name": "al Coda",
        "symbol": "al Coda", 
        "smufl": "",  # Text only
        "description": "Continue until Coda marking"
    },
    "to_coda": {
        "name": "To Coda",
        "symbol": "To 𝄌",
        "smufl": "\uE048",  # Uses coda symbol
        "description": "Jump to Coda section"
    }
}

# Form layout constants for measure management
FORM_LAYOUT_CONSTANTS = {
    "default_measure_width": 160,
    "min_measure_width": 80,
    "max_measure_width": 400,
    "measures_per_system": 4,
    "dynamic_width_enabled": True,
    "auto_wrap_enabled": True,
    "justify_measures": True
}

# Bracket and brace constants
BRACKET_CONSTANTS = {
    'thickness': 2.0,         # Thickness of the bracket lines
    'extension': 3.0,         # How far the bracket extends from staff edges
    'horizontal_protrusion': 10.0,  # How far the bracket extends horizontally
    'inset': 5.0              # Distance from left margin
}

BRACE_CONSTANTS = {
    'width': 12.0,            # Width of the brace
    'font_size_ratio': 0.75,  # Ratio of brace height to font size
    'inset': 10.0,            # Distance from left margin
    'extension': 2.0          # How far the brace extends from staff edges
}

# Key signature constants
KEY_SIGNATURE_CONSTANTS = {
    'interAccidentalSpacing': 12,  # Space between accidentals
    
    # Order of accidentals for sharps and flats
    'sharpOrder': ['F', 'C', 'G', 'D', 'A', 'E', 'B'],
    'flatOrder': ['B', 'E', 'A', 'D', 'G', 'C', 'F'],
    
    # Y-positions of accidentals relative to staff lines based on clef
    'treblePositions': {
        'F': 0,       # 5th line (from bottom)
        'C': -0.5,    # 3rd space
        'G': -1.0,    # 2nd line
        'D': -1.5,    # 1st space
        'A': -2.0,    # Above the staff
        'E': -2.5,    # 3rd line
        'B': -3.0     # 4th space
    },
    'bassPositions': {
        'F': 2,       # 3rd space from bottom
        'C': 1.5,     # 2nd space from bottom
        'G': 1.0,     # 2nd line from bottom
        'D': 0.5,     # Bottom space
        'A': 0,       # 1st ledger line below staff
        'E': -0.5,    # 2nd ledger line below staff
        'B': -1.0     # 3rd ledger line below staff
    }
}

# Time signature constants (Enhanced with positioning)
TIME_SIGNATURE_CONSTANTS = {
    'x_offset': 40,         # Offset from left margin
    'numberOffset': 18,     # Vertical offset between numerator and denominator (increased for more visible spacing)
    'fontSize': 24,         # Font size for time signature numbers
    'verticalPosition': 0,  # Centered on staff (0 = middle line)
    'horizontalSpacing': 4, # Space between multiple time signatures
    'numeratorY': 10,       # Y offset for numerator (above center)
    'denominatorY': -10     # Y offset for denominator (below center)
}

# Note spacing constants
NOTE_SPACING_CONSTANTS = {
    'minimumSpacing': 15,  # Minimum horizontal spacing between notes
    'spacePerDuration': {
        'whole': 40,
        'half': 30,
        'quarter': 25,
        'eighth': 20,
        'sixteenth': 15,
        'thirtysecond': 12
    }
}

# Ledger line constants
LEDGER_LINE_CONSTANTS = {
    'thickness': 1.0,
    'extent': 6.0  # How far ledger lines extend past the notehead
}

# Stem constants
STEM_CONSTANTS = {
    'thickness': 1.0,
    'defaultStemUp': 35,
    'defaultStemDown': 35,
    'minStemLength': 20,
    'maxStemLength': 45
}

# Flag constants
FLAG_CONSTANTS = {
    'offset': 1.0  # Small offset for proper positioning
}

# Beam constants
BEAM_CONSTANTS = {
    'thickness': 4.0,
    'spacing': 5.0,  # Spacing between multiple beams
    'minSlope': 0.1,
    'maxSlope': 0.5
}

# Articulation constants
ARTICULATION_CONSTANTS = {
    'staccatoOffset': 8.0,
    'accentOffset': 9.0,
    'tenutoOffset': 6.0,
    'marcatoOffset': 12.0,
    'fermataOffset': 14.0
}

# Dynamic constants
DYNAMIC_CONSTANTS = {
    'defaultY': 8.0,  # Default distance below bottom staff line
    'textSize': 16
}

# System spacing constants
SYSTEM_CONSTANTS = {
    'defaultSpacing': 80,        # Default space between systems
    'grandStaffSpacing': 0.8,    # Spacing factor for grand staff (relative to STAFF_LINE_SPACING)
    'bracketWidth': 8,           # Width of a staff bracket
    'systemStartIndent': 10,     # Indent for system excluding first one
    'firstSystemIndent': 20      # Extra indent for first system
}

# Spacing measurements
DEFAULT_STAFF_SPACING = 50  # Default space between staves
DEFAULT_SYSTEM_SPACING = 80  # Default space between systems

# Sizing relative to staff
# These are ratios relative to staff height for consistent scaling
SIZING_RATIOS = {
    'noteheadDiameter': 0.8,  # Ratio of notehead diameter to space between staff lines
    'stemThickness': 0.12,    # Stem thickness relative to staff height
    'stemLength': 3.5,        # Stem length in staff spaces
    'beamThickness': 0.5,     # Beam thickness relative to staff space
    'staffLineSpacing': 1.0,  # Staff line spacing (1.0 = standard)
}

# Layout settings
DEFAULT_MEASURES_PER_SYSTEM = 4
DEFAULT_MEASURE_WIDTH = 160  # Default width of a measure 

# Get the configuration directory for saving settings
def get_config_dir():
    """Get the user's configuration directory for ONOTE"""
    home_dir = str(Path.home())
    config_dir = os.path.join(home_dir, '.onote')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir

# Constants file path
CONFIG_FILE = os.path.join(get_config_dir(), 'notation_constants.json')

# Functions to save defaults

def save_all_constants_to_disk():
    """Save all notation constants to a JSON configuration file"""
    try:
        # Create a dictionary with all constants
        constants_dict = {
            'STAFF_LINE_SPACING': STAFF_LINE_SPACING,
            'STAFF_LINE_THICKNESS': STAFF_LINE_THICKNESS,
            'STAFF_LINE_COUNT': STAFF_LINE_COUNT,
            'STAFF_HEIGHT': STAFF_HEIGHT,
            'DEFAULT_PAGE_MARGINS': DEFAULT_PAGE_MARGINS,
            'FONT_SIZES': FONT_SIZES,
            'CLEF_POSITIONS': CLEF_POSITIONS,
            'CLEF_CONSTANTS': CLEF_CONSTANTS,
            'BARLINE_CONSTANTS': BARLINE_CONSTANTS,
            'TIME_SIGNATURE_CONSTANTS': TIME_SIGNATURE_CONSTANTS,
            'KEY_SIGNATURE_CONSTANTS': KEY_SIGNATURE_CONSTANTS,
            'BRACKET_CONSTANTS': BRACKET_CONSTANTS,
            'BRACE_CONSTANTS': BRACE_CONSTANTS
        }
        
        # Save to JSON file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(constants_dict, f, indent=2)
        
        print(f"Saved all notation constants to {CONFIG_FILE}")
        return True
    except Exception as e:
        print(f"Error saving notation constants: {e}")
        return False

def load_constants_from_disk():
    """Load notation constants from JSON configuration file if it exists"""
    global STAFF_LINE_SPACING, STAFF_LINE_THICKNESS, STAFF_LINE_COUNT, STAFF_HEIGHT
    global DEFAULT_PAGE_MARGINS, FONT_SIZES, CLEF_POSITIONS, CLEF_CONSTANTS
    global BARLINE_CONSTANTS, TIME_SIGNATURE_CONSTANTS, KEY_SIGNATURE_CONSTANTS
    global BRACKET_CONSTANTS, BRACE_CONSTANTS
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                constants_dict = json.load(f)
            
            # Update all constants from the loaded dictionary
            if 'STAFF_LINE_SPACING' in constants_dict:
                STAFF_LINE_SPACING = constants_dict['STAFF_LINE_SPACING']
            if 'STAFF_LINE_THICKNESS' in constants_dict:
                STAFF_LINE_THICKNESS = constants_dict['STAFF_LINE_THICKNESS']
            if 'STAFF_LINE_COUNT' in constants_dict:
                STAFF_LINE_COUNT = constants_dict['STAFF_LINE_COUNT']
            if 'STAFF_HEIGHT' in constants_dict:
                STAFF_HEIGHT = constants_dict['STAFF_HEIGHT']
            if 'DEFAULT_PAGE_MARGINS' in constants_dict:
                DEFAULT_PAGE_MARGINS.update(constants_dict['DEFAULT_PAGE_MARGINS'])
            if 'FONT_SIZES' in constants_dict:
                FONT_SIZES.update(constants_dict['FONT_SIZES'])
            if 'CLEF_POSITIONS' in constants_dict:
                for clef, settings in constants_dict['CLEF_POSITIONS'].items():
                    if clef in CLEF_POSITIONS:
                        CLEF_POSITIONS[clef].update(settings)
            if 'CLEF_CONSTANTS' in constants_dict:
                for clef, settings in constants_dict['CLEF_CONSTANTS'].items():
                    if clef in CLEF_CONSTANTS:
                        CLEF_CONSTANTS[clef].update(settings)
            if 'BARLINE_CONSTANTS' in constants_dict:
                for barline_type, settings in constants_dict['BARLINE_CONSTANTS'].items():
                    if barline_type in BARLINE_CONSTANTS:
                        BARLINE_CONSTANTS[barline_type].update(settings)
            if 'TIME_SIGNATURE_CONSTANTS' in constants_dict:
                TIME_SIGNATURE_CONSTANTS.update(constants_dict['TIME_SIGNATURE_CONSTANTS'])
            if 'KEY_SIGNATURE_CONSTANTS' in constants_dict:
                for key, value in constants_dict['KEY_SIGNATURE_CONSTANTS'].items():
                    if key in KEY_SIGNATURE_CONSTANTS and not isinstance(KEY_SIGNATURE_CONSTANTS[key], list):
                        KEY_SIGNATURE_CONSTANTS[key] = value
            if 'BRACKET_CONSTANTS' in constants_dict:
                BRACKET_CONSTANTS.update(constants_dict['BRACKET_CONSTANTS'])
            if 'BRACE_CONSTANTS' in constants_dict:
                BRACE_CONSTANTS.update(constants_dict['BRACE_CONSTANTS'])
            
            print(f"Loaded notation constants from {CONFIG_FILE}")
            return True
    except Exception as e:
        print(f"Error loading notation constants: {e}")
    return False

# Try to load constants from disk at module initialization
load_constants_from_disk()

def save_staff_defaults(settings):
    """Save staff-related settings as defaults"""
    global STAFF_LINE_SPACING, STAFF_LINE_THICKNESS, STAFF_LINE_COUNT
    
    if 'staff_line_spacing' in settings:
        STAFF_LINE_SPACING = settings['staff_line_spacing']
    
    if 'staff_line_thickness' in settings:
        STAFF_LINE_THICKNESS = settings['staff_line_thickness']
    
    if 'staff_line_count' in settings:
        STAFF_LINE_COUNT = settings['staff_line_count']
    
    # Recalculate dependent values
    global STAFF_HEIGHT
    STAFF_HEIGHT = (STAFF_LINE_COUNT - 1) * STAFF_LINE_SPACING
    
    # Print information about the update
    print(f"Saved staff defaults: spacing={STAFF_LINE_SPACING}, thickness={STAFF_LINE_THICKNESS}, count={STAFF_LINE_COUNT}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_margins_defaults(margins):
    """Save margin settings as defaults"""
    global DEFAULT_PAGE_MARGINS
    
    for key, value in margins.items():
        if key in DEFAULT_PAGE_MARGINS:
            DEFAULT_PAGE_MARGINS[key] = value
    
    # Print information about the update
    print(f"Saved margin defaults: {DEFAULT_PAGE_MARGINS}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_font_defaults(font_sizes):
    """Save font size settings as defaults"""
    global FONT_SIZES
    
    for key, value in font_sizes.items():
        if key in FONT_SIZES:
            FONT_SIZES[key] = value
    
    # Print information about the update
    print(f"Saved font size defaults")
    
    # Save to disk
    save_all_constants_to_disk()

def save_clef_position_defaults(clef_name, settings):
    """Save position settings for a specific clef as defaults"""
    global CLEF_POSITIONS
    
    if clef_name in CLEF_POSITIONS:
        for key, value in settings.items():
            if key in CLEF_POSITIONS[clef_name]:
                CLEF_POSITIONS[clef_name][key] = value
    
    # Print information about the update
    print(f"Saved position defaults for {clef_name} clef: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_clef_defaults(clef_name, settings):
    """Save settings for a specific clef as defaults (updates both position and constants)"""
    global CLEF_POSITIONS, CLEF_CONSTANTS
    
    if clef_name in CLEF_POSITIONS:
        for key, value in settings.items():
            if key in CLEF_POSITIONS[clef_name]:
                CLEF_POSITIONS[clef_name][key] = value
                
                # Synchronize with CLEF_CONSTANTS for y position
                if key == 'y_offset' and clef_name in CLEF_CONSTANTS:
                    # Convert staff space offset to y_offset in pixels
                    # This is a critical step to ensure rendering uses updated values
                    if clef_name == 'treble':
                        CLEF_CONSTANTS[clef_name]['y_offset'] = 7 + (value * STAFF_LINE_SPACING / 2)
                    elif clef_name == 'bass':
                        CLEF_CONSTANTS[clef_name]['y_offset'] = 3 + (value * STAFF_LINE_SPACING / 2)
                    elif clef_name == 'alto':
                        CLEF_CONSTANTS[clef_name]['y_offset'] = 7 + (value * STAFF_LINE_SPACING / 2)
                    elif clef_name == 'tenor':
                        CLEF_CONSTANTS[clef_name]['y_offset'] = 8.5 + (value * STAFF_LINE_SPACING / 2)
                    
                    print(f"Updated rendering y_offset for {clef_name} clef to {CLEF_CONSTANTS[clef_name]['y_offset']}")
    
    # Print information about the update
    print(f"Saved defaults for {clef_name} clef: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_barline_defaults(barline_type, settings):
    """Save settings for a specific barline type as defaults"""
    global BARLINE_CONSTANTS
    
    if barline_type in BARLINE_CONSTANTS:
        for key, value in settings.items():
            if key in BARLINE_CONSTANTS[barline_type]:
                BARLINE_CONSTANTS[barline_type][key] = value
    
    # Print information about the update
    print(f"Saved defaults for {barline_type} barline: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_time_sig_defaults(settings):
    """Save time signature settings as defaults"""
    global TIME_SIGNATURE_CONSTANTS
    
    for key, value in settings.items():
        if key in TIME_SIGNATURE_CONSTANTS:
            TIME_SIGNATURE_CONSTANTS[key] = value
    
    # Print information about the update
    print(f"Saved time signature defaults: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_key_sig_defaults(settings):
    """Save key signature settings as defaults"""
    global KEY_SIGNATURE_CONSTANTS
    
    if 'interAccidentalSpacing' in settings:
        KEY_SIGNATURE_CONSTANTS['interAccidentalSpacing'] = settings['interAccidentalSpacing']
    
    # Print information about the update
    print(f"Saved key signature defaults: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_bracket_defaults(settings):
    """Save bracket settings as defaults"""
    global BRACKET_CONSTANTS
    
    for key, value in settings.items():
        if key in BRACKET_CONSTANTS:
            BRACKET_CONSTANTS[key] = value
    
    # Print information about the update
    print(f"Saved bracket defaults: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_brace_defaults(settings):
    """Save brace settings as defaults"""
    global BRACE_CONSTANTS
    
    for key, value in settings.items():
        if key in BRACE_CONSTANTS:
            BRACE_CONSTANTS[key] = value
    
    # Print information about the update
    print(f"Saved brace defaults: {settings}")
    
    # Save to disk
    save_all_constants_to_disk()

def save_clef_constants_defaults(clef_name, settings):
    """Save clef constants settings as defaults"""
    global CLEF_CONSTANTS, CLEF_POSITIONS
    
    if clef_name in CLEF_CONSTANTS:
        for key, value in settings.items():
            if key in CLEF_CONSTANTS[clef_name]:
                CLEF_CONSTANTS[clef_name][key] = value
                
                # If y_offset is changed in CLEF_CONSTANTS, also update CLEF_POSITIONS
                if key == 'y_offset' and clef_name in CLEF_POSITIONS:
                    # Convert pixel offset to staff space offset
                    if clef_name == 'treble':
                        CLEF_POSITIONS[clef_name]['y_offset'] = (value - 7) * 2 / STAFF_LINE_SPACING
                    elif clef_name == 'bass':
                        CLEF_POSITIONS[clef_name]['y_offset'] = (value - 3) * 2 / STAFF_LINE_SPACING
                    elif clef_name == 'alto':
                        CLEF_POSITIONS[clef_name]['y_offset'] = (value - 7) * 2 / STAFF_LINE_SPACING
                    elif clef_name == 'tenor':
                        CLEF_POSITIONS[clef_name]['y_offset'] = (value - 8.5) * 2 / STAFF_LINE_SPACING
                    
                    print(f"Updated CLEF_POSITIONS y_offset for {clef_name} to {CLEF_POSITIONS[clef_name]['y_offset']}")
    
    # Print information about the update
    print(f"Saved clef constants defaults for {clef_name}: {settings}")
    
    # Save to disk
    save_all_constants_to_disk() 