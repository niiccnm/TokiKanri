# ui_components.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any, Union

class ModernStyle:
    """Class for managing application styling"""
    # Color scheme - Light Mode
    BG_COLOR = "#ffffff"
    ACCENT_COLOR = "#007AFF"
    TEXT_COLOR = "#333333"
    INACTIVE_COLOR = "#9CA3AF"
    SUCCESS_COLOR = "#10B981"
    BUTTON_REMOVE_COLOR = "#FF4444"
    BUTTON_TOGGLE_COLOR = "#6366F1"
    
    # Mini window colors - These will remain the same in both modes
    MINI_ACTIVE_BG = "#10B981"
    MINI_INACTIVE_BG = "#9CA3AF"
    MINI_NO_TRACKING_BG = "#FF4444"
    
    # Card styling - Light Mode
    CARD_BG = "#F9FAFB"
    CARD_BORDER = "#E5E7EB"
    CARD_SHADOW = "#0000001A"
    CARD_ACTIVE_BORDER = "#10B981"
    
    # Dark Mode Colors
    DARK_BG_COLOR = "#1E1E2E"
    DARK_ACCENT_COLOR = "#007AFF"
    DARK_TEXT_COLOR = "#E5E7EB"
    DARK_INACTIVE_COLOR = "#6B7280"
    DARK_SUCCESS_COLOR = "#10B981"
    DARK_BUTTON_REMOVE_COLOR = "#FF4444"
    DARK_BUTTON_TOGGLE_COLOR = "#6366F1"
    
    # Card styling - Dark Mode
    DARK_CARD_BG = "#2D2D3F"
    DARK_CARD_BORDER = "#4B4B63"
    DARK_CARD_SHADOW = "#0000004D"
    DARK_CARD_ACTIVE_BORDER = "#10B981"
    
    # Hover colors
    BUTTON_HOVER_LIGHTEN = 20  # Amount to lighten button colors on hover
    
    # Current mode
    _dark_mode = False
    
    @classmethod
    def toggle_dark_mode(cls, enable_dark_mode=None):
        """Toggle or set dark mode"""
        if enable_dark_mode is not None:
            cls._dark_mode = enable_dark_mode
        else:
            cls._dark_mode = not cls._dark_mode
        return cls._dark_mode
    
    @classmethod
    def is_dark_mode(cls):
        """Check if dark mode is enabled"""
        return cls._dark_mode
    
    @classmethod
    def get_bg_color(cls):
        return cls.DARK_BG_COLOR if cls._dark_mode else cls.BG_COLOR
    
    @classmethod
    def get_accent_color(cls):
        return cls.DARK_ACCENT_COLOR if cls._dark_mode else cls.ACCENT_COLOR
    
    @classmethod
    def get_text_color(cls):
        return cls.DARK_TEXT_COLOR if cls._dark_mode else cls.TEXT_COLOR
    
    @classmethod
    def get_inactive_color(cls):
        return cls.DARK_INACTIVE_COLOR if cls._dark_mode else cls.INACTIVE_COLOR
    
    @classmethod
    def get_success_color(cls):
        return cls.DARK_SUCCESS_COLOR if cls._dark_mode else cls.SUCCESS_COLOR
    
    @classmethod
    def get_button_remove_color(cls):
        return cls.DARK_BUTTON_REMOVE_COLOR if cls._dark_mode else cls.BUTTON_REMOVE_COLOR
    
    @classmethod
    def get_button_toggle_color(cls):
        return cls.DARK_BUTTON_TOGGLE_COLOR if cls._dark_mode else cls.BUTTON_TOGGLE_COLOR
    
    @classmethod
    def get_card_bg(cls):
        return cls.DARK_CARD_BG if cls._dark_mode else cls.CARD_BG
    
    @classmethod
    def get_card_border(cls):
        return cls.DARK_CARD_BORDER if cls._dark_mode else cls.CARD_BORDER
    
    @classmethod
    def get_card_shadow(cls):
        return cls.DARK_CARD_SHADOW if cls._dark_mode else cls.CARD_SHADOW
    
    @classmethod
    def get_card_active_border(cls):
        return cls.DARK_CARD_ACTIVE_BORDER if cls._dark_mode else cls.CARD_ACTIVE_BORDER
    
    @classmethod
    def apply(cls, root):
        style = ttk.Style()
        
        bg_color = cls.get_bg_color()
        text_color = cls.get_text_color()
        card_bg = cls.get_card_bg()
        accent_color = cls.get_accent_color()
        success_color = cls.get_success_color()
        
        styles = {
            "Modern.TFrame": {"background": bg_color},
            "Card.TFrame": {
                "background": card_bg,
            },
            "Modern.TLabel": {
                "background": bg_color,
                "foreground": text_color,
                "padding": 5
            },
            "Card.TLabel": {
                "background": card_bg,
                "foreground": text_color,
                "padding": 5
            },
            "Header.TLabel": {
                "font": ("Segoe UI", 14, "bold"),
                "background": bg_color,
                "foreground": text_color
            },
            "Subheader.TLabel": {
                "font": ("Segoe UI", 12),
                "background": bg_color,
                "foreground": text_color
            },
            "Timer.TLabel": {
                "background": card_bg,
                "foreground": text_color,
                "font": ("Segoe UI", 14, "bold")
            },
            "Status.TLabel": {
                "background": bg_color,
                "foreground": accent_color,
                "font": ("Segoe UI", 10)
            },
            "Active.TLabel": {
                "background": card_bg,
                "foreground": success_color,
                "font": ("Segoe UI", 10, "bold")
            },
            "Modern.Horizontal.TProgressbar": {
                "background": accent_color,
                "troughcolor": cls.DARK_CARD_BG if cls._dark_mode else "#F3F4F6",
                "borderwidth": 0,
                "thickness": 8
            },
            "Search.TEntry": {
                "font": ("Segoe UI", 10),
                "fieldbackground": cls.DARK_CARD_BG if cls._dark_mode else "#F3F4F6"
            }
        }
        
        for style_name, style_options in styles.items():
            style.configure(style_name, **style_options)

class BaseWidget:
    """Base class for custom widgets"""
    @staticmethod
    def create_button(parent, text: str, command: Callable, bg_color: str, 
                     width: Optional[int] = None, height: Optional[int] = None, 
                     font=('Segoe UI', 10), padx: int = 10, pady: int = 5, 
                     corner_radius: int = 8) -> tk.Button:
        """Create a modern-looking button with hover effects"""
        # For tkinter buttons, we need to handle None values for width/height
        # by omitting those parameters entirely
        button_kwargs = {
            "text": text,
            "command": command,
            "bg": bg_color,
            "fg": 'white',
            "activebackground": bg_color,
            "activeforeground": 'white',
            "relief": 'flat',
            "borderwidth": 0,
            "padx": padx,
            "pady": pady,
            "font": font,
            "cursor": "hand2"  # Add hand cursor by default
        }
        
        # Only add width/height if they are not None
        if width is not None:
            button_kwargs["width"] = width
        if height is not None:
            button_kwargs["height"] = height
            
        button = tk.Button(parent, **button_kwargs)
        
        # Add hover effect
        def on_enter(e):
            # Lighten the button color on hover
            r, g, b = parent.winfo_rgb(bg_color)
            r = min(65535, r + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
            g = min(65535, g + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
            b = min(65535, b + ModernStyle.BUTTON_HOVER_LIGHTEN * 256)
            hover_color = f"#{r//256:02x}{g//256:02x}{b//256:02x}"
            button.config(background=hover_color, activebackground=hover_color)
            
        def on_leave(e):
            button.config(background=bg_color, activebackground=bg_color)
            
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
        
    @staticmethod
    def create_card_frame(parent, padding: int = 10) -> ttk.Frame:
        """Create a card-like frame with subtle border and shadow effect"""
        # Main card frame
        card = ttk.Frame(parent, style="Card.TFrame")
        
        # Apply visual styling using border and background
        card.configure(borderwidth=1, relief="solid")
        
        # We need to manually set the border color since ttk doesn't support this directly
        # This is a workaround using canvas as a border
        def configure_card_border(event):
            card.update_idletasks()
            width = card.winfo_width()
            height = card.winfo_height()
            
            # Store the canvas as an attribute of the frame
            if not hasattr(card, '_border_canvas_obj'):
                border_canvas = tk.Canvas(
                    card, 
                    highlightthickness=1,
                    highlightbackground=ModernStyle.get_card_border(),
                    bd=0
                )
                border_canvas.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Put the canvas behind all other widgets
                # Don't use lower() without arguments as it causes errors
                for child in card.winfo_children():
                    if child != border_canvas:
                        child.lift()
                
                # Store the canvas object as an attribute
                setattr(card, '_border_canvas_obj', border_canvas)
            else:
                # Update existing canvas dimensions
                canvas_obj = getattr(card, '_border_canvas_obj')
                canvas_obj.configure(width=width, height=height)
                canvas_obj.configure(highlightbackground=ModernStyle.get_card_border())
        
        card.bind("<Configure>", configure_card_border)
        
        return card
    
    @staticmethod
    def create_search_entry(parent, var: tk.StringVar, 
                           placeholder: str = "Search...", 
                           command: Optional[Callable[[Any], None]] = None) -> ttk.Frame:
        """Create a modern search entry with placeholder text"""
        frame = ttk.Frame(parent, style="Modern.TFrame")
        
        # Create and configure the entry widget using tk.Entry instead of ttk.Entry
        # Use explicit colors for dark mode compatibility
        if ModernStyle.is_dark_mode():
            bg_color = "#2D2D3F"  # Dark card background
            fg_color = "#E5E7EB"  # Light text
            highlight_color = "#4B4B63"  # Dark border
        else:
            bg_color = "#F9FAFB"  # Light card background
            fg_color = "#333333"  # Dark text
            highlight_color = "#E5E7EB"  # Light border
            
        entry = tk.Entry(
            frame, 
            textvariable=var, 
            bg=bg_color,
            fg=fg_color,
            insertbackground=fg_color,
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=highlight_color,
            font=('Segoe UI', 10)
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Add placeholder functionality
        entry.insert(0, placeholder)
        entry.config(foreground=ModernStyle.get_inactive_color())
        
        def on_entry_click(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(foreground=fg_color)
                
        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder)
                entry.config(foreground=ModernStyle.get_inactive_color())
                
        entry.bind('<FocusIn>', on_entry_click)
        entry.bind('<FocusOut>', on_focus_out)
        
        if command:
            entry.bind('<KeyRelease>', command)
        
        # Add search icon button
        search_btn = BaseWidget.create_button(
            frame,
            text="🔍",
            command=lambda: command(None) if command else None,
            bg_color=ModernStyle.get_accent_color(),
            padx=5,
            pady=2
        )
        search_btn.pack(side=tk.RIGHT)
        
        return frame
