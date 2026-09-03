-- =============================================================
-- Migration 0003 — Ensure plant_id and assigned_by columns
-- on alerts table (handles existing databases upgraded from
-- the old ad-hoc schema creation in alert_service.py).
-- Safe to run on a fresh database created by migration 0001.
-- =============================================================

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS plant_id   INT NULL;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS assigned_by INT NULL;

-- Back-fill plant_id for any alerts that were created before this
-- column existed (sets them to the first plant as a safe default).
UPDATE alerts
SET plant_id = (SELECT id FROM plants ORDER BY id ASC LIMIT 1)
WHERE plant_id IS NULL;
