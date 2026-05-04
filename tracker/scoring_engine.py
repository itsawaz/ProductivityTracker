"""
Scoring Engine — Calculates productivity metrics.
Handles per-interval scoring, daily aggregation, and efficiency calculation.
"""

import logging
import config

logger = logging.getLogger(__name__)


class ScoringEngine:
    """
    Calculates productivity scores from classified intervals.
    
    Metrics computed:
        - Per-interval productive seconds
        - Daily productive hours
        - Efficiency percentage
        - Rolling productivity score
    """

    def __init__(self):
        self._interval_duration = config.INTERVAL_DURATION

    def calculate_productive_seconds(
        self, duration: int, weight: float
    ) -> float:
        """
        Calculate productive seconds for a single interval.
        
        Args:
            duration: Interval duration in seconds.
            weight: Adjusted productivity weight (0.0 to 1.0).
        
        Returns:
            Productive seconds (duration × weight).
        """
        return duration * weight

    def calculate_efficiency(
        self, productive_seconds: float, total_logged_seconds: int
    ) -> float:
        """
        Calculate efficiency as a percentage.
        
        Args:
            productive_seconds: Total productive seconds.
            total_logged_seconds: Total seconds tracked.
        
        Returns:
            Efficiency percentage (0.0 to 100.0).
        """
        if total_logged_seconds == 0:
            return 0.0
        return (productive_seconds / total_logged_seconds) * 100.0

    def calculate_rolling_score(self, recent_weights: list) -> float:
        """
        Calculate a rolling average score from recent interval weights.
        
        Args:
            recent_weights: List of recent adjusted weights.
        
        Returns:
            Rolling average score (0.0 to 1.0).
        """
        if not recent_weights:
            return 0.0
        window = config.ROLLING_AVERAGE_WINDOW
        relevant = recent_weights[-window:]
        return sum(relevant) / len(relevant)

    def format_productive_hours(self, productive_seconds: float) -> str:
        """
        Format productive seconds as HH:MM:SS.
        
        Args:
            productive_seconds: Total productive seconds.
        
        Returns:
            Formatted string like "5h 23m".
        """
        hours = int(productive_seconds // 3600)
        minutes = int((productive_seconds % 3600) // 60)
        return f"{hours}h {minutes:02d}m"
