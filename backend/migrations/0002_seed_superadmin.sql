-- =============================================================
-- Migration 0002 — Seed superadmin user
-- Creates the default superadmin account if it does not exist.
-- Password hash below corresponds to: "superadmin123"
-- IMPORTANT: change the password immediately after first login.
-- =============================================================

INSERT INTO users (name, email, password_hash, role, plant_id, machines)
SELECT
    'Super Admin',
    'superadmin@smartmaintain.local',
    -- bcrypt hash of "superadmin123" (cost=12)
    '$2b$12$ePzYqDHiX9cD6vUCMnkgx.kpxeIZ4V5v6W0QaM3uAIf8HBf3Gn4hm',
    'superadmin',
    NULL,
    '{}'
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE role = 'superadmin'
);
