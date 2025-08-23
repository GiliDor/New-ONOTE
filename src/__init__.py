"""
ONOTE - Object-Oriented Music Notation Software
Central version management and package initialization.
"""

# =============================================================================
# VERSION INFORMATION
# =============================================================================

# Current version - This is the single source of truth for ONOTE version
__version__ = "2.0.0"

# Version metadata
VERSION_INFO = {
    'major': 2,
    'minor': 0,
    'patch': 0,
    'release': 'stable',
    'build': '2024.12.19',
    'codename': 'Multi-Window Architecture',
    'description': 'Major architectural update with multi-window support and enhanced layout system'
}

# Version history
VERSION_HISTORY = {
    '2.0.0': {
        'date': '2024-12-19',
        'codename': 'Multi-Window Architecture',
        'changes': [
            'Multi-window model implementation',
            'Independent document windows',
            'Enhanced page layout system',
            'Improved dynamic resizing',
            'Architectural restructure'
        ]
    },
    '1.3.0': {
        'date': '2024-12-18',
        'codename': 'Barline System Restructure',
        'changes': [
            'Complete barline system rebuild',
            'Dynamic proportional spacing',
            'Enhanced measure numbering',
            'Improved undo/redo system'
        ]
    },
    '1.2.0': {
        'date': '2024-12-17',
        'codename': 'Section Ordering Fix',
        'changes': [
            'Fixed section ordering issues',
            'Enhanced form widget functionality',
            'Improved dialog synchronization'
        ]
    },
    '1.1.0': {
        'date': '2024-12-16',
        'codename': 'Form Widget Enhancement',
        'changes': [
            'Enhanced musical form dialog',
            'Improved radio button behavior',
            'Better layout management'
        ]
    },
    '1.0.0': {
        'date': '2024-12-15',
        'codename': 'Initial Release',
        'changes': [
            'Core music notation functionality',
            'Staff view and rendering',
            'Basic file operations',
            'Score setup system'
        ]
    },
    '0.1.0': {
        'date': '2024-12-14',
        'codename': 'Alpha',
        'changes': [
            'Initial development version',
            'Basic framework implementation'
        ]
    }
}

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get detailed version information."""
    return VERSION_INFO.copy()

def get_version_history():
    """Get the complete version history."""
    return VERSION_HISTORY.copy()

def get_version_string():
    """Get a formatted version string with metadata."""
    info = VERSION_INFO
    return f"{__version__} ({info['codename']}) - {info['build']}"

def is_development_version():
    """Check if this is a development version."""
    return VERSION_INFO['release'] == 'development'

def is_stable_version():
    """Check if this is a stable version."""
    return VERSION_INFO['release'] == 'stable'

# =============================================================================
# PACKAGE INITIALIZATION
# =============================================================================

# Import core modules
from . import gui
from . import notation
from . import core
from . import midi
from . import audio
from . import plugins

__all__ = [
    '__version__',
    'get_version',
    'get_version_info', 
    'get_version_history',
    'get_version_string',
    'is_development_version',
    'is_stable_version',
    'gui',
    'notation',
    'core',
    'midi',
    'audio',
    'plugins'
]
