# data_manager.py
import json
import csv
import os
import time
from pathlib import Path
from logger import Logger
from config import Config # Import Config

class DataManager:
    """Manages program data persistence and tracking"""
    def __init__(self, config: Config): # Accept config object
        self.tracked_programs = {}
        self.currently_tracking = None
        self.start_time = None
        self.logger = Logger()
        self.config = config # Store config object
        self.max_programs = self.config.get('max_programs') # Get max_programs from config
        self.data_file_path = self.logger.get_base_dir() / 'program_tracker_data.json'
        self.load_data()
        
        # After loading data, only update max_programs if tracked programs exceed the limit
        num_tracked_programs = len(self.tracked_programs)
        max_programs_val = self.max_programs or 0  # Handle None case
        if num_tracked_programs > max_programs_val:
            self.logger.info(f"Loaded {num_tracked_programs} programs, which exceeds current max limit of {self.max_programs}. Updating max_programs setting.")
            self.config.set('max_programs', num_tracked_programs)
            self.max_programs = num_tracked_programs
        
    def save_data(self):
        """Save tracked program data to file"""
        try:
            with open(self.data_file_path, 'w') as f:
                json.dump({'tracked_programs': self.tracked_programs}, f)
        except Exception as e:
            self.logger.error(f"Error saving data: {Logger.format_error(e)}")
            
    def export_data(self, filepath):
        """Export tracked program data to a JSON or CSV file.

        Parameters
        ----------
        filepath : str
            Destination file path. Extension determines format (``.json`` or ``.csv``).
        Returns
        -------
        bool
            ``True`` on success, ``False`` on failure.
        """
        try:
            if filepath.lower().endswith('.csv'):
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['program', 'seconds'])
                    for program, seconds in self.tracked_programs.items():
                        writer.writerow([program, seconds])
            else:  # default to JSON
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({'tracked_programs': self.tracked_programs}, f, indent=2)
            self.logger.info(f"Exported data to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error exporting data: {Logger.format_error(e)}")
            return False

    def import_data(self, filepath, merge=False):
        """Import program data from a JSON or CSV file.

        Parameters
        ----------
        filepath : str
            Source file path. Extension determines format (``.json`` or ``.csv``).
        merge : bool, optional
            If ``True``, merge with existing data (summing times). If ``False`` replace existing data. Default ``False``.
        Returns
        -------
        bool
            ``True`` on success, ``False`` on failure.
        """
        try:
            # Ensure self.max_programs is up-to-date with the current config value
            self.max_programs = self.config.get('max_programs')

            loaded_data = {}
            if not os.path.exists(filepath):
                self.logger.error(f"Import path does not exist: {filepath}")
                return False

            if filepath.lower().endswith('.csv'):
                with open(filepath, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        program = row.get('program') or row.get('Program')
                        seconds = float(row.get('seconds') or row.get('Seconds') or 0)
                        loaded_data[program] = seconds
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Support both legacy and bare dict formats
                    loaded_data = data.get('tracked_programs', data)

            if not isinstance(loaded_data, dict):
                self.logger.error("Imported data has unexpected format.")
                return False

            if merge:
                # Calculate the potential new size after merge
                merged_keys = set(self.tracked_programs.keys()).union(set(loaded_data.keys()))
                potential_new_size = len(merged_keys)

                # If merging would exceed max_programs, update the setting
                max_programs_val = self.max_programs or 0  # Handle None case
                if potential_new_size > max_programs_val:
                    self.logger.info(f"Merging data would result in {potential_new_size} programs, which exceeds the current max limit of {self.max_programs}. Updating max_programs setting.")
                    self.config.set('max_programs', potential_new_size)
                    self.max_programs = potential_new_size # Update local attribute as well

                for program, seconds in loaded_data.items():
                    self.tracked_programs[program] = self.tracked_programs.get(program, 0) + seconds
            else:
                # If replacing, update max_programs if imported data has more programs
                max_programs_val = self.max_programs or 0  # Handle None case
                if len(loaded_data) > max_programs_val:
                    self.logger.info(f"Imported data contains {len(loaded_data)} programs, which exceeds the current max limit of {self.max_programs}. Updating max_programs setting.")
                    self.config.set('max_programs', len(loaded_data))
                    self.max_programs = len(loaded_data) # Update local attribute as well
                self.tracked_programs = loaded_data

            self.save_data()
            self.logger.info(f"Imported data from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error importing data: {Logger.format_error(e)}")
            return False

    def load_data(self):
        """Load tracked program data from file"""
        try:
            if self.data_file_path.exists():
                with open(self.data_file_path, 'r') as f:
                    data = json.load(f)
                    self.tracked_programs = data['tracked_programs']
            else:
                self.tracked_programs = {}
        except Exception as e:
            self.logger.error(f"Error loading data: {Logger.format_error(e)}")
            self.tracked_programs = {}
            
    def update_tracking(self, program, is_active):
        """Update tracking for specified program"""
        if program != self.currently_tracking:
            if self.currently_tracking and self.start_time is not None:
                self._update_elapsed_time() # Changed from _save_elapsed_time
            
            self.currently_tracking = program
            self.start_time = time.time() if is_active else None
            
        elif self.start_time is not None and is_active:
            self._update_elapsed_time() # Changed from _save_elapsed_time
            self.start_time = time.time()
            
    def _update_elapsed_time(self): # Renamed from _save_elapsed_time
        """Update elapsed time for current program"""
        if self.currently_tracking and self.start_time is not None:
            elapsed = time.time() - self.start_time
            self.tracked_programs[self.currently_tracking] = self.tracked_programs.get(self.currently_tracking, 0) + elapsed # Ensure program exists
            # self.save_data() # Removed save_data call
            
    def get_current_times(self):
        """Get current times for all programs including active session"""
        current_times = self.tracked_programs.copy()
        
        if (self.currently_tracking and 
            self.start_time is not None):
            elapsed = time.time() - self.start_time
            current_times[self.currently_tracking] = current_times.get(
                self.currently_tracking, 0) + elapsed
                
        return current_times
        
    def reset_program(self, program):
        """Reset timer for specified program"""
        if program in self.tracked_programs:
            self.tracked_programs[program] = 0
            if self.currently_tracking == program:
                self.start_time = time.time()
            self.save_data() # Keep save here as it's a direct user action
            self.logger.info(f"Timer reset for {program}")
            
    def reset_all_programs(self):
        """Reset timers for all programs"""
        for program in self.tracked_programs:
            self.tracked_programs[program] = 0
        if self.currently_tracking:
            self.start_time = time.time()
        self.save_data() # Keep save here as it's a direct user action
        self.logger.info("All timers reset")
            
    def remove_program(self, program):
        """Remove program from tracking"""
        if program in self.tracked_programs:
            if self.currently_tracking == program:
                self.currently_tracking = None
                self.start_time = None
            del self.tracked_programs[program]
            self.save_data() # Keep save here as it's a direct user action
            self.logger.info(f"Stopped tracking {program}")
            
    def remove_all_programs(self):
        """Remove all programs from tracking"""
        self.tracked_programs = {}
        self.currently_tracking = None
        self.start_time = None
        self.save_data()
        self.logger.info("Removed all tracked programs")
