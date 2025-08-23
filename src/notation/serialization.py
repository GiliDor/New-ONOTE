"""
Serialization utilities for the music notation model.

This module provides functionality for serializing and deserializing
music notation objects to and from JSON.
"""
import json
from typing import Dict, Any, Type, Optional, Union, List, Callable

from .model.base import MusicElement

# Global registry of types that can be serialized and deserialized
_TYPE_REGISTRY: Dict[str, Type[MusicElement]] = {}

def register_type(cls: Type[MusicElement]) -> Type[MusicElement]:
    """
    Register a class in the type registry.
    Can be used as a decorator.
    
    Args:
        cls: The class to register.
        
    Returns:
        The registered class.
    """
    _TYPE_REGISTRY[cls.__name__] = cls
    return cls

def get_registered_type(type_name: str) -> Optional[Type[MusicElement]]:
    """
    Get a class from the type registry.
    
    Args:
        type_name: The name of the class to get.
        
    Returns:
        The registered class, or None if not found.
    """
    return _TYPE_REGISTRY.get(type_name)

def deserialize_element(data: Dict[str, Any]) -> Optional[MusicElement]:
    """
    Deserialize a dictionary into a MusicElement.
    
    Args:
        data: The dictionary to deserialize.
        
    Returns:
        A new MusicElement instance, or None if the type is not registered.
    """
    type_name = data.get('type')
    if not type_name:
        return None
        
    element_class = get_registered_type(type_name)
    if not element_class:
        return None
        
    # Create the element using the appropriate from_dict method
    element = element_class.from_dict(data)
    
    # Process children recursively
    children_data = data.get('children', [])
    for child_data in children_data:
        child = deserialize_element(child_data)
        if child:
            element.add_child(child)
            
    return element

def serialize_to_file(element: MusicElement, filepath: str) -> bool:
    """
    Serialize a MusicElement to a JSON file.
    
    Args:
        element: The element to serialize.
        filepath: The file path to save to.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(element.to_dict(), f, indent=2)
        return True
    except Exception as e:
        print(f"Error serializing to file: {e}")
        return False

def deserialize_from_file(filepath: str) -> Optional[MusicElement]:
    """
    Deserialize a MusicElement from a JSON file.
    
    Args:
        filepath: The file path to load from.
        
    Returns:
        A new MusicElement instance, or None if loading failed.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return deserialize_element(data)
    except Exception as e:
        print(f"Error deserializing from file: {e}")
        return None

# Register model classes
def register_model_classes():
    """Register all model classes in the type registry."""
    from .model import (
        Score, Section, StaffSystem,
        SingleStaff, GrandStaff, Staff,
        Note, Rest, Chord, Duration, Pitch,
        Clef, KeySignature, TimeSignature
    )
    
    # Register all classes
    register_type(MusicElement)
    register_type(Score)
    register_type(Section)
    register_type(StaffSystem)
    register_type(Staff)
    register_type(SingleStaff)
    register_type(GrandStaff)
    register_type(Note)
    register_type(Rest)
    register_type(Chord)
    register_type(Clef)
    register_type(KeySignature)
    register_type(TimeSignature)
    
# Register all model classes when this module is imported
register_model_classes() 