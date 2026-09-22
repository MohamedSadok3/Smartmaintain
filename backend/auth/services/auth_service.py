import bcrypt
from psycopg2 import errors

from shared.database import get_db_connection
from shared.auth import create_token
from models import User
from queries import (
    AUTH_SELECT_USER_BY_EMAIL,
    AUTH_UPDATE_LAST_LOGIN,
    AUTH_SELECT_USER_BY_ID,
    AUTH_SELECT_USER_WITH_PASSWORD_BY_ID,
    AUTH_UPDATE_PROFILE_RETURNING,
)


class AuthService:
    @staticmethod
    def authenticate_user(email, password):
        """Authenticate user and return user data if valid."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(AUTH_SELECT_USER_BY_EMAIL, (email,))
                row = cur.fetchone()

                if not row or not bcrypt.checkpw(
                    password.encode("utf-8"), row["password_hash"].encode("utf-8")
                ):
                    return None

                user = User.from_row(row)
                cur.execute(AUTH_UPDATE_LAST_LOGIN, (user.id,))
                conn.commit()

        return user

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(AUTH_SELECT_USER_BY_ID, (user_id,))
                row = cur.fetchone()
                return User.from_row(row)

    @staticmethod
    def create_user_token(user):
        """Create JWT token for user."""
        return create_token(user)

    @staticmethod
    def update_profile(user_id, updates):
        """Update the authenticated user's profile."""
        current_password = updates.get("current_password")
        new_password = updates.get("new_password")
        fields = []
        values = []

        if "name" in updates and updates["name"]:
            fields.append("name = %s")
            values.append(updates["name"].strip())

        if "email" in updates and updates["email"]:
            fields.append("email = %s")
            values.append(updates["email"].strip().lower())

        if new_password:
            if not current_password:
                return None, "Le mot de passe actuel est requis."
            if len(new_password) < 6:
                return None, "Le nouveau mot de passe doit contenir au moins 6 caractères."

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(AUTH_SELECT_USER_WITH_PASSWORD_BY_ID, (user_id,))
                    row = cur.fetchone()
                    if not row:
                        return None, "Utilisateur introuvable."
                    if not bcrypt.checkpw(
                        current_password.encode("utf-8"),
                        row["password_hash"].encode("utf-8"),
                    ):
                        return None, "Mot de passe actuel incorrect."

            hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            fields.append("password_hash = %s")
            values.append(hashed)

        if not fields:
            return None, "Aucun champ valide à mettre à jour."

        values.append(user_id)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        AUTH_UPDATE_PROFILE_RETURNING.format(fields=", ".join(fields)),
                        tuple(values),
                    )
                    row = cur.fetchone()
                    user = User.from_row(row)
                    conn.commit()
                    return user, None
                except errors.UniqueViolation:
                    conn.rollback()
                    return None, "Cet email est déjà utilisé."
