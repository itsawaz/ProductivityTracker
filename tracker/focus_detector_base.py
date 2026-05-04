"""
Focus Detector — Abstract Base Class.
Defines the cross-platform interface for detecting VDI/Remote Desktop focus.
"""

from abc import ABC, abstractmethod


class BaseFocusDetector(ABC):
    """
    Abstract base class for platform-specific focus detection.
    
    Implementations must detect whether a VDI/Remote Desktop client
    is the currently active (foreground) application.
    """

    @abstractmethod
    def is_vdi_active(self) -> bool:
        """
        Check if a VDI/Remote Desktop client is the frontmost application.
        
        Returns:
            True if a recognized VDI app is in the foreground, False otherwise.
        """
        pass

    @abstractmethod
    def get_active_app_name(self) -> str:
        """
        Get the name of the currently active (foreground) application.
        
        Returns:
            Human-readable application name, or "Unknown" if unavailable.
        """
        pass
