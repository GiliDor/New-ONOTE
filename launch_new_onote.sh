#!/bin/bash

# Launch the NEW desktop page-based ONOTE
# This is the working version with desktop architecture and Form widget

echo "🎵 Launching NEW ONOTE Desktop Page-Based Architecture..."
echo "📁 Working directory: $(pwd)"

# Activate virtual environment
source venv/bin/activate

# Launch the NEW desktop architecture
python -m src.main_multi_window

echo "✅ ONOTE launched successfully!" 