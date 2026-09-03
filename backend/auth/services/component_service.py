import time
from psycopg2 import errors

from shared.constants import MACHINE_TYPES, ROLE_SUPERADMIN
from shared.database import get_db_connection
from models import Component
from queries import (
    COMPONENT_SELECT_LIST,
    COMPONENT_INSERT,
    COMPONENT_SELECT_FOR_PLANT_CHECK,
    COMPONENT_UPDATE_RETURNING,
    COMPONENT_DELETE_SUPERADMIN,
    COMPONENT_DELETE_BY_PLANT,
)


class ComponentService:
    @staticmethod
    def list_components(current_role=None, current_plant_id=None, plant_id=None):
        """List components with role-based filtering."""
        filters = []
        values = []
        if current_role == "superadmin":
            if plant_id:
                filters.append("plant_id = %s")
                values.append(int(plant_id))
        else:
            filters.append("plant_id = %s")
            values.append(current_plant_id)

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    COMPONENT_SELECT_LIST.format(where_clause=where_clause),
                    tuple(values),
                )
                rows = cur.fetchall()
                return Component.from_rows(rows)

    @staticmethod
    def create_component(name, component_type, enabled=True, current_role=None, current_plant_id=None, plant_id=None):
        """Create a new component."""
        if component_type not in MACHINE_TYPES:
            return None, "Invalid component type."

        safe_name = "".join(ch for ch in name.lower() if ch.isalnum())
        if not safe_name:
            safe_name = "component"
        key = f"{safe_name}-{int(time.time())}"

        if current_role == ROLE_SUPERADMIN:
            if not plant_id:
                return None, "plant_id is required for superadmin component creation."
            target_plant_id = plant_id
        else:
            target_plant_id = current_plant_id

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        COMPONENT_INSERT,
                        (key, name, component_type, target_plant_id, enabled),
                    )
                    row = cur.fetchone()
                    component = Component.from_row(row)
                    conn.commit()
                    return component, None
                except errors.UniqueViolation:
                    conn.rollback()
                    return None, "Component key already exists."

    @staticmethod
    def update_component(component_id, updates, current_role=None, current_plant_id=None):
        """Update component information."""
        fields = []
        values = []

        if "name" in updates:
            name = (updates.get("name") or "").strip()
            if not name:
                return None, "name cannot be empty."
            fields.append("name = %s")
            values.append(name)
        if "type" in updates:
            component_type = (updates.get("type") or "").strip().lower()
            if component_type not in MACHINE_TYPES:
                return None, "Invalid component type."
            fields.append("type = %s")
            values.append(component_type)
        if "enabled" in updates:
            fields.append("enabled = %s")
            values.append(bool(updates.get("enabled")))
        if "plant_id" in updates:
            if current_role != "superadmin":
                return None, "Only superadmin can change component plant."
            fields.append("plant_id = %s")
            values.append(updates.get("plant_id"))

        if not fields:
            return None, "No valid fields to update."

        fields.append("updated_at = NOW()")
        values.append(component_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    if current_role != ROLE_SUPERADMIN:
                        cur.execute(COMPONENT_SELECT_FOR_PLANT_CHECK, (component_id, current_plant_id))
                        if not cur.fetchone():
                            return None, "Component not found."
                    cur.execute(
                        COMPONENT_UPDATE_RETURNING.format(fields=", ".join(fields)),
                        tuple(values),
                    )
                    row = cur.fetchone()
                    component = Component.from_row(row)
                    conn.commit()
                    return component, None
                except errors.UniqueViolation:
                    conn.rollback()
                    return None, "Component key already exists."

    @staticmethod
    def delete_component(component_id, current_role=None, current_plant_id=None):
        """Delete a component."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if current_role == ROLE_SUPERADMIN:
                    cur.execute(COMPONENT_DELETE_SUPERADMIN, (component_id,))
                else:
                    cur.execute(COMPONENT_DELETE_BY_PLANT, (component_id, current_plant_id))
                deleted = cur.rowcount
                conn.commit()
                return deleted > 0
