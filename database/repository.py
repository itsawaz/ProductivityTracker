"""
Repository — Data access layer for MySQL.
All database read/write operations go through this module.
"""

import json
import logging
from datetime import datetime
from database.connection import get_connection

logger = logging.getLogger(__name__)


class Repository:
    """
    Data access layer providing CRUD operations for intervals
    and daily summaries stored in MySQL.
    """

    # ─── Interval Operations ─────────────────────────────────────────

    def save_interval(self, data: dict):
        """
        Insert a new interval record.
        
        Args:
            data: dict with keys matching the intervals table columns.
        """
        sql = """
            INSERT INTO intervals 
                (timestamp, duration, vdi_active, key_count, mouse_move_count,
                 mouse_click_count, scroll_count, total_events, activity_state,
                 raw_weight, adjusted_weight, productive_seconds)
            VALUES 
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            data["timestamp"],
            data["duration"],
            1 if data["vdi_active"] else 0,
            data["key_count"],
            data["mouse_move_count"],
            data["mouse_click_count"],
            data["scroll_count"],
            data["total_events"],
            data["activity_state"],
            data["raw_weight"],
            data["adjusted_weight"],
            data["productive_seconds"],
        )
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            cursor.close()
        finally:
            conn.close()

    def get_intervals_for_date(self, date_str: str, limit: int = 500) -> list:
        """
        Get all intervals for a given date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format.
            limit: Maximum number of records.
        
        Returns:
            List of interval dicts.
        """
        sql = """
            SELECT id, timestamp, duration, vdi_active, key_count,
                   mouse_move_count, mouse_click_count, scroll_count,
                   total_events, activity_state, raw_weight, adjusted_weight,
                   productive_seconds
            FROM intervals
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp DESC
            LIMIT %s
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str, limit))
            rows = cursor.fetchall()
            cursor.close()
            # Convert datetime objects to ISO strings for JSON serialization
            for row in rows:
                if isinstance(row.get("timestamp"), datetime):
                    row["timestamp"] = row["timestamp"].isoformat()
                row["vdi_active"] = bool(row.get("vdi_active"))
            return rows
        finally:
            conn.close()

    def get_recent_intervals(self, limit: int = 20) -> list:
        """
        Get the most recent intervals.
        
        Args:
            limit: Number of recent intervals to fetch.
        
        Returns:
            List of interval dicts, most recent first.
        """
        sql = """
            SELECT id, timestamp, duration, vdi_active, key_count,
                   mouse_move_count, mouse_click_count, scroll_count,
                   total_events, activity_state, raw_weight, adjusted_weight,
                   productive_seconds
            FROM intervals
            ORDER BY timestamp DESC
            LIMIT %s
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (limit,))
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                if isinstance(row.get("timestamp"), datetime):
                    row["timestamp"] = row["timestamp"].isoformat()
                row["vdi_active"] = bool(row.get("vdi_active"))
            return rows
        finally:
            conn.close()

    # ─── Hourly Breakdown ────────────────────────────────────────────

    def get_hourly_breakdown(self, date_str: str) -> dict:
        """
        Aggregate intervals by hour for a given date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format.
        
        Returns:
            Dict mapping hour strings ("00"-"23") to average weights.
        """
        sql = """
            SELECT HOUR(timestamp) as hour,
                   AVG(adjusted_weight) as avg_weight,
                   SUM(productive_seconds) as total_productive,
                   COUNT(*) as interval_count
            FROM intervals
            WHERE DATE(timestamp) = %s
            GROUP BY HOUR(timestamp)
            ORDER BY hour
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            rows = cursor.fetchall()
            cursor.close()

            breakdown = {}
            for row in rows:
                hour_key = f"{int(row['hour']):02d}"
                breakdown[hour_key] = {
                    "avg_weight": round(float(row["avg_weight"]), 4),
                    "total_productive": round(float(row["total_productive"]), 1),
                    "interval_count": int(row["interval_count"]),
                }
            return breakdown
        finally:
            conn.close()

    # ─── Daily Summary Operations ────────────────────────────────────

    def save_daily_summary(self, summary: dict):
        """
        Insert or update a daily summary (upsert).
        
        Args:
            summary: dict with keys matching the daily_summary columns.
        """
        sql = """
            INSERT INTO daily_summary
                (date, total_logged_seconds, productive_seconds, idle_seconds,
                 efficiency, max_focus_streak, interruptions, hourly_breakdown)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                total_logged_seconds = VALUES(total_logged_seconds),
                productive_seconds = VALUES(productive_seconds),
                idle_seconds = VALUES(idle_seconds),
                efficiency = VALUES(efficiency),
                max_focus_streak = VALUES(max_focus_streak),
                interruptions = VALUES(interruptions),
                hourly_breakdown = VALUES(hourly_breakdown)
        """
        hourly_json = json.dumps(summary.get("hourly_breakdown", {}))
        params = (
            summary["date"],
            summary["total_logged_seconds"],
            summary["productive_seconds"],
            summary["idle_seconds"],
            summary["efficiency"],
            summary["max_focus_streak"],
            summary["interruptions"],
            hourly_json,
        )
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            cursor.close()
        finally:
            conn.close()

    def get_daily_summary(self, date_str: str) -> dict | None:
        """
        Get the daily summary for a specific date.
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            Summary dict or None if not found.
        """
        sql = """
            SELECT date, total_logged_seconds, productive_seconds,
                   idle_seconds, efficiency, max_focus_streak,
                   interruptions, hourly_breakdown
            FROM daily_summary
            WHERE date = %s
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            row = cursor.fetchone()
            cursor.close()
            if row:
                row["date"] = str(row["date"])
                # Parse JSON hourly_breakdown
                if isinstance(row.get("hourly_breakdown"), str):
                    row["hourly_breakdown"] = json.loads(
                        row["hourly_breakdown"]
                    )
            return row
        finally:
            conn.close()

    def get_daily_summaries(
        self, start_date: str, end_date: str
    ) -> list:
        """
        Get daily summaries for a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD), inclusive.
            end_date: End date (YYYY-MM-DD), inclusive.
        
        Returns:
            List of summary dicts.
        """
        sql = """
            SELECT date, total_logged_seconds, productive_seconds,
                   idle_seconds, efficiency, max_focus_streak,
                   interruptions, hourly_breakdown
            FROM daily_summary
            WHERE date BETWEEN %s AND %s
            ORDER BY date ASC
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (start_date, end_date))
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                row["date"] = str(row["date"])
                if isinstance(row.get("hourly_breakdown"), str):
                    row["hourly_breakdown"] = json.loads(
                        row["hourly_breakdown"]
                    )
            return rows
        finally:
            conn.close()

    # ─── Aggregate Queries ───────────────────────────────────────────

    def get_today_totals(self, date_str: str) -> dict:
        """
        Calculate today's totals directly from the intervals table.
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            Dict with total_seconds, productive_seconds, idle_seconds.
        """
        sql = """
            SELECT 
                COALESCE(SUM(duration), 0) as total_seconds,
                COALESCE(SUM(productive_seconds), 0) as productive_seconds,
                COALESCE(SUM(CASE WHEN activity_state = 'idle' THEN duration ELSE 0 END), 0) as idle_seconds,
                COUNT(*) as interval_count
            FROM intervals
            WHERE DATE(timestamp) = %s
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            row = cursor.fetchone()
            cursor.close()
            return {
                "total_seconds": int(row["total_seconds"]),
                "productive_seconds": float(row["productive_seconds"]),
                "idle_seconds": int(row["idle_seconds"]),
                "interval_count": int(row["interval_count"]),
            }
        finally:
            conn.close()

    def get_focus_streaks(self, date_str: str) -> list:
        """
        Compute focus streaks for a given date.
        
        A streak is a sequence of consecutive productive intervals
        (active or high_focus).
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            List of streak dicts with start_time, end_time, and length.
        """
        sql = """
            SELECT timestamp, activity_state
            FROM intervals
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp ASC
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            rows = cursor.fetchall()
            cursor.close()

            streaks = []
            current_streak_start = None
            current_streak_len = 0

            for row in rows:
                is_productive = row["activity_state"] in (
                    "active", "high_focus"
                )
                if is_productive:
                    if current_streak_start is None:
                        current_streak_start = row["timestamp"]
                    current_streak_len += 1
                else:
                    if current_streak_len > 0:
                        streaks.append({
                            "start_time": (
                                current_streak_start.isoformat()
                                if isinstance(current_streak_start, datetime)
                                else str(current_streak_start)
                            ),
                            "end_time": (
                                row["timestamp"].isoformat()
                                if isinstance(row["timestamp"], datetime)
                                else str(row["timestamp"])
                            ),
                            "length": current_streak_len,
                            "duration_minutes": current_streak_len * 0.5,
                        })
                    current_streak_start = None
                    current_streak_len = 0

            # Handle streak at end of data
            if current_streak_len > 0 and rows:
                streaks.append({
                    "start_time": (
                        current_streak_start.isoformat()
                        if isinstance(current_streak_start, datetime)
                        else str(current_streak_start)
                    ),
                    "end_time": (
                        rows[-1]["timestamp"].isoformat()
                        if isinstance(rows[-1]["timestamp"], datetime)
                        else str(rows[-1]["timestamp"])
                    ),
                    "length": current_streak_len,
                    "duration_minutes": current_streak_len * 0.5,
                })

            return streaks
        finally:
            conn.close()

    # ─── Insights Queries ────────────────────────────────────────────

    def get_vdi_focus_stats(self, date_str: str) -> dict:
        """
        Get VDI focus time vs non-VDI time for a given date.
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            Dict with vdi_seconds, non_vdi_seconds, vdi_percentage,
            and hourly_vdi breakdown.
        """
        sql = """
            SELECT 
                COALESCE(SUM(CASE WHEN vdi_active = 1 THEN duration ELSE 0 END), 0) as vdi_seconds,
                COALESCE(SUM(CASE WHEN vdi_active = 0 THEN duration ELSE 0 END), 0) as non_vdi_seconds,
                COALESCE(SUM(duration), 0) as total_seconds
            FROM intervals
            WHERE DATE(timestamp) = %s
        """
        hourly_sql = """
            SELECT 
                HOUR(timestamp) as hour,
                COALESCE(SUM(CASE WHEN vdi_active = 1 THEN duration ELSE 0 END), 0) as vdi_seconds,
                COALESCE(SUM(CASE WHEN vdi_active = 0 THEN duration ELSE 0 END), 0) as non_vdi_seconds
            FROM intervals
            WHERE DATE(timestamp) = %s
            GROUP BY HOUR(timestamp)
            ORDER BY hour
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            row = cursor.fetchone()

            cursor.execute(hourly_sql, (date_str,))
            hourly_rows = cursor.fetchall()
            cursor.close()

            total = int(row["total_seconds"])
            vdi = int(row["vdi_seconds"])
            non_vdi = int(row["non_vdi_seconds"])

            hourly_vdi = {}
            for hr in hourly_rows:
                hour_key = f"{int(hr['hour']):02d}"
                hourly_vdi[hour_key] = {
                    "vdi_seconds": int(hr["vdi_seconds"]),
                    "non_vdi_seconds": int(hr["non_vdi_seconds"]),
                }

            return {
                "vdi_seconds": vdi,
                "non_vdi_seconds": non_vdi,
                "total_seconds": total,
                "vdi_percentage": round((vdi / total * 100) if total > 0 else 0, 1),
                "hourly_vdi": hourly_vdi,
            }
        finally:
            conn.close()

    def get_input_totals(self, date_str: str) -> dict:
        """
        Get aggregated input totals for a given date.
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            Dict with total keystrokes, clicks, scrolls, mouse moves,
            and per-hour breakdown.
        """
        sql = """
            SELECT 
                COALESCE(SUM(key_count), 0) as total_keys,
                COALESCE(SUM(mouse_click_count), 0) as total_clicks,
                COALESCE(SUM(scroll_count), 0) as total_scrolls,
                COALESCE(SUM(mouse_move_count), 0) as total_mouse_moves,
                COALESCE(SUM(total_events), 0) as total_events
            FROM intervals
            WHERE DATE(timestamp) = %s
        """
        hourly_sql = """
            SELECT 
                HOUR(timestamp) as `hour`,
                COALESCE(SUM(key_count), 0) as `keys`,
                COALESCE(SUM(mouse_click_count), 0) as `clicks`,
                COALESCE(SUM(scroll_count), 0) as `scrolls`,
                COALESCE(SUM(mouse_move_count), 0) as `mouse_moves`,
                COALESCE(SUM(total_events), 0) as `events`
            FROM intervals
            WHERE DATE(timestamp) = %s
            GROUP BY HOUR(timestamp)
            ORDER BY `hour`
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            row = cursor.fetchone()

            cursor.execute(hourly_sql, (date_str,))
            hourly_rows = cursor.fetchall()
            cursor.close()

            hourly_input = {}
            for hr in hourly_rows:
                hour_key = f"{int(hr['hour']):02d}"
                hourly_input[hour_key] = {
                    "keys": int(hr["keys"]),
                    "clicks": int(hr["clicks"]),
                    "scrolls": int(hr["scrolls"]),
                    "mouse_moves": int(hr["mouse_moves"]),
                    "events": int(hr["events"]),
                }

            return {
                "total_keys": int(row["total_keys"]),
                "total_clicks": int(row["total_clicks"]),
                "total_scrolls": int(row["total_scrolls"]),
                "total_mouse_moves": int(row["total_mouse_moves"]),
                "total_events": int(row["total_events"]),
                "hourly_input": hourly_input,
            }
        finally:
            conn.close()

    def get_deep_work_sessions(self, date_str: str) -> dict:
        """
        Compute deep work sessions for a given date.
        
        A deep work session is a streak of >= 6 consecutive 
        active or high_focus intervals (>= 3 minutes of sustained focus).
        
        Args:
            date_str: Date in YYYY-MM-DD format.
        
        Returns:
            Dict with session_count, total_duration_minutes, 
            longest_session_minutes, and sessions list.
        """
        sql = """
            SELECT timestamp, duration, activity_state
            FROM intervals
            WHERE DATE(timestamp) = %s
            ORDER BY timestamp ASC
        """
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, (date_str,))
            rows = cursor.fetchall()
            cursor.close()

            sessions = []
            current_start = None
            current_len = 0
            current_duration = 0

            for row in rows:
                is_deep = row["activity_state"] in ("active", "high_focus")
                if is_deep:
                    if current_start is None:
                        current_start = row["timestamp"]
                    current_len += 1
                    current_duration += row["duration"]
                else:
                    if current_len >= 6:
                        sessions.append({
                            "start_time": (
                                current_start.isoformat()
                                if isinstance(current_start, datetime)
                                else str(current_start)
                            ),
                            "end_time": (
                                row["timestamp"].isoformat()
                                if isinstance(row["timestamp"], datetime)
                                else str(row["timestamp"])
                            ),
                            "intervals": current_len,
                            "duration_minutes": round(current_duration / 60, 1),
                        })
                    current_start = None
                    current_len = 0
                    current_duration = 0

            # Handle streak at end of data
            if current_len >= 6 and rows:
                sessions.append({
                    "start_time": (
                        current_start.isoformat()
                        if isinstance(current_start, datetime)
                        else str(current_start)
                    ),
                    "end_time": (
                        rows[-1]["timestamp"].isoformat()
                        if isinstance(rows[-1]["timestamp"], datetime)
                        else str(rows[-1]["timestamp"])
                    ),
                    "intervals": current_len,
                    "duration_minutes": round(current_duration / 60, 1),
                })

            total_minutes = sum(s["duration_minutes"] for s in sessions)
            longest = max(
                (s["duration_minutes"] for s in sessions), default=0
            )

            return {
                "session_count": len(sessions),
                "total_duration_minutes": round(total_minutes, 1),
                "longest_session_minutes": round(longest, 1),
                "sessions": sessions,
            }
        finally:
            conn.close()
