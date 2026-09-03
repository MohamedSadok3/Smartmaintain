import bcrypt
from psycopg2 import errors

from shared.constants import ROLE_ADMIN, ROLE_SUPERADMIN, ROLE_SUPERVISEUR
from shared.database import get_db_connection
from models import User
from queries import (
    USER_SELECT_LIST,
    USER_INSERT,
    USER_SELECT_FOR_PLANT_CHECK,
    USER_UPDATE_RETURNING,
    USER_DELETE_SUPERADMIN,
    USER_DELETE_BY_PLANT,
)


class UserService:
    @staticmethod
    def list_users(role=None, plant_id=None, current_role=None, current_plant_id=None):
        """List users with optional filtering."""
        filters = []
        values = []

        if role:
            filters.append("role = %s")
            values.append(role)
        if current_role in {ROLE_ADMIN, ROLE_SUPERVISEUR}:
            filters.append("plant_id = %s")
            values.append(current_plant_id)
            filters.append("role != %s")
            values.append(ROLE_SUPERADMIN)
        elif plant_id:
            filters.append("plant_id = %s")
            values.append(int(plant_id))

        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    USER_SELECT_LIST.format(where_clause=where_clause),
                    tuple(values),
                )
                rows = cur.fetchall()
                return User.from_rows(rows)

    @staticmethod
    def create_user(name, email, password, role, plant_id, machines):
        """Create a new user."""
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        USER_INSERT,
                        (name, email, password_hash, role, plant_id, machines),
                    )
                    row = cur.fetchone()
                    user = User.from_row(row)
                    conn.commit()
                    return user, None
                except errors.UniqueViolation:
                    conn.rollback()
                    return None, "Cet email est déjà utilisé."

    @staticmethod
    def update_user(user_id, updates, current_role=None, current_plant_id=None):
        """Update user information."""
        fields = []
        values = []

        if "name" in updates:
            fields.append("name = %s")
            values.append(updates["name"])
        if "email" in updates:
            fields.append("email = %s")
            values.append(updates["email"])
        if "role" in updates:
            fields.append("role = %s")
            values.append(updates["role"])
        if "plant_id" in updates:
            fields.append("plant_id = %s")
            values.append(updates["plant_id"])
        if "machines" in updates:
            fields.append("machines = %s")
            values.append(updates["machines"])
        if "password" in updates:
            hashed = bcrypt.hashpw(updates["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            fields.append("password_hash = %s")
            values.append(hashed)

        if not fields:
            return None, "Aucun champ valide à mettre à jour."

        values.append(user_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if current_role != ROLE_SUPERADMIN:
                    cur.execute(USER_SELECT_FOR_PLANT_CHECK, (user_id, current_plant_id))
                    if not cur.fetchone():
                        return None, "Accès refusé."
                cur.execute(
                    USER_UPDATE_RETURNING.format(fields=", ".join(fields)),
                    tuple(values),
                )
                row = cur.fetchone()
                user = User.from_row(row)
                conn.commit()
                return user, None

    @staticmethod
    def delete_user(user_id, current_role=None, current_plant_id=None):
        """Delete a user."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if current_role == ROLE_SUPERADMIN:
                    cur.execute(USER_DELETE_SUPERADMIN, (user_id,))
                else:
                    cur.execute(USER_DELETE_BY_PLANT, (user_id, current_plant_id))
                deleted = cur.rowcount
                conn.commit()
                return deleted > 0
