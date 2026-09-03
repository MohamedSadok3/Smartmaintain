from typing import List, Optional

from shared.entity import isoformat_value, mapping_from_row


class IoTMqttConfig:
    def __init__(self, id, plant_id, host, port, username=None, password=None, updated_at=None):
        self.id = id
        self.plant_id = plant_id
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "host": self.host,
            "port": self.port,
            "username": self.username or "",
            "password": "",
            "password_configured": bool(self.password),
            "updated_at": isoformat_value(self.updated_at),
        }

    @staticmethod
    def from_row(row) -> Optional["IoTMqttConfig"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return IoTMqttConfig(
            id=data.get("id"),
            plant_id=data.get("plant_id"),
            host=data.get("host"),
            port=data.get("port"),
            username=data.get("username"),
            password=data.get("password"),
            updated_at=data.get("updated_at"),
        )


class IoTSensorConfig:
    def __init__(
        self,
        id,
        plant_id,
        machine,
        sensor_name,
        unit,
        min_value,
        max_value,
        enabled=True,
        updated_at=None,
    ):
        self.id = id
        self.plant_id = plant_id
        self.machine = machine
        self.sensor_name = sensor_name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.enabled = enabled
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "machine": self.machine,
            "sensor_name": self.sensor_name,
            "unit": self.unit,
            "min_value": float(self.min_value),
            "max_value": float(self.max_value),
            "enabled": bool(self.enabled),
            "updated_at": isoformat_value(self.updated_at),
        }

    @staticmethod
    def from_row(row) -> Optional["IoTSensorConfig"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return IoTSensorConfig(
            id=data.get("id"),
            plant_id=data.get("plant_id"),
            machine=data.get("machine"),
            sensor_name=data.get("sensor_name"),
            unit=data.get("unit"),
            min_value=data.get("min_value"),
            max_value=data.get("max_value"),
            enabled=data.get("enabled"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["IoTSensorConfig"]:
        return [item for row in rows if (item := cls.from_row(row))]
