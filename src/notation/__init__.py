"""
Music notation package for ONOTE.
"""

# Import version from main package
from .. import __version__

from .model import (
    MusicElement,
    Score, Section, StaffSystem,
    Staff, GrandStaff, SingleStaff,
    Note, Rest, Chord, Duration, Pitch,
    Clef, KeySignature, TimeSignature
)

__all__ = [
    'MusicElement',
    'Score',
    'Section',
    'StaffSystem',
    'Staff',
    'GrandStaff',
    'SingleStaff',
    'Note',
    'Rest',
    'Chord',
    'Duration',
    'Pitch',
    'Clef',
    'KeySignature',
    'TimeSignature',
] 