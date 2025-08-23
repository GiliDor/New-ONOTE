"""
Base classes for the music notation model.
"""
from typing import Dict, List, Optional, Any, Set
import uuid
import json


class MusicElement:
    """
    Base class for all music notation elements.
    
    This provides common functionality for identifiers, attributes,
    and hierarchical relationships between elements.
    """
    
    def __init__(self, id: Optional[str] = None):
        """
        Initialize a MusicElement.
        
        Args:
            id: Optional unique identifier for this element.
                If not provided, a UUID will be generated.
        """
        self.id = id or str(uuid.uuid4())
        self.attributes: Dict[str, Any] = {}
        self.parent = None
        self._children: List[MusicElement] = []
    
    def add_child(self, child: 'MusicElement') -> 'MusicElement':
        """
        Add a child element to this element.
        
        Args:
            child: The child element to add.
            
        Returns:
            The added child element for method chaining.
        """
        self._children.append(child)
        child.parent = self
        return child
    
    def remove_child(self, child: 'MusicElement') -> None:
        """
        Remove a child element from this element.
        
        Args:
            child: The child element to remove.
        """
        if child in self._children:
            self._children.remove(child)
            child.parent = None
    
    @property
    def children(self) -> List['MusicElement']:
        """Get all child elements."""
        return self._children.copy()
    
    def find_by_id(self, id: str) -> Optional['MusicElement']:
        """
        Find an element by its ID in this element's subtree.
        
        Args:
            id: The ID to search for.
            
        Returns:
            The element with the matching ID, or None if not found.
        """
        if self.id == id:
            return self
        
        for child in self._children:
            result = child.find_by_id(id)
            if result is not None:
                return result
        
        return None
    
    def find_by_type(self, element_type: type) -> List['MusicElement']:
        """
        Find all elements of a given type in this element's subtree.
        
        Args:
            element_type: The type to search for.
            
        Returns:
            A list of elements of the matching type.
        """
        results = []
        
        if isinstance(self, element_type):
            results.append(self)
        
        for child in self._children:
            results.extend(child.find_by_type(element_type))
        
        return results
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this element to a dictionary representation.
        
        Returns:
            A dictionary representing this element.
        """
        result = {
            'id': self.id,
            'type': self.__class__.__name__,
            'attributes': self.attributes.copy(),
            'children': [child.to_dict() for child in self._children]
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MusicElement':
        """
        Create a MusicElement from a dictionary representation.
        
        Args:
            data: The dictionary to create from.
            
        Returns:
            A new MusicElement instance.
        """
        # This is a basic implementation that will be overridden by subclasses
        element = cls(id=data.get('id'))
        element.attributes = data.get('attributes', {}).copy()
        
        # Process children recursively - this requires a type registry
        # which will be implemented when we call from the Score class
        return element
    
    def to_json(self) -> str:
        """
        Convert this element to a JSON string.
        
        Returns:
            A JSON string representing this element.
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'MusicElement':
        """
        Create a MusicElement from a JSON string.
        
        Args:
            json_str: The JSON string to create from.
            
        Returns:
            A new MusicElement instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data) 