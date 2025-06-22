# logger.py
import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
import sys
import time
import codecs

class Logger:
    """Application logging management"""
    def __init__(self, name="TokiKanri"):
        self.logger = logging.getLogger(name)
        
        # Determine the base directory of the application
        if getattr(sys, 'frozen', False):
            # If the application is bundled by PyInstaller
            self._base_dir = Path(sys.executable).parent
        else:
            # If running as a script
            self._base_dir = Path(os.path.abspath(os.path.dirname(__file__)))
            
        self.setup_logger()

    def setup_logger(self):
        """Configure logger settings"""
        # Prevent adding handlers multiple times
        if self.logger.handlers:
            return
        self.logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        log_dir = self._base_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        # Create formatters
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # File handler (with rotation) - using UTF-8 encoding
        log_file = log_dir / "tokikanri.log"
        file_handler = UnicodeRotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)

        # Console handler with UTF-8 encoding
        console_handler = UnicodeStreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message, exc_info=True):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message, exc_info=True):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)

    @staticmethod
    def format_error(e):
        """Format exception for logging"""
        import traceback
        return f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

    def get_base_dir(self):
        """Return the base directory of the application."""
        return self._base_dir


class UnicodeRotatingFileHandler(RotatingFileHandler):
    """A RotatingFileHandler that ensures UTF-8 encoding"""
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding='utf-8', delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)


class UnicodeStreamHandler(logging.StreamHandler):
    """A StreamHandler that ensures proper Unicode handling"""
    def __init__(self, stream=None):
        if stream is None:
            stream = sys.stdout
        super().__init__(stream)
        
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Safely encode and decode for console output
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # If console can't handle the encoding, use a safe representation
                safe_msg = msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)
