from flask import Blueprint
from datetime import datetime, timezone

from shared.auth import get_current_user, require_auth
from shared.constants import MACHINE_TYPES, ROLE_ADMIN, ROLE_SUPERADMIN
from shared.http import get_json_body, json_error, json_response
from shared.timezone_utils import now_local, format_iso_local
from services.config_service import ConfigService
from services.replay_service import ReplayService

iot_bp = Blueprint("iot", __name__)
config_service = ConfigService()
injection_service = ReplayService()


@iot_bp.route("/status", methods=["GET"])
@require_auth()
def status():
    return json_response({"status": "ok", "service": "iot"})


@iot_bp.route("/config", methods=["GET"])
@require_auth([ROLE_ADMIN])
def get_config():
    current_user = get_current_user()
    plant_id = current_user.get("plant_id")
    if not plant_id:
        return json_error("Aucune usine associée à cet administrateur.", 403)

    mqtt, sensors = config_service.get_config(int(plant_id))
    return json_response(
        {
            "mqtt": mqtt.to_dict() if mqtt else None,
            "sensors": [item.to_dict() for item in sensors],
        }
    )


@iot_bp.route("/config", methods=["POST"])
@require_auth([ROLE_ADMIN])
def save_config():
    current_user = get_current_user()
    plant_id = current_user.get("plant_id")
    if not plant_id:
        return json_error("Aucune usine associée à cet administrateur.", 403)

    body = get_json_body()
    mqtt_payload = body.get("mqtt")
    sensors_payload = body.get("sensors")

    if not mqtt_payload and not sensors_payload:
        return json_error("Aucune donnée de configuration fournie.")

    mqtt, sensors = config_service.save_config(
        int(plant_id),
        mqtt_payload=mqtt_payload,
        sensors_payload=sensors_payload,
    )
    return json_response(
        {
            "mqtt": mqtt.to_dict() if mqtt else None,
            "sensors": [item.to_dict() for item in sensors],
        }
    )


@iot_bp.route("/config/test", methods=["POST"])
@require_auth([ROLE_ADMIN])
def test_mqtt_config():
    body = get_json_body()
    host = body.get("host")
    port = body.get("port", 1883)
    username = body.get("username")
    password = body.get("password")

    ok, message = config_service.test_mqtt_connection(host, port, username, password)
    if not ok:
        return json_error(message, 400)
    return json_response({"message": message})


@iot_bp.route("/inject", methods=["POST"])
@require_auth([ROLE_ADMIN, ROLE_SUPERADMIN])
def inject():
    body      = get_json_body()
    machine   = body.get("machine")
    sensors   = body.get("sensors")
    timestamp = body.get("timestamp")
    current_user = get_current_user()
    plant_id = current_user.get("plant_id")
    if current_user.get("role") == ROLE_SUPERADMIN:
        plant_id = body.get("plant_id")

    if machine not in MACHINE_TYPES:
        return json_error("Invalid machine.")
    if not isinstance(sensors, dict):
        return json_error("sensors must be an object.")
    if plant_id is None:
        return json_error("plant_id est requis.", 400)

    service = injection_service
    # Allow caller to override the plant_id for this injection
    service.plant_id = int(plant_id)
    ts = timestamp or format_iso_local(now_local())

    try:
        if machine == "moteur":
            # Motor expects pre-computed VBL features in the sensors dict
            row = {"timestamp": ts, **sensors}
            payload = service.publish_motor_features(row)
        else:
            # Other machines: build a full sensor window from the arrays in sensors
            from shared.ml_config import WINDOW_SIZES
            window_size = WINDOW_SIZES.get(machine, 1)
            sensor_map = service.SENSOR_MAPPINGS.get(machine, {})
            # sensors is {v7_name: [values...]}, convert to CSV-column-keyed row
            row_base = {"timestamp": ts}
            for v7_name, csv_col in sensor_map.items():
                vals = sensors.get(v7_name, [])
                row_base[csv_col] = float(vals[-1]) if isinstance(vals, list) and vals else (float(vals) if vals else 0.0)
            # Replicate row to fill the required window size
            window = [row_base] * window_size
            # Skip normalization for manual injections to ensure anomalies are detected
            payload = service.publish_machine_window(machine, window, skip_normalization=True)
    except Exception as exc:
        return json_error(f"Injection error: {exc}", 500)

    if payload is None:
        return json_error("unsupported_raw_input", 422)
    return json_response({"message": "Injected", "payload": payload}, 201)
