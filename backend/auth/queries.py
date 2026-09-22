# ---------------------------------------------------------------------------
# Auth service — all SQL queries in one place.
# Dynamic parts (WHERE clauses, SET lists) are kept as format-string templates;
# the service layer calls .format(fields=..., where_clause=...) before executing.
# All %s placeholders are passed as psycopg2 parameters — never interpolated.
# ---------------------------------------------------------------------------

# ── Authentication ──────────────────────────────────────────────────────────

AUTH_SELECT_USER_BY_EMAIL = """
    SELECT id, name, email, password_hash, role, plant_id, machines, last_login, created_at
    FROM users
    WHERE email = %s;
"""

AUTH_UPDATE_LAST_LOGIN = """
    UPDATE users SET last_login = NOW() WHERE id = %s;
"""

AUTH_SELECT_USER_BY_ID = """
    SELECT id, name, email, role, plant_id, machines, last_login, created_at
    FROM users
    WHERE id = %s;
"""

AUTH_SELECT_USER_WITH_PASSWORD_BY_ID = """
    SELECT id, name, email, password_hash, role, plant_id, machines, last_login, created_at
    FROM users
    WHERE id = %s;
"""

AUTH_UPDATE_PROFILE_RETURNING = """
    UPDATE users
    SET {fields}
    WHERE id = %s
    RETURNING id, name, email, role, plant_id, machines, last_login, created_at;
"""

AUTH_SELECT_SUPERADMINS = """
    SELECT id, name, email
    FROM users
    WHERE role = 'superadmin'
    ORDER BY id ASC;
"""

# ── Users ───────────────────────────────────────────────────────────────────

# {where_clause} is built dynamically in user_service; always parameterised.
USER_SELECT_LIST = """
    SELECT id, name, email, role, plant_id, machines, last_login, created_at
    FROM users
    {where_clause}
    ORDER BY id ASC;
"""

USER_INSERT = """
    INSERT INTO users (name, email, password_hash, role, plant_id, machines)
    VALUES (%s, %s, %s, %s, %s, %s)
    RETURNING id, name, email, role, plant_id, machines, last_login, created_at;
"""

USER_SELECT_FOR_PLANT_CHECK = """
    SELECT id FROM users WHERE id = %s AND plant_id = %s;
"""

# {fields} is a comma-separated list of "col = %s" built in user_service.
USER_UPDATE_RETURNING = """
    UPDATE users
    SET {fields}
    WHERE id = %s
    RETURNING id, name, email, role, plant_id, machines, last_login, created_at;
"""

USER_DELETE_SUPERADMIN = """
    DELETE FROM users WHERE id = %s;
"""

USER_DELETE_BY_PLANT = """
    DELETE FROM users WHERE id = %s AND plant_id = %s;
"""

# ── Plants ──────────────────────────────────────────────────────────────────

# {where_clause} is built dynamically in plant_service.
PLANT_SELECT_LIST = """
    SELECT id, name, code, status, contact_name, contact_email, contact_phone,
           location, industry, description, approved_by, approved_at, created_at
    FROM plants
    {where_clause}
    ORDER BY created_at DESC;
"""

PLANT_SELECT_BY_ID = """
    SELECT id, name, code, status, contact_name, contact_email, contact_phone,
           location, industry, description, approved_by, approved_at, created_at
    FROM plants
    WHERE id = %s;
"""

# {fields} is a comma-separated list of "col = %s" built in plant_service.
PLANT_UPDATE_RETURNING = """
    UPDATE plants
    SET {fields}
    WHERE id = %s
    RETURNING id, name, code, status, contact_name, contact_email, contact_phone,
              location, industry, description, approved_by, approved_at, created_at;
"""

PLANT_SELECT_USERS_FOR_OVERVIEW = """
    SELECT id, name, email, role, plant_id, machines, last_login, created_at
    FROM users
    WHERE plant_id = %s
    ORDER BY role ASC, id ASC;
"""

PLANT_COUNT_USERS = """
    SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s;
"""

PLANT_COUNT_ADMINS = """
    SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'admin';
"""

PLANT_COUNT_SUPERVISORS = """
    SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'superviseur';
"""

PLANT_COUNT_TECHNICIANS = """
    SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'technicien';
"""

PLANT_COUNT_COMPONENTS = """
    SELECT COUNT(*)::INT AS count FROM components WHERE plant_id = %s;
"""

PLANT_COUNT_TOTAL_ALERTS = """
    SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s;
"""

PLANT_COUNT_OPEN_ALERTS = """
    SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s AND status != 'resolved';
"""

PLANT_COUNT_RESOLVED_ALERTS = """
    SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s AND status = 'resolved';
"""

PLANT_DELETE_INTERVENTIONS = """
    DELETE FROM interventions
    WHERE alert_id IN (SELECT id FROM alerts WHERE plant_id = %s);
"""

PLANT_DELETE_ALERTS = """
    DELETE FROM alerts WHERE plant_id = %s;
"""

PLANT_DELETE_COMPONENTS = """
    DELETE FROM components WHERE plant_id = %s;
"""

PLANT_DELETE_USERS = """
    DELETE FROM users WHERE plant_id = %s;
"""

PLANT_DELETE = """
    DELETE FROM plants WHERE id = %s;
"""

# Used when approving a registration — inserts a new active plant.
PLANT_INSERT_ON_APPROVE = """
    INSERT INTO plants (name, code, status, contact_name, contact_email, approved_by, approved_at)
    VALUES (%s, %s, 'active', %s, %s, %s, NOW())
    RETURNING id, name, code, status, contact_name, contact_email,
              location, industry, description, approved_by, approved_at, created_at;
"""

# ── Components ──────────────────────────────────────────────────────────────

# {where_clause} is built dynamically in component_service.
COMPONENT_SELECT_LIST = """
    SELECT id, key, name, type, plant_id, enabled, created_at, updated_at
    FROM components
    {where_clause}
    ORDER BY id ASC;
"""

COMPONENT_INSERT = """
    INSERT INTO components (key, name, type, plant_id, enabled)
    VALUES (%s, %s, %s, %s, %s)
    RETURNING id, key, name, type, plant_id, enabled, created_at, updated_at;
"""

COMPONENT_SELECT_FOR_PLANT_CHECK = """
    SELECT id FROM components WHERE id = %s AND plant_id = %s;
"""

# {fields} is a comma-separated list of "col = %s" built in component_service.
COMPONENT_UPDATE_RETURNING = """
    UPDATE components
    SET {fields}
    WHERE id = %s
    RETURNING id, key, name, type, plant_id, enabled, created_at, updated_at;
"""

COMPONENT_DELETE_SUPERADMIN = """
    DELETE FROM components WHERE id = %s;
"""

COMPONENT_DELETE_BY_PLANT = """
    DELETE FROM components WHERE id = %s AND plant_id = %s;
"""

# ── Plant registrations ─────────────────────────────────────────────────────

REGISTRATION_CHECK_PLANT_EXISTS = """
    SELECT id FROM plants WHERE code = %s OR LOWER(name) = LOWER(%s);
"""

REGISTRATION_CHECK_PENDING_EXISTS = """
    SELECT id FROM plant_registrations
    WHERE status = 'pending' AND (plant_code = %s OR LOWER(plant_name) = LOWER(%s));
"""

REGISTRATION_CHECK_EMAILS_TAKEN = """
    SELECT id FROM users WHERE LOWER(email) = ANY(%s);
"""

REGISTRATION_INSERT = """
    INSERT INTO plant_registrations (plant_name, plant_code, contact_name, contact_email, payload, status)
    VALUES (%s, %s, %s, %s, %s, 'pending')
    RETURNING id, plant_name, plant_code, contact_name, contact_email,
              payload, status, review_note, reviewed_by, reviewed_at, created_at;
"""

REGISTRATION_SELECT_ALL = """
    SELECT id, plant_name, plant_code, contact_name, contact_email,
           payload, status, review_note, reviewed_by, reviewed_at, created_at
    FROM plant_registrations
    ORDER BY created_at DESC;
"""

REGISTRATION_SELECT_BY_STATUS = """
    SELECT id, plant_name, plant_code, contact_name, contact_email,
           payload, status, review_note, reviewed_by, reviewed_at, created_at
    FROM plant_registrations
    WHERE status = %s
    ORDER BY created_at DESC;
"""

REGISTRATION_SELECT_BY_ID = """
    SELECT id, plant_name, plant_code, contact_name, contact_email,
           payload, status, review_note, reviewed_by, reviewed_at, created_at
    FROM plant_registrations
    WHERE id = %s;
"""

REGISTRATION_REJECT = """
    UPDATE plant_registrations
    SET status = 'rejected', review_note = %s, reviewed_by = %s,
        payload = %s, reviewed_at = NOW()
    WHERE id = %s
    RETURNING id, plant_name, plant_code, contact_name, contact_email,
              payload, status, review_note, reviewed_by, reviewed_at, created_at;
"""

REGISTRATION_INSERT_USER = """
    INSERT INTO users (name, email, password_hash, role, plant_id, machines)
    VALUES (%s, %s, %s, %s, %s, %s);
"""

REGISTRATION_APPROVE = """
    UPDATE plant_registrations
    SET status = 'approved', review_note = %s, reviewed_by = %s,
        payload = %s, reviewed_at = NOW()
    WHERE id = %s
    RETURNING id, plant_name, plant_code, contact_name, contact_email,
              payload, status, review_note, reviewed_by, reviewed_at, created_at;
"""
