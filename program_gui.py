# program_gui.py
import tkinter as tk 
from tkinter import ttk, simpledialog
from ui_components import ModernStyle, BaseWidget
from utils import TimeFormatter

# Constants for ProgramGUI
NO_PROGRAMS_TEXT = "No programs tracked yet"
NO_PROGRAMS_PADY = 20
PROGRAM_FRAME_PADY = 10
TIME_PROGRESS_FRAME_PADY = (5, 0)
PROGRESS_BAR_LENGTH = 150
PROGRESS_BAR_PADX = 10
RESET_BUTTON_TEXT = "⟳"
REMOVE_BUTTON_TEXT = "×"
EDIT_BUTTON_TEXT = "✏️"  # Standard pencil emoji instead of ✎
RESET_BUTTON_BG = "#FFA500"
EDIT_BUTTON_BG = "#4A90E2"
RESET_BUTTON_PADX = (0, 5)
EDIT_BUTTON_PADX = 5
BUTTON_FONT = ('Segoe UI', 12)
BUTTON_WIDTH = 2
BUTTON_HEIGHT = 1
BUTTON_PADX = 6
BUTTON_PADY = 4
CARD_PADDING = 12

class CustomNameDialog(tk.Toplevel):
    """Custom dialog for editing program display names with modern styling"""
    
    def __init__(self, parent, program_name, current_name=None):
        super().__init__(parent)
        self.result = None
        self.program_name = program_name
        self.current_name = current_name
        
        # Configure window
        self.title("Edit Program Name")
        self.configure(bg=ModernStyle.get_bg_color())
        self.resizable(False, False)
        self.transient(parent)  # Set to be on top of the parent window
        self.grab_set()  # Make window modal
        
        # Position window near parent
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Create content
        self._create_widgets()
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Set focus on entry
        self.entry.focus_set()
        
        # Wait for window to be destroyed
        self.wait_window()
    
    def _create_widgets(self):
        """Create the dialog widgets"""
        # Main frame with padding
        main_frame = ttk.Frame(self, style="Modern.TFrame")
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Header label
        header_label = ttk.Label(
            main_frame, 
            text=f"Edit name for '{self.program_name}'",
            style="Modern.TLabel",
            font=('Segoe UI', 11, 'bold')
        )
        header_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Name entry
        entry_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        entry_frame.pack(fill=tk.X, pady=(0, 15))
        
        name_label = ttk.Label(
            entry_frame, 
            text="Display name:",
            style="Modern.TLabel"
        )
        name_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Custom styled entry
        self.entry = tk.Entry(
            entry_frame,
            bg=ModernStyle.get_input_bg_color(),
            fg=ModernStyle.get_text_color(),
            insertbackground=ModernStyle.get_text_color(),  # Cursor color
            relief=tk.FLAT,
            font=('Segoe UI', 11),
            width=30
        )
        self.entry.pack(fill=tk.X, ipady=5)
        
        # Add border to entry
        entry_border_frame = tk.Frame(
            entry_frame,
            bg=ModernStyle.get_accent_color(),
            height=2
        )
        entry_border_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Set initial value
        if self.current_name:
            self.entry.insert(0, self.current_name)
            self.entry.select_range(0, tk.END)
        
        # Bind Enter key
        self.entry.bind("<Return>", self._on_ok)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame, style="Modern.TFrame")
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Reset to default button
        reset_btn = BaseWidget().create_button(
            button_frame,
            text="Reset to Default",
            command=self._on_reset,
            bg_color=ModernStyle.get_inactive_color(),
            font=('Segoe UI', 10),
            padx=10,
            pady=5
        )
        reset_btn.pack(side=tk.LEFT)
        
        # OK and Cancel buttons
        cancel_btn = BaseWidget().create_button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            bg_color=ModernStyle.get_inactive_color(),
            font=('Segoe UI', 10),
            padx=10,
            pady=5
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        ok_btn = BaseWidget().create_button(
            button_frame,
            text="Save",
            command=self._on_ok,
            bg_color=ModernStyle.get_accent_color(),
            font=('Segoe UI', 10, 'bold'),
            padx=10,
            pady=5
        )
        ok_btn.pack(side=tk.RIGHT)
    
    def _on_ok(self, event=None):
        """Handle OK button click"""
        self.result = self.entry.get()
        self.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.destroy()
    
    def _on_reset(self):
        """Handle Reset to Default button click"""
        self.result = ""  # Empty string means reset to default
        self.destroy()

class ProgramGUI(BaseWidget):
    """Main GUI for program tracking display"""
    def __init__(self, parent, frame):
        self.parent = parent
        self.programs_frame = frame
        self.program_widgets = {}
        self.last_sorted_programs = [] # To keep track of the last sort order

    @staticmethod
    def _format_program_name(name: str, custom_name: str | None = None) -> str:
        """Return a user-friendly program name.

        * Uses custom name if provided
        * Renames 'explorer.exe' to 'Windows File Explorer'.
        * Renames 'CLIPStudioPaint.exe' to 'Clip Studio Paint'.
        * Removes the '.exe' suffix from other program names.
        """
        # If custom name is provided, use it
        if custom_name and custom_name.strip():
            return custom_name
            
        lower = name.lower()
        if lower in ('explorer.exe', 'explorer'):
            formatted = 'Windows File Explorer'
        elif lower == 'clipstudiopaint.exe':
            formatted = 'Clip Studio Paint'
        elif lower == 'code.exe':
            formatted = 'VS Code'
        elif lower == 'dnplayer.exe':
            formatted = 'LDPlayer'
        else:
            formatted = name[:-4] if lower.endswith('.exe') else name

        # Capitalize first character if it is lowercase
        if formatted and formatted[0].islower():
            formatted = formatted[0].upper() + formatted[1:]
        return formatted
        
    def create_program_widgets(self, tracked_programs, current_times, currently_tracking):
        """Create and update program display widgets.
        This method is for adding/removing programs and initial setup.
        It also establishes the initial sort order.
        """
        # Identify programs to remove
        programs_to_remove = [p for p in self.program_widgets if p not in tracked_programs]
        for program in programs_to_remove:
            self.program_widgets[program]['frame'].destroy()
            del self.program_widgets[program]

        # Identify programs to add
        programs_to_add = [p for p in tracked_programs if p not in self.program_widgets]
        for program in programs_to_add:
            # Create a card-like frame for each program
            program_frame = self.create_card_frame(self.programs_frame)
            program_frame.configure(padding=CARD_PADDING)
            
            # Program name container with name and edit button
            name_container = ttk.Frame(program_frame, style="Card.TFrame")
            name_container.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
            
            # Get custom name if available
            custom_name = self.parent.data_manager.get_display_name(program)
            
            # Create a horizontal container for name and edit button
            name_edit_container = ttk.Frame(name_container, style="Card.TFrame")
            name_edit_container.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Program name with icon (could be added later)
            name_label = ttk.Label(
                name_edit_container, 
                text=self._format_program_name(program, custom_name), 
                style="Card.TLabel",
                font=('Segoe UI', 11, 'bold')
            )
            name_label.pack(side=tk.LEFT)
            
            # Create edit button - we'll control visibility with a variable
            edit_visible = tk.BooleanVar(value=False)
            
            # Create edit button frame to reserve space
            edit_frame = ttk.Frame(name_edit_container, width=30, height=30, style="Card.TFrame")
            edit_frame.pack(side=tk.LEFT, padx=EDIT_BUTTON_PADX)
            edit_frame.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
            
            # Create edit button label
            edit_label = ttk.Label(
                edit_frame,
                text=EDIT_BUTTON_TEXT,
                style="Card.TLabel",
                font=('Segoe UI', 14),  # Larger font size
                cursor="hand2",
                foreground=ModernStyle.get_text_color(),
                anchor="center",  # Center the text in the label
                padding=(0, 0, 0, 0)  # Remove any internal padding
            )
            
            # Function to show/hide edit button - create a closure for this specific program
            def make_update_visibility(label, visible_var):
                def update():
                    if visible_var.get():
                        label.pack(fill=tk.BOTH, expand=True)
                    else:
                        label.pack_forget()
                return update
                
            update_edit_visibility = make_update_visibility(edit_label, edit_visible)
            
            # Initial state - hidden
            update_edit_visibility()
            
            # Bind click event to the label
            edit_label.bind("<Button-1>", lambda e, p=program: self._edit_program_name(p))
            
            # Setup hover events with delay to prevent flickering - create closures for this specific program
            def make_hover_handlers(container, visible_var, update_func, prog_name):
                timer_ref = {'value': None}  # Use dict to allow modification in closure
                
                def on_enter(e):
                    # Cancel any pending leave timer
                    if timer_ref['value'] is not None:
                        container.after_cancel(timer_ref['value'])
                        timer_ref['value'] = None
                    
                    # Set visible and update
                    visible_var.set(True)
                    
                    # Make sure the edit button is visible with good contrast in both light and dark mode
                    if ModernStyle.is_dark_mode():
                        self.program_widgets[prog_name]['edit_label'].configure(foreground="#FFFFFF")  # White in dark mode
                    else:
                        self.program_widgets[prog_name]['edit_label'].configure(foreground="#333333")  # Dark gray in light mode
                        
                    update_func()
                
                def on_leave(e):
                    # Use timer to delay hiding to prevent flickering
                    if timer_ref['value'] is not None:
                        container.after_cancel(timer_ref['value'])
                    timer_ref['value'] = container.after(100, lambda: (visible_var.set(False), update_func()))
                    
                return on_enter, on_leave, timer_ref
            
            # Create hover handlers for this specific program
            on_enter, on_leave, timer_ref = make_hover_handlers(
                name_edit_container, 
                edit_visible, 
                update_edit_visibility,
                program
            )
            
            # Bind hover events to both the name container and edit button
            name_edit_container.bind("<Enter>", on_enter)
            name_edit_container.bind("<Leave>", on_leave)
            edit_label.bind("<Enter>", on_enter)
            edit_label.bind("<Leave>", on_leave)
            
            # Time and progress section
            time_progress_frame_elements = self._create_time_progress_frame_elements(program_frame, program)
            
            # Store everything in the program_widgets dictionary
            self.program_widgets[program] = {
                'frame': program_frame,
                'name_label': name_label,
                'name_container': name_container,
                'name_edit_container': name_edit_container,
                'edit_frame': edit_frame,
                'edit_label': edit_label,
                'edit_visible': edit_visible,
                'timer_ref': timer_ref,
                'update_visibility': update_edit_visibility,
                'time_label': time_progress_frame_elements['time_label'],
                'progress': time_progress_frame_elements['progress']
            }
            
        # If no programs, display message
        if not tracked_programs:
            # Check if "No programs tracked yet" label already exists
            if not any(isinstance(w, ttk.Label) and w.cget("text") == NO_PROGRAMS_TEXT for w in self.programs_frame.winfo_children()):
                ttk.Label(self.programs_frame, text=NO_PROGRAMS_TEXT, style="Modern.TLabel").pack(pady=NO_PROGRAMS_PADY)
            self.last_sorted_programs = []
            return
        else:
            # Remove "No programs tracked yet" label if it exists
            for widget in self.programs_frame.winfo_children():
                if isinstance(widget, ttk.Label) and widget.cget("text") == NO_PROGRAMS_TEXT:
                    widget.destroy()

        # Now, reorder and pack all existing widgets
        # This will ensure widgets are sorted by time spent and properly displayed
        self.reorder_widgets(current_times, currently_tracking)
        self.update_displays(current_times, currently_tracking) # Update values after reordering
    

    def _adjust_color(self, hex_color, factor):
        """Adjust color brightness by a factor"""
        # Convert hex to RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Adjust brightness
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def _create_time_progress_frame_elements(self, parent, program):
        """Helper to create the time, progress bar, and buttons for a program."""
        time_progress_frame = ttk.Frame(parent, style="Card.TFrame")
        time_progress_frame.pack(fill=tk.X, pady=TIME_PROGRESS_FRAME_PADY)
        
        # Time display with larger font
        time_label = ttk.Label(time_progress_frame, text="--:--", style="Timer.TLabel")
        time_label.pack(side=tk.LEFT)
        
        # Progress bar with rounded corners (via styling)
        progress = ttk.Progressbar(
            time_progress_frame,
            style="Modern.Horizontal.TProgressbar",
            length=PROGRESS_BAR_LENGTH,
            mode='determinate'
        )
        progress.pack(side=tk.LEFT, padx=PROGRESS_BAR_PADX, fill=tk.X, expand=True)
        
        # Button container for alignment
        button_frame = ttk.Frame(time_progress_frame, style="Card.TFrame")
        button_frame.pack(side=tk.RIGHT)
        
        # Reset button with improved styling
        reset_btn = self.create_button(
            button_frame,
            text=RESET_BUTTON_TEXT,
            command=lambda p=program: self.parent.reset_timer(p),
            bg_color=RESET_BUTTON_BG,
            font=BUTTON_FONT,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY
        )
        reset_btn.pack(side=tk.LEFT, padx=RESET_BUTTON_PADX)
        
        # Remove button with improved styling
        remove_btn = self.create_button(
            button_frame,
            text=REMOVE_BUTTON_TEXT,
            command=lambda p=program: self.parent.remove_program(p),
            bg_color=ModernStyle.get_button_remove_color(),
            font=BUTTON_FONT,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            padx=BUTTON_PADX,
            pady=BUTTON_PADY
        )
        remove_btn.pack(side=tk.LEFT)
        
        return {'time_label': time_label, 'progress': progress}
        
    def _edit_program_name(self, program):
        """Open a dialog to edit the program name"""
        # Get current display name or default formatted name
        current_name = self.parent.data_manager.get_display_name(program)
        default_name = self._format_program_name(program)
        
        # Use custom dialog instead of simpledialog
        dialog = CustomNameDialog(
            self.parent.root,
            program,
            current_name
        )
        
        new_name = dialog.result
        
        # If user didn't cancel, update the name
        if new_name is not None:  # None means user canceled
            # Update the name in data manager
            self.parent.data_manager.set_display_name(program, new_name)
            
            # Update the display
            if program in self.program_widgets:
                custom_name = self.parent.data_manager.get_display_name(program)
                self.program_widgets[program]['name_label'].configure(
                    text=self._format_program_name(program, custom_name)
                )
                
                # Update status display if this is the currently tracking program
                if self.parent.data_manager.currently_tracking == program:
                    self.parent._update_status(
                        self.parent.activity_tracker.is_active, 
                        program
                    )

    def reorder_widgets(self, current_times, currently_tracking):
        """Public wrapper to reorder existing program widgets without recreating them.
        This minimizes UI lag when the active program changes or activity state toggles.
        """
        # Check if there's an active search in the main window
        has_active_search = False
        search_text = ""
        
        # The parent is ProgramTokiKanri, and main_window is an attribute of it
        if hasattr(self.parent, 'main_window'):
            has_active_search = getattr(self.parent.main_window, '_active_search', False)
            search_text = getattr(self.parent.main_window, '_current_search_text', "")
        
        # Always get the sorted programs list (by time used)
        # Use a more efficient sorting approach
        sorted_items = sorted(current_times.items(), key=lambda x: x[1], reverse=True)
        sorted_programs = [p for p, _ in sorted_items]
        
        # If there's an active search, filter the programs
        if has_active_search and search_text:
            # First, unpack all widgets to start fresh
            for program in self.program_widgets:
                if 'frame' in self.program_widgets[program]:
                    self.program_widgets[program]['frame'].pack_forget()
            
            # Filter and pack programs in the sorted order (already sorted by time)
            visible_programs = []
            for program in sorted_programs:
                if program in self.program_widgets:
                    widgets = self.program_widgets[program]
                    if 'frame' not in widgets:
                        continue
                    
                    # Get display name (including custom name if set)
                    custom_name = self.parent.data_manager.get_display_name(program)
                    program_name = self._format_program_name(program, custom_name).lower()
                    
                    # Only show programs that match the search
                    if search_text in program_name:
                        widgets['frame'].pack(fill=tk.X, pady=10)
                        visible_programs.append(program)
            
            # Update the last sorted programs to match what we've just done
            self.last_sorted_programs = visible_programs
            
            # Update displays without reordering again
            self.update_displays(current_times, currently_tracking)
        else:
            # Always unpack all widgets first to ensure clean ordering
            for program in self.program_widgets:
                if 'frame' in self.program_widgets[program]:
                    self.program_widgets[program]['frame'].pack_forget()
            
            # Pack widgets in the new sorted order (highest time to lowest)
            for program in sorted_programs:
                if program in self.program_widgets:
                    self.program_widgets[program]['frame'].pack(fill=tk.X, pady=PROGRAM_FRAME_PADY)
            
            # Store current order
            self.last_sorted_programs = sorted_programs[:] 
            
            # Update scroll region if canvas exists
            if hasattr(self.programs_frame, 'update_idletasks'):
                self.programs_frame.update_idletasks()
            
            # Always update the display values
            self.update_displays(current_times, currently_tracking)

    def update_displays(self, current_times, currently_tracking):
        """Update all program displays (time, progress, active style).
        This method does NOT reorder widgets.
        """
        total_time = sum(current_times.values())
        
        for program, widgets in self.program_widgets.items():
            if program in current_times:  # Only update if program still exists
                duration = current_times[program]
                
                # Update time label
                widgets['time_label'].configure(
                    text=TimeFormatter.format_time(duration))
                
                # Update progress bar
                if total_time > 0:
                    widgets['progress']['value'] = \
                        (duration / total_time) * 100
                else:
                    widgets['progress']['value'] = 0 # Handle division by zero
                
                # Update style based on tracking status
                is_active = program == currently_tracking
                
                # Get custom name if available
                custom_name = self.parent.data_manager.get_display_name(program)
                
                # Visual indication of active program
                frame = widgets['frame']
                if is_active:
                    # Highlight active program card
                    if hasattr(frame, '_border_canvas_obj'):
                        canvas = getattr(frame, '_border_canvas_obj')
                        canvas.configure(highlightbackground=ModernStyle.get_card_active_border(), highlightthickness=2)
                    
                    # Set active label style
                    widgets['name_label'].configure(
                        style="Active.TLabel", 
                        text=self._format_program_name(program, custom_name)
                    )
                else:
                    # Reset to normal border
                    if hasattr(frame, '_border_canvas_obj'):
                        canvas = getattr(frame, '_border_canvas_obj')
                        canvas.configure(highlightbackground=ModernStyle.get_card_border(), highlightthickness=1)
                    
                    # Set normal label style
                    widgets['name_label'].configure(
                        style="Card.TLabel", 
                        text=self._format_program_name(program, custom_name)
                    )
        
        # Force update
        if hasattr(self.programs_frame, 'update_idletasks'):
            self.programs_frame.update_idletasks()
