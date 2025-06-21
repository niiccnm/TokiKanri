# program_gui.py
import tkinter as tk 
from tkinter import ttk
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
RESET_BUTTON_BG = "#FFA500"
RESET_BUTTON_PADX = (0, 5)
BUTTON_FONT = ('Segoe UI', 12)
BUTTON_WIDTH = 2
BUTTON_HEIGHT = 1
BUTTON_PADX = 6
BUTTON_PADY = 4
CARD_PADDING = 12

class ProgramGUI(BaseWidget):
    """Main GUI for program tracking display"""
    def __init__(self, parent, frame):
        self.parent = parent
        self.programs_frame = frame
        self.program_widgets = {}
        self.last_sorted_programs = [] # To keep track of the last sort order

    @staticmethod
    def _format_program_name(name: str) -> str:
        """Return a user-friendly program name.

        * Renames 'explorer.exe' to 'Windows File Explorer'.
        * Renames 'CLIPStudioPaint.exe' to 'Clip Studio Paint'.
        * Removes the '.exe' suffix from other program names.
        """
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
            
            # Program name with icon (could be added later)
            name_label = ttk.Label(
                program_frame, 
                text=self._format_program_name(program), 
                style="Card.TLabel",
                font=('Segoe UI', 11, 'bold')
            )
            name_label.pack(anchor=tk.W, pady=(0, 5), fill=tk.X)
            
            # Time and progress section
            time_progress_frame_elements = self._create_time_progress_frame_elements(program_frame, program)
            
            self.program_widgets[program] = {
                'frame': program_frame,
                'name_label': name_label,
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
        self._reorder_and_pack_widgets(current_times, currently_tracking)
        self.update_displays(current_times, currently_tracking) # Update values after reordering

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

    def _reorder_and_pack_widgets(self, current_times, currently_tracking):
        """Reorder and pack existing program widgets based on sorted times."""
        sorted_programs = [p for p, _ in sorted(current_times.items(), key=lambda x: x[1], reverse=True)]

        # Check if the order has actually changed
        if sorted_programs == self.last_sorted_programs:
            return # No need to re-pack if order is the same

        # Always unpack all widgets first to ensure clean reordering
        for program in self.program_widgets:
            if program in self.program_widgets and 'frame' in self.program_widgets[program]:
                self.program_widgets[program]['frame'].pack_forget()

        # Pack widgets in the new sorted order
        for program in sorted_programs:
            if program in self.program_widgets:
                self.program_widgets[program]['frame'].pack(fill=tk.X, pady=PROGRAM_FRAME_PADY)
        
        self.last_sorted_programs = sorted_programs[:] # Store current order

        # Update scroll region if canvas exists
        if hasattr(self.programs_frame, 'update_idletasks'):
            self.programs_frame.update_idletasks()

    def reorder_widgets(self, current_times, currently_tracking):
        """Public wrapper to reorder existing program widgets without recreating them.
        This minimizes UI lag when the active program changes or activity state toggles.
        """
        self._reorder_and_pack_widgets(current_times, currently_tracking)

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
                        text=self._format_program_name(program)
                    )
                else:
                    # Reset to normal border
                    if hasattr(frame, '_border_canvas_obj'):
                        canvas = getattr(frame, '_border_canvas_obj')
                        canvas.configure(highlightbackground=ModernStyle.get_card_border(), highlightthickness=1)
                    
                    # Set normal label style
                    widgets['name_label'].configure(
                        style="Card.TLabel", 
                        text=self._format_program_name(program)
                    )
        
        # Force update
        if hasattr(self.programs_frame, 'update_idletasks'):
            self.programs_frame.update_idletasks()
