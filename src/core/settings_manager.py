"""
ONOTE Settings Manager

Provides centralized access to application settings and preferences with proper precedence handling.
Settings Hierarchy:
1. Application Preferences (QSettings) - Default for new documents
2. Document-specific settings - Override preferences per document
3. Dialog overrides - Temporary overrides via Full Score Options dialog
"""

from PyQt6.QtCore import QSettings
import os
from typing import Any, Dict, Optional

class SettingsManager:
    """Centralized settings management for ONOTE with proper precedence handling"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.settings = QSettings("ONOTE", "Preferences")
            self._initialized = True
    
    # SETTINGS PRECEDENCE SYSTEM
    
    def get_setting_with_precedence(self, key: str, default_value: Any = None, 
                                  document_settings: Optional[Dict] = None) -> Any:
        """
        Get a setting value using proper precedence:
        1. Document-specific settings (highest priority)
        2. Application preferences (QSettings)
        3. Default value (fallback)
        """
        # First check document-specific settings
        if document_settings and key in document_settings:
            return document_settings[key]
        
        # Then check application preferences
        app_value = self.settings.value(key, None)
        if app_value is not None:
            return app_value
        
        # Finally use default value
        return default_value
    
    def load_default_document_settings(self) -> Dict[str, Any]:
        """
        Load default settings for a new document from application preferences.
        This creates the initial document settings based on user preferences.
        """
        document_settings = {}
        
        # Layout settings from preferences
        document_settings.update({
            'page_size': self.get_default_page_size(),
            'page_orientation': self.get_default_orientation(),
            'top_margin': self.get_default_top_margin(),
            'bottom_margin': self.get_default_bottom_margin(),
            'left_margin': self.get_default_left_margin(),
            'right_margin': self.get_default_right_margin(),
            'staff_spacing': self.get_default_staff_spacing(),
            'system_spacing': self.get_default_system_spacing(),
            'measures_per_system': self.get_default_measures_per_system(),
            'notation_scale': self.get_default_notation_scale(),
            'show_measure_numbers': self.get_show_measure_numbers(),
            'measure_numbers_frequency': self.get_measure_numbers_frequency(),
            'measure_numbers_position': self.get_measure_numbers_position(),
            'measure_numbers_vertical': self.get_measure_numbers_vertical(),
            'measure_numbers_font_size': self.get_measure_numbers_font_size(),
            'show_staff_names': self.get_show_staff_names(),
            'show_page_numbers': self.get_show_page_numbers(),
            'justify_last_system': self.get_justify_last_system(),
            'hide_empty_staves': self.get_hide_empty_staves(),
        })
        
        # Notation settings from preferences
        document_settings.update({
            'staff_name_font_size': self.get_staff_name_font_size(),
            'staff_name_vertical': self.get_staff_name_vertical(),
            'staff_name_horizontal': self.get_staff_name_horizontal(),
            'section_name_font_size': self.get_section_name_font_size(),
            'section_name_vertical': self.get_section_name_vertical(),
            'section_name_horizontal': self.get_section_name_horizontal(),
            'time_sig_font_size': self.get_time_sig_font_size(),
            'time_sig_vertical': self.get_time_sig_vertical(),
            'time_sig_horizontal': self.get_time_sig_horizontal(),
            'time_sig_spacing': self.get_time_sig_spacing(),
            'key_sig_font_size': self.get_key_sig_font_size(),
            'key_sig_vertical': self.get_key_sig_vertical(),
            'key_sig_horizontal': self.get_key_sig_horizontal(),
            'key_sig_accidental_spacing': self.get_key_sig_accidental_spacing(),
            'clef_font_size': self.get_clef_font_size(),
            'clef_vertical': self.get_clef_vertical(),
            'clef_horizontal': self.get_clef_horizontal(),
            'directions_font_size': self.get_directions_font_size(),
            'directions_vertical': self.get_directions_vertical(),
        })
        
        return document_settings
    
    # LAYOUT & PAGE SETTINGS (from preferences)
    
    def get_default_page_size(self):
        """Get the default page size"""
        return self.settings.value("layout/default_page_size", "A4 (210 × 297 mm)")
    
    def get_default_orientation(self):
        """Get the default page orientation"""
        return self.settings.value("layout/default_orientation", "Portrait")
    
    def get_default_top_margin(self):
        """Get the default top margin"""
        return float(self.settings.value("layout/default_top_margin", 20.0))
    
    def get_default_bottom_margin(self):
        """Get the default bottom margin"""
        return float(self.settings.value("layout/default_bottom_margin", 20.0))
    
    def get_default_left_margin(self):
        """Get the default left margin"""
        return float(self.settings.value("layout/default_left_margin", 25.0))
    
    def get_default_right_margin(self):
        """Get the default right margin"""
        return float(self.settings.value("layout/default_right_margin", 25.0))
    
    def get_default_staff_spacing(self):
        """Get the default staff spacing"""
        return int(self.settings.value("layout/default_staff_spacing", 40))
    
    def get_default_system_spacing(self):
        """Get the default system spacing"""
        return int(self.settings.value("layout/default_system_spacing", 80))
    
    def get_default_measures_per_system(self):
        """Get the default measures per system"""
        return int(self.settings.value("layout/default_measures_per_system", 4))
    
    def get_default_notation_scale(self):
        """Get the default notation scale"""
        return float(self.settings.value("layout/default_notation_size", 1.0))
    
    def get_show_measure_numbers(self):
        """Get whether to show measure numbers by default"""
        return self.settings.value("layout/show_measure_numbers", True, type=bool)
    
    def get_measure_numbers_frequency(self):
        """Get the measure numbers frequency"""
        return self.settings.value("layout/measure_numbers_frequency", "Every Measure")
    
    def get_measure_numbers_position(self):
        """Get the measure numbers position"""
        return self.settings.value("layout/measure_numbers_position", "Center")
    
    def get_measure_numbers_vertical(self):
        """Get the measure numbers vertical position"""
        return self.settings.value("layout/measure_numbers_vertical", "Above System")
    
    def get_measure_numbers_font_size(self):
        """Get the measure numbers font size"""
        return int(self.settings.value("layout/measure_numbers_font_size", 10))
    
    def get_show_staff_names(self):
        """Get whether to show staff names by default"""
        return self.settings.value("layout/show_staff_names", True, type=bool)
    
    def get_show_page_numbers(self):
        """Get whether to show page numbers by default"""
        return self.settings.value("layout/show_page_numbers", True, type=bool)
    
    def get_justify_last_system(self):
        """Get whether to justify the last system by default"""
        return self.settings.value("layout/justify_last_system", False, type=bool)
    
    def get_hide_empty_staves(self):
        """Get whether to hide empty staves by default"""
        return self.settings.value("layout/hide_empty_staves", False, type=bool)
    
    # NOTATION SETTINGS (from preferences)
    
    def get_staff_name_font_size(self):
        """Get the staff name font size"""
        return int(self.settings.value("notation/staff_name_font_size", 10))
    
    def get_staff_name_vertical(self):
        """Get the staff name vertical offset"""
        return int(self.settings.value("notation/staff_name_vertical", -8))
    
    def get_staff_name_horizontal(self):
        """Get the staff name horizontal offset"""
        return int(self.settings.value("notation/staff_name_horizontal", -50))
    
    def get_section_name_font_size(self):
        """Get the section name font size"""
        return int(self.settings.value("notation/section_name_font_size", 12))
    
    def get_section_name_vertical(self):
        """Get the section name vertical offset"""
        return int(self.settings.value("notation/section_name_vertical", -25))
    
    def get_section_name_horizontal(self):
        """Get the section name horizontal offset"""
        return int(self.settings.value("notation/section_name_horizontal", -60))
    
    def get_time_sig_font_size(self):
        """Get the time signature font size"""
        return int(self.settings.value("notation/time_sig_font_size", 24))
    
    def get_time_sig_vertical(self):
        """Get the time signature vertical offset"""
        return int(self.settings.value("notation/time_sig_vertical", 0))
    
    def get_time_sig_horizontal(self):
        """Get the time signature horizontal offset"""
        return int(self.settings.value("notation/time_sig_horizontal", 40))
    
    def get_time_sig_spacing(self):
        """Get the time signature spacing"""
        return int(self.settings.value("notation/time_sig_spacing", 18))
    
    def get_key_sig_font_size(self):
        """Get the key signature font size"""
        return int(self.settings.value("notation/key_sig_font_size", 14))
    
    def get_key_sig_vertical(self):
        """Get the key signature vertical offset"""
        return int(self.settings.value("notation/key_sig_vertical", 0))
    
    def get_key_sig_horizontal(self):
        """Get the key signature horizontal offset"""
        return int(self.settings.value("notation/key_sig_horizontal", 75))
    
    def get_key_sig_accidental_spacing(self):
        """Get the key signature accidental spacing"""
        return int(self.settings.value("notation/key_sig_accidental_spacing", 12))
    
    def get_clef_font_size(self):
        """Get the clef font size"""
        return int(self.settings.value("notation/clef_font_size", 32))
    
    def get_clef_vertical(self):
        """Get the clef vertical offset"""
        return int(self.settings.value("notation/clef_vertical", 0))
    
    def get_clef_horizontal(self):
        """Get the clef horizontal offset"""
        return int(self.settings.value("notation/clef_horizontal", 20))
    
    def get_directions_font_size(self):
        """Get the directions font size"""
        return int(self.settings.value("notation/directions_font_size", 11))
    
    def get_directions_vertical(self):
        """Get the directions vertical offset"""
        return int(self.settings.value("notation/directions_vertical", 30))
    
    # GENERAL SETTINGS (existing methods preserved)
    
    # General Settings
    def get_score_directory(self):
        """Get the default score directory"""
        default_path = "/Users/gilidor/Library/Mobile Documents/com~apple~CloudDocs/QC-Projects/ONOTE Music scores"
        return self.settings.value("general/score_directory", default_path)
    
    def get_view_mode(self):
        """Get the default view mode"""
        return self.settings.value("general/view_mode", "Pages Down")
    
    def get_autosave_interval(self):
        """Get the autosave interval in minutes"""
        return int(self.settings.value("general/autosave_interval", 5))
    
    def get_default_zoom(self):
        """Get the default zoom level"""
        return self.settings.value("general/default_zoom", "100%")
    
    def get_show_rulers(self):
        """Get whether to show rulers by default"""
        return self.settings.value("general/show_rulers", True, type=bool)
    
    def get_show_grid(self):
        """Get whether to show grid by default"""
        return self.settings.value("general/show_grid", False, type=bool)
    
    def get_recent_files_count(self):
        """Get the number of recent files to keep"""
        return int(self.settings.value("general/recent_files_count", 10))
    
    def get_create_backup(self):
        """Get whether to create backup files"""
        return self.settings.value("general/create_backup", True, type=bool)
    
    def get_auto_backup(self):
        """Get whether to auto-backup to external drive"""
        return self.settings.value("general/auto_backup", True, type=bool)
    
    # Audio Settings
    def get_audio_device(self):
        """Get the audio output device"""
        return self.settings.value("audio/device", "System Default")
    
    def get_sample_rate(self):
        """Get the sample rate"""
        return self.settings.value("audio/sample_rate", "44100 Hz")
    
    def get_buffer_size(self):
        """Get the buffer size"""
        return self.settings.value("audio/buffer_size", "512")
    
    # MIDI Record Settings
    def get_quantize_input(self):
        """Get the input quantization setting"""
        return self.settings.value("midi_record/quantize_input", "None")
    
    def get_record_mode(self):
        """Get the recording mode"""
        return self.settings.value("midi_record/record_mode", "Replace")
    
    def get_count_in(self):
        """Get the count-in measures"""
        return int(self.settings.value("midi_record/count_in", 1))
    
    def get_metronome_volume(self):
        """Get the metronome volume"""
        return int(self.settings.value("midi_record/metronome_volume", 80))
    
    def get_metronome_sound(self):
        """Get the metronome sound"""
        return self.settings.value("midi_record/metronome_sound", "Click")
    
    def get_metronome_playback(self):
        """Get whether metronome is enabled during playback"""
        return self.settings.value("midi_record/metronome_playback", True, type=bool)
    
    def get_metronome_recording(self):
        """Get whether metronome is enabled during recording"""
        return self.settings.value("midi_record/metronome_recording", True, type=bool)
    
    # MIDI Import Settings
    def get_import_quantize(self):
        """Get the import quantization setting"""
        return self.settings.value("midi_import/quantize", "None")
    
    def get_channel_handling(self):
        """Get the channel handling setting"""
        return self.settings.value("midi_import/channel_handling", "Merge All")
    
    def get_import_tempo(self):
        """Get whether to import tempo changes"""
        return self.settings.value("midi_import/import_tempo", True, type=bool)
    
    def get_import_dynamics(self):
        """Get whether to import dynamics"""
        return self.settings.value("midi_import/import_dynamics", True, type=bool)
    
    def get_import_articulations(self):
        """Get whether to import articulations"""
        return self.settings.value("midi_import/import_articulations", True, type=bool)
    
    def get_split_point(self):
        """Get the split point for grand staff"""
        return int(self.settings.value("midi_import/split_point", 60))
    
    def get_detect_tuplets(self):
        """Get whether to detect tuplets"""
        return self.settings.value("midi_import/detect_tuplets", True, type=bool)
    
    def get_detect_grace_notes(self):
        """Get whether to detect grace notes"""
        return self.settings.value("midi_import/detect_grace_notes", True, type=bool)
    
    def get_detect_pickup(self):
        """Get whether to detect pickup measures"""
        return self.settings.value("midi_import/detect_pickup", True, type=bool)
    
    # Generic get/set methods
    def get_setting(self, key: str, default=None):
        """Get a setting value with fallback to defaults"""
        # First try to get from QSettings
        value = self.settings.value(key, None)
        
        # If not found, try default settings
        if value is None:
            defaults = self._get_default_settings()
            if key in defaults:
                value = defaults[key]
                print(f"SETTINGS: Using default value for {key}: {value}")
            else:
                value = default
        
        print(f"SETTINGS: get_setting({key}) = {value}")
        return value
    
    def set_setting(self, key, value):
        """Set a setting by key"""
        self.settings.setValue(key, value)
        self.settings.sync()
    
    def sync(self):
        """Sync settings to disk"""
        self.settings.sync()

    def _get_default_settings(self):
        """Get default settings values"""
        return {
            # Layout & Page Settings
            "layout/page_width": 8.5,
            "layout/page_height": 11.0,
            "layout/page_margins_top": 1.0,
            "layout/page_margins_bottom": 1.0,
            "layout/page_margins_left": 1.0,
            "layout/page_margins_right": 1.0,
            "layout/system_spacing": 1.5,
            "layout/staff_spacing": 1.0,
            
            # CRITICAL FIX: Default to "Every Measure" for measure numbers
            "layout/measure_numbers_frequency": "Every Measure",  # Changed from "Every System"
            "layout/measure_numbers_position": "Beginning",  # Beginning of each measure
            "layout/measure_numbers_h_offset": -34,  # Horizontal offset from measure start (FIXED: reasonable position)  
            "layout/measure_numbers_v_offset": 9,   # Vertical offset from staff
            "layout/measure_numbers_horizontal_offset": -34,  # FIXED: Consistent key naming with same value
            
            # Staff and Note Settings
            "notation/staff_line_thickness": 0.5,
            "notation/default_clef": "treble",
            "notation/default_key_signature": "",
            "notation/default_time_signature": "4/4",
            
            # View Settings
            "view/zoom_level": 100,
            "view/show_rulers": True,
            "view/show_grid": False,
            "view/default_view_mode": "page_down",
            
            # Audio Settings
            "audio/sample_rate": 44100,
            "audio/buffer_size": 512,
            "audio/default_instrument": "piano",
            
            # Export Settings
            "export/default_format": "pdf",
            "export/image_resolution": 300,
            
            # UI Settings
            "ui/show_toolbar": True,
            "ui/show_statusbar": True,
            "ui/auto_save_interval": 300,  # seconds
        }

# Global instance
settings = SettingsManager() 