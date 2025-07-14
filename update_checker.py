"""
Update checker module for TokiKanri application.

This module provides functionality to check for updates by comparing the current version
with the latest release on GitHub.
"""

import json
import logging
import platform
import re
import ssl
import tkinter as tk
from tkinter import messagebox
from urllib.request import Request, urlopen
from urllib.error import URLError

from version import VERSION, VERSION_TUPLE
from update_config import GITHUB_API_URL, GITHUB_OWNER, GITHUB_REPO

logger = logging.getLogger(__name__)

# Default user agent
DEFAULT_USER_AGENT = "TokiKanri-UpdateChecker"


class UpdateChecker:
    """Class for checking application updates from GitHub releases."""
    
    def __init__(self, user_agent=DEFAULT_USER_AGENT, auto_check=True):
        """Initialize the update checker.
        
        Args:
            user_agent (str, optional): User agent for API requests. Defaults to DEFAULT_USER_AGENT.
            auto_check (bool, optional): Whether to check for updates automatically. Defaults to True.
        """
        self.user_agent = user_agent
        self.api_url = GITHUB_API_URL
        self.latest_version = None
        self.latest_version_tuple = None
        self.download_url = None
        self.release_notes = None
        
        if auto_check:
            self.check_for_updates(silent=True)
    
    def check_for_updates(self, silent=False):
        """Check for updates from GitHub.
        
        Args:
            silent (bool, optional): If True, suppress error messages. Defaults to False.
            
        Returns:
            bool: True if updates are available, False otherwise
        """
        try:
            # Create a request with user agent
            req = Request(self.api_url)
            req.add_header("User-Agent", self.user_agent)
            
            # Create SSL context
            context = ssl.create_default_context()
            
            # Make the request
            with urlopen(req, context=context, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
                
                # Extract version from tag_name (e.g., "v1.0.0" -> "1.0.0")
                version_str = data["tag_name"]
                if version_str.startswith("v"):
                    version_str = version_str[1:]
                    
                # Store release information
                self.latest_version = version_str
                self.latest_version_tuple = tuple(map(int, version_str.split('.')))
                self.release_notes = data["body"]
                
                # Find the appropriate asset for the current platform
                assets = data["assets"]
                for asset in assets:
                    # For Windows, look for .exe files
                    if platform.system() == "Windows" and asset["name"].endswith(".exe"):
                        self.download_url = asset["browser_download_url"]
                        break
                
                # If no specific platform asset found, use the first asset or zip file
                if not self.download_url and assets:
                    for asset in assets:
                        if asset["name"].endswith(".zip"):
                            self.download_url = asset["browser_download_url"]
                            break
                    if not self.download_url:
                        self.download_url = assets[0]["browser_download_url"]
                
                # Fall back to the general release URL if no assets
                if not self.download_url:
                    self.download_url = data["html_url"]
                
                # Compare versions
                current_version_tuple = VERSION_TUPLE
                is_update_available = self.latest_version_tuple > current_version_tuple
                
                logger.info(f"Current version: {VERSION}, Latest version: {self.latest_version}")
                logger.info(f"Update available: {is_update_available}")
                
                return is_update_available
                
        except URLError as e:
            if not silent:
                logger.error(f"Error checking for updates: {str(e)}")
            return False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if not silent:
                logger.error(f"Error parsing update information: {str(e)}")
            return False
        except Exception as e:
            if not silent:
                logger.error(f"Unexpected error during update check: {str(e)}")
            return False
    
    def show_update_dialog(self, parent=None):
        """Show a dialog with update information if updates are available.
        
        Args:
            parent (tk.Widget, optional): Parent widget for the dialog. Defaults to None.
            
        Returns:
            bool: True if user chose to update, False otherwise
        """
        if not self.latest_version or not self.download_url or not self.latest_version_tuple:
            return False
            
        if VERSION_TUPLE >= self.latest_version_tuple:
            return False
            
        # Format release notes (limit to a reasonable length)
        notes = self.release_notes or ""  # Ensure release_notes is not None
        if len(notes) > 500:  # Limit to first 500 chars + ellipsis
            notes = notes[:500] + "...\n(See full release notes on GitHub)"
        
        message = (
            f"A new version of TokiKanri is available!\n\n"
            f"Current version: {VERSION}\n"
            f"Latest version: {self.latest_version}\n\n"
            f"Release Notes:\n{notes}\n\n"
            f"Would you like to download the update now?"
        )
        
        # Show message box with update information
        if parent:
            result = messagebox.askyesno("Update Available", message, parent=parent)
        else:
            result = messagebox.askyesno("Update Available", message)
            
        if result and self.download_url:
            self.open_download_page()
            return True
        
        return False
    
    def open_download_page(self):
        """Open the download URL in the default web browser."""
        import webbrowser
        if self.download_url:
            webbrowser.open(self.download_url)
        
def check_for_updates(silent=True, show_dialog=False, parent=None):
    """Convenience function to check for updates and optionally show a dialog.
    
    Args:
        silent (bool, optional): Whether to suppress error messages. Defaults to True.
        show_dialog (bool, optional): Whether to show a dialog if updates are available. 
                                      Defaults to False.
        parent (tk.Widget, optional): Parent widget for the dialog. Defaults to None.
        
    Returns:
        bool: True if updates are available, False otherwise
    """
    checker = UpdateChecker(auto_check=False)
    updates_available = checker.check_for_updates(silent=silent)
    
    if updates_available and show_dialog:
        checker.show_update_dialog(parent=parent)
        
    return updates_available 