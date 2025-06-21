# window_selector.py
import win32gui
import win32process
import psutil

class WindowSelector:
    """Handles window selection and tracking"""
    def __init__(self, max_programs):
        self.max_programs = max_programs
        self.selecting_window = False
        
    def start_selection(self):
        """Start window selection process"""
        self.selecting_window = True
        return True
        
    def stop_selection(self):
        """Stop window selection process"""
        self.selecting_window = False
        
    def check_selected_window(self, tracked_programs):
        """Check the foreground window and decide whether it should be added to tracking.

        Parameters
        ----------
        tracked_programs : dict
            Dictionary of currently tracked programs.

        Returns
        -------
        tuple | None
            (process_name, is_new)
            process_name (str): Executable name of the foreground window.
            is_new (bool): True if the program is not yet tracked and can be added,
                           False if it is already being tracked.
            None is returned when no valid window is detected or when the max
            program limit has been reached.
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)

            # Exclude TokiKanri's own windows and empty titles
            our_app_titles = ["TokiKanri", "TokiKanri Mini"]
            if hwnd and window_title and window_title not in our_app_titles:
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name()

                    # Already tracked – inform caller
                    if process_name in tracked_programs:
                        return (process_name, False)

                    # New program – ensure we have capacity
                    if len(tracked_programs) < self.max_programs:
                        return (process_name, True)
                    else:
                        # Max programs limit reached
                        return (None, 'MAX_REACHED')

                except Exception as e:
                    print(f"Error getting process info: {e}")
                    return (None, 'ERROR') # Indicate an error occurred

            return (None, 'NO_WINDOW') # Indicate no valid window found

        except Exception as e:
            print(f"Error during window selection: {e}")
            return None
