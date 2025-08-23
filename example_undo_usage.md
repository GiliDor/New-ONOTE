# Using Undo/Redo in ONOTE's White Mode (EDIT Mode)

## Overview

ONOTE now has comprehensive undo/redo functionality that works seamlessly in white mode (EDIT mode) without requiring you to enter score setup mode. This allows you to focus on editing while having full control over changes.

## Key Features

✅ **Works in White Mode**: No need to switch to setup mode for undo/redo  
✅ **Comprehensive Coverage**: All major operations are undoable  
✅ **Keyboard Shortcuts**: Standard Ctrl+Z and Shift+Cmd+Z shortcuts  
✅ **Context Aware**: Each undo shows what operation is being reversed  
✅ **Auto UI Updates**: Interface refreshes automatically after undo/redo  
✅ **Memory Efficient**: Limits to 50 undo states to prevent memory issues  

## Supported Undoable Operations

### Staff Management
- **Add Staff** - Adding instruments via the setup dialog
- **Remove Staff** - Deleting staves from your score  
- **Move Staff Up/Down** - Reordering staves in the score
- **Change Staff Name** - Renaming instrument parts

### Musical Properties  
- **Change Clef** - Switching between treble, bass, alto, percussion clefs
- **Change Key Signature** - Modifying the key of individual staves
- **Change Staff Properties** - Updating staff type, name, abbreviation

### Mode Operations
- **Enter/Exit Setup Mode** - Mode switching is fully undoable
- **Apply Setup Changes** - All setup dialog changes can be undone

## How to Use

### Basic Usage
1. **Work in White Mode**: Perform your normal editing operations in EDIT mode (white background)
2. **Undo with Ctrl+Z**: Press Ctrl+Z to undo the last operation
3. **Redo with Shift+Cmd+Z**: Press Shift+Cmd+Z to redo an undone operation

### Advanced Features
- **Smart Mode Handling**: If you undo to a state that was in setup mode, the setup dialog will automatically open
- **Setup Widget Sync**: When setup dialog is open, it automatically refreshes to show the current state after undo/redo
- **Context Messages**: Console shows what operation is being undone (useful for debugging)

## Example Workflow

```
1. Start in white mode (EDIT mode)
2. Add a violin staff via Score Setup dialog → [Undoable]
3. Change its clef to bass → [Undoable] 
4. Add a cello staff → [Undoable]
5. Move violin staff down → [Undoable]
6. Press Ctrl+Z → Undoes the staff move
7. Press Ctrl+Z → Undoes adding the cello 
8. Press Shift+Cmd+Z → Redoes adding the cello
```

## Implementation Details

### State Saving
- Operations automatically save document state before making changes
- Each saved state includes a context description (e.g., "Add Staff", "Change Clef")
- Duplicate states are detected and skipped to avoid cluttering the undo stack

### Memory Management  
- Maximum of 50 undo states are kept
- Older states are automatically removed when limit is exceeded
- Redo stack is cleared when new operations are performed

### Document Restoration
- Full document state restoration including:
  - Staff layout and positioning
  - Section assignments  
  - Musical properties (clef, key, time signature)
  - Staff types and names

## Technical Architecture

The undo/redo system is built into the `ScoreDocument` class with:
- `undo_stack`: Stores previous document states  
- `redo_stack`: Stores states for redo operations
- `save_state()`: Captures current state with context
- `undo()` / `redo()`: Restores previous/next states
- `_restore_state()`: Applies saved state to document

## Benefits

1. **Non-Disruptive**: Work stays in white mode for normal editing
2. **Safety Net**: Quickly recover from accidental changes  
3. **Experimentation**: Try different arrangements knowing you can undo
4. **Workflow Efficiency**: No need to manually re-enter setup mode
5. **Complete Coverage**: All major operations are reversible

## Future Enhancements

The system can be easily extended to support:
- Note editing operations (when note input is implemented)
- Measure operations (add/remove measures)
- Page layout changes
- Tempo and dynamics changes
- Copy/paste operations

---

**Ready to use now!** The undo/redo system is fully implemented and working in your ONOTE application. Start editing and use Ctrl+Z / Shift+Cmd+Z as needed! 