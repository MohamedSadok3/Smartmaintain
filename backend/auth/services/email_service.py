import base64
import smtplib
from email.message import EmailMessage

import requests

from shared.config import get_env
from shared.constants import APP_BASE_DEFAULT_URL, RESEND_API_DEFAULT_URL


class EmailService:
    def __init__(self):
        self.mail_provider = (get_env("MAIL_PROVIDER", "resend") or "resend").strip().lower()
        self.api_key = get_env("RESEND_API_KEY")
        self.from_email = get_env("MAIL_FROM_EMAIL") or get_env("RESEND_FROM_EMAIL")
        self.api_url = get_env("RESEND_API_URL", RESEND_API_DEFAULT_URL)
        self.app_base_url = get_env("APP_BASE_URL", APP_BASE_DEFAULT_URL)
        self.smtp_host = get_env("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(get_env("SMTP_PORT", "587"))
        self.smtp_username = get_env("SMTP_USERNAME")
        self.smtp_password = get_env("SMTP_PASSWORD")

    def _send_via_resend(self, payload, context_label):
        if not self.api_key or not self.from_email:
            print(f"Skipping {context_label}: Resend is not configured.")
            return False

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            if response.status_code >= 400:
                print(
                    f"Resend error during {context_label}: status={response.status_code}, body={response.text}"
                )
                return False
            return True
        except Exception as exc:
            print(f"Failed during {context_label}: {exc}")
            return False

    def _send_via_smtp(self, payload, context_label):
        if not self.from_email or not self.smtp_username or not self.smtp_password:
            import sys
            print(f"Skipping {context_label}: SMTP is not configured.", file=sys.stderr)
            return False

        to_list = payload.get("to") or []
        if not to_list:
            return False

        # MODE DEMO: Afficher les emails au lieu de les envoyer
        import sys
        sys.stderr.write(f"\n{'='*80}\n")
        sys.stderr.write(f"📧 EMAIL SIMULATION - {context_label}\n")
        sys.stderr.write(f"{'='*80}\n")
        sys.stderr.write(f"From: {self.from_email}\n")
        sys.stderr.write(f"To: {', '.join(to_list)}\n")
        sys.stderr.write(f"Subject: {payload.get('subject', '')}\n")
        sys.stderr.write(f"\nBody:\n{payload.get('text', '')}\n")
        if payload.get("attachments"):
            sys.stderr.write(f"\nAttachments: {len(payload.get('attachments'))} file(s)\n")
        sys.stderr.write(f"{'='*80}\n\n")
        sys.stderr.flush()
        
        # Pour la démo, on retourne True sans vraiment envoyer
        return True

        # CODE ORIGINAL (commenté pour la démo)
        # try:
        #     message = EmailMessage()
        #     message["From"] = self.from_email
        #     message["To"] = ", ".join(to_list)
        #     message["Subject"] = payload.get("subject", "")
        #     message.set_content(payload.get("text", ""))

        #     for attachment in payload.get("attachments", []):
        #         raw_content = (attachment.get("content") or "").strip()
        #         if not raw_content:
        #             continue
        #         try:
        #             decoded = base64.b64decode(raw_content)
        #         except Exception:
        #             continue
        #         filename = attachment.get("filename") or "document.pdf"
        #         message.add_attachment(
        #             decoded,
        #             maintype="application",
        #             subtype="pdf",
        #             filename=filename,
        #         )

        #     with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
        #         server.starttls()
        #         server.login(self.smtp_username, self.smtp_password)
        #         server.send_message(message)
        #     return True
        # except Exception as exc:
        #     import sys
        #     print(f"SMTP error during {context_label}: {exc}", file=sys.stderr)
        #     return False

    def _send_email(self, payload, context_label):
        if self.mail_provider == "smtp":
            return self._send_via_smtp(payload, context_label)
        return self._send_via_resend(payload, context_label)

    def send_registration_received_email(self, recipient_email, recipient_name, plant_name, plant_code):
        """Confirm to company contact that the registration request was received."""
        if not recipient_email:
            return False

        subject = f"Demande d'inscription recue - {plant_name}"
        body = (
            f"Bonjour {recipient_name or ''},\n\n"
            "Nous avons bien recu votre demande d'inscription.\n"
            "Elle est en cours de validation par notre equipe.\n\n"
            f"Nom de l'usine: {plant_name}\n"
            "\n"
            "Vous recevrez un email lorsque la demande sera traitee.\n\n"
            "Cordialement,\n"
            "Equipe SmartMaintain"
        )

        return self._send_email(
            {
                "to": [recipient_email],
                "subject": subject,
                "text": body,
            },
            context_label=f"registration received email to {recipient_email}",
        )

    def send_registration_approved_email(self, recipient_email, recipient_name, plant_name, plant_code):
        """Send email notification when plant registration is approved."""
        if not recipient_email:
            return False

        login_url = f"{self.app_base_url.rstrip('/')}/login"
        subject = f"Inscription de l'usine {plant_name} approuvee"
        body = (
            f"Bonjour {recipient_name or ''},\n\n"
            f"L'inscription de votre usine a ete approuvee.\n\n"
            f"Nom de l'usine: {plant_name}\n"
            "\n"
            f"Vous pouvez vous connecter ici: {login_url}\n\n"
            "Cordialement,\n"
            "Equipe SmartMaintain"
        )

        return self._send_email(
            {
                "to": [recipient_email],
                "subject": subject,
                "text": body,
            },
            context_label=f"approval email to {recipient_email}",
        )

    def send_registration_documents_to_superadmin(
        self, recipient_email, recipient_name, registration_id, plant_name, plant_code, documents
    ):
        """Send new registration notification to superadmin with attached legal docs."""
        if not recipient_email:
            return False

        attachments = []
        for key in ("patente", "rne"):
            doc = (documents or {}).get(key) or {}
            content = (doc.get("data") or "").strip()
            filename = (doc.get("name") or f"{key}.pdf").strip()
            if not content:
                continue
            # Accept either raw base64 content or data-URI form.
            if "," in content and content.lower().startswith("data:"):
                content = content.split(",", 1)[1]
            attachments.append({"filename": filename, "content": content})

        subject = f"Nouvelle demande d'inscription usine: {plant_name}"
        body = (
            f"Bonjour {recipient_name or 'Superadmin'},\n\n"
            f"Une nouvelle demande d'inscription est en attente de validation.\n\n"
            f"ID demande: {registration_id}\n"
            f"Usine: {plant_name}\n"
            "\n"
            "Les documents Patente/RNE sont joints a ce message.\n"
        )
        payload = {
            "to": [recipient_email],
            "subject": subject,
            "text": body,
        }
        if attachments:
            payload["attachments"] = attachments

        return self._send_email(
            payload,
            context_label=f"registration documents email to {recipient_email}",
        )
