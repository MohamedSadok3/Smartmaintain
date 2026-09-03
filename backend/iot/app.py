import threading

from flask import Flask, jsonify
from flask_cors import CORS

from shared.config import get_env
from shared.constants import IOT_DEFAULT_PORT
from routes.iot import iot_bp
from services.replay_service import ReplayService


def create_app():
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)
    CORS(flask_app)
    flask_app.register_blueprint(iot_bp, url_prefix="/api/iot")

    @flask_app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "iot"})

    return flask_app


def create_and_start_services():
    """Start background replay threads."""
    replay_service = ReplayService()
    replay_service.start_replay_threads()
    return replay_service


app = create_app()

# Start background services when the module is loaded by a WSGI server
_replay_service = create_and_start_services()


if __name__ == "__main__":
    port = int(get_env("IOT_PORT", str(IOT_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
