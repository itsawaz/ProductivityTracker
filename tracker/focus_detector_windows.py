"""
Focus Detector — Windows Implementation.
Uses pywin32 (win32gui) + psutil to detect the foreground application.
Dual detection strategy: process name (primary) + window title (fallback).
"""

import logging
from tracker.focus_detector_base import BaseFocusDetector
import config

logger = logging.getLogger(__name__)


class WindowsFocusDetector(BaseFocusDetector):
    """
    Windows focus detector using win32gui and psutil.
    
    Requires:
        - pywin32 installed
        - psutil installed
    
    No special permissions required on Windows.
    """

    def __init__(self):
        # Lazy imports — only on Windows
        try:
            import win32gui
            import win32process
            import psutil
            self._win32gui = win32gui
            self._win32process = win32process
            self._psutil = psutil
            logger.info("WindowsFocusDetector initialized successfully")
        except ImportError as e:
            raise ImportError(
                f"pywin32 and psutil are required on Windows. "
                f"Install with: pip install pywin32 psutil. Error: {e}"
            )

        self._vdi_process_names = {n.lower() for n in config.VDI_PROCESS_NAMES}
        self._vdi_title_patterns = config.VDI_TITLE_PATTERNS

    def _get_foreground_info(self):
        """
        Get foreground window handle, process name, and window title.
        
        Returns:
            Tuple of (hwnd, process_name, window_title) or (None, None, None) on failure.
        """
        try:
            hwnd = self._win32gui.GetForegroundWindow()
            if not hwnd:
                return None, None, None

            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)
            title = self._win32gui.GetWindowText(hwnd) or ""

            try:
                proc = self._psutil.Process(pid)
                proc_name = proc.name().lower()
            except (self._psutil.NoSuchProcess, self._psutil.AccessDenied):
                proc_name = ""

            return hwnd, proc_name, title
        except Exception as e:
            logger.warning(f"Error getting foreground window info: {e}")
            return None, None, None

    def is_vdi_active(self) -> bool:
        """Check if a VDI client is the foreground Windows application."""
        _, proc_name, title = self._get_foreground_info()

        if proc_name is None:
            return False

        # Primary: match by process name
        if proc_name in self._vdi_process_names:
            return True

        # Fallback: match by window title substring
        if title:
            for pattern in self._vdi_title_patterns:
                if pattern in title:
                    return True

        return False

    def get_active_app_name(self) -> str:
        """Get the name of the foreground Windows application."""
        _, proc_name, title = self._get_foreground_info()

        if proc_name:
            return proc_name
        if title:
            return title
        return "Unknown"
