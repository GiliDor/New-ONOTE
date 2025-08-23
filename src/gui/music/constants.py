"""
Constants for music notation display using Bravura font.
Based on SMuFL (Standard Music Font Layout) specifications.
"""

# Font settings
BRAVURA_FONT_SIZE = 24  # Base size for Bravura font
STAFF_LINE_SPACING = 8  # Space between staff lines
STAFF_SPACING = 40     # Space between staves

# Staff dimensions (in pixels)
STAFF_HEIGHT = 4 * STAFF_LINE_SPACING  # Height of a single staff
STAFF_LINE_THICKNESS = 1  # Thickness of staff lines

# Margins
LEFT_MARGIN = 50
RIGHT_MARGIN = 50
TOP_MARGIN = 20
BOTTOM_MARGIN = 20

# Clef dimensions
CLEF_WIDTH = 30  # Width of clef symbols
CLEF_HEIGHT = 50  # Height of clef symbols

# Symbol positions (relative to staff)
CLEF_POSITION = {
    'treble': {'x': LEFT_MARGIN, 'y': 0},  # G clef
    'bass': {'x': LEFT_MARGIN, 'y': 0},    # F clef
    'alto': {'x': LEFT_MARGIN, 'y': 0},    # C clef
    'tenor': {'x': LEFT_MARGIN, 'y': 0}    # C clef
}

KEY_SIGNATURE_POSITION = {
    'x': LEFT_MARGIN + 40,  # Position after clef
    'y': 0
}

TIME_SIGNATURE_POSITION = {
    'x': LEFT_MARGIN + 80,  # Position after key signature
    'y': 0
}

# Unicode symbols for Bravura font
SYMBOLS = {
    'clefs': {
        'treble': '𝄞',  # G clef
        'bass': '𝄢',    # F clef
        'alto': '𝄡',    # C clef
        'tenor': '𝄡'    # C clef (same symbol as alto)
    },
    'accidentals': {
        'sharp': '♯',
        'flat': '♭',
        'natural': '♮',
        'double_sharp': '𝄪',
        'double_flat': '𝄫'
    }
} 