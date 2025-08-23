#!/usr/bin/env python3
"""
Final comprehensive fix for all indentation issues in staff_view.py
"""

import re

def final_indentation_fix():
    """Fix all remaining indentation issues comprehensively"""
    
    with open('src/gui/music/staff_view.py', 'r') as f:
        content = f.read()
    
    print("🔧 Applying final comprehensive indentation fixes...")
    
    # Fix all malformed else clauses with excessive indentation
    content = re.sub(r'(\s{20,})else:', r'        else:', content)
    content = re.sub(r'(\s{16,})if (.*?):', r'        if \2:', content)
    content = re.sub(r'(\s{16,})print\(', r'            print(', content)
    content = re.sub(r'(\s{16,})return ', r'            return ', content)
    content = re.sub(r'(\s{16,})measures_dict\[', r'            measures_dict[', content)
    content = re.sub(r'(\s{16,})new_measure\.', r'            new_measure.', content)
    content = re.sub(r'(\s{16,})self\.', r'            self.', content)
    
    # Fix specific problematic patterns
    # Fix measures_dict assignment lines
    content = re.sub(r'(\s{20,})measures_dict\[measure_num\] = measure', r'            measures_dict[measure_num] = measure', content)
    
    # Fix other common excessive indentations
    content = re.sub(r'(\s{20,})(.*?measures.*?=.*?)', r'            \2', content)
    content = re.sub(r'(\s{20,})(.*?\.measures.*?)', r'            \2', content)
    
    # Fix if statements with excessive indentation
    content = re.sub(r'(\s{20,})if isinstance\(', r'            if isinstance(', content)
    content = re.sub(r'(\s{20,})if hasattr\(', r'            if hasattr(', content)
    content = re.sub(r'(\s{20,})if main_window', r'            if main_window', content)
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.write(content)
    
    print("✅ Applied final comprehensive indentation fixes")

def fix_specific_line_issues():
    """Fix specific line-by-line issues"""
    
    with open('src/gui/music/staff_view.py', 'r') as f:
        lines = f.readlines()
    
    print("🔧 Fixing specific line issues...")
    
    fixed_lines = []
    for i, line in enumerate(lines):
        # Fix lines that start with excessive whitespace
        if len(line) > 24 and line.startswith(' ' * 24):
            # If it's a continuation of code, reduce to 12 spaces
            if any(keyword in line for keyword in ['measures_dict', 'new_measure', 'self.', 'print(', 'return', 'if ', 'else:']):
                fixed_line = '            ' + line.lstrip()
                fixed_lines.append(fixed_line)
                print(f"Fixed line {i+1}: excessive indentation reduced")
            else:
                fixed_lines.append(line)
        elif len(line) > 20 and line.startswith(' ' * 20):
            # Similar fix for 20-space indentation
            if any(keyword in line for keyword in ['measures_dict', 'new_measure', 'self.', 'print(', 'return', 'if ', 'else:']):
                fixed_line = '            ' + line.lstrip()
                fixed_lines.append(fixed_line)
                print(f"Fixed line {i+1}: excessive indentation reduced")
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed lines back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fixed specific line issues")

if __name__ == "__main__":
    try:
        final_indentation_fix()
        fix_specific_line_issues()
        print("✅ All comprehensive indentation fixes applied successfully!")
    except Exception as e:
        print(f"❌ Error fixing indentation: {e}")
        import traceback
        traceback.print_exc() 