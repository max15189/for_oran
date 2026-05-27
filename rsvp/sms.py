import os
import logging
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER  = os.getenv("TWILIO_FROM_NUMBER")
MESSAGE_CHANNEL     = os.getenv("MESSAGE_CHANNEL", "sms").lower()  # "sms" or "whatsapp"


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


def _channel(phone: str) -> str:
    """Prefix phone with whatsapp: if using WhatsApp channel."""
    e164 = normalize_phone(phone)
    if MESSAGE_CHANNEL == "whatsapp":
        return f"whatsapp:{e164}"
    return e164


def send_message(to: str, message: str) -> bool:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    from_  = TWILIO_FROM_NUMBER
    to_    = _channel(to)

    # WhatsApp from-number also needs the prefix
    if MESSAGE_CHANNEL == "whatsapp" and not from_.startswith("whatsapp:"):
        from_ = f"whatsapp:{from_}"

    try:
        msg = client.messages.create(body=message, from_=from_, to=to_)
        log.info("[%s] Message sent to %s — SID: %s", MESSAGE_CHANNEL, to, msg.sid)
        return True
    except Exception as exc:
        log.error("[%s] Failed to send to %s: %s", MESSAGE_CHANNEL, to, exc)
        return False
