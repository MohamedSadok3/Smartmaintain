from flask import Blueprint, request

from shared.auth import get_current_user, require_auth
from shared.constants import ROLE_SUPERADMIN
from shared.http import get_json_body, json_error, json_response
from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = get_json_body()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return json_error("Email et mot de passe sont requis.")

    user = AuthService.authenticate_user(email, password)
    if not user:
        return json_error("Identifiants invalides.", 401)

    token = AuthService.create_user_token(user)
    return json_response({"token": token, "user": user.to_dict()})


@auth_bp.route("/me", methods=["GET"])
@require_auth()
def me():
    current_user = get_current_user()
    user = AuthService.get_user_by_id(int(current_user["sub"]))

    if not user:
        return json_error("Utilisateur introuvable.", 404)

    return json_response({"user": user.to_dict()})


@auth_bp.route("/me", methods=["PATCH"])
@require_auth()
def update_me():
    current_user = get_current_user()
    data = get_json_body()
    user, error = AuthService.update_profile(int(current_user["sub"]), data)

    if error:
        status_code = 400
        if error == "Utilisateur introuvable.":
            status_code = 404
        return json_error(error, status_code)

    return json_response({"user": user.to_dict()})


@auth_bp.route("/register-plant", methods=["POST"])
def register_plant():
    from services.registration_service import RegistrationService

    data = get_json_body()
    plant = data.get("plant") or {}
    users = data.get("users") or {}
    documents = data.get("documents") or {}

    service = RegistrationService()
    registration, error = service.register_plant(plant, users, documents)
    if error:
        return json_error(error)

    return json_response({"registration": registration.to_dict()}, 201)


@auth_bp.route("/registrations", methods=["GET"])
@require_auth([ROLE_SUPERADMIN])
def list_registrations():
    from services.registration_service import RegistrationService

    status = request.args.get("status", "pending")
    service = RegistrationService()
    registrations = service.list_registrations(status)
    return json_response({"registrations": [item.to_dict() for item in registrations]})


@auth_bp.route("/registrations/<int:registration_id>/review", methods=["PATCH"])
@require_auth([ROLE_SUPERADMIN])
def review_registration(registration_id):
    from services.registration_service import RegistrationService

    data = get_json_body()
    action = (data.get("action") or "").strip().lower()
    review_note = (data.get("note") or "").strip() or None
    reviewer_id = int(get_current_user()["sub"])

    service = RegistrationService()
    result, extra = service.review_registration(registration_id, action, review_note, reviewer_id)
    if result is None:
        return json_error(extra or "Échec du traitement de l'inscription.")

    response = {"registration": result.to_dict()}
    if extra is not None:
        response["plant"] = extra.to_dict()

    return json_response(response)
