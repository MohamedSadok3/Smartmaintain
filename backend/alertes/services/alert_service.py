from datetime import datetime, timedelta, timezone

import redis
from psycopg2 import sql

from shared.config import get_env
from shared.constants import (
    ASSIGNMENT_ALLOWED_ROLES,
    MACHINE_TYPES,
    REDIS_DEFAULT_URL,
    ROLE_SUPERADMIN,
    ROLE_TECHNICIEN,
    SEVERITY_CRITIQUE,
    SEVERITY_MAJEURE,
    SEVERITY_MINEURE,
    SEVERITY_THRESHOLD_CRITIQUE,
    SEVERITY_THRESHOLD_MAJEURE,
    SEVERITY_THRESHOLD_MINEURE,
)
from shared.database import get_db_connection
from models import Alert, Technician
from queries import (
    ALERTS_CREATE_TABLE,
    ALERTS_ADD_COLUMN_PLANT_ID,
    ALERTS_ADD_COLUMN_ASSIGNED_BY,
    INTERVENTIONS_CREATE_TABLE,
    ALERTS_BACKFILL_PLANT_ID,
    ALERT_SELECT_DEFAULT_PLANT,
    ALERT_INSERT,
    ALERT_SELECT_BY_ID,
    ALERT_SELECT_WITH_USERS,
    TECHNICIAN_SELECT_BY_ID,
    ALERT_UPDATE,
    INTERVENTION_SELECT_LATEST_FOR_ALERT,
    INTERVENTION_UPDATE,
    INTERVENTION_INSERT,
    DASHBOARD_COUNT_OPEN_ALERTS,
    DASHBOARD_COUNT_PENDING_INTERVENTIONS,
    DASHBOARD_SELECT_RECENT_ALERTS,
    DASHBOARD_SELECT_PENDING_LIST,
)
from services.exceptions import (
    AlertNotFoundException,
    InvalidStatusTransitionException,
    TechnicianNotEligibleException,
    UnauthorizedActionException,
)


class AlertService:
    def __init__(self):
        self.redis_client = redis.from_url(get_env("REDIS_URL", REDIS_DEFAULT_URL), decode_responses=True)

    def init_db(self):
        """Initialise les tables alertes et interventions."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERTS_CREATE_TABLE)
                cur.execute(ALERTS_ADD_COLUMN_PLANT_ID)
                cur.execute(ALERTS_ADD_COLUMN_ASSIGNED_BY)
                cur.execute(INTERVENTIONS_CREATE_TABLE)
                cur.execute(ALERTS_BACKFILL_PLANT_ID)
                conn.commit()

    def get_default_plant_id(self):
        """Retourne l'identifiant d'usine par défaut."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_DEFAULT_PLANT)
                row = cur.fetchone()
                if not row:
                    return None
                if isinstance(row, dict):
                    return row.get('id')
                return row[0]

    def severity_from_score(self, score):
        """Détermine la sévérité à partir du score d'anomalie."""
        if score >= SEVERITY_THRESHOLD_CRITIQUE:
            return SEVERITY_CRITIQUE
        if score >= SEVERITY_THRESHOLD_MAJEURE:
            return SEVERITY_MAJEURE
        if score >= SEVERITY_THRESHOLD_MINEURE:
            return SEVERITY_MINEURE
        return None

    def insert_alert(self, plant_id, machine, defect, defect_score, confidence, severity):
        """Insère une nouvelle alerte et retourne son enregistrement."""
        created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    ALERT_INSERT,
                    (plant_id, machine, defect, defect_score, confidence, severity, created_at),
                )
                row = cur.fetchone()
                conn.commit()
                return Alert.from_row(row)

    def get_alert_by_id(self, alert_id):
        """Récupère une alerte par identifiant."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_BY_ID, (alert_id,))
                row = cur.fetchone()
                return Alert.from_row(row)

    def get_alert_with_users(self, alert_id):
        """Récupère une alerte enrichie avec les noms des utilisateurs assignés."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_WITH_USERS, (alert_id,))
                row = cur.fetchone()
                return Alert.from_row(row)

    def get_technician(self, user_id):
        """Récupère les informations d'un technicien."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(TECHNICIAN_SELECT_BY_ID, (user_id,))
                row = cur.fetchone()
                return Technician.from_row(row)

    def list_alerts(self, current_user, filters=None):
        """Liste les alertes avec filtrage selon le rôle."""
        filters = filters or {}
        machine = filters.get("machine")
        severity = filters.get("severity")
        status = filters.get("status")
        acknowledged = filters.get("acknowledged")
        page = max(1, int(filters.get("page", 1)))
        limit = max(1, int(filters.get("limit", 20)))
        offset = (page - 1) * limit

        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")

        where_parts = []
        values = []

        if current_role != ROLE_SUPERADMIN:
            where_parts.append(sql.SQL("a.plant_id = %s"))
            values.append(current_plant_id)
        if machine:
            where_parts.append(sql.SQL("a.machine = %s"))
            values.append(machine)
        if severity:
            where_parts.append(sql.SQL("a.severity = %s"))
            values.append(severity)
        if status:
            where_parts.append(sql.SQL("a.status = %s"))
            values.append(status)
        if acknowledged is not None:
            acknowledged_value = acknowledged.lower()
            if acknowledged_value not in {"true", "false"}:
                raise ValueError("Le paramètre acknowledged doit être true ou false.")
            where_parts.append(sql.SQL("a.acknowledged = %s"))
            values.append(acknowledged_value == "true")
        if current_role == ROLE_TECHNICIEN:
            where_parts.append(sql.SQL("a.assigned_to = %s"))
            values.append(int(current_user.get("sub")))

        where_clause = (
            sql.SQL(" WHERE {}").format(sql.SQL(" AND ").join(where_parts))
            if where_parts
            else sql.SQL("")
        )
        query = sql.SQL("""
            SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
                   a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged,
                   a.created_at, a.resolved_at,
                   assigned_user.name  AS assigned_to_name,
                   assigner_user.name  AS assigned_by_name
            FROM alerts a
            LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
            LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
            {where}
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """).format(where=where_clause)
        values.extend([limit, offset])

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, tuple(values))
                rows = cur.fetchall()

        return Alert.from_rows(rows), page, limit

    def _get_alert_for_update(self, alert_id, current_user):
        """Charge une alerte et vérifie l'accès à l'usine."""
        current_alert = self.get_alert_by_id(alert_id)
        if not current_alert:
            raise AlertNotFoundException("Alerte introuvable.")
        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")
        if current_role != ROLE_SUPERADMIN and current_alert.plant_id != current_plant_id:
            raise UnauthorizedActionException("Accès refusé.")
        return current_alert

    def _validate_technician_for_alert(self, technician_id, current_alert, current_user):
        """Vérifie que le technicien est éligible pour la machine de l'alerte."""
        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")

        technician = self.get_technician(technician_id)
        if not technician or technician.role != ROLE_TECHNICIEN:
            raise TechnicianNotEligibleException("L'utilisateur assigné doit être un technicien.")
        if current_role != ROLE_SUPERADMIN and technician.plant_id != current_plant_id:
            raise TechnicianNotEligibleException("Ce technicien n'appartient pas à votre usine.")
        technician_machines = technician.machines or []
        if current_alert.machine not in technician_machines:
            raise TechnicianNotEligibleException("Ce technicien n'est pas assigné à ce type de machine.")

    def _apply_alert_update(self, cur, alert_id, fields, values):
        """Exécute la mise à jour SQL de l'alerte."""
        values.append(alert_id)
        cur.execute(
            ALERT_UPDATE.format(fields=", ".join(fields)),
            tuple(values),
        )
        row = cur.fetchone()
        if not row:
            raise AlertNotFoundException("Alerte introuvable.")
        # Read through the same transaction. A second pooled connection cannot
        # see this uncommitted update and previously returned stale state.
        cur.execute(ALERT_SELECT_WITH_USERS, (alert_id,))
        return Alert.from_row(cur.fetchone())

    def _upsert_intervention(self, cur, alert_id, alert_row):
        """Crée ou met à jour l'intervention liée à l'alerte assignée."""
        cur.execute(INTERVENTION_SELECT_LATEST_FOR_ALERT, (alert_id,))
        intervention_row = cur.fetchone()
        if alert_row.assigned_to is None:
            return

        deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
        intervention_id = None
        if intervention_row:
            intervention_id = (
                intervention_row["id"]
                if hasattr(intervention_row, "keys")
                else intervention_row[0]
            )
        if intervention_id:
            cur.execute(
                INTERVENTION_UPDATE,
                (alert_row.assigned_to, deadline, intervention_id),
            )
        else:
            cur.execute(
                INTERVENTION_INSERT,
                (
                    alert_id,
                    alert_row.machine,
                    alert_row.assigned_to,
                    deadline,
                    datetime.now(timezone.utc).replace(tzinfo=None),
                ),
            )

    def assign_alert(self, alert_id, data, current_user):
        """Assigne une alerte ouverte à un technicien et crée l'intervention."""
        current_role = current_user.get("role")
        current_user_id = int(current_user.get("sub"))

        if current_role not in ASSIGNMENT_ALLOWED_ROLES:
            raise UnauthorizedActionException("Seul un superviseur ou administrateur peut assigner des tâches.")

        if "assigned_to" not in data:
            raise InvalidStatusTransitionException("Le champ assigned_to est requis pour l'assignation.")

        current_alert = self._get_alert_for_update(alert_id, current_user)
        assigned_to = data["assigned_to"]

        fields = ["assigned_to = %s"]
        values = [assigned_to]

        if assigned_to is not None:
            self._validate_technician_for_alert(assigned_to, current_alert, current_user)
            fields.extend(
                [
                    "assigned_by = %s",
                    "status = %s",
                    "acknowledged = %s",
                ]
            )
            values.extend([current_user_id, "assigned", False])
        else:
            fields.append("assigned_by = %s")
            values.append(None)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                alert_row = self._apply_alert_update(cur, alert_id, fields, values)
                if assigned_to is not None:
                    self._upsert_intervention(cur, alert_id, alert_row)
                conn.commit()

        return alert_row

    def acknowledge_alert(self, alert_id, data, current_user):
        """Acquitte une alerte assignée par le technicien concerné."""
        current_role = current_user.get("role")
        current_user_id = int(current_user.get("sub"))

        if current_role != ROLE_TECHNICIEN:
            raise UnauthorizedActionException("Seul le technicien assigné peut acquitter une tâche.")

        current_alert = self._get_alert_for_update(alert_id, current_user)

        if current_alert.assigned_to != current_user_id:
            raise UnauthorizedActionException("Vous n'êtes pas assigné à cette tâche.")

        acknowledged = data.get("acknowledged", True)
        if bool(acknowledged) is not True:
            raise InvalidStatusTransitionException("Seul acknowledged=true est supporté.")

        fields = ["acknowledged = %s", "status = %s"]
        values = [True, "acknowledged"]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                alert_row = self._apply_alert_update(cur, alert_id, fields, values)
                conn.commit()

        return alert_row

    def resolve_alert(self, alert_id, data, current_user):
        """Valide la résolution d'une alerte acquittée."""
        current_role = current_user.get("role")

        if current_role not in ASSIGNMENT_ALLOWED_ROLES:
            raise UnauthorizedActionException("Seul un superviseur ou administrateur peut valider une tâche.")

        current_alert = self._get_alert_for_update(alert_id, current_user)

        if not current_alert.acknowledged or current_alert.status != "acknowledged":
            raise InvalidStatusTransitionException(
                "La tâche doit être acquittée par le technicien assigné avant validation."
            )

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        fields = ["status = %s", "acknowledged = %s", "resolved_at = %s"]
        values = ["resolved", True, now]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                alert_row = self._apply_alert_update(cur, alert_id, fields, values)
                conn.commit()

        return alert_row

    def reopen_alert(self, alert_id, data, current_user):
        """Réouvre une alerte précédemment validée."""
        current_role = current_user.get("role")

        if current_role not in ASSIGNMENT_ALLOWED_ROLES:
            raise UnauthorizedActionException("Seul un superviseur ou administrateur peut valider une tâche.")

        current_alert = self._get_alert_for_update(alert_id, current_user)

        if current_alert.status != "resolved":
            raise InvalidStatusTransitionException("Seules les tâches validées peuvent être réouvertes.")

        reopened_status = "assigned" if current_alert.assigned_to is not None else "open"
        fields = ["status = %s", "acknowledged = %s", "resolved_at = %s"]
        values = [reopened_status, False, None]

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                alert_row = self._apply_alert_update(cur, alert_id, fields, values)
                conn.commit()

        return alert_row

    def get_dashboard_summary(self, current_user):
        """Retourne les indicateurs du tableau de bord."""
        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")

        filters = []
        values = []
        if current_role != ROLE_SUPERADMIN:
            filters.append("a.plant_id = %s")
            values.append(current_plant_id)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        and_or_where = "AND" if where_clause else "WHERE"

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    DASHBOARD_COUNT_OPEN_ALERTS.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                row = cur.fetchone()
                open_alerts = row["count"] if isinstance(row, dict) else row[0]

                cur.execute(
                    DASHBOARD_COUNT_PENDING_INTERVENTIONS.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                row = cur.fetchone()
                pending_interventions = row["count"] if isinstance(row, dict) else row[0]

                cur.execute(
                    DASHBOARD_SELECT_RECENT_ALERTS.format(where_clause=where_clause),
                    tuple(values),
                )
                recent_alerts = Alert.from_rows(cur.fetchall())

                cur.execute(
                    DASHBOARD_SELECT_PENDING_LIST.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                pending_list = Alert.from_rows(cur.fetchall())

        return {
            "active_machines": len(MACHINE_TYPES),
            "open_alerts": open_alerts,
            "pending_interventions": pending_interventions,
            "recent_alerts": recent_alerts,
            "pending_list": pending_list,
        }
