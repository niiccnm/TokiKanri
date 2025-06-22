"""Dedicated settings window to host all configuration options.

Future settings can be added here; the window is launched from MainWindow
via the Settings button.
"""
import tkinter as tk
from tkinter import ttk
import webbrowser

from ui_components import ModernStyle, BaseWidget
from startup_utils import enable_startup, disable_startup
from version import get_version_string


class SettingsWindow(tk.Toplevel, BaseWidget):
    """A singleton Toplevel window that contains application settings."""

    def __init__(self, parent, app):
        """Create the settings window.

        Parameters
        ----------
        parent : tk.Tk | tk.Toplevel
            Parent window (main application root).
        app : ProgramTokiKanri
            Reference to the main application/controller so we can access
            Config and other components.
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
        require_media_playback_chk.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=(25, 5), pady=2)
        
        # Media programs management -----------------------------------------------------
        media_programs_frame = ttk.Frame(container, style="Modern.TFrame")
        media_programs_frame.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E, padx=(25, 5), pady=5)
        
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
        dark_mode_chk.grid(row=6, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # External links frame ----------------------------------------------------------
        links_frame = ttk.Frame(container, style="Modern.TFrame")
        links_frame.grid(row=7, column=0, columnspan=2, sticky=tk.W+tk.E, padx=5, pady=10)
        
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
        version_label = ttk.Label(
            container,
            text=get_version_string(),
            style="Modern.TLabel",
            font=("", 8)  # Smaller font for version info
        )
        version_label.grid(row=100, column=0, columnspan=2, pady=(10, 0), sticky=tk.S)

        # Improve spacing
        container.columnconfigure(1, weight=1)
    
    def _populate_media_programs(self):
        """Populate the listbox with the current media programs"""
        self.media_programs_listbox.delete(0, tk.END)
        media_programs = self.config_manager.get("media_programs", [])
        for program in media_programs:
            self.media_programs_listbox.insert(tk.END, program)
    
    def _add_media_program(self):
        """Add a new media program to the list"""
        # Create a simple dialog to get the program name
        add_dialog = tk.Toplevel(self)
        add_dialog.title("Add Media Program")
        add_dialog.configure(bg=ModernStyle.get_bg_color())
        add_dialog.resizable(False, False)
        add_dialog.transient(self)
        add_dialog.grab_set()
        
        # Center the dialog on the settings window
        x = self.winfo_x() + (self.winfo_width() // 2) - (300 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (100 // 2)
        add_dialog.geometry(f"300x100+{x}+{y}")
        
        # Create the dialog content
        frame = ttk.Frame(add_dialog, style="Modern.TFrame")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(
            frame,
            text="Enter program name (e.g., vlc.exe):",
            style="Modern.TLabel",
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        entry = ttk.Entry(frame, width=30)
        entry.pack(fill=tk.X, padx=5, pady=5)
        entry.focus_set()
        
        def on_add():
            program_name = entry.get().strip()
            if program_name:
                # Get current media programs
                media_programs = self.config_manager.get("media_programs", [])
                
                # Check if program already exists
                if program_name not in media_programs:
                    media_programs.append(program_name)
                    self.config_manager.set("media_programs", media_programs)
                    self._populate_media_programs()
                    self.app.update_activity_tracker_settings()
                    self.app.logger.info(f"Added media program: {program_name}")
                
                add_dialog.destroy()
        
        # Add button
        button_frame = ttk.Frame(frame, style="Modern.TFrame")
        button_frame.pack(fill=tk.X, pady=5)
        
        add_button = self.create_button(
            button_frame,
            "Add",
            on_add,
            ModernStyle.get_accent_color(),
            width=8,
        )
        add_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = self.create_button(
            button_frame,
            "Cancel",
            add_dialog.destroy,
            ModernStyle.get_inactive_color(),
            width=8,
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key to add button
        entry.bind("<Return>", lambda event: on_add())
        
    def _remove_media_program(self):
        """Remove the selected media program from the list"""
        selected_idx = self.media_programs_listbox.curselection()
        if selected_idx:
            selected_program = self.media_programs_listbox.get(selected_idx[0])
            
            # Get current media programs
            media_programs = self.config_manager.get("media_programs", [])
            
            # Remove the selected program
            if selected_program in media_programs:
                media_programs.remove(selected_program)
                self.config_manager.set("media_programs", media_programs)
                self._populate_media_programs()
                self.app.update_activity_tracker_settings()
                self.app.logger.info(f"Removed media program: {selected_program}")
    
    def _open_url(self, url):
        """Open URL in default browser"""
        try:
            webbrowser.open_new_tab(url)
        except Exception as e:
            self.app.logger.error(f"Error opening URL {url}: {e}")

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def _on_max_change(self):
        value = int(self.max_var.get())
        self.config_manager.set("max_programs", value)
        # Update live components
        self.app.window_selector.max_programs = value

    def _on_mini_mode_toggle(self):
        enabled = bool(self.mini_mode_var.get())
        self.config_manager.set("start_in_mini_mode", enabled)
        
    def _on_media_mode_toggle(self):
        enabled = bool(self.media_mode_var.get())
        self.config_manager.set("media_mode_enabled", enabled)
        # Update live components
        self.app.update_activity_tracker_settings()
        self.app.logger.info(f"Media mode toggled: {enabled}")

    def _on_require_media_playback_toggle(self):
        enabled = bool(self.require_media_playback_var.get())
        self.config_manager.set("require_media_playback", enabled)
        # Update live components
        self.app.update_activity_tracker_settings()
        self.app.logger.info(f"Require media playback toggled: {enabled}")

    def _on_startup_toggle(self):
        enabled = bool(self.startup_var.get())
        self.config_manager.set("start_at_startup", enabled)
        try:
            if enabled:
                enable_startup()
                self.app.logger.info("Startup registry entry added")
            else:
                disable_startup()
                self.app.logger.info("Startup registry entry removed")
        except Exception as e:
            error_msg = f"Startup registry error: {e}"
            self.app.logger.error(error_msg)
            
            # Show error to user
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Startup Setting Error",
                f"Could not {('enable' if enabled else 'disable')} startup setting.\n\n"
                f"Error: {str(e)}\n\n"
                "You may need to run the application as administrator."
            )
            
            # Revert the checkbox to its previous state
            self.startup_var.set(not enabled)
            self.config_manager.set("start_at_startup", not enabled)

    def _on_dark_mode_toggle(self):
        enabled = bool(self.dark_mode_var.get())
        self.config_manager.set("dark_mode", enabled)
        # Update live components
        ModernStyle.toggle_dark_mode(enabled)
        self.app.update_ui_for_theme()
        self.update_ui_for_theme()
        
        # Log the change
        theme_name = "dark" if enabled else "light"
        self.app.logger.info(f"Theme changed to {theme_name}")

    def _on_close(self):
        # Just hide; window instance kept for reuse
        self.withdraw()

    def update_ui_for_theme(self):
        """Update UI elements for the current theme"""
        # Update background color for the window
        self.configure(bg=ModernStyle.get_bg_color())
        
        # Update all checkbuttons
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                # Use winfo_children() recursively instead of winfo_descendants()
                for child in self._get_all_children(widget):
                    if isinstance(child, tk.Checkbutton):
                        child.configure(
                            bg=ModernStyle.get_bg_color(),
                            fg=ModernStyle.get_text_color(),
                            activebackground=ModernStyle.get_bg_color(),
                            selectcolor=ModernStyle.get_bg_color(),
                        )
                    elif isinstance(child, tk.Spinbox):
                        child.configure(
                            bg=ModernStyle.get_bg_color(),
                            fg=ModernStyle.get_text_color(),
                            buttonbackground=ModernStyle.get_bg_color(),
                        )
                    elif isinstance(child, tk.Listbox):
                        child.configure(
                            bg=ModernStyle.get_input_bg_color(),
                            fg=ModernStyle.get_text_color(),
                            selectbackground=ModernStyle.get_accent_color(),
                            selectforeground=ModernStyle.get_bg_color(),
                        )
    
    def _get_all_children(self, widget):
        """Get all children widgets recursively"""
        children = widget.winfo_children()
        result = list(children)
        for child in children:
            result.extend(self._get_all_children(child))
        return result
