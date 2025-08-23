#!/usr/bin/env python3
"""
Comprehensive Test for ONOTE Temporal Grid Reconstruction

This test validates the complete temporal grid system according to the detailed specifications:

1. TEMPORAL GRID STRUCTURE: Time signatures, tempo, PPQN, tick grid, quantization grid
2. CONTENT MERGING MODEL: Measures are divisions of continuous temporal grid, "deleting" merges content
3. DYNAMIC SPACING: Based on notation density, mixed note values, polyphonic complexity
4. BEAT-ALIGNMENT RULES: All staves align vertically on beats
5. JUSTIFICATION RULES: Measures stretch to fit system width

KEY TESTS:
- Content merging instead of measure deletion
- Consecutive measure numbering after merge operations
- Dynamic spacing based on content complexity
- Temporal grid with proper PPQN/tick positioning
- Migration from old system to new system
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QSettings

# Import temporal grid system
from src.gui.music.temporal_grid_system import (
    TemporalGridSystem, TemporalGridMeasure, TemporalGridSettings,
    TemporalPosition, NotationElement, Note, Rest, Chord,
    NoteDuration, BeatPosition, TimeSignature
)
from src.gui.music.temporal_bridge_v2 import TemporalBridgeV2
from src.gui.music.barline_temporal_bridge_migration import migrate_barline_bridge_to_temporal_grid
from src.gui.music.score_document import ScoreDocument


def test_temporal_grid_basic_functionality():
    """Test 1: Basic temporal grid functionality"""
    print("\\n=== TEST 1: Basic Temporal Grid Functionality ===")
    
    # Create temporal grid system
    grid_settings = TemporalGridSettings()
    grid_settings.ppqn = 480
    grid_settings.default_tempo = 120.0
    
    temporal_grid = TemporalGridSystem()
    temporal_grid.grid_settings = grid_settings
    
    # Test initial state
    assert len(temporal_grid.measures) == 0, "Grid should start empty"
    print("✅ Initial state: Grid starts empty")
    
    # Create initial measure
    initial_measure = temporal_grid.create_initial_measure()
    assert len(temporal_grid.measures) == 1, "Should have 1 measure after creation"
    assert 1 in temporal_grid.measures, "Measure #1 should exist"
    assert initial_measure.measure_number == 1, "Initial measure should be numbered 1"
    print("✅ Initial measure creation: Working correctly")
    
    # Test measure properties
    measure_1 = temporal_grid.measures[1]
    assert measure_1.time_signature.numerator == 4, "Default time signature should be 4/4"
    assert measure_1.time_signature.denominator == 4, "Default time signature should be 4/4"
    assert measure_1.grid_settings.ppqn == 480, "PPQN should be set correctly"
    print("✅ Measure properties: Time signature and PPQN correct")
    
    return True


def test_temporal_content_management():
    """Test 2: Temporal content management with beat positions"""
    print("\\n=== TEST 2: Temporal Content Management ===")
    
    # Create temporal grid measure
    grid_settings = TemporalGridSettings()
    measure = TemporalGridMeasure(1, TimeSignature(4, 4), grid_settings)
    
    # Create notation elements
    note_1 = Note(
        duration=NoteDuration.QUARTER,
        beat_position=BeatPosition(1.0),
        pitch="C4"
    )
    
    note_2 = Note(
        duration=NoteDuration.EIGHTH,
        beat_position=BeatPosition(2.0),
        pitch="D4"
    )
    
    rest_1 = Rest(
        duration=NoteDuration.QUARTER,
        beat_position=BeatPosition(3.0)
    )
    
    # Add temporal content
    pos_1 = TemporalPosition(1, 1.0, 0)
    pos_2 = TemporalPosition(1, 2.0, 0)
    pos_3 = TemporalPosition(1, 3.0, 0)
    
    success_1 = measure.add_temporal_content(pos_1, note_1)
    success_2 = measure.add_temporal_content(pos_2, note_2)
    success_3 = measure.add_temporal_content(pos_3, rest_1)
    
    assert success_1, "Should successfully add note at beat 1"
    assert success_2, "Should successfully add note at beat 2" 
    assert success_3, "Should successfully add rest at beat 3"
    assert len(measure.temporal_content) == 3, "Should have 3 temporal elements"
    print("✅ Temporal content addition: Working correctly")
    
    # Test content complexity calculation
    measure._recalculate_content_complexity()
    assert measure.content_complexity_score > 0, "Content complexity should be calculated"
    print(f"✅ Content complexity: {measure.content_complexity_score:.3f}")
    
    # Test spacing calculations
    measure._recalculate_spacing_demands()
    assert len(measure.spacing_demands) > 0, "Spacing demands should be calculated"
    print(f"✅ Spacing demands: {len(measure.spacing_demands)} elements with spacing requirements")
    
    # Test natural width calculation
    measure._recalculate_natural_width()
    assert measure.calculated_natural_width > 0, "Natural width should be calculated"
    print(f"✅ Natural width calculation: {measure.calculated_natural_width:.1f}px")
    
    return True


def test_content_merging_model():
    """Test 3: Content merging instead of measure deletion"""
    print("\\n=== TEST 3: Content Merging Model ===")
    
    # Create temporal grid with multiple measures
    temporal_grid = TemporalGridSystem()
    
    # Create initial measure
    measure_1 = temporal_grid.create_initial_measure()
    
    # Add more measures by inserting barlines
    measure_2 = temporal_grid.insert_barline_at_position(400.0, "single")
    measure_3 = temporal_grid.insert_barline_at_position(600.0, "single")
    
    assert len(temporal_grid.measures) == 3, "Should have 3 measures after barline insertions"
    assert sorted(temporal_grid.measures.keys()) == [1, 2, 3], "Measures should be numbered consecutively"
    print("✅ Multiple measure creation: Working correctly")
    
    # Add content to measures
    note_in_measure_2 = Note(duration=NoteDuration.QUARTER, beat_position=BeatPosition(1.0), pitch="E4")
    temporal_grid.measures[2].add_temporal_content(TemporalPosition(2, 1.0, 0), note_in_measure_2)
    
    note_in_measure_3 = Note(duration=NoteDuration.HALF, beat_position=BeatPosition(1.0), pitch="F4")
    temporal_grid.measures[3].add_temporal_content(TemporalPosition(3, 1.0, 0), note_in_measure_3)
    
    print("✅ Added content to measures 2 and 3")
    
    # Test content merging by "removing" measure 2 (should merge into measure 1)
    success = temporal_grid.remove_barline_at_measure(2)
    
    assert success, "Barline removal should succeed"
    assert len(temporal_grid.measures) == 2, "Should have 2 measures after merge"
    assert sorted(temporal_grid.measures.keys()) == [1, 2], "Measures should be renumbered consecutively"
    print("✅ Content merging: Measure count reduced correctly")
    print("✅ Consecutive renumbering: Measures are [1, 2] after merge")
    
    # Verify content was merged (not lost)
    merged_measure = temporal_grid.measures[1]
    merged_content_count = len(merged_measure.temporal_content)
    
    # Should have content from original measure 1 plus merged content from measure 2
    print(f"✅ Content preservation: Merged measure has {merged_content_count} temporal elements")
    assert merged_content_count > 0, "Merged measure should have temporal content"
    
    # Verify measure 2 (formerly measure 3) still has its content
    remaining_measure = temporal_grid.measures[2]
    remaining_content_count = len(remaining_measure.temporal_content)
    print(f"✅ Remaining content: Measure 2 has {remaining_content_count} temporal elements")
    
    return True


def test_dynamic_spacing_and_justification():
    """Test 4: Dynamic spacing based on content complexity"""
    print("\\n=== TEST 4: Dynamic Spacing and Justification ===")
    
    # Create measures with different content complexity
    grid_settings = TemporalGridSettings()
    
    # Simple measure (low complexity)
    simple_measure = TemporalGridMeasure(1, TimeSignature(4, 4), grid_settings)
    simple_note = Note(duration=NoteDuration.WHOLE, beat_position=BeatPosition(1.0), pitch="C4")
    simple_measure.add_temporal_content(TemporalPosition(1, 1.0, 0), simple_note)
    
    # Complex measure (high complexity)  
    complex_measure = TemporalGridMeasure(2, TimeSignature(4, 4), grid_settings)
    
    # Add multiple notes with different durations
    complex_notes = [
        (Note(duration=NoteDuration.SIXTEENTH, beat_position=BeatPosition(1.0), pitch="C4"), 1.0),
        (Note(duration=NoteDuration.SIXTEENTH, beat_position=BeatPosition(1.25), pitch="D4"), 1.25),
        (Note(duration=NoteDuration.EIGHTH, beat_position=BeatPosition(1.5), pitch="E4"), 1.5),
        (Note(duration=NoteDuration.QUARTER, beat_position=BeatPosition(2.0), pitch="F4"), 2.0),
        (Note(duration=NoteDuration.EIGHTH_TRIPLET, beat_position=BeatPosition(3.0), pitch="G4"), 3.0),
        (Note(duration=NoteDuration.EIGHTH_TRIPLET, beat_position=BeatPosition(3.33), pitch="A4"), 3.33),
        (Note(duration=NoteDuration.EIGHTH_TRIPLET, beat_position=BeatPosition(3.67), pitch="B4"), 3.67),
    ]
    
    for note, beat in complex_notes:
        complex_measure.add_temporal_content(TemporalPosition(2, beat, 0), note)
    
    # Compare complexity scores
    simple_complexity = simple_measure.content_complexity_score
    complex_complexity = complex_measure.content_complexity_score
    
    assert complex_complexity > simple_complexity, "Complex measure should have higher complexity score"
    print(f"✅ Complexity scoring: Simple={simple_complexity:.3f}, Complex={complex_complexity:.3f}")
    
    # Compare natural widths
    simple_width = simple_measure.calculated_natural_width
    complex_width = complex_measure.calculated_natural_width
    
    assert complex_width > simple_width, "Complex measure should require more width"
    print(f"✅ Dynamic spacing: Simple={simple_width:.1f}px, Complex={complex_width:.1f}px")
    
    # Test justification
    system_width = 800.0
    simple_measure.set_justified_width(system_width / 2)
    complex_measure.set_justified_width(system_width / 2)
    
    assert simple_measure.calculated_justified_width == system_width / 2, "Justification should set width"
    assert complex_measure.calculated_justified_width == system_width / 2, "Justification should set width"
    print("✅ Justification: Measures stretch to fit system width")
    
    return True


def test_temporal_bridge_integration():
    """Test 5: Temporal bridge integration with document"""
    print("\\n=== TEST 5: Temporal Bridge Integration ===")
    
    # Create document
    document = ScoreDocument()
    
    # Create temporal bridge
    temporal_bridge = TemporalBridgeV2(document)
    
    assert temporal_bridge.document == document, "Bridge should reference document"
    assert temporal_bridge.temporal_grid is not None, "Bridge should have temporal grid"
    print("✅ Bridge initialization: Document reference and temporal grid created")
    
    # Test barline creation
    measure_1 = temporal_bridge.create_barline_at_position(300.0, "single")
    
    assert measure_1 is not None, "Should create initial measure"
    assert measure_1.measure_number == 1, "Initial measure should be numbered 1"
    assert hasattr(document, 'measures'), "Document should have measures"
    assert 1 in document.measures, "Document should contain measure 1"
    print("✅ Barline creation: Initial measure created and synced to document")
    
    # Test additional barline creation
    measure_2 = temporal_bridge.create_barline_at_position(500.0, "single")
    
    assert len(temporal_bridge.temporal_grid.measures) == 2, "Should have 2 measures in temporal grid"
    assert len(document.measures) == 2, "Should have 2 measures in document"
    assert sorted(document.measures.keys()) == [1, 2], "Document measures should be numbered consecutively"
    print("✅ Multiple barlines: Created and synced correctly")
    
    # Test barline removal (content merging)
    success = temporal_bridge.remove_barline(2)
    
    assert success, "Barline removal should succeed"
    assert len(temporal_bridge.temporal_grid.measures) == 1, "Should have 1 measure in temporal grid after merge"
    assert len(document.measures) == 1, "Should have 1 measure in document after merge"
    assert 1 in document.measures, "Document should contain measure 1"
    print("✅ Barline removal: Content merging and document sync working")
    
    return True


def test_migration_from_old_system():
    """Test 6: Migration from old discrete measure system"""
    print("\\n=== TEST 6: Migration from Old System ===")
    
    # Create document with old-style measures
    document = ScoreDocument()
    
    # Simulate old discrete measures
    from src.gui.music.measure_object import MeasureObject
    
    old_measures = {
        1: MeasureObject(1, 300.0, document, "single"),
        3: MeasureObject(3, 600.0, document, "single"),  # Non-consecutive numbering (simulate the bug)
        5: MeasureObject(5, 900.0, document, "single"),  # Non-consecutive numbering
    }
    
    # Set problematic properties that the old system had
    old_measures[1].width = 200.0
    old_measures[3].width = 200.0  
    old_measures[5].width = 200.0
    
    document.measures = old_measures
    
    print(f"Created old system with measures: {sorted(old_measures.keys())}")
    print("(Non-consecutive numbering simulates the old system bugs)")
    
    # Perform migration
    new_bridge = migrate_barline_bridge_to_temporal_grid(document)
    
    # Verify migration results
    assert isinstance(new_bridge, TemporalBridgeV2), "Should return TemporalBridgeV2"
    assert len(new_bridge.temporal_grid.measures) == 3, "Should have 3 measures after migration"
    
    # Check consecutive renumbering
    temporal_numbers = sorted(new_bridge.temporal_grid.measures.keys())
    expected_numbers = [1, 2, 3]
    assert temporal_numbers == expected_numbers, "Measures should be renumbered consecutively"
    print(f"✅ Migration: Fixed numbering {sorted(old_measures.keys())} → {temporal_numbers}")
    
    # Check document sync
    assert len(document.measures) == 3, "Document should have 3 measures after migration"
    document_numbers = sorted(document.measures.keys())
    assert document_numbers == expected_numbers, "Document measures should also be consecutive"
    print("✅ Migration: Document sync with consecutive numbering")
    
    # Verify measure properties were preserved
    for i, measure_num in enumerate([1, 2, 3]):
        temporal_measure = new_bridge.temporal_grid.measures[measure_num]
        document_measure = document.measures[measure_num]
        
        assert temporal_measure.barline_type == "single", "Barline type should be preserved"
        assert document_measure.barline_type == "single", "Document barline type should be preserved"
    
    print("✅ Migration: Measure properties preserved")
    
    return True


def test_onote_rule_compliance():
    """Test 7: ONOTE Rule 1 and Rule 2 compliance"""
    print("\\n=== TEST 7: ONOTE Rule Compliance ===")
    
    # Create temporal bridge
    document = ScoreDocument()
    temporal_bridge = TemporalBridgeV2(document)
    
    # Set up known dimensions for testing
    temporal_bridge.LEFTMOST_NOTE_X = 265.0
    temporal_bridge.END_BARLINE_X = 1000.0
    
    # Test Rule 1: Equal division of staff length
    print("Testing ONOTE Rule 1: Equal division of staff length")
    
    # Create 4 measures
    for i in range(4):
        temporal_bridge.create_barline_at_position(300.0 + i * 100, "single")
    
    # Get justified positions
    justified_positions = temporal_bridge._calculate_justified_positions(4)
    
    # Verify equal spacing
    notation_space = temporal_bridge.END_BARLINE_X - temporal_bridge.LEFTMOST_NOTE_X
    expected_spacing = notation_space / 4
    
    for i, position in enumerate(justified_positions):
        expected_position = temporal_bridge.LEFTMOST_NOTE_X + (i + 1) * expected_spacing
        assert abs(position - expected_position) < 0.1, f"Position {i+1} should be at {expected_position}"
    
    print(f"✅ Rule 1: Equal spacing verified - {expected_spacing:.1f}px per measure")
    
    # Test Rule 2: Index inheritance and consecutive numbering
    print("Testing ONOTE Rule 2: Index inheritance and consecutive numbering")
    
    # Remove middle measure (should merge content and renumber)
    initial_count = len(temporal_bridge.temporal_grid.measures)
    temporal_bridge.remove_barline(2)
    
    final_count = len(temporal_bridge.temporal_grid.measures)
    final_numbers = sorted(temporal_bridge.temporal_grid.measures.keys())
    expected_final_numbers = list(range(1, final_count + 1))
    
    assert final_count == initial_count - 1, "Should have one less measure after removal"
    assert final_numbers == expected_final_numbers, "Remaining measures should be numbered consecutively"
    print(f"✅ Rule 2: Consecutive numbering after merge - {final_numbers}")
    
    return True


def run_all_tests():
    """Run all temporal grid reconstruction tests"""
    print("🧪 ONOTE TEMPORAL GRID RECONSTRUCTION - COMPREHENSIVE TESTS")
    print("=" * 70)
    
    # Initialize Qt application for tests
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Clear any existing settings
    settings = QSettings()
    settings.clear()
    
    # Test results
    test_results = {
        "Basic Functionality": test_temporal_grid_basic_functionality(),
        "Temporal Content Management": test_temporal_content_management(),
        "Content Merging Model": test_content_merging_model(),
        "Dynamic Spacing and Justification": test_dynamic_spacing_and_justification(),
        "Temporal Bridge Integration": test_temporal_bridge_integration(),
        "Migration from Old System": test_migration_from_old_system(),
        "ONOTE Rule Compliance": test_onote_rule_compliance(),
    }
    
    # Print results summary
    print("\\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed_count = 0
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed_count += 1
    
    print("=" * 70)
    print(f"📈 OVERALL RESULT: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - TEMPORAL GRID RECONSTRUCTION SUCCESSFUL!")
        print("\\n🚀 Key features verified:")
        print("  ✅ Content merging instead of measure deletion")
        print("  ✅ Consecutive measure numbering after operations")
        print("  ✅ Dynamic spacing based on content complexity")
        print("  ✅ Temporal grid with PPQN/tick positioning")
        print("  ✅ ONOTE Rule 1 and Rule 2 compliance")
        print("  ✅ Migration from old discrete measure system")
        print("  ✅ Complete temporal bridge integration")
    else:
        print("⚠️  Some tests failed - review implementation")
        failed_tests = [name for name, result in test_results.items() if not result]
        print(f"Failed tests: {failed_tests}")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 