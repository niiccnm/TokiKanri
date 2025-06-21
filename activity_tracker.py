# activity_tracker.py
import win32api
import win32gui
import win32process
import psutil
from ctypes import windll, Structure, c_ulong, byref, sizeof
import time
from config import Config
from logger import Logger

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_ulong),
        ('dwTime', c_ulong)
    ]

class ActivityTracker:
    """Tracks user activity and active window information"""
    def __init__(self):
        self.config = Config()
        self.logger = Logger()
        self.inactivity_threshold = self.config.get('inactivity_threshold')
        self._initialize_tracking()
        
    def _initialize_tracking(self):
        """Initialize tracking variables"""
        try:
            self.last_mouse_pos = win32api.GetCursorPos()
        except Exception as e:
            # Handle access denied error at startup
            self.logger.warning(f"Could not get cursor position at startup: {Logger.format_error(e)}")
            self.last_mouse_pos = (0, 0)  # Use fallback position
            
        self.last_input_info = LASTINPUTINFO()
        self.last_input_info.cbSize = sizeof(LASTINPUTINFO)
        self.last_activity_time = time.time()
        self.is_active = True
        
        try:
            windll.user32.GetLastInputInfo(byref(self.last_input_info))
        except Exception as e:
            self.logger.warning(f"Could not get last input info at startup: {Logger.format_error(e)}")
        
    def check_activity(self):
        """Check current user activity status"""
        try:
            try:
                current_mouse_pos = win32api.GetCursorPos()
                mouse_moved = current_mouse_pos != self.last_mouse_pos
                self.last_mouse_pos = current_mouse_pos
            except Exception as e:
                self.logger.warning(f"Could not get cursor position: {Logger.format_error(e)}")
                current_mouse_pos = self.last_mouse_pos
                mouse_moved = False
            
            try:
                system_uptime = win32api.GetTickCount()
                windll.user32.GetLastInputInfo(byref(self.last_input_info))
                idle_time = (system_uptime - self.last_input_info.dwTime) / 1000.0
                input_received = idle_time < self.inactivity_threshold
            except Exception as e:
                self.logger.warning(f"Could not get input info: {Logger.format_error(e)}")
                input_received = False
            
            was_active = self.is_active
            self.is_active = mouse_moved or input_received
            
            return was_active != self.is_active
            
        except Exception as e:
            self.logger.error(f"Error checking activity: {Logger.format_error(e)}")
            return False
            
    @staticmethod
    def get_active_window_info():
        """Get information about the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Filter out empty windows or invalid handles
            if hwnd and window_title:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()
                    # print(f"Active window: {window_title} ({process_name})")  # Debug print - REMOVED
                    return process_name
                except Exception as e:
                    # Use a temporary logger instance for static method
                    temp_logger = Logger() 
                    temp_logger.error(f"Error getting process info: {Logger.format_error(e)}")
                    return ""
            return ""
            
        except Exception as e:
            # Use a temporary logger instance for static method
            temp_logger = Logger()
            temp_logger.error(f"Error getting window info: {Logger.format_error(e)}")
            return ""
