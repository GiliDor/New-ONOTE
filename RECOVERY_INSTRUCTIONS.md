# ONOTE Barline/Measure System Recovery Instructions

## Stable Working State: v1.2-barline-fixes

This document provides instructions for recovering the working barline/measure system if the restructure needs to be reverted.

### Recovery Commands

#### 1. Return to Stable Working State
```bash
# Navigate to ONOTE project directory
cd /Users/gilidor/Projects/ONOTE

# Restore to the tagged working state
git checkout v1.2-barline-fixes

# Or checkout the development branch with working code
git checkout development-v1.2-next
```

#### 2. Verify Working Features
After recovery, these features should work correctly:

**✅ Barline Positioning**
- All barlines positioned consistently at x=1136
- No gap between automatic and user-created barlines
- Final barlines properly aligned

**✅ Measure Number Positioning** 
- Measure numbers appear on ALL staves (no missing staves)
- Proper vertical distribution without overlap
- No y-clamping at 400px limit

**✅ Undo/Redo System**
- Ctrl+Z for undo (50 steps)
- Ctrl+Y for redo
- Granular barline-by-barline undo
- Proper state management

**✅ Justified Positioning**
- Equal measure spacing across available width
- Shuffle insertion (click anywhere to insert measures)
- Sequential measure numbering (1, 2, 3, 4...)

**✅ Settings Manager**
- Proper default values (-34 offset for measure numbers)
- Consistent key naming
- Cached settings reset capability

### Working Files State

The following key files contain the working implementations:

#### Core Files Modified
- `src/core/settings_manager.py` - Default values and key consistency
- `src/gui/dialogs/preferences_dialog.py` - UI defaults alignment
- `src/gui/music/measure_numbers.py` - Positioning logic fixes
- `src/gui/music/barline_temporal_bridge.py` - Shuffle insertion and coordinates
- `src/gui/music/staff_view.py` - Grid generation and constants
- `src/gui/music/score_renderer.py` - Barline positioning fixes
- `src/gui/music/measure_manager.py` - Layout management

#### Test Files Available
- `test_staff_debugging.py` - Staff structure analysis
- `reset_cached_settings.py` - Settings reset utility

### Key Technical Details

#### Barline Positioning Fix
```python
# In score_renderer.py line ~1974
final_barline_x = 1136.0  # Fixed consistent positioning
```

#### Measure Number Y-Clamping Fix
```python
# In measure_numbers.py - REMOVED the problematic y > 400 limit
if y < 30:
    y = 30  # Only minimum visible position
# REMOVED: if y > 400: y = 400  # This was causing overlap
```

#### Settings Defaults Fix
```python
# In settings_manager.py
"layout/measure_numbers_horizontal_offset": -34,
"layout/measure_numbers_h_offset": -34,  # Both keys for consistency
```

### Known Issues at Recovery Point

The following issues existed and prompted the restructure:

1. **Final barline positioning** - Still complex with multiple logic paths
2. **Multiple initialization paths** - Too many ways to create initial measures
3. **Mode switching inconsistencies** - Different behavior in setup vs edit modes
4. **Temporal bridge complexity** - Overly complex bridge system

### Remote Repository Sync

To sync with remote repository:

```bash
# Push the tagged state to remote (if desired)
git push origin v1.2-barline-fixes

# Push the development branch
git push origin development-v1.2-next

# Push the restructure branch (if working on it)
git push origin restructure-barline-system
```

### Environment Setup

**Python Environment:**
```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt
```

**Launch Application:**
```bash
# Standard launch
python launch_onote.py

# Alternative launch methods
python run_onote.sh
python run.py
```

### Troubleshooting

#### If Measures Don't Show Numbers
```bash
# Reset cached settings
python reset_cached_settings.py
```

#### If Barlines Are Misaligned
Check that the following constants are consistent:
- `END_BARLINE_X = 1136.0` in `barline_temporal_bridge.py`
- `final_barline_x = 1136.0` in `score_renderer.py`

#### If Undo/Redo Doesn't Work
Verify these keyboard shortcuts in `main_window.py`:
- Ctrl+Z → undo action
- Ctrl+Y → redo action

### Commit Information

**Stable Commit:** acc8843 (tagged as v1.2-barline-fixes)
**Branch:** development-v1.2-next
**Restructure Branch:** restructure-barline-system

---

*Created: $(date)*
*Purpose: Recovery instructions for ONOTE barline/measure system* 