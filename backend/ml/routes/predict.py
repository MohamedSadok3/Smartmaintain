from flask import Blueprint, current_app

from shared.auth import require_auth
from shared.http import get_json_body, json_error, json_response

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/predict", methods=["POST"])
@require_auth()
def predict():
    body     = get_json_body()
    machine  = body.get("equipment_type") or body.get("machine")
    features = body.get("features")
    series   = body.get("series")
    sensors  = body.get("sensors")
    plant_id = body.get("plant_id")
    component_id = body.get("component_id")
    version = body.get("model_version") or body.get("version")  # Support version selection

    if not machine:
        return json_error("equipment_type (ou machine) est requis.")
    if features is not None and series is not None:
        return json_error("Fournir features ou series, pas les deux.")
    model_input = {"features": features} if features is not None else {"series": series} if series is not None else sensors
    if not isinstance(model_input, dict):
        return json_error("features, series ou sensors est requis.")

    response, status_code = current_app.extensions["ml_service"].predict_for_machine(
        machine, 
        model_input,
        plant_id=plant_id,
        component_id=component_id,
        version=version
    )
    return json_response(response, status_code)
