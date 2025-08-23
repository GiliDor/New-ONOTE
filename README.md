# ONOTE - Music Notation Software

## Quick Start

### Launch ONOTE
```bash
python3 run.py
```

This launches ONOTE with:
- ✅ Multi-window architecture
- ✅ Immediate rendering in Score Setup Dialog
- ✅ Debug output visible
- ✅ All latest features and fixes

### Features
- **Immediate Rendering**: Changes in Score Setup Dialog apply instantly
- **Multi-Window**: Independent document windows
- **Page-Based Layout**: Professional music notation layout
- **Dynamic Resizing**: Responsive to window changes
- **Undo/Redo**: Comprehensive history system
- **Multiple Staff Types**: Single staff, grand staff, sections
- **File Operations**: Save, load, export functionality

### Development
- **Single Entry Point**: `run.py` is the only launch script
- **Debug Output**: Visible when running from Python
- **Clean Architecture**: Multi-window, page-based design

### Testing Immediate Rendering
1. Run `python3 run.py`
2. Create a new score
3. Click "Score Setup" button
4. Add staves or change settings
5. **Changes appear immediately** (no need to click Apply)

## Requirements
- Python 3.8+
- PyQt6
- macOS (primary platform)

## Project Structure
```
New-ONOTE/
├── run.py                    # Single launch script
├── src/                      # Source code
│   ├── main_multi_window.py  # Multi-window entry point
│   ├── gui/                  # User interface
│   └── core/                 # Core functionality
└── ONOTE.app/               # Compiled bundle (optional)
``` 