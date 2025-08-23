"""
Classes for representing music notation elements.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import re

from .base import MusicElement


class Duration:
    """
    Represents a musical duration.
    
    Durations are represented as a combination of a base value (1, 2, 4, 8, 16, etc.)
    and a dot count (0, 1, 2, etc.).
    """
    
    def __init__(self, value: int = 4, dots: int = 0):
        """
        Initialize a Duration.
        
        Args:
            value: The base duration value (1 = whole, 2 = half, 4 = quarter, etc.).
            dots: The number of dots (each dot extends the duration by half).
        """
        self.value = value
        self.dots = dots
    
    @property
    def as_fraction(self) -> Tuple[int, int]:
        """
        Get the duration as a fraction (numerator, denominator).
        
        Returns:
            A tuple (numerator, denominator) representing the duration.
        """
        # Calculate the base duration
        numerator = 1
        denominator = self.value
        
        # Add dots (each dot adds half the previous value)
        if self.dots > 0:
            dot_factor_num = 2 ** self.dots - 1
            dot_factor_den = 2 ** self.dots
            numerator = numerator * dot_factor_den + dot_factor_num
            denominator = denominator * dot_factor_den
        
        return (numerator, denominator)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'value': self.value,
            'dots': self.dots
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Duration':
        """Create from dictionary representation."""
        return cls(
            value=data.get('value', 4),
            dots=data.get('dots', 0)
        )
    
    @classmethod
    def from_string(cls, duration_str: str) -> 'Duration':
        """
        Create a Duration from a string representation.
        
        Args:
            duration_str: A string like "4", "2.", "16..", etc.
            
        Returns:
            A Duration instance.
        """
        # Count the dots
        dots = duration_str.count('.')
        
        # Remove the dots to get the base value
        base_str = duration_str.replace('.', '')
        
        try:
            value = int(base_str)
            return cls(value=value, dots=dots)
        except ValueError:
            # Default to quarter note if parsing fails
            return cls(value=4, dots=0)

    @classmethod
    def from_ticks(cls, ticks: int, ppqn: int = 480) -> 'Duration':
        """
        Converts a duration in MIDI ticks to a Duration object (value and dots).
        Tries to find the simplest representation (largest base unit with fewest dots).

        Args:
            ticks: The duration in MIDI ticks.
            ppqn: Pulses Per Quarter Note (ticks per quarter note).

        Returns:
            A Duration object.
        """
        if ticks <= 0:
            # Or raise error, or return a default? For now, a very short duration if supported.
            # Smallest common value is 64th note. If less, it's problematic.
            # Let's default to a 64th if ticks are positive but too small for other logic.
            # If ticks is zero or negative, it is an error or a grace note context not handled here.
            print(f"Warning: Duration.from_ticks received non-positive ticks: {ticks}. Returning 64th.")
            return cls(value=64, dots=0) 

        # (ticks_value, (duration_value, num_dots))
        # Sorted by ticks_value descending to find the largest component first.
        # These values should be integers after calculation.
        known_tick_mappings = sorted([
            (int(round(4.0   * ppqn)),   (1, 0)),  # Whole
            (int(round(2.0   * ppqn * 1.75)), (2, 2)),  # Dbl Dotted Half
            (int(round(2.0   * ppqn * 1.5)),  (2, 1)),  # Dotted Half
            (int(round(2.0   * ppqn)),   (2, 0)),  # Half
            (int(round(1.0   * ppqn * 1.75)), (4, 2)),  # Dbl Dotted Quarter
            (int(round(1.0   * ppqn * 1.5)),  (4, 1)),  # Dotted Quarter
            (int(round(1.0   * ppqn)),   (4, 0)),  # Quarter
            (int(round(0.5   * ppqn * 1.75)), (8, 2)),  # Dbl Dotted Eighth
            (int(round(0.5   * ppqn * 1.5)),  (8, 1)),  # Dotted Eighth
            (int(round(0.5   * ppqn)),   (8, 0)),  # Eighth
            (int(round(0.25  * ppqn * 1.75)), (16, 2)), # Dbl Dotted 16th
            (int(round(0.25  * ppqn * 1.5)),  (16, 1)), # Dotted 16th
            (int(round(0.25  * ppqn)),   (16, 0)), # 16th
            (int(round(0.125 * ppqn * 1.75)), (32, 2)), # Dbl Dotted 32nd
            (int(round(0.125 * ppqn * 1.5)),  (32, 1)), # Dotted 32nd
            (int(round(0.125 * ppqn)),   (32, 0)), # 32nd
            (int(round(0.0625* ppqn * 1.75)), (64, 2)), # Dbl Dotted 64th
            (int(round(0.0625* ppqn * 1.5)),  (64, 1)), # Dotted 64th
            (int(round(0.0625* ppqn)),   (64, 0))  # 64th
        ], key=lambda item: item[0], reverse=True)

        for tick_val, (dur_val, num_dots) in known_tick_mappings:
            # Use a small tolerance for float comparisons if ppqn or multipliers lead to float tick_val
            if abs(ticks - tick_val) < 1e-3: # Match if very close
                return cls(value=dur_val, dots=num_dots)
        
        print(f"Warning: Duration.from_ticks could not find an exact standard match for {ticks} ticks (ppqn={ppqn}). Defaulting to a quarter note.")
        return cls(value=4, dots=0) # Default if no specific match found

    def to_ticks(self, ppqn: int = 480) -> int:
        """
        Converts this Duration object (value and dots) to MIDI ticks.

        Args:
            ppqn: Pulses Per Quarter Note (ticks per quarter note).

        Returns:
            The duration in MIDI ticks.
        """
        if self.value == 0: # Avoid division by zero for invalid duration value
            return 0

        # Calculate base ticks for the note value
        # e.g., if value is 4 (quarter), base_duration_is_X_quarter_notes = 1.0
        # if value is 2 (half), base_duration_is_X_quarter_notes = 2.0
        # if value is 8 (eighth), base_duration_is_X_quarter_notes = 0.5
        base_duration_as_quarter_notes = 4.0 / self.value
        base_ticks = base_duration_as_quarter_notes * ppqn

        # Apply dots
        total_ticks = base_ticks
        dot_multiplier = 0.5
        for _ in range(self.dots):
            total_ticks += base_ticks * dot_multiplier
            dot_multiplier /= 2
            
        return int(round(total_ticks))

    def __repr__(self):
        return f"Duration({self.value}, {self.dots})"


class Accidental(Enum):
    """Enum for various accidentals."""
    DOUBLE_FLAT = "bb"
    FLAT = "b"
    NATURAL = ""
    SHARP = "#"
    DOUBLE_SHARP = "##"


class Pitch:
    """
    Represents a musical pitch.
    
    Pitches are represented as a combination of a note name (C, D, E, etc.),
    an accidental (flat, natural, sharp, etc.), and an octave number.
    """
    
    PITCH_REGEX = re.compile(r'^([A-Ga-g])([#b]*)(\d+)?$')
    
    def __init__(
        self,
        note_name: str = 'C',
        accidental: Union[Accidental, str] = Accidental.NATURAL,
        octave: int = 4
    ):
        """
        Initialize a Pitch.
        
        Args:
            note_name: The note name (C, D, E, F, G, A, B).
            accidental: The accidental (flat, natural, sharp, etc.).
            octave: The octave number (4 = middle C octave).
        """
        self.note_name = note_name.upper()
        
        if isinstance(accidental, str):
            # Convert string to Accidental enum
            for acc in Accidental:
                if acc.value == accidental:
                    self.accidental = acc
                    break
            else:
                self.accidental = Accidental.NATURAL
        else:
            self.accidental = accidental
        
        self.octave = octave
    
    @property
    def midi_number(self) -> int:
        """
        Get the MIDI note number for this pitch.
        
        Returns:
            The MIDI note number (middle C = 60).
        """
        # Base values for C in each octave
        c_midi = {0: 12, 1: 24, 2: 36, 3: 48, 4: 60, 5: 72, 6: 84, 7: 96, 8: 108}
        
        # Offsets from C for each note name
        name_offset = {
            'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11
        }
        
        # Accidental offsets
        acc_offset = {
            Accidental.DOUBLE_FLAT: -2,
            Accidental.FLAT: -1,
            Accidental.NATURAL: 0,
            Accidental.SHARP: 1,
            Accidental.DOUBLE_SHARP: 2
        }
        
        # Calculate MIDI number
        midi = c_midi.get(self.octave, 60) + name_offset.get(self.note_name, 0)
        midi += acc_offset.get(self.accidental, 0)
        
        return midi
    
    def transpose(self, semitones: int) -> 'Pitch':
        """
        Transpose this pitch by a number of semitones.
        
        Args:
            semitones: The number of semitones to transpose (positive = up, negative = down).
            
        Returns:
            A new transposed Pitch.
        """
        # TODO: Implement transposition logic
        # This requires proper handling of enharmonic equivalents
        # For now, just return a copy of self
        return Pitch(
            note_name=self.note_name,
            accidental=self.accidental,
            octave=self.octave
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'note_name': self.note_name,
            'accidental': self.accidental.value,
            'octave': self.octave
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pitch':
        """Create from dictionary representation."""
        return cls(
            note_name=data.get('note_name', 'C'),
            accidental=data.get('accidental', ''),
            octave=data.get('octave', 4)
        )
    
    @classmethod
    def from_string(cls, pitch_str: str) -> 'Pitch':
        """
        Create a Pitch from a string representation.
        
        Args:
            pitch_str: A string like "C4", "F#5", "Bb3", etc.
            
        Returns:
            A Pitch instance.
        """
        match = cls.PITCH_REGEX.match(pitch_str)
        if match:
            note_name, accidental, octave_str = match.groups()
            octave = int(octave_str) if octave_str else 4
            return cls(note_name=note_name, accidental=accidental, octave=octave)
        else:
            # Default to middle C if parsing fails
            return cls(note_name='C', accidental='', octave=4)
    
    def __str__(self) -> str:
        """Get string representation."""
        return f"{self.note_name}{self.accidental.value}{self.octave}"


class Clef(MusicElement):
    """
    Represents a clef in sheet music.
    """
    
    def __init__(
        self,
        name: str = "treble",
        position: int = 0,
        id: Optional[str] = None
    ):
        """
        Initialize a Clef.
        
        Args:
            name: The clef name (treble, bass, alto, tenor, etc.).
            position: The position offset (in staff lines).
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.name = name
        self.position = position
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'name': self.name,
            'position': self.position
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Clef':
        """Create from dictionary representation."""
        clef = cls(
            name=data.get('name', 'treble'),
            position=data.get('position', 0),
            id=data.get('id')
        )
        clef.attributes = data.get('attributes', {}).copy()
        return clef


class KeySignature(MusicElement):
    """
    Represents a key signature in sheet music.
    """
    
    def __init__(
        self,
        key: str = "C",
        id: Optional[str] = None
    ):
        """
        Initialize a KeySignature.
        
        Args:
            key: The key name (C, G, F, Bb, etc.).
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.key = key
        
        # Derived properties (number of sharps/flats)
        self._calculate_accidentals()
    
    def _calculate_accidentals(self) -> None:
        """Calculate the number of sharps or flats from the key name."""
        # Map of key names to number of sharps (positive) or flats (negative)
        key_map = {
            'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7,
            'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7
        }
        
        self.accidentals = key_map.get(self.key, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'key': self.key,
            'accidentals': self.accidentals
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeySignature':
        """Create from dictionary representation."""
        key_sig = cls(
            key=data.get('key', 'C'),
            id=data.get('id')
        )
        key_sig.attributes = data.get('attributes', {}).copy()
        return key_sig


class TimeSignature(MusicElement):
    """
    Represents a musical time signature.
    
    A TimeSignature has a numerator and a denominator.
    """
    
    def __init__(
        self,
        numerator: int = 4,
        denominator: int = 4,
        id: Optional[str] = None
    ):
        """
        Initialize a TimeSignature.
        
        Args:
            numerator: The number of beats in a measure.
            denominator: The note value that represents one beat.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.numerator = numerator
        self.denominator = denominator
    
    @property
    def as_string(self) -> str:
        """Return the time signature as a string (e.g., "4/4")."""
        return f"{self.numerator}/{self.denominator}"
    
    @classmethod
    def from_string(cls, time_str: str) -> 'TimeSignature':
        """
        Create a TimeSignature object from a string (e.g., "4/4").
        
        Args:
            time_str: The time signature string.
            
        Returns:
            A TimeSignature instance.
        """
        parts = time_str.split('/')
        if len(parts) == 2:
            try:
                num = int(parts[0])
                den = int(parts[1])
                return cls(numerator=num, denominator=den)
            except ValueError:
                # Handle cases like "C" for common time or "C|" for cut time if desired
                if time_str.upper() == 'C':
                    return cls(numerator=4, denominator=4)
                elif time_str.upper() == 'C|': # common representation for cut time
                    return cls(numerator=2, denominator=2)
                else:
                    raise ValueError(f"Invalid time signature string: {time_str}")
        else:
            raise ValueError(f"Time signature string must be in num/den format: {time_str}")
    
    def is_compound(self) -> bool:
        """
        Checks if the time signature is compound.
        Compound meters have a numerator of 6, 9, 12, etc. (divisible by 3, and >= 6),
        and the beat is typically a dotted note.
        """
        return self.numerator >= 6 and self.numerator % 3 == 0

    def is_simple_duple(self) -> bool:
        """
        Checks if the time signature is simple duple (e.g., 2/4, 2/2).
        The main beats divide into two sub-beats.
        For the beaming rule, this means things like 2/x, 4/x (where 4/x is often treated as two groups of 2).
        """
        # Simple duple typically has 2 or 4 as numerator.
        # 4/x can be considered quadruple, which is two duples.
        if self.is_compound(): # Compound meters are not simple duple
            return False
        return self.numerator == 2 or self.numerator == 4
        
    def is_simple_triple(self) -> bool:
        """
        Checks if the time signature is simple triple (e.g., 3/4, 3/8).
        The main beats divide into two sub-beats, but there are three main beats.
        """
        if self.is_compound():
            return False
        return self.numerator == 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'numerator': self.numerator,
            'denominator': self.denominator
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TimeSignature':
        """Create from dictionary representation."""
        time_sig = cls(
            numerator=data.get('numerator', 4),
            denominator=data.get('denominator', 4),
            id=data.get('id')
        )
        time_sig.attributes = data.get('attributes', {}).copy()
        return time_sig


class Note(MusicElement):
    """
    Represents a musical note.
    
    A Note has a pitch and a duration.
    """
    
    def __init__(
        self,
        pitch: Optional[Pitch] = None,
        duration: Optional[Duration] = None,
        start_tick_offset: int = 0,
        id: Optional[str] = None,
        is_tied_to_next: bool = False,
        # Beaming attributes
        beam_count_to_next: int = 0,
        has_flag: bool = False,
        flag_beam_count: int = 0,
        flag_direction: Optional[str] = None
    ):
        """
        Initialize a Note.
        
        Args:
            pitch: The pitch of the note.
            duration: The duration of the note.
            start_tick_offset: The starting tick offset of this note within its measure.
            id: Optional unique identifier.
            is_tied_to_next: True if this note is tied to the next musical event.
            beam_count_to_next: Number of full beams to the next note (0 if none).
            has_flag: True if the note has a flag (partial beam).
            flag_beam_count: Number of strokes in the flag (e.g., 1 for 8th, 2 for 16th).
            flag_direction: Direction of the flag ('left' or 'right').
        """
        super().__init__(id=id)
        self.pitch = pitch or Pitch()
        self.duration = duration or Duration()
        self.start_tick_offset = start_tick_offset
        self.is_tied_to_next = is_tied_to_next
        
        # Initialize beaming attributes
        self.beam_count_to_next = beam_count_to_next
        self.has_flag = has_flag
        self.flag_beam_count = flag_beam_count
        self.flag_direction = flag_direction
        
        # Visual properties
        self.stem_direction = "auto"  # "up", "down", or "auto"
        self.stem_length = 1.0  # Multiplier for stem length
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'pitch': self.pitch.to_dict(),
            'duration': self.duration.to_dict(),
            'start_tick_offset': self.start_tick_offset,
            'stem_direction': self.stem_direction,
            'stem_length': self.stem_length,
            'is_tied_to_next': self.is_tied_to_next,
            # Beaming attributes for serialization
            'beam_count_to_next': self.beam_count_to_next,
            'has_flag': self.has_flag,
            'flag_beam_count': self.flag_beam_count,
            'flag_direction': self.flag_direction
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create from dictionary representation."""
        note = cls(
            pitch=Pitch.from_dict(data.get('pitch', {})),
            duration=Duration.from_dict(data.get('duration', {})),
            start_tick_offset=data.get('start_tick_offset', 0),
            id=data.get('id'),
            is_tied_to_next=data.get('is_tied_to_next', False),
            # Beaming attributes from serialization
            beam_count_to_next=data.get('beam_count_to_next', 0),
            has_flag=data.get('has_flag', False),
            flag_beam_count=data.get('flag_beam_count', 0),
            flag_direction=data.get('flag_direction')
        )
        note.attributes = data.get('attributes', {}).copy()
        note.stem_direction = data.get('stem_direction', 'auto')
        note.stem_length = data.get('stem_length', 1.0)
        return note
    
    @classmethod
    def from_string(cls, note_str: str) -> 'Note':
        """
        Create a Note from a string representation.
        
        Args:
            note_str: A string like "C4", "F#5/8", "Bb3/16.", etc.
            
        Returns:
            A Note instance.
        """
        # Split into pitch and duration parts
        parts = note_str.split('/')
        
        pitch_str = parts[0]
        duration_str = parts[1] if len(parts) > 1 else "4"
        
        pitch = Pitch.from_string(pitch_str)
        duration = Duration.from_string(duration_str)
        
        return cls(pitch=pitch, duration=duration)


class Rest(MusicElement):
    """
    Represents a musical rest.
    
    A Rest has a duration but no pitch.
    """
    
    def __init__(
        self,
        duration: Optional[Duration] = None,
        start_tick_offset: int = 0,
        id: Optional[str] = None
    ):
        """
        Initialize a Rest.
        
        Args:
            duration: The duration of the rest.
            start_tick_offset: The starting tick offset of this rest within its measure.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.duration = duration or Duration()
        self.start_tick_offset = start_tick_offset
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'duration': self.duration.to_dict(),
            'start_tick_offset': self.start_tick_offset
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rest':
        """Create from dictionary representation."""
        rest = cls(
            duration=Duration.from_dict(data.get('duration', {})),
            start_tick_offset=data.get('start_tick_offset', 0),
            id=data.get('id')
        )
        rest.attributes = data.get('attributes', {}).copy()
        return rest
    
    @classmethod
    def from_string(cls, rest_str: str) -> 'Rest':
        """
        Create a Rest from a string representation.
        
        Args:
            rest_str: A string like "4", "8.", "16..", etc.
            
        Returns:
            A Rest instance.
        """
        duration = Duration.from_string(rest_str)
        return cls(duration=duration)


class Chord(MusicElement):
    """
    Represents a musical chord.
    
    A Chord has a duration and multiple pitches.
    """
    
    def __init__(
        self,
        pitches: Optional[List[Pitch]] = None,
        duration: Optional[Duration] = None,
        start_tick_offset: int = 0,
        id: Optional[str] = None
    ):
        """
        Initialize a Chord.
        
        Args:
            pitches: The pitches in the chord.
            duration: The duration of the chord.
            start_tick_offset: The starting tick offset of this chord within its measure.
            id: Optional unique identifier.
        """
        super().__init__(id=id)
        self.pitches = pitches or []
        self.duration = duration or Duration()
        self.start_tick_offset = start_tick_offset
        
        # Visual properties
        self.stem_direction = "auto"  # "up", "down", or "auto"
        self.stem_length = 1.0  # Multiplier for stem length
    
    def add_pitch(self, pitch: Pitch) -> None:
        """
        Add a pitch to this chord.
        
        Args:
            pitch: The pitch to add.
        """
        self.pitches.append(pitch)
    
    def remove_pitch(self, pitch: Pitch) -> None:
        """
        Remove a pitch from this chord.
        
        Args:
            pitch: The pitch to remove.
        """
        self.pitches = [p for p in self.pitches if p != pitch]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = super().to_dict()
        result.update({
            'pitches': [pitch.to_dict() for pitch in self.pitches],
            'duration': self.duration.to_dict(),
            'start_tick_offset': self.start_tick_offset,
            'stem_direction': self.stem_direction,
            'stem_length': self.stem_length
        })
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chord':
        """Create from dictionary representation."""
        chord = cls(
            pitches=[Pitch.from_dict(p) for p in data.get('pitches', [])],
            duration=Duration.from_dict(data.get('duration', {})),
            start_tick_offset=data.get('start_tick_offset', 0),
            id=data.get('id')
        )
        chord.attributes = data.get('attributes', {}).copy()
        chord.stem_direction = data.get('stem_direction', 'auto')
        chord.stem_length = data.get('stem_length', 1.0)
        return chord


class Measure(MusicElement):
    """
    Represents a measure in a staff.
    A Measure contains a sequence of musical events (notes, rests, chords)
    and has a specific time signature context.
    """
    def __init__(
        self,
        measure_number: int,
        time_signature: Optional[TimeSignature] = None, # Can be inherited from Staff
        id: Optional[str] = None
    ):
        super().__init__(id=id)
        self.measure_number = measure_number
        self._time_signature = time_signature # The time signature active for this measure
        self.events: List[Union[Note, Rest, Chord]] = [] # Holds musical events

    @property
    def time_signature(self) -> Optional[TimeSignature]:
        """Get the time signature for this measure."""
        # Potentially logic to get from parent Staff if not set directly
        return self._time_signature

    @time_signature.setter
    def time_signature(self, ts: TimeSignature) -> None:
        self._time_signature = ts

    def add_event(self, event: Union[Note, Rest, Chord], position: Optional[int] = None) -> None:
        """
        Adds a musical event to this measure.
        Args:
            event: The Note, Rest, or Chord to add.
            position: Optional index at which to insert the event. If None, appends.
        """
        if position is None:
            self.events.append(event)
        else:
            self.events.insert(position, event)
        # self.add_child(event) # MusicElement hierarchy - add_child is part of MusicElement, not needed to call explicitly here if events are already children.
                                # Events become children when their parent is set, or if Measure explicitly adds them as children if they are not already.
                                # For now, let's assume events added to self.events list are conceptually children.
                                # A more robust approach would ensure event.parent is set to this measure.
        # Let's ensure parentage for proper MusicElement tree traversal and serialization
        event.parent = self 
        if event not in self._children: # _children is from MusicElement
             self._children.append(event)


    def remove_event(self, event: Union[Note, Rest, Chord]) -> None:
        """Removes a musical event from this measure."""
        if event in self.events:
            self.events.remove(event)
            # self.remove_child(event) # MusicElement hierarchy - similar to add_event, ensure correct handling.
            if event in self._children:
                self._children.remove(event)
            event.parent = None


    def get_total_duration_ticks(self, ppqn: int = 480) -> int:
        """
        Calculates the total duration of all events in the measure in ticks.
        This needs a robust way to get duration from Note/Rest/Chord
        and their Duration objects. The Duration class currently has 'value' (like 4 for quarter)
        and 'dots'. We need to convert this to a beat fraction and then to ticks.
        Example: A quarter note (value=4, dots=0) is 1 beat.
                 A dotted quarter note (value=4, dots=1) is 1.5 beats.
                 A half note (value=2, dots=0) is 2 beats.
                 A whole note (value=1, dots=0) is 4 beats (assuming 4/4 context for "beat").
        The `Duration.as_fraction` method (e.g., (1,4) for quarter note) is a good start.
        If 1/4 note = 1 beat = `ppqn` ticks.
        Duration (1, d) => (4/d) beats.
        Duration (n, d) with dots => (n/d) * (2 - 1/(2^dots)) base value, need careful conversion to beats.

        Let's simplify: assume ppqn is ticks_per_quarter_note.
        A whole note (Duration(1)) is 4 * ppqn.
        A half note (Duration(2)) is 2 * ppqn.
        A quarter note (Duration(4)) is 1 * ppqn.
        An eighth note (Duration(8)) is 0.5 * ppqn.
        A dot adds 50% of the preceding value.
        """
        total_ticks = 0
        for item in self.events:
            base_duration_value = item.duration.value # e.g., 4 for quarter, 2 for half
            num_dots = item.duration.dots

            # Calculate ticks for the base duration (relative to a quarter note)
            # If value is 4 (quarter), factor is 1. If 2 (half), factor is 2. If 1 (whole), factor is 4.
            # If 8 (eighth), factor is 0.5.
            beat_equivalent_of_base = 4.0 / base_duration_value
            current_event_ticks = beat_equivalent_of_base * ppqn

            # Add duration for dots
            dot_multiplier = 1.0
            for _ in range(num_dots):
                dot_multiplier += 0.5 ** (_ + 1)
            current_event_ticks *= dot_multiplier
            
            total_ticks += int(round(current_event_ticks))
        return total_ticks

    def get_capacity_ticks(self, ppqn: int = 480) -> Optional[int]:
        """
        Calculates the total capacity of the measure in ticks based on its time signature.
        Returns None if time_signature is not set.
        """
        if not self.time_signature:
            return None
        
        # Capacity in quarter notes = numerator * (4 / denominator)
        # E.g., 3/4 time: 3 * (4/4) = 3 quarter notes
        # E.g., 6/8 time: 6 * (4/8) = 3 quarter notes
        # E.g., 2/2 time (cut time): 2 * (4/2) = 4 quarter notes
        capacity_in_quarter_notes = self.time_signature.numerator * (4.0 / self.time_signature.denominator)
        return int(round(capacity_in_quarter_notes * ppqn))

    def is_full(self, ppqn: int = 480) -> bool:
        """
        Checks if the measure is full based on its time signature.
        Returns False if capacity cannot be determined (no time signature).
        """
        capacity = self.get_capacity_ticks(ppqn)
        if capacity is None:
            return False # Cannot determine if full if no time signature implies not full by definition
        return self.get_total_duration_ticks(ppqn) >= capacity

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            'measure_number': self.measure_number,
            'time_signature': self.time_signature.to_dict() if self.time_signature else None,
            'events': [event.to_dict() for event in self.events] # Relies on MusicElement.to_dict() for children
        })
        # We don't need to explicitly list children if MusicElement.to_dict() handles it.
        # Let's remove the explicit 'events' and rely on the parent class's 'children' handling.
        # The events list is the primary store, MusicElement children list is for hierarchy.
        # For serialization, ensure events are captured.
        # The MusicElement.to_dict already has 'children': [child.to_dict() for child in self._children]
        # So, as long as events added via add_event are also added to self._children, it should be fine.
        return result # The current result is fine, it explicitly serializes events.

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Measure':
        from .base import MusicElement # Ensure MusicElement is in scope for type checking if needed
        # from ..serialization import deserialize_element # This path might be for a higher-level loader

        ts_data = data.get('time_signature')
        measure = cls(
            measure_number=data.get('measure_number', 0),
            time_signature=TimeSignature.from_dict(ts_data) if ts_data else None,
            id=data.get('id')
        )
        measure.attributes = data.get('attributes', {}).copy()
        
        # Children deserialization should ideally be handled by MusicElement.from_dict
        # or a dedicated deserializer that knows how to map 'type' strings to classes.
        # If MusicElement.from_dict is generic, we might need to populate self.events manually here
        # after children are created by the superclass's from_dict (if it handles children).
        # For now, let's assume we populate self.events from 'events' data directly as it's simpler.

        for event_data in data.get('events', []): # Assuming 'events' key from to_dict
            event_type_str = event_data.get('type') # 'Note', 'Rest', 'Chord'
            event = None
            if event_type_str == 'Note':
                event = Note.from_dict(event_data)
            elif event_type_str == 'Rest':
                event = Rest.from_dict(event_data)
            elif event_type_str == 'Chord':
                event = Chord.from_dict(event_data)
            # TODO: Add other possible event types if any (e.g. ClefChange, KeyChange in measure)
            
            if event:
                measure.add_event(event) # This also handles parentage and _children list
        return measure 