-- =============================================================
-- Migration 0006 — Seed 4 dedicated demo technicians
-- One technician per machine type (moteur, pompe, compresseur,
-- echangeur), all attached to plant_id = 1 (Usine Demo).
-- Idempotent: uses ON CONFLICT DO NOTHING.
-- Passwords (change after demo):
--   tech.moteur@usine-demo.com      → TechMoteur2024!
--   tech.pompe@usine-demo.com       → TechPompe2024!
--   tech.compresseur@usine-demo.com → TechComp2024!
--   tech.echangeur@usine-demo.com   → TechEch2024!
-- =============================================================

INSERT INTO users (name, email, password_hash, role, plant_id, machines)
VALUES
    (
        'Technicien Moteur',
        'tech.moteur@usine-demo.com',
        '$2b$12$GBJqRjLZvGc/VUCsWd/1SOUjPLGJik5sEKFD9S.72agMiIp1oZ6ky',
        'technicien',
        1,
        '{moteur}'
    ),
    (
        'Technicien Pompe',
        'tech.pompe@usine-demo.com',
        '$2b$12$34K1FgHLxfaoy4X7ModL4eSG61jzJ7WzLuCUvj1ewpL22OPu9lzsm',
        'technicien',
        1,
        '{pompe}'
    ),
    (
        'Technicien Compresseur',
        'tech.compresseur@usine-demo.com',
        '$2b$12$xz8hu.YZXGvnQsGBA7EIceZouhyHVHwFQn4hOzp7YBqJDafNlfWn.',
        'technicien',
        1,
        '{compresseur}'
    ),
    (
        'Technicien Echangeur',
        'tech.echangeur@usine-demo.com',
        '$2b$12$b77g0IM4bIA7Q14vymjGJ.mqY/ejgu5HYTornx39FwbdVwgU22juq',
        'technicien',
        1,
        '{echangeur}'
    )
ON CONFLICT (email) DO NOTHING;
