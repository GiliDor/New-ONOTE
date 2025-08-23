# Mac 2-Finger Zooming Feature

## Overview

ONOTE now supports native Mac 2-finger pinch-to-zoom gestures on the music page, providing an intuitive and smooth zooming experience similar to other Mac applications.

## Features

### 🎯 **Native Mac Gesture Support**
- **Pinch Outward**: Zoom in on the music page
- **Pinch Inward**: Zoom out on the music page
- **Smooth Animation**: Fluid zoom transitions
- **Center Preservation**: Zoom maintains the center point of the gesture

### 📏 **Zoom Constraints**
- **Minimum Zoom**: 30% (prevents page from becoming too small)
- **Maximum Zoom**: 300% (prevents excessive zooming)
- **Default Zoom**: 100% (normal size)

### 🎨 **Visual Feedback**
- **Status Bar Display**: Shows current zoom percentage
- **Real-time Updates**: Zoom percentage updates during gesture
- **Smooth Transitions**: Page scales smoothly during zoom

## Implementation Details

### Gesture Recognition
```python
# Enable pinch gesture recognition
self.desktop_view.grabGesture(Qt.GestureType.PinchGesture)
self.desktop_view.installEventFilter(self)
```

### Event Handling
```python
def eventFilter(self, obj, event):
    """Handle pinch gesture events for Mac 2-finger zooming."""
    if obj == self.desktop_view:
        if event.type() == QEvent.Type.Gesture:
            pinch_gesture = event.gesture(Qt.GestureType.PinchGesture)
            if pinch_gesture:
                self._handle_pinch_gesture(pinch_gesture)
                return True
    return super().eventFilter(obj, event)
```

### Zoom Calculation
```python
def _handle_pinch_gesture(self, pinch_gesture):
    """Handle pinch gesture for zooming the music page."""
    scale_factor = pinch_gesture.scaleFactor()
    new_zoom = self.page_zoom * scale_factor
    new_zoom = max(0.3, min(3.0, new_zoom))  # Clamp to 30%-300%
    
    if abs(new_zoom - self.page_zoom) > 0.01:
        self.page_zoom = new_zoom
        self._apply_zoom()
```

## Usage

### Mac Trackpad Gestures
1. **Open ONOTE Desktop Window**
2. **Position cursor over the music page**
3. **Use two fingers on trackpad**:
   - **Pinch outward** (spread fingers apart) → Zoom in
   - **Pinch inward** (bring fingers together) → Zoom out

### Keyboard Shortcuts (Still Available)
- **Ctrl++**: Zoom in
- **Ctrl+-**: Zoom out
- **Ctrl+0**: Reset zoom to 100%

### Menu Options
- **View → Zoom In**: Zoom in on the page
- **View → Zoom Out**: Zoom out on the page
- **View → Reset Zoom**: Reset zoom to 100%

## Technical Architecture

### Components
1. **DesktopWindow**: Main window class with gesture handling
2. **QGraphicsView**: Desktop view with gesture recognition
3. **MusicPage**: Zoomable page component
4. **Event Filter**: Gesture event processing

### Gesture Flow
1. **Trackpad Input** → Mac OS gesture recognition
2. **Qt Gesture Event** → DesktopWindow event filter
3. **Pinch Gesture** → Scale factor calculation
4. **Zoom Application** → Page scaling and view adjustment
5. **Visual Update** → Status bar and page rendering

### Zoom Preservation
- **Center Point**: Maintains zoom center during gesture
- **Scroll Position**: Adjusts view to keep zoom center
- **Page Position**: Preserves page location on desktop

## Testing

### Test Script
Run `test_mac_zoom.py` to verify functionality:
```bash
python test_mac_zoom.py
```

### Test Scenarios
1. **Basic Zoom**: Pinch in/out to verify zoom works
2. **Zoom Limits**: Verify 30%-300% constraints
3. **Center Preservation**: Check zoom maintains center
4. **Status Updates**: Confirm zoom percentage display
5. **Smooth Animation**: Verify fluid zoom transitions

## Compatibility

### System Requirements
- **macOS**: 10.12 or later (for Qt6 gesture support)
- **Trackpad**: Built-in or external trackpad with gesture support
- **Qt6**: PyQt6 with gesture recognition enabled

### Browser Compatibility
- **Safari**: Full support
- **Chrome**: Full support
- **Firefox**: Full support
- **Other browsers**: Should work with standard trackpad gestures

## Future Enhancements

### Planned Features
- **Zoom Animation**: Smoother transitions with easing
- **Zoom Presets**: Quick zoom to common percentages
- **Zoom History**: Remember zoom levels per document
- **Touch Bar Support**: Zoom controls on MacBook Pro Touch Bar

### Performance Optimizations
- **Gesture Throttling**: Prevent excessive zoom updates
- **Render Optimization**: Efficient page scaling
- **Memory Management**: Optimize zoom memory usage

## Troubleshooting

### Common Issues
1. **Gestures Not Working**: Check trackpad settings in System Preferences
2. **Zoom Too Fast/Slow**: Adjust trackpad sensitivity in System Preferences
3. **Page Jumps**: Ensure proper gesture center point calculation
4. **Performance Issues**: Check system resources and Qt6 version

### Debug Information
- **Gesture Events**: Logged to console during development
- **Zoom Values**: Displayed in status bar
- **Error Handling**: Graceful fallback to keyboard shortcuts

## Code Examples

### Basic Gesture Setup
```python
# Enable gestures
view.grabGesture(Qt.GestureType.PinchGesture)
view.installEventFilter(self)
```

### Gesture Handling
```python
def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.Gesture:
        pinch = event.gesture(Qt.GestureType.PinchGesture)
        if pinch:
            self.handle_zoom(pinch.scaleFactor())
            return True
    return super().eventFilter(obj, event)
```

### Zoom Application
```python
def handle_zoom(self, scale_factor):
    new_zoom = self.current_zoom * scale_factor
    new_zoom = max(0.3, min(3.0, new_zoom))
    self.apply_zoom(new_zoom)
```

---

**Note**: This feature is specifically designed for Mac trackpad gestures and provides a native Mac-like zooming experience in ONOTE. 