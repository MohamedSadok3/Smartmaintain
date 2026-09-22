from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request

from .config import get_env
from .constants import JWT_ALGORITHM, JWT_DEFAULT_EXPIRES_HOURS


# JWT_SECRET must come from the environment — no default in code.
JWT_SECRET = get_env("JWT_SECRET", required=True)
JWT_EXPIRES_HOURS = int(get_env("JWT_EXPIRES_HOURS", str(JWT_DEFAULT_EXPIRES_HOURS)))


def create_token(user, expires_hours=JWT_EXPIRES_HOURS):
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "machines": user.machines or [],
        "plant_id": user.plant_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_current_user():
    return getattr(g, "current_user", None)


def parse_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def get_current_user_from_request():
    token = parse_bearer_token()
    if not token:
        return None
    try:
        return decode_token(token)
    except jwt.InvalidTokenError:
        return None


def require_auth(roles=None):
    """Validate JWT on each downstream service route (defence in depth).

    The gateway already rejects invalid tokens before proxying, but each
    service re-validates independently so a compromised or bypassed gateway
    cannot impersonate users on internal endpoints.
    """
    roles = roles or []

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            token = parse_bearer_token()
            if not token:
                return jsonify({"error": "Unauthorized"}), 401

            try:
                payload = decode_token(token)
            except jwt.InvalidTokenError:
                return jsonify({"error": "Unauthorized"}), 401

            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403

            g.current_user = payload
            return func(*args, **kwargs)

        return wrapped

    return decorator
