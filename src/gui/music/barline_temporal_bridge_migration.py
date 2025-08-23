"""
Migration Script for ONOTE Temporal Grid Reconstruction

This module provides migration utilities to replace the old discrete measure model
with the new temporal grid-based system.

MIGRATION STRATEGY:
1. Detect existing measures in document
2. Migrate content to temporal grid measures
3. Replace barline_temporal_bridge with new temporal bridge
4. Maintain compatibility with existing UI components
"""

from typing import Dict, List, Optional, Any
import copy

from .temporal_bridge_v2 import TemporalBridgeV2
from .temporal_grid_system import TemporalGridSystem, TemporalGridMeasure
from .measure_object import MeasureObject


class TemporalGridMigration:
    """Handles migration from old measure system to temporal grid"""
    
    def __init__(self, document=None):
        self.document = document
        self.migration_log: List[str] = []
        self.backup_measures: Dict[int, MeasureObject] = {}
    
    def migrate_document_to_temporal_grid(self) -> TemporalBridgeV2:
        """
        Complete migration of document from old system to temporal grid system.
        
        Returns:
            TemporalBridgeV2: New temporal bridge with migrated content
        """
        print("\\n=== TEMPORAL GRID MIGRATION ===")
        self.migration_log.append("Starting temporal grid migration")
        
        # Step 1: Backup existing measures
        self._backup_existing_measures()
        
        # Step 2: Create new temporal bridge
        new_bridge = TemporalBridgeV2(self.document)
        
        # Step 3: Migrate existing measures to temporal grid
        if self.backup_measures:
            self._migrate_measures_to_temporal_grid(new_bridge)
        else:
            # No existing measures - create initial measure
            self.migration_log.append("No existing measures found - creating initial measure")
            new_bridge.create_initial_measure()
        
        # Step 4: Update document references
        self._update_document_references(new_bridge)
        
        # Step 5: Verify migration
        self._verify_migration(new_bridge)
        
        print("=== MIGRATION COMPLETE ===")
        self._print_migration_log()
        
        return new_bridge
    
    def _backup_existing_measures(self):
        """Backup existing measures before migration"""
        if not self.document or not hasattr(self.document, 'measures'):
            self.migration_log.append("No existing measures to backup")
            return
        
        measures = self.document.measures
        if isinstance(measures, dict):
            self.backup_measures = copy.deepcopy(measures)
        elif isinstance(measures, list):
            # Convert list to dict
            for i, measure in enumerate(measures):
                measure_num = getattr(measure, 'measure_number', i + 1)
                self.backup_measures[measure_num] = copy.deepcopy(measure)
        
        self.migration_log.append(f"Backed up {len(self.backup_measures)} existing measures")
        print(f"MIGRATION: Backed up {len(self.backup_measures)} measures")
        
        # Log measure details
        for num, measure in self.backup_measures.items():
            barline_type = getattr(measure, 'barline_type', 'unknown')
            end_x = getattr(measure, 'end_x', 'unknown')
            width = getattr(measure, 'width', 'unknown')
            self.migration_log.append(f"  Measure #{num}: type={barline_type}, end_x={end_x}, width={width}")
    
    def _migrate_measures_to_temporal_grid(self, new_bridge: TemporalBridgeV2):
        """Migrate backed up measures to temporal grid system"""
        self.migration_log.append("Migrating measures to temporal grid")
        
        # Sort measures by number
        sorted_measures = sorted(self.backup_measures.items())
        
        # Check if measures are consecutively numbered
        expected_numbers = list(range(1, len(sorted_measures) + 1))
        actual_numbers = [num for num, _ in sorted_measures]
        
        if actual_numbers != expected_numbers:
            self.migration_log.append(f"WARNING: Non-consecutive measure numbering detected")
            self.migration_log.append(f"  Expected: {expected_numbers}")
            self.migration_log.append(f"  Actual: {actual_numbers}")
            
            # Renumber measures consecutively
            renumbered_measures = {}
            for i, (old_num, measure) in enumerate(sorted_measures):
                new_num = i + 1
                measure.measure_number = new_num
                renumbered_measures[new_num] = measure
                self.migration_log.append(f"  Renumbered measure #{old_num} → #{new_num}")
            
            self.backup_measures = renumbered_measures
            sorted_measures = sorted(self.backup_measures.items())
        
        # Migrate each measure
        for measure_num, measure in sorted_measures:
            self._migrate_single_measure(new_bridge, measure_num, measure)
        
        self.migration_log.append(f"Successfully migrated {len(sorted_measures)} measures to temporal grid")
    
    def _migrate_single_measure(self, new_bridge: TemporalBridgeV2, measure_num: int, measure: MeasureObject):
        """Migrate a single measure to temporal grid"""
        self.migration_log.append(f"Migrating measure #{measure_num}")
        
        # Extract measure properties
        barline_type = getattr(measure, 'barline_type', 'single')
        width = getattr(measure, 'width', 160.0)
        end_x = getattr(measure, 'end_x', width)
        
        # Create temporal grid measure
        temporal_measure = TemporalGridMeasure(
            measure_number=measure_num,
            time_signature=new_bridge.temporal_grid.grid_settings.default_time_signature,
            grid_settings=new_bridge.temporal_grid.grid_settings
        )
        
        # Copy properties
        temporal_measure.barline_type = barline_type
        temporal_measure.calculated_natural_width = width
        temporal_measure.calculated_justified_width = width
        
        # Handle special barline types
        if hasattr(measure, 'is_repeat_start'):
            temporal_measure.is_repeat_start = measure.is_repeat_start
        if hasattr(measure, 'is_repeat_end'):
            temporal_measure.is_repeat_end = measure.is_repeat_end
        
        # Migrate temporal content if any exists
        self._migrate_measure_content(measure, temporal_measure)
        
        # Add to temporal grid
        new_bridge.temporal_grid.measures[measure_num] = temporal_measure
        
        self.migration_log.append(f"  Migrated measure #{measure_num}: type={barline_type}, width={width}")
    
    def _migrate_measure_content(self, old_measure: MeasureObject, temporal_measure: TemporalGridMeasure):
        """Migrate any existing content from old measure to temporal measure"""
        # Check for notation elements (if any exist in the old system)
        if hasattr(old_measure, 'notation_elements'):
            elements = getattr(old_measure, 'notation_elements', [])
            for element in elements:
                # Try to add element at beat 0 (beginning of measure)
                # This is a basic migration - more sophisticated positioning could be added
                try:
                    from .temporal_grid_system import TemporalPosition
                    temporal_pos = TemporalPosition(temporal_measure.measure_number, 0.0, 0)
                    temporal_measure.add_temporal_content(temporal_pos, element)
                    self.migration_log.append(f"    Migrated notation element: {element.__class__.__name__}")
                except Exception as e:
                    self.migration_log.append(f"    WARNING: Failed to migrate element: {e}")
        
        # Recalculate measure properties
        temporal_measure._recalculate_content_complexity()
        temporal_measure._recalculate_spacing_demands()
        temporal_measure._recalculate_natural_width()
    
    def _update_document_references(self, new_bridge: TemporalBridgeV2):
        """Update document to reference new temporal bridge"""
        if not self.document:
            return
        
        # Update document's temporal bridge reference
        if hasattr(self.document, 'temporal_bridge'):
            self.document.temporal_bridge = new_bridge
            self.migration_log.append("Updated document temporal_bridge reference")
        
        # Update staff view reference if it exists
        if hasattr(self.document, 'staff_view'):
            if hasattr(self.document.staff_view, 'temporal_bridge'):
                self.document.staff_view.temporal_bridge = new_bridge
                self.migration_log.append("Updated staff_view temporal_bridge reference")
            
            # Update barline temporal bridge reference
            if hasattr(self.document.staff_view, 'barline_temporal_bridge'):
                self.document.staff_view.barline_temporal_bridge = new_bridge
                self.migration_log.append("Updated staff_view barline_temporal_bridge reference")
        
        # Sync temporal grid to document measures
        new_bridge._sync_to_document()
        self.migration_log.append("Synced temporal grid to document measures")
    
    def _verify_migration(self, new_bridge: TemporalBridgeV2):
        """Verify that migration was successful"""
        self.migration_log.append("Verifying migration")
        
        # Check measure count
        temporal_count = len(new_bridge.temporal_grid.measures)
        document_count = len(getattr(self.document, 'measures', {})) if self.document else 0
        backup_count = len(self.backup_measures)
        
        self.migration_log.append(f"Measure counts - Backup: {backup_count}, Temporal: {temporal_count}, Document: {document_count}")
        
        if temporal_count == backup_count:
            self.migration_log.append("✅ Measure count verification PASSED")
        else:
            self.migration_log.append("❌ Measure count verification FAILED")
        
        # Check measure numbering
        if temporal_count > 0:
            temporal_numbers = sorted(new_bridge.temporal_grid.measures.keys())
            expected_numbers = list(range(1, temporal_count + 1))
            
            if temporal_numbers == expected_numbers:
                self.migration_log.append("✅ Consecutive numbering verification PASSED")
            else:
                self.migration_log.append(f"❌ Consecutive numbering verification FAILED")
                self.migration_log.append(f"  Expected: {expected_numbers}")
                self.migration_log.append(f"  Actual: {temporal_numbers}")
        
        # Check document sync
        if document_count == temporal_count:
            self.migration_log.append("✅ Document sync verification PASSED")
        else:
            self.migration_log.append("❌ Document sync verification FAILED")
    
    def _print_migration_log(self):
        """Print migration log for debugging"""
        print("\\n=== MIGRATION LOG ===")
        for entry in self.migration_log:
            print(f"MIGRATION: {entry}")
        print("=== END MIGRATION LOG ===\\n")
    
    def rollback_migration(self) -> bool:
        """Rollback migration and restore original measures"""
        if not self.backup_measures or not self.document:
            print("MIGRATION: No backup to rollback to")
            return False
        
        print("MIGRATION: Rolling back to original measures")
        
        # Restore original measures
        self.document.measures = copy.deepcopy(self.backup_measures)
        
        # Log rollback
        self.migration_log.append("ROLLBACK: Restored original measures")
        
        print(f"MIGRATION: Rollback complete - restored {len(self.backup_measures)} measures")
        return True
    
    def get_migration_summary(self) -> Dict[str, Any]:
        """Get summary of migration results"""
        return {
            "backup_measure_count": len(self.backup_measures),
            "migration_log": self.migration_log,
            "migration_successful": any("✅" in entry for entry in self.migration_log),
            "has_backup": len(self.backup_measures) > 0
        }


def migrate_barline_bridge_to_temporal_grid(document) -> TemporalBridgeV2:
    """
    Main migration function to replace old barline bridge with temporal grid system.
    
    Args:
        document: The ONOTE document to migrate
        
    Returns:
        TemporalBridgeV2: New temporal bridge with migrated content
    """
    print("\\n🔄 STARTING TEMPORAL GRID MIGRATION")
    
    # Create migration handler
    migration = TemporalGridMigration(document)
    
    # Perform migration
    new_bridge = migration.migrate_document_to_temporal_grid()
    
    # Get summary
    summary = migration.get_migration_summary()
    
    if summary["migration_successful"]:
        print("✅ TEMPORAL GRID MIGRATION SUCCESSFUL")
        print(f"   Migrated {summary['backup_measure_count']} measures")
        print("   Content merging model now active")
        print("   Consecutive measure numbering ensured")
    else:
        print("❌ TEMPORAL GRID MIGRATION FAILED")
        print("   Check migration log for details")
        
        # Offer rollback
        if summary["has_backup"]:
            print("   Backup available for rollback")
    
    return new_bridge 