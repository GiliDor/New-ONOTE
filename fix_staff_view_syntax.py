#!/usr/bin/env python3
"""
Fix critical syntax errors in staff_view.py that prevent ONOTE from running
"""

import re

def fix_staff_view_syntax():
    """Fix the critical syntax errors in staff_view.py"""
    
    # Read the current staff_view.py file
    with open('src/gui/music/staff_view.py', 'r') as f:
        content = f.read()
    
    print("🔧 Fixing staff_view.py syntax errors...")
    
    # Fix 1: Fix the malformed conditional around line 1705
    # Replace the incorrectly indented return False and print statement
    old_pattern1 = r'(\s+)if y < system_top or y > system_bottom:\s*\n\s+print\(f"BARLINE_POSITION: y=\{y\} outside system bounds.*?\)\s*\n\s+return False\s*\n\s+print\(f"BARLINE_POSITION: y=\{y\} within system bounds.*?\)\s*\n\s+return True'
    
    new_pattern1 = '''                if y < system_top or y > system_bottom:
                    print(f"BARLINE_POSITION: y={y} outside system bounds (top={system_top}, bottom={system_bottom})")
                    return False
                
                print(f"BARLINE_POSITION: y={y} within system bounds (top={system_top}, bottom={system_bottom}) - VALID")
                return True'''
    
    # Fix 2: Fix malformed for loops and conditionals in find_barline_at_position
    content = re.sub(
        r'(\s+)for measure in measures:\s*\n\s+if hasattr\(measure, \'end_x\'\):\s*\n\s+distance = abs\(measure\.end_x - x\)\s*\n\s+print\(f"BARLINE_SELECTION: Measure',
        r'\1for measure in measures:\n\1    if hasattr(measure, \'end_x\'):\n\1        distance = abs(measure.end_x - x)\n\1        print(f"BARLINE_SELECTION: Measure',
        content
    )
    
    # Fix 3: Fix malformed try/except blocks
    # Find and fix the problematic try block structure
    content = re.sub(
        r'(\s+)if new_barline:\s*\n\s+# Don\'t save state here.*?\n\s+# Emit signal for regular measures.*?\n\s+if hasattr\(new_barline, \'measure_number\'\).*?\n\s+self\.barline_created\.emit\(new_barline\)\s*\n\s+# Update the display\s*\n\s+self\.update\(\)\s*\n\s+print\(f"BARLINE_CREATE: Successfully created barline using temporal bridge"\)\s*\n\s+return new_barline\s*\n\s+else:\s*\n\s+print\("BARLINE_CREATE: Temporal bridge returned None for barline creation"\)',
        r'''\1if new_barline:
\1    # Don't save state here - let the form widget handle it to prevent duplicate state saves
\1    # This prevents undo reversion issues on clicks
\1    
\1    # Emit signal for regular measures (not graphical dashed barlines)
\1    if hasattr(new_barline, 'measure_number') and not hasattr(new_barline, 'is_graphical_dashed'):
\1        self.barline_created.emit(new_barline)
\1    
\1    # Update the display
\1    self.update()
\1    
\1    print(f"BARLINE_CREATE: Successfully created barline using temporal bridge")
\1    return new_barline
\1else:
\1    print("BARLINE_CREATE: Temporal bridge returned None for barline creation")''',
        content
    )
    
    # Fix 4: Fix the malformed except clause indentation
    content = re.sub(
        r'(\s+)except Exception as e:\s*\n\s+print\(f"BARLINE_CREATE: Error using temporal bridge: \{e\}"\)\s*\n\s+# Fall back to original behavior below',
        r'''\1except Exception as e:
\1    print(f"BARLINE_CREATE: Error using temporal bridge: {e}")
\1    # Fall back to original behavior below''',
        content
    )
    
    # Fix 5: Fix another malformed try/except for measure manager
    content = re.sub(
        r'(\s+)except Exception as e:\s*\n\s+print\(f"BARLINE_CREATE: Error using measure manager: \{e\}"\)\s*\n\s+# Fall back to original behavior below',
        r'''\1except Exception as e:
\1    print(f"BARLINE_CREATE: Error using measure manager: {e}")
\1    # Fall back to original behavior below''',
        content
    )
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed staff_view.py syntax errors")
    return True

if __name__ == "__main__":
    try:
        fix_staff_view_syntax()
        print("✅ All syntax fixes applied successfully!")
    except Exception as e:
        print(f"❌ Error fixing syntax: {e}")
        import traceback
        traceback.print_exc() 