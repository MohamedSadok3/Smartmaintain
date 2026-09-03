# ---------------------------------------------------------------------------
# IoT service — SQL queries
# ---------------------------------------------------------------------------

IOT_MQTT_SELECT_BY_PLANT = """
    SELECT id, plant_id, host, port, username, password, updated_at
    FROM iot_mqtt_configs
    WHERE plant_id = %s;
"""

IOT_MQTT_UPSERT = """
    INSERT INTO iot_mqtt_configs (plant_id, host, port, username, password, updated_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (plant_id) DO UPDATE
    SET host = EXCLUDED.host,
        port = EXCLUDED.port,
        username = EXCLUDED.username,
        password = COALESCE(EXCLUDED.password, iot_mqtt_configs.password),
        updated_at = NOW()
    RETURNING id, plant_id, host, port, username, password, updated_at;
"""

IOT_SENSOR_SELECT_BY_PLANT = """
    SELECT id, plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at
    FROM iot_sensor_configs
    WHERE plant_id = %s
    ORDER BY machine ASC, sensor_name ASC;
"""

IOT_SENSOR_UPSERT = """
    INSERT INTO iot_sensor_configs
        (plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (plant_id, machine, sensor_name) DO UPDATE
    SET unit = EXCLUDED.unit,
        min_value = EXCLUDED.min_value,
        max_value = EXCLUDED.max_value,
        enabled = EXCLUDED.enabled,
        updated_at = NOW()
    RETURNING id, plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at;
"""
