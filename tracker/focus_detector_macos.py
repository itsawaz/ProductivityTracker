"""
Focus Detector — macOS Implementation.
Uses pyobjc (AppKit / NSWorkspace) to detect the frontmost application.
Supports split-screen / multi-monitor setups by checking if a VDI
app has actual visible windows on screen (not just running).
"""

import logging
from tracker.focus_detector_base import BaseFocusDetector
import config

logger = logging.getLogger(__name__)


class MacOSFocusDetector(BaseFocusDetector):
    """
    macOS focus detector using NSWorkspace + Quartz.
    
    Detection modes:
        - STRICT: VDI must be the frontmost (focused) app.
        - VISIBLE: VDI must have at least one visible window on screen.
    
    Requires:
        - pyobjc-framework-Cocoa installed
        - pyobjc-framework-Quartz installed
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

        # Try to import Quartz for window-level detection
        try:
            import Quartz
            self._Quartz = Quartz
            self._has_quartz = True
            logger.info("Quartz available — using window-level VDI detection")
        except ImportError:
            self._Quartz = None
            self._has_quartz = False
            logger.warning(
                "pyobjc-framework-Quartz not available. "
                "Falling back to app-level detection. "
                "Install with: pip install pyobjc-framework-Quartz"
            )
        
        self._vdi_bundle_ids = config.VDI_BUNDLE_IDS

        # Use VISIBLE mode for split-screen / multi-monitor support
        self._detection_mode = getattr(
            config, "VDI_DETECTION_MODE", "visible"
        )
        logger.info(
            f"VDI detection mode: {self._detection_mode}"
        )

    def is_vdi_active(self) -> bool:
        """
        Check if a VDI client is active.
        
        In 'strict' mode: VDI must be the frontmost app.
        In 'visible' mode: VDI must have visible windows on screen.
        """
        try:
            if self._detection_mode == "strict":
                return self._is_vdi_frontmost()
            else:
                return self._is_vdi_has_windows()
        except Exception as e:
            logger.warning(f"Error checking VDI focus: {e}")
            return False

    def _is_vdi_frontmost(self) -> bool:
        """Check if a VDI client is the frontmost macOS application."""
        app = self._NSWorkspace.sharedWorkspace().frontmostApplication()
        if app is None:
            return False
        bundle_id = app.bundleIdentifier()
        if bundle_id is None:
            return False
        return bundle_id in self._vdi_bundle_ids

    def _is_vdi_has_windows(self) -> bool:
        """
        Check if any VDI client has visible windows on screen.
        
        Uses Quartz CGWindowListCopyWindowInfo to enumerate all on-screen
        windows. This correctly handles:
            - App running but no windows open → False
            - App running with windows on other monitor → True
            - App hidden/minimized → False
            - App quit → False
        
        Falls back to frontmost check if Quartz is not available.
        """
        if not self._has_quartz:
            return self._is_vdi_frontmost()

        # Get the PIDs of running VDI apps
        workspace = self._NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        vdi_pids = set()
        for app in running_apps:
            bundle_id = app.bundleIdentifier()
            if bundle_id and bundle_id in self._vdi_bundle_ids:
                if not app.isTerminated():
                    vdi_pids.add(app.processIdentifier())

        if not vdi_pids:
            return False

        # Check if any of those PIDs have visible on-screen windows
        window_list = self._Quartz.CGWindowListCopyWindowInfo(
            self._Quartz.kCGWindowListOptionOnScreenOnly
            | self._Quartz.kCGWindowListExcludeDesktopElements,
            self._Quartz.kCGNullWindowID,
        )

        if window_list is None:
            return False

        for window in window_list:
            owner_pid = window.get("kCGWindowOwnerPID", -1)
            if owner_pid in vdi_pids:
                # Check that it's a real window (not a menu bar item etc.)
                layer = window.get("kCGWindowLayer", 0)
                # Layer 0 = normal windows, >0 = system elements
                if layer == 0:
                    return True

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

    def get_vdi_app_info(self) -> dict:
        """
        Get information about running VDI apps (for debugging).
        
        Returns:
            Dict with VDI app details or empty if none found.
        """
        try:
            workspace = self._NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            vdi_apps = []
            for app in running_apps:
                bundle_id = app.bundleIdentifier()
                if bundle_id and bundle_id in self._vdi_bundle_ids:
                    pid = app.processIdentifier()
                    has_windows = self._check_pid_has_windows(pid)
                    vdi_apps.append({
                        "name": app.localizedName(),
                        "bundle_id": bundle_id,
                        "pid": pid,
                        "is_hidden": app.isHidden(),
                        "is_active": app.isActive(),
                        "is_terminated": app.isTerminated(),
                        "has_visible_windows": has_windows,
                    })
            
            return {
                "detection_mode": self._detection_mode,
                "has_quartz": self._has_quartz,
                "frontmost_app": self.get_active_app_name(),
                "is_vdi_active": self.is_vdi_active(),
                "vdi_apps_found": len(vdi_apps),
                "vdi_apps": vdi_apps,
            }
        except Exception as e:
            logger.warning(f"Error getting VDI app info: {e}")
            return {"error": str(e)}

    def _check_pid_has_windows(self, pid: int) -> bool:
        """Check if a specific PID has any visible on-screen windows."""
        if not self._has_quartz:
            return False
        try:
            window_list = self._Quartz.CGWindowListCopyWindowInfo(
                self._Quartz.kCGWindowListOptionOnScreenOnly
                | self._Quartz.kCGWindowListExcludeDesktopElements,
                self._Quartz.kCGNullWindowID,
            )
            if window_list is None:
                return False
            for window in window_list:
                if window.get("kCGWindowOwnerPID", -1) == pid:
                    if window.get("kCGWindowLayer", 0) == 0:
                        return True
            return False
        except Exception:
            return False
