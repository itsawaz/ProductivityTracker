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

    @app.route("/api/debug/vdi")
    def api_debug_vdi():
        """Debug endpoint: show VDI detection state."""
        if _aggregator is None:
            return jsonify({"error": "Tracker not initialized"}), 503
        try:
            detector = _aggregator._focus_detector
            if hasattr(detector, 'get_vdi_app_info'):
                return jsonify(detector.get_vdi_app_info())
            return jsonify({
                "is_vdi_active": detector.is_vdi_active(),
                "active_app": detector.get_active_app_name(),
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

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

    @app.route("/api/summary/<date_str>")
    def api_summary(date_str):
        """Get full summary for a specific date (works for past days too)."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        today = datetime.now().strftime("%Y-%m-%d")
        is_today = (date_str == today)

        try:
            # Get totals from DB
            totals = _repository.get_today_totals(date_str)
            hourly = _repository.get_hourly_breakdown(date_str)

            productive_secs = totals["productive_seconds"]
            total_secs = totals["total_seconds"]
            idle_secs = totals["idle_seconds"]

            # For today, use live in-memory values if aggregator is running
            if is_today and _aggregator:
                status = _aggregator.get_status()
                productive_secs = status["productive_seconds"]
                total_secs = status["total_seconds"]
                idle_secs = status["idle_seconds"]

            # Calculate VDI seconds from intervals
            vdi_secs = 0
            for h, info in hourly.items():
                # Estimate VDI seconds from intervals that were VDI-active
                pass  # Will use insights for VDI data

            efficiency = (productive_secs / total_secs * 100) if total_secs > 0 else 0
            prod_hrs = int(productive_secs // 3600)
            prod_mins = int((productive_secs % 3600) // 60)

            return jsonify({
                "date": date_str,
                "is_today": is_today,
                "productive_seconds": round(productive_secs, 1),
                "productive_hours": f"{prod_hrs}h {prod_mins:02d}m",
                "total_seconds": total_secs,
                "idle_seconds": idle_secs,
                "efficiency": round(efficiency, 1),
                "interval_count": totals["interval_count"],
                "hourly_breakdown": hourly,
            })
        except Exception as e:
            logger.error(f"Error in /api/summary: {e}")
            return jsonify({"error": str(e)}), 500

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

    @app.route("/api/insights/<date_str>")
    def api_insights(date_str):
        """Get comprehensive insights for a specific date."""
        if _repository is None:
            return jsonify({"error": "Repository not initialized"}), 503

        try:
            # VDI Focus Stats
            vdi_stats = _repository.get_vdi_focus_stats(date_str)

            # Input Totals
            input_totals = _repository.get_input_totals(date_str)

            # Deep Work Sessions
            deep_work = _repository.get_deep_work_sessions(date_str)

            # Peak Productivity Hour (from hourly breakdown)
            hourly = _repository.get_hourly_breakdown(date_str)
            peak_hour = None
            peak_weight = 0
            for hour, info in hourly.items():
                if info["avg_weight"] > peak_weight:
                    peak_weight = info["avg_weight"]
                    peak_hour = hour

            # Today totals
            totals = _repository.get_today_totals(date_str)

            return jsonify({
                "date": date_str,
                "vdi_stats": vdi_stats,
                "input_totals": input_totals,
                "deep_work": deep_work,
                "peak_hour": peak_hour,
                "peak_weight": round(peak_weight, 4),
                "totals": totals,
                "hourly_breakdown": hourly,
            })
        except Exception as e:
            logger.error(f"Error in /api/insights: {e}")
            return jsonify({"error": str(e)}), 500
