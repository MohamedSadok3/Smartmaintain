from flask import Blueprint, request

from shared.auth import get_current_user, require_auth
from shared.constants import ROLE_ADMIN, ROLE_SUPERADMIN
from shared.http import get_json_body, json_error, json_response
from services.plant_service import PlantService

plants_bp = Blueprint('plants', __name__)


@plants_bp.route("/me", methods=["GET"])
@require_auth([ROLE_ADMIN])
def get_my_plant():
    plant_id = get_current_user().get("plant_id")
    if not plant_id:
        return json_error("Aucune usine assignée.", 400)

    plant = PlantService.get_my_plant(plant_id)
    if not plant:
        return json_error("Usine introuvable.", 404)

    return json_response({"plant": plant.to_dict()})


@plants_bp.route("/me", methods=["PATCH"])
@require_auth([ROLE_ADMIN])
def update_my_plant():
    plant_id = get_current_user().get("plant_id")
    if not plant_id:
        return json_error("Aucune usine assignée.", 400)

    data = get_json_body()
    plant, error = PlantService.update_my_plant(plant_id, data)
    if error:
        return json_error(error)

    return json_response({"plant": plant.to_dict()})


@plants_bp.route("", methods=["GET"])
@require_auth([ROLE_SUPERADMIN])
def list_plants():
    """List all plants."""
    status = request.args.get("status")
    plants = PlantService.list_plants(status)
    return json_response({"plants": [plant.to_dict() for plant in plants]})


@plants_bp.route("/<int:plant_id>", methods=["PATCH"])
@require_auth([ROLE_SUPERADMIN])
def update_plant_by_superadmin(plant_id):
    """Update plant by superadmin (not allowed)."""
    return json_error("Le superadmin ne peut pas modifier les informations d'une usine.", 403)


@plants_bp.route("/<int:plant_id>", methods=["DELETE"])
@require_auth([ROLE_SUPERADMIN])
def delete_plant_by_superadmin(plant_id):
    """Delete plant and all related data."""
    if PlantService.delete_plant(plant_id):
        return json_response({"message": "Usine et données associées supprimées avec succès."})
    return json_error("Usine introuvable ou impossible à supprimer.", 404)


@plants_bp.route("/<int:plant_id>/overview", methods=["GET"])
@require_auth([ROLE_SUPERADMIN])
def get_plant_overview(plant_id):
    """Get comprehensive plant overview."""
    overview = PlantService.get_plant_overview(plant_id)
    if not overview:
        return json_error("Usine introuvable.", 404)

    return json_response(
        {
            "plant": overview["plant"].to_dict(),
            "users": [user.to_dict() for user in overview["users"]],
            "kpis": overview["kpis"],
        }
    )
