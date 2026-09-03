"""
Gateway Service - SmartMaintain API Gateway
===========================================
Central API gateway with:
- Request proxying to microservices
- JWT authentication
- WebSocket bridge (Redis → Frontend)
- Health check aggregation

Optimizations:
- Connection pooling for HTTP requests
- Structured logging
- Graceful error handling
- Efficient Redis pub/sub
"""

import eventlet
eventlet.monkey_patch()

import json
import logging
import threading
import time
from typing import Dict, Optional

import redis
import requests
import socketio
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room

from shared.config import get_env
from shared.constants import (
    ALERTES_SERVICE_DEFAULT_URL,
    AUTH_SERVICE_DEFAULT_URL,
    FRONTEND_DEFAULT_ORIGINS,
    GATEWAY_DEFAULT_PORT,
    IOT_SERVICE_DEFAULT_URL,
    ML_SERVICE_DEFAULT_URL,
    REDIS_DEFAULT_URL,
)
from shared.auth import decode_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(get_env("GATEWAY_PORT", str(GATEWAY_DEFAULT_PORT)))
AUTH_URL = get_env("AUTH_URL", AUTH_SERVICE_DEFAULT_URL)
IOT_URL = get_env("IOT_URL", IOT_SERVICE_DEFAULT_URL)
ML_URL = get_env("ML_URL", ML_SERVICE_DEFAULT_URL)
ALERTES_URL = get_env("ALERTES_URL", ALERTES_SERVICE_DEFAULT_URL)
REDIS_URL = get_env("REDIS_URL", REDIS_DEFAULT_URL)
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in get_env("FRONTEND_ORIGINS", ",".join(FRONTEND_DEFAULT_ORIGINS)).split(",")
    if origin.strip()
]

# Service routing map
SERVICE_MAP = {
    "auth": AUTH_URL,
    "users": AUTH_URL,
    "plants": AUTH_URL,
    "components": AUTH_URL,
    "iot": IOT_URL,
    "ml": ML_URL,
    "alertes": ALERTES_URL,
    "dashboard": ALERTES_URL,
}

# HTTP session with connection pooling (performance optimization)
http_session = requests.Session()
adapter = requests.adapters.HTTPAdapter(
    pool_connections=20,
    pool_maxsize=20,
    max_retries=3
)
http_session.mount("http://", adapter)
http_session.mount("https://", adapter)

# Flask app
app = Flask(__name__)
CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True)
socketio_server = SocketIO(
    app, cors_allowed_origins=FRONTEND_ORIGINS, async_mode="eventlet"
)

# Legacy WebSocket client for Alertes service (fallback)
alertes_socket = socketio.Client(reconnection=True)

logger.info(f"Gateway initialized on port {PORT}")
logger.info(f"Frontend origins: {FRONTEND_ORIGINS}")
logger.info(f"Service map: {SERVICE_MAP}")

SUPERADMIN_ROOM = "role:superadmin"


@socketio_server.on("connect")
def authenticate_socket(auth):
    """Authenticate Socket.IO clients and isolate them by plant."""
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        logger.warning("Rejected WebSocket connection without token")
        return False
    try:
        payload = decode_token(token)
    except Exception:
        logger.warning("Rejected WebSocket connection with invalid token")
        return False

    if payload.get("role") == "superadmin":
        join_room(SUPERADMIN_ROOM)
        return True

    plant_id = payload.get("plant_id")
    if plant_id is None:
        logger.warning("Rejected WebSocket connection without plant scope")
        return False
    join_room(f"plant:{int(plant_id)}")
    return True


def emit_to_tenant(event, data):
    """Emit an event only to its plant and to authorized superadmins."""
    plant_id = data.get("plant_id") if isinstance(data, dict) else None
    if plant_id is None:
        logger.warning("Dropped unscoped WebSocket event %s", event)
        return
    socketio_server.emit(event, data, to=f"plant:{int(plant_id)}")
    socketio_server.emit(event, data, to=SUPERADMIN_ROOM)



# ============================================================================
# Request Proxying
# ============================================================================

def _build_target_url(section: str, path: str) -> str:
    """Build target URL for service proxying."""
    base = SERVICE_MAP[section]
    if path:
        return f"{base}/api/{section}/{path}"
    return f"{base}/api/{section}"


def _proxy_request(section: str, path: str = "") -> Response:
    """
    Proxy HTTP request to backend microservice.
    
    Optimizations:
    - Uses persistent HTTP session with connection pooling
    - Strips unnecessary headers
    - 15s timeout to prevent hanging
    """
    target_url = _build_target_url(section, path)

    # Filter headers (exclude hop-by-hop headers)
    excluded_headers = {"host", "content-length"}
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in excluded_headers
    }

    try:
        # Use pooled session (faster than requests.request)
        upstream_response = http_session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=15,
        )

        # Filter response headers
        response_headers = [
            (name, value)
            for name, value in upstream_response.headers.items()
            if name.lower() not in {"content-encoding", "transfer-encoding", "connection"}
        ]

        return Response(
            response=upstream_response.content,
            status=upstream_response.status_code,
            headers=response_headers,
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout proxying request to {section}: {target_url}")
        return jsonify({"error": "Service timeout"}), 504
    except Exception as e:
        logger.error(f"Error proxying request to {section}: {e}")
        return jsonify({"error": "Service unavailable"}), 503


# ============================================================================
# Authentication
# ============================================================================

def _is_public_route() -> bool:
    """Check if current route is public (no JWT required)."""
    if request.path == "/health" and request.method == "GET":
        return True
    if request.path == "/api/auth/login" and request.method == "POST":
        return True
    if request.path == "/api/auth/register-plant" and request.method == "POST":
        return True
    return False


@app.before_request
def require_jwt():
    """Require valid JWT for all API routes except public endpoints."""
    # Allow OPTIONS (CORS preflight)
    if request.method == "OPTIONS":
        return None
    
    # Allow public routes
    if _is_public_route():
        return None
    
    # Non-API routes don't require auth
    if not request.path.startswith("/api/"):
        return None

    # Validate JWT
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(" ", 1)[1].strip()
    try:
        decode_token(token)
    except Exception as e:
        logger.warning(f"Invalid JWT token: {e}")
        return jsonify({"error": "Unauthorized"}), 401
    
    return None



# ============================================================================
# API Routes (Dynamic Proxy Registration)
# ============================================================================

PROXY_SECTIONS = [
    "auth",
    "users",
    "components",
    "plants",
    "iot",
    "ml",
    "alertes",
    "dashboard",
]

# Register proxy routes dynamically
for section in PROXY_SECTIONS:
    endpoint = f"proxy_{section}"
    
    # Base route: /api/{section}
    app.add_url_rule(
        f"/api/{section}",
        endpoint,
        (lambda section: (lambda path="": _proxy_request(section, path)))(section),
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    )
    
    # Path route: /api/{section}/<path>
    app.add_url_rule(
        f"/api/{section}/<path:path>",
        f"{endpoint}_path",
        (lambda section: (lambda path: _proxy_request(section, path)))(section),
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    )

logger.info(f"Registered proxy routes for {len(PROXY_SECTIONS)} sections")


# ============================================================================
# Health Check
# ============================================================================

@app.route("/health", methods=["GET"])
def health() -> Dict:
    """
    Aggregate health check from all backend services.
    
    Returns service status for monitoring and load balancers.
    """
    services = {
        "auth": AUTH_URL,
        "iot": IOT_URL,
        "ml": ML_URL,
        "alertes": ALERTES_URL,
    }
    health_status = {"gateway": "ok"}

    for name, base_url in services.items():
        try:
            response = http_session.get(f"{base_url}/health", timeout=3)
            is_ok = response.status_code == 200 and response.json().get("status") == "ok"
            health_status[name] = "ok" if is_ok else "error"
        except Exception as e:
            logger.debug(f"Health check failed for {name}: {e}")
            health_status[name] = "error"

    return jsonify(health_status)



# ============================================================================
# WebSocket Bridges
# ============================================================================

# Legacy WebSocket handlers (for Alertes service fallback)
@alertes_socket.on("alert:new")
def on_alert_new(data):
    """Forward new alert from Alertes service to frontend."""
    emit_to_tenant("alert:new", data)
    logger.debug(f"Forwarded alert:new: {data.get('id', 'unknown')}")


@alertes_socket.on("alert:updated")
def on_alert_updated(data):
    """Forward alert update from Alertes service to frontend."""
    emit_to_tenant("alert:updated", data)
    logger.debug(f"Forwarded alert:updated: {data.get('id', 'unknown')}")


@alertes_socket.on("sensor:data")
def on_sensor_data(data):
    """Forward sensor data from Alertes service to frontend."""
    emit_to_tenant("sensor:data", data)


def connect_to_alertes():
    """
    Legacy WebSocket bridge to Alertes service.
    
    Kept for backward compatibility when Alertes service is operational.
    Uses exponential backoff for reconnection.
    """
    delay = 1
    max_delay = 60

    logger.info("Starting legacy Alertes WebSocket bridge...")
    
    while True:
        try:
            if not alertes_socket.connected:
                logger.info(f"Connecting to Alertes WebSocket: {ALERTES_URL}")
                alertes_socket.connect(ALERTES_URL, transports=["websocket", "polling"])
                logger.info("✅ Connected to Alertes WebSocket")
                delay = 1  # Reset delay on successful connection
            alertes_socket.wait()
        except Exception as e:
            logger.warning(f"Alertes WebSocket connection error: {e}")

        try:
            if alertes_socket.connected:
                alertes_socket.disconnect()
        except Exception:
            pass

        time.sleep(delay)
        delay = min(delay * 2, max_delay)  # Exponential backoff


def redis_to_websocket_bridge():
    """
    Direct Redis → WebSocket bridge (PRIMARY METHOD).
    
    Workaround for Alertes service PostgreSQL initialization issues.
    Consumes ml_predictions from Redis and emits sensor:data to frontend.
    
    This bridge ensures data flow even when Alertes service is down,
    providing high availability for real-time monitoring.
    """
    logger.info("🔄 Starting Redis→WebSocket bridge (PRIMARY)")
    
    retry_delay = 5
    
    while True:
        try:
            # Create Redis client with connection pooling
            redis_pool = redis.ConnectionPool.from_url(
                REDIS_URL,
                max_connections=5,
                decode_responses=True
            )
            redis_client = redis.Redis(connection_pool=redis_pool)
            pubsub = redis_client.pubsub()
            pubsub.subscribe("ml_predictions")
            
            logger.info("✅ Redis→WebSocket bridge connected")
            
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        machine = payload.get('machine', 'unknown')
                        
                        # Emit to frontend WebSocket
                        emit_to_tenant("sensor:data", payload)
                        logger.debug(f"📡 Emitted sensor:data for {machine}")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in Redis message: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
                        continue
                        
        except redis.ConnectionError as e:
            logger.error(f"⚠️  Redis connection error: {e}")
        except Exception as e:
            logger.error(f"⚠️  Redis→WebSocket bridge error: {e}", exc_info=True)
        
        # Retry after delay
        logger.info(f"Reconnecting Redis bridge in {retry_delay}s...")
        time.sleep(retry_delay)


# ============================================================================
# Background Threads
# ============================================================================

# Start legacy Alertes bridge (fallback)
bridge_thread = threading.Thread(
    target=connect_to_alertes,
    daemon=True,
    name="AlertesBridge"
)
bridge_thread.start()

# Start Redis→WebSocket bridge (primary)
redis_bridge_thread = threading.Thread(
    target=redis_to_websocket_bridge,
    daemon=True,
    name="RedisBridge"
)
redis_bridge_thread.start()

logger.info("✅ Background bridges started")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info(f"Starting Gateway server on 0.0.0.0:{PORT}")
    socketio_server.run(app, host="0.0.0.0", port=PORT, debug=False)
