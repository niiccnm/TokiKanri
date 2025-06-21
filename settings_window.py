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
        dark_mode_chk.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # External links frame ----------------------------------------------------------
        links_frame = ttk.Frame(container, style="Modern.TFrame")
        links_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        # GitHub button - using a text symbol instead of an icon
        github_btn = self.create_button(
            links_frame,
            " GitHub",
            lambda: self._open_url("https://github.com/niiccnm/TokiKanri"),
            ModernStyle.get_accent_color(),
            width=12,
        )
        # Add GitHub symbol (octocat) or alternative symbol
        github_btn.config(text="🐙 GitHub", font=("Segoe UI", 10, "bold"))
        github_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Donate button - using a text symbol instead of an icon
        donate_btn = self.create_button(
            links_frame,
            " Donate",
            lambda: self._open_url("https://ko-fi.com/niiccnm#payment-widget"),
            "#FF5E5B",  # Ko-fi red color
            width=12,
        )
        # Add coffee cup symbol
        donate_btn.config(text="☕ Donate", font=("Segoe UI", 10, "bold"))
        donate_btn.pack(side=tk.LEFT)

        # Close button ------------------------------------------------------------------
        close_btn = self.create_button(
            container,
            "Close",
            self._on_close,
            ModernStyle.get_inactive_color(),
            width=8,
        )
        close_btn.grid(row=99, column=0, columnspan=2, pady=(15, 0))
        
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
        ModernStyle.toggle_dark_mode(enabled)
        
        # Update UI for all windows
        ModernStyle.apply(self.app.main_window.root)
        self.update_ui_for_theme()
        
        # Update main window UI
        self.app.main_window.update_ui_for_theme()
        
        # Log the change
        self.app.logger.info(f"Dark mode toggled: {enabled}")
        
        # Force save config to ensure it persists
        self.config_manager.save_config()

    def _on_close(self):
        # Just hide; window instance kept for reuse
        self.withdraw()

    def update_ui_for_theme(self):
        """Update UI elements for the current theme"""
        # Update window background
        self.configure(bg=ModernStyle.get_bg_color())
        
        # Update all checkbuttons and spinboxes
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Checkbutton):
                        child.config(bg=ModernStyle.get_bg_color(), 
                                    fg=ModernStyle.get_text_color(),
                                    activebackground=ModernStyle.get_bg_color(),
                                    selectcolor=ModernStyle.get_bg_color())
                    elif isinstance(child, tk.Spinbox):
                        child.config(bg=ModernStyle.get_bg_color(),
                                    fg=ModernStyle.get_text_color(),
                                    buttonbackground=ModernStyle.get_bg_color())
