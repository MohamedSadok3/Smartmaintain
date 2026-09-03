import re
import json
import base64
import binascii
import secrets
import unicodedata
import bcrypt

from shared.constants import (
    REGISTRATION_REVIEW_ACTIONS,
    ROLE_ADMIN,
    ROLE_SUPERVISEUR,
    ROLE_TECHNICIEN,
)
from shared.database import get_db_connection
from models import Plant, PlantRegistration
from .email_service import EmailService
from queries import (
    AUTH_SELECT_SUPERADMINS,
    REGISTRATION_CHECK_PLANT_EXISTS,
    REGISTRATION_CHECK_PENDING_EXISTS,
    REGISTRATION_CHECK_EMAILS_TAKEN,
    REGISTRATION_INSERT,
    REGISTRATION_SELECT_ALL,
    REGISTRATION_SELECT_BY_STATUS,
    REGISTRATION_SELECT_BY_ID,
    REGISTRATION_REJECT,
    REGISTRATION_INSERT_USER,
    REGISTRATION_APPROVE,
    PLANT_INSERT_ON_APPROVE,
)

MAX_DOCUMENT_BYTES = 5 * 1024 * 1024
PDF_SIGNATURE = b"%PDF-"


def _generate_plant_code(plant_name):
    """Generate a unique internal code; it is not a user-facing field."""
    ascii_name = unicodedata.normalize("NFKD", plant_name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or "usine"
    slug = slug[:23].rstrip("-")
    if len(slug) < 3:
        slug = f"usine-{slug}"[:23].rstrip("-")
    return f"{slug}-{secrets.token_hex(4)}"


def _validate_pdf_document(document, label):
    """Validate a base64-encoded PDF without trusting browser metadata."""
    encoded = document.get("data") if isinstance(document, dict) else None
    filename = (document.get("name") or "").strip() if isinstance(document, dict) else ""
    if not encoded or not filename.lower().endswith(".pdf"):
        return f"Le document {label} doit être un fichier PDF."
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        return f"Le document {label} est invalide."
    if not raw.startswith(PDF_SIGNATURE):
        return f"Le document {label} n'est pas un PDF valide."
    if len(raw) > MAX_DOCUMENT_BYTES:
        return f"Le document {label} dépasse la taille maximale de 5 Mo."
    return None


class RegistrationService:
    def __init__(self):
        self.email_service = EmailService()

    def register_plant(self, plant_data, users_data, documents=None):
        """Register a new plant with initial users and optional legal documents."""
        plant_name = (plant_data.get("name") or "").strip()
        contact_name = (plant_data.get("contact_name") or "").strip()
        contact_email = (plant_data.get("contact_email") or "").strip().lower()

        if not all([plant_name, contact_name, contact_email]):
            return None, "Les informations de l'usine sont incomplètes."
        plant_code = _generate_plant_code(plant_name)

        admin_user = users_data.get("admin") or {}
        if not all((admin_user.get(field) or "").strip() for field in ("name", "email", "password")):
            return None, "Le compte administrateur est requis (nom, email, mot de passe)."
        if len(admin_user.get("password", "")) < 8:
            return None, "Le mot de passe administrateur doit contenir au moins 8 caractères."

        if not documents or not documents.get("patente") or not documents.get("rne"):
            return None, "Les documents Patente et RNE sont obligatoires."

        patente_doc = documents.get("patente") or {}
        rne_doc = documents.get("rne") or {}
        for document, label in ((patente_doc, "Patente"), (rne_doc, "RNE")):
            document_error = _validate_pdf_document(document, label)
            if document_error:
                return None, document_error

        emails = [admin_user.get("email", "").strip().lower(), contact_email]

        password_hash = bcrypt.hashpw(
            admin_user.get("password", "").encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        payload = {
            "plant": {
                "name": plant_name,
                "code": plant_code,
                "contact_name": contact_name,
                "contact_email": contact_email,
            },
            "users": {
                "admin": {
                    "name": admin_user.get("name", "").strip(),
                    "email": admin_user.get("email", "").strip().lower(),
                    "password_hash": password_hash,
                    "machines": [],
                },
            },
            "documents": {
                "patente": {"data": patente_doc.get("data"), "name": patente_doc.get("name", "patente.pdf")},
                "rne": {"data": rne_doc.get("data"), "name": rne_doc.get("name", "rne.pdf")},
            },
        }

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(REGISTRATION_CHECK_PLANT_EXISTS, (plant_code, plant_name))
                if cur.fetchone():
                    return None, "Cette usine existe déjà."
                cur.execute(REGISTRATION_CHECK_PENDING_EXISTS, (plant_code, plant_name))
                if cur.fetchone():
                    return None, "Une demande d'inscription est déjà en attente pour cette usine."
                cur.execute(REGISTRATION_CHECK_EMAILS_TAKEN, (emails,))
                if cur.fetchone():
                    return None, "Un ou plusieurs emails sont déjà utilisés."

                cur.execute(
                    REGISTRATION_INSERT,
                    (plant_name, plant_code, contact_name, contact_email, json.dumps(payload)),
                )
                row = cur.fetchone()
                registration = PlantRegistration.from_row(row)
                conn.commit()

        self._notify_after_registration_submitted(registration)
        return registration, None

    def _notify_after_registration_submitted(self, registration):
        """Contact: confirmation received. Superadmins: new request + documents."""
        payload = registration.payload_data
        plant_payload = payload.get("plant") or {}
        documents_payload = payload.get("documents") or {}
        plant_name = plant_payload.get("name") or registration.plant_name
        plant_code = plant_payload.get("code") or registration.plant_code

        contact_email = (plant_payload.get("contact_email") or registration.contact_email or "").strip().lower()
        contact_name = (plant_payload.get("contact_name") or registration.contact_name or "").strip() or "Responsable usine"
        if contact_email:
            self.email_service.send_registration_received_email(
                recipient_email=contact_email,
                recipient_name=contact_name,
                plant_name=plant_name,
                plant_code=plant_code,
            )

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(AUTH_SELECT_SUPERADMINS)
                superadmin_rows = cur.fetchall()

        for row in superadmin_rows:
            superadmin_email = (row.get("email") or "").strip().lower()
            if not superadmin_email:
                continue
            self.email_service.send_registration_documents_to_superadmin(
                recipient_email=superadmin_email,
                recipient_name=row.get("name") or "Superadmin",
                registration_id=registration.id,
                plant_name=plant_name,
                plant_code=plant_code,
                documents=documents_payload,
            )

    def list_registrations(self, status="pending"):
        """List plant registrations."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if status == "all":
                    cur.execute(REGISTRATION_SELECT_ALL)
                else:
                    cur.execute(REGISTRATION_SELECT_BY_STATUS, (status,))
                rows = cur.fetchall()
                return PlantRegistration.from_rows(rows)

    def review_registration(self, registration_id, action, review_note, reviewer_id):
        """Approve or reject a plant registration."""
        if action not in REGISTRATION_REVIEW_ACTIONS:
            return None, "L'action doit être 'approve' ou 'reject'."

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(REGISTRATION_SELECT_BY_ID, (registration_id,))
                row = cur.fetchone()
                registration = PlantRegistration.from_row(row)
                if not registration:
                    return None, "Inscription introuvable."
                if registration.status != "pending":
                    return None, "Cette inscription a déjà été traitée."

                payload = registration.payload_data
                users_payload = payload.get("users") or {}

                if action == "reject":
                    for user_payload in users_payload.values():
                        if isinstance(user_payload, dict):
                            user_payload.pop("password", None)
                            user_payload.pop("password_hash", None)
                    cur.execute(
                        REGISTRATION_REJECT,
                        (review_note, reviewer_id, json.dumps(payload), registration_id),
                    )
                    row = cur.fetchone()
                    reviewed = PlantRegistration.from_row(row)
                    conn.commit()
                    return reviewed, None

                plant_payload = payload.get("plant") or {}
                admin_payload = users_payload.get("admin") or {}

                admin_password_hash = admin_payload.get("password_hash")
                if not admin_password_hash:
                    legacy_password = admin_payload.get("password", "")
                    if not legacy_password:
                        return None, "La demande ne contient pas de mot de passe administrateur valide."
                    admin_password_hash = bcrypt.hashpw(
                        legacy_password.encode("utf-8"), bcrypt.gensalt()
                    ).decode("utf-8")

                cur.execute(
                    PLANT_INSERT_ON_APPROVE,
                    (
                        plant_payload.get("name"),
                        plant_payload.get("code"),
                        plant_payload.get("contact_name"),
                        plant_payload.get("contact_email"),
                        reviewer_id,
                    ),
                )
                plant_row = cur.fetchone()
                plant = Plant.from_row(plant_row)

                for role_key in (ROLE_ADMIN, ROLE_SUPERVISEUR, ROLE_TECHNICIEN):
                    user_payload = users_payload.get(role_key)
                    if not user_payload:
                        continue
                    # New registrations store only a bcrypt hash. Keep a
                    # one-time compatibility path for pending legacy rows.
                    password_hash = (
                        admin_password_hash
                        if role_key == ROLE_ADMIN
                        else user_payload.get("password_hash")
                    )
                    if not password_hash:
                        continue
                    cur.execute(
                        REGISTRATION_INSERT_USER,
                        (
                            user_payload.get("name"),
                            user_payload.get("email"),
                            password_hash,
                            role_key,
                            plant.id,
                            user_payload.get("machines") or [],
                        ),
                    )

                for user_payload in users_payload.values():
                    if isinstance(user_payload, dict):
                        user_payload.pop("password", None)
                        user_payload.pop("password_hash", None)
                cur.execute(
                    REGISTRATION_APPROVE,
                    (review_note, reviewer_id, json.dumps(payload), registration_id),
                )
                row = cur.fetchone()
                reviewed = PlantRegistration.from_row(row)
                conn.commit()

        admin_email = (admin_payload.get("email") or "").strip().lower()
        admin_name = (admin_payload.get("name") or "").strip() or "Admin usine"
        if admin_email:
            self.email_service.send_registration_approved_email(
                recipient_email=admin_email,
                recipient_name=admin_name,
                plant_name=plant_payload.get("name") or registration.plant_name,
                plant_code=plant_payload.get("code") or registration.plant_code,
            )

        return reviewed, plant
