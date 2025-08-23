#!/usr/bin/env python3
"""
Test script to ensure that changing any parameter in the Full Score Options dialog does not affect unrelated parameters.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication
from src.gui.music.dialogs.full_score_options_dialog import FullScoreOptionsDialog
from src.gui.music.score_document import ScoreDocument

def get_all_settings(dialog):
    return {
        'clef_color': dialog.clef_color_value,
        'key_sig_color': dialog.key_sig_color_value,
        'time_sig_color': dialog.time_sig_color_value,
        'staff_name_color': dialog.staff_name_color_value,
        'section_name_color': dialog.section_name_color_value,
        'clef_font_size': dialog.clef_font_size.value(),
        'key_sig_font_size': dialog.key_sig_font_size.value(),
        'time_sig_font_size': dialog.time_sig_font_size.value(),
        'staff_name_font_size': dialog.staff_name_font_size.value(),
        'section_name_font_size': dialog.section_name_font_size.value(),
        'clef_x': dialog.clef_horizontal.value(),
        'clef_y': dialog.clef_vertical.value(),
        'key_sig_x': dialog.key_sig_horizontal.value(),
        'key_sig_y': dialog.key_sig_vertical.value(),
        'time_sig_x': dialog.time_sig_horizontal.value(),
        'time_sig_y': dialog.time_sig_vertical.value(),
        'staff_name_x': dialog.staff_name_horizontal.value(),
        'staff_name_y': dialog.staff_name_vertical.value(),
        'section_name_x': dialog.section_name_horizontal.value(),
        'section_name_y': dialog.section_name_vertical.value(),
        # Add more as needed
    }

def set_all_settings(dialog, values):
    dialog.clef_color_value = values['clef_color']
    dialog.key_sig_color_value = values['key_sig_color']
    dialog.time_sig_color_value = values['time_sig_color']
    dialog.staff_name_color_value = values['staff_name_color']
    dialog.section_name_color_value = values['section_name_color']
    dialog.clef_font_size.setValue(values['clef_font_size'])
    dialog.key_sig_font_size.setValue(values['key_sig_font_size'])
    dialog.time_sig_font_size.setValue(values['time_sig_font_size'])
    dialog.staff_name_font_size.setValue(values['staff_name_font_size'])
    dialog.section_name_font_size.setValue(values['section_name_font_size'])
    dialog.clef_horizontal.setValue(values['clef_x'])
    dialog.clef_vertical.setValue(values['clef_y'])
    dialog.key_sig_horizontal.setValue(values['key_sig_x'])
    dialog.key_sig_vertical.setValue(values['key_sig_y'])
    dialog.time_sig_horizontal.setValue(values['time_sig_x'])
    dialog.time_sig_vertical.setValue(values['time_sig_y'])
    dialog.staff_name_horizontal.setValue(values['staff_name_x'])
    dialog.staff_name_vertical.setValue(values['staff_name_y'])
    dialog.section_name_horizontal.setValue(values['section_name_x'])
    dialog.section_name_vertical.setValue(values['section_name_y'])
    # Add more as needed

def assert_settings_unchanged(before, after, changed_keys):
    for k in before:
        if k not in changed_keys:
            assert before[k] == after[k], f"Parameter '{k}' changed unexpectedly: {before[k]} -> {after[k]}"

def test_isolation():
    app = QApplication.instance() or QApplication([])
    document = ScoreDocument()
    document.settings = {}
    dialog = FullScoreOptionsDialog()
    dialog.document = document
    dialog.show()
    # Set all to known values
    initial = {
        'clef_color': '#111111',
        'key_sig_color': '#222222',
        'time_sig_color': '#333333',
        'staff_name_color': '#444444',
        'section_name_color': '#555555',
        'clef_font_size': 10,
        'key_sig_font_size': 11,
        'time_sig_font_size': 12,
        'staff_name_font_size': 13,
        'section_name_font_size': 14,
        'clef_x': 1,
        'clef_y': 2,
        'key_sig_x': 3,
        'key_sig_y': 4,
        'time_sig_x': 5,
        'time_sig_y': 6,
        'staff_name_x': 7,
        'staff_name_y': 8,
        'section_name_x': 9,
        'section_name_y': 10,
    }
    set_all_settings(dialog, initial)
    # 1. Change clef color
    before = get_all_settings(dialog)
    dialog.clef_color_value = '#abcdef'
    after = get_all_settings(dialog)
    assert after['clef_color'] == '#abcdef', 'Clef color did not update.'
    assert_settings_unchanged(before, after, ['clef_color'])
    # 2. Change key signature color
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.key_sig_color_value = '#bcdefa'
    after = get_all_settings(dialog)
    assert after['key_sig_color'] == '#bcdefa', 'Key sig color did not update.'
    assert_settings_unchanged(before, after, ['key_sig_color'])
    # 3. Change time signature color
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.time_sig_color_value = '#cdefab'
    after = get_all_settings(dialog)
    assert after['time_sig_color'] == '#cdefab', 'Time sig color did not update.'
    assert_settings_unchanged(before, after, ['time_sig_color'])
    # 4. Change staff name color
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.staff_name_color_value = '#defabc'
    after = get_all_settings(dialog)
    assert after['staff_name_color'] == '#defabc', 'Staff name color did not update.'
    assert_settings_unchanged(before, after, ['staff_name_color'])
    # 5. Change section name color
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.section_name_color_value = '#efabcd'
    after = get_all_settings(dialog)
    assert after['section_name_color'] == '#efabcd', 'Section name color did not update.'
    assert_settings_unchanged(before, after, ['section_name_color'])
    # 6. Change clef font size
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.clef_font_size.setValue(20)
    after = get_all_settings(dialog)
    assert after['clef_font_size'] == 20, 'Clef font size did not update.'
    assert_settings_unchanged(before, after, ['clef_font_size'])
    # 7. Change clef x position
    set_all_settings(dialog, initial)
    before = get_all_settings(dialog)
    dialog.clef_horizontal.setValue(99)
    after = get_all_settings(dialog)
    assert after['clef_x'] == 99, 'Clef x did not update.'
    assert_settings_unchanged(before, after, ['clef_x'])
    print('All isolation tests passed.')

if __name__ == '__main__':
    test_isolation() 