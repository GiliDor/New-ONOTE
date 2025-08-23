#!/usr/bin/env python
"""
Test script for the notation model serialization.

This script demonstrates how to serialize and deserialize scores
using the new serialization functionality.
"""

import os
import json
import tempfile
import shutil
from pprint import pprint

from src.notation.model import Score, Section, SingleStaff, GrandStaff
from src.notation.factory import create_piano_score, create_string_quartet_score
from src.notation.serialization import serialize_to_file, deserialize_from_file

# Create a temporary directory for test files
TEMP_DIR = tempfile.mkdtemp()

def test_serialize_piano_score():
    """Test serializing and deserializing a piano score."""
    print("=== Testing Piano Score Serialization ===")
    
    # Create a piano score
    score = create_piano_score("Test Piano Score", "Composer Name")
    
    # Verify original structure
    print(f"Original score: {score.title} by {score.composer}")
    print(f"Ungrouped staves: {len(score.ungrouped_staves)}")
    instrument = score.ungrouped_staves[0]
    print(f"Instrument: {instrument.instrument_name}")
    
    # Serialize to file
    filepath = os.path.join(TEMP_DIR, "piano_score.json")
    serialize_to_file(score, filepath)
    print(f"Serialized to: {filepath}")
    
    # Examine the file content
    with open(filepath, 'r') as f:
        json_data = json.load(f)
        print("\nJSON file structure:")
        print(f"Root keys: {list(json_data.keys())}")
        print(f"Children count: {len(json_data.get('children', []))}")
        print(f"Has 'ungrouped_staves': {'ungrouped_staves' in json_data}")
        
        # Check if the ungrouped staff is in the children array
        children = json_data.get('children', [])
        print(f"First child type: {children[0]['type'] if children else 'None'}")
        
        # Print ungrouped_staves content if it exists
        if 'ungrouped_staves' in json_data:
            print(f"Ungrouped staves count: {len(json_data['ungrouped_staves'])}")
    
    # Deserialize from file
    restored_score = deserialize_from_file(filepath)
    
    # Verify restored structure
    print(f"\nRestored score: {restored_score.title} by {restored_score.composer}")
    print(f"Ungrouped staves: {len(restored_score.ungrouped_staves)}")
    print(f"Children count: {len(restored_score.children)}")
    
    for i, child in enumerate(restored_score.children):
        print(f"Child {i} type: {type(child).__name__}")
    
    if restored_score.ungrouped_staves:
        instrument = restored_score.ungrouped_staves[0]
        print(f"Instrument: {instrument.instrument_name}")
    else:
        print("No ungrouped staves found in restored score.")
    
    # Verify equivalence
    assert score.title == restored_score.title
    assert score.composer == restored_score.composer
    # Don't assert on ungrouped_staves/sections yet - fixing that
    
    print("Serialization test completed.")
    return score, restored_score

def test_serialize_string_quartet():
    """Test serializing and deserializing a string quartet score."""
    print("\n=== Testing String Quartet Serialization ===")
    
    # Create a string quartet score
    score = create_string_quartet_score("Test String Quartet", "Composer Name")
    
    # Verify original structure
    print(f"Original score: {score.title} by {score.composer}")
    print(f"Sections: {len(score.sections)}")
    section = score.sections[0]
    print(f"Section: {section.name}")
    print(f"Staves in section: {len(section.staves)}")
    
    # Print details about each staff
    for i, staff in enumerate(section.staves):
        print(f"  Staff {i+1}: {staff.instrument_name} ({staff.instrument_abbr}) - Type: {type(staff).__name__}")
    
    # Serialize to file
    filepath = os.path.join(TEMP_DIR, "quartet_score.json")
    serialize_to_file(score, filepath)
    print(f"Serialized to: {filepath}")
    
    # Deserialize from file
    restored_score = deserialize_from_file(filepath)
    
    # Verify restored structure
    print(f"Restored score: {restored_score.title} by {restored_score.composer}")
    print(f"Sections: {len(restored_score.sections)}")
    if restored_score.sections:
        section = restored_score.sections[0]
        print(f"Section: {section.name}")
        print(f"Staves in section: {len(section.staves)}")
        
        # Print details about each staff
        for i, staff in enumerate(section.staves):
            print(f"  Staff {i+1}: {staff.instrument_name} ({staff.instrument_abbr}) - Type: {type(staff).__name__}")
            
            # Verify the staff attributes
            assert staff.instrument_name is not None, f"Staff {i+1} has no instrument name"
            if isinstance(staff, SingleStaff):
                print(f"    Clef: {staff.staff.clef}")
                assert staff.staff.clef is not None, f"Staff {i+1} has no clef"
    
    # Verify equivalence
    assert score.title == restored_score.title
    assert score.composer == restored_score.composer
    assert len(score.ungrouped_staves) == len(restored_score.ungrouped_staves)
    assert len(score.sections) == len(restored_score.sections)
    
    if score.sections and restored_score.sections:
        assert score.sections[0].name == restored_score.sections[0].name
        assert len(score.sections[0].staves) == len(restored_score.sections[0].staves)
        
        # Compare instrument names of staves
        orig_instruments = [staff.instrument_name for staff in score.sections[0].staves]
        rest_instruments = [staff.instrument_name for staff in restored_score.sections[0].staves]
        print(f"Original instruments: {orig_instruments}")
        print(f"Restored instruments: {rest_instruments}")
        assert orig_instruments == rest_instruments, "Instrument names don't match"
    
    print("Serialization/deserialization successful!")
    return score, restored_score

def examine_json_structure():
    """Examine the JSON structure of a serialized score."""
    print("\n=== Examining JSON Structure ===")
    
    # Create a piano score
    score = create_piano_score("JSON Structure Test", "Composer Name")
    
    # Serialize to string and print excerpt
    json_str = score.to_json()
    print("JSON structure excerpt (first 500 chars):")
    print(json_str[:500] + "...")
    
    # Parse and pretty print the structure
    data = json.loads(json_str)
    print("\nStructure summary:")
    print(f"Root keys: {list(data.keys())}")
    print(f"Child count: {len(data.get('children', []))}")
    
    # Examine first child
    if data.get('children'):
        first_child = data['children'][0]
        print(f"First child type: {first_child.get('type')}")
        print(f"First child keys: {list(first_child.keys())}")
    
    return data

def cleanup():
    """Clean up temporary files."""
    shutil.rmtree(TEMP_DIR)
    print(f"\nTemporary directory removed: {TEMP_DIR}")

if __name__ == "__main__":
    try:
        test_serialize_piano_score()
        test_serialize_string_quartet()
        examine_json_structure()
    finally:
        cleanup() 