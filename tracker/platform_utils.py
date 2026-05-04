"""
Platform Utilities — OS detection and factory functions.
Isolates all platform-specific decisions to this module.
"""

import platform
import logging

logger = logging.getLogger(__name__)


def get_platform() -> str:
    """
    Detect the current operating system.
    
    Returns:
        'darwin' for macOS, 'windows' for Windows.
    
    Raises:
        RuntimeError: If the platform is not supported.
    """
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    else:
        raise RuntimeError(
            f"Unsupported platform: {system}. "
            "Only macOS (darwin) and Windows are supported."
        )


def create_focus_detector():
    """
    Factory function — returns the platform-appropriate FocusDetector instance.
    
    Uses lazy imports so platform-specific packages (pyobjc / pywin32)
    are only imported on the correct OS.
    """
    plat = get_platform()
    
    if plat == "darwin":
        logger.info("Detected macOS — using MacOSFocusDetector")
        from tracker.focus_detector_macos import MacOSFocusDetector
        return MacOSFocusDetector()
    else:
        logger.info("Detected Windows — using WindowsFocusDetector")
        from tracker.focus_detector_windows import WindowsFocusDetector
        return WindowsFocusDetector()
