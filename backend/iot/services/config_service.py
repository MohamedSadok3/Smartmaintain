import socket

from shared.constants import MACHINE_TYPES
from shared.database import get_db_connection
from models.models import IoTMqttConfig, IoTSensorConfig
from queries import (
    IOT_MQTT_SELECT_BY_PLANT,
    IOT_MQTT_UPSERT,
    IOT_SENSOR_SELECT_BY_PLANT,
    IOT_SENSOR_UPSERT,
)

DEFAULT_SENSOR_DEFINITIONS = {
    "moteur": [
        ("vibration", "mm/s", 0.0, 5.0),
        ("current", "A", 0.0, 25.0),
        ("temperature", "°C", 20.0, 90.0),
    ],
    "pompe": [
        ("pressure_in", "bar", 0.0, 10.0),
        ("pressure_out", "bar", 0.0, 15.0),
        ("flow_rate", "m³/h", 0.0, 200.0),
        ("vibration", "mm/s", 0.0, 5.0),
    ],
    "compresseur": [
        ("pressure", "bar", 0.0, 12.0),
        ("temperature_oil", "°C", 20.0, 110.0),
        ("temperature_air", "°C", 10.0, 60.0),
        ("current", "A", 0.0, 30.0),
    ],
    "echangeur": [
        ("temp_in_hot", "°C", 40.0, 120.0),
        ("temp_out_hot", "°C", 30.0, 100.0),
        ("temp_in_cold", "°C", 5.0, 40.0),
        ("temp_out_cold", "°C", 10.0, 50.0),
        ("flow_rate", "m³/h", 0.0, 150.0),
    ],
}


class ConfigService:
    def get_config(self, plant_id):
        mqtt = self._get_mqtt_config(plant_id)
        sensors = self._get_sensor_configs(plant_id)
        if not sensors:
            sensors = self._seed_default_sensors(plant_id)
        return mqtt, sensors

    def save_config(self, plant_id, mqtt_payload=None, sensors_payload=None):
        mqtt = None
        sensors = []

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if mqtt_payload:
                    cur.execute(
                        IOT_MQTT_UPSERT,
                        (
                            plant_id,
                            mqtt_payload.get("host", "localhost"),
                            int(mqtt_payload.get("port", 1883)),
                            mqtt_payload.get("username") or None,
                            mqtt_payload.get("password") or None,
                        ),
                    )
                    mqtt = IoTMqttConfig.from_row(cur.fetchone())

                if sensors_payload:
                    for item in sensors_payload:
                        machine = item.get("machine")
                        sensor_name = item.get("sensor_name")
                        if machine not in MACHINE_TYPES or not sensor_name:
                            continue
                        cur.execute(
                            IOT_SENSOR_UPSERT,
                            (
                                plant_id,
                                machine,
                                sensor_name,
                                item.get("unit", ""),
                                float(item.get("min_value", 0)),
                                float(item.get("max_value", 100)),
                                bool(item.get("enabled", True)),
                            ),
                        )
                        row = cur.fetchone()
                        if row:
                            sensors.append(IoTSensorConfig.from_row(row))

                conn.commit()

        if mqtt is None:
            mqtt = self._get_mqtt_config(plant_id)
        if not sensors:
            sensors = self._get_sensor_configs(plant_id)

        return mqtt, sensors

    def test_mqtt_connection(self, host, port, username=None, password=None):
        host = (host or "").strip()
        if not host:
            return False, "Adresse IP ou hôte MQTT requis."

        try:
            port = int(port)
        except (TypeError, ValueError):
            return False, "Port MQTT invalide."

        try:
            with socket.create_connection((host, port), timeout=5):
                pass
        except OSError as exc:
            return False, f"Connexion MQTT impossible : {exc}"

        return True, "Connexion MQTT établie avec succès."

    def _get_mqtt_config(self, plant_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(IOT_MQTT_SELECT_BY_PLANT, (plant_id,))
                row = cur.fetchone()
                if row:
                    return IoTMqttConfig.from_row(row)
        return IoTMqttConfig(
            id=None,
            plant_id=plant_id,
            host="localhost",
            port=1883,
            username="",
            password="",
        )

    def _get_sensor_configs(self, plant_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(IOT_SENSOR_SELECT_BY_PLANT, (plant_id,))
                rows = cur.fetchall()
                return IoTSensorConfig.from_rows(rows)

    def _seed_default_sensors(self, plant_id):
        sensors = []
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for machine, definitions in DEFAULT_SENSOR_DEFINITIONS.items():
                    for sensor_name, unit, min_value, max_value in definitions:
                        cur.execute(
                            IOT_SENSOR_UPSERT,
                            (plant_id, machine, sensor_name, unit, min_value, max_value, True),
                        )
                        row = cur.fetchone()
                        if row:
                            sensors.append(IoTSensorConfig.from_row(row))
                conn.commit()
        return sensors
