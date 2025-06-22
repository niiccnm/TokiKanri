# mini_window.py
import tkinter as tk
import win32gui
import win32con
import os
from ui_components import ModernStyle
from config import Config
from logger import Logger

# Constants for MiniWindow
MINI_WINDOW_TITLE = "TokiKanri Mini"
TITLE_BAR_HEIGHT = 1
TIME_LABEL_DEFAULT_TEXT = "00:00"
TIME_LABEL_FONT = ("Helvetica", 18, "bold")
TIME_LABEL_FG = "white"
TIME_LABEL_PADY = (3, 4)
STATUS_DOT_SIZE = 6
STATUS_DOT_PADX = 4
STATUS_DOT_PADY = (0, 6)
DRAG_CLICK_THRESHOLD_MS = 300
MONITOR_POS_MARGIN_X = 10
MONITOR_POS_MARGIN_Y = 10
CONTEXT_MENU_SHOW_MAIN = "Show Main Window"
CONTEXT_MENU_EXIT = "Exit"
STATUS_DOT_ACTIVE_COLOR = 'green'
STATUS_DOT_PAUSED_COLOR = 'yellow'
STATUS_DOT_INACTIVE_COLOR = 'red'
NO_TRACKING_TIME_TEXT = "--:--"

# Default window size if config is not available
DEFAULT_MINI_WIDTH = 180
DEFAULT_MINI_HEIGHT = 45

class MiniWindow:
    """Mini window interface for compact program display"""
    def __init__(self, parent):
        """Initialize mini window
        
        Args:
            parent: Parent application instance
        """
        self.parent = parent
        # Use parent's config if available, otherwise create a new one
        self.config = getattr(parent, 'config', Config())
        self.logger = Logger()
        
        # Create a toplevel window for the mini view
        self.window = tk.Toplevel(parent.root)
        self.window.title(MINI_WINDOW_TITLE)
        
        # Initialize window state
        self.dragging = False
        self.offset_x = self.offset_y = 0
        self.last_valid_x = self.last_valid_y = 0
        self._last_click_time = 0
        
        # Configure window
        self._setup_window()
        self._create_widgets()
        self._setup_bindings()
        
        # Initially hide the window
        self.window.withdraw()

    def _setup_window(self):
        """Configure window properties"""
        # Set window attributes
        self.window.wm_attributes('-topmost', True)
        self.window.protocol("WM_DELETE_WINDOW", self.parent.quit_app)
        
        # Get window size from config with defaults
        width = DEFAULT_MINI_WIDTH
        height = DEFAULT_MINI_HEIGHT
        try:
            mini_window_size = self.config.get('mini_window_size')
            if mini_window_size and isinstance(mini_window_size, dict):
                width = mini_window_size.get('width', DEFAULT_MINI_WIDTH)
                height = mini_window_size.get('height', DEFAULT_MINI_HEIGHT)
        except (AttributeError, TypeError):
            # Use defaults if config access fails
            pass
            
        self.window.geometry(f"{width}x{height}")
        self.position_window()
        
        # Configure window style for Windows
        if os.name == 'nt':
            self._configure_windows_style()

    def _configure_windows_style(self):
        """Configure Windows-specific window style"""
        try:
            hwnd = self.window.winfo_id()
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            # Remove maximize button but keep minimize and close
            style = style & ~win32con.WS_MAXIMIZEBOX
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        except Exception as e:
            self.logger.error(f"Error configuring Windows style: {Logger.format_error(e)}")

    def _create_widgets(self):
        """Create window widgets"""
        # Main frame
        self.frame = tk.Frame(
            self.window,
            bg=ModernStyle.MINI_NO_TRACKING_BG,
            highlightthickness=0
        )
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Title bar with minimal height
        self.title_bar = tk.Frame(
            self.frame,
            bg=ModernStyle.MINI_NO_TRACKING_BG,
            height=TITLE_BAR_HEIGHT
        )
        self.title_bar.pack(fill=tk.X)
        
        # Time display label
        self.time_label = tk.Label(
            self.frame,
            text=TIME_LABEL_DEFAULT_TEXT,
            font=TIME_LABEL_FONT,
            bg=ModernStyle.MINI_NO_TRACKING_BG,
            fg=TIME_LABEL_FG
        )
        self.time_label.pack(pady=TIME_LABEL_PADY)
        
        # Status indicator
        self._create_status_indicator()
        
        # Make window non-resizable
        self.window.resizable(False, False)

    def _create_status_indicator(self):
        """Create status dot indicator"""
        self.status_dot = tk.Canvas(
            self.frame,
            width=STATUS_DOT_SIZE,
            height=STATUS_DOT_SIZE,
            bg=ModernStyle.MINI_NO_TRACKING_BG,
            highlightthickness=0
        )
        self.status_dot.pack(side=tk.RIGHT, padx=STATUS_DOT_PADX, pady=STATUS_DOT_PADY)
        self.status_dot.create_oval(0, 0, STATUS_DOT_SIZE, STATUS_DOT_SIZE, fill='white')

    def _setup_bindings(self):
        """Setup window event bindings"""
        for widget in (self.title_bar, self.frame):
            self._bind_widget(widget)
        
        # Bind time label and status dot separately
        self._bind_widget(self.time_label)
        self._bind_widget(self.status_dot)

    def _bind_widget(self, widget):
        """Bind events to a widget
        
        Args:
            widget: Widget to bind events to
        """
        widget.bind("<Button-1>", self.start_drag)
        widget.bind("<B1-Motion>", self.on_drag)
        widget.bind("<ButtonRelease-1>", self.stop_drag)
        widget.bind("<Button-3>", self.show_context_menu)
        widget.bind("<Double-Button-1>", 
                   lambda e: self.parent.show_main_window())

    def start_drag(self, event):
        """Start window dragging
        
        Args:
            event: Event object containing click information
        """
        if event.time - self._last_click_time > DRAG_CLICK_THRESHOLD_MS:
            self.dragging = True
            self.offset_x = event.x_root - self.window.winfo_x()
            self.offset_y = event.y_root - self.window.winfo_y()
        self._last_click_time = event.time

    def on_drag(self, event):
        """Handle window dragging
        
        Args:
            event: Event object containing mouse position
        """
        if self.dragging:
            # Calculate new position
            new_x = event.x_root - self.offset_x
            new_y = event.y_root - self.offset_y
            
            # Update position directly - simplified approach
            self._update_position(new_x, new_y)

    def _update_position(self, x, y):
        """Update window position
        
        Args:
            x: New X coordinate
            y: New Y coordinate
        """
        self.window.geometry(f"+{x}+{y}")
        self.last_valid_x, self.last_valid_y = x, y

    def stop_drag(self, event):
        """Stop window dragging
        
        Args:
            event: Event object
        """
        if self.dragging:
            self.dragging = False
        elif not hasattr(self, '_last_click_time') or \
             event.time - self._last_click_time > DRAG_CLICK_THRESHOLD_MS:
            self.parent.show_main_window()

    def show_context_menu(self, event):
        """Show context menu
        
        Args:
            event: Event object containing click position
        """
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(
            label=CONTEXT_MENU_SHOW_MAIN,
            command=self.parent.show_main_window
        )
        menu.add_command(
            label=CONTEXT_MENU_EXIT,
            command=self.parent.quit_app
        )
        menu.tk_popup(event.x_root, event.y_root)

    def position_window(self):
        """Position window on screen"""
        # Get window dimensions
        width = DEFAULT_MINI_WIDTH
        height = DEFAULT_MINI_HEIGHT
        try:
            mini_window_size = self.config.get('mini_window_size')
            if mini_window_size and isinstance(mini_window_size, dict):
                width = mini_window_size.get('width', DEFAULT_MINI_WIDTH)
                height = mini_window_size.get('height', DEFAULT_MINI_HEIGHT)
        except (AttributeError, TypeError):
            # Use defaults if config access fails
            pass

        if hasattr(self, 'last_valid_x') and self.last_valid_x is not None:
            # Position at last known coordinates
            self.window.geometry(
                f"{width}x{height}+{self.last_valid_x}+{self.last_valid_y}")
        else:
            # Fallback positioning in bottom right corner
            x = self.window.winfo_screenwidth() - width - MONITOR_POS_MARGIN_X
            y = self.window.winfo_screenheight() - height - MONITOR_POS_MARGIN_Y
            self.window.geometry(f"{width}x{height}+{x}+{y}")
            self.last_valid_x, self.last_valid_y = x, y

    def show(self):
        """Show mini window"""
        self.window.deiconify()
        self.position_window()
        self.window.lift()

    def hide(self):
        """Hide mini window"""
        self.window.withdraw()

    def update_status(self, is_active, program):
        """Update status display based on activity.

        Args:
            is_active (bool): Whether the tracked program is active.
            program (str or None): The name of the program being tracked.
        """
        is_tracking = program is not None
        
        if not is_tracking:
            bg_color = ModernStyle.MINI_NO_TRACKING_BG
            dot_color = STATUS_DOT_INACTIVE_COLOR
        else:
            bg_color = ModernStyle.MINI_ACTIVE_BG if is_active else ModernStyle.MINI_INACTIVE_BG
            dot_color = STATUS_DOT_ACTIVE_COLOR if is_active else STATUS_DOT_PAUSED_COLOR

        for widget in [self.frame, self.title_bar, self.time_label, self.status_dot]:
            widget.configure(bg=bg_color)
        
        self.status_dot.delete('all')
        self.status_dot.create_oval(0, 0, STATUS_DOT_SIZE, STATUS_DOT_SIZE, fill=dot_color, outline=bg_color)

    def update_display(self, time_text, is_active, is_tracking):
        """Update the mini window display
        
        Args:
            time_text: Time string to display
            is_active: Whether tracking is active
            is_tracking: Whether a program is being tracked
        """
        if is_tracking:
            # Set background color based on activity state
            if is_active:
                bg_color = ModernStyle.MINI_ACTIVE_BG
                dot_color = STATUS_DOT_ACTIVE_COLOR
            else:
                bg_color = ModernStyle.MINI_INACTIVE_BG
                dot_color = STATUS_DOT_PAUSED_COLOR
        else:
            bg_color = ModernStyle.MINI_NO_TRACKING_BG
            dot_color = STATUS_DOT_INACTIVE_COLOR
            # Use placeholder text when not tracking
            time_text = NO_TRACKING_TIME_TEXT
            
        # Update UI elements
        self.frame.config(bg=bg_color)
        self.title_bar.config(bg=bg_color)
        self.time_label.config(bg=bg_color, text=time_text)
        self.status_dot.config(bg=bg_color)
        
        # Update status dot - recreate it to ensure it's visible
        self.status_dot.delete("all")
        self.status_dot.create_oval(0, 0, STATUS_DOT_SIZE, STATUS_DOT_SIZE, fill=dot_color)
    
    def update_ui_for_theme(self):
        """Update UI elements for the current theme"""
        # No specific theme changes needed for mini window as it uses
        # fixed colors that are the same in both light and dark modes
        # Just ensure the current state is properly reflected
        if hasattr(self, 'time_label') and hasattr(self, 'status_dot'):
            # Get current text and determine if tracking/active
            current_text = self.time_label.cget('text')
            is_tracking = current_text != NO_TRACKING_TIME_TEXT
            
            # Get current dot color to determine if active
            is_active = False
            try:
                # Try to get the color of the first item in the canvas
                if self.status_dot.find_all():
                    dot_id = self.status_dot.find_all()[0]
                    dot_color = self.status_dot.itemcget(dot_id, 'fill')
                    is_active = dot_color == STATUS_DOT_ACTIVE_COLOR
            except (AttributeError, IndexError, tk.TclError):
                # Handle any errors that might occur
                pass
                
            # Update display with current state
            self.update_display(current_text, is_active, is_tracking)
