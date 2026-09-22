"""
Auth Service Models
===================
Data models for authentication, users, plants, and components.

All models follow the DAO (Data Access Object) pattern:
- from_row() / from_rows(): Convert DB rows to objects
- to_dict(): Serialize for API responses
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from shared.entity import isoformat_value, mapping_from_row

# Valid user roles
VALID_ROLES = {"superadmin", "admin", "superviseur", "technicien"}

# Valid plant statuses
VALID_PLANT_STATUSES = {"pending", "active", "suspended"}

# Valid registration statuses
VALID_REGISTRATION_STATUSES = {"pending", "approved", "rejected"}

# Valid machine types
VALID_MACHINE_TYPES = {"moteur", "pompe", "compresseur", "echangeur"}


class User:
    """
    User model - Represents a platform user.
    
    Attributes:
        id (int): User ID
        name (str): Full name
        email (str): Email address (unique)
        role (str): User role (superadmin, admin, operator)
        plant_id (int|None): Associated plant ID
        machines (list): Accessible machine types
        last_login (datetime|None): Last login timestamp
        created_at (datetime|None): Creation timestamp
        password_hash (str|None): Bcrypt password hash (never exposed in API)
    """

    def __init__(
        self,
        id: int,
        name: str,
        email: str,
        role: str,
        plant_id: Optional[int] = None,
        machines: Optional[List[str]] = None,
        last_login: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        password_hash: Optional[str] = None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.plant_id = plant_id
        self.machines = machines or []
        self.last_login = last_login
        self.created_at = created_at
        self.password_hash = password_hash
        
        # Validation
        if role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize user to dictionary (safe for API - no password_hash)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "plant_id": self.plant_id,
            "machines": self.machines or [],
            "last_login": isoformat_value(self.last_login),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["User"]:
        """Create User from database row."""
        data = mapping_from_row(row)
        if not data:
            return None
        try:
            return User(
                id=data.get("id"),
                name=data.get("name"),
                email=data.get("email"),
                role=data.get("role"),
                plant_id=data.get("plant_id"),
                machines=data.get("machines") or [],
                last_login=data.get("last_login"),
                created_at=data.get("created_at"),
                password_hash=data.get("password_hash"),
            )
        except ValueError as e:
            # Log validation error but don't crash
            import logging
            logging.getLogger(__name__).error(f"Invalid user data: {e}")
            return None

    @classmethod
    def from_rows(cls, rows) -> List["User"]:
        return [user for row in rows if (user := cls.from_row(row))]


class Plant:
    """
    Plant model - Represents a manufacturing plant/factory.
    
    Attributes:
        id (int): Plant ID
        name (str): Plant name
        code (str): Unique plant code
        status (str): Plant status (pending, active, suspended)
        contact_name (str): Contact person name
        contact_email (str): Contact person email
        contact_phone (str): Contact phone number
        location (str): Plant location/address
        industry (str): Industry type
        description (str): Plant description
        approved_by (int|None): Superadmin user ID who approved
        approved_at (datetime|None): Approval timestamp
        created_at (datetime|None): Creation timestamp
    """

    def __init__(
        self,
        id: int,
        name: str,
        code: str,
        status: str,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None,
        approved_by: Optional[int] = None,
        approved_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.status = status
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.location = location
        self.industry = industry
        self.description = description
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at
        
        # Validation
        if status not in VALID_PLANT_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_PLANT_STATUSES}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize plant to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "status": self.status,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "location": self.location,
            "industry": self.industry,
            "description": self.description,
            "approved_by": self.approved_by,
            "approved_at": isoformat_value(self.approved_at),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["Plant"]:
        """Create Plant from database row."""
        data = mapping_from_row(row)
        if not data:
            return None
        try:
            return Plant(
                id=data.get("id"),
                name=data.get("name"),
                code=data.get("code"),
                status=data.get("status"),
                contact_name=data.get("contact_name"),
                contact_email=data.get("contact_email"),
                contact_phone=data.get("contact_phone"),
                location=data.get("location"),
                industry=data.get("industry"),
                description=data.get("description"),
                approved_by=data.get("approved_by"),
                approved_at=data.get("approved_at"),
                created_at=data.get("created_at"),
            )
        except ValueError as e:
            import logging
            logging.getLogger(__name__).error(f"Invalid plant data: {e}")
            return None

    @classmethod
    def from_rows(cls, rows) -> List["Plant"]:
        return [plant for row in rows if (plant := cls.from_row(row))]


class Component:
    """
    Component model - Represents a monitored machine/equipment in a plant.
    
    Attributes:
        id (int): Component ID
        key (str): Unique component key (e.g., "moteur-001")
        name (str): Component display name
        type (str): Machine type (moteur, pompe, compresseur, echangeur)
        plant_id (int): Associated plant ID
        enabled (bool): Whether monitoring is enabled
        created_at (datetime|None): Creation timestamp
        updated_at (datetime|None): Last update timestamp
    """

    def __init__(
        self,
        id: int,
        key: str,
        name: str,
        type: str,
        plant_id: int,
        enabled: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.key = key
        self.name = name
        self.type = type
        self.plant_id = plant_id
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at
        
        # Validation
        if type not in VALID_MACHINE_TYPES:
            raise ValueError(f"Invalid machine type '{type}'. Must be one of: {VALID_MACHINE_TYPES}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize component to dictionary."""
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "type": self.type,
            "plant_id": self.plant_id,
            "enabled": bool(self.enabled),
            "created_at": isoformat_value(self.created_at),
            "updated_at": isoformat_value(self.updated_at),
        }

    @staticmethod
    def from_row(row) -> Optional["Component"]:
        """Create Component from database row."""
        data = mapping_from_row(row)
        if not data:
            return None
        try:
            return Component(
                id=data.get("id"),
                key=data.get("key"),
                name=data.get("name"),
                type=data.get("type"),
                plant_id=data.get("plant_id"),
                enabled=data.get("enabled", True),
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at"),
            )
        except ValueError as e:
            import logging
            logging.getLogger(__name__).error(f"Invalid component data: {e}")
            return None

    @classmethod
    def from_rows(cls, rows) -> List["Component"]:
        return [component for row in rows if (component := cls.from_row(row))]


class PlantRegistration:
    """
    Plant Registration model - Represents a plant registration request.
    
    This model handles the workflow of new plant onboarding:
    1. User submits registration (status=pending)
    2. Superadmin reviews and approves/rejects
    3. If approved, plant and users are created automatically
    
    Attributes:
        id (int): Registration ID
        plant_name (str): Proposed plant name
        plant_code (str): Proposed plant code
        contact_name (str): Contact person name
        contact_email (str): Contact person email
        payload (dict|str): JSON payload with users, components, etc.
        status (str): Registration status (pending, approved, rejected)
        review_note (str|None): Admin's review note
        reviewed_by (int|None): Superadmin user ID who reviewed
        reviewed_at (datetime|None): Review timestamp
        created_at (datetime|None): Creation timestamp
    """

    def __init__(
        self,
        id: int,
        plant_name: str,
        plant_code: str,
        contact_name: str,
        contact_email: str,
        payload: Any,  # Can be dict or JSON string
        status: str,
        review_note: Optional[str] = None,
        reviewed_by: Optional[int] = None,
        reviewed_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.plant_name = plant_name
        self.plant_code = plant_code
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.payload = payload
        self.status = status
        self.review_note = review_note
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.created_at = created_at
        
        # Validation
        if status not in VALID_REGISTRATION_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_REGISTRATION_STATUSES}")

    @property
    def payload_data(self) -> Dict[str, Any]:
        """Parse payload to dict (handles both dict and JSON string)."""
        if isinstance(self.payload, dict):
            return self.payload
        if isinstance(self.payload, str):
            return json.loads(self.payload)
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize registration to dictionary.
        
        Security: Passwords and password_hash are stripped from payload
        to prevent accidental exposure via API.
        """
        payload_data = self.payload_data
        # Deep copy to avoid modifying original
        safe_payload = json.loads(json.dumps(payload_data))
        
        # Strip sensitive data from users
        for user in (safe_payload.get("users") or {}).values():
            if isinstance(user, dict):
                user.pop("password", None)
                user.pop("password_hash", None)
        
        return {
            "id": self.id,
            "plant_name": self.plant_name,
            "plant_code": self.plant_code,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "payload": json.dumps(safe_payload),
            "payload_data": safe_payload,
            "documents": safe_payload.get("documents") or {},
            "status": self.status,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": isoformat_value(self.reviewed_at),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["PlantRegistration"]:
        """Create PlantRegistration from database row."""
        data = mapping_from_row(row)
        if not data:
            return None
        try:
            return PlantRegistration(
                id=data.get("id"),
                plant_name=data.get("plant_name"),
                plant_code=data.get("plant_code"),
                contact_name=data.get("contact_name"),
                contact_email=data.get("contact_email"),
                payload=data.get("payload"),
                status=data.get("status"),
                review_note=data.get("review_note"),
                reviewed_by=data.get("reviewed_by"),
                reviewed_at=data.get("reviewed_at"),
                created_at=data.get("created_at"),
            )
        except ValueError as e:
            import logging
            logging.getLogger(__name__).error(f"Invalid registration data: {e}")
            return None

    @classmethod
    def from_rows(cls, rows) -> List["PlantRegistration"]:
        return [item for row in rows if (item := cls.from_row(row))]
