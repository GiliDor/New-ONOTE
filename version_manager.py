#!/usr/bin/env python3
"""
ONOTE Version Manager
Utility script for managing and retrieving version information.
"""

import sys
import os
from pathlib import Path

# Add src to path to import ONOTE modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

def get_current_version():
    """Retrieve the current version of ONOTE."""
    try:
        from src import __version__, get_version_info, get_version_string
        return {
            'version': __version__,
            'version_string': get_version_string(),
            'info': get_version_info()
        }
    except ImportError as e:
        print(f"Error importing ONOTE version: {e}")
        return None

def get_version_history():
    """Retrieve the complete version history."""
    try:
        from src import get_version_history
        return get_version_history()
    except ImportError as e:
        print(f"Error importing version history: {e}")
        return None

def print_version_info():
    """Print detailed version information."""
    version_data = get_current_version()
    if not version_data:
        print("❌ Could not retrieve version information")
        return
    
    print("🎵 ONOTE Version Information")
    print("=" * 50)
    print(f"📋 Version: {version_data['version']}")
    print(f"📝 Full String: {version_data['version_string']}")
    
    info = version_data['info']
    print(f"🏷️  Codename: {info['codename']}")
    print(f"📅 Build Date: {info['build']}")
    print(f"🔧 Release Type: {info['release']}")
    print(f"📖 Description: {info['description']}")
    print()

def print_version_history():
    """Print the complete version history."""
    history = get_version_history()
    if not history:
        print("❌ Could not retrieve version history")
        return
    
    print("📚 ONOTE Version History")
    print("=" * 50)
    
    # Sort versions by version number (reverse chronological)
    sorted_versions = sorted(history.items(), key=lambda x: [int(n) for n in x[0].split('.')], reverse=True)
    
    for version, details in sorted_versions:
        print(f"\n🎯 Version {version} - {details['codename']}")
        print(f"   📅 Date: {details['date']}")
        print("   📝 Changes:")
        for change in details['changes']:
            print(f"      • {change}")
    
    print()

def check_version_compatibility():
    """Check if the current version is compatible with the system."""
    version_data = get_current_version()
    if not version_data:
        return False
    
    info = version_data['info']
    
    print("🔍 Version Compatibility Check")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print(f"❌ Python version {python_version.major}.{python_version.minor} is not supported")
        print("   Required: Python 3.8+")
        return False
    else:
        print(f"✅ Python version {python_version.major}.{python_version.minor} is supported")
    
    # Check if it's a stable release
    if info['release'] == 'stable':
        print("✅ This is a stable release")
    else:
        print("⚠️  This is a development release")
    
    # Check build date
    print(f"📅 Build date: {info['build']}")
    
    return True

def export_version_info(output_file=None):
    """Export version information to a file."""
    version_data = get_current_version()
    history = get_version_history()
    
    if not version_data or not history:
        print("❌ Could not retrieve version information")
        return False
    
    if not output_file:
        output_file = f"onote_version_{version_data['version']}.txt"
    
    try:
        with open(output_file, 'w') as f:
            f.write("ONOTE Version Information Export\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Current Version: {version_data['version']}\n")
            f.write(f"Version String: {version_data['version_string']}\n")
            
            info = version_data['info']
            f.write(f"Codename: {info['codename']}\n")
            f.write(f"Build Date: {info['build']}\n")
            f.write(f"Release Type: {info['release']}\n")
            f.write(f"Description: {info['description']}\n\n")
            
            f.write("Version History:\n")
            f.write("-" * 20 + "\n")
            
            sorted_versions = sorted(history.items(), key=lambda x: [int(n) for n in x[0].split('.')], reverse=True)
            
            for version, details in sorted_versions:
                f.write(f"\nVersion {version} - {details['codename']}\n")
                f.write(f"Date: {details['date']}\n")
                f.write("Changes:\n")
                for change in details['changes']:
                    f.write(f"  • {change}\n")
        
        print(f"✅ Version information exported to: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error exporting version information: {e}")
        return False

def main():
    """Main function for command-line usage."""
    if len(sys.argv) < 2:
        print("Usage: python version_manager.py [command]")
        print("\nCommands:")
        print("  current    - Show current version information")
        print("  history    - Show version history")
        print("  check      - Check version compatibility")
        print("  export     - Export version information to file")
        print("  all        - Show all version information")
        return
    
    command = sys.argv[1].lower()
    
    if command == "current":
        print_version_info()
    elif command == "history":
        print_version_history()
    elif command == "check":
        check_version_compatibility()
    elif command == "export":
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        export_version_info(output_file)
    elif command == "all":
        print_version_info()
        print_version_history()
        check_version_compatibility()
    else:
        print(f"Unknown command: {command}")
        print("Use 'python version_manager.py' for help")

if __name__ == "__main__":
    main() 