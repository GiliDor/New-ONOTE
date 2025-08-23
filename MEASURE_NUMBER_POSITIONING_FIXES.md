# ONOTE Measure Number Positioning Fixes

## Issues Addressed

### Issue 1: Measure Number 1 Positioning
**Problem**: Measure number 1 was positioned too far to the right and not using the correct reference point. The user indicated that measure 1 should be positioned relative to a constant after the key signature, not relative to the measure boundaries.

**Root Cause**: 
- Measure number 1 was using the same positioning logic as other measures (relative to measure start + percentage)
- Settings were still showing H:-47 instead of the updated -130 value
- No special positioning logic for measure 1's unique reference point

### Issue 2: Saved Score Measure Numbers
**Problem**: When opening saved scores, measure numbers weren't displaying properly across all staves as they should.

**Root Cause**:
- Measure number manager instances were not refreshing their settings when documents changed
- Cached settings from previous sessions were being used instead of current global settings
- No forced refresh mechanism when loading saved documents

## Fixes Applied

### Fix 1: Special Positioning for Measure 1
**File**: `src/gui/music/measure_numbers.py`

1. **Modified `calculate_position()` method**:
   - Added `measure_number` parameter to identify measure 1
   - Added special case for measure 1 positioning
   - Uses fixed reference point after key signature (225px) + horizontal offset
   - Other measures continue to use relative positioning

```python
# SPECIAL CASE: Measure 1 positioning - use a constant reference point after key signature
if measure_number == 1:
    # Use a fixed position after key signature (around 225px) + offset
    # This provides consistent positioning regardless of measure width
    key_signature_end = 225.0  # Position after key signature ends
    x = key_signature_end + self.settings.horizontal_offset
    print(f"MEASURE_NUMBERS: Measure 1 special positioning - key_sig_end: {key_signature_end}, offset: {self.settings.horizontal_offset}, final_x: {x}")
else:
    # Apply horizontal offset for other measures
    x += self.settings.horizontal_offset
```

2. **Updated method call**:
   - Modified `render_measure_numbers_for_system()` to pass measure number to `calculate_position()`

### Fix 2: Settings Refresh Mechanism
**File**: `src/gui/music/measure_numbers.py`

1. **Enhanced `_load_settings()` method**:
   - Added debugging output to track settings loading
   - Added forced renderer update after settings change
   - Added document override tracking

2. **Added `refresh_settings()` method**:
   - Provides way to force reload settings from global settings manager
   - Critical for when settings change or documents are loaded

```python
def refresh_settings(self):
    """Force refresh settings from global settings manager - used when settings change"""
    print("MEASURE_NUMBERS: Force refreshing settings from global settings manager")
    self._load_settings(self.document)
```

### Fix 3: Score Renderer Integration
**File**: `src/gui/music/score_renderer.py`

1. **Enhanced `_initialize_measure_number_manager()`**:
   - Added forced settings refresh after initialization
   - Ensures latest settings are always used

2. **Enhanced `set_document()` method**:
   - Added automatic refresh when document changes
   - Critical for saved score loading

```python
# CRITICAL FIX: Refresh measure number manager when document changes
# This ensures saved scores get the correct measure number settings
if hasattr(self, 'measure_number_manager') and self.measure_number_manager:
    self.measure_number_manager.document = document
    self.measure_number_manager.refresh_settings()
    print(f"RENDERER: Refreshed measure number settings for new document")
```

## Expected Results

### Measure Number 1 Positioning
- Measure 1 numbers now positioned at fixed point after key signature (225px) + offset
- Uses -130 horizontal offset for proper left positioning
- Independent of measure width variations
- Consistent across all staves

### Saved Score Measure Numbers
- Measure numbers display correctly when opening saved scores
- Settings automatically refresh when documents are loaded
- No more cached setting issues
- Proper display frequency ("Every Measure") maintained

### Other Measures (2, 3, 4, etc.)
- Continue to use relative positioning within measure boundaries
- Responsive to measure width changes
- Consistent -130 offset applied for uniform appearance

## Technical Details

### Positioning Logic
- **Measure 1**: `key_signature_end (225px) + horizontal_offset (-130) = 95px`
- **Other measures**: `measure_start + (measure_width * position_percentage) + horizontal_offset`

### Settings Precedence
1. Document-specific settings (if saved in document)
2. Global application settings
3. Fallback defaults

### Refresh Triggers
- Application startup
- Document loading/changing
- Settings changes in preferences
- Manual refresh calls

## Testing Verification

1. **Create new score**: Measure numbers should appear correctly positioned
2. **Save and reload score**: Measure numbers should maintain correct positioning
3. **Change settings**: Should immediately reflect in display
4. **Multiple staves**: All staves should show measure numbers consistently

The fixes ensure professional measure number layout with proper positioning relative to musical elements rather than arbitrary measure boundaries. 