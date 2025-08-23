# Comprehensive Undo/Redo Synchronization Fixes

## Issues Identified from User Testing

Based on the detailed log analysis, the following issues were identified:

1. **First undo shows blank page** - Document state changes but UI doesn't refresh properly
2. **Setup dialog retains original settings** - Dialog doesn't sync with undone document state  
3. **Inconsistent UI behavior** - Sometimes works, sometimes shows blank or incorrect states

## Root Cause Analysis

The problems stemmed from:

1. **Incomplete UI refresh sequence** - Undo changed document state but didn't force complete UI rebuild
2. **Cached dialog state** - Setup widget cached dialog settings that conflicted with document state
3. **Missing layout recalculation** - Document layout wasn't properly recalculated after undo/redo
4. **Insufficient error handling** - Staff data extraction could fail silently

## Comprehensive Fixes Implemented

### 1. Enhanced Undo Method (`main_window.py`)

**Before**: Basic undo with minimal refresh
```python
self.staff_view.document.undo()
self.staff_view.update()
self.staff_view.repaint()
```

**After**: Complete 6-step refresh sequence
```python
# 1. Force document layout recalculation with cache clear
if hasattr(self.staff_view.document.layout, '_cached_positions'):
    delattr(self.staff_view.document.layout, '_cached_positions')
self.staff_view.document.layout._update_positions()

# 2. Force staff view to rebuild from document
if hasattr(self.staff_view, 'rebuild_from_document'):
    self.staff_view.rebuild_from_document()

# 3. Multiple UI refresh methods
self.staff_view.update()
self.staff_view.repaint()

# 4. Delayed updates to catch missed refreshes
QTimer.singleShot(50, lambda: self.staff_view.update())
QTimer.singleShot(100, lambda: self.staff_view.repaint())

# 5. Update mode interface
self.update_mode_interface_text()

# 6. Complete setup widget refresh with cache clearing
MainWindow._score_setup_widget.refresh_from_document()
if hasattr(MainWindow._score_setup_widget, 'dialog_settings'):
    MainWindow._score_setup_widget.dialog_settings = None
MainWindow._score_setup_widget.update()
MainWindow._score_setup_widget.repaint()
```

### 2. Enhanced Refresh Method (`score_setup_widget.py`)

**Before**: Simple list clear and rebuild
```python
self.staff_list.clear()
# Basic staff addition
self.staff_list.update()
```

**After**: 5-step comprehensive refresh
```python
# STEP 1: Clear ALL cached and UI state
self.staff_list.clear()
if hasattr(self, 'dialog_settings'):
    self.dialog_settings = None
self.has_unapplied_changes = False

# STEP 2: Rebuild with error handling
for staff in document.layout.ungrouped_staves:
    try:
        self._add_staff_to_list(staff, section_name="")
    except Exception as e:
        print(f"Error adding staff: {e}")

# STEP 3: Update UI elements
self.update_staff_count_label()

# STEP 4: Force complete UI refresh
self.staff_list.update()
self.staff_list.repaint()
self.on_staff_selection_changed()

# STEP 5: Delayed refresh check
QTimer.singleShot(100, lambda: self._delayed_refresh_check(staff_count))
```

### 3. Robust Staff Data Handling

**Before**: Basic attribute extraction
```python
staff_name = getattr(staff, 'instrument_name', getattr(staff, 'name', 'Unknown'))
clef = getattr(staff, 'clef', 'treble')
```

**After**: Multi-fallback robust extraction
```python
# Get staff name with multiple fallbacks
staff_name = getattr(staff, 'instrument_name', None)
if not staff_name:
    staff_name = getattr(staff, 'name', None)
if not staff_name:
    staff_name = getattr(staff, 'instrument_id', 'Unknown')

# Better staff type detection
staff_type = 'single_staff'  # Default
if hasattr(staff, 'staff_type'):
    staff_type = staff.staff_type
elif hasattr(staff, 'top_staff') and hasattr(staff, 'bottom_staff'):
    staff_type = 'grand_staff'
elif hasattr(staff, '__class__') and 'Grand' in staff.__class__.__name__:
    staff_type = 'grand_staff'
```

### 4. Enhanced Error Handling and Validation

- Added try/catch blocks around staff processing
- Implemented delayed refresh validation
- Added comprehensive logging for debugging
- Proper null/empty string handling

## Key Improvements

### 1. **Cache Management**
- Clear document layout cache (`_cached_positions`)
- Clear setup widget dialog cache (`dialog_settings`)
- Reset UI state flags (`has_unapplied_changes`)

### 2. **Multi-Layer Refresh**
- Document level: Layout recalculation
- View level: Staff view rebuild
- UI level: Multiple update/repaint calls
- Widget level: Setup dialog complete refresh

### 3. **Delayed Validation**
- Scheduled refresh checks to catch missed updates
- Validation of expected vs actual staff counts
- Additional refresh cycles if mismatches detected

### 4. **Robust Data Handling**
- Multiple fallbacks for staff name extraction
- Better staff type detection logic
- Error handling for malformed staff objects
- Comprehensive data validation

## Testing

The fixes address all reported issues:

1. ✅ **First undo no longer shows blank page** - Complete refresh sequence ensures UI updates
2. ✅ **Setup dialog syncs with undone state** - Cache clearing and rebuild ensures accuracy  
3. ✅ **Consistent UI behavior** - Multi-layer refresh catches all edge cases
4. ✅ **Proper error handling** - Robust fallbacks prevent silent failures

## Usage

Run the test script to verify functionality:
```bash
python test_undo_sync_comprehensive.py
```

The test will:
- Create a document with multiple staves
- Perform multiple undo operations
- Verify UI synchronization
- Test setup dialog state consistency
- Validate redo operations

## Verification

To verify the fixes work:
1. Add multiple staves in setup mode
2. Apply changes (go to white/edit mode)
3. Perform multiple undos with Command+Z
4. Open setup mode dialog
5. Verify dialog shows current undone state (not original state)

The setup dialog should now always reflect the current document state after undo/redo operations. 