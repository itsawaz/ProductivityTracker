"""
REST API Routes — Endpoints for the dashboard.
"""

import logging
from datetime import datetime, timedelta
from flask import render_template, jsonify, request

logger = logging.getLogger(__name__)

# These will be set by main.py after initialization
_aggregator = None
_repository = None


def set_dependencies(aggregator, repository):
    """Set the aggregator and repository instances for route handlers."""
    global _aggregator, _repository
    _aggregator = aggregator
    _repository = repository


def register_routes(app):
    """Register all API routes on the Flask app."""

    @app.route("/")
    def index():
        """Serve the main dashboard page."""
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        """Get current real-time tracking status."""
        if _aggregator is None:
            return jsonify({"error": "Tracker not initialized"}), 503
        return jsonify(_aggregator.get_status())

    @app.route("/api/today")
    def api_today():
        """Get today's summary metrics."""
        if _aggregator is None:
            return jsonify({"error": "Tracker not initialized"}), 503

        status = _aggregator.get_status()
        today = datetime.now().strftime("%Y-%m-%d")

        # Get hourly breakdown
        hourly = {}
        if _repository:
            try:
                hourly = _repository.get_hourly_breakdown(today)
            except Exception as e:
                logger.error(f"Error fetching hourly breakdown: {e}")

        return jsonify({
            "date": today,
            "productive_hours": status["productive_hours"],
            "productive_seconds": status["productive_seconds"],
            "total_seconds": status["total_seconds"],
            "idle_seconds": status["idle_seconds"],
            "efficiency": status["efficiency"],
            "max_streak": status["max_streak"],
            "interruptions": status["interruptions"],
            "hourly_breakdown": hourly,
        })

    @app.route("/api/hourly/<date_str>")
    def api_hourly(date_str):
        """Get hourly breakdown for a specific date."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        try:
            breakdown = _repository.get_hourly_breakdown(date_str)
            return jsonify({
                "date": date_str,
                "hourly": breakdown,
            })
        except Exception as e:
            logger.error(f"Error in /api/hourly: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/daily")
    def api_daily():
        """Get daily summaries for a date range."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        end_date = request.args.get(
            "end", datetime.now().strftime("%Y-%m-%d")
        )
        start_date = request.args.get(
            "start",
            (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        )

        try:
            summaries = _repository.get_daily_summaries(start_date, end_date)
            return jsonify({
                "start": start_date,
                "end": end_date,
                "summaries": summaries,
            })
        except Exception as e:
            logger.error(f"Error in /api/daily: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/streaks/<date_str>")
    def api_streaks(date_str):
        """Get focus streak data for a specific date."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        try:
            streaks = _repository.get_focus_streaks(date_str)
            return jsonify({
                "date": date_str,
                "streaks": streaks,
            })
        except Exception as e:
            logger.error(f"Error in /api/streaks: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/intervals")
    def api_intervals():
        """Get raw interval data."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        date_str = request.args.get(
            "date", datetime.now().strftime("%Y-%m-%d")
        )
        limit = int(request.args.get("limit", 50))

        try:
            intervals = _repository.get_intervals_for_date(date_str, limit)
            return jsonify({
                "date": date_str,
                "intervals": intervals,
            })
        except Exception as e:
            logger.error(f"Error in /api/intervals: {e}")
            return jsonify({"error": str(e)}), 500
