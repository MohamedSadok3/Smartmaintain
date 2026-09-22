-- =============================================================
-- Migration 0001 — Initial schema
-- Creates all base tables for SmartMaintain.
-- Idempotent: uses CREATE TABLE IF NOT EXISTS throughout.
-- =============================================================

-- ── Plants ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plants (
    id             SERIAL PRIMARY KEY,
    name           TEXT NOT NULL,
    code           TEXT NOT NULL UNIQUE,
    status         TEXT NOT NULL DEFAULT 'active',
    contact_name   TEXT,
    contact_email  TEXT,
    contact_phone  TEXT,
    location       TEXT,
    industry       TEXT,
    description    TEXT,
    approved_by    INT NULL,
    approved_at    TIMESTAMP NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Users ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id             SERIAL PRIMARY KEY,
    name           TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    password_hash  TEXT NOT NULL,
    role           TEXT NOT NULL,
    plant_id       INT NULL REFERENCES plants(id) ON DELETE SET NULL,
    machines       TEXT[] NOT NULL DEFAULT '{}',
    last_login     TIMESTAMP NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Components ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS components (
    id         SERIAL PRIMARY KEY,
    key        TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    type       TEXT NOT NULL,
    plant_id   INT NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    enabled    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Plant registrations ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS plant_registrations (
    id             SERIAL PRIMARY KEY,
    plant_name     TEXT NOT NULL,
    plant_code     TEXT NOT NULL,
    contact_name   TEXT NOT NULL,
    contact_email  TEXT NOT NULL,
    payload        JSONB NOT NULL DEFAULT '{}',
    status         TEXT NOT NULL DEFAULT 'pending',
    review_note    TEXT NULL,
    reviewed_by    INT NULL REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at    TIMESTAMP NULL,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Alerts ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id             SERIAL PRIMARY KEY,
    plant_id       INT NULL REFERENCES plants(id) ON DELETE SET NULL,
    machine        TEXT NOT NULL,
    defect         TEXT NOT NULL,
    anomaly_score  DOUBLE PRECISION NOT NULL,
    confidence     DOUBLE PRECISION NOT NULL,
    severity       TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'open',
    assigned_to    INT NULL REFERENCES users(id) ON DELETE SET NULL,
    assigned_by    INT NULL REFERENCES users(id) ON DELETE SET NULL,
    acknowledged   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    resolved_at    TIMESTAMP NULL
);

-- ── Interventions ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interventions (
    id          SERIAL PRIMARY KEY,
    alert_id    INT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    machine     TEXT NOT NULL,
    assigned_to INT NULL REFERENCES users(id) ON DELETE SET NULL,
    deadline    TIMESTAMP NULL,
    notes       TEXT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── IoT MQTT config ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS iot_mqtt_configs (
    id        SERIAL PRIMARY KEY,
    plant_id  INT NOT NULL UNIQUE REFERENCES plants(id) ON DELETE CASCADE,
    host      TEXT NOT NULL DEFAULT 'localhost',
    port      INT  NOT NULL DEFAULT 1883,
    username  TEXT NULL,
    password  TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── IoT sensor config ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS iot_sensor_configs (
    id           SERIAL PRIMARY KEY,
    plant_id     INT  NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    machine      TEXT NOT NULL,
    sensor_name  TEXT NOT NULL,
    unit         TEXT NOT NULL DEFAULT '',
    min_value    DOUBLE PRECISION NOT NULL DEFAULT 0,
    max_value    DOUBLE PRECISION NOT NULL DEFAULT 100,
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (plant_id, machine, sensor_name)
);

-- ── Indexes for common query patterns ───────────────────────
CREATE INDEX IF NOT EXISTS idx_users_plant_id     ON users(plant_id);
CREATE INDEX IF NOT EXISTS idx_users_email        ON users(email);
CREATE INDEX IF NOT EXISTS idx_components_plant   ON components(plant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_plant_id    ON alerts(plant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status      ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at  ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interventions_alert ON interventions(alert_id);
