import logging
import threading

from flask import Flask
from flask_cors import CORS

from shared.config import get_env
from shared.constants import ML_DEFAULT_PORT
from routes.predict import ml_bp
from routes.status import status_bp
from services.ml_service import MLService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app(ml_service=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    app.extensions["ml_service"] = ml_service or MLService()
    app.register_blueprint(ml_bp, url_prefix="/api/ml")
    app.register_blueprint(status_bp, url_prefix="/api/ml/status")

    @app.route("/health", methods=["GET"])
    def health():
        ml_service = app.extensions["ml_service"]
        return {
            "status": "ok",
            "service": "ml",
            "model_version": ml_service.default_version,
            "available_versions": ml_service.engine.get_available_versions(),
        }

    return app


def create_and_start_services(app):
    """Initialize services and start background threads."""
    ml_service = app.extensions["ml_service"]
    consumer_thread = threading.Thread(target=ml_service.consume_sensor_data, daemon=True)
    consumer_thread.start()
    return ml_service


# Start the Redis consumer when the module is loaded by any WSGI server
# (gunicorn, eventlet, etc.) — not just when run directly.
app = create_app()
_ml_service = create_and_start_services(app)


if __name__ == "__main__":
    port = int(get_env("ML_PORT", str(ML_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
