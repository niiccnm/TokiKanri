# utils.py
import time

class TimeFormatter:
    """Utility class for time formatting"""
    @staticmethod
    def format_time(seconds):
        """Format seconds into HH:MM:SS or MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

class Timer:
    """Utility class for managing timing operations"""
    def __init__(self):
        self.start_time = None
        
    def start(self):
        """Start timer"""
        self.start_time = time.time()
        
    def stop(self):
        """Stop timer and return elapsed time"""
        if self.start_time is None:
            return 0
            
        elapsed = time.time() - self.start_time
        self.start_time = None
        return elapsed
        
    def get_elapsed(self):
        """Get elapsed time without stopping timer"""
        if self.start_time is None:
            return 0
            
        return time.time() - self.start_time