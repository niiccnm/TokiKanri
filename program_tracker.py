# program_tracker.py
import tkinter as tk
import threading
import os
import time
from tkinter import messagebox, filedialog
import win32gui
import win32process
import psutil
from main_window import MainWindow
from mini_window import MiniWindow
from activity_tracker import ActivityTracker
from data_manager import DataManager
from window_selector import WindowSelector
from system_tray import SystemTrayIcon
from utils import TimeFormatter, Timer
from config import Config
from logger import Logger
from ui_components import ModernStyle
from version import get_version_string

class ProgramTokiKanri:
    """Main program tracker class"""
    def __init__(self):
        self.is_shutting_down = False
        self.always_on_top = False
        self.last_update_time = time.time()
        self.last_program = None  # Track last program for detecting switches
        self.last_save_time = time.time() # For periodic saving
        
        # Initialize components
        self.logger = Logger()
        self.logger.info("Initializing ProgramTokiKanri")
        
        # Initialize config first
        self.config = Config()
        
        # Update version information in config
        self.config.update_version()
        
        # Initialize dark mode from config
        dark_mode = self.config.get("dark_mode", False)
        ModernStyle.toggle_dark_mode(dark_mode)
        
        # Create the main root window and apply styles
        self.root = tk.Tk()
        self.root.withdraw()  # Hide initially, will be managed by MainWindow
        ModernStyle.apply(self.root)
        
        self.data_manager = DataManager(self.config)
        self.activity_tracker = ActivityTracker()
        
        # DataManager already handles max_programs check and update when loading data
        # Use the max_programs value from data_manager which is guaranteed to be updated if needed
        self.window_selector = WindowSelector(self.data_manager.max_programs)
        self.timer = Timer()
        
        # Create windows
        self.main_window = MainWindow(self)
        self.mini_window = MiniWindow(self)
        
        # Initialize program widgets with loaded data
        self.main_window.program_gui.create_program_widgets(
            self.data_manager.tracked_programs,
            self.data_manager.get_current_times(),
            self.data_manager.currently_tracking
        )
        
        # Setup system tray
        self.system_tray = SystemTrayIcon(self)
        
        # Update UI for dark mode if enabled
        if dark_mode:
            self.logger.info("Applying dark mode to UI elements")
            self.main_window.update_ui_for_theme()
            # Mini window doesn't need theme updates as it uses fixed colors
        
        # Update activity tracker settings from config
        self.update_activity_tracker_settings()
        
        # Start tracking loops
        self._start_tracking_loops()
        
    def _start_tracking_loops(self):
        """Start timer and activity tracking loops"""
        self.update_timer()
        self.check_activity()
        
    def update_timer(self):
        """Main timer update loop"""
        if self.is_shutting_down:
            return
            
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Track if any program time has been updated
        time_updated = False
            
        if not self.window_selector.selecting_window:
            try:
                current_process = self.activity_tracker.get_active_window_info()
                program_switched = current_process != self.last_program
                
                if current_process in self.data_manager.tracked_programs:
                    # Only update time if we're active
                    if self.activity_tracker.is_active:
                        self.data_manager.tracked_programs[current_process] += time_delta
                        self.data_manager.currently_tracking = current_process
                        self._update_status(True, current_process)
                        time_updated = True
                    else:
                        self.data_manager.currently_tracking = current_process  # Keep tracking the program even when inactive
                        self._update_status(False, current_process)
                        
                    # Always reorder widgets when program switched or time updated
                    if program_switched or time_updated:
                        # Use reorder_widgets which now respects search filters and always sorts by time
                        self.main_window.program_gui.reorder_widgets(
                            self.data_manager.get_current_times(),
                            self.data_manager.currently_tracking
                        )
                    
                    # Always update displays to ensure mini window shows correct time
                    self._update_displays()
                else:
                    # Stop tracking if current window is not tracked
                    self.data_manager.currently_tracking = None
                    self._update_status(False, None)
                    self._update_displays()
                
                self.last_program = current_process
                
                # Periodic data saving
                if current_time - self.last_save_time >= (self.config.get('save_interval') or 60):  # Default to 60 seconds if None
                    self.data_manager.save_data()
                    self.last_save_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in update_timer: {Logger.format_error(e)}")
                
        if not self.is_shutting_down:
            self.main_window.root.after(1000, self.update_timer) # Update timer every 1 second
            
    def check_activity(self):
        """Activity checking loop"""
        if self.is_shutting_down:
            return
            
        was_active = self.activity_tracker.is_active
        if self.activity_tracker.check_activity():
            # If activity state changed, update sorting
            if was_active != self.activity_tracker.is_active:
                self._handle_activity_change()
                # Reorder widgets to reflect new activity state without recreating
                # Use reorder_widgets which now respects search filters and always sorts by time
                self.main_window.program_gui.reorder_widgets(
                    self.data_manager.get_current_times(),
                    self.data_manager.currently_tracking
                )
                # Immediately update displays to reflect the activity change
                self._update_displays()
            
        if not self.is_shutting_down:
            # Check more frequently to be more responsive to media state changes
            self.main_window.root.after(50, self.check_activity) # Increased responsiveness for media tracking
            
    def _handle_activity_change(self):
        """Handle changes in activity state"""
        if self.data_manager.currently_tracking:
            if self.activity_tracker.is_active:
                self.last_update_time = time.time()  # Reset timer base on resume
                self._update_status(True, self.data_manager.currently_tracking)
            else:
                self._update_status(False, self.data_manager.currently_tracking)
                # Force an immediate update when activity stops
                self._update_displays()
                # Save data immediately when activity stops
                self.data_manager.save_data()
    
    def update_activity_tracker_settings(self):
        """Update ActivityTracker settings from config"""
        # Get the latest settings from config
        old_media_mode = self.activity_tracker.media_mode_enabled
        old_require_playback = self.activity_tracker.require_media_playback
        old_media_programs = self.activity_tracker.media_programs
        
        # Update settings from config
        self.activity_tracker.inactivity_threshold = self.config.get('inactivity_threshold')
        self.activity_tracker.media_mode_enabled = self.config.get('media_mode_enabled', False)
        self.activity_tracker.require_media_playback = self.config.get('require_media_playback', True)
        
        # Make sure we get the latest media_programs list from the config
        media_programs = self.config.get('media_programs', [])
        if not media_programs:
            media_programs = []
            
        self.activity_tracker.media_programs = media_programs
        
        # Log only significant changes
        media_programs_changed = set(old_media_programs) != set(media_programs)
        
        if old_media_mode != self.activity_tracker.media_mode_enabled:
            self.logger.info(f"Media mode changed: {old_media_mode} -> {self.activity_tracker.media_mode_enabled}")
            
        if old_require_playback != self.activity_tracker.require_media_playback:
            self.logger.info(f"Require media playback changed: {old_require_playback} -> {self.activity_tracker.require_media_playback}")
            if not self.activity_tracker.require_media_playback:
                self.logger.info("Media programs will be considered active regardless of playback status")
            else:
                self.logger.info("Media programs will only be considered active when media is playing")
                
        # Only log media programs if they've changed or if media mode was just enabled
        if media_programs_changed or (not old_media_mode and self.activity_tracker.media_mode_enabled):
            self.activity_tracker.log_media_programs()
                    
    def _update_displays(self):
        """Update all displays with current data"""
        # Get current times
        current_times = self.data_manager.get_current_times()
        
        # Update main window displays
        self.main_window.program_gui.update_displays(
            current_times,
            self.data_manager.currently_tracking
        )
        
        # Update total time
        total_time = sum(current_times.values())
        self.main_window.update_total_time(
            TimeFormatter.format_time(total_time)
        )
        
        # Update mini window - always show current time when tracking, even when inactive
        if self.data_manager.currently_tracking:
            # Get the time for the currently tracking program
            current_program = self.data_manager.currently_tracking
            if current_program in self.data_manager.tracked_programs:
                current_time = self.data_manager.tracked_programs[current_program]
                self.mini_window.update_display(
                    TimeFormatter.format_time(current_time),
                    self.activity_tracker.is_active,
                    True  # Always true when we have a currently tracking program
                )
            else:
                # Fallback if the program isn't in tracked_programs (shouldn't happen)
                self.mini_window.update_display("00:00", self.activity_tracker.is_active, True)
        else:
            self.mini_window.update_display("--:--", False, False)
            
    def _update_status(self, is_active, program=None):
        """Update status displays"""
        if program is None:
            status_text = "Ready to Track"
        else:
            # Get custom display name if available
            display_name = self.data_manager.get_display_name(program)
            # Format the program name
            if display_name:
                program_display = display_name
            else:
                # Use the same formatting logic as in program_gui.py
                lower = program.lower()
                if lower in ('explorer.exe', 'explorer'):
                    program_display = 'Windows File Explorer'
                elif lower == 'clipstudiopaint.exe':
                    program_display = 'Clip Studio Paint'
                elif lower == 'code.exe':
                    program_display = 'VS Code'
                elif lower == 'dnplayer.exe':
                    program_display = 'LDPlayer'
                else:
                    program_display = program[:-4] if lower.endswith('.exe') else program
                
                # Capitalize first character if it is lowercase
                if program_display and program_display[0].islower():
                    program_display = program_display[0].upper() + program_display[1:]
            
            if is_active:
                status_text = f"Tracking: {program_display}"
            else:
                status_text = "Tracking paused: No activity"
            
        self.main_window.update_status(status_text, is_active)
        
        # Also update mini window status
        self.mini_window.update_status(is_active, program)
        
    # Window management methods
    def show_mini_window(self):
        """Show mini window and hide main window"""
        self.mini_window.show()
        self.main_window.root.withdraw()

    def show_main_window(self):
        """Show main window"""
        self.mini_window.hide()
        self.main_window.root.deiconify()
        self.main_window.root.lift()
        
    def minimize_to_tray(self):
        """Minimize to system tray"""
        self.main_window.root.withdraw()
        self.mini_window.show()
        
    def toggle_always_on_top(self):
        """Toggle always on top state"""
        self.always_on_top = not self.always_on_top
        # Apply pin to main window
        self.main_window.root.attributes('-topmost', self.always_on_top)
        # Apply pin to settings window if it exists
        try:
            if hasattr(self.main_window, '_settings_window') and self.main_window._settings_window.winfo_exists():
                self.main_window._settings_window.wm_attributes('-topmost', self.always_on_top)
        except Exception:
            pass
        self.main_window.update_pin_button(self.always_on_top)
        
    # Window selection methods
    def start_window_selection(self):
        """Start window selection process"""
        if not self.window_selector.selecting_window:
            self.window_selector.selecting_window = True
            self.main_window.update_select_button(True)
            self.main_window.update_status("Selecting window... Click on target window")
            self.main_window.root.iconify()  # Minimize the window
            self.main_window.root.after(100, self.check_selected_window)
            
    def check_selected_window(self):
        """Check for selected window"""
        if self.window_selector.selecting_window:
            result = self.window_selector.check_selected_window(
                self.data_manager.tracked_programs
            )
            
            if result:
                process_name, status = result

                if status == 'MAX_REACHED':
                    messagebox.showwarning("Limit Reached", f"Cannot track more than {self.config.get('max_programs')} programs. Please adjust the setting or remove existing programs.")
                    self.window_selector.selecting_window = False
                    self.main_window.update_select_button(False)
                    self.main_window.root.deiconify()
                    self._update_status(False, None)
                    return
                elif status == 'ERROR':
                    messagebox.showerror("Selection Error", "An error occurred during window selection. Please try again.")
                    self.window_selector.selecting_window = False
                    self.main_window.update_select_button(False)
                    self.main_window.root.deiconify()
                    self._update_status(False, None)
                    return
                elif status == 'NO_WINDOW':
                    # Continue checking if no valid window selected yet
                    self.main_window.root.after(100, self.check_selected_window)
                    return
                
                # If we reach here, it means a program was selected (process_name, True/False)
                is_new = status # Renamed from is_new to status in window_selector, but here it's still a boolean

                # If the program is already being tracked, inform the user and exit selection mode
                if not is_new:
                    messagebox.showinfo("Already Tracking", f"'{process_name}' is already being tracked.")
                    self.window_selector.selecting_window = False
                    self.main_window.update_select_button(False)
                    self.main_window.root.deiconify()
                    self._update_status(False, None)
                    return
                self.logger.info(f"Started tracking {process_name}")
                
                # Add new program to tracking
                self.data_manager.tracked_programs[process_name] = 0
                
                # Immediately start tracking if active
                if self.activity_tracker.is_active:
                    self.data_manager.currently_tracking = process_name
                    self.last_update_time = time.time()
                
                # Update UI
                self.main_window.program_gui.create_program_widgets(
                    self.data_manager.tracked_programs,
                    self.data_manager.get_current_times(),
                    self.data_manager.currently_tracking
                )
                
                # Update status
                self._update_status(self.activity_tracker.is_active, process_name)
                
                # Save data
                self.data_manager.save_data()
                
                # Reset selection state
                self.window_selector.selecting_window = False
                self.main_window.update_select_button(False)
                self.main_window.root.deiconify()  # Restore the window
                return
                
            # Continue checking if no window selected yet (this line is now redundant due to 'NO_WINDOW' handling above)
            self.main_window.root.after(100, self.check_selected_window)
            
    # Program management methods
    def reset_timer(self, program):
        """Reset timer for specific program"""
        self.data_manager.reset_program(program)
        self._update_displays()
        
    def export_data(self):
        """Prompt user to export data to a file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"),
                ("CSV Files", "*.csv"),
                ("All Files", "*.*"),
            ],
            title="Export TokiKanri data to...",
        )
        if filepath:
            if self.data_manager.export_data(filepath):
                messagebox.showinfo("Export Successful", f"Data exported to {filepath}")
            else:
                messagebox.showerror("Export Failed", "Unable to export data. Check logs for details.")

    def import_data(self):
        """Prompt user to import data from a file."""
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("JSON Files", "*.json"),
                ("CSV Files", "*.csv"),
                ("All Files", "*.*"),
            ],
            title="Import TokiKanri data from...",
        )
        if filepath:
            merge = messagebox.askyesno("Merge or Replace?", "Do you want to MERGE the imported data with existing timers?\nChoose No to replace existing data.")
            if self.data_manager.import_data(filepath, merge=merge):
                # Explicitly reload config to ensure settings window gets the latest max_programs value
                self.config.load_config()
                # Update max_programs in window_selector after data import, as config might have changed
                self.window_selector.max_programs = self.config.get('max_programs')
                
                # Re-initialize settings window to reflect new config if it's open
                if hasattr(self.main_window, '_settings_window') and self.main_window._settings_window.winfo_exists():
                    self.main_window._settings_window.destroy() # Destroy old instance
                    del self.main_window._settings_window # Remove reference
                    self.main_window._open_settings() # Open new instance with updated config
                
                # Refresh UI after import
                self.main_window.program_gui.create_program_widgets(
                    self.data_manager.tracked_programs,
                    self.data_manager.get_current_times(),
                    self.data_manager.currently_tracking,
                )
                self._update_displays()
                messagebox.showinfo("Import Successful", f"Data imported from {filepath}")
            else:
                messagebox.showerror("Import Failed", "Unable to import data. Check logs for details.")

    def export_config(self):
        """Prompt user to export configuration to a file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
            title="Export TokiKanri Configuration to...",
        )
        if filepath:
            if self.config.export_config(filepath):
                messagebox.showinfo("Export Successful", f"Configuration exported to {filepath}")
            else:
                messagebox.showerror("Export Failed", "Unable to export configuration. Check logs for details.")

    def import_config(self):
        """Prompt user to import configuration from a file."""
        filepath = filedialog.askopenfilename(
            filetypes=[
                ("JSON Files", "*.json"),
                ("All Files", "*.*"),
            ],
            title="Import TokiKanri Configuration from...",
        )
        if filepath:
            if self.config.import_config(filepath):
                messagebox.showinfo("Import Successful", f"Configuration imported from {filepath}")
                # Re-initialize settings window to reflect new config
                if hasattr(self.main_window, '_settings_window') and self.main_window._settings_window.winfo_exists():
                    self.main_window._settings_window.destroy() # Destroy old instance
                    del self.main_window._settings_window # Remove reference
                self.main_window._open_settings() # Open new instance with updated config
                # Update max_programs in window_selector
                self.window_selector.max_programs = self.config.get('max_programs')
            else:
                messagebox.showerror("Import Failed", "Unable to import configuration. Check logs for details.")

    def reset_all_timers(self):
        """Reset all program timers"""
        self.data_manager.reset_all_programs()
        self.main_window.program_gui.create_program_widgets(
            self.data_manager.tracked_programs,
            self.data_manager.get_current_times(),
            self.data_manager.currently_tracking
        )
        
    def remove_program(self, program):
        """Remove program from tracking"""
        self.data_manager.remove_program(program)
        self.main_window.program_gui.create_program_widgets(
            self.data_manager.tracked_programs,
            self.data_manager.get_current_times(),
            self.data_manager.currently_tracking
        )
        
    def remove_all_programs(self):
        """Remove all programs from tracking"""
        if not self.data_manager.tracked_programs:
            # No programs to remove
            return
            
        # Show confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Remove All",
            "Are you sure you want to remove all tracked programs? This cannot be undone.",
            icon="warning"
        )
        
        if confirm:
            self.data_manager.remove_all_programs()
            self.main_window.program_gui.create_program_widgets(
                self.data_manager.tracked_programs,
                self.data_manager.get_current_times(),
                self.data_manager.currently_tracking
            )
            self._update_status(False, None)  # Reset status
        
    def quit_app(self):
        """Clean shutdown of application"""
        try:
            self.is_shutting_down = True
            self.data_manager.save_data()
            
            if hasattr(self, 'system_tray'):
                self.system_tray.stop()
                
            self.mini_window.window.destroy()
            self.main_window.root.quit()
            self.main_window.root.destroy()
            
            if threading.active_count() > 1:
                os._exit(0)
                
        except Exception as e:
            self.logger.critical(f"Error during shutdown: {Logger.format_error(e)}")
            os._exit(1)
            
    def run(self):
        """Start the application"""
        # Ensure config is saved before starting
        self.config.save_config()
        
        # Show mini window if configured
        start_in_mini_mode = self.config.get('start_in_mini_mode', False)
        self.logger.info(f"Starting in mini mode: {start_in_mini_mode}")
        
        if start_in_mini_mode:
            self.logger.info("Showing mini window")
            self.mini_window.show()
        else:
            # Show main window
            self.logger.info("Showing main window")
            self.main_window.show()

        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.critical(f"Error in main loop: {Logger.format_error(e)}")

    def reload_config(self):
        """Reload configuration from file"""
        try:
            self.config.load_config()
            self.logger.info("Configuration reloaded")
            # Update activity tracker settings after reloading config
            self.update_activity_tracker_settings()
            return True
        except Exception as e:
            self.logger.error(f"Error reloading config: {Logger.format_error(e)}")
            return False
            
    def update_ui_for_theme(self):
        """Update UI elements for the current theme"""
        # Update main window
        if hasattr(self, 'main_window'):
            self.main_window.update_ui_for_theme()
            
        # Update mini window if needed
        if hasattr(self, 'mini_window') and hasattr(self.mini_window, 'update_ui_for_theme'):
            self.mini_window.update_ui_for_theme()
            
        # Update settings window if it exists
        if hasattr(self.main_window, '_settings_window') and self.main_window._settings_window:
            self.main_window._settings_window.update_ui_for_theme()
            
        self.logger.info("Updated UI for theme change")
