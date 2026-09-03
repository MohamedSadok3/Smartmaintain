from typing import List, Optional

from shared.entity import isoformat_value, mapping_from_row


class Alert:
    """Alerte de maintenance prédictive."""

    def __init__(
        self,
        id,
        machine,
        defect,
        anomaly_score,
        confidence,
        severity,
        status="open",
        plant_id=None,
        assigned_to=None,
        assigned_by=None,
        acknowledged=False,
        created_at=None,
        resolved_at=None,
        assigned_to_name=None,
        assigned_by_name=None,
    ):
        self.id = id
        self.plant_id = plant_id
        self.machine = machine
        self.defect = defect
        self.anomaly_score = anomaly_score
        self.confidence = confidence
        self.severity = severity
        self.status = status
        self.assigned_to = assigned_to
        self.assigned_by = assigned_by
        self.acknowledged = acknowledged
        self.created_at = created_at
        self.resolved_at = resolved_at
        self.assigned_to_name = assigned_to_name
        self.assigned_by_name = assigned_by_name

    def to_dict(self) -> dict:
        """Représentation API JSON de l'alerte."""
        resolved_at = isoformat_value(self.resolved_at)
        score = float(self.anomaly_score) if self.anomaly_score is not None else 0.0
        confidence = float(self.confidence) if self.confidence is not None else 0.0
        return {
            "id": self.id,
            "plant_id": self.plant_id,
            "machine": self.machine,
            "defect": self.defect,
            "defect_score": score,
            "anomaly_score": score,
            "confidence": confidence,
            "severity": self.severity,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assigned_to_name,
            "assigned_by": self.assigned_by,
            "assigned_by_name": self.assigned_by_name,
            "acknowledged": bool(self.acknowledged),
            "created_at": isoformat_value(self.created_at),
            "resolved_at": resolved_at,
            "validation_at": resolved_at,
        }

    @staticmethod
    def from_row(row) -> Optional["Alert"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return Alert(
            id=data.get("id"),
            plant_id=data.get("plant_id"),
            machine=data.get("machine"),
            defect=data.get("defect"),
            anomaly_score=data.get("anomaly_score"),
            confidence=data.get("confidence"),
            severity=data.get("severity"),
            status=data.get("status", "open"),
            assigned_to=data.get("assigned_to"),
            assigned_by=data.get("assigned_by"),
            acknowledged=data.get("acknowledged", False),
            created_at=data.get("created_at"),
            resolved_at=data.get("resolved_at"),
            assigned_to_name=data.get("assigned_to_name"),
            assigned_by_name=data.get("assigned_by_name"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["Alert"]:
        return [alert for row in rows if (alert := cls.from_row(row))]


class Technician:
    """Profil technicien (lecture depuis la table users)."""

    def __init__(self, id, role, machines=None, plant_id=None):
        self.id = id
        self.role = role
        self.machines = machines or []
        self.plant_id = plant_id

    @staticmethod
    def from_row(row) -> Optional["Technician"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return Technician(
            id=data.get("id"),
            role=data.get("role"),
            machines=data.get("machines") or [],
            plant_id=data.get("plant_id"),
        )
