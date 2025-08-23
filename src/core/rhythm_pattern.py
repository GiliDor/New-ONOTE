from dataclasses import dataclass
from typing import List, Tuple
import numpy as np

@dataclass
class Note:
    duration: float  # Duration in beats
    is_rest: bool = False
    is_tied: bool = False

class RhythmPattern:
    def __init__(self, size: str = 'q', ratio: Tuple[int, int] = (1, 1)):
        """
        Initialize a rhythm pattern.
        
        Args:
            size: Size of the pattern ('w' for whole note, 'h' for half note, 'q' for quarter note)
            ratio: Tuple of (numerator, denominator) for the polyrhythmic ratio
        """
        self.size = size
        self.ratio = ratio
        self.notes: List[Note] = []
        self._generate_pattern()
        
    def _get_size_in_beats(self) -> float:
        """Convert size string to number of beats."""
        size_map = {
            'w': 4.0,  # whole note
            'h': 2.0,  # half note
            'q': 1.0,  # quarter note
            'e': 0.5,  # eighth note
            's': 0.25  # sixteenth note
        }
        return size_map.get(self.size, 1.0)
        
    def _generate_pattern(self):
        """Generate the rhythm pattern based on the ratio and size."""
        total_beats = self._get_size_in_beats()
        num_attacks = max(self.ratio)
        attack_positions = []
        
        # Generate attack positions based on ratio
        for i in range(num_attacks):
            if i % self.ratio[0] == 0:
                attack_positions.append(i * total_beats / num_attacks)
                
        # Create notes between attacks
        attack_positions.append(total_beats)  # Add end position
        for i in range(len(attack_positions) - 1):
            duration = attack_positions[i + 1] - attack_positions[i]
            if duration > 0:
                self.notes.append(Note(duration=duration))
                
    def augment(self):
        """Double the duration of all notes in the pattern."""
        for note in self.notes:
            note.duration *= 2
            
    def diminish(self):
        """Halve the duration of all notes in the pattern."""
        for note in self.notes:
            note.duration /= 2
            
    def get_total_duration(self) -> float:
        """Get the total duration of the pattern in beats."""
        return sum(note.duration for note in self.notes)
        
    def to_midi_ticks(self, ticks_per_beat: int = 480) -> List[int]:
        """Convert the pattern to MIDI ticks for playback."""
        ticks = []
        current_tick = 0
        for note in self.notes:
            if not note.is_rest:
                ticks.append(current_tick)
            current_tick += int(note.duration * ticks_per_beat)
        return ticks
        
    def __str__(self) -> str:
        """String representation of the pattern."""
        return f"RhythmPattern(size={self.size}, ratio={self.ratio}, notes={self.notes})" 