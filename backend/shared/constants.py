"""Centralized constants shared across backend services."""

# Security / auth — JWT_SECRET must be set via environment (never in code)
JWT_DEFAULT_EXPIRES_HOURS = 8
JWT_ALGORITHM = "HS256"

# Common roles
ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_SUPERVISEUR = "superviseur"
ROLE_TECHNICIEN = "technicien"
VALID_ROLES = {
    ROLE_SUPERADMIN,
    ROLE_ADMIN,
    ROLE_SUPERVISEUR,
    ROLE_TECHNICIEN,
}
ASSIGNMENT_ALLOWED_ROLES = {ROLE_ADMIN, ROLE_SUPERVISEUR}
REGISTRATION_REVIEW_ACTIONS = {"approve", "reject"}

# Domain entities
MACHINE_TYPES = [
    "moteur",
    "pompe",
    "compresseur",
    "echangeur",
]

# Alerts
ALERT_ACTION_ASSIGN = "assign"
ALERT_ACTION_ACKNOWLEDGE = "acknowledge"
ALERT_ACTION_RESOLVE = "resolve"
ALERT_ACTION_REOPEN = "reopen"
SEVERITY_CRITIQUE = "Critique"
SEVERITY_MAJEURE = "Majeure"
SEVERITY_MINEURE = "Mineure"
SEVERITY_THRESHOLD_CRITIQUE = 0.85
SEVERITY_THRESHOLD_MAJEURE = 0.65
SEVERITY_THRESHOLD_MINEURE = 0.40
ALERT_SUPPORTED_ACTIONS = frozenset(
    {
        ALERT_ACTION_ASSIGN,
        ALERT_ACTION_ACKNOWLEDGE,
        ALERT_ACTION_RESOLVE,
        ALERT_ACTION_REOPEN,
    }
)

# Gateway defaults
GATEWAY_DEFAULT_PORT = 5000
IOT_DEFAULT_PORT = 5001
ML_DEFAULT_PORT = 5002
ALERTES_DEFAULT_PORT = 5003
AUTH_DEFAULT_PORT = 5004
AUTH_SERVICE_DEFAULT_URL = "http://auth:5004"
IOT_SERVICE_DEFAULT_URL = "http://iot:5001"
ML_SERVICE_DEFAULT_URL = "http://ml:5002"
ALERTES_SERVICE_DEFAULT_URL = "http://alertes:5003"
FRONTEND_DEFAULT_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
)

# ML defaults
REDIS_DEFAULT_URL = "redis://localhost:6379"
REDIS_SENSOR_CHANNEL = "sensor_data"
REDIS_ML_PREDICTIONS_CHANNEL = "ml_predictions"
# External integrations
RESEND_API_DEFAULT_URL = "https://api.resend.com/emails"
APP_BASE_DEFAULT_URL = "http://localhost:3000"
