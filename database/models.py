"""
Database Models — MySQL schema creation and migrations.
"""

import logging
from database.connection import get_connection

logger = logging.getLogger(__name__)

SCHEMA_SQL = [
    # ── Intervals table ──────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS intervals (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        duration INT DEFAULT 30,
        vdi_active TINYINT(1) DEFAULT 0,
        key_count INT DEFAULT 0,
        mouse_move_count INT DEFAULT 0,
        mouse_click_count INT DEFAULT 0,
        scroll_count INT DEFAULT 0,
        total_events INT DEFAULT 0,
        activity_state VARCHAR(20) DEFAULT 'idle',
        raw_weight FLOAT DEFAULT 0.0,
        adjusted_weight FLOAT DEFAULT 0.0,
        productive_seconds FLOAT DEFAULT 0.0,
        INDEX idx_intervals_timestamp (timestamp)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,

    # ── Daily Summary table ──────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS daily_summary (
        id INT AUTO_INCREMENT PRIMARY KEY,
        date DATE UNIQUE NOT NULL,
        total_logged_seconds INT DEFAULT 0,
        productive_seconds FLOAT DEFAULT 0.0,
        idle_seconds INT DEFAULT 0,
        efficiency FLOAT DEFAULT 0.0,
        max_focus_streak INT DEFAULT 0,
        interruptions INT DEFAULT 0,
        hourly_breakdown JSON,
        INDEX idx_daily_date (date)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]


def create_tables():
    """
    Create all required tables if they don't exist.
    Safe to call multiple times.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        for sql in SCHEMA_SQL:
            cursor.execute(sql)
        cursor.close()
        logger.info("Database tables created / verified successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise
    finally:
        conn.close()
