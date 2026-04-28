import os
import random
import logging
import time
import schedule
import requests
from dotenv import load_dotenv
from questions import QUESTIONS

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("whatsapp_sender.log"),
    ],
)
log = logging.getLogger(__name__)

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")  # e.g. https://graph.facebook.com/v19.0/<phone-id>/messages
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
RECIPIENT_PHONE = os.getenv("RECIPIENT_PHONE")  # international format, no +, e.g. 972501234567


def pick_question() -> str:
    return random.choice(QUESTIONS)


def send_whatsapp_message(text: str) -> bool:
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_PHONE,
        "type": "text",
        "text": {"body": text},
    }
    try:
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        log.info("Message sent successfully: %s", text[:60])
        return True
    except requests.RequestException as exc:
        log.error("Failed to send message: %s", exc)
        return False


def send_random_question():
    question = pick_question()
    log.info("Sending question: %s", question)
    send_whatsapp_message(question)


def validate_env():
    missing = [v for v in ("WHATSAPP_API_URL", "WHATSAPP_TOKEN", "RECIPIENT_PHONE") if not os.getenv(v)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")


def main():
    validate_env()
    log.info("WhatsApp hourly question bot started.")
    log.info("Recipient: %s", RECIPIENT_PHONE)

    # Send one immediately on startup, then every hour
    send_random_question()

    schedule.every(1).hour.do(send_random_question)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
