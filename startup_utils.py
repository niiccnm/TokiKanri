"""Utilities for registering/unregistering the app to start at Windows startup.

This uses the HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry key,
which ensures the program launches when the current user logs in.
"""
from __future__ import annotations

import os
import sys
import winreg
from typing import Optional


_RUN_KEY = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
_APP_NAME = "TokiKanri"

def _get_executable_path() -> str:
    """Return the path that should be executed on startup.

    If the program has been packaged with PyInstaller (``sys.frozen``), return the
    bundled executable path (``sys.executable``). Otherwise, return the absolute
    path to the current script interpreted by Python.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def _open_run_key(access: int):
    """Convenience wrapper to open the *Run* registry key with the desired access."""
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, access)


def is_startup_enabled() -> bool:
    """Check if a registry entry already exists for the application."""
    try:
        with _open_run_key(winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        # Key exists but value not found
        return False


def enable_startup(executable_path: Optional[str] = None) -> None:
    """Create or update the registry entry that starts the program on login.

    Parameters
    ----------
    executable_path : Optional[str]
        Path to the executable or script to run. Defaults to the path returned by
        :func:`_get_executable_path`.
    """
    try:
        exe = executable_path or _get_executable_path()
        
        # Get the absolute path to ensure it works when run at startup
        exe = os.path.abspath(exe)
        
        # Add quotes to handle paths with spaces
        if ' ' in exe and not (exe.startswith('"') and exe.endswith('"')):
            exe = f'"{exe}"'
        
        with _open_run_key(winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, exe)
            
        # Log success if possible
        try:
            from logger import Logger
            Logger().info(f"Added application to startup: {exe}")
        except:
            pass
            
    except Exception as e:
        # Log error if possible
        try:
            from logger import Logger
            Logger().error(f"Failed to enable startup: {str(e)}")
        except:
            print(f"Failed to enable startup: {str(e)}")


def disable_startup() -> None:
    """Remove the registry entry that starts the program on login, if present."""
    try:
        with _open_run_key(winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, _APP_NAME)
            
        # Log success if possible
        try:
            from logger import Logger
            Logger().info("Removed application from startup")
        except:
            pass
            
    except FileNotFoundError:
        # Already removed/no-op
        pass
    except Exception as e:
        # Log error if possible
        try:
            from logger import Logger
            Logger().error(f"Failed to disable startup: {str(e)}")
        except:
            print(f"Failed to disable startup: {str(e)}")
