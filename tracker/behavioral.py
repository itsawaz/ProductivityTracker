"""
Behavioral Enhancements — Focus continuity bonus, break penalty,
rolling average smoothing, and focus streak tracking.
"""

import logging
import config

logger = logging.getLogger(__name__)


class BehavioralEngine:
    """
    Applies behavioral adjustments to raw productivity weights.
    
    Enhancements:
        1. Focus Continuity Bonus — rewards sustained focus
        2. Break Penalty — penalizes returning from long idle
        3. Rolling Average Smoothing — reduces noise
        4. Focus Streak Tracking — records longest productive streak
    """

    def __init__(self):
        # Focus continuity tracking
        self._consecutive_active = 0
        self._bonus = config.FOCUS_CONTINUITY_BONUS
        self._bonus_min_streak = config.FOCUS_CONTINUITY_MIN_STREAK
        self._weight_cap = config.WEIGHT_CAP

        # Break penalty tracking
        self._consecutive_idle = 0
        self._penalty_multiplier = config.BREAK_PENALTY_MULTIPLIER
        self._penalty_idle_threshold = config.BREAK_PENALTY_IDLE_THRESHOLD
        self._penalty_duration = config.BREAK_PENALTY_DURATION
        self._penalty_remaining = 0  # intervals of penalty left

        # Streak tracking
        self._current_streak = 0
        self._max_streak_today = 0

        # Rolling average
        self._recent_weights = []
        self._rolling_window = config.ROLLING_AVERAGE_WINDOW

    def adjust_weight(self, raw_weight: float, state: str) -> float:
        """
        Apply behavioral adjustments to a raw productivity weight.
        
        Args:
            raw_weight: Base weight from the classifier (0.0 to 1.0).
            state: Activity state string.
        
        Returns:
            Adjusted weight after all behavioral enhancements.
        """
        adjusted = raw_weight
        is_productive = state in ("active", "high_focus")
        is_idle = state == "idle"

        # ── Focus Continuity Bonus ────────────────────────────────────
        if is_productive:
            self._consecutive_active += 1
            self._consecutive_idle = 0

            if self._consecutive_active >= self._bonus_min_streak:
                adjusted = min(adjusted + self._bonus, self._weight_cap)
                logger.debug(
                    f"Focus bonus applied: {raw_weight:.2f} → {adjusted:.2f} "
                    f"(streak: {self._consecutive_active})"
                )
        else:
            self._consecutive_active = 0

        # ── Break Penalty ─────────────────────────────────────────────
        if is_idle:
            self._consecutive_idle += 1
        else:
            # Check if returning from a long idle
            if self._consecutive_idle >= self._penalty_idle_threshold:
                self._penalty_remaining = self._penalty_duration
                logger.debug(
                    f"Break penalty triggered after {self._consecutive_idle} "
                    f"idle intervals — penalty for {self._penalty_duration} intervals"
                )
            self._consecutive_idle = 0

        if self._penalty_remaining > 0 and not is_idle:
            adjusted *= self._penalty_multiplier
            self._penalty_remaining -= 1
            logger.debug(
                f"Break penalty applied: weight × {self._penalty_multiplier} "
                f"(remaining: {self._penalty_remaining})"
            )

        # ── Streak Tracking ───────────────────────────────────────────
        if is_productive:
            self._current_streak += 1
            self._max_streak_today = max(
                self._max_streak_today, self._current_streak
            )
        else:
            self._current_streak = 0

        # ── Rolling Average ───────────────────────────────────────────
        self._recent_weights.append(adjusted)
        if len(self._recent_weights) > self._rolling_window * 2:
            # Keep twice the window for flexibility
            self._recent_weights = self._recent_weights[-self._rolling_window * 2:]

        return round(adjusted, 4)

    def get_current_streak(self) -> int:
        """Get the current consecutive productive interval count."""
        return self._current_streak

    def get_max_streak_today(self) -> int:
        """Get the longest productive streak today."""
        return self._max_streak_today

    def get_rolling_score(self) -> float:
        """Get the rolling average score over the configured window."""
        window = self._recent_weights[-self._rolling_window:]
        if not window:
            return 0.0
        return round(sum(window) / len(window), 4)

    def get_recent_weights(self) -> list:
        """Get recent adjusted weights for scoring engine."""
        return self._recent_weights.copy()

    def reset_daily(self):
        """Reset daily counters (call at midnight or start of day)."""
        self._max_streak_today = 0
        self._current_streak = 0
        self._consecutive_active = 0
        self._consecutive_idle = 0
        self._penalty_remaining = 0
        self._recent_weights.clear()
        logger.info("BehavioralEngine daily counters reset")
