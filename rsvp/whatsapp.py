import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")


def _headers():
    return {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}


def normalize_phone(phone: str) -> str:
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        return phone[1:]
    if phone.startswith("0"):
        return "972" + phone[1:]
    return phone


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


def send_invitation(phone: str, message: str, rsvp_link: str, media_id: str = None) -> bool:
    to = normalize_phone(phone)
    full_text = f"{message}\n\nPlease RSVP here:\n{rsvp_link}"

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
        log.info("Sent invitation to %s", phone)
        return True
    except requests.RequestException as exc:
        log.error("Failed to send to %s: %s", phone, exc)
        return False
