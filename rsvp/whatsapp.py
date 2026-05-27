import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_TOKEN   = os.getenv("WHATSAPP_TOKEN")


def normalize_phone(phone: str) -> str:
    """Convert any Israeli format to international digits only (e.g. 972501234567)."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone[1:]
    if phone.startswith("0"):
        return "972" + phone[1:]
    return phone


def _headers():
    return {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}


def upload_image(image_path: str) -> str:
    phone_number_id = WHATSAPP_API_URL.split("/")[-2]
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/media"
    with open(image_path, "rb") as f:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"},
            files={"file": ("invitation.png", f, "image/png")},
            data={"messaging_product": "whatsapp", "type": "image/png"},
            timeout=30,
        )
    resp.raise_for_status()
    return resp.json()["id"]


def send_invitation(phone: str, message: str, media_id: str = None) -> bool:
    to = normalize_phone(phone)
    full_text = (
        f"{message}\n\n"
        "Please reply with:\n"
        "1 - Yes, I'll be there! ✓\n"
        "2 - Sadly I can't make it ✗\n"
        "3 - Not sure yet ?\n\n"
        "Just send 1, 2, or 3"
    )

    if media_id:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"id": media_id, "caption": full_text},
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": full_text},
        }

    try:
        resp = requests.post(WHATSAPP_API_URL, json=payload, headers=_headers(), timeout=15)
        resp.raise_for_status()
        log.info("Invitation sent to %s", phone)
        return True
    except requests.RequestException as exc:
        log.error("Failed to send to %s: %s", phone, exc)
        return False
