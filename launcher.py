# launcher.py
import os
import sys
import traceback
import tkinter as tk
import time
from logger import Logger

# Initialize logger
logger = Logger()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 6):
        return False, "Python 3.6 or higher is required"
    return True, None

def check_required_modules():
    """Check if required modules are available"""
    required_modules = [
        'tkinter',
        'win32gui',
        'win32process',
        'psutil',
        'PIL',  # For system tray icon
        'pystray'  # For system tray functionality
    ]
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        return False, f"Missing required modules: {', '.join(missing_modules)}"
    return True, None

def main():
    try:
        logger.info("Starting TokiKanri launcher")
        
        # Check Python version
        version_ok, version_error = check_python_version()
        if not version_ok:
            raise RuntimeError(version_error)
        
        # Check required modules
        modules_ok, modules_error = check_required_modules()
        if not modules_ok:
            raise RuntimeError(modules_error)
        
        # Import main module
        logger.info("Importing program_tracker")
        from program_tracker import ProgramTokiKanri
        
        logger.info("Creating program instance")
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

class ErrorWindow:
    """Error display window"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TokiKanri Error")
        self.root.geometry("600x400")
        self.root.configure(bg='white')
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 600) // 2
        y = (screen_height - 400) // 2
        self.root.geometry(f"600x400+{x}+{y}")
        
        # Error text widget
        self.text = tk.Text(self.root, wrap=tk.WORD, bg='white', fg='black')
        self.text.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Close button
        self.close_btn = tk.Button(
            self.root,
            text="Close",
            command=self.root.destroy,
            bg='#007AFF',
            fg='white',
            relief='flat',
            padx=20,
            pady=10
        )
        self.close_btn.pack(pady=20)
    
    def show_error(self, error_message):
        """Display error message"""
        self.text.insert('1.0', error_message)
        self.root.mainloop()

if __name__ == "__main__":
    try:
        print("Starting TokiKanri...")
        sys.exit(main())
    except Exception as e:
        print(f"Critical error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)