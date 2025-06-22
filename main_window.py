# main_window.py
import tkinter as tk
from tkinter import ttk
import platform
from ui_components import ModernStyle, BaseWidget
from program_gui import ProgramGUI
from config import Config
from startup_utils import enable_startup, disable_startup  # still used by SettingsWindow
from settings_window import SettingsWindow

# Constants for MainWindow
MAIN_WINDOW_TITLE = "TokiKanri"
MAIN_CONTAINER_PADX = 20
MAIN_CONTAINER_PADY = 20
HEADER_FRAME_PADY = (0, 20)
HEADER_LABEL_TEXT = "Program Time Tracker"
PIN_BUTTON_TEXT = "📌"
MINIMIZE_BUTTON_TEXT = "🗕"
MINIMIZE_BUTTON_PADX = 5
CONTROLS_FRAME_PADY = (0, 20)
SELECT_WINDOW_BUTTON_TEXT = "Select Window"
SELECT_WINDOW_ACTIVE_TEXT = "Click on the window you want to track"
RESET_ALL_BUTTON_TEXT = "Reset All"
REMOVE_ALL_BUTTON_TEXT = "Remove All"
EXPORT_BUTTON_TEXT = "Export"
IMPORT_BUTTON_TEXT = "Import"
EXPORT_CONFIG_BUTTON_TEXT = "Export Config"
IMPORT_CONFIG_BUTTON_TEXT = "Import Config"
CONTROL_BUTTONS_PADY = (0, 10)
TOTAL_TIME_FRAME_PADY = (0, 20)
TOTAL_TIME_CONTAINER_PADY = 5
TOTAL_TIME_LABEL_TEXT = "Total Time Tracked:"
TOTAL_TIME_DEFAULT_TEXT = "00:00"
STATUS_LABEL_DEFAULT_TEXT = "Click 'Select Window' to start tracking"
STATUS_LABEL_PADY = 10
CANVAS_ANCHOR = "nw"
MOUSEWHEEL_SCROLL_UNITS = 120
STATUS_READY_TEXT = "Ready to Track"
STATUS_TRACKING_PREFIX = "Tracking: "
STATUS_PAUSED_TEXT = "Tracking paused: No activity"
SETTINGS_BUTTON_TEXT = "⚙"
SEARCH_PLACEHOLDER = "Search programs..."

# Custom scrollbar class for dark mode support
class DarkModeScrollbar(tk.Canvas):
    """A custom scrollbar implementation that supports dark mode styling"""
    
    def __init__(self, parent, **kwargs):
        self.command = kwargs.pop('command', None)
        
        # Set fixed dimensions and styling
        kwargs['highlightthickness'] = 0
        kwargs['bd'] = 0
        width = kwargs.pop('width', 14) if 'width' in kwargs else 14
        
        # Initialize with default colors - these will be updated in configure_colors
        tk.Canvas.__init__(self, parent, width=width, **kwargs)
        
        # Store dimensions
        self.width = width
        self.button_height = 16  # Height of arrow buttons
        self.thumb_width = width - 6  # Width of the thumb (with padding)
        self.thumb_min_height = 80  # Minimum height of the thumb
        self.thumb_radius = 4  # Corner radius for the thumb
        
        # Initial values for scrolling
        self._start = 0.0
        self._end = 1.0
        self._dragging = False
        self._initial_thumb_top = 0  # Store initial thumb position for dragging
        self._initial_y = 0  # Store initial click position for dragging
        
        # Create the track, thumb, and arrow buttons
        self.track = self.create_rectangle(0, self.button_height, width, 1000-self.button_height, outline="")
        
        # Create rounded thumb (will be updated in update_thumb)
        self.thumb = self.create_rounded_rectangle(
            3, self.button_height+3, 
            width-3, self.button_height+self.thumb_min_height, 
            self.thumb_radius
        )
        
        # Create up arrow button
        self.up_button_bg = self.create_rectangle(0, 0, width, self.button_height, outline="")
        self.up_arrow = self.create_polygon(
            width/2, 4,               # Top point
            width-4, self.button_height-4,  # Bottom right
            4, self.button_height-4,        # Bottom left
            fill="white", outline=""
        )
        
        # Create down arrow button
        self.down_button_bg = self.create_rectangle(0, 1000-self.button_height, width, 1000, outline="")
        self.down_arrow = self.create_polygon(
            width/2, 1000-4,               # Bottom point
            width-4, 1000-self.button_height+4,  # Top right
            4, 1000-self.button_height+4,        # Top left
            fill="white", outline=""
        )
        
        # Configure colors based on current theme
        self.configure_colors()
        
        # Bind events for thumb
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Configure>", self._on_configure)
        
        # Bind events for buttons
        self.tag_bind(self.up_button_bg, "<ButtonPress-1>", self._on_up_button)
        self.tag_bind(self.up_arrow, "<ButtonPress-1>", self._on_up_button)
        self.tag_bind(self.down_button_bg, "<ButtonPress-1>", self._on_down_button)
        self.tag_bind(self.down_arrow, "<ButtonPress-1>", self._on_down_button)
        
        # Bind events for track clicks (page up/down)
        self.tag_bind(self.track, "<ButtonPress-1>", self._on_track_click)
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)
    
    def configure_colors(self):
        """Configure colors based on current theme"""
        if ModernStyle.is_dark_mode():
            # Dark mode colors
            self.track_color = "#1E1E2E"  # Dark background
            self.thumb_color = "#4B4B63"  # Visible thumb
            self.active_thumb_color = "#6B6B83"  # Lighter on hover
            self.button_color = "#2D2D3F"  # Button background
            self.arrow_color = "#AAAAAA"  # Arrow color
        else:
            # Light mode colors
            self.track_color = "#DDDDDD"  # Light gray track
            self.thumb_color = "#A3A3A3"  # Dark gray thumb
            self.active_thumb_color = "#777777"  # Darker on hover
            self.button_color = "#CCCCCC"  # Button background
            self.arrow_color = "#555555"  # Arrow color
        
        # Apply colors
        self.configure(bg=self.track_color)
        self.itemconfig(self.track, fill=self.track_color)
        self.itemconfig(self.thumb, fill=self.thumb_color)
        self.itemconfig(self.up_button_bg, fill=self.button_color)
        self.itemconfig(self.down_button_bg, fill=self.button_color)
        self.itemconfig(self.up_arrow, fill=self.arrow_color)
        self.itemconfig(self.down_arrow, fill=self.arrow_color)
        self.current_thumb_color = self.thumb_color
    
    def _on_configure(self, event):
        """Handle resize events"""
        height = self.winfo_height()
        if height <= 0:
            return
            
        # Update track to fill the area between buttons
        self.coords(self.track, 0, self.button_height, self.width, height-self.button_height)
        
        # Update down button position
        self.coords(self.down_button_bg, 0, height-self.button_height, self.width, height)
        self.coords(
            self.down_arrow,
            self.width/2, height-4,               # Bottom point
            self.width-4, height-self.button_height+4,  # Top right
            4, height-self.button_height+4         # Top left
        )
        
        self.update_thumb()
    
    def _on_press(self, event):
        """Handle mouse press on scrollbar"""
        y = event.y
        
        # Ignore clicks on buttons
        if y < self.button_height or y > self.winfo_height() - self.button_height:
            return
        
        # Check if click is directly on the thumb
        # We need to check if the click is within the thumb's coordinates
        thumb_id = self.find_closest(event.x, event.y)[0]
        if thumb_id == self.thumb:
            self._dragging = True
            self._initial_y = y
            
            # Get current thumb position
            thumb_coords = self.coords(self.thumb)
            # For polygon (rounded rectangle), we need the second y-coordinate (index 3)
            self._initial_thumb_top = thumb_coords[3]
            
            self.current_thumb_color = self.active_thumb_color
            self.itemconfig(self.thumb, fill=self.current_thumb_color)
        else:
            # Handle click on track (page up/down)
            self._on_track_click(event)
    
    def _on_track_click(self, event):
        """Handle click on the track (not on thumb)"""
        y = event.y
        thumb_coords = self.coords(self.thumb)
        thumb_top = thumb_coords[1]
        
        # If click is above thumb, page up; if below, page down
        if y < thumb_top:
            if self.command:
                self.command("scroll", -1, "pages")
        else:
            if self.command:
                self.command("scroll", 1, "pages")
    
    def _on_release(self, event):
        """Handle mouse release"""
        self._dragging = False
        self.current_thumb_color = self.thumb_color
        self.itemconfig(self.thumb, fill=self.current_thumb_color)
    
    def _on_motion(self, event):
        """Handle mouse drag"""
        if self._dragging:
            # Calculate the delta movement
            delta_y = event.y - self._initial_y
            
            # Calculate new thumb position based on initial position plus delta
            new_y = self._initial_thumb_top + delta_y
            
            # Get current thumb coordinates to determine its height
            thumb_coords = self.coords(self.thumb)
            thumb_height = thumb_coords[-3] - thumb_coords[1]  # Using y-coordinates from the polygon
            
            # Calculate the relative position for moveto
            height = self.winfo_height()
            if height <= 0:
                return
                
            # Calculate available scrolling area
            scroll_height = height - 2 * self.button_height
            
            # Calculate relative position based on the top of the thumb
            rel_pos = (new_y - thumb_height/2 - self.button_height) / scroll_height
            rel_pos = max(0.0, min(1.0, rel_pos))
            
            # Update scrollbar position through command
            if self.command:
                self.command("moveto", rel_pos)
    
    def _on_enter(self, event):
        """Handle mouse enter"""
        self.current_thumb_color = self.active_thumb_color
        self.itemconfig(self.thumb, fill=self.current_thumb_color)
    
    def _on_leave(self, event):
        """Handle mouse leave"""
        if not self._dragging:
            self.current_thumb_color = self.thumb_color
            self.itemconfig(self.thumb, fill=self.current_thumb_color)
    
    def _on_up_button(self, event):
        """Handle up button click"""
        if self.command:
            self.command("scroll", -1, "units")
    
    def _on_down_button(self, event):
        """Handle down button click"""
        if self.command:
            self.command("scroll", 1, "units")
    
    def _update_thumb_from_absolute_y(self, y):
        """Update thumb position from absolute y coordinate"""
        height = self.winfo_height()
        if height <= 0:
            return
            
        # Calculate available scrolling area
        scroll_height = height - 2 * self.button_height
        
        # Constrain y to valid range
        y = max(self.button_height, min(y, height - self.button_height))
        
        # Calculate relative position
        rel_pos = (y - self.button_height) / scroll_height
        
        # Update scrollbar position through command
        if self.command:
            self.command("moveto", rel_pos)
            
    def _update_thumb_from_y(self, y):
        """Update thumb position from mouse y coordinate"""
        height = self.winfo_height()
        if height <= 0:
            return
            
        # Calculate available scrolling area
        scroll_height = height - 2 * self.button_height
        
        # Constrain y to valid range
        y = max(self.button_height, min(y, height - self.button_height))
        
        # Calculate relative position
        rel_pos = (y - self.button_height) / scroll_height
        
        # Update scrollbar position through command
        if self.command:
            self.command("moveto", rel_pos)
    
    def update_thumb(self):
        """Update thumb position and size based on current values"""
        height = self.winfo_height()
        if height <= 0:
            return
            
        # Calculate available scrolling area
        scroll_height = height - 2 * self.button_height
        
        # Calculate thumb dimensions
        visible_fraction = min(1.0, (self._end - self._start))
        thumb_height = max(self.thumb_min_height, scroll_height * visible_fraction)
        
        # Calculate thumb position
        top_pos = self.button_height + (scroll_height * self._start)
        bottom_pos = top_pos + thumb_height
        
        # Ensure bottom position doesn't exceed bounds
        bottom_pos = min(bottom_pos, height - self.button_height)
        
        # Delete old thumb and create new one with rounded corners
        self.delete(self.thumb)
        self.thumb = self.create_rounded_rectangle(
            3, top_pos, 
            self.width-3, bottom_pos, 
            self.thumb_radius,
            fill=self.current_thumb_color,
            outline=""
        )
        
        # Rebind events to the new thumb
        self.tag_bind(self.thumb, "<ButtonPress-1>", self._on_press)
        self.tag_bind(self.thumb, "<ButtonRelease-1>", self._on_release)
        self.tag_bind(self.thumb, "<B1-Motion>", self._on_motion)
        self.tag_bind(self.thumb, "<Enter>", self._on_enter)
        self.tag_bind(self.thumb, "<Leave>", self._on_leave)
    
    def set(self, start, end):
        """Set scrollbar position (called by scrolled widget)"""
        self._start = float(start)
        self._end = float(end)
        self.update_thumb()
        return True

class MainWindow(BaseWidget):
    """Main application window"""
    def __init__(self, parent):
        """Initialize main window"""
        self.parent = parent
        # Use parent's root window
        self.root = parent.root
        self.root.title("TokiKanri")
        
        # Get config from parent
        self.config = parent.config
        
        # Initialize search variables
        self._active_search = False
        self._current_search_text = ""
        
        # Set window size from config
        window_size = self.config.get("window_size", {"width": 400, "height": 600})
        width = window_size.get("width", 400)
        height = window_size.get("height", 600)
        self.root.geometry(f"{width}x{height}")
        
        # Set window background
        self.root.configure(bg=ModernStyle.get_bg_color())
        
        # Set up the window and create the GUI
        self._setup_window()
        self._create_gui()
        
    def _setup_window(self):
        """Initialize main window"""
        self.root.title(MAIN_WINDOW_TITLE)
        self.root.protocol("WM_DELETE_WINDOW", self.parent.quit_app)
        
        # Set window icon if available
        # self.root.iconbitmap("icon.ico")  # Uncomment when icon is available
        
    def _create_gui(self):
        """Create main GUI elements"""
        # Main container
        main_container = ttk.Frame(self.root, style="Modern.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True, padx=MAIN_CONTAINER_PADX, pady=MAIN_CONTAINER_PADY)
        
        # Bind click event to clear focus from search entry
        main_container.bind("<Button-1>", self._clear_search_focus)
        self.root.bind("<Button-1>", self._clear_search_focus)
        
        self._create_header(main_container)
        self._create_controls(main_container)
        self._create_search_bar(main_container)
        self._create_status(main_container)
        self._create_programs_area(main_container)
        
    def _create_header(self, parent):
        """Create header section"""
        header_frame = ttk.Frame(parent, style="Modern.TFrame")
        header_frame.pack(fill=tk.X, pady=HEADER_FRAME_PADY)
        
        # App title with modern font
        ttk.Label(header_frame,
                 text=HEADER_LABEL_TEXT,
                 style="Header.TLabel").pack(side=tk.LEFT)
        
        # Control buttons container for better alignment
        controls_container = ttk.Frame(header_frame, style="Modern.TFrame")
        controls_container.pack(side=tk.RIGHT)
        
        # Initial color for pin button (will be updated in update_pin_button)
        initial_pin_color = ModernStyle.get_button_toggle_color() if self.parent.always_on_top else ModernStyle.get_inactive_color()
        
        # Pin button with icon
        self.toggle_button = self.create_button(
            controls_container,
            PIN_BUTTON_TEXT,
            self.parent.toggle_always_on_top,
            initial_pin_color,
            padx=8,
            pady=4
        )
        self.toggle_button.pack(side=tk.RIGHT, padx=2)
        
        # Minimize button with icon
        minimize_button = self.create_button(
            controls_container,
            MINIMIZE_BUTTON_TEXT,
            self.parent.minimize_to_tray,
            ModernStyle.get_accent_color(),
            padx=8,
            pady=4
        )
        minimize_button.pack(side=tk.RIGHT, padx=2)
        
        # Settings button
        settings_button = self.create_button(
            controls_container,
            SETTINGS_BUTTON_TEXT,
            self._open_settings,
            ModernStyle.get_accent_color(),
            padx=8,
            pady=4
        )
        settings_button.pack(side=tk.RIGHT, padx=2)
        
    def _create_controls(self, parent):
        """Create control buttons section with improved layout"""
        # Main controls frame
        controls_frame = ttk.Frame(parent, style="Modern.TFrame")
        controls_frame.pack(fill=tk.X, pady=CONTROLS_FRAME_PADY)
        
        # Left side controls (primary actions)
        left_controls = ttk.Frame(controls_frame, style="Modern.TFrame")
        left_controls.pack(side=tk.LEFT)
        
        # Select window button (primary action)
        self.select_button = self.create_button(
            left_controls,
            SELECT_WINDOW_BUTTON_TEXT,
            self.parent.start_window_selection,
            ModernStyle.get_success_color(),
            padx=10,
            pady=6
        )
        self.select_button.pack(side=tk.LEFT, padx=5, pady=CONTROL_BUTTONS_PADY)
        
        # Reset all button
        reset_all_button = self.create_button(
            left_controls,
            RESET_ALL_BUTTON_TEXT,
            self.parent.reset_all_timers,
            ModernStyle.get_button_remove_color(),
            padx=10,
            pady=6
        )
        reset_all_button.pack(side=tk.LEFT, padx=5, pady=CONTROL_BUTTONS_PADY)
        
        # Remove all button
        remove_all_button = self.create_button(
            left_controls,
            REMOVE_ALL_BUTTON_TEXT,
            self.parent.remove_all_programs,
            ModernStyle.get_button_remove_color(),
            padx=10,
            pady=6
        )
        remove_all_button.pack(side=tk.LEFT, padx=5, pady=CONTROL_BUTTONS_PADY)
        
        # Right side controls (secondary actions)
        right_controls = ttk.Frame(controls_frame, style="Modern.TFrame")
        right_controls.pack(side=tk.RIGHT)
        
        # Data management buttons in a row
        data_buttons = [
            (EXPORT_BUTTON_TEXT, self.parent.export_data),
            (IMPORT_BUTTON_TEXT, self.parent.import_data),
            (EXPORT_CONFIG_BUTTON_TEXT, self.parent.export_config),
            (IMPORT_CONFIG_BUTTON_TEXT, self.parent.import_config)
        ]
        
        for text, command in data_buttons:
            btn = self.create_button(
                right_controls,
                text,
                command,
                ModernStyle.get_accent_color(),
                padx=8,
                pady=5
            )
            btn.pack(side=tk.LEFT, padx=3, pady=CONTROL_BUTTONS_PADY)
        
        # Create the total time card with explicit colors
        self._create_total_time_card(parent)
    
    def _create_total_time_card(self, parent):
        """Create total time display with card style and explicit colors"""
        try:
            # Create a frame with explicit styling
            self.total_time_frame = ttk.Frame(parent, style="Card.TFrame")
            self.total_time_frame.pack(fill=tk.X, pady=TOTAL_TIME_FRAME_PADY)
            
            # Create a canvas for the border with explicit colors
            card_border = tk.Canvas(
                self.total_time_frame,
                highlightthickness=1,
                highlightbackground=ModernStyle.get_card_border(),
                bg=ModernStyle.get_card_bg(),
                bd=0
            )
            card_border.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Store the canvas as an attribute for theme updates
            setattr(self.total_time_frame, '_border_canvas_obj', card_border)
            
            # Content container
            total_container = ttk.Frame(self.total_time_frame, style="Card.TFrame")
            total_container.pack(fill=tk.X, pady=TOTAL_TIME_CONTAINER_PADY, padx=10)
            
            # Make sure the container is above the border canvas
            total_container.lift()
            
            # Labels with explicit styling
            label = ttk.Label(
                total_container,
                text=TOTAL_TIME_LABEL_TEXT,
                style="Card.TLabel",
                font=("Segoe UI", 11)
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            self.total_time_label = ttk.Label(
                total_container,
                text=TOTAL_TIME_DEFAULT_TEXT,
                style="Timer.TLabel"
            )
            self.total_time_label.pack(side=tk.RIGHT)
            
        except Exception as e:
            # Fallback to standard frame if card creation fails
            print(f"Warning: Card frame creation failed, using standard frame: {e}")
            self.total_time_frame = ttk.Frame(parent, style="Modern.TFrame")
            self.total_time_frame.pack(fill=tk.X, pady=TOTAL_TIME_FRAME_PADY)
            
            total_container = ttk.Frame(self.total_time_frame, style="Modern.TFrame")
            total_container.pack(fill=tk.X, pady=TOTAL_TIME_CONTAINER_PADY)
            
            ttk.Label(
                total_container,
                text=TOTAL_TIME_LABEL_TEXT,
                style="Modern.TLabel"
            ).pack(side=tk.LEFT)
            
            self.total_time_label = ttk.Label(
                total_container,
                text=TOTAL_TIME_DEFAULT_TEXT,
                style="Timer.TLabel"
            )
            self.total_time_label.pack(side=tk.RIGHT)
    
    def _create_search_bar(self, parent):
        """Create search functionality for programs"""
        try:
            self.search_var = tk.StringVar()
            search_frame = self.create_search_entry(
                parent, 
                self.search_var, 
                SEARCH_PLACEHOLDER,
                self._filter_programs
            )
            search_frame.pack(fill=tk.X, pady=(0, 10))
            
            # Store reference to the entry widget for focus management
            for child in search_frame.winfo_children():
                if isinstance(child, tk.Entry):
                    self.search_entry = child
                    break
                    
        except Exception as e:
            print(f"Warning: Search bar creation failed: {e}")
            # Create a simple fallback search entry
            search_frame = ttk.Frame(parent, style="Modern.TFrame")
            search_frame.pack(fill=tk.X, pady=(0, 10))
            
            self.search_var = tk.StringVar()
            # Use tk.Entry instead of ttk.Entry for better dark mode styling
            entry = tk.Entry(
                search_frame, 
                textvariable=self.search_var,
                bg=ModernStyle.get_card_bg(),
                fg=ModernStyle.get_text_color(),
                insertbackground=ModernStyle.get_text_color(),
                relief="flat",
                bd=1,
                highlightthickness=1,
                highlightbackground=ModernStyle.get_card_border(),
                font=('Segoe UI', 10)
            )
            entry.pack(fill=tk.X, expand=True)
            entry.bind('<KeyRelease>', self._filter_programs)
            
            # Store reference to the entry widget for focus management
            self.search_entry = entry
            
            # Add placeholder functionality
            entry.insert(0, SEARCH_PLACEHOLDER)
            entry.config(foreground=ModernStyle.get_inactive_color())
            
            def on_entry_click(event):
                if entry.get() == SEARCH_PLACEHOLDER:
                    entry.delete(0, tk.END)
                    entry.config(foreground=ModernStyle.get_text_color())
                    
            def on_focus_out(event):
                if entry.get() == '':
                    entry.insert(0, SEARCH_PLACEHOLDER)
                    entry.config(foreground=ModernStyle.get_inactive_color())
                    
            entry.bind('<FocusIn>', on_entry_click)
            entry.bind('<FocusOut>', on_focus_out)
        
    def _filter_programs(self, event=None):
        """Filter programs based on search text"""
        if not hasattr(self, 'program_gui') or not hasattr(self.program_gui, 'program_widgets'):
            return
            
        search_text = self.search_var.get().lower()
        is_empty_search = not search_text or search_text == SEARCH_PLACEHOLDER.lower()
        
        # Store current search state
        self._current_search_text = "" if is_empty_search else search_text
        self._active_search = not is_empty_search
        
        # Use the improved reorder_widgets method which now handles search filtering
        self.program_gui.reorder_widgets(
            self.parent.data_manager.get_current_times(),
            self.parent.data_manager.currently_tracking
        )
        
        # Update canvas scroll region
        self._on_frame_configure()
        
    def has_active_search(self):
        """Check if there's an active search filter"""
        return hasattr(self, '_active_search') and self._active_search
        
    def get_current_search_text(self):
        """Get the current search text"""
        return getattr(self, '_current_search_text', "")
    
    def _create_status(self, parent):
        """Create status display section"""
        self.tracking_status_label = ttk.Label(
            parent,
            text=STATUS_LABEL_DEFAULT_TEXT,
            style="Status.TLabel"
        )
        self.tracking_status_label.pack(pady=STATUS_LABEL_PADY)
        
    def _create_programs_area(self, parent):
        """Create scrollable programs display area with improved styling"""
        # Create canvas and scrollbar container
        scroll_frame = ttk.Frame(parent, style="Modern.TFrame")
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas with modern styling
        self.canvas = tk.Canvas(
            scroll_frame,
            bg=ModernStyle.get_bg_color(),
            highlightthickness=0,
            bd=0
        )
        
        # Use custom scrollbar for better dark mode styling
        self.scrollbar = DarkModeScrollbar(
            scroll_frame,
            command=self.canvas.yview
        )
        
        # Explicitly configure colors to ensure proper initial appearance
        self.scrollbar.configure_colors()
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create frame for programs
        self.programs_frame = ttk.Frame(self.canvas, style="Modern.TFrame")
        
        # Pack components
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Create window in canvas with a default width
        # We'll set a minimal default width to avoid errors when the canvas is not yet sized
        default_width = 400  # Reasonable default width
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.programs_frame,
            anchor=CANVAS_ANCHOR,
            width=default_width
        )
        
        # Configure scrolling
        self.programs_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mousewheel events based on platform
        self._bind_mousewheel()
        
        # Create program GUI manager
        self.program_gui = ProgramGUI(self.parent, self.programs_frame)

    def _bind_mousewheel(self):
        """Bind mousewheel events based on platform"""
        os_name = platform.system()
        
        if os_name == "Windows":
            # Windows uses <MouseWheel> event
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        elif os_name == "Darwin":
            # macOS uses <MouseWheel> event with different scaling
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel_macos)
        else:
            # Linux uses Button-4 and Button-5 for scroll up/down
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux_up)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux_down)
    
    def _on_mousewheel_windows(self, event):
        """Handle mousewheel scrolling on Windows"""
        if not hasattr(self, 'programs_frame') or not hasattr(self, 'canvas'):
            return
            
        # Only scroll if the content is larger than the canvas
        if self.programs_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / MOUSEWHEEL_SCROLL_UNITS)), "units")
    
    def _on_mousewheel_macos(self, event):
        """Handle mousewheel scrolling on macOS"""
        if not hasattr(self, 'programs_frame') or not hasattr(self, 'canvas'):
            return
            
        # macOS uses different scaling
        if self.programs_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
    
    def _on_mousewheel_linux_up(self, event):
        """Handle scroll up on Linux"""
        if not hasattr(self, 'programs_frame') or not hasattr(self, 'canvas'):
            return
            
        if self.programs_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(-1, "units")
    
    def _on_mousewheel_linux_down(self, event):
        """Handle scroll down on Linux"""
        if not hasattr(self, 'programs_frame') or not hasattr(self, 'canvas'):
            return
            
        if self.programs_frame.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(1, "units")

    def _open_settings(self):
        """Open the settings window (singleton)."""
        try:
            if hasattr(self, '_settings_window') and self._settings_window.winfo_exists():
                # If window exists but is withdrawn, deiconify first
                self._settings_window.deiconify()
                self._settings_window.lift()
                return
        except Exception:
            pass  # if window object exists but already destroyed

        self._settings_window = SettingsWindow(
            self.root,
            self.parent
        )
        
    def _on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_canvas_configure(self, event):
        """When the canvas is resized, resize the inner frame to match"""
        if not hasattr(self, 'canvas_window'):
            return
            
        if event and hasattr(event, 'width'):
            width = event.width
            if width > 0:
                self.canvas.itemconfig(self.canvas_window, width=width)
        
    def _on_mousewheel(self, event):
        """Legacy mousewheel handler - kept for backward compatibility"""
        self._on_mousewheel_windows(event)
        
    def update_select_button(self, selecting):
        """Update select window button text based on selection state"""
        if not hasattr(self, 'select_button'):
            return
            
        text = SELECT_WINDOW_ACTIVE_TEXT if selecting else SELECT_WINDOW_BUTTON_TEXT
        color = ModernStyle.get_button_toggle_color() if selecting else ModernStyle.get_success_color()
        self.select_button.configure(text=text, bg=color, activebackground=color)
        
    def update_status(self, text, is_active=True):
        """Update status text with appropriate styling"""
        if not hasattr(self, 'tracking_status_label'):
            return
            
        if is_active:
            self.tracking_status_label.configure(
                text=f"{STATUS_TRACKING_PREFIX}{text}",
                style="Active.TLabel"
            )
        else:
            self.tracking_status_label.configure(
                text=text if text else STATUS_READY_TEXT,
                style="Status.TLabel"
            )
            
    def update_total_time(self, time_text):
        """Update total time display"""
        if hasattr(self, 'total_time_label'):
            self.total_time_label.configure(text=time_text)
        
    def update_pin_button(self, is_pinned):
        """Update pin button appearance based on pin state"""
        if hasattr(self, 'toggle_button'):
            color = ModernStyle.get_button_toggle_color() if is_pinned else ModernStyle.get_inactive_color()
            # Update both background and activebackground to ensure consistent appearance
            self.toggle_button.configure(
                bg=color, 
                activebackground=color,
                # Add relief effect when pinned to make the state more visible
                relief='sunken' if is_pinned else 'flat'
            )
            
            # Update hover event handlers to respect the pinned state
            def on_enter(e):
                # Lighten the button color on hover while maintaining the current state color
                r, g, b = self.root.winfo_rgb(color)
                r = min(65535, r + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
                g = min(65535, g + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
                b = min(65535, b + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
                hover_color = f"#{r//256:02x}{g//256:02x}{b//256:02x}"
                self.toggle_button.config(background=hover_color, activebackground=hover_color)
                
            def on_leave(e):
                self.toggle_button.config(background=color, activebackground=color)
                
            # Unbind any existing hover events and rebind with updated colors
            self.toggle_button.unbind("<Enter>")
            self.toggle_button.unbind("<Leave>")
            self.toggle_button.bind("<Enter>", on_enter)
            self.toggle_button.bind("<Leave>", on_leave)

    def update_ui_for_theme(self):
        """Update UI elements for the current theme"""
        # Update window background
        self.root.configure(bg=ModernStyle.get_bg_color())
        
        # Update canvas background
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=ModernStyle.get_bg_color())
        
        # Update scrollbar colors
        if hasattr(self, 'scrollbar'):
            if isinstance(self.scrollbar, DarkModeScrollbar):
                # Use the scrollbar's built-in method to update colors
                self.scrollbar.configure_colors()
            else:
                # Fallback for standard scrollbar
                self.scrollbar.configure(
                    bg=ModernStyle.get_card_bg(),
                    troughcolor=ModernStyle.get_bg_color(),
                    activebackground=ModernStyle.get_card_border()
                )
        
        # Update button colors
        if hasattr(self, 'select_button'):
            selecting = self.select_button.cget('text') == SELECT_WINDOW_ACTIVE_TEXT
            color = ModernStyle.get_button_toggle_color() if selecting else ModernStyle.get_success_color()
            self.select_button.configure(bg=color, activebackground=color)
        
        # Update pin button
        if hasattr(self, 'toggle_button'):
            is_pinned = self.parent.always_on_top
            color = ModernStyle.get_button_toggle_color() if is_pinned else ModernStyle.get_inactive_color()
            self.toggle_button.configure(bg=color, activebackground=color)
        
        # Update card frames
        if hasattr(self, 'total_time_frame') and hasattr(self.total_time_frame, '_border_canvas_obj'):
            canvas_obj = getattr(self.total_time_frame, '_border_canvas_obj')
            canvas_obj.configure(
                highlightbackground=ModernStyle.get_card_border(),
                bg=ModernStyle.get_card_bg()
            )
        
        # Update program cards
        if hasattr(self, 'program_gui') and hasattr(self.program_gui, 'program_widgets'):
            for program, widgets in self.program_gui.program_widgets.items():
                if 'frame' in widgets and hasattr(widgets['frame'], '_border_canvas_obj'):
                    canvas_obj = getattr(widgets['frame'], '_border_canvas_obj')
                    canvas_obj.configure(
                        highlightbackground=ModernStyle.get_card_border(),
                        bg=ModernStyle.get_card_bg()
                    )
        
        # Update search entry and clear button if they exist
        try:
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Frame):
                            # Look for search entry
                            for grandchild in child.winfo_children():
                                if isinstance(grandchild, tk.Entry):
                                    try:
                                        bg_color = ModernStyle.get_card_bg()
                                        fg_color = ModernStyle.get_text_color()
                                        grandchild.configure(
                                            bg=bg_color,
                                            fg=fg_color,
                                            insertbackground=fg_color,
                                            highlightbackground=ModernStyle.get_card_border()
                                        )
                                    except tk.TclError:
                                        pass
                                # Look for clear button (X) label
                                elif isinstance(grandchild, ttk.Frame):
                                    for button in grandchild.winfo_children():
                                        if isinstance(button, tk.Label) and button.cget("text") == "✕":
                                            try:
                                                button.configure(
                                                    fg=ModernStyle.get_text_color(),
                                                    bg=bg_color  # Match the search entry background
                                                )
                                            except tk.TclError:
                                                pass
        except Exception:
            # Ignore any errors in the search entry update
            pass
        
        # Reapply styles to ensure all ttk widgets are updated
        ModernStyle.apply(self.root)
        
        # Force redraw
        self.root.update_idletasks()

    def show(self):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _clear_search_focus(self, event=None):
        """Clear focus from search entry when clicking elsewhere"""
        # Only process if we have a search entry and the click wasn't on the search entry
        if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            # Get the search entry's parent frame
            search_frame = self.search_entry.master if hasattr(self.search_entry, 'master') else None
            
            # If the click wasn't on the search entry or its parent frame, clear focus
            if event and hasattr(event, 'widget') and event.widget != self.search_entry and event.widget != search_frame:
                self.root.focus_set()  # Set focus to the main window

