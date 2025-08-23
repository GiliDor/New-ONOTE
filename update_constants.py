"""
Temporary script to update the notation constants.
This will update the clef font size and save it to the configuration file.
"""

from src.gui.music.notation_constants import FONT_SIZES, save_all_constants_to_disk

print("Current clef font size:", FONT_SIZES['clef'])

# Update clef font size
FONT_SIZES['clef'] = 36  # More reasonable size - bigger than default but not too big

print("Updated clef font size to:", FONT_SIZES['clef'])

# Save to disk
success = save_all_constants_to_disk()
print("Settings saved:", success)

print("Now run the main application with 'python3 run.py'") 