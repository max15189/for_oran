import csv
import datetime
import logging
import os
import uuid

from dotenv import load_dotenv

from models import Guest, Session
from sms import normalize_phone, send_sms

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

INVITATION_MESSAGE = os.getenv("INVITATION_MESSAGE", "You are invited!")
GUESTS_CSV = os.path.join(os.path.dirname(__file__), "guests.csv")

MESSAGE_TEMPLATE = (
    "{message}\n\n"
    "Please reply with:\n"
    "1 - Yes, I'll be there! ✓\n"
    "2 - Sadly I can't make it ✗\n"
    "3 - Not sure yet ?"
)


def main():
    db = Session()
    sent = skipped = failed = 0

    with open(GUESTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name  = row.get("name",  "Guest").strip()
            phone = row.get("phone", "").strip()
            if not phone:
                continue

            normalized = normalize_phone(phone)

            guest = db.query(Guest).filter_by(phone=normalized).first()
            if not guest:
                guest = Guest(name=name, phone=normalized, token=str(uuid.uuid4()))
                db.add(guest)
                db.commit()

            if guest.invited_at:
                log.info("Skipping %s — already invited", name)
                skipped += 1
                continue

            ok = send_sms(normalized, MESSAGE_TEMPLATE.format(message=INVITATION_MESSAGE))
            if ok:
                guest.invited_at = datetime.datetime.utcnow()
                db.commit()
                sent += 1
            else:
                failed += 1

    db.close()
    log.info("Done — sent: %d  skipped: %d  failed: %d", sent, skipped, failed)


if __name__ == "__main__":
    main()
