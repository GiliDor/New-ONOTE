"""
Service module for the notation model.

This module provides the main API for working with the notation model,
including loading, saving, and managing score documents.
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Union

from src.gui.music.score_document import ScoreDocument

from .model import Score
from .adapter import document_to_model, model_to_document
from .factory import create_empty_score, create_piano_score, create_string_quartet_score
from .serialization import serialize_to_file, deserialize_from_file

logger = logging.getLogger(__name__)

class NotationService:
    """
    Service for managing notation documents.
    
    This service provides methods for creating, loading, and saving
    notation documents, as well as converting between the document
    and model representations.
    """
    
    def __init__(self):
        """Initialize the NotationService."""
        self.current_score: Optional[Score] = None
        self.current_document: Optional[ScoreDocument] = None
    
    def create_empty_document(self, title: str = "New Score", composer: str = "") -> ScoreDocument:
        """
        Create a new empty document.
        
        Args:
            title: The title of the score.
            composer: The composer of the score.
            
        Returns:
            A new ScoreDocument instance.
        """
        self.current_score = create_empty_score(title, composer)
        self.current_document = model_to_document(self.current_score)
        return self.current_document
    
    def create_piano_document(self, title: str = "Piano Score", composer: str = "") -> ScoreDocument:
        """
        Create a new piano document.
        
        Args:
            title: The title of the score.
            composer: The composer of the score.
            
        Returns:
            A new ScoreDocument instance with a piano staff.
        """
        self.current_score = create_piano_score(title, composer)
        self.current_document = model_to_document(self.current_score)
        return self.current_document
    
    def create_string_quartet_document(self, title: str = "String Quartet", composer: str = "") -> ScoreDocument:
        """
        Create a new string quartet document.
        
        Args:
            title: The title of the score.
            composer: The composer of the score.
            
        Returns:
            A new ScoreDocument instance with a string quartet.
        """
        self.current_score = create_string_quartet_score(title, composer)
        self.current_document = model_to_document(self.current_score)
        return self.current_document
    
    def load_document(self, document: ScoreDocument) -> Score:
        """
        Load a document into the notation model.
        
        Args:
            document: The ScoreDocument to load.
            
        Returns:
            The Score model created from the document.
        """
        self.current_document = document
        self.current_score = document_to_model(document)
        return self.current_score
    
    def update_document(self) -> ScoreDocument:
        """
        Update the document from the current model.
        
        Returns:
            The updated ScoreDocument.
        """
        if self.current_score is None:
            raise ValueError("No current score to update document from")
        
        self.current_document = model_to_document(self.current_score)
        return self.current_document
    
    def save_score_to_json(self, filepath: str) -> bool:
        """
        Save the current score to a JSON file.
        
        Args:
            filepath: The file path to save to.
            
        Returns:
            True if successful, False otherwise.
        """
        if self.current_score is None:
            logger.error("No score to save")
            return False
        
        try:
            result = serialize_to_file(self.current_score, filepath)
            if result:
                logger.info(f"Score saved to {filepath}")
            return result
        except Exception as e:
            logger.error(f"Error saving score: {e}")
            return False
    
    def load_score_from_json(self, filepath: str) -> Optional[Score]:
        """
        Load a score from a JSON file.
        
        Args:
            filepath: The file path to load from.
            
        Returns:
            The loaded Score, or None if loading failed.
        """
        try:
            score = deserialize_from_file(filepath)
            if not isinstance(score, Score):
                logger.error(f"Loaded file is not a Score: {filepath}")
                return None
                
            self.current_score = score
            self.current_document = model_to_document(score)
            
            logger.info(f"Score loaded from {filepath}")
            return score
        except Exception as e:
            logger.error(f"Error loading score: {e}")
            return None
            
    def save_document(self, document: ScoreDocument, filepath: str) -> bool:
        """
        Save a document to a JSON file.
        
        Args:
            document: The document to save.
            filepath: The file path to save to.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Convert document to model
            score = document_to_model(document)
            
            # Save model to file
            result = serialize_to_file(score, filepath)
            if result:
                logger.info(f"Document saved to {filepath}")
            return result
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False
    
    def load_document_from_file(self, filepath: str) -> Optional[ScoreDocument]:
        """
        Load a document from a JSON file.
        
        Args:
            filepath: The file path to load from.
            
        Returns:
            The loaded document, or None if loading failed.
        """
        try:
            # Load model from file
            score = deserialize_from_file(filepath)
            if not isinstance(score, Score):
                logger.error(f"Loaded file is not a Score: {filepath}")
                return None
                
            # Convert model to document
            document = model_to_document(score)
            
            # Update current state
            self.current_score = score
            self.current_document = document
            
            logger.info(f"Document loaded from {filepath}")
            return document
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            return None

# Singleton instance
notation_service = NotationService() 