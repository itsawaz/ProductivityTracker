"""
Interval Aggregator — Manages the 30-second interval lifecycle.
Orchestrates data collection, classification, scoring, storage, and emission.
"""

import time
import threading
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class IntervalAggregator:
    """
    Core orchestrator that runs on a fixed interval timer.
    
    Every INTERVAL_DURATION seconds:
    1. Collects input counts from InputTracker
    2. Queries FocusDetector for VDI active state
    3. Classifies the interval via Classifier
    4. Applies behavioral adjustments
    5. Calculates productive seconds via ScoringEngine
    6. Stores the interval in the database via Repository
    7. Emits real-time update via Emitter
    """

    def __init__(
        self, focus_detector, input_tracker, classifier, scoring_engine,
        behavioral_engine, repository, emitter=None
    ):
        self._focus_detector = focus_detector
        self._input_tracker = input_tracker
        self._classifier = classifier
        self._scoring_engine = scoring_engine
        self._behavioral = behavioral_engine
        self._repository = repository
        self._emitter = emitter

        self._interval_duration = config.INTERVAL_DURATION
        self._running = False
        self._timer_thread = None

        # Real-time state for the dashboard
        self._current_state = "idle"
        self._current_weight = 0.0
        self._vdi_active = False
        self._today_productive_seconds = 0.0
        self._today_total_seconds = 0
        self._today_idle_seconds = 0
        self._today_vdi_seconds = 0
        self._interruptions = 0
        self._last_was_productive = False
        self._current_date = datetime.now().strftime("%Y-%m-%d")

    def start(self):
        """Start the interval aggregation loop in a background thread."""
        if self._running:
            logger.warning("IntervalAggregator already running")
            return

        self._running = True
        # Load today's existing data from DB
        self._load_today_totals()

        # Main interval processing thread
        self._timer_thread = threading.Thread(
            target=self._run_loop, daemon=True
        )
        self._timer_thread.start()

        # Live status broadcast thread (pushes updates every 5s)
        self._live_thread = threading.Thread(
            target=self._live_status_loop, daemon=True
        )
        self._live_thread.start()

        logger.info(
            f"IntervalAggregator started — {self._interval_duration}s intervals"
        )

    def stop(self):
        """Stop the aggregation loop and save daily summary."""
        self._running = False
        if self._timer_thread:
            self._timer_thread.join(timeout=5)
        if hasattr(self, '_live_thread') and self._live_thread:
            self._live_thread.join(timeout=2)
        self._save_daily_summary()
        logger.info("IntervalAggregator stopped")

    def _run_loop(self):
        """Main interval loop — runs every INTERVAL_DURATION seconds."""
        while self._running:
            time.sleep(self._interval_duration)
            if not self._running:
                break
            try:
                self._process_interval()
            except Exception as e:
                logger.error(f"Error processing interval: {e}", exc_info=True)

    def _live_status_loop(self):
        """
        Broadcast live status every 5 seconds for real-time dashboard updates.
        
        This provides near-instant VDI status, current state, and running
        timer updates between the 30-second interval processing cycles.
        """
        while self._running:
            time.sleep(5)
            if not self._running:
                break
            try:
                # Update VDI status in real-time
                self._vdi_active = self._focus_detector.is_vdi_active()
                
                if self._emitter:
                    self._emitter.emit_status_update(self.get_status())
            except Exception as e:
                logger.debug(f"Live status emit error: {e}")

    def _process_interval(self):
        """Process a single interval — the core aggregation logic."""
        # Check if day has changed (midnight rollover)
        self._check_day_change()

        timestamp = datetime.now()

    def _check_day_change(self):
        """
        Detect midnight rollover and reset daily counters.
        
        Saves yesterday's summary and resets all in-memory state
        so the dashboard starts fresh for the new day.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if today == self._current_date:
            return

        logger.info(
            f"🌅 Day changed: {self._current_date} → {today}. "
            f"Resetting daily counters."
        )

        # Save yesterday's summary before resetting
        self._save_daily_summary()

        # Reset all daily counters
        self._current_date = today
        self._today_productive_seconds = 0.0
        self._today_total_seconds = 0
        self._today_idle_seconds = 0
        self._today_vdi_seconds = 0
        self._interruptions = 0
        self._last_was_productive = False
        self._current_state = "idle"
        self._current_weight = 0.0

        # Reset behavioral engine for the new day
        self._behavioral.reset_daily()

        # Reload any data already logged today (in case of late restart)
        self._load_today_totals()

        logger.info("Daily counters reset for new day")

        # 1. Collect input data
        input_data = self._input_tracker.reset_and_get()

        # 2. Check VDI focus
        vdi_active = self._focus_detector.is_vdi_active()
        self._vdi_active = vdi_active

        # 3. Classify activity
        state = self._classifier.classify(
            input_data["total_events"], vdi_active
        )
        raw_weight = self._classifier.get_weight(state)

        # 4. Apply behavioral adjustments
        adjusted_weight = self._behavioral.adjust_weight(raw_weight, state)

        # 5. Calculate productive seconds
        productive_seconds = self._scoring_engine.calculate_productive_seconds(
            self._interval_duration, adjusted_weight
        )

        # 6. Update daily totals
        self._today_total_seconds += self._interval_duration
        self._today_productive_seconds += productive_seconds
        if state == "idle":
            self._today_idle_seconds += self._interval_duration
        if vdi_active:
            self._today_vdi_seconds += self._interval_duration

        # Track interruptions (transition from productive → idle)
        is_productive = state in ("active", "high_focus")
        if self._last_was_productive and not is_productive:
            self._interruptions += 1
        self._last_was_productive = is_productive

        # Update current state
        self._current_state = state
        self._current_weight = adjusted_weight

        # 7. Store in database
        interval_data = {
            "timestamp": timestamp,
            "duration": self._interval_duration,
            "vdi_active": vdi_active,
            "key_count": input_data["key_count"],
            "mouse_move_count": input_data["mouse_move_count"],
            "mouse_click_count": input_data["mouse_click_count"],
            "scroll_count": input_data["scroll_count"],
            "total_events": input_data["total_events"],
            "activity_state": state,
            "raw_weight": raw_weight,
            "adjusted_weight": adjusted_weight,
            "productive_seconds": productive_seconds,
        }

        try:
            self._repository.save_interval(interval_data)
        except Exception as e:
            logger.error(f"Failed to save interval to DB: {e}")

        # 8. Emit real-time update
        if self._emitter:
            self._emitter.emit_interval_update(
                interval_data, self.get_status()
            )

        logger.info(
            f"Interval: state={state} events={input_data['total_events']} "
            f"weight={adjusted_weight:.2f} productive={productive_seconds:.1f}s "
            f"vdi={vdi_active}"
        )

    def get_status(self) -> dict:
        """Get current real-time status for the dashboard."""
        efficiency = self._scoring_engine.calculate_efficiency(
            self._today_productive_seconds, self._today_total_seconds
        )
        rolling_score = self._behavioral.get_rolling_score()
        productive_hours = self._scoring_engine.format_productive_hours(
            self._today_productive_seconds
        )

        vdi_pct = round(
            (self._today_vdi_seconds / self._today_total_seconds * 100)
            if self._today_total_seconds > 0 else 0, 1
        )

        return {
            "current_state": self._current_state,
            "current_weight": self._current_weight,
            "vdi_active": self._vdi_active,
            "productive_hours": productive_hours,
            "productive_seconds": round(self._today_productive_seconds, 1),
            "total_seconds": self._today_total_seconds,
            "idle_seconds": self._today_idle_seconds,
            "vdi_seconds": self._today_vdi_seconds,
            "vdi_percentage": vdi_pct,
            "efficiency": round(efficiency, 1),
            "rolling_score": round(rolling_score, 4),
            "current_streak": self._behavioral.get_current_streak(),
            "max_streak": self._behavioral.get_max_streak_today(),
            "interruptions": self._interruptions,
            "timestamp": datetime.now().isoformat(),
        }

    def _load_today_totals(self):
        """Load today's totals from database on startup or day change."""
        try:
            today = self._current_date

            # Load from intervals table (source of truth)
            totals = self._repository.get_today_totals(today)
            self._today_total_seconds = totals.get("total_seconds", 0)
            self._today_productive_seconds = totals.get(
                "productive_seconds", 0.0
            )
            self._today_idle_seconds = totals.get("idle_seconds", 0)

            # Load VDI seconds from intervals
            try:
                vdi_stats = self._repository.get_vdi_focus_stats(today)
                self._today_vdi_seconds = vdi_stats.get("vdi_seconds", 0)
            except Exception:
                self._today_vdi_seconds = 0

            # Load interruptions from daily summary if available
            summary = self._repository.get_daily_summary(today)
            if summary:
                self._interruptions = summary.get("interruptions", 0)

            logger.info(
                f"Loaded today's totals: "
                f"{self._today_productive_seconds:.0f}s productive, "
                f"{self._today_total_seconds}s total"
            )
        except Exception as e:
            logger.warning(f"Could not load today's totals: {e}")

    def _save_daily_summary(self):
        """Save/update today's daily summary."""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            efficiency = self._scoring_engine.calculate_efficiency(
                self._today_productive_seconds, self._today_total_seconds
            )

            # Get hourly breakdown from DB
            hourly = self._repository.get_hourly_breakdown(today)

            summary = {
                "date": today,
                "total_logged_seconds": self._today_total_seconds,
                "productive_seconds": self._today_productive_seconds,
                "idle_seconds": self._today_idle_seconds,
                "efficiency": round(efficiency, 2),
                "max_focus_streak": self._behavioral.get_max_streak_today(),
                "interruptions": self._interruptions,
                "hourly_breakdown": hourly,
            }
            self._repository.save_daily_summary(summary)
            logger.info(f"Daily summary saved for {today}")
        except Exception as e:
            logger.error(f"Failed to save daily summary: {e}")
