"""
Flask Application Factory + SocketIO Initialization.
"""

import os
import logging
from flask import Flask
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

socketio = SocketIO()


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Configured Flask app instance.
    """
    # Resolve paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, "dashboard", "templates")
    static_dir = os.path.join(project_root, "dashboard", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
    )
    app.config["SECRET_KEY"] = "productivity-tracker-local-secret"

    # Initialize SocketIO
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")

    # Register routes
    from server.routes import register_routes
    register_routes(app)

    # Register SocketIO events
    from server.emitter import register_socket_events
    register_socket_events(socketio)

    logger.info("Flask app created successfully")
    return app
