"""
Simple test script for the music notation model.
"""
import json
from pprint import pprint

from .model import (
    Score, Section, StaffSystem,
    SingleStaff, GrandStaff,
    Note, Rest, Chord, Duration, Pitch,
    Clef, KeySignature, TimeSignature
)
from .factory import (
    create_empty_score,
    create_piano_score,
    create_string_quartet_score,
    parse_note_sequence
)


def test_piano_score():
    """Test creating a piano score."""
    score = create_piano_score("Test Piano Score", "Composer Name")
    
    # Verify the structure
    print(f"Score: {score.title} by {score.composer}")
    print(f"Ungrouped staves: {len(score.ungrouped_staves)}")
    
    # Access the piano staff
    piano = score.ungrouped_staves[0]
    print(f"Instrument: {piano.instrument_name} ({piano.instrument_abbr})")
    print(f"Upper staff clef: {piano.upper_staff.clef}")
    print(f"Lower staff clef: {piano.lower_staff.clef}")
    
    # Serialize to dict
    score_dict = score.to_dict()
    print("\nSerialized score (truncated):")
    print(json.dumps(score_dict, indent=2)[:500] + "...")
    
    return score


def test_string_quartet():
    """Test creating a string quartet score."""
    score = create_string_quartet_score("Test String Quartet", "Composer Name")
    
    # Verify the structure
    print(f"Score: {score.title} by {score.composer}")
    print(f"Sections: {len(score.sections)}")
    
    # Access the strings section
    strings = score.sections[0]
    print(f"Section: {strings.name}")
    print(f"Staves in section: {len(strings.staves)}")
    
    for i, staff in enumerate(strings.staves):
        print(f"Staff {i+1}: {staff.instrument_name} ({staff.instrument_abbr}), Clef: {staff.staff.clef}")
    
    return score


def test_note_parsing():
    """Test parsing note sequences."""
    sequence = "C4/4 D4/8 E4/8 r/4 [C4 E4 G4]/4 F4/8. G4/16"
    notes = parse_note_sequence(sequence)
    
    print(f"Parsed {len(notes)} notes from sequence:")
    for i, note in enumerate(notes):
        if isinstance(note, Note):
            print(f"{i+1}: Note - Pitch: {note.pitch}, Duration: {note.duration.value}/{note.duration.dots}")
        elif isinstance(note, Rest):
            print(f"{i+1}: Rest - Duration: {note.duration.value}/{note.duration.dots}")
        elif isinstance(note, Chord):
            pitches = ", ".join(str(p) for p in note.pitches)
            print(f"{i+1}: Chord - Pitches: [{pitches}], Duration: {note.duration.value}/{note.duration.dots}")
    
    return notes


def run_tests():
    """Run all tests."""
    print("=== Testing Piano Score ===")
    test_piano_score()
    print("\n=== Testing String Quartet ===")
    test_string_quartet()
    print("\n=== Testing Note Parsing ===")
    test_note_parsing()


if __name__ == "__main__":
    run_tests() 