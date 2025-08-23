# Immediate Rendering and Section Movement Fixes

## Issues Fixed

### Issue 1: Changes in Score Setup Dialog Not Rendering Immediately
**Problem**: Changes made in the Score Setup Dialog were not being applied immediately to the score rendering.

**Root Cause**: The signal handlers in `ScoreSetupDialog` were calling `self.setup_widget.apply_changes_immediate(options)` instead of applying changes directly to the document and forcing a render update.

**Solution**: 
1. **Added `apply_changes_immediate` method** to `ScoreSetupDialog` that:
   - Gets the document reference from the parent window
   - Applies options directly to the document
   - Forces a render update on the staff view
2. **Updated signal handlers** to call `self.apply_changes_immediate(options)` instead of the widget method
3. **Added `_apply_options_to_document` method** to handle the actual document updates

### Issue 2: Section Movement Not Skipping Complete Sections
**Problem**: When moving staves up/down in the Score Setup Dialog, the movement went through individual staves within sections instead of treating sections as single units.

**Root Cause**: The `move_staff_up` and `move_staff_down` methods were using simple index arithmetic without considering section boundaries.

**Solution**:
1. **Enhanced `move_staff_up` method** to:
   - Detect if the current staff is in a section
   - Find section boundaries
   - If at section start, move to previous section's start
   - If inside section, move to previous staff in same section
2. **Enhanced `move_staff_down` method** to:
   - Detect if the current staff is in a section
   - Find section boundaries  
   - If at section end, move to next section's start
   - If inside section, move to next staff in same section

## Files Modified

### `src/gui/music/score_setup_dialog.py`
- Added `apply_changes_immediate()` method
- Added `_apply_options_to_document()` method
- Updated signal handlers to use immediate rendering

### `src/gui/music/score_setup_widget.py`
- Enhanced `move_staff_up()` with section-aware movement
- Enhanced `move_staff_down()` with section-aware movement

## Results

✅ **Immediate Rendering**: Changes in Score Setup Dialog now apply immediately to the score
✅ **Section Movement**: Up/down movement now skips complete sections as single units
✅ **Signal Handling**: All signal handlers now properly trigger immediate rendering
✅ **Document Updates**: Changes are applied directly to the document for live preview

## Testing

The fixes ensure that:
1. Adding/removing staves shows immediately in the score
2. Changing staff options (clef, name, etc.) updates immediately
3. Reordering staves updates immediately
4. Moving staves up/down respects section boundaries
5. Sections are treated as single units during movement 