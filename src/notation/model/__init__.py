"""
Music notation model for ONOTE.

This package contains the core classes for representing music notation
in a hierarchical structure inspired by the Music Encoding Initiative (MEI).
"""

from .base import MusicElement
from .score import Score, Section, StaffSystem
from .staves import Staff, GrandStaff, SingleStaff
from .notation import Note, Rest, Chord, Duration, Pitch, Clef, KeySignature, TimeSignature

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