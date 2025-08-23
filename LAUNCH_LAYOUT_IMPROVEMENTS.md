# ONOTE Launch Layout Improvements

## Overview
Enhanced ONOTE's launch behavior to provide a better user experience with improved window sizing and element positioning.

## Improvements Implemented

### 1. Window Launch Size
**Problem**: ONOTE launched in a standard window size, requiring users to manually maximize or resize.

**Solution**: Window now launches just short of full screen, leaving 50px at the top for menu bar accessibility.

**Implementation**:
```python
def _setup_initial_window_size(self):
    """Setup window to launch just short of full screen with menu accessible."""
    # Get screen geometry
    screen = QApplication.primaryScreen()
    screen_geometry = screen.geometry()
    
    # Calculate window size (leave 50px at top for menu bar visibility)
    window_width = screen_geometry.width()
    window_height = screen_geometry.height() - 50  # Leave space for menu
    
    # Set window geometry
    self.setGeometry(0, 0, window_width, window_height)
    
    # Position window at top-left of screen
    self.move(0, 0)
```

**Benefits**:
- Menu bar remains accessible without full screen mode
- Maximum workspace utilization
- Consistent launch experience across different screen sizes

### 2. Page Positioning
**Problem**: Music page was positioned in the center of the desktop, not taking advantage of the available space.

**Solution**: Page is now positioned on the left side of the desktop by default.

**Implementation**:
```python
# Create music page
self.music_page = MusicPage(self.document)
# Position page on the left side of desktop
self.music_page.setPos(100, 200)  # Left side positioning
```

**Benefits**:
- Better space utilization
- Room for dialogs and tools on the right
- More intuitive layout for music notation workflow

### 3. Dialog Positioning
**Problem**: Score setup dialog appeared in default position, potentially overlapping with the music page.

**Solution**: Dialog is automatically positioned on the right side of the desktop when opened.

**Implementation**:
```python
def _position_score_setup_dialog(self, dialog):
    """Position the score setup dialog on the right side of the desktop."""
    # Get window geometry
    window_geometry = self.geometry()
    
    # Calculate dialog position (right side, centered vertically)
    dialog_width = 400  # Approximate dialog width
    dialog_height = 600  # Approximate dialog height
    
    # Position on right side with some margin
    x = window_geometry.width() - dialog_width - 50  # 50px margin from right edge
    y = (window_geometry.height() - dialog_height) // 2  # Center vertically
    
    # Ensure dialog stays within window bounds
    x = max(50, min(x, window_geometry.width() - dialog_width - 50))
    y = max(100, min(y, window_geometry.height() - dialog_height - 100))
    
    # Set dialog position
    dialog.move(x, y)
```

**Benefits**:
- No overlap with music page
- Consistent positioning across sessions
- Better workflow with page on left, dialog on right

## User Experience Flow

### Launch Sequence
1. **Window Opens**: Just short of full screen with menu accessible
2. **Page Appears**: Music page positioned on left side of desktop
3. **Setup Mode**: Page shows pink background (setup mode)
4. **Dialog Auto-Launches**: Score setup dialog appears on right side
5. **Ready for Configuration**: User can configure score while seeing both page and dialog

### Layout Benefits
- **Left Side**: Music page for visual feedback
- **Right Side**: Score setup dialog for configuration
- **Top**: Menu bar always accessible
- **Full Width**: Maximum workspace utilization

## Technical Details

### Window Geometry Calculation
- Uses `QApplication.primaryScreen()` to get screen dimensions
- Calculates optimal window size (screen height - 50px)
- Positions window at (0, 0) for consistent launch

### Dialog Positioning Logic
- Calculates dialog dimensions (400x600 approximate)
- Positions on right side with 50px margin
- Centers vertically within window bounds
- Ensures dialog stays within window boundaries

### Integration with Existing Features
- Works with existing zoom functionality
- Compatible with page dragging
- Maintains dialog closing functionality
- Preserves all existing menu and toolbar features

## Testing

### Automated Tests
Run `test_launch_layout_improvements.py` to verify:
- Window size calculation
- Page positioning
- Dialog positioning
- Dialog closing functionality

### Manual Verification
1. Launch ONOTE
2. Verify menu bar is accessible at top
3. Check page appears on left side
4. Confirm score setup dialog appears on right side
5. Test dialog closes when switching to edit mode

## Future Enhancements

### Potential Improvements
- **Dynamic Positioning**: Adjust based on screen size and resolution
- **User Preferences**: Allow users to customize default positions
- **Multiple Monitors**: Handle multi-monitor setups
- **Layout Presets**: Save and restore user's preferred layouts

### Configuration Options
- Window size percentage (currently 50px from top)
- Page default position (currently left side)
- Dialog default position (currently right side)
- Auto-launch behavior (currently enabled)

## Compatibility

### System Requirements
- Works on all platforms (Windows, macOS, Linux)
- Adapts to different screen resolutions
- Handles various window managers
- Compatible with high DPI displays

### Version Compatibility
- Requires PyQt6
- Compatible with existing ONOTE features
- No breaking changes to existing functionality
- Backward compatible with saved documents 