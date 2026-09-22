from flask import Flask
from flask_cors import CORS

from shared.config import get_env
from shared.constants import AUTH_DEFAULT_PORT
from routes.auth import auth_bp
from routes.users import users_bp
from routes.plants import plants_bp
from routes.components import components_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024
    CORS(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(plants_bp, url_prefix='/api/plants')
    app.register_blueprint(components_bp, url_prefix='/api/components')

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "auth"}

    return app


app = create_app()


if __name__ == "__main__":
    port = int(get_env("AUTH_PORT", str(AUTH_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
