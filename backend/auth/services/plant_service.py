from shared.database import get_db_connection
from models import Plant, User
from queries import (
    PLANT_SELECT_LIST,
    PLANT_SELECT_BY_ID,
    PLANT_UPDATE_RETURNING,
    PLANT_SELECT_USERS_FOR_OVERVIEW,
    PLANT_COUNT_USERS,
    PLANT_COUNT_ADMINS,
    PLANT_COUNT_SUPERVISORS,
    PLANT_COUNT_TECHNICIANS,
    PLANT_COUNT_COMPONENTS,
    PLANT_COUNT_TOTAL_ALERTS,
    PLANT_COUNT_OPEN_ALERTS,
    PLANT_COUNT_RESOLVED_ALERTS,
    PLANT_DELETE_INTERVENTIONS,
    PLANT_DELETE_ALERTS,
    PLANT_DELETE_COMPONENTS,
    PLANT_DELETE_USERS,
    PLANT_DELETE,
)


class PlantService:
    @staticmethod
    def _extract_count(row):
        """Handle both RealDictCursor and tuple cursor formats safely."""
        if row is None:
            return 0
        if isinstance(row, dict):
            return int(row.get("count", 0))
        return int(row[0])

    @staticmethod
    def list_plants(status=None):
        """List plants with optional status filter."""
        filters = []
        values = []
        if status:
            filters.append("status = %s")
            values.append(status)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    PLANT_SELECT_LIST.format(where_clause=where_clause),
                    tuple(values),
                )
                rows = cur.fetchall()
                return Plant.from_rows(rows)

    @staticmethod
    def get_plant_by_id(plant_id):
        """Get plant by ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(PLANT_SELECT_BY_ID, (plant_id,))
                row = cur.fetchone()
                return Plant.from_row(row)

    @staticmethod
    def get_my_plant(plant_id):
        """Get plant for admin user."""
        return PlantService.get_plant_by_id(plant_id)

    @staticmethod
    def update_my_plant(plant_id, updates):
        """Update plant information by admin."""
        allowed = {"name", "contact_name", "contact_email", "contact_phone", "location", "industry", "description"}
        fields = []
        values = []
        for key in allowed:
            if key in updates:
                fields.append(f"{key} = %s")
                values.append((updates.get(key) or "").strip() or None)

        if not fields:
            return None, "No valid fields to update."

        values.append(plant_id)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    PLANT_UPDATE_RETURNING.format(fields=", ".join(fields)),
                    tuple(values),
                )
                row = cur.fetchone()
                plant = Plant.from_row(row)
                conn.commit()
                return plant, None

    @staticmethod
    def get_plant_overview(plant_id):
        """Get comprehensive plant overview with users and KPIs."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(PLANT_SELECT_BY_ID, (plant_id,))
                plant = Plant.from_row(cur.fetchone())
                if not plant:
                    return None

                cur.execute(PLANT_SELECT_USERS_FOR_OVERVIEW, (plant_id,))
                rows = cur.fetchall()
                users = User.from_rows(rows)

                cur.execute(PLANT_COUNT_USERS, (plant_id,))
                users_count = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_ADMINS, (plant_id,))
                admins_count = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_SUPERVISORS, (plant_id,))
                supervisors_count = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_TECHNICIANS, (plant_id,))
                technicians_count = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_COMPONENTS, (plant_id,))
                components_count = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_TOTAL_ALERTS, (plant_id,))
                total_alerts = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_OPEN_ALERTS, (plant_id,))
                open_alerts = PlantService._extract_count(cur.fetchone())
                cur.execute(PLANT_COUNT_RESOLVED_ALERTS, (plant_id,))
                resolved_alerts = PlantService._extract_count(cur.fetchone())

        return {
            "plant": plant,
            "users": users,
            "kpis": {
                "users_count": users_count,
                "admins_count": admins_count,
                "supervisors_count": supervisors_count,
                "technicians_count": technicians_count,
                "components_count": components_count,
                "total_alerts": total_alerts,
                "open_alerts": open_alerts,
                "resolved_alerts": resolved_alerts,
            },
        }

    @staticmethod
    def delete_plant(plant_id):
        """Delete plant and all related data."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                plant = PlantService.get_plant_by_id(plant_id)
                if not plant:
                    return False
                if plant.code == "usine-demo":
                    return False

                cur.execute(PLANT_DELETE_INTERVENTIONS, (plant_id,))
                cur.execute(PLANT_DELETE_ALERTS, (plant_id,))
                cur.execute(PLANT_DELETE_COMPONENTS, (plant_id,))
                cur.execute(PLANT_DELETE_USERS, (plant_id,))
                cur.execute(PLANT_DELETE, (plant_id,))
                conn.commit()
                return True
