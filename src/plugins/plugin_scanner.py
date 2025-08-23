import os
import platform
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict
import glob
import json

@dataclass
class Plugin:
    name: str
    path: str
    format: str  # "VST" or "VST3"
    is_enabled: bool = True
    vendor: str = "Unknown"
    version: str = "Unknown"
    category: str = "Unknown"
    id: str = ""  # Unique identifier for the plugin
    instruments: List[Dict] = None  # List of instruments provided by the plugin
    
    def __post_init__(self):
        if not self.id:
            # Generate a unique ID based on the path if not provided
            self.id = self.path.replace(os.sep, '_').replace('.', '_').lower()
        if self.instruments is None:
            # Initialize with a default instrument based on the plugin name
            self.instruments = [{
                'id': self.id,
                'name': self.name,
                'type': 'synthesizer'
            }]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Plugin':
        return cls(**data)
    
class PluginScanner:
    def __init__(self):
        self.system = platform.system()
        self.vst_paths = []
        self.vst3_paths = []
        self.plugins: List[Plugin] = []
        self.plugin_states = {}
        self.settings_file = os.path.expanduser("~/.onote/plugin_settings.json")
        self._setup_default_paths()
        self._load_settings()
        
    def _setup_default_paths(self):
        """Setup default plugin paths based on OS"""
        if self.system == "Darwin":  # macOS
            # VST paths
            self.vst_paths = [
                "/Library/Audio/Plug-Ins/VST",
                os.path.expanduser("~/Library/Audio/Plug-Ins/VST"),
                "/Applications/VSTPlugins",
                "/Library/Application Support/VSTPlugins"
            ]
            # VST3 paths
            self.vst3_paths = [
                "/Library/Audio/Plug-Ins/VST3",
                os.path.expanduser("~/Library/Audio/Plug-Ins/VST3"),
                "/Applications/VST3",
                "/Library/Application Support/VST3"
            ]
        elif self.system == "Windows":
            # Common VST paths on Windows
            program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            self.vst_paths = [
                os.path.join(program_files, "VSTPlugins"),
                os.path.join(program_files, "Steinberg\\VSTPlugins"),
                os.path.join(program_files_x86, "VSTPlugins"),
                os.path.join(program_files_x86, "Steinberg\\VSTPlugins"),
                os.path.join(program_files, "Common Files\\VST2")
            ]
            self.vst3_paths = [
                os.path.join(program_files, "Common Files\\VST3"),
                os.path.join(program_files_x86, "Common Files\\VST3")
            ]
        elif self.system == "Linux":
            # Common VST paths on Linux
            self.vst_paths = [
                "/usr/lib/vst",
                "/usr/local/lib/vst",
                os.path.expanduser("~/.vst"),
                "/usr/lib/lxvst",
                "/usr/local/lib/lxvst",
                os.path.expanduser("~/.lxvst")
            ]
            self.vst3_paths = [
                "/usr/lib/vst3",
                "/usr/local/lib/vst3",
                os.path.expanduser("~/.vst3")
            ]
            
    def _ensure_settings_dir(self):
        """Ensure the settings directory exists"""
        settings_dir = os.path.dirname(self.settings_file)
        os.makedirs(settings_dir, exist_ok=True)
        
    def _load_settings(self):
        """Load plugin settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    # Load custom paths
                    self.vst_paths.extend(data.get('vst_paths', []))
                    self.vst3_paths.extend(data.get('vst3_paths', []))
                    # Remove duplicates while preserving order
                    self.vst_paths = list(dict.fromkeys(self.vst_paths))
                    self.vst3_paths = list(dict.fromkeys(self.vst3_paths))
                    # Load plugin states
                    self.plugin_states = data.get('plugin_states', {})
        except Exception as e:
            print(f"Error loading plugin settings: {e}")
            self.plugin_states = {}
            
    def _save_settings(self):
        """Save plugin settings to file"""
        try:
            self._ensure_settings_dir()
            data = {
                'vst_paths': self.vst_paths,
                'vst3_paths': self.vst3_paths,
                'plugin_states': {
                    plugin.path: {
                        'is_enabled': plugin.is_enabled,
                        'name': plugin.name,
                        'format': plugin.format,
                        'vendor': plugin.vendor,
                        'version': plugin.version,
                        'category': plugin.category
                    }
                    for plugin in self.plugins
                }
            }
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving plugin settings: {e}")
            
    def add_custom_path(self, path: str, format_type: str):
        """Add a custom path to scan for plugins"""
        if format_type.upper() == "VST":
            if path not in self.vst_paths:
                self.vst_paths.append(path)
        elif format_type.upper() == "VST3":
            if path not in self.vst3_paths:
                self.vst3_paths.append(path)
        self._save_settings()
                
    def _is_plugin_file(self, filename: str, format_type: str) -> bool:
        """Check if a file is a plugin based on extension"""
        if format_type.upper() == "VST":
            if self.system == "Darwin":
                return filename.lower().endswith((".vst", ".component"))
            elif self.system == "Windows":
                return filename.lower().endswith((".dll", ".vst"))
            else:  # Linux
                return filename.lower().endswith((".so", ".vst"))
        elif format_type.upper() == "VST3":
            return filename.lower().endswith(".vst3")
        return False

    def _extract_plugin_info(self, path: str) -> tuple:
        """Extract plugin metadata from the file path and structure"""
        name = os.path.splitext(os.path.basename(path))[0]
        vendor = "Unknown"
        version = "Unknown"
        category = "Unknown"

        # Try to extract vendor from path components
        path_parts = path.split(os.sep)
        for part in path_parts:
            if part.lower() in ["native instruments", "waves", "izotope", "fabfilter", 
                              "u-he", "arturia", "steinberg", "universal audio"]:
                vendor = part
                break

        # For VST3 bundles on macOS, try to get more info from Info.plist
        if self.system == "Darwin" and path.endswith(".vst3"):
            info_plist = os.path.join(path, "Contents/Info.plist")
            if os.path.exists(info_plist):
                try:
                    import plistlib
                    with open(info_plist, 'rb') as fp:
                        pl = plistlib.load(fp)
                        if 'CFBundleShortVersionString' in pl:
                            version = pl['CFBundleShortVersionString']
                        if 'CFBundleGetInfoString' in pl:
                            info = pl['CFBundleGetInfoString']
                            if ' by ' in info:
                                vendor = info.split(' by ')[1].split()[0]
                except:
                    pass

        return name, vendor, version, category
    
    def scan_plugins(self) -> List[Plugin]:
        """Scan for VST and VST3 plugins in all configured paths"""
        plugins = []
        
        # Helper function to scan directory
        def scan_directory(base_path: str, format_type: str):
            if not os.path.exists(base_path):
                return
            
            # Use glob for recursive search
            if self.system == "Darwin":
                if format_type == "VST":
                    patterns = ["**/*.vst", "**/*.component"]
                else:  # VST3
                    patterns = ["**/*.vst3"]
            elif self.system == "Windows":
                if format_type == "VST":
                    patterns = ["**/*.dll", "**/*.vst"]
                else:  # VST3
                    patterns = ["**/*.vst3"]
            else:  # Linux
                if format_type == "VST":
                    patterns = ["**/*.so", "**/*.vst"]
                else:  # VST3
                    patterns = ["**/*.vst3"]
            
            for pattern in patterns:
                full_pattern = os.path.join(base_path, pattern)
                for path in glob.glob(full_pattern, recursive=True):
                    name, vendor, version, category = self._extract_plugin_info(path)
                    # Check if we have saved state for this plugin
                    plugin_state = self.plugin_states.get(path, {})
                    is_enabled = plugin_state.get('is_enabled', True)
                    plugins.append(Plugin(
                        name=name,
                        path=path,
                        format=format_type,
                        vendor=vendor,
                        version=version,
                        category=category,
                        is_enabled=is_enabled
                    ))
        
        # Scan VST plugins
        for path in self.vst_paths:
            scan_directory(path, "VST")
        
        # Scan VST3 plugins
        for path in self.vst3_paths:
            scan_directory(path, "VST3")
        
        self.plugins = sorted(plugins, key=lambda x: x.name.lower())
        self._save_settings()
        return self.plugins
        
    def update_plugin_state(self, plugin: Plugin):
        """Update the state of a plugin and save settings"""
        for p in self.plugins:
            if p.path == plugin.path:
                p.is_enabled = plugin.is_enabled
                break
        self._save_settings()
        
    def get_enabled_plugins(self) -> List[Plugin]:
        """Get list of enabled plugins"""
        # Scan for plugins if we haven't already
        if not self.plugins:
            self.scan_plugins()
        return [plugin for plugin in self.plugins if plugin.is_enabled] 