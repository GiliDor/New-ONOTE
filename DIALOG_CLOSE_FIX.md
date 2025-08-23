# Dialog Close Fix for Score Menu Toggle

## Issue
When in score setup mode with the score setup dialog open, clicking the "Score Setup" menu item (which shows "Edit Mode") would switch the page to edit mode but leave the dialog open, creating a confusing user experience.

## Solution
Modified the `_handle_score_setup_toggle` method in `DesktopWindow` to properly close the score setup dialog when switching from setup to edit mode.

## Changes Made

### 1. Added Dialog Tracking
Added a `score_setup_dialog` attribute to track the currently open dialog:

```python
# Dialog tracking
self.score_setup_dialog = None
```

### 2. Updated Dialog Creation
Modified `open_score_setup()` to store the dialog reference:

```python
# Store dialog reference
self.score_setup_dialog = dialog

# ... dialog execution ...

# Clear dialog reference
self.score_setup_dialog = None
```

### 3. Enhanced Toggle Logic
Updated `_handle_score_setup_toggle()` to close the dialog when switching modes:

```python
def _handle_score_setup_toggle(self):
    """Handle score setup action toggle between setup and edit modes."""
    if self.music_page and self.music_page.mode == "setup":
        # Currently in setup mode, switch to edit mode
        # Close any open score setup dialog first
        if self.score_setup_dialog and self.score_setup_dialog.isVisible():
            self.score_setup_dialog.close()
        
        self._enter_edit_mode()
        self.status_bar.showMessage("Switched to edit mode")
    else:
        # Currently in edit mode, open score setup dialog
        self.open_score_setup()
```

## Expected Behavior

### Before Fix
- User opens score setup dialog (pink page)
- User clicks "Score Setup" menu item
- Page switches to edit mode (white) but dialog remains open ❌

### After Fix
- User opens score setup dialog (pink page)
- User clicks "Score Setup" menu item (shows "Edit Mode")
- Dialog closes and page switches to edit mode (white) ✅
- User clicks "Edit Mode" menu item (shows "Score Setup")
- Dialog opens and page switches to setup mode (pink) ✅

## Testing

Run the test script to verify the fix:

```bash
python test_dialog_close_fix.py
```

### Manual Test Steps
1. Launch ONOTE Desktop (auto-opens score setup dialog)
2. Verify dialog is open and page is in setup mode (pink)
3. Click "Score Setup" menu item (should show "Edit Mode")
4. Verify dialog closes and page switches to edit mode (white)
5. Click "Edit Mode" menu item (should show "Score Setup")
6. Verify dialog opens again and page switches to setup mode

## Files Modified
- `src/gui/desktop_window.py` - Added dialog tracking and close logic

## Files Added
- `test_dialog_close_fix.py` - Test script to verify the fix
- `DIALOG_CLOSE_FIX.md` - This documentation

## Benefits
- ✅ Improved user experience with consistent dialog behavior
- ✅ Clear visual feedback when switching between modes
- ✅ Prevents confusion from having dialogs open in wrong modes
- ✅ Maintains proper state synchronization between UI elements 