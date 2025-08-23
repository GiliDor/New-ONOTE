# Crash Fix - Score Setup Widget

## Issue
The application was crashing with a `NameError: name 'from_index' is not defined` in the `move_staff_down` method of `score_setup_widget.py`.

## Root Cause
The `move_staff_up` and `move_staff_down` methods were incomplete - they had placeholder comments but no actual implementation. The variables `from_index` and `to_index` were being used in debug prints and signal emissions without being defined.

## Fix Applied
Implemented the complete `move_staff_up` and `move_staff_down` methods in `src/gui/music/score_setup_widget.py`:

### move_staff_up method:
- Gets selected items from staff list
- Checks if item can be moved up (not at index 0)
- Calculates from_index and to_index
- Moves item using takeTopLevelItem and insertTopLevelItem
- Selects the moved item
- Marks unapplied changes
- Emits staff_reordered signal

### move_staff_down method:
- Gets selected items from staff list  
- Checks if item can be moved down (not at last index)
- Calculates from_index and to_index
- Moves item using takeTopLevelItem and insertTopLevelItem
- Selects the moved item
- Marks unapplied changes
- Emits staff_reordered signal

## Result
✅ Application no longer crashes when using staff reordering buttons
✅ Staff up/down movement works correctly
✅ Signal emissions work properly for immediate rendering
✅ Debug output shows proper from_index and to_index values

## Files Modified
- `src/gui/music/score_setup_widget.py` - Fixed move_staff_up and move_staff_down methods 