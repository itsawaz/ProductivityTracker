"""
Real-Time Emitter — Broadcasts events via SocketIO.
"""

import logging
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

_socketio = None


class Emitter:
    """
    Emits real-time events to connected dashboard clients via SocketIO.
    """

    def __init__(self, socketio_instance: SocketIO):
        self._socketio = socketio_instance

    def emit_interval_update(self, interval_data: dict, status: dict):
        """
        Broadcast a new interval update to all connected clients.
        
        Args:
            interval_data: The completed interval data.
            status: Current aggregated status.
        """
        try:
            # Serialize datetime for JSON
            payload = {
                "interval": {
                    "timestamp": (
                        interval_data["timestamp"].isoformat()
                        if hasattr(interval_data["timestamp"], "isoformat")
                        else str(interval_data["timestamp"])
                    ),
                    "duration": interval_data["duration"],
                    "vdi_active": interval_data["vdi_active"],
                    "total_events": interval_data["total_events"],
                    "activity_state": interval_data["activity_state"],
                    "adjusted_weight": interval_data["adjusted_weight"],
                    "productive_seconds": interval_data["productive_seconds"],
                    "key_count": interval_data["key_count"],
                    "mouse_move_count": interval_data["mouse_move_count"],
                    "mouse_click_count": interval_data["mouse_click_count"],
                    "scroll_count": interval_data["scroll_count"],
                },
                "status": status,
            }

            self._socketio.emit("interval_update", payload)
            logger.debug(
                f"Emitted interval_update: state={interval_data['activity_state']}"
            )
        except Exception as e:
            logger.error(f"Error emitting interval update: {e}")

    def emit_status_update(self, status: dict):
        """
        Broadcast a status-only update (between intervals).
        
        Args:
            status: Current aggregated status.
        """
        try:
            self._socketio.emit("status_update", status)
        except Exception as e:
            logger.error(f"Error emitting status update: {e}")


def register_socket_events(socketio_instance: SocketIO):
    """Register SocketIO event handlers."""
    global _socketio
    _socketio = socketio_instance

    @socketio_instance.on("connect")
    def handle_connect():
        logger.info("Dashboard client connected")

    @socketio_instance.on("disconnect")
    def handle_disconnect():
        logger.info("Dashboard client disconnected")

    @socketio_instance.on("request_status")
    def handle_request_status():
        """Handle manual status request from client."""
        logger.debug("Client requested status update")
