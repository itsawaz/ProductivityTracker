"""
Activity Classifier — Classifies intervals into productivity states.
States: Idle, Passive, Active, High Focus.
"""

import logging
import config

logger = logging.getLogger(__name__)

# Activity state constants
STATE_IDLE = "idle"
STATE_PASSIVE = "passive"
STATE_ACTIVE = "active"
STATE_HIGH_FOCUS = "high_focus"


class Classifier:
    """
    Classifies user activity into one of four productivity states
    based on the total event count within an interval.
    
    Includes noise filtering to prevent accidental single-event
    intervals from being counted as productive.
    """

    def __init__(self):
        self._thresholds = {
            "passive_min": config.THRESHOLD_PASSIVE_MIN,
            "active_min": config.THRESHOLD_ACTIVE_MIN,
            "high_focus_min": config.THRESHOLD_HIGH_FOCUS_MIN,
        }
        self._noise_filter = config.NOISE_FILTER_ENABLED
        # Keep track of last few states for noise filtering
        self._recent_states = []

    def classify(self, total_events: int, vdi_active: bool) -> str:
        """
        Classify an interval based on event count and VDI focus.
        
        Args:
            total_events: Total input events in the interval.
            vdi_active: Whether the VDI app was in focus.
        
        Returns:
            Activity state string: 'idle', 'passive', 'active', or 'high_focus'.
        """
        # If VDI is not active, always mark as idle
        if not vdi_active:
            state = STATE_IDLE
        elif total_events == 0:
            state = STATE_IDLE
        elif total_events < self._thresholds["active_min"]:
            state = STATE_PASSIVE
        elif total_events < self._thresholds["high_focus_min"]:
            state = STATE_ACTIVE
        else:
            state = STATE_HIGH_FOCUS

        # Noise filtering: single-event intervals surrounded by idle → demote to idle
        if self._noise_filter and state == STATE_PASSIVE and total_events <= 1:
            if self._is_isolated_event():
                logger.debug(
                    f"Noise filter: demoting single-event interval to idle "
                    f"(total_events={total_events})"
                )
                state = STATE_IDLE

        # Track for noise filtering
        self._recent_states.append(state)
        if len(self._recent_states) > 5:
            self._recent_states.pop(0)

        return state

    def _is_isolated_event(self) -> bool:
        """
        Check if the current event is isolated (previous state was idle).
        Used for noise filtering.
        """
        if not self._recent_states:
            return True
        return self._recent_states[-1] == STATE_IDLE

    def get_weight(self, state: str) -> float:
        """
        Get the base productivity weight for a given state.
        
        Args:
            state: Activity state string.
        
        Returns:
            Productivity weight (0.0 to 1.0).
        """
        weights = {
            STATE_IDLE: config.WEIGHT_IDLE,
            STATE_PASSIVE: config.WEIGHT_PASSIVE,
            STATE_ACTIVE: config.WEIGHT_ACTIVE,
            STATE_HIGH_FOCUS: config.WEIGHT_HIGH_FOCUS,
        }
        return weights.get(state, config.WEIGHT_IDLE)
