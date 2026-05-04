"""
Input Tracker — Global keyboard and mouse event capture.
Uses pynput (cross-platform) to count input events per interval.
"""

import time
import threading
import logging
from pynput import keyboard, mouse
import config

logger = logging.getLogger(__name__)


class InputTracker:
    """
    Tracks keyboard and mouse activity using pynput listeners.
    
    Counts events per interval and provides an atomic reset-and-get
    method for the interval aggregator to consume.
    
    Cross-platform: works on macOS and Windows.
    
    macOS Note: Requires Accessibility permissions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._key_count = 0
        self._mouse_move_count = 0
        self._mouse_click_count = 0
        self._scroll_count = 0
        self._last_mouse_move_time = 0.0
        self._mouse_sample_interval = config.MOUSE_SAMPLE_INTERVAL

        self._keyboard_listener = None
        self._mouse_listener = None
        self._running = False

    def start(self):
        """Start keyboard and mouse listeners in background threads."""
        if self._running:
            logger.warning("InputTracker already running")
            return

        self._running = True

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
        )
        self._keyboard_listener.daemon = True
        self._keyboard_listener.start()

        self._mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
        )
        self._mouse_listener.daemon = True
        self._mouse_listener.start()

        logger.info("InputTracker started — keyboard and mouse listeners active")

    def stop(self):
        """Stop all listeners."""
        self._running = False
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
        logger.info("InputTracker stopped")

    # ─── Event Handlers ──────────────────────────────────────────────

    def _on_key_press(self, key):
        """Handle keyboard press event."""
        with self._lock:
            self._key_count += 1

    def _on_mouse_move(self, x, y):
        """
        Handle mouse movement event.
        Throttled to avoid excessive CPU usage from raw move events.
        """
        now = time.time()
        if now - self._last_mouse_move_time < self._mouse_sample_interval:
            return
        with self._lock:
            self._mouse_move_count += 1
            self._last_mouse_move_time = now

    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click event (only on press, not release)."""
        if pressed:
            with self._lock:
                self._mouse_click_count += 1

    def _on_mouse_scroll(self, x, y, dx, dy):
        """Handle mouse scroll event."""
        with self._lock:
            self._scroll_count += 1

    # ─── Data Access ─────────────────────────────────────────────────

    def reset_and_get(self) -> dict:
        """
        Atomically read current counts and reset to zero.
        
        Called by the IntervalAggregator at the end of each interval.
        
        Returns:
            dict with keys: key_count, mouse_move_count, mouse_click_count,
            scroll_count, total_events
        """
        with self._lock:
            data = {
                "key_count": self._key_count,
                "mouse_move_count": self._mouse_move_count,
                "mouse_click_count": self._mouse_click_count,
                "scroll_count": self._scroll_count,
            }
            data["total_events"] = (
                data["key_count"]
                + data["mouse_move_count"]
                + data["mouse_click_count"]
                + data["scroll_count"]
            )

            # Reset counters
            self._key_count = 0
            self._mouse_move_count = 0
            self._mouse_click_count = 0
            self._scroll_count = 0

        return data

    def get_current_counts(self) -> dict:
        """
        Read current counts without resetting (for real-time status).
        """
        with self._lock:
            total = (
                self._key_count
                + self._mouse_move_count
                + self._mouse_click_count
                + self._scroll_count
            )
            return {
                "key_count": self._key_count,
                "mouse_move_count": self._mouse_move_count,
                "mouse_click_count": self._mouse_click_count,
                "scroll_count": self._scroll_count,
                "total_events": total,
            }
