# ONOTE Multi-Window Setup Guide

## 🎯 Quick Start

The multi-window ONOTE version is now ready to use! Here's how to run it from Cursor:

### Method 1: Cursor Run Menu (Recommended)
1. Open Cursor
2. Go to **Run and Debug** (Ctrl+Shift+D)
3. Select **"ONOTE Multi-Window (Simple)"** from the dropdown
4. Click the green play button ▶️

### Method 2: Terminal Commands
```bash
# Simple launcher (recommended)
python run_multi_window.py

# Full launcher with checks
python3 run.py

# Direct launch
python src/main_multi_window.py
```

## 🆕 What's New in Multi-Window Version

### ✅ Multi-Window Architecture
- **Independent Document Windows**: Each score opens in its own ONOTE window
- **Word Processor Style**: Similar to how Word, Pages, or Finale work
- **Proper Page Layout**: Each window has its own page setup and layout
- **Window Management**: Multiple scores can be open simultaneously

### ✅ Enhanced Features
- **New Action**: Creates completely new ONOTE windows (not just new documents)
- **Independent Documents**: Each window has its own `ScoreDocument` instance
- **Separate State**: Changes in one window don't affect others
- **Window Focus**: Proper focus management between windows
- **Clean Shutdown**: All windows close properly when application exits

### ✅ Technical Improvements
- **ApplicationManager**: Central management of all document windows
- **DocumentWindow**: Dedicated window class for individual scores
- **Signal Integration**: Proper communication between windows and manager
- **Memory Management**: Efficient handling of multiple document instances

## 🔧 Available Launch Options

### In Cursor Run Menu:
1. **ONOTE Multi-Window (Simple)** - Quick launch with basic setup
2. **ONOTE Multi-Window (Full)** - Full launcher with dependency checks
3. **ONOTE Multi-Window (Direct)** - Direct launch of main file
4. **ONOTE Legacy (Old Version)** - Original single-window version

### File Structure:
```
ONOTE/
├── run_multi_window.py          # Simple multi-window launcher
├── run.py                       # Full multi-window launcher
├── src/main_multi_window.py     # Multi-window main entry point
├── src/gui/application_manager.py  # Window management
├── src/gui/document_window.py   # Individual document windows
└── run.py                       # Legacy single-window version
```

## 🧪 Testing Multi-Window Functionality

### Test Scripts Available:
```bash
# Test basic multi-window functionality
python test_multi_window.py

# Test "New" action creates new windows
python test_multi_window_new.py
```

### Manual Testing:
1. Launch multi-window ONOTE
2. Click **File → New** (or use Ctrl+N)
3. Verify a new ONOTE window opens
4. Create different content in each window
5. Verify windows are independent

## 🚀 Development Workflow

### For Development:
- Use **"ONOTE Multi-Window (Simple)"** for quick testing
- Use **"ONOTE Multi-Window (Full)"** for comprehensive testing
- Use **"ONOTE Legacy"** to compare with old version

### Debugging:
- All configurations use integrated terminal
- Console output shows window creation/deletion
- Error messages are clearly displayed

## 📋 Configuration Files Updated

### `.vscode/launch.json`
- Added multi-window launch configurations
- Reordered to prioritize new version
- Kept legacy version for comparison

### New Files Created:
- `run_multi_window.py` - Simple launcher
- `src/main_multi_window.py` - Multi-window entry point
- `src/gui/application_manager.py` - Window management
- `src/gui/document_window.py` - Document window class

## 🎵 Ready for Development!

The multi-window ONOTE is now fully functional and ready for detailed development. You can:

1. **Create multiple scores** in separate windows
2. **Test independent functionality** between windows
3. **Develop new features** with proper window isolation
4. **Compare behavior** with the legacy version

### Next Steps:
- Test all existing functionality in multi-window mode
- Develop new features that benefit from window isolation
- Optimize performance for multiple open windows
- Add window-specific features and preferences

---

**🎯 The multi-window ONOTE is now your primary development environment!** 