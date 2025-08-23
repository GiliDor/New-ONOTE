#!/usr/bin/env python3
"""
Fix specific indentation issues in staff_view.py
"""

def fix_indentation_issues():
    """Fix the specific indentation problems"""
    
    with open('src/gui/music/staff_view.py', 'r') as f:
        lines = f.readlines()
    
    print("🔧 Fixing specific indentation issues...")
    
    # Fix line 2016 - excessive indentation
    if len(lines) > 2015:  # Index 2015 = line 2016
        lines[2015] = "        from .measure_object import MeasureObject\n"
        print("✅ Fixed line 2016 indentation")
    
    # Fix malformed else clauses throughout the file
    for i, line in enumerate(lines):
        # Fix excessively indented else clauses  
        if line.strip().startswith('else:') and line.startswith('                        else:'):
            lines[i] = "            else:\n"
            print(f"✅ Fixed malformed else clause on line {i+1}")
        
        # Fix other malformed indentations
        if 'from .measure_object import MeasureObject' in line and line.startswith('                        '):
            lines[i] = "        from .measure_object import MeasureObject\n"
            print(f"✅ Fixed excessive indentation on line {i+1}")
    
    # Write the fixed content back
    with open('src/gui/music/staff_view.py', 'w') as f:
        f.writelines(lines)
    
    print("✅ Fixed staff_view.py indentation issues")

if __name__ == "__main__":
    try:
        fix_indentation_issues()
        print("✅ All indentation fixes applied successfully!")
    except Exception as e:
        print(f"❌ Error fixing indentation: {e}")
        import traceback
        traceback.print_exc() 