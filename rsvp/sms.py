import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER  = os.getenv("TWILIO_FROM_NUMBER")


def normalize_phone(phone: str) -> str:
    """Convert any Israeli format to E.164 (+972XXXXXXXXX)."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone
    if phone.startswith("0"):
        return "+972" + phone[1:]
    if phone.startswith("972"):
        return "+" + phone
    return phone


def send_sms(to: str, message: str) -> bool:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(
            body=message,
            from_=TWILIO_FROM_NUMBER,
            to=normalize_phone(to),
        )
        log.info("SMS sent to %s — SID: %s", to, msg.sid)
        return True
    except Exception as exc:
        log.error("Failed to send to %s: %s", to, exc)
        return False
