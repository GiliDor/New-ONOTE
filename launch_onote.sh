#!/bin/bash
# Launch ONOTE.app from Cursor
# This script launches the ONOTE macOS app bundle so you can use Cursor's Run button.

echo "🚀 Launching ONOTE macOS App Bundle..."
echo "📱 App Path: /Users/gilidor/Projects/New-ONOTE/ONOTE.app"

# Check if the app bundle exists
if [ ! -d "/Users/gilidor/Projects/New-ONOTE/ONOTE.app" ]; then
    echo "❌ Error: ONOTE.app not found at /Users/gilidor/Projects/New-ONOTE/ONOTE.app"
    exit 1
fi

echo "✅ Found ONOTE.app bundle"
echo "🎵 Launching as native macOS app..."
echo "   (Menu bar will show 'ONOTE' instead of 'Python')"
echo "   (App will appear in Dock)"

# Launch the app bundle using the 'open' command
if open "/Users/gilidor/Projects/New-ONOTE/ONOTE.app"; then
    echo "✅ ONOTE.app launched successfully!"
    echo "🍎 ONOTE is now running as a native macOS app"
    echo "   - Menu bar shows 'ONOTE' as the first menu"
    echo "   - App appears in Dock"
    echo "   - Native macOS integration active"
    echo "   - Default zoom is 81%"
    echo "   - User Zoom Presets available in View menu"
    echo "   - Score Dialog updates immediately in pink mode"
    exit 0
else
    echo "❌ Error launching ONOTE.app"
    exit 1
fi
