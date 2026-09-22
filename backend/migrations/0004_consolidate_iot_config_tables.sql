-- Consolidate legacy singular IoT configuration tables into the canonical
-- plural tables created by 0001. The legacy tables are intentionally retained
-- for one release so an operator can verify the copied data before removal.

DO $$
BEGIN
    IF to_regclass('public.iot_mqtt_config') IS NOT NULL THEN
        INSERT INTO iot_mqtt_configs
            (plant_id, host, port, username, password, updated_at)
        SELECT plant_id, host, port, username, password, updated_at
        FROM iot_mqtt_config
        ON CONFLICT (plant_id) DO UPDATE
        SET host = EXCLUDED.host,
            port = EXCLUDED.port,
            username = EXCLUDED.username,
            password = EXCLUDED.password,
            updated_at = EXCLUDED.updated_at;
    END IF;

    IF to_regclass('public.iot_sensor_config') IS NOT NULL THEN
        INSERT INTO iot_sensor_configs
            (plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at)
        SELECT plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at
        FROM iot_sensor_config
        ON CONFLICT (plant_id, machine, sensor_name) DO UPDATE
        SET unit = EXCLUDED.unit,
            min_value = EXCLUDED.min_value,
            max_value = EXCLUDED.max_value,
            enabled = EXCLUDED.enabled,
            updated_at = EXCLUDED.updated_at;
    END IF;
END $$;
