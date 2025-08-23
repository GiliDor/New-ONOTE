# Score Setup Dialog Integration

## Overview

The score setup dialog has been fully integrated with the ONOTE desktop window, providing a seamless workflow from initial score configuration to notation editing.

## Key Features

### 🎯 **Automatic Setup Mode**
- **Pink Page**: Desktop window starts in setup mode with a pink page background
- **Grid Pattern**: Setup mode displays a light pink grid for visual guidance
- **Traditional ONOTE Look**: Matches the classic ONOTE setup mode appearance

### 🔄 **Seamless Mode Transitions**
- **Setup → Edit**: Automatic transition when score setup is applied
- **Visual Feedback**: Page color changes from pink (setup) to white (edit)
- **Status Updates**: Real-time status bar messages guide the user

### 🎨 **Integrated Dialog System**
- **Direct Integration**: Score setup dialog connects directly to the music page's staff view
- **Parent-Child Relationship**: Dialog uses staff view as parent for proper data flow
- **Signal Handling**: Automatic completion detection and mode switching

## Implementation Details

### Desktop Window Integration

The `DesktopWindow` class now includes:

```python
def _enter_setup_mode(self):
    """Enter setup mode (pink page)."""
    if self.music_page and self.music_page.staff_view:
        # Set page to setup mode
        self.music_page.set_mode("setup")
        
        # Enter setup mode in staff view
        self.music_page.staff_view.enter_setup_mode()
        
        # Update menu text
        self.toggle_edit_mode_action.setText("&Toggle Edit Mode")
        self.score_setup_action.setText("&Score Setup")
        
        # Update status
        self.status_bar.showMessage("Setup mode - configure your score")

def _enter_edit_mode(self):
    """Enter edit mode (white page)."""
    if self.music_page and self.music_page.staff_view:
        # Set page to edit mode
        self.music_page.set_mode("edit")
        
        # Enter edit mode in staff view
        self.music_page.staff_view.enter_edit_mode()
        
        # Update menu text
        self.toggle_edit_mode_action.setText("&Toggle Setup Mode")
        self.score_setup_action.setText("&Edit Mode")
        
        # Update status
        self.status_bar.showMessage("Edit mode - ready for notation")
```

### Music Page Visual States

The `MusicPage` class provides visual feedback:

```python
def _update_appearance(self):
    """Update page appearance based on mode."""
    if self.mode == "setup":
        # Setup mode: pink background with grid (traditional ONOTE setup mode)
        self.page_color = QColor(255, 240, 245)  # Light pink
        self.border_color = QColor(255, 105, 180)  # Hot pink
        self.grid_color = QColor(255, 182, 193)  # Light pink grid
    else:
        # Edit mode: white background
        self.page_color = QColor(255, 255, 255)  # White
        self.border_color = QColor(200, 200, 200)  # Light gray
        self.grid_color = QColor(240, 240, 240)  # Very light gray grid
```

### Dialog Integration

The score setup dialog integration:

```python
def open_score_setup(self):
    """Open the score setup dialog."""
    from src.gui.music.score_setup_dialog import ScoreSetupDialog
    
    # Ensure we're in setup mode before opening dialog
    if self.music_page and self.music_page.mode != "setup":
        self._enter_setup_mode()
    
    # Create dialog with music page's staff view as parent
    dialog = ScoreSetupDialog(self.music_page.staff_view if self.music_page else self)
    
    # Connect dialog signals
    dialog.setup_widget.setup_completed.connect(self._on_score_setup_completed)
    
    # Show dialog
    if dialog.exec():
        # Dialog was accepted - setup is complete
        self._on_score_setup_completed()
    else:
        # Dialog was cancelled - stay in setup mode
        self.status_bar.showMessage("Score setup cancelled")
```

## User Workflow

### 1. **Initial Launch**
- Desktop window opens with pink page (setup mode)
- Status bar shows "Setup mode - configure your score"
- Menu shows "Score Setup" option

### 2. **Score Configuration**
- Click "Score Setup" or use menu Score → Score Setup
- Score setup dialog opens with current document structure
- Add, remove, or configure staves and sections
- Configure notation settings for each staff

### 3. **Apply Changes**
- Click "Apply" in the score setup dialog
- Dialog closes automatically
- Page transitions from pink to white (edit mode)
- Status bar updates to "Edit mode - ready for notation"

### 4. **Edit Mode**
- Page is now white with clean background
- Staff view is in edit mode
- Ready for notation input and editing
- Can toggle back to setup mode if needed

## Technical Architecture

### Signal Flow
```
DesktopWindow.page_mode_changed → UI Updates
ScoreSetupDialog.setup_completed → DesktopWindow._on_score_setup_completed
StaffView.enter_setup_mode → Document layout setup mode
StaffView.enter_edit_mode → Document layout edit mode
```

### Data Flow
```
Document → StaffView → ScoreSetupDialog → StaffView → Document
```

### Mode Synchronization
- **Page Mode**: Visual state (pink/white)
- **Staff View Mode**: Functional state (setup/edit)
- **Document Layout Mode**: Data state (setup/edit)

## Testing

Use the test script to verify integration:

```bash
python test_score_setup_integration.py
```

The test script verifies:
1. Desktop window starts in setup mode (pink page)
2. Score setup dialog opens correctly
3. Mode transition works when applying changes
4. Visual feedback is correct

## Benefits

### 🎯 **User Experience**
- **Intuitive Workflow**: Clear visual distinction between setup and edit modes
- **Seamless Transitions**: Automatic mode switching eliminates confusion
- **Traditional Feel**: Maintains ONOTE's classic pink setup mode

### 🔧 **Developer Experience**
- **Clean Architecture**: Clear separation of concerns
- **Signal-Based**: Event-driven design for loose coupling
- **Testable**: Comprehensive test coverage for all workflows

### 🚀 **Performance**
- **Efficient Rendering**: Mode-specific visual updates
- **Minimal Overhead**: Direct integration without unnecessary layers
- **Responsive UI**: Real-time status updates and feedback

## Future Enhancements

### Planned Features
- **Setup Templates**: Pre-configured score setups
- **Mode Persistence**: Remember user's preferred mode
- **Advanced Grid Options**: Customizable setup grid patterns
- **Setup Mode Shortcuts**: Keyboard shortcuts for quick mode switching

### Integration Opportunities
- **Form Widget**: Floating form widget in setup mode
- **Tool Palette**: Setup-specific tools and options
- **Preview Mode**: Real-time preview of score layout
- **Export Setup**: Save and share score configurations 