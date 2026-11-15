import base64
import json
import logging
import smtplib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage

from app.config import settings
from app.models import Alert

logger = logging.getLogger(__name__)


def _alert_subject(alert: Alert) -> str:
    return f"[LPR Alert] {alert.alert_type.value} — {alert.plate_number}"


def send_email_alert(alert: Alert) -> bool:
    if not settings.smtp_enabled or not settings.notify_email_to or not settings.smtp_host:
        return False
    msg = EmailMessage()
    from_addr = settings.smtp_from or settings.smtp_user or "numberplates@localhost"
    msg["From"] = from_addr
    msg["To"] = settings.notify_email_to
    msg["Subject"] = _alert_subject(alert)
    msg.set_content(alert.message)
    try:
        if settings.smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                server.starttls(context=context)
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        return True
    except OSError as exc:
        logger.warning("Email alert failed: %s", exc)
        return False


def send_sms_alert(alert: Alert) -> bool:
    if not settings.sms_enabled or not settings.notify_sms_to:
        return False
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_from_number:
        return False
    body = f"{_alert_subject(alert)}\n{alert.message}"[:1500]
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    )
    payload = urllib.parse.urlencode(
        {
            "To": settings.notify_sms_to,
            "From": settings.twilio_from_number,
            "Body": body,
        }
    ).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    creds = f"{settings.twilio_account_sid}:{settings.twilio_auth_token}".encode("utf-8")
    req.add_header("Authorization", "Basic " + base64.b64encode(creds).decode("ascii"))
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            json.loads(resp.read().decode("utf-8"))
        return True
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        logger.warning("SMS alert failed: %s", exc)
        return False


def notify_alert(alert: Alert) -> None:
    send_email_alert(alert)
    send_sms_alert(alert)
