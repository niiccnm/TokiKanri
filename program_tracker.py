# program_tracker.py
import tkinter as tk
import threading
import queue
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
from update_checker import check_for_updates

class ThreadManager:
    """Manages background threads for operations that would otherwise block the GUI."""
    def __init__(self, logger):
        self.logger = logger
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_tasks, daemon=True)
        self.worker_thread.start()
        
    def _process_tasks(self):
        """Worker thread that processes tasks from the queue."""
        while self.is_running:
            try:
                task = self.task_queue.get(timeout=0.5)
                if task is None:  # Shutdown signal
                    break
                    
                func, args, kwargs, callback, error_callback = task
                try:
                    result = func(*args, **kwargs)
                    if callback:
                        # Put the callback and result in the result queue for execution in the main thread
                        self.result_queue.put((callback, (result,), {}))
                except Exception as e:
                    self.logger.error(f"Error in background thread: {Logger.format_error(e)}")
                    if error_callback:
                        self.result_queue.put((error_callback, (e,), {}))
                        
                self.task_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                self.logger.error(f"Error in thread manager: {Logger.format_error(e)}")
                
    def process_results(self):
        """Process any results and invoke callbacks in the main thread."""
        try:
            while not self.result_queue.empty():
                callback, args, kwargs = self.result_queue.get_nowait()
                callback(*args, **kwargs)
                self.result_queue.task_done()
        except Exception as e:
            self.logger.error(f"Error processing thread results: {Logger.format_error(e)}")
            
    def submit_task(self, func, *args, callback=None, error_callback=None, **kwargs):
        """Submit a task to be executed in a background thread.
        
        Args:
            func (callable): The function to execute
            *args: Arguments to pass to the function
            callback (callable, optional): Function to call with the result when the task completes
            error_callback (callable, optional): Function to call with the exception if the task fails
            **kwargs: Keyword arguments to pass to the function
        """
        self.task_queue.put((func, args, kwargs, callback, error_callback))
        
    def shutdown(self):
        """Shutdown the thread manager."""
        self.is_running = False
        self.task_queue.put(None)  # Signal to exit
        if self.worker_thread.is_alive():
            self.worker_thread.join(1.0)  # Wait for worker thread with timeout

class ProgramTokiKanri:
    """Main program tracker class."""
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
        
        # Initialize thread manager
        self.thread_manager = ThreadManager(self.logger)
        
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
        
        # Ensure proper mousewheel bindings
        self.main_window.update_program_bindings()
        
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
        
        # Start thread result processing timer
        self._process_thread_results()
        
        # Check for updates in background thread after UI is initialized
        self.thread_manager.submit_task(
            self._check_for_updates,
            show_dialog=True,
            callback=self._on_update_check_complete,
            error_callback=self._on_update_check_error
        )
        
    def _check_for_updates(self, show_dialog=True):
        """Check for updates in background thread.
        
        Args:
            show_dialog (bool): Whether to show a dialog if updates are available
        
        Returns:
            bool: True if updates are available, False otherwise
        """
        self.logger.info("Checking for application updates...")
        return check_for_updates(silent=True, show_dialog=show_dialog)
        
    def _on_update_check_complete(self, updates_available):
        """Callback when update check completes.
        
        Args:
            updates_available (bool): Whether updates are available
        """
        if updates_available:
            self.logger.info("Updates are available")
        else:
            self.logger.info("No updates available")
            
    def _on_update_check_error(self, error):
        """Callback when update check fails.
        
        Args:
            error (Exception): The error that occurred
        """
        self.logger.error(f"Error checking for updates: {Logger.format_error(error)}")
        
    def check_for_updates_manually(self, parent=None):
        """Check for updates and show results dialog.
        
        This method is called from the settings window.
        
        Args:
            parent (tk.Widget, optional): Parent widget for dialog. Defaults to None.
        """
        self.thread_manager.submit_task(
            self._check_for_updates,
            show_dialog=True,
            callback=lambda result: self._handle_manual_update_result(result, parent),
            error_callback=lambda error: self._handle_manual_update_error(error, parent)
        )
        
    def _handle_manual_update_result(self, updates_available, parent=None):
        """Handle the result of a manual update check.
        
        Args:
            updates_available (bool): Whether updates are available
            parent (tk.Widget, optional): Parent widget for dialog. Defaults to None.
        """
        if not updates_available:
            messagebox.showinfo(
                "No Updates Available",
                f"You are using the latest version ({get_version_string()}).",
                parent=parent
            )
            
    def _handle_manual_update_error(self, error, parent=None):
        """Handle errors during manual update check.
        
        Args:
            error (Exception): The error that occurred
            parent (tk.Widget, optional): Parent widget for dialog. Defaults to None.
        """
        self.logger.error(f"Error checking for updates: {Logger.format_error(error)}")
        messagebox.showerror(
            "Update Check Failed",
            f"Failed to check for updates: {str(error)}",
            parent=parent
        )
        
    def _start_tracking_loops(self):
        """Start timer and activity tracking loops"""
        self.update_timer()
        self.check_activity()
        
    def _process_thread_results(self):
        """Process results from background threads"""
        if self.is_shutting_down:
            return
            
        try:
            self.thread_manager.process_results()
        except Exception as e:
            self.logger.error(f"Error processing thread results: {Logger.format_error(e)}")
            
        # Schedule next processing
        if not self.is_shutting_down:
            self.main_window.root.after(50, self._process_thread_results)  # Process every 50ms
        
    def update_timer(self):
        """Main timer update loop"""
        if self.is_shutting_down:
            return
            
        # Run active window detection in background thread
        if not self.window_selector.selecting_window:
            self.thread_manager.submit_task(
                self._check_active_window,
                callback=self._on_active_window_check_complete,
                error_callback=self._on_active_window_check_error
            )
                
        # Schedule next timer update
        if not self.is_shutting_down:
            self.main_window.root.after(1000, self.update_timer) # Update timer every 1 second
            
    def _check_active_window(self):
        """Check active window and return time tracking information (runs in background thread)"""
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        current_process = self.activity_tracker.get_active_window_info()
        program_switched = current_process != self.last_program
        
        return {
            'current_time': current_time,
            'time_delta': time_delta,
            'current_process': current_process,
            'program_switched': program_switched
        }
        
    def _on_active_window_check_complete(self, result):
        """Handle active window check completion (runs in main thread)"""
        self.last_update_time = result['current_time']
        time_delta = result['time_delta']
        current_process = result['current_process']
        program_switched = result['program_switched']
        
        # Track if any program time has been updated
        time_updated = False
            
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
        current_time = time.time()
        if current_time - self.last_save_time >= (self.config.get('save_interval') or 60):  # Default to 60 seconds if None
            # Save data in background thread to prevent UI blocking
            self.thread_manager.submit_task(
                self.data_manager.save_data,
                error_callback=lambda e: self.logger.error(f"Error saving data: {Logger.format_error(e)}")
            )
            self.last_save_time = current_time
            
    def _on_active_window_check_error(self, error):
        """Handle active window check error (runs in main thread)"""
        self.logger.error(f"Error in update_timer: {Logger.format_error(error)}")
            
    def check_activity(self):
        """Activity checking loop"""
        if self.is_shutting_down:
            return
            
        # Run activity check in background thread to prevent UI freezing
        self.thread_manager.submit_task(
            self.activity_tracker.check_activity,
            callback=self._on_activity_check_complete,
            error_callback=self._on_activity_check_error
        )
            
        if not self.is_shutting_down:
            # Check less frequently to reduce memory usage while still maintaining good responsiveness
            self.main_window.root.after(200, self.check_activity) # Reduced polling frequency to prevent memory leaks
            
    def _on_activity_check_complete(self, activity_changed):
        """Handle activity check completion"""
        if activity_changed:
            self._handle_activity_change()
            # Reorder widgets to reflect new activity state without recreating
            self.main_window.program_gui.reorder_widgets(
                self.data_manager.get_current_times(),
                self.data_manager.currently_tracking
            )
            # Immediately update displays to reflect the activity change
            self._update_displays()
            
    def _on_activity_check_error(self, error):
        """Handle activity check error"""
        self.logger.error(f"Error in activity check: {Logger.format_error(error)}")
    
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
        
        # Ensure proper mousewheel bindings are maintained
        self.main_window.update_program_bindings()
        
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
            # Run window selection check in background thread
            self.thread_manager.submit_task(
                self.window_selector.check_selected_window,
                self.data_manager.tracked_programs,
                callback=self._on_window_selection_complete,
                error_callback=self._on_window_selection_error
            )
            
    def _on_window_selection_complete(self, result):
        """Handle window selection completion"""
        if not result:
            # Continue checking if no result yet
            self.main_window.root.after(100, self.check_selected_window)
            return
            
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
        
        # Ensure proper mousewheel bindings
        self.main_window.update_program_bindings()
        
        # Update status
        self._update_status(self.activity_tracker.is_active, process_name)
        
        # Save data
        self.thread_manager.submit_task(
            self.data_manager.save_data,
            error_callback=lambda e: self.logger.error(f"Error saving data: {Logger.format_error(e)}")
        )
        
        # Reset selection state
        self.window_selector.selecting_window = False
        self.main_window.update_select_button(False)
        self.main_window.root.deiconify()  # Restore the window
            
    def _on_window_selection_error(self, error):
        """Handle window selection error"""
        self.logger.error(f"Error in window selection: {Logger.format_error(error)}")
        messagebox.showerror("Selection Error", "An error occurred during window selection. Please try again.")
        self.window_selector.selecting_window = False
        self.main_window.update_select_button(False)
        self.main_window.root.deiconify()
        self._update_status(False, None)
            
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
            # Show processing indicator
            self.main_window.update_status("Exporting data...", is_active=False)
            
            # Run export in background thread
            self.thread_manager.submit_task(
                self.data_manager.export_data,
                filepath,
                callback=self._on_export_data_complete,
                error_callback=self._on_export_data_error
            )
    
    def _on_export_data_complete(self, success):
        """Handle export data completion"""
        if success:
            messagebox.showinfo("Export Successful", "Data exported successfully")
        else:
            messagebox.showerror("Export Failed", "Unable to export data. Check logs for details.")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)
            
    def _on_export_data_error(self, error):
        """Handle export data error"""
        self.logger.error(f"Error exporting data: {Logger.format_error(error)}")
        messagebox.showerror("Export Failed", f"Error exporting data: {str(error)}")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)

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
            
            # Show processing indicator
            self.main_window.update_status("Importing data...", is_active=False)
            
            # Run import in background thread
            self.thread_manager.submit_task(
                self.data_manager.import_data,
                filepath,
                merge=merge,
                callback=self._on_import_data_complete,
                error_callback=self._on_import_data_error
            )
    
    def _on_import_data_complete(self, success):
        """Handle import data completion"""
        if success:
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
            messagebox.showinfo("Import Successful", "Data imported successfully")
        else:
            messagebox.showerror("Import Failed", "Unable to import data. Check logs for details.")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)
            
    def _on_import_data_error(self, error):
        """Handle import data error"""
        self.logger.error(f"Error importing data: {Logger.format_error(error)}")
        messagebox.showerror("Import Failed", f"Error importing data: {str(error)}")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)

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
            # Show processing indicator
            self.main_window.update_status("Exporting configuration...", is_active=False)
            
            # Run export in background thread
            self.thread_manager.submit_task(
                self.config.export_config,
                filepath,
                callback=self._on_export_config_complete,
                error_callback=self._on_export_config_error
            )
    
    def _on_export_config_complete(self, success):
        """Handle export config completion"""
        if success:
            messagebox.showinfo("Export Successful", "Configuration exported successfully")
        else:
            messagebox.showerror("Export Failed", "Unable to export configuration. Check logs for details.")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)
            
    def _on_export_config_error(self, error):
        """Handle export config error"""
        self.logger.error(f"Error exporting configuration: {Logger.format_error(error)}")
        messagebox.showerror("Export Failed", f"Error exporting configuration: {str(error)}")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)

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
            # Show processing indicator
            self.main_window.update_status("Importing configuration...", is_active=False)
            
            # Run import in background thread
            self.thread_manager.submit_task(
                self.config.import_config,
                filepath,
                callback=self._on_import_config_complete,
                error_callback=self._on_import_config_error
            )
    
    def _on_import_config_complete(self, success):
        """Handle import config completion"""
        if success:
            messagebox.showinfo("Import Successful", "Configuration imported successfully")
            # Re-initialize settings window to reflect new config
            if hasattr(self.main_window, '_settings_window') and self.main_window._settings_window.winfo_exists():
                self.main_window._settings_window.destroy() # Destroy old instance
                del self.main_window._settings_window # Remove reference
            self.main_window._open_settings() # Open new instance with updated config
            # Update max_programs in window_selector
            self.window_selector.max_programs = self.config.get('max_programs')
        else:
            messagebox.showerror("Import Failed", "Unable to import configuration. Check logs for details.")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)
            
    def _on_import_config_error(self, error):
        """Handle import config error"""
        self.logger.error(f"Error importing configuration: {Logger.format_error(error)}")
        messagebox.showerror("Import Failed", f"Error importing configuration: {str(error)}")
        self._update_status(self.activity_tracker.is_active, self.data_manager.currently_tracking)

    def reset_all_timers(self):
        """Reset all program timers"""
        # Reset all times in data manager
        self.data_manager.reset_all_programs()
        
        # Update UI with all programs at 0 time
        self.main_window.program_gui.create_program_widgets(
            self.data_manager.tracked_programs,
            self.data_manager.get_current_times(),
            self.data_manager.currently_tracking
        )
        
        # Ensure proper mousewheel bindings
        self.main_window.update_program_bindings()
        
        # Update total time to 0
        self.main_window.update_total_time("00:00")
        
    def remove_program(self, program):
        """Remove a program from tracking"""
        # Remove from data manager
        self.data_manager.remove_program(program)
        
        # Update UI to remove the program
        self.main_window.program_gui.create_program_widgets(
            self.data_manager.tracked_programs,
            self.data_manager.get_current_times(),
            self.data_manager.currently_tracking
        )
        
        # Ensure proper mousewheel bindings
        self.main_window.update_program_bindings()
        
        # Update total time
        self._update_displays()
        
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
            # Clear all programs in data manager
            self.data_manager.remove_all_programs()
            
            # Update UI to remove all programs
            self.main_window.program_gui.create_program_widgets(
                self.data_manager.tracked_programs,
                self.data_manager.get_current_times(),
                self.data_manager.currently_tracking
            )
            
            # Ensure proper mousewheel bindings
            self.main_window.update_program_bindings()
            
            # Update total time to 0
            self.main_window.update_total_time("00:00")
            self._update_status(False, None)  # Reset status
        
    def quit_app(self):
        """Clean shutdown of application"""
        try:
            self.is_shutting_down = True
            
            # Save data synchronously before shutdown
            self.data_manager.save_data()
            
            # Clean up Windows Media API resources before shutdown
            if hasattr(self, 'activity_tracker'):
                self.activity_tracker.cleanup_resources()
                
            # Shutdown thread manager
            if hasattr(self, 'thread_manager'):
                self.thread_manager.shutdown()
                
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
