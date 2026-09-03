from flask import Blueprint, request

from shared.auth import get_current_user, require_auth
from shared.constants import (
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
    ROLE_SUPERVISEUR,
    ROLE_TECHNICIEN,
    VALID_ROLES,
)
from shared.http import get_json_body, json_error, json_response
from services.user_service import UserService

users_bp = Blueprint('users', __name__)


@users_bp.route("", methods=["GET"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_SUPERVISEUR])
def list_users():
    role = request.args.get("role")
    plant_id = request.args.get("plant_id")
    current_user = get_current_user()
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    if current_role == ROLE_SUPERVISEUR and role != ROLE_TECHNICIEN:
        return json_error("Accès refusé.", 403)

    users = UserService.list_users(role, plant_id, current_role, current_plant_id)
    return json_response({"users": [user.to_dict() for user in users]})


@users_bp.route("", methods=["POST"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def create_user():
    data = get_json_body()
    name = data.get("name")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    role = data.get("role")
    machines = data.get("machines", [])
    plant_id = data.get("plant_id")

    current_user = get_current_user()
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    if not all([name, email, password, role]):
        return json_error("Nom, email, mot de passe et rôle sont requis.")
    if role not in VALID_ROLES:
        return json_error("Rôle invalide.")
    if current_role != ROLE_SUPERADMIN and role == ROLE_SUPERADMIN:
        return json_error("Accès refusé.", 403)
    if not isinstance(machines, list):
        return json_error("Le champ machines doit être un tableau.")
    if current_role == ROLE_SUPERADMIN:
        if role != ROLE_SUPERADMIN and not plant_id:
            return json_error("plant_id est requis pour les utilisateurs non-superadmin.")
    else:
        plant_id = current_plant_id

    user, error = UserService.create_user(name, email, password, role, plant_id, machines)
    if error:
        status_code = 409 if "already exists" in error else 400
        return json_error(error, status_code)

    return json_response({"user": user.to_dict()}, 201)


@users_bp.route("/<int:user_id>", methods=["PATCH"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def update_user(user_id):
    data = get_json_body()
    current_user = get_current_user()
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    user, error = UserService.update_user(user_id, data, current_role, current_plant_id)
    if error:
        return json_error(error, 403 if error == "Forbidden" else 400)

    return json_response({"user": user.to_dict()})


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@require_auth([ROLE_SUPERADMIN, ROLE_ADMIN])
def delete_user(user_id):
    current_user = get_current_user()
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    if UserService.delete_user(user_id, current_role, current_plant_id):
        return json_response({"message": "Utilisateur supprimé avec succès."})
    return json_error("Utilisateur introuvable.", 404)
