# system_tray.py
from PIL import Image, ImageDraw
import pystray
import threading
from version import get_version_string

class SystemTrayIcon:
    """Manages system tray icon and functionality"""
    def __init__(self, parent):
        self.parent = parent
        self._create_icon()
        self.start_tray()
        
    def _create_icon(self):
        """Create system tray icon"""
        # Create a simple icon
        icon_image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(icon_image)
        draw.rectangle([16, 16, 48, 48], fill='blue')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.parent.show_main_window),
            pystray.MenuItem("Exit", self.parent.quit_app)
        )
        
        # Create system tray icon with version in tooltip
        tooltip_text = f"TokiKanri - {get_version_string()}"
        self.icon = pystray.Icon(
            "tokikanri",
            icon_image,
            tooltip_text,
            menu
        )
        
    def start_tray(self):
        """Start system tray in separate thread"""
        self.tray_thread = threading.Thread(
            target=self._run_tray,
            daemon=True
        )
        self.tray_thread.start()
        
    def _run_tray(self):
        """Run system tray icon"""
        try:
            self.icon.run()
        except Exception as e:
            print(f"System tray error: {e}")
            
    def stop(self):
        """Stop system tray icon"""
        if hasattr(self, 'icon'):
            self.icon.stop()
        
        if hasattr(self, 'tray_thread'):
            self.tray_thread.join(timeout=1.0)