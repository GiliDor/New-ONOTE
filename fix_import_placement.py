#!/usr/bin/env python3
"""
Fix misplaced imports and remaining indentation issues in staff_view.py
"""

def fix_import_placement():
    """Fix the misplaced import statements and indentation"""
    
    with open('src/gui/music/staff_view.py', 'r') as f:
        content = f.read()
    
    print("🔧 Fixing misplaced imports and indentation...")
    
    # Add the import at the top of the file (after other imports)
    if 'from .measure_object import MeasureObject' not in content[:2000]:  # Check if not already at top
        # Find the end of existing imports
        lines = content.split('\n')
        import_end_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end_index = i
        
        # Insert the import after existing imports
        lines.insert(import_end_index + 1, 'from .measure_object import MeasureObject')
        content = '\n'.join(lines)
    
    # Remove all the misplaced imports from inside functions
    import re
    
    # Pattern to match the misplaced imports with various indentations
    patterns_to_remove = [
        r'\s*from \.measure_object import MeasureObject\s*\n',
        r'\s*if isinstance\(existing_barline, MeasureObject\):\s*\n\s*from \.measure_object import MeasureObject\s*\n',
        r'\s*# Only emit signal for actual MeasureObjects.*?\n\s*from \.measure_object import MeasureObject\s*\n',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '', content, flags=re.MULTILINE | re.DOTALL)
    
    # Remove standalone misplaced imports
    content = re.sub(r'(\s{8,})from \.measure_object import MeasureObject\s*\n', '', content)
    
    # Fix specific malformed conditionals
    # Fix the if isinstance lines that lost their import
    content = re.sub(
        r'(\s+)if isinstance\((.*?), MeasureObject\):',
        r'\1if isinstance(\2, MeasureObject):',
        content
    )
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.write(content)
    
    print("✅ Fixed import placement and remaining issues")

if __name__ == "__main__":
    try:
        fix_import_placement()
        print("✅ All import and indentation fixes applied successfully!")
    except Exception as e:
        print(f"❌ Error fixing imports: {e}")
        import traceback
        traceback.print_exc() 