# ---------------------------------------------------------------------------
# Alertes service — all SQL queries in one place.
# Dynamic parts (WHERE clauses, SET lists) are kept as format-string templates;
# the service layer calls .format(where_clause=..., fields=...) before executing.
# All %s placeholders are passed as psycopg2 parameters — never interpolated.
# ---------------------------------------------------------------------------

# ── Schema initialisation ───────────────────────────────────────────────────

ALERTS_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS alerts (
        id             SERIAL PRIMARY KEY,
        plant_id       INT NULL,
        machine        TEXT NOT NULL,
        defect         TEXT NOT NULL,
        anomaly_score  DOUBLE PRECISION NOT NULL,
        confidence     DOUBLE PRECISION NOT NULL,
        severity       TEXT NOT NULL,
        status         TEXT DEFAULT 'open',
        assigned_to    INT NULL,
        assigned_by    INT NULL,
        acknowledged   BOOL DEFAULT false,
        created_at     TIMESTAMP NOT NULL,
        resolved_at    TIMESTAMP NULL
    );
"""

ALERTS_ADD_COLUMN_PLANT_ID = """
    ALTER TABLE alerts ADD COLUMN IF NOT EXISTS plant_id INT NULL;
"""

ALERTS_ADD_COLUMN_ASSIGNED_BY = """
    ALTER TABLE alerts ADD COLUMN IF NOT EXISTS assigned_by INT NULL;
"""

INTERVENTIONS_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS interventions (
        id          SERIAL PRIMARY KEY,
        alert_id    INT REFERENCES alerts(id) ON DELETE CASCADE,
        machine     TEXT NOT NULL,
        assigned_to INT NULL,
        deadline    TIMESTAMP NULL,
        notes       TEXT NULL,
        created_at  TIMESTAMP NOT NULL
    );
"""

ALERTS_BACKFILL_PLANT_ID = """
    UPDATE alerts
    SET plant_id = (SELECT id FROM plants ORDER BY id ASC LIMIT 1)
    WHERE plant_id IS NULL;
"""

# ── Alerts ──────────────────────────────────────────────────────────────────

ALERT_SELECT_DEFAULT_PLANT = """
    SELECT id FROM plants ORDER BY id ASC LIMIT 1;
"""

ALERT_INSERT = """
    INSERT INTO alerts (plant_id, machine, defect, anomaly_score, confidence, severity, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    RETURNING id, plant_id, machine, defect, anomaly_score, confidence, severity,
              status, assigned_to, assigned_by, acknowledged, created_at, resolved_at;
"""

ALERT_SELECT_BY_ID = """
    SELECT id, plant_id, machine, defect, anomaly_score, confidence, severity,
           status, assigned_to, assigned_by, acknowledged, created_at, resolved_at
    FROM alerts
    WHERE id = %s;
"""

ALERT_SELECT_WITH_USERS = """
    SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
           a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged,
           a.created_at, a.resolved_at,
           assigned_user.name  AS assigned_to_name,
           assigner_user.name  AS assigned_by_name
    FROM alerts a
    LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
    LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
    WHERE a.id = %s;
"""

TECHNICIAN_SELECT_BY_ID = """
    SELECT id, role, machines, plant_id
    FROM users
    WHERE id = %s;
"""

# {where_clause} built dynamically in alert_service; LIMIT and OFFSET appended as %s.
ALERT_SELECT_LIST = """
    SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
           a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged,
           a.created_at, a.resolved_at,
           assigned_user.name  AS assigned_to_name,
           assigner_user.name  AS assigned_by_name
    FROM alerts a
    LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
    LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
    {where_clause}
    ORDER BY a.created_at DESC
    LIMIT %s OFFSET %s;
"""

# {fields} is a comma-separated list of "col = %s" built in alert_service.
ALERT_UPDATE = """
    UPDATE alerts
    SET {fields}
    WHERE id = %s
    RETURNING id;
"""

# ── Interventions ───────────────────────────────────────────────────────────

INTERVENTION_SELECT_LATEST_FOR_ALERT = """
    SELECT id
    FROM interventions
    WHERE alert_id = %s
    ORDER BY id DESC
    LIMIT 1;
"""

INTERVENTION_UPDATE = """
    UPDATE interventions
    SET assigned_to = %s, deadline = %s
    WHERE id = %s;
"""

INTERVENTION_INSERT = """
    INSERT INTO interventions (alert_id, machine, assigned_to, deadline, created_at)
    VALUES (%s, %s, %s, %s, %s);
"""

# ── Dashboard ───────────────────────────────────────────────────────────────
# {where_clause}  — e.g. "WHERE a.plant_id = %s" or ""
# {and_or_where}  — "AND" when where_clause is non-empty, "WHERE" otherwise

DASHBOARD_COUNT_OPEN_ALERTS = """
    SELECT COUNT(*)::INT AS count
    FROM alerts a
    {where_clause} {and_or_where} a.status = 'open';
"""

DASHBOARD_COUNT_PENDING_INTERVENTIONS = """
    SELECT COUNT(*)::INT AS count
    FROM interventions i
    JOIN alerts a ON a.id = i.alert_id
    {where_clause} {and_or_where} a.status != 'resolved';
"""

DASHBOARD_SELECT_RECENT_ALERTS = """
    SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
           a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged,
           a.created_at, a.resolved_at,
           assigned_user.name  AS assigned_to_name,
           assigner_user.name  AS assigned_by_name
    FROM alerts a
    LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
    LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
    {where_clause}
    ORDER BY a.created_at DESC
    LIMIT 5;
"""

DASHBOARD_SELECT_PENDING_LIST = """
    SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
           a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged,
           a.created_at, a.resolved_at,
           assigned_user.name  AS assigned_to_name,
           assigner_user.name  AS assigned_by_name
    FROM alerts a
    LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
    LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
    {where_clause} {and_or_where} a.status = 'open'
    ORDER BY a.severity DESC, a.created_at DESC
    LIMIT 5;
"""
