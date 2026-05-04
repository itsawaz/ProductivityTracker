"""
ProTrack — Productivity Tracking System
Entry point: orchestrates all modules and starts the application.
"""

import sys
import signal
import logging
import webbrowser
import threading
import config

# ── Logging Setup ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ProTrack")


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("  ProTrack — Productivity Tracking System")
    logger.info("=" * 60)

    # ── 1. Detect Platform ────────────────────────────────────────────
    from tracker.platform_utils import get_platform, create_focus_detector

    try:
        platform = get_platform()
        logger.info(f"Platform: {platform}")
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    # ── 2. Initialize Database ────────────────────────────────────────
    logger.info("Connecting to MySQL and creating tables...")
    try:
        from database.connection import init_pool
        from database.models import create_tables

        init_pool()
        create_tables()
        logger.info("✅ Database ready")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error(
            "Make sure MySQL is running and credentials in config.py are correct."
        )
        sys.exit(1)

    # ── 3. Create Components ──────────────────────────────────────────
    logger.info("Initializing tracker components...")

    # Focus Detector (platform-specific)
    try:
        focus_detector = create_focus_detector()
        logger.info("✅ Focus detector initialized")
    except ImportError as e:
        logger.error(f"❌ Focus detector failed: {e}")
        sys.exit(1)

    # Input Tracker
    from tracker.input_tracker import InputTracker
    input_tracker = InputTracker()

    # Classifier
    from tracker.classifier import Classifier
    classifier = Classifier()

    # Scoring Engine
    from tracker.scoring_engine import ScoringEngine
    scoring_engine = ScoringEngine()

    # Behavioral Engine
    from tracker.behavioral import BehavioralEngine
    behavioral_engine = BehavioralEngine()

    # Repository
    from database.repository import Repository
    repository = Repository()

    # ── 4. Create Flask App & Emitter ─────────────────────────────────
    from server.app import create_app, socketio
    from server.emitter import Emitter
    from server.routes import set_dependencies

    app = create_app()
    emitter = Emitter(socketio)

    # ── 5. Create Interval Aggregator ─────────────────────────────────
    from tracker.interval_aggregator import IntervalAggregator

    aggregator = IntervalAggregator(
        focus_detector=focus_detector,
        input_tracker=input_tracker,
        classifier=classifier,
        scoring_engine=scoring_engine,
        behavioral_engine=behavioral_engine,
        repository=repository,
        emitter=emitter,
    )

    # Set dependencies for API routes
    set_dependencies(aggregator, repository)

    # ── 6. Start Tracking ─────────────────────────────────────────────
    logger.info("Starting tracker...")
    input_tracker.start()
    aggregator.start()
    logger.info("✅ Tracking active")

    # ── 7. Graceful Shutdown Handler ──────────────────────────────────
    def shutdown(sig=None, frame=None):
        logger.info("\n🛑 Shutting down ProTrack...")
        aggregator.stop()
        input_tracker.stop()
        logger.info("Goodbye! 👋")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── 8. Open Dashboard in Browser ──────────────────────────────────
    if config.AUTO_OPEN_BROWSER:
        url = f"http://localhost:{config.SERVER_PORT}"
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
        logger.info(f"🌐 Dashboard will open at {url}")

    # ── 9. Start Flask Server (blocking) ──────────────────────────────
    logger.info(
        f"🚀 Starting server on {config.SERVER_HOST}:{config.SERVER_PORT}"
    )
    logger.info("─" * 60)

    try:
        socketio.run(
            app,
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            debug=config.SERVER_DEBUG,
            use_reloader=False,
            log_output=False,
        )
    except Exception as e:
        logger.error(f"Server error: {e}")
        shutdown()


if __name__ == "__main__":
    main()
