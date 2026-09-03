from flask import Blueprint, request

from shared.auth import get_current_user, require_auth
from shared.constants import (
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
    ROLE_SUPERVISEUR,
    ROLE_TECHNICIEN,
)
from shared.http import get_json_body, json_error, json_response
from services.component_service import ComponentService

components_bp = Blueprint("components", __name__)


@components_bp.route("", methods=["GET"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_SUPERVISEUR, ROLE_TECHNICIEN])
def list_components():
    current_user = get_current_user()
    plant_id = request.args.get("plant_id")
    components = ComponentService.list_components(
        current_user.get("role"),
        current_user.get("plant_id"),
        plant_id,
    )
    return json_response({"components": [component.to_dict() for component in components]})


@components_bp.route("", methods=["POST"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def create_component():
    data = get_json_body()
    name = (data.get("name") or "").strip()
    component_type = (data.get("type") or "").strip().lower()
    if not name or not component_type:
        return json_error("name and type are required.")

    enabled = bool(data.get("enabled", True))
    current_user = get_current_user()
    component, error = ComponentService.create_component(
        name,
        component_type,
        enabled,
        current_user.get("role"),
        current_user.get("plant_id"),
        data.get("plant_id"),
    )

    if error:
        status = 409 if "already exists" in error else 400
        return json_error(error, status)

    return json_response({"component": component.to_dict()}, 201)


@components_bp.route("/<int:component_id>", methods=["PATCH"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def update_component(component_id):
    data = get_json_body()
    current_user = get_current_user()
    component, error = ComponentService.update_component(
        component_id,
        data,
        current_user.get("role"),
        current_user.get("plant_id"),
    )

    if error:
        status = 409 if "already exists" in error else 400
        return json_error(error, status)

    return json_response({"component": component.to_dict()})


@components_bp.route("/<int:component_id>", methods=["DELETE"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def delete_component(component_id):
    current_user = get_current_user()
    if ComponentService.delete_component(
        component_id,
        current_user.get("role"),
        current_user.get("plant_id"),
    ):
        return json_response({"message": "Component deleted successfully."})
    return json_error("Component not found.", 404)
