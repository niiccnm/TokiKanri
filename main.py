# main.py
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
import os
import time
from program_tracker import ProgramTokiKanri
from logger import Logger
from version import get_version_string

# Constants for ErrorWindow
ERROR_WINDOW_WIDTH = 600
ERROR_WINDOW_HEIGHT = 400
ERROR_WINDOW_TITLE = "TokiKanri Error"
ERROR_WINDOW_BG = 'white'
ERROR_TEXT_FG = 'black'
ERROR_BUTTON_BG = '#007AFF'
ERROR_BUTTON_FG = 'white'
ERROR_BUTTON_TEXT = "Close"

# Constants for requirements check
MIN_PYTHON_VERSION = (3, 6)
REQUIRED_MODULES = ['tkinter', 'win32gui', 'win32process', 'psutil']

# Initialize logger
logger = Logger()

class ErrorWindow:
    """Error display window for application errors"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(ERROR_WINDOW_TITLE)
        self.root.geometry(f"{ERROR_WINDOW_WIDTH}x{ERROR_WINDOW_HEIGHT}")
        self.root.configure(bg=ERROR_WINDOW_BG)
        
        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - ERROR_WINDOW_WIDTH) // 2
        y = (screen_height - ERROR_WINDOW_HEIGHT) // 2
        self.root.geometry(f"{ERROR_WINDOW_WIDTH}x{ERROR_WINDOW_HEIGHT}+{x}+{y}")
        
        # Error text widget
        self.text = tk.Text(self.root, wrap=tk.WORD, bg=ERROR_WINDOW_BG, fg=ERROR_TEXT_FG)
        self.text.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Close button
        self.close_btn = tk.Button(
            self.root,
            text=ERROR_BUTTON_TEXT,
            command=self.root.destroy,
            bg=ERROR_BUTTON_BG,
            fg=ERROR_BUTTON_FG,
            relief='flat',
            padx=20,
            pady=10
        )
        self.close_btn.pack(pady=20)
    
    def show_error(self, error_message):
        """Display error message and show window"""
        self.text.insert('1.0', error_message)
        self.root.mainloop()

# Removed write_to_log function, now using Logger

def check_requirements():
    """Check Python version and required modules"""
    try:
        # Check Python version
        if sys.version_info < MIN_PYTHON_VERSION:
            return False, f"Python {'.'.join(map(str, MIN_PYTHON_VERSION))} or higher is required"
        
        # Check required modules
        missing_modules = []
        
        for module in REQUIRED_MODULES:
            try:
                __import__(module)
            except ImportError:
                missing_modules.append(module)
        
        if missing_modules:
            return False, f"Missing required modules: {', '.join(missing_modules)}"
            
        return True, None
        
    except Exception as e:
        return False, f"Error checking requirements: {str(e)}"

def main():
    """Main application entry point"""
    try:
        logger.info(f"Starting {get_version_string()}")
        
        # Check requirements
        requirements_met, error_message = check_requirements()
        if not requirements_met:
            raise RuntimeError(error_message)
        
        # Create and run program tracker
        logger.info("Creating program tracker instance")
        app = ProgramTokiKanri()
        
        logger.info("Running program")
        app.run()
        
        return 0
        
    except Exception as e:
        error_msg = f"""TokiKanri encountered an error:

Error Type: {type(e).__name__}
Error Message: {str(e)}

Full Traceback:
{traceback.format_exc()}

System Information:
Python Version: {sys.version}
Executable Path: {sys.executable}
Working Directory: {os.getcwd()}

Please report this error to the developer."""
        
        logger.error(f"Error occurred:\n{error_msg}")
        
        # Show error window
        error_window = ErrorWindow()
        error_window.show_error(error_msg)
        
        return 1

if __name__ == "__main__":
    try:
        print(f"{get_version_string()}")
        logger.info("Starting TokiKanri...")
        sys.exit(main())
    except Exception as e:
        logger.critical(f"Critical error: {Logger.format_error(e)}")
        input("Press Enter to exit...")
        sys.exit(1)
