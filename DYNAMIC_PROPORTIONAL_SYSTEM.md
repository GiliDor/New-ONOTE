# Dynamic Proportional Barline Positioning System

## Problem Solved

The original ONOTE barline system used a **fixed staff length** determined by the window size when computing barline positions. This caused several issues:

1. **Static Positioning**: Barlines remained fixed in place when the window was resized
2. **Inconsistent Layout**: Page dimensions didn't scale proportionally with window changes
3. **Poor User Experience**: Users expected barlines to adjust dynamically with window resizing
4. **Non-Standard Behavior**: Professional music notation software typically uses dynamic proportional systems

## Solution: Dynamic Proportional System

### Core Principles

The new system implements **dynamic proportional barline positioning** that follows common music notation practices:

1. **Proportional Scaling**: Barline positions scale proportionally with page dimensions
2. **Dynamic Page Width Detection**: System automatically detects current page width from multiple sources
3. **Real-time Responsiveness**: Barlines adjust immediately when window is resized
4. **Consistent Coordinate System**: All components use the same dynamic calculation methods

### Implementation Details

#### 1. Dynamic Page Width Detection

The system now uses a hierarchical approach to determine the current page width:

```python
def _get_dynamic_page_width(self):
    """Get the current page width dynamically from the actual layout"""
    page_width = 800.0  # Default fallback
    
    if self.document:
        # 1. Try document's renderer (most accurate)
        if hasattr(self.document, 'renderer') and self.document.renderer:
            page_width = getattr(self.document.renderer, 'page_width', page_width)
        
        # 2. Try staff view's renderer
        elif (hasattr(self.document, 'staff_view') and self.document.staff_view and 
              hasattr(self.document.staff_view, 'renderer')):
            page_width = getattr(self.document.staff_view.renderer, 'page_width', page_width)
        
        # 3. Try document's layout
        elif hasattr(self.document, 'layout') and self.document.layout:
            page_width = getattr(self.document.layout, 'page_width', page_width)
        
        # 4. Calculate from widget width (most dynamic)
        elif (hasattr(self.document, 'staff_view') and self.document.staff_view and 
              hasattr(self.document.staff_view, 'width')):
            widget_width = self.document.staff_view.width()
            zoom_factor = getattr(self.document.staff_view, 'zoom_factor', 1.0)
            page_width = widget_width / zoom_factor
    
    return float(page_width)
```

#### 2. Dynamic Right Margin Detection

Similar approach for right margin calculation:

```python
def _get_dynamic_right_margin(self):
    """Get the current right margin dynamically from the actual layout"""
    right_margin = 50.0  # Default fallback
    
    if self.document:
        # Try renderer margins first
        if hasattr(self.document, 'renderer') and self.document.renderer:
            margins = getattr(self.document.renderer, 'margins', {'right': right_margin})
            right_margin = margins.get('right', right_margin)
        
        # Try document layout
        elif hasattr(self.document, 'layout') and self.document.layout:
            right_margin = getattr(self.document.layout, 'right_margin', right_margin)
    
    return float(right_margin)
```

#### 3. Dynamic End Barline Position Calculation

The end barline position is now calculated dynamically:

```python
def get_current_end_barline_x(self):
    """Get the current END_BARLINE_X position using dynamic proportional calculation"""
    page_width = self._get_dynamic_page_width()
    right_margin = self._get_dynamic_right_margin()
    calculated_end_x = page_width - right_margin
    
    # Update if different (allows for dynamic changes)
    if abs(calculated_end_x - self.END_BARLINE_X) > 0.1:
        self.END_BARLINE_X = calculated_end_x
    
    return self.END_BARLINE_X
```

#### 4. Automatic Layout Refresh

The renderer's `set_page_size` method now automatically triggers layout refresh:

```python
def set_page_size(self, width, height):
    """Set the page size for rendering with dynamic layout refresh."""
    old_width = self.page_width
    self.page_width = width
    self.page_height = height
    
    # If page width changed significantly, trigger layout refresh
    if abs(old_width - width) > 1.0:
        # Trigger layout refresh if we have a document with temporal bridge
        if (hasattr(self, 'document') and self.document and 
            hasattr(self.document, 'staff_view') and self.document.staff_view and
            hasattr(self.document.staff_view, 'temporal_bridge')):
            
            self.document.staff_view.temporal_bridge._force_layout_refresh()
```

### Component Integration

#### 1. Temporal Bridge Integration

The `BarlineTemporalBridge` now uses the dynamic system for all calculations:

- `_force_layout_refresh()`: Uses dynamic page width and margin detection
- `get_current_end_barline_x()`: Always calculates dynamically
- All measure positioning uses proportional calculations

#### 2. Staff View Integration

The `StaffView` delegates to the temporal bridge for consistency:

```python
def get_actual_end_barline_x(self) -> float:
    """Get the actual end barline position using dynamic proportional calculation"""
    # Use the same dynamic system as the temporal bridge for consistency
    if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
        return self.temporal_bridge.get_current_end_barline_x()
    
    # Fallback: calculate dynamically from renderer
    if hasattr(self, 'renderer') and self.renderer:
        page_width = getattr(self.renderer, 'page_width', 800)
        margins = getattr(self.renderer, 'margins', {'right': 50})
        right_margin = margins.get('right', 50)
        return float(page_width - right_margin)
```

#### 3. Form Widget Integration

The `FormWidget` also uses the dynamic system:

```python
def _get_staff_end_position(self):
    """Get the staff end position dynamically using the proportional system"""
    # Use the same dynamic system as the temporal bridge for consistency
    if hasattr(self, 'temporal_bridge') and self.temporal_bridge:
        return self.temporal_bridge.get_current_end_barline_x()
```

### Resize Event Handling

#### 1. Main Window Resize

The main window's resize event updates the renderer and triggers layout refresh:

```python
def resizeEvent(self, event):
    # Update renderer page width to match new window size
    if hasattr(self.staff_view, 'renderer') and self.staff_view.renderer:
        new_width = self.width()
        self.staff_view.renderer.page_width = new_width
        
        # The renderer's set_page_size method will automatically trigger layout refresh
        if hasattr(self.staff_view.temporal_bridge, '_force_layout_refresh'):
            self.staff_view.temporal_bridge._force_layout_refresh()
```

#### 2. Staff View Resize

The staff view's resize event uses the enhanced renderer method:

```python
def resizeEvent(self, event):
    # Update renderer page size to match new widget size
    if hasattr(self, 'renderer') and self.renderer:
        new_width = int(self.width() / self.zoom_factor)
        new_height = int(self.height() / self.zoom_factor)
        
        # Use the renderer's enhanced set_page_size method which will trigger layout refresh
        self.renderer.set_page_size(new_width, new_height)
```

### Benefits

1. **Professional Behavior**: Matches industry-standard music notation software
2. **Responsive Design**: Barlines adjust immediately to window resizing
3. **Consistent Layout**: All components use the same proportional calculations
4. **User-Friendly**: Intuitive behavior that users expect
5. **Scalable**: Works with any page size or window dimensions
6. **Maintainable**: Centralized dynamic calculation logic

### Testing

Use the provided test script `test_dynamic_proportional_system.py` to verify:

1. Create test barlines
2. Resize window to different sizes
3. Verify barlines adjust proportionally
4. Test layout refresh functionality

### Common Practices Followed

This implementation follows common practices in professional music notation software:

1. **Proportional Scaling**: Barlines scale with page dimensions
2. **Dynamic Detection**: Automatic detection of current layout parameters
3. **Real-time Updates**: Immediate response to layout changes
4. **Consistent Behavior**: All components use the same calculation methods
5. **Fallback Systems**: Multiple sources for layout information
6. **Error Handling**: Graceful degradation when components are unavailable

The system now provides a professional, responsive barline positioning experience that scales dynamically with window resizing and page dimension changes. 