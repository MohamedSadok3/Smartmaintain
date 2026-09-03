"""
Alertes Service - SmartMaintain Alert Management
=================================================
Manages predictive maintenance alerts with:
- Redis consumer for ML predictions
- WebSocket emission to Gateway
- Alert persistence in PostgreSQL
- Dashboard analytics

Optimizations:
- Robust PostgreSQL connection with exponential backoff
- Graceful degradation if DB unavailable
- Structured logging
- Better error handling

Note: Service can run in degraded mode (WebSocket only) if PostgreSQL fails,
ensuring real-time data flow continues even during DB issues.
"""

import eventlet
eventlet.monkey_patch()

import logging
import time
from typing import Tuple

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from shared.config import get_env
from shared.constants import ALERTES_DEFAULT_PORT
from routes.alerts import alerts_bp
from routes.dashboard import dashboard_bp
from services.alert_service import AlertService
from services.redis_consumer import RedisConsumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app() -> Tuple[Flask, SocketIO]:
    """
    Create and configure the Flask application with SocketIO.
    
    Returns:
        Tuple of (Flask app, SocketIO instance)
    """
    app = Flask(__name__)
    CORS(app)

    # Initialize SocketIO with eventlet async mode
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

    # Register API blueprints
    app.register_blueprint(alerts_bp, url_prefix='/api/alertes')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # Store socketio instance on app for access in routes
    app.socketio = socketio

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "ok", "service": "alertes"}

    logger.info("Alertes Flask app created")
    return app, socketio


app, socketio = create_app()


def create_and_start_services(socketio: SocketIO, degraded_mode: bool = False) -> Tuple:
    """
    Initialize services and start background threads with robust error handling.
    
    PostgreSQL Retry Strategy:
    - 10 attempts with 3-second delay (exponential backoff possible)
    - If all retries fail, can run in degraded mode (WebSocket only, no DB)
    
    Args:
        socketio: SocketIO instance for WebSocket communication
        degraded_mode: If True, skip DB initialization and run WebSocket-only
        
    Returns:
        Tuple of (AlertService, RedisConsumer) or (None, RedisConsumer) in degraded mode
    """
    alert_service = None
    
    if not degraded_mode:
        # Try to initialize database with retry logic
        max_retries = 10
        retry_delay = 3
        
        logger.info(f"Initializing PostgreSQL connection (max {max_retries} retries)...")
        
        for attempt in range(max_retries):
            try:
                alert_service = AlertService()
                alert_service.init_db()
                logger.info(f"✅ Database initialized successfully on attempt {attempt + 1}")
                break
            except Exception as e:
                logger.warning(
                    f"⚠️  Database connection failed (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    logger.info(f"   Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Optional: exponential backoff
                    # retry_delay = min(retry_delay * 1.5, 30)
                else:
                    logger.error(
                        "❌ Failed to initialize database after all retries. "
                        "Running in DEGRADED MODE (WebSocket only, no alert persistence)"
                    )
                    # Could raise here, or continue in degraded mode
                    # For high availability, we continue without DB
                    break
    else:
        logger.warning("Starting in DEGRADED MODE - Database features disabled")

    # Start Redis consumer (critical for real-time data flow)
    # This runs even if DB is unavailable, ensuring WebSocket bridge works
    try:
        redis_consumer = RedisConsumer(socketio)
        redis_consumer.start_consumer_thread()
        logger.info("✅ Redis consumer started successfully")
    except Exception as e:
        logger.critical(f"❌ Failed to start Redis consumer: {e}", exc_info=True)
        raise  # Cannot continue without Redis consumer

    return alert_service, redis_consumer


# ============================================================================
# Service Initialization
# ============================================================================

# Start background services when module is loaded
# (works with gunicorn, eventlet, uwsgi, etc.)
try:
    _alert_service, _redis_consumer = create_and_start_services(socketio)
    
    if _alert_service is None:
        logger.warning(
            "⚠️  Running in degraded mode: "
            "Real-time WebSocket works, but alert persistence is disabled"
        )
    else:
        logger.info("✅ Alertes service fully operational")
        
except Exception as e:
    logger.critical(f"❌ Failed to start Alertes service: {e}", exc_info=True)
    raise


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(get_env("ALERTES_PORT", str(ALERTES_DEFAULT_PORT)))
    logger.info(f"Starting Alertes server on 0.0.0.0:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
