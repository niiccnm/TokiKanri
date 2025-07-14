"""Dedicated settings window to host all configuration options.

Future settings can be added here; the window is launched from MainWindow
via the Settings button.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

from ui_components import ModernStyle, BaseWidget
from startup_utils import enable_startup, disable_startup
from version import get_version_string


class SettingsWindow(tk.Toplevel, BaseWidget):
    """A singleton Toplevel window that contains application settings."""

    def __init__(self, parent, app):
        """Create the settings window.

        Args:
            parent (tk.Tk | tk.Toplevel): Parent window (main application root)
            app (ProgramTokiKanri): Reference to the main application/controller so we can access
                Config and other components
        """
        super().__init__(parent)
        self.app = app
        self.config_manager = app.config  # alias
        self.title("TokiKanri Settings")
        self.configure(bg=ModernStyle.get_bg_color())
        # Keep window above main if 'Always on top' (pin) is active
        self.wm_attributes('-topmost', app.always_on_top)
        self.lift()

        # Ensure only one instance: disable close to hide, not destroy
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._create_widgets()

    # ---------------------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------------------
    def _create_widgets(self):
        container = ttk.Frame(self, style="Modern.TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Max programs -----------------------------------------------------------------
        ttk.Label(
            container,
            text="Max programs to track:",
            style="Modern.TLabel",
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.max_var = tk.IntVar(value=self.config_manager.get("max_programs"))
        max_spin = tk.Spinbox(
            container,
            from_=1,
            to=50,
            width=5,
            textvariable=self.max_var,
            command=self._on_max_change, # Still keep for arrow clicks
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            buttonbackground=ModernStyle.get_bg_color(),
        )
        max_spin.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        max_spin.bind("<Return>", lambda event: self._on_max_change())
        max_spin.bind("<FocusOut>", lambda event: self._on_max_change())

        # Startup -----------------------------------------------------------------------
        self.startup_var = tk.BooleanVar(value=self.config_manager.get("start_at_startup"))
        startup_chk = tk.Checkbutton(
            container,
            text="Start TokiKanri when Windows starts",
            variable=self.startup_var,
            command=self._on_startup_toggle,
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            activebackground=ModernStyle.get_bg_color(),
            selectcolor=ModernStyle.get_bg_color(),
            anchor="w",
        )
        startup_chk.grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Mini-mode startup -------------------------------------------------------------
        self.mini_mode_var = tk.BooleanVar(value=self.config_manager.get("start_in_mini_mode"))
        mini_mode_chk = tk.Checkbutton(
            container,
            text="Start in Mini-Window mode",
            variable=self.mini_mode_var,
            command=self._on_mini_mode_toggle,
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            activebackground=ModernStyle.get_bg_color(),
            selectcolor=ModernStyle.get_bg_color(),
            anchor="w",
        )
        mini_mode_chk.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Media mode toggle -------------------------------------------------------------
        self.media_mode_var = tk.BooleanVar(value=self.config_manager.get("media_mode_enabled"))
        media_mode_chk = tk.Checkbutton(
            container,
            text="Enable Media Mode (track media players without user input)",
            variable=self.media_mode_var,
            command=self._on_media_mode_toggle,
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            activebackground=ModernStyle.get_bg_color(),
            selectcolor=ModernStyle.get_bg_color(),
            anchor="w",
        )
        media_mode_chk.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # API Status Alert --------------------------------------------------------------
        # This frame will be hidden/shown based on API status
        self.api_alert_frame = ttk.Frame(container, style="Modern.TFrame")
        self.api_alert_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, padx=(25, 5), pady=(5, 5))
        self.api_alert_frame.grid_remove()  # Hide initially
        
        # Create a frame with warning background
        alert_bg_frame = tk.Frame(
            self.api_alert_frame,
            bg="#FFF3CD",  # Light yellow background
            bd=1,
            relief=tk.SOLID,
            highlightbackground="#FFE494",  # Darker yellow border
            highlightthickness=1,
        )
        alert_bg_frame.pack(fill=tk.X, expand=True, padx=0, pady=0)
        
        # Warning icon (emoji)
        warning_label = tk.Label(
            alert_bg_frame,
            text="⚠️",
            bg="#FFF3CD",
            fg="#856404",  # Dark yellow/amber text
            font=("Segoe UI", 10),
        )
        warning_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        
        # Alert text
        self.api_alert_text = tk.StringVar(value="Media API issue detected")
        self.api_alert_label = tk.Label(
            alert_bg_frame,
            textvariable=self.api_alert_text,
            bg="#FFF3CD",
            fg="#856404",  # Dark yellow/amber text
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            anchor=tk.W,
            padx=5,
            pady=5,
        )
        self.api_alert_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # Media playback detection toggle -------------------------------------------------
        self.require_media_playback_var = tk.BooleanVar(value=self.config_manager.get("require_media_playback", True))
        require_media_playback_chk = tk.Checkbutton(
            container,
            text="    Require media to be playing (only track when media is active)",
            variable=self.require_media_playback_var,
            command=self._on_require_media_playback_toggle,
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            activebackground=ModernStyle.get_bg_color(),
            selectcolor=ModernStyle.get_bg_color(),
            anchor="w",
        )
        require_media_playback_chk.grid(row=5, column=0, columnspan=2, sticky=tk.W, padx=(25, 5), pady=2)
        
        # Media programs management -----------------------------------------------------
        media_programs_frame = ttk.Frame(container, style="Modern.TFrame")
        media_programs_frame.grid(row=6, column=0, columnspan=2, sticky=tk.W+tk.E, padx=(25, 5), pady=5)
        
        ttk.Label(
            media_programs_frame,
            text="Media Programs:",
            style="Modern.TLabel",
            font=("Segoe UI", 10),  # Match font size with listbox
        ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Create a listbox to display media programs
        self.media_programs_listbox = tk.Listbox(
            media_programs_frame,
            height=6,
            width=40,
            bg=ModernStyle.get_input_bg_color(),
            fg=ModernStyle.get_text_color(),
            selectbackground=ModernStyle.get_accent_color(),
            selectforeground=ModernStyle.get_bg_color(),
            font=("Segoe UI", 10),  # Add font specification for larger text
        )
        self.media_programs_listbox.grid(row=1, column=0, rowspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Populate the listbox with current media programs
        self._populate_media_programs()
        
        # Add buttons to add/remove media programs
        add_btn = self.create_button(
            media_programs_frame,
            "Add",
            self._add_media_program,
            ModernStyle.get_accent_color(),
            width=10,
            font=("Segoe UI", 10),
        )
        add_btn.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        remove_btn = self.create_button(
            media_programs_frame,
            "Remove",
            self._remove_media_program,
            ModernStyle.get_inactive_color(),
            width=10,
            font=("Segoe UI", 10),
        )
        remove_btn.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Dark mode toggle --------------------------------------------------------------
        self.dark_mode_var = tk.BooleanVar(value=self.config_manager.get("dark_mode"))
        dark_mode_chk = tk.Checkbutton(
            container,
            text="Dark Mode",
            variable=self.dark_mode_var,
            command=self._on_dark_mode_toggle,
            bg=ModernStyle.get_bg_color(),
            fg=ModernStyle.get_text_color(),
            activebackground=ModernStyle.get_bg_color(),
            selectcolor=ModernStyle.get_bg_color(),
            anchor="w",
        )
        dark_mode_chk.grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # External links frame ----------------------------------------------------------
        links_frame = ttk.Frame(container, style="Modern.TFrame")
        links_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=10)
        
        # Center the buttons in the frame
        links_frame.columnconfigure(0, weight=1)
        links_frame.columnconfigure(1, weight=1)
        links_frame.columnconfigure(2, weight=1)
        
        # Create a centered inner frame for the buttons
        buttons_frame = ttk.Frame(links_frame, style="Modern.TFrame")
        buttons_frame.grid(row=0, column=1, sticky=tk.EW)
        
        # GitHub button - using a text symbol instead of an icon
        github_btn = self.create_button(
            buttons_frame,
            " GitHub",
            lambda: self._open_url("https://github.com/niiccnm/TokiKanri"),
            ModernStyle.get_accent_color(),
            width=14,
            font=("Segoe UI", 10, "bold")
        )
        # Add GitHub symbol (octocat) or alternative symbol
        github_btn.config(text="🐙 GitHub")
        github_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Donate button - using a text symbol instead of an icon
        donate_btn = self.create_button(
            buttons_frame,
            " Donate",
            lambda: self._open_url("https://ko-fi.com/niiccnm"),
            "#FF5E5B",  # Ko-fi red color
            width=14,
            font=("Segoe UI", 10, "bold")
        )
        # Add coffee cup symbol
        donate_btn.config(text="☕ Donate")
        donate_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Updates frame ----------------------------------------------------------------
        updates_frame = ttk.Frame(container, style="Modern.TFrame")
        updates_frame.grid(row=98, column=0, columnspan=2, sticky=tk.EW, pady=(15, 0))
        updates_frame.columnconfigure(0, weight=1)
        
        # Check for Updates button
        update_btn = self.create_button(
            updates_frame,
            "🔄 Check for Updates",
            self._check_for_updates,
            ModernStyle.get_accent_color(),
            width=20,
            font=("Segoe UI", 10)
        )
        update_btn.grid(row=0, column=0)
        
        # Close button ------------------------------------------------------------------
        close_btn_frame = ttk.Frame(container, style="Modern.TFrame")
        close_btn_frame.grid(row=99, column=0, columnspan=2, sticky=tk.EW, pady=(15, 0))
        close_btn_frame.columnconfigure(0, weight=1)
        
        close_btn = self.create_button(
            close_btn_frame,
            "Close",
            self._on_close,
            ModernStyle.get_inactive_color(),
            width=14,
            font=("Segoe UI", 10, "bold"),
        )
        close_btn.grid(row=0, column=0)
        
        # Version information ----------------------------------------------------------
        version_str = get_version_string()
        version_label = ttk.Label(
            container,
            text=f"Version {version_str}",
            style="Modern.TLabel",
            font=("Segoe UI", 9),
        )
        version_label.grid(row=100, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        # Initialize API status
        self.update_api_status()
        
        # Update API status periodically
        self.after(5000, self._periodic_api_status_update)

    def update_api_status(self):
        """Update the API status display based on the current status"""
        if not hasattr(self.app, 'activity_tracker'):
            return
            
        activity_tracker = self.app.activity_tracker
        status = activity_tracker.media_api_status
        
        # Only show alert for problem states
        if status == "Unresponsive":
            self.api_alert_text.set("Windows Media Control API is unresponsive. Media detection may not work correctly.")
            self.api_alert_frame.grid()  # Show the alert
        elif status == "Unavailable":
            self.api_alert_text.set("Windows Media Control API is not available. Media detection features will be limited.")
            self.api_alert_frame.grid()  # Show the alert
        else:
            # Hide the alert for "Available" or "Unknown" status
            self.api_alert_frame.grid_remove()
        
    def _periodic_api_status_update(self):
        """Update the API status display periodically"""
        self.update_api_status()
        # Schedule next update
        self.after(5000, self._periodic_api_status_update)

    def _populate_media_programs(self):
        """Populate the listbox with the current media programs"""
        self.media_programs_listbox.delete(0, tk.END)
        media_programs = self.config_manager.get("media_programs", [])
        for program in media_programs:
            self.media_programs_listbox.insert(tk.END, program)

    def _check_for_updates(self):
        """Check for application updates from GitHub"""
        self.app.logger.info("Manually checking for updates...")
        try:
            # Call the check_for_updates_manually method in the app controller
            self.app.check_for_updates_manually(parent=self)
        except Exception as e:
            self.app.logger.error(f"Error checking for updates: {e}")
            messagebox.showerror(
                "Update Check Failed",
                f"Failed to check for updates: {str(e)}",
                parent=self
            )

    def _add_media_program(self):
        """Add a new media program to the list"""
        # Create a simple dialog to get the program name
        add_dialog = tk.Toplevel(self)
        add_dialog.title("Add Media Program")
        add_dialog.resizable(False, False)
        add_dialog.configure(bg=ModernStyle.get_bg_color())
        add_dialog.transient(self)
        add_dialog.grab_set()
        
        # Keep dialog above main if 'Always on top' (pin) is active
        add_dialog.wm_attributes('-topmost', self.app.always_on_top)
        
        # Center the dialog on the parent window
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (350 // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (160 // 2)
        add_dialog.geometry(f"350x160+{x}+{y}")
        
        # Create the dialog content
        frame = ttk.Frame(add_dialog, style="Modern.TFrame", padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="Enter program name (e.g., vlc.exe):",
            style="Modern.TLabel",
            wraplength=330
        ).pack(pady=(0, 12))
        
        program_entry = ttk.Entry(frame, width=40)
        program_entry.pack(pady=8, fill=tk.X, ipady=2)
        program_entry.focus_set()
        
        # Create buttons frame with center alignment
        buttons_container = ttk.Frame(frame, style="Modern.TFrame")
        buttons_container.pack(pady=10, fill=tk.X)
        
        # Create inner frame to center the buttons
        buttons_frame = ttk.Frame(buttons_container, style="Modern.TFrame")
        buttons_frame.pack(expand=True)
        
        # Add button
        add_btn = self.create_button(
            buttons_frame,
            "Add",
            lambda: on_add(),
            ModernStyle.get_accent_color(),
            width=10
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Cancel button
        cancel_btn = self.create_button(
            buttons_frame,
            "Cancel",
            add_dialog.destroy,
            ModernStyle.get_inactive_color(),
            width=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Handle Enter key
        add_dialog.bind("<Return>", lambda event: on_add())
        add_dialog.bind("<Escape>", lambda event: add_dialog.destroy())
        
        def on_add():
            program_name = program_entry.get().strip()
            if not program_name:
                return
                
            # Get current media programs
            media_programs = self.config_manager.get("media_programs", [])
            
            # Add the new program if it doesn't already exist
            if program_name not in media_programs:
                media_programs.append(program_name)
                self.config_manager.set("media_programs", media_programs)
                self._populate_media_programs()
                
                self.app.logger.info(f"Added media program: {program_name}")
                
                # Update activity tracker with new settings
                self.app.update_activity_tracker_settings()
                
            add_dialog.destroy()

    def _remove_media_program(self):
        """Remove the selected media program from the list"""
        selected_idx = self.media_programs_listbox.curselection()
        if not selected_idx:
            return
        selected_program = self.media_programs_listbox.get(selected_idx[0])
        
        # Get current media programs
        media_programs = self.config_manager.get("media_programs", [])
        
        # Remove the selected program
        if selected_program in media_programs:
            media_programs.remove(selected_program)
            self.config_manager.set("media_programs", media_programs)
            self._populate_media_programs()
            
            self.app.logger.info(f"Removed media program: {selected_program}")
            
            # Update activity tracker with new settings
            self.app.update_activity_tracker_settings()
        
    def _open_url(self, url):
        """Open the specified URL in the default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            self.app.logger.error(f"Failed to open URL: {url} - {e}")
            
    def _on_max_change(self):
        """Handle changes to the max programs spinbox"""
        max_programs = self.max_var.get()
        self.config_manager.set("max_programs", max_programs)
        
        # Update the data manager's max_programs value
        self.app.data_manager.update_max_programs(max_programs)
        
        # Update window selector
        self.app.window_selector.max_programs = max_programs
        
    def _on_mini_mode_toggle(self):
        self.config_manager.set("start_in_mini_mode", bool(self.mini_mode_var.get()))
        
    def _on_media_mode_toggle(self):
        enabled = bool(self.media_mode_var.get())
        self.config_manager.set("media_mode_enabled", enabled)
        
        # Update activity tracker settings
        self.app.update_activity_tracker_settings()
        
        # Update API status display immediately after toggling media mode
        self.update_api_status()
        
        self.app.logger.info(f"Media mode toggled: {enabled}")
        
    def _on_require_media_playback_toggle(self):
        enabled = bool(self.require_media_playback_var.get())
        self.config_manager.set("require_media_playback", enabled)
        
        # Update activity tracker settings
        self.app.update_activity_tracker_settings()
        
        self.app.logger.info(f"Require media playback toggled: {enabled}")
        
    def _on_startup_toggle(self):
        """Handle changes to the startup checkbox"""
        startup_enabled = bool(self.startup_var.get())
        self.config_manager.set("start_at_startup", startup_enabled)
        
        if startup_enabled:
            try:
                # Enable startup in system
                enable_startup()
                self.app.logger.info("Application set to start with Windows")
            except Exception as e:
                self.app.logger.error(f"Error enabling startup: {e}")
                self.startup_var.set(False)
                self.config_manager.set("start_at_startup", False)
        else:
            try:
                # Disable startup in system
                disable_startup()
                self.app.logger.info("Application will no longer start with Windows")
            except Exception as e:
                self.app.logger.error(f"Error disabling startup: {e}")
                self.startup_var.set(True)
                self.config_manager.set("start_at_startup", True)
        
    def _on_dark_mode_toggle(self):
        """Handle changes to the dark mode checkbox"""
        dark_mode = bool(self.dark_mode_var.get())
        self.config_manager.set("dark_mode", dark_mode)
        
        # Update theme for entire application
        ModernStyle.toggle_dark_mode(dark_mode)
        self.app.update_ui_for_theme()
        
        self.app.logger.info(f"Dark mode toggled: {dark_mode}")
        
    def _on_close(self):
        # Just hide; window instance kept for reuse
        self.withdraw()
        
    def update_ui_for_theme(self):
        """Update all UI elements for the current theme"""
        bg_color = ModernStyle.get_bg_color()
        text_color = ModernStyle.get_text_color()
        input_bg_color = ModernStyle.get_input_bg_color()
        
        # Update main window background
        self.configure(bg=bg_color)
        
        # Update all child widgets
        for widget in self._get_all_children(self):
            if isinstance(widget, tk.Checkbutton):
                widget.configure(
                    bg=bg_color,
                    fg=text_color,
                    activebackground=bg_color,
                    selectcolor=bg_color,
                )
            elif isinstance(widget, tk.Spinbox):
                widget.configure(
                    bg=input_bg_color,
                    fg=text_color,
                    buttonbackground=bg_color,
                )
            elif isinstance(widget, tk.Listbox):
                widget.configure(
                    bg=input_bg_color,
                    fg=text_color,
                    selectbackground=ModernStyle.get_accent_color(),
                    selectforeground=bg_color,
                )
            elif isinstance(widget, tk.Entry):
                widget.configure(
                    bg=input_bg_color,
                    fg=text_color,
                )
                
        # Alert frame colors are fixed and don't change with theme
        
        # Update API status display
        self.update_api_status()
                
    def _get_all_children(self, widget):
        """Recursively get all child widgets"""
        children = widget.winfo_children()
        result = list(children)
        
        for child in children:
            result.extend(self._get_all_children(child))
            
        return result
