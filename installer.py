import sys
import subprocess
import pkg_resources
import os
import time
from tkinter import Tk, Label, ttk, messagebox
import threading
import site
import shutil
import logging
import traceback

# Set up logging
logging.basicConfig(
    filename='tokikanri_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

REQUIRED_PACKAGES = {
    'pywin32': 'pywin32',
    'psutil': 'psutil',
    'tkinter': None  # Built into Python
}

class InstallerGUI:
    def __init__(self):
        try:
            self.root = Tk()
            self.root.title("TokiKanri Installer")
            self.root.geometry("400x200")
            self.root.configure(bg="#ffffff")
            
            # Prevent window from being closed during installation
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.installation_complete = False
            
            # Center window
            self.center_window()
            
            # Create and pack widgets
            self.status_label = Label(
                self.root,
                text="Checking requirements...",
                font=("Helvetica", 10),
                bg="#ffffff",
                fg="#333333"
            )
            self.status_label.pack(pady=20)
            
            self.progress = ttk.Progressbar(
                self.root,
                length=300,
                mode='determinate',
                style="Modern.Horizontal.TProgressbar"
            )
            self.progress.pack(pady=10)
            
            # Configure style
            style = ttk.Style()
            style.configure(
                "Modern.Horizontal.TProgressbar",
                background="#007AFF",
                troughcolor="#F3F4F6",
                borderwidth=0,
                thickness=8
            )
            
            logging.info("GUI initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing GUI: {str(e)}\n{traceback.format_exc()}")
            raise

    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 400
        window_height = 200
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def update_status(self, message, progress_value):
        try:
            self.status_label.config(text=message)
            self.progress['value'] = progress_value
            self.root.update()
            logging.info(f"Status updated: {message} - Progress: {progress_value}")
        except Exception as e:
            logging.error(f"Error updating status: {str(e)}\n{traceback.format_exc()}")

    def on_closing(self):
        if self.installation_complete:
            self.root.destroy()
        else:
            if messagebox.askokcancel("Quit", "Installation in progress. Are you sure you want to quit?"):
                logging.info("User cancelled installation")
                os._exit(1)

def post_pywin32_install():
    try:
        python_path = sys.executable
        python_dir = os.path.dirname(python_path)
        
        logging.info("Running pywin32 post-install script")
        subprocess.run([python_path, os.path.join(site.getsitepackages()[0], 'pywin32_postinstall.py'), '-install'])
        logging.info("pywin32 post-install completed successfully")
    except Exception as e:
        logging.error(f"Error in pywin32 post-install: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"Error during pywin32 installation: {str(e)}")

def check_and_install_dependencies(gui):
    try:
        missing_packages = []
        
        # Check for required packages
        for package, pip_name in REQUIRED_PACKAGES.items():
            if pip_name:  # Skip tkinter as it's built into Python
                try:
                    pkg_resources.get_distribution(package)
                    gui.update_status(f"✓ {package} is installed", 30)
                    logging.info(f"Package {package} is already installed")
                    time.sleep(0.5)
                except pkg_resources.DistributionNotFound:
                    missing_packages.append(pip_name)
                    gui.update_status(f"✗ {package} is missing", 30)
                    logging.info(f"Package {package} needs to be installed")
                    time.sleep(0.5)
        
        # Install missing packages
        if missing_packages:
            gui.update_status("Installing missing packages...", 50)
            for package in missing_packages:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    if package == 'pywin32':
                        post_pywin32_install()
                    gui.update_status(f"✓ Installed {package}", 70)
                    logging.info(f"Successfully installed {package}")
                    time.sleep(0.5)
                except subprocess.CalledProcessError as e:
                    error_msg = f"Error installing {package}: {str(e)}"
                    logging.error(f"{error_msg}\n{traceback.format_exc()}")
                    messagebox.showerror("Installation Error", error_msg)
                    sys.exit(1)
        
        gui.update_status("All requirements satisfied!", 90)
        time.sleep(1)
        
        # Run the main program
        try:
            gui.update_status("Starting TokiKanri...", 100)
            time.sleep(1)
            gui.installation_complete = True
            gui.root.destroy()
            
            logging.info("Starting main program")
            # Import and run the main program
            from program_tracker import ProgramTokiKanri
            tracker = ProgramTokiKanri()
            tracker.run()
            
        except Exception as e:
            error_msg = f"Error starting the program: {str(e)}"
            logging.error(f"{error_msg}\n{traceback.format_exc()}")
            messagebox.showerror("Error", error_msg)
            sys.exit(1)
            
    except Exception as e:
        error_msg = f"Error during dependency check: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("Error", error_msg)
        sys.exit(1)

def main():
    try:
        logging.info("Starting TokiKanri installer")
        
        # Initialize the GUI
        gui = InstallerGUI()
        
        # Run the dependency checker in a separate thread
        threading.Thread(target=check_and_install_dependencies, args=(gui,), daemon=True).start()
        
        # Start the GUI main loop
        gui.root.mainloop()
        
    except Exception as e:
        error_msg = f"Error in installer: {str(e)}"
        logging.error(f"{error_msg}\n{traceback.format_exc()}")
        messagebox.showerror("Error", error_msg)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Critical error: {str(e)}\n{traceback.format_exc()}")
        messagebox.showerror("Critical Error", f"A critical error occurred: {str(e)}\nCheck tokikanri_log.txt for details.")