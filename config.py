# config.py
import os
import sys
from pathlib import Path
import json
from logger import Logger
from version import VERSION, VERSION_DATE

class Config:
    """Application configuration management"""
    # Singleton instance
    _instance = None
    
    # Default configuration
    DEFAULT_CONFIG = {
        'max_programs': 10,
        'inactivity_threshold': 3,
        'save_interval': 60,
        'window_size': {
            'width': 400,
            'height': 600
        },
        'mini_window_size': {
            'width': 180,
            'height': 45
        },
        'auto_minimize': False,
        'start_minimized': False,
        'start_at_startup': False,
        'start_in_mini_mode': True,
        'dark_mode': False,
        'media_mode_enabled': False,
        'media_programs': ['vlc.exe', 'mpv.exe', 'mpc-hc.exe', 'mpc-hc64.exe', 'mpc-be.exe', 'mpc-be64.exe', 'PotPlayerMini64.exe', 'PotPlayerMini.exe', 'MusicBee.exe', 'Spotify.exe'],
        'require_media_playback': False,
        'version': VERSION,
        'version_date': VERSION_DATE
    }
    
    def __new__(cls):
        """Create or return the singleton instance"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize configuration (only once)"""
        # Skip initialization if already done
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Initialize logger first to ensure it's available
        self.logger = Logger()
        
        # Get the base directory of the application using the logger's base_dir
        # This ensures we use the same base directory logic across the application
        base_dir = self.logger.get_base_dir()
        
        # Use absolute path for config file
        self.config_file = base_dir / 'tokikanri_config.json'
        
        # Load configuration
        self.load_config()
        
        # Log settings once at INFO level after initial load
        self.logger.info(f"Loaded settings: dark_mode={self.config.get('dark_mode')}, max_programs={self.config.get('max_programs')}")
        
        # Mark as initialized
        self._initialized = True

    def load_config(self):
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge loaded config with defaults
                    self.config = {**self.DEFAULT_CONFIG, **loaded_config}
                    self.logger.debug(f"Loaded settings from file: {self.config_file}")
            else:
                self.config = self.DEFAULT_CONFIG.copy()
                self.logger.info("Config file not found, using defaults")
                self.save_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = self.DEFAULT_CONFIG.copy()

    def save_config(self):
        """Save current configuration to file"""
        try:
            # Make sure the directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a temporary file first, then move it to avoid corruption
            temp_file = self.config_file.with_suffix('.tmp')
            
            # Write to the temporary file
            with open(temp_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            # If we got here, the write was successful, so move the temp file to the actual config file
            if temp_file.exists():
                # On Windows, we need to remove the destination file first
                if self.config_file.exists():
                    self.config_file.unlink()
                temp_file.rename(self.config_file)
                
                # Log success
                self.logger.info(f"Configuration saved to {self.config_file}")
                
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set configuration value and save"""
        old_value = self.config.get(key)
        self.config[key] = value
        self.logger.info(f"Config changed: {key} {old_value} -> {value}")
        
        # Save immediately after any setting change
        self.save_config()

    def update(self, updates):
        """Update multiple configuration values"""
        for k, v in updates.items():
            old_v = self.config.get(k)
            self.logger.info(f"Config updated: {k} {old_v} -> {v}")
            self.config[k] = v
        self.save_config()

    def export_config(self, filepath):
        """Export current configuration to a JSON file.

        Parameters
        ----------
        filepath : str
            Destination file path.
        Returns
        -------
        bool
            True on success, False on failure.
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Exported config to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting config: {Logger.format_error(e)}")
            return False

    def import_config(self, filepath):
        """Import configuration from a JSON file.

        Parameters
        ----------
        filepath : str
            Source file path.
        Returns
        -------
        bool
            True on success, False on failure.
        """
        try:
            if not Path(filepath).exists():
                self.logger.error(f"Import path does not exist: {filepath}")
                return False

            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            if not isinstance(loaded_config, dict):
                self.logger.error("Imported config has unexpected format.")
                return False

            # Merge loaded config with current config, prioritizing loaded values
            self.config = {**self.config, **loaded_config}
            self.save_config()
            self.logger.info(f"Imported config from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing config: {Logger.format_error(e)}")
            return False

    def get_version(self):
        """Get the application version information
        
        Returns
        -------
        tuple
            (version, version_date)
        """
        return (
            self.config.get('version', VERSION),
            self.config.get('version_date', VERSION_DATE)
        )
        
    def update_version(self):
        """Update the stored version information to the current version"""
        self.config['version'] = VERSION
        self.config['version_date'] = VERSION_DATE
        self.save_config()
