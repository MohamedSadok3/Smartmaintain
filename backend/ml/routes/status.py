from flask import Blueprint, current_app, request

from shared.auth import require_auth
from shared.http import json_response

status_bp = Blueprint("status", __name__)


@status_bp.route("", methods=["GET"])
@require_auth()
def status():
    # Support version query parameter: /api/ml/status?version=v7
    version = request.args.get("version")
    response = current_app.extensions["ml_service"].get_status(version=version)
    return json_response(response)
