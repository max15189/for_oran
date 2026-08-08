"""WhatsApp notifications.

Reuses the exact WhatsApp Cloud API pattern from the root project's
``whatsapp_sender.py`` — same three environment variables and the same
``raise_for_status`` + logging behavior — so credentials and setup are shared.
"""

import logging
import os

import requests

from models import Listing

log = logging.getLogger(__name__)

REQUIRED_ENV = ("WHATSAPP_API_URL", "WHATSAPP_TOKEN", "RECIPIENT_PHONE")


def validate_env() -> None:
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


def _fmt_price(listing: Listing) -> str:
    if listing.price is None:
        return "מחיר לא צוין"
    return f"{listing.price:,.0f} {listing.currency}"


def format_listing(listing: Listing) -> str:
    """Build a compact, readable WhatsApp message for one listing."""
    lines = ["🏠 דירה חדשה שמתאימה לחיפוש שלך"]

    if listing.title:
        lines.append(listing.title)

    location = " · ".join(p for p in (listing.neighborhood, listing.city) if p)
    if location:
        lines.append(f"📍 {location}")

    facts = []
    facts.append(f"💰 {_fmt_price(listing)}")
    if listing.rooms is not None:
        facts.append(f"🚪 {listing.rooms:g} חד'")
    if listing.sqm is not None:
        facts.append(f"📐 {listing.sqm:g} מ\"ר")
    if listing.floor is not None:
        facts.append(f"🏢 קומה {listing.floor}")
    if listing.furnished is True:
        facts.append("🛋️ מרוהט")
    elif listing.furnished is False:
        facts.append("לא מרוהט")
    lines.append("  ".join(facts))

    if listing.url:
        lines.append(listing.url)

    return "\n".join(lines)


def send_whatsapp_message(text: str) -> bool:
    """Send a single WhatsApp text message. Returns True on success."""
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_TOKEN')}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": os.getenv("RECIPIENT_PHONE"),
        "type": "text",
        "text": {"body": text},
    }
    try:
        response = requests.post(
            os.getenv("WHATSAPP_API_URL"), json=payload, headers=headers, timeout=15
        )
        response.raise_for_status()
        log.info("Message sent successfully: %s", text.splitlines()[0][:60])
        return True
    except requests.RequestException as exc:
        log.error("Failed to send message: %s", exc)
        return False


def notify(listing: Listing) -> bool:
    """Format and send a notification for one listing."""
    return send_whatsapp_message(format_listing(listing))
