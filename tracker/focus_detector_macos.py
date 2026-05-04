"""
Focus Detector — macOS Implementation.
Uses pyobjc (AppKit / NSWorkspace) to detect the frontmost application.
"""

import logging
from tracker.focus_detector_base import BaseFocusDetector
import config

logger = logging.getLogger(__name__)


class MacOSFocusDetector(BaseFocusDetector):
    """
    macOS focus detector using NSWorkspace.
    
    Requires:
        - pyobjc-framework-Cocoa installed
        - Accessibility permissions granted to the terminal/app
    """

    def __init__(self):
        # Lazy import — only on macOS
        try:
            from AppKit import NSWorkspace
            self._NSWorkspace = NSWorkspace
            logger.info("MacOSFocusDetector initialized successfully")
        except ImportError:
            raise ImportError(
                "pyobjc-framework-Cocoa is required on macOS. "
                "Install with: pip install pyobjc-framework-Cocoa"
            )
        
        self._vdi_bundle_ids = config.VDI_BUNDLE_IDS

    def is_vdi_active(self) -> bool:
        """Check if a VDI client is the frontmost macOS application."""
        try:
            app = self._NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is None:
                return False
            bundle_id = app.bundleIdentifier()
            if bundle_id is None:
                return False
            return bundle_id in self._vdi_bundle_ids
        except Exception as e:
            logger.warning(f"Error checking VDI focus: {e}")
            return False

    def get_active_app_name(self) -> str:
        """Get the name of the frontmost macOS application."""
        try:
            app = self._NSWorkspace.sharedWorkspace().frontmostApplication()
            if app is not None:
                return app.localizedName() or "Unknown"
        except Exception as e:
            logger.warning(f"Error getting active app name: {e}")
        return "Unknown"
