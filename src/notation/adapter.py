"""
Adapter module to bridge between the existing UI components and the new notation model.

This module handles the conversion between the existing document format and
the new notation model objects.
"""
from typing import Dict, List, Optional, Any, Tuple
import logging

from src.gui.music.score_document import ScoreDocument
from src.gui.music.staff_types import StaffType, SectionGroup, SingleStaff as UIStaffSingle, GrandStaff as UIStaffGrand

from .model import (
    Score, Section, StaffSystem,
    SingleStaff, GrandStaff,
    Staff, Note, Rest, Chord, Duration, Pitch,
    Clef, KeySignature, TimeSignature
)

logger = logging.getLogger(__name__)

def document_to_model(document: ScoreDocument) -> Score:
    """
    Convert a ScoreDocument to a Score model.
    
    Args:
        document: The ScoreDocument to convert.
        
    Returns:
        A Score instance with the document's structure.
    """
    score = Score(
        title=document.title,
        composer=document.composer,
    )
    
    # Process the layout staves
    layout = document.layout
    
    # Process section_map: maps instrument_id -> section_name
    section_map = document.section_map or {}
    
    # Keep track of created sections by name
    sections: Dict[str, Section] = {}
    
    # Process ungrouped staves
    for staff in layout.ungrouped_staves:
        instrument_id = staff.instrument_id
        instrument_name = staff.instrument_name
        instrument_abbr = staff.instrument_abbr
        display_order_index = getattr(staff, 'display_order_index', 0)
        
        # Determine staff type
        if hasattr(staff, 'type'):
            staff_type = staff.type
        else:
            # Fallback determination
            staff_type = StaffType.GRAND if hasattr(staff, 'top_staff') else StaffType.SINGLE
        
        if staff_type == StaffType.SINGLE:
            staff_system = SingleStaff(
                instrument_name=instrument_name,
                instrument_abbr=instrument_abbr,
                instrument_id=instrument_id,
                display_order_index=display_order_index,
                clef=staff.clef,
                key=staff.key,
                time_signature=staff.time_signature
            )
        elif staff_type == StaffType.GRAND:
            staff_system = GrandStaff(
                instrument_name=instrument_name,
                instrument_abbr=instrument_abbr,
                instrument_id=instrument_id,
                display_order_index=display_order_index,
                upper_clef=staff.top_staff.clef,
                lower_clef=staff.bottom_staff.clef,
                key=staff.key,
                time_signature=staff.time_signature
            )
        else:
            logger.warning(f"Unknown staff type: {staff_type}")
            continue
        
        # Add directly to score as it's ungrouped
        score.add_staff_system(staff_system)
    
    # Process sections
    for section_group in layout.sections:
        section_name = section_group.name
        display_order_index = getattr(section_group, 'display_order_index', 0)
        section = Section(name=section_name, display_order_index=display_order_index)
        score.add_section(section)
        sections[section_name] = section
        
        # Process staves in this section
        for staff in section_group.staves:
            instrument_id = staff.instrument_id
            instrument_name = staff.instrument_name
            instrument_abbr = staff.instrument_abbr
            display_order_index = getattr(staff, 'display_order_index', 0)
            
            # Determine staff type
            if hasattr(staff, 'type'):
                staff_type = staff.type
            else:
                # Fallback determination
                staff_type = StaffType.GRAND if hasattr(staff, 'top_staff') else StaffType.SINGLE
            
            if staff_type == StaffType.SINGLE:
                staff_system = SingleStaff(
                    instrument_name=instrument_name,
                    instrument_abbr=instrument_abbr,
                    instrument_id=instrument_id,
                    display_order_index=display_order_index,
                    clef=staff.clef,
                    key=staff.key,
                    time_signature=staff.time_signature
                )
            elif staff_type == StaffType.GRAND:
                staff_system = GrandStaff(
                    instrument_name=instrument_name,
                    instrument_abbr=instrument_abbr,
                    instrument_id=instrument_id,
                    display_order_index=display_order_index,
                    upper_clef=staff.top_staff.clef,
                    lower_clef=staff.bottom_staff.clef,
                    key=staff.key,
                    time_signature=staff.time_signature
                )
            else:
                logger.warning(f"Unknown staff type: {staff_type}")
                continue
            
            # Add to section
            section.add_staff_system(staff_system)
    
    return score

def model_to_document(score: Score) -> ScoreDocument:
    """
    Convert a Score model to a ScoreDocument.
    
    Args:
        score: The Score to convert.
        
    Returns:
        A ScoreDocument with the score's structure.
    """
    document = ScoreDocument()
    document.layout.ungrouped_staves = []  # Clear default staves
    document.title = score.title
    document.composer = score.composer
    
    # Build section map
    section_map = {}
    
    # Process ungrouped staves
    for staff_system in score.ungrouped_staves:
        if isinstance(staff_system, SingleStaff):
            # Create a single staff
            single_staff = UIStaffSingle(
                instrument_id=staff_system.instrument_id,
                instrument_name=staff_system.instrument_name,
                instrument_abbr=staff_system.instrument_abbr,
                clef=staff_system.staff.clef,
                key=staff_system.staff.key,
                time_signature=staff_system.staff.time_signature
            )
            # Preserve display_order_index if available
            if hasattr(staff_system, 'display_order_index'):
                single_staff.display_order_index = staff_system.display_order_index
            document.add_ungrouped_staff(single_staff)
            
        elif isinstance(staff_system, GrandStaff):
            # Create top and bottom staves
            top_staff = UIStaffSingle(
                instrument_id=staff_system.instrument_id,
                instrument_name=staff_system.instrument_name,
                instrument_abbr=staff_system.instrument_abbr,
                clef=staff_system.upper_staff.clef,
                key=staff_system.upper_staff.key,
                time_signature=staff_system.upper_staff.time_signature
            )
            
            bottom_staff = UIStaffSingle(
                instrument_id=staff_system.instrument_id,
                instrument_name=staff_system.instrument_name,
                instrument_abbr=staff_system.instrument_abbr,
                clef=staff_system.lower_staff.clef,
                key=staff_system.lower_staff.key,
                time_signature=staff_system.lower_staff.time_signature
            )
            
            # Create the grand staff
            grand_staff = UIStaffGrand(
                instrument_id=staff_system.instrument_id,
                instrument_name=staff_system.instrument_name,
                instrument_abbr=staff_system.instrument_abbr,
                clef="grand",  # Will be set separately for each staff
                key=staff_system.upper_staff.key,  # Use the upper staff's key
                time_signature=staff_system.upper_staff.time_signature,
                top_staff=top_staff,
                bottom_staff=bottom_staff
            )
            # Preserve display_order_index if available
            if hasattr(staff_system, 'display_order_index'):
                grand_staff.display_order_index = staff_system.display_order_index
            
            document.add_ungrouped_staff(grand_staff)
    
    # Process sections and their staves
    for section in score.sections:
        # Create a section group
        section_group = SectionGroup(name=section.name, staves=[])
        # Preserve display_order_index if available
        if hasattr(section, 'display_order_index'):
            section_group.display_order_index = section.display_order_index
        document.add_section(section_group)
        
        for staff_system in section.staves:
            if isinstance(staff_system, SingleStaff):
                # Create a single staff
                single_staff = UIStaffSingle(
                    instrument_id=staff_system.instrument_id,
                    instrument_name=staff_system.instrument_name,
                    instrument_abbr=staff_system.instrument_abbr,
                    clef=staff_system.staff.clef,
                    key=staff_system.staff.key,
                    time_signature=staff_system.staff.time_signature,
                    section=section.name
                )
                # Preserve display_order_index if available
                if hasattr(staff_system, 'display_order_index'):
                    single_staff.display_order_index = staff_system.display_order_index
                document.add_staff_to_section(single_staff, section.name)
                
                # Add to section map
                section_map[staff_system.instrument_id] = section.name
            
            elif isinstance(staff_system, GrandStaff):
                # Create top and bottom staves
                top_staff = UIStaffSingle(
                    instrument_id=staff_system.instrument_id,
                    instrument_name=staff_system.instrument_name,
                    instrument_abbr=staff_system.instrument_abbr,
                    clef=staff_system.upper_staff.clef,
                    key=staff_system.upper_staff.key,
                    time_signature=staff_system.upper_staff.time_signature,
                    section=section.name
                )
                
                bottom_staff = UIStaffSingle(
                    instrument_id=staff_system.instrument_id,
                    instrument_name=staff_system.instrument_name,
                    instrument_abbr=staff_system.instrument_abbr,
                    clef=staff_system.lower_staff.clef,
                    key=staff_system.lower_staff.key,
                    time_signature=staff_system.lower_staff.time_signature,
                    section=section.name
                )
                
                # Create the grand staff
                grand_staff = UIStaffGrand(
                    instrument_id=staff_system.instrument_id,
                    instrument_name=staff_system.instrument_name,
                    instrument_abbr=staff_system.instrument_abbr,
                    clef="grand",  # Will be set separately for each staff
                    key=staff_system.upper_staff.key,  # Use the upper staff's key
                    time_signature=staff_system.upper_staff.time_signature,
                    top_staff=top_staff,
                    bottom_staff=bottom_staff,
                    section=section.name
                )
                # Preserve display_order_index if available
                if hasattr(staff_system, 'display_order_index'):
                    grand_staff.display_order_index = staff_system.display_order_index
                
                document.add_staff_to_section(grand_staff, section.name)
                
                # Add to section map
                section_map[staff_system.instrument_id] = section.name
    
    # Set the section map
    document.section_map = section_map
    
    return document 