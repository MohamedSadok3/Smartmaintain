-- =============================================================
-- Migration 0005 — Seed default plant
-- Creates a default plant (id=1) so the IoT service (IOT_PLANT_ID=1)
-- can insert alerts without a foreign-key violation on fresh deploys.
-- Idempotent: uses ON CONFLICT DO NOTHING.
-- =============================================================

INSERT INTO plants (id, name, code, status, location, description)
VALUES (
    1,
    'Usine Principale',
    'PLANT-001',
    'active',
    'Tunis, Tunisie',
    'Usine de démonstration SmartMaintain'
)
ON CONFLICT DO NOTHING;

-- Keep the sequence ahead of the seeded id so app-created plants
-- get fresh ids starting from 2.
SELECT setval('plants_id_seq', GREATEST((SELECT MAX(id) FROM plants), 1));
