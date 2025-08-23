# 🎵 ONOTE Launch Instructions

## Version 1.2 - Complete with Section Ordering Fix

Welcome to ONOTE Music Notation Application! This document provides comprehensive instructions for launching your corrected and complete ONOTE application.

## 🚀 Quick Start

### Option 1: Shell Script (macOS/Linux - Recommended)
```bash
./run_onote.sh
```

### Option 2: Python Launcher (Cross-platform)
```bash
python3 run.py
```

### Option 3: Direct Python (Advanced users)
```bash
python run.py
```

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 512MB RAM minimum
- **Display**: 1024x768 minimum resolution

### Python Dependencies
Make sure you have all required packages installed:
```bash
pip install -r requirements.txt
```

**Core Dependencies:**
- PyQt6 (GUI framework)
- setproctitle (process naming)
- Additional packages as listed in requirements.txt

## 🔧 Setup Instructions

### 1. Navigate to ONOTE Directory
```bash
cd /path/to/your/ONOTE
```

### 2. Activate Virtual Environment (if using one)
```bash
# If you have a virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 3. Verify Installation
The launchers will automatically check for:
- ✅ Required Python version
- ✅ All dependencies installed  
- ✅ Core application files present
- ✅ Proper directory structure

## 🎼 Features in This Version

This corrected version includes:

### ✅ **Section Ordering Fix**
- **Issue**: Sections appeared at bottom of score after loading files
- **Status**: **FIXED** ✅
- **Impact**: All saved files now load with correct section positioning

### ✅ **Complete Undo/Redo System**
- Comprehensive document-level undo/redo
- Granular state management for all operations
- Support for barline operations, layout changes, and more
- Standard shortcuts: Ctrl+Z (undo), Ctrl+Y (redo)

### ✅ **Advanced Barline Support**
- Single, double, dashed, repeat (start/end/both) barlines
- Individual barline selection and modification
- Full integration with undo/redo system
- Proper visual feedback and selection states

### ✅ **Full Score Options Dialog**
- Comprehensive layout and formatting options
- Measure number display controls
- Font and spacing settings
- Page layout configuration

### ✅ **Multiple Staff Types**
- Single staves with various clefs (treble, bass, alto, percussion)
- Grand staff support with automatic brace rendering
- Section grouping and organization
- Proper staff spacing and alignment

### ✅ **Robust File Handling**
- Save/load functionality with data integrity
- Backward compatibility with older file formats
- Automatic data migration and validation

## 🐛 Troubleshooting

### Common Issues and Solutions

#### "PyQt6 not found" Error
```bash
pip install PyQt6
# or install all requirements
pip install -r requirements.txt
```

#### "run.py not found" Error
Make sure you're in the correct directory:
```bash
ls -la  # Should show run.py in the listing
```

#### Permission Denied (macOS/Linux)
Make the shell script executable:
```bash
chmod +x run_onote.sh
```

#### Virtual Environment Issues
Recreate your virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## 📁 File Structure Verification

Your ONOTE directory should contain:
```
ONOTE/
├── run.py                    # Main application entry point
├── run_onote.sh             # Shell launcher (macOS/Linux)
├── run.py                   # Python launcher (cross-platform)
├── requirements.txt         # Python dependencies
├── src/                     # Source code
│   └── gui/
│       └── music/
│           ├── main_window.py
│           ├── score_document.py
│           ├── staff_types.py
│           └── staff_view.py
└── venv/                    # Virtual environment (optional)
```

## 🔍 Verification Steps

After launching, verify the fix is working:

1. **Create a new score** with multiple staves and sections
2. **Save the file** to disk
3. **Close and reopen** the application
4. **Load the saved file**
5. **Verify** that sections appear in their correct positions (not at the bottom)

## 📞 Support

If you encounter any issues:

1. **Check the console output** for detailed error messages
2. **Verify all prerequisites** are met
3. **Ensure file permissions** are correct
4. **Try the alternative launch methods** if one doesn't work

## 🎉 Success Indicators

When ONOTE launches successfully, you should see:
- ✅ Clean startup without errors
- ✅ Proper GUI rendering
- ✅ All menu items and toolbars functional  
- ✅ Score rendering working correctly
- ✅ File operations working properly

## 📝 Version Notes

**Version 1.2 Highlights:**
- **Critical Fix**: Section ordering issue resolved
- **Enhanced**: Undo/redo system improvements
- **Improved**: File compatibility and data integrity
- **Updated**: Error handling and user feedback

---

🎵 **Enjoy using ONOTE Music Notation Application!** 🎵 