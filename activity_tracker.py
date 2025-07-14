# activity_tracker.py
import win32api
import win32gui
import win32process
import psutil
from ctypes import windll, Structure, c_ulong, byref, sizeof
import time
import asyncio
from config import Config
from logger import Logger
import concurrent.futures
import threading
import gc
import weakref

# Import Windows Media Control API
try:
    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
    MEDIA_API_AVAILABLE = True
except ImportError:
    MEDIA_API_AVAILABLE = False

# Import Windows toast notification
# We use a try/except block so the code still runs if windows-toasts is not installed
try:
    # This is properly handled by the try/except, even if linter flags it as missing
    from windows_toasts import WindowsToaster, Toast
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_ulong),
        ('dwTime', c_ulong)
    ]

class ActivityTracker:
    """Tracks user activity and active window information."""
    
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.inactivity_threshold = self.config.get('inactivity_threshold')
        self.media_mode_enabled = self.config.get('media_mode_enabled', False)
        self.media_programs = self.config.get('media_programs', []) or []  # Ensure it's always a list
        self.require_media_playback = self.config.get('require_media_playback', True)
        # Convert class variable to instance variable
        self._last_logged_process = ""
        self._initialize_tracking()
        # Log media configuration at startup if media mode is enabled
        if self.media_mode_enabled:
            self.log_media_programs()
        # Track previous window info to reduce redundant logging
        self.previous_window_info = ""
        self.previous_media_status = False
        self.is_media_playing = False
        
        # API status tracking
        self.media_api_status = "Unknown"  # Can be "Unknown", "Available", "Unresponsive"
        self.last_api_failure_time = 0
        self.api_failure_count = 0
        self.api_notification_shown = False
        
        # Initialize toast notifier if available
        if TOAST_AVAILABLE:
            self.toaster = WindowsToaster("TokiKanri")
        else:
            self.toaster = None
        
        # Track event loops and async resources
        self._current_media_task = None
        self._event_loop = None
        self._executor = None
        
    def log_media_programs(self):
        """Log the current media programs list for debugging.
        
        This method is called only when settings change.
        """
        # This method is now intended to be called only when settings change
        if self.media_programs:
            self.logger.info(f"Media programs configured: {', '.join(self.media_programs)}")
            self.logger.info(f"Media mode enabled: {self.media_mode_enabled}")
            self.logger.info(f"Require media playback: {self.require_media_playback}")
            if MEDIA_API_AVAILABLE:
                self.logger.info("Windows Media Control API is available")
                self.media_api_status = "Available"
            else:
                self.logger.warning("Windows Media Control API is not available")
                self.media_api_status = "Unavailable"
        else:
            self.logger.warning("No media programs configured in settings")
        
    def _initialize_tracking(self):
        """Initialize tracking variables."""
        try:
            self.last_mouse_pos = win32api.GetCursorPos()
            self.last_input_info = LASTINPUTINFO()
            self.last_input_info.cbSize = sizeof(self.last_input_info)
            windll.user32.GetLastInputInfo(byref(self.last_input_info))
            self.is_active = True  # Assume active at start
        except Exception as e:
            self.logger.error(f"Error initializing tracking: {Logger.format_error(e)}")
            self.is_active = False
            
    def _ensure_clean_event_loop(self):
        """Ensure we have a clean event loop for async operations.
        
        Returns:
            asyncio.AbstractEventLoop: A clean event loop for async operations
        """
        try:
            # Try to get the current event loop
            try:
                loop = asyncio.get_event_loop()
                # If the loop is closed, create a new one
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                # If no event loop exists, create a new one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Keep track of the current event loop
            self._event_loop = loop
            return loop
        except Exception as e:
            self.logger.error(f"Error ensuring clean event loop: {Logger.format_error(e)}")
            # Create a new event loop as a last resort
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._event_loop = loop
            return loop

    def show_api_notification(self, message):
        """Show a notification about API status.
        
        Args:
            message (str): The notification message to display
        """
        # Only show notification if we haven't shown one recently (within 5 minutes)
        current_time = time.time()
        if current_time - self.last_api_failure_time > 300:  # 5 minutes
            self.api_notification_shown = True
            self.last_api_failure_time = current_time
            
            # Show Windows toast notification if available
            if TOAST_AVAILABLE and self.toaster is not None:
                threading.Thread(
                    target=self._show_toast_notification,
                    args=(message,),
                    daemon=True
                ).start()
                
    def _show_toast_notification(self, message):
        """Show Windows toast notification in a separate thread.
        
        Args:
            message (str): The message to display in the toast notification
        """
        try:
            # Only attempt to show toast if toaster is not None
            if self.toaster is not None:
                toast = Toast()
                toast.text_fields = ["TokiKanri Media Mode", message]
                self.toaster.show_toast(toast)
        except Exception as e:
            self.logger.error(f"Error showing toast notification: {Logger.format_error(e)}")

    async def _get_media_info_with_timeout(self, timeout=1.0):
        """Get media info with a timeout to prevent hanging.
        
        Args:
            timeout (float, optional): Timeout in seconds. Defaults to 1.0.
            
        Returns:
            dict or None: Media information if available, None otherwise
        """
        try:
            # Create a task for the media info request
            task = asyncio.create_task(self.get_media_info())
            
            # Keep a reference to cancel it if needed
            self._current_media_task = task
            
            # Wait for the task to complete with a timeout
            result = await asyncio.wait_for(task, timeout=timeout)
            
            # If we get here, API is responsive
            if self.media_api_status == "Unresponsive":
                self.media_api_status = "Available"
                self.api_failure_count = 0
                self.show_api_notification("Windows Media Control API is now responsive again")
                
            return result
            
        except asyncio.TimeoutError:
            self.logger.warning(f"Media API call timed out after {timeout} seconds")
            
            # Update API status
            self.media_api_status = "Unresponsive"
            self.api_failure_count += 1
            
            # Show notification if this is a recurring issue (3 failures)
            if self.api_failure_count >= 3 and not self.api_notification_shown:
                self.show_api_notification("Windows Media Control API is unresponsive. Media detection may not work properly.")
                
            return None
        except Exception as e:
            self.logger.error(f"Error in media API call: {Logger.format_error(e)}")
            return None
        finally:
            # Clean up the task if it's still running
            if self._current_media_task and not self._current_media_task.done():
                self._current_media_task.cancel()
                try:
                    # Try to await the canceled task to properly clean up
                    await asyncio.wait_for(self._current_media_task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                except Exception:
                    pass
            self._current_media_task = None
            
    async def get_media_info(self):
        """Get information about currently playing media using Windows Media Control API.
        
        Returns:
            dict or None: Media information if available, None otherwise
        """
        if not MEDIA_API_AVAILABLE:
            self.logger.debug("Windows Media Control API not available")
            return None
            
        sessions = None
        current_session = None
            
        try:
            sessions = await MediaManager.request_async()
            current_session = sessions.get_current_session()
            
            if current_session:
                info = await current_session.try_get_media_properties_async()
                playback_info = current_session.get_playback_info()
                
                # Add null check for playback_info and playback_status
                status = "Unknown"
                if playback_info and hasattr(playback_info, 'playback_status'):
                    if playback_info.playback_status:
                        status = playback_info.playback_status.name  # Playing, Paused, Stopped
                
                media_info = {
                    'title': info.title if info else "",
                    'artist': info.artist if info else "",
                    'status': status
                }
                
                self.logger.debug(f"Media info: {media_info}")
                return media_info
            else:
                self.logger.debug("No active media session found")
                return None
        except Exception as e:
            self.logger.error(f"Error getting media info: {Logger.format_error(e)}")
            return None
        finally:
            # Explicitly clear references to help garbage collection
            # These objects come from COM/WinRT and need explicit cleanup
            if current_session:
                current_session = None
            if sessions:
                sessions = None
            # Force a garbage collection cycle to help clean up COM objects
            gc.collect()
            
    def check_media_playback(self):
        """Check if media is currently playing
        
        Returns
        -------
        tuple
            (is_playing, media_info) where is_playing is a boolean and media_info is a dict
        """
        if not self.media_mode_enabled or not MEDIA_API_AVAILABLE:
            return False, None
            
        try:
            # Use a thread-safe approach with timeout to prevent hanging
            media_info = None
            
            # Create executor only when needed and reuse it
            if self._executor is None or self._executor._shutdown:
                self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            
            # Use a finite timeout to avoid blocking forever
            executor = self._executor
            future = None
            
            try:
                # Create a clean event loop for each check to avoid resource leaks
                def run_async_task():
                    # Set up a clean event loop
                    loop = self._ensure_clean_event_loop()
                    try:
                        # Run the async task in this thread's event loop
                        return loop.run_until_complete(self._get_media_info_with_timeout(timeout=1.5))
                    finally:
                        # Don't close the loop as it may be reused
                        pass
                
                # Submit the task to the executor
                future = executor.submit(run_async_task)
                
                # Wait for the future to complete with a timeout
                media_info = future.result(timeout=2.0)
                
            except concurrent.futures.TimeoutError:
                self.logger.warning("Media playback check timed out")
                
                # Update API status
                self.media_api_status = "Unresponsive"
                self.api_failure_count += 1
                
                # Show notification if this is a recurring issue (3 failures)
                if self.api_failure_count >= 3 and not self.api_notification_shown:
                    self.show_api_notification("Windows Media Control API is unresponsive. Media detection may not work properly.")
                    
                return False, None
                
            except Exception as e:
                self.logger.error(f"Error in media playback thread: {Logger.format_error(e)}")
                return False, None
                
            finally:
                # Cancel the future if it's still running to prevent lingering threads
                if future and not future.done():
                    future.cancel()
            
            if media_info and media_info.get('status', '').upper() == 'PLAYING':
                self.is_media_playing = True
                self.logger.debug(f"Media is playing: {media_info.get('title', 'Unknown')} - {media_info.get('artist', 'Unknown')}")
                return True, media_info
            else:
                # When media is not playing, immediately update the status
                was_playing = self.is_media_playing
                self.is_media_playing = False
                if was_playing:
                    self.logger.info(f"Media stopped playing. Status: {media_info.get('status', 'Unknown') if media_info else 'No media info'}")
                elif media_info:
                    self.logger.debug(f"Media is not playing. Status: {media_info.get('status', 'Unknown')}")
                return False, media_info
        except Exception as e:
            self.logger.error(f"Error checking media playback: {Logger.format_error(e)}")
            return False, None
            
    def is_media_program(self, process_name):
        """Check if the given process is a media program
        
        Parameters
        ----------
        process_name : str
            The process name to check
            
        Returns
        -------
        bool
            True if the process is a media program, False otherwise
        """
        if not process_name:
            self.logger.debug("No process name provided")
            return False
            
        if not self.media_mode_enabled:
            self.logger.debug("Media mode is disabled")
            return False
            
        # Only log when process_name is different from previous check
        if process_name != self.previous_window_info:
            self.logger.debug(f"Checking if '{process_name}' is in media programs list: {self.media_programs}")
        
        try:
            process_lower = process_name.lower()
            for prog in self.media_programs:
                try:
                    prog_lower = prog.lower()
                    # Only log detailed comparison for new window checks
                    if process_name != self.previous_window_info:
                        self.logger.debug(f"Comparing '{process_lower}' with '{prog_lower}'")
                    if prog_lower == process_lower:
                        # Only log match if it's a new match
                        if process_name != self.previous_window_info or not self.previous_media_status:
                            self.logger.info(f"Media program match: '{process_name}' matches '{prog}'")
                        return True
                except UnicodeError:
                    # Handle Unicode errors in program names
                    self.logger.warning(f"Unicode error when comparing with program: {prog}")
                    # Try with safe representation
                    try:
                        safe_prog = prog.encode('utf-8', errors='replace').decode('utf-8', errors='replace').lower()
                        safe_process = process_name.encode('utf-8', errors='replace').decode('utf-8', errors='replace').lower()
                        if safe_prog == safe_process:
                            # Only log match if it's a new match
                            if process_name != self.previous_window_info or not self.previous_media_status:
                                self.logger.info(f"Media program match (safe comparison): '{process_name}' matches '{prog}'")
                            return True
                    except Exception as e:
                        self.logger.error(f"Failed to compare process names: {Logger.format_error(e)}")
        except UnicodeError:
            self.logger.warning(f"Unicode error when processing: {process_name}")
            return False
                
        # Only log non-match for new window checks
        if process_name != self.previous_window_info:
            self.logger.debug(f"'{process_name}' is not in the media programs list")
        return False
        
    def check_activity(self):
        """Check current user activity status
        
        Returns:
            bool: True if activity state changed, False otherwise
        """
        try:
            # Get the current active window info
            current_window_info = self.get_active_window_info()
            
            # Store previous active state to detect changes
            was_active = self.is_active
            
            # Check if we're in media mode and the current program is a media program
            is_media_program = False
            if current_window_info:
                is_media_program = self.is_media_program(current_window_info)
            
            try:
                # Get mouse position to check for activity
                try:
                    current_mouse_pos = win32api.GetCursorPos()
                    mouse_moved = current_mouse_pos != self.last_mouse_pos
                    self.last_mouse_pos = current_mouse_pos
                except Exception as e:
                    self.logger.warning(f"Could not get cursor position: {Logger.format_error(e)}")
                    current_mouse_pos = self.last_mouse_pos
                    mouse_moved = False
                
                # Check for user input
                try:
                    system_uptime = win32api.GetTickCount()
                    windll.user32.GetLastInputInfo(byref(self.last_input_info))
                    idle_time = (system_uptime - self.last_input_info.dwTime) / 1000.0
                    input_received = idle_time < self.inactivity_threshold
                except Exception as e:
                    self.logger.warning(f"Could not get input info: {Logger.format_error(e)}")
                    input_received = False
                
                # If we're in media mode and this is a media program
                if is_media_program:
                    # Get media info for display purposes if API is available
                    media_info = None
                    is_playing = False
                    if MEDIA_API_AVAILABLE:
                        try:
                            is_playing, media_info = self.check_media_playback()
                        except Exception as e:
                            self.logger.error(f"Error checking media playback: {Logger.format_error(e)}")
                            is_playing = False
                            media_info = None
                    
                    # Ensure media_info is not None to prevent attribute errors
                    if media_info is None:
                        media_info = {'title': 'Unknown', 'artist': 'Unknown', 'status': 'Unknown'}
                    
                    # Format media info for display
                    title = media_info.get('title', 'Unknown')
                    artist = media_info.get('artist', 'Unknown')
                    status = media_info.get('status', 'Unknown')
                    
                    # Check if we need to verify media playback
                    if self.require_media_playback and MEDIA_API_AVAILABLE:
                        if is_playing:
                            self.is_active = True
                            if current_window_info != self.previous_window_info or self.previous_media_status != is_media_program:
                                self.logger.info(f"Media is playing in {current_window_info} - Now playing: \"{title} - {artist}\"")
                            if not was_active:
                                self.logger.info(f"Media mode activated tracking for {current_window_info} - Now playing: \"{title} - {artist}\"")
                        else:
                            # If media is not playing, immediately set to inactive
                            self.is_active = False
                            if was_active:
                                self.logger.info(f"Media stopped playing in {current_window_info} - Status: {status}")
                            elif current_window_info != self.previous_window_info or self.previous_media_status != is_media_program:
                                self.logger.info(f"Media is not playing in {current_window_info} - Status: {status}")
                    else:
                        # If we don't need to verify media playback or API isn't available, consider active
                        # regardless of playback status
                        self.is_active = True
                        
                        # Format media info string if available
                        if title and artist and title != 'Unknown' and artist != 'Unknown':
                            media_str = f" - Media info: \"{title} - {artist}\" ({status})"
                        elif status != 'Unknown':
                            media_str = f" - Media status: {status}"
                        else:
                            media_str = ""
                        
                        if current_window_info != self.previous_window_info or self.previous_media_status != is_media_program:
                            self.logger.info(f"Media mode active for {current_window_info}{media_str} - Activity status: {self.is_active}")
                        if not was_active:
                            self.logger.info(f"Media mode activated tracking for {current_window_info}{media_str}")
                else:
                    self.is_active = mouse_moved or input_received
                    if current_window_info and (current_window_info != self.previous_window_info or was_active != self.is_active):
                        self.logger.debug(f"Regular activity check for {current_window_info}: mouse_moved={mouse_moved}, input_received={input_received}, is_active={self.is_active}")
                
                # Update previous window info and media status for next comparison
                self.previous_window_info = current_window_info
                self.previous_media_status = is_media_program
                
                # Return True if activity state changed, False otherwise
                return was_active != self.is_active
                
            except Exception as e:
                self.logger.error(f"Error in activity check logic: {Logger.format_error(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking activity: {Logger.format_error(e)}")
            return False
            
    def get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window title with proper Unicode handling
            try:
                window_title = win32gui.GetWindowText(hwnd)
            except UnicodeError:
                # Create a temporary logger for error reporting
                temp_logger = Logger()
                temp_logger.warning("Unicode error when getting window title")
                # Use a safe representation
                window_title = ""
            
            # Filter out empty windows or invalid handles
            if hwnd and window_title:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    
                    try:
                        process_name = process.name()
                        if not process_name:
                            return ""
                            
                        # Only log when process changes
                        if process_name != self._last_logged_process:
                            self.logger.debug(f"Active window: {window_title} ({process_name})")
                            self._last_logged_process = process_name
                            
                        return process_name
                    except UnicodeError:
                        # Create a temporary logger for error reporting
                        temp_logger = Logger()
                        temp_logger.warning("Unicode error when getting process name")
                        # Use a safe representation
                        try:
                            safe_name = process.name().encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                            return safe_name
                        except Exception as e:
                            temp_logger.error(f"Failed to get safe process name: {Logger.format_error(e)}")
                            return ""
                except Exception as e:
                    # Create a temporary logger for error reporting
                    temp_logger = Logger()
                    temp_logger.warning(f"Error getting process info: {Logger.format_error(e)}")
                    return ""
            return ""
        except Exception as e:
            # Create a temporary logger for error reporting
            temp_logger = Logger()
            temp_logger.error(f"Error getting window info: {Logger.format_error(e)}")
            return ""
            
    def cleanup_resources(self):
        """Explicitly clean up resources when the tracker is no longer needed"""
        try:
            # Cancel any running media task
            if self._current_media_task and not self._current_media_task.done():
                self._current_media_task.cancel()
            self._current_media_task = None
            
            # Shutdown the executor if it exists
            if self._executor:
                self._executor.shutdown(wait=False)
            self._executor = None
            
            # Clear references to help garbage collection
            self.previous_window_info = None
            self.current_window_info = None
            
            # Force a garbage collection cycle
            gc.collect()
        except Exception as e:
            self.logger.error(f"Error during resource cleanup: {Logger.format_error(e)}")
