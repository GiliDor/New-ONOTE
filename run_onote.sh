#!/bin/bash

# ONOTE Music Notation Application Launcher
# Version: 1.2 (Section Ordering Fix Applied)
# Last Updated: Post Section Ordering Bug Fix

echo "🎵 Starting ONOTE Music Notation Application..."
echo "📝 Version: 1.2 with Section Ordering Fix"
echo "🔧 Build: Complete with all fixes applied"
echo ""

# Check if we're in the correct directory
if [ ! -f "run.py" ]; then
    echo "❌ Error: run.py not found. Please run this script from the ONOTE project directory."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  Warning: Virtual environment not found. Using system Python."
fi

# Check Python installation
if ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed or not in PATH."
    exit 1
fi

# Check required dependencies
echo "📦 Checking dependencies..."
python -c "import PyQt6" 2>/dev/null || {
    echo "❌ Error: PyQt6 not found. Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
}

# Verify key application files exist
echo "🔍 Verifying application files..."
required_files=(
    "src/gui/music/main_window.py"
    "src/gui/music/score_document.py" 
    "src/gui/music/staff_types.py"
    "src/gui/music/staff_view.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: Required file $file not found."
        exit 1
    fi
done

echo "✅ All required files found."
echo ""

# Set environment variables for optimal performance
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export QT_AUTO_SCREEN_SCALE_FACTOR=1

# Create user config directory if it doesn't exist
mkdir -p ~/.onote

echo "🚀 Launching ONOTE Application..."
echo "📍 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo ""
echo "🎼 Features available in this version:"
echo "   ✅ Section ordering fix applied"
echo "   ✅ Comprehensive undo/redo system"
echo "   ✅ Granular barline support"  
echo "   ✅ Full score options dialog"
echo "   ✅ Multiple staff types and clefs"
echo "   ✅ Grand staff support"
echo "   ✅ File save/load functionality"
echo ""

# Run the application with error handling
if python run.py; then
    echo ""
    echo "👋 ONOTE application closed successfully."
else
    echo ""
    echo "❌ ONOTE application encountered an error."
    echo "💡 Check the console output above for details."
    exit 1
fi

# Deactivate virtual environment if it was activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

echo "🎵 Thank you for using ONOTE!" 