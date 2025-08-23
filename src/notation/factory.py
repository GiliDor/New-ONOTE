"""
Factory functions for creating common music notation structures.
"""
from typing import Dict, List, Optional, Any, Union

from .model import (
    Score, Section, StaffSystem,
    SingleStaff, GrandStaff,
    Note, Rest, Chord, Duration, Pitch,
    Clef, KeySignature, TimeSignature
)


def create_empty_score(title: str = "New Score", composer: str = "") -> Score:
    """
    Create a new empty score.
    
    Args:
        title: The title of the score.
        composer: The composer of the score.
        
    Returns:
        A new Score instance.
    """
    return Score(title=title, composer=composer)


def create_piano_score(title: str = "Piano Score", composer: str = "") -> Score:
    """
    Create a new piano score with a grand staff.
    
    Args:
        title: The title of the score.
        composer: The composer of the score.
        
    Returns:
        A new Score instance with a piano grand staff.
    """
    score = Score(title=title, composer=composer)
    piano = GrandStaff(
        instrument_name="Piano",
        instrument_abbr="Pno.",
        upper_clef="treble",
        lower_clef="bass",
        key="C",
        time_signature="4/4"
    )
    score.add_staff_system(piano)
    return score


def create_string_quartet_score(title: str = "String Quartet", composer: str = "") -> Score:
    """
    Create a new string quartet score.
    
    Args:
        title: The title of the score.
        composer: The composer of the score.
        
    Returns:
        A new Score instance with a string quartet section.
    """
    score = Score(title=title, composer=composer)
    section = Section(name="Strings")
    score.add_section(section)
    
    violin1 = SingleStaff(
        instrument_name="Violin I",
        instrument_abbr="Vln. I",
        clef="treble",
        key="C",
        time_signature="4/4"
    )
    section.add_staff_system(violin1)
    
    violin2 = SingleStaff(
        instrument_name="Violin II",
        instrument_abbr="Vln. II",
        clef="treble",
        key="C",
        time_signature="4/4"
    )
    section.add_staff_system(violin2)
    
    viola = SingleStaff(
        instrument_name="Viola",
        instrument_abbr="Vla.",
        clef="alto",
        key="C",
        time_signature="4/4"
    )
    section.add_staff_system(viola)
    
    cello = SingleStaff(
        instrument_name="Violoncello",
        instrument_abbr="Vc.",
        clef="bass",
        key="C",
        time_signature="4/4"
    )
    section.add_staff_system(cello)
    
    return score


def parse_note_sequence(sequence: str) -> List[Union[Note, Rest, Chord]]:
    """
    Parse a sequence of notes, rests, and chords from a string.
    
    Format:
    - Single notes: "C4/4", "F#5/8.", etc. (pitch/duration)
    - Rests: "r/4", "r/8.", etc. (r/duration)
    - Chords: "[C4 E4 G4]/4", "[F#3 C4 F#4]/8.", etc. ([pitches]/duration)
    
    Args:
        sequence: The note sequence string.
        
    Returns:
        A list of Note, Rest, and Chord instances.
    """
    result = []
    tokens = sequence.split()
    
    for token in tokens:
        if token.startswith('r/'):
            # Rest
            duration_str = token[2:]
            rest = Rest(duration=Duration.from_string(duration_str))
            result.append(rest)
        elif token.startswith('[') and ']/' in token:
            # Chord
            chord_part, duration_part = token.split(']/')
            chord_part = chord_part[1:]  # Remove leading '['
            pitch_strs = chord_part.split()
            pitches = [Pitch.from_string(p) for p in pitch_strs]
            duration = Duration.from_string(duration_part)
            chord = Chord(pitches=pitches, duration=duration)
            result.append(chord)
        else:
            # Note
            note = Note.from_string(token)
            result.append(note)
    
    return result 