import logging

from flask import Blueprint, current_app, request

from shared.auth import get_current_user, require_auth
from shared.constants import (
    ALERT_ACTION_ACKNOWLEDGE,
    ALERT_ACTION_ASSIGN,
    ALERT_ACTION_REOPEN,
    ALERT_ACTION_RESOLVE,
    ALERT_SUPPORTED_ACTIONS,
    ROLE_SUPERADMIN,
    ROLE_TECHNICIEN,
)
from shared.http import get_json_body, json_error, json_response
from services.alert_service import AlertService
from services.exceptions import (
    AlertNotFoundException,
    InvalidStatusTransitionException,
    TechnicianNotEligibleException,
    UnauthorizedActionException,
)

alerts_bp = Blueprint("alerts", __name__)
logger = logging.getLogger(__name__)

SUPPORTED_ACTIONS = ALERT_SUPPORTED_ACTIONS


def _resolve_patch_action(data):
    """Détermine l'action PATCH à partir du body (action explicite ou champs legacy)."""
    action = data.get("action")
    if action:
        return action
    if "assigned_to" in data:
        return ALERT_ACTION_ASSIGN
    if data.get("acknowledged") is True:
        return ALERT_ACTION_ACKNOWLEDGE
    if data.get("status") == "resolved":
        return ALERT_ACTION_RESOLVE
    if data.get("status") == "reopened":
        return ALERT_ACTION_REOPEN
    return None


@alerts_bp.route("", methods=["GET"])
@require_auth()
def list_alertes():
    current_user = get_current_user()
    filters = {
        "machine": request.args.get("machine"),
        "severity": request.args.get("severity"),
        "status": request.args.get("status"),
        "acknowledged": request.args.get("acknowledged"),
        "page": request.args.get("page", 1),
        "limit": request.args.get("limit", 20),
    }

    try:
        alerts, page, limit = AlertService().list_alerts(current_user, filters)
    except ValueError as e:
        return json_error(str(e))

    return json_response(
        {
            "alerts": [alert.to_dict() for alert in alerts],
            "page": page,
            "limit": limit,
        }
    )


@alerts_bp.route("/<int:alert_id>", methods=["GET"])
@require_auth()
def get_alerte(alert_id):
    current_user = get_current_user()
    alert = AlertService().get_alert_with_users(alert_id)
    if not alert:
        return json_error("Alert not found.", 404)

    if current_user.get("role") != ROLE_SUPERADMIN and alert.plant_id != current_user.get("plant_id"):
        return json_error("Forbidden", 403)

    if current_user.get("role") == ROLE_TECHNICIEN and alert.assigned_to != int(current_user.get("sub")):
        return json_error("Forbidden", 403)

    return json_response({"alert": alert.to_dict()})


@alerts_bp.route("/<int:alert_id>", methods=["PATCH"])
@require_auth()
def patch_alerte(alert_id):
    """Met à jour une alerte selon l'action demandée dans le body JSON."""
    current_user = get_current_user()
    data = get_json_body()
    action = _resolve_patch_action(data)

    if not action or action not in SUPPORTED_ACTIONS:
        return json_error(
            "Action non supportée. Utilisez assign, acknowledge, resolve ou reopen.",
            400,
        )

    alert_service = AlertService()

    try:
        if action == ALERT_ACTION_ASSIGN:
            alert = alert_service.assign_alert(alert_id, data, current_user)
        elif action == ALERT_ACTION_ACKNOWLEDGE:
            alert = alert_service.acknowledge_alert(alert_id, data, current_user)
        elif action == ALERT_ACTION_RESOLVE:
            alert = alert_service.resolve_alert(alert_id, data, current_user)
        else:
            alert = alert_service.reopen_alert(alert_id, data, current_user)
    except AlertNotFoundException as e:
        return json_error(str(e), 404)
    except UnauthorizedActionException as e:
        return json_error(str(e), 403)
    except InvalidStatusTransitionException as e:
        return json_error(str(e), 400)
    except TechnicianNotEligibleException as e:
        return json_error(str(e), 400)
    except Exception:
        logger.exception("Erreur inattendue lors de la mise à jour de l'alerte %s", alert_id)
        return json_error("Erreur interne du serveur.", 500)

    payload = alert.to_dict()
    if hasattr(current_app, "socketio"):
        current_app.socketio.emit("alert:updated", payload)

    return json_response({"alert": payload})
