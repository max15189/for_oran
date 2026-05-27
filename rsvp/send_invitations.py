import csv
import datetime
import logging
import os
import uuid

from dotenv import load_dotenv

from models import Guest, Session
from whatsapp import normalize_phone, send_invitation, upload_image

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

INVITATION_MESSAGE = os.getenv("INVITATION_MESSAGE", "You are invited!")
IMAGE_PATH  = os.path.join(os.path.dirname(__file__), "static", "invitation.png")
GUESTS_CSV  = os.path.join(os.path.dirname(__file__), "guests.csv")


def main():
    media_id = None
    if os.path.exists(IMAGE_PATH):
        log.info("Uploading invitation image...")
        try:
            media_id = upload_image(IMAGE_PATH)
            log.info("Image uploaded — media_id: %s", media_id)
        except Exception as exc:
            log.warning("Image upload failed (%s) — sending text only", exc)

    db = Session()
    with open(GUESTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name  = row.get("name", "Guest").strip()
            phone = row.get("phone", "").strip()
            if not phone:
                continue

            normalized = normalize_phone(phone)

            guest = db.query(Guest).filter_by(phone=normalized).first()
            if not guest:
                guest = Guest(name=name, phone=normalized, token=str(uuid.uuid4()))
                db.add(guest)
                db.commit()

            ok = send_invitation(phone, INVITATION_MESSAGE, media_id)
            if ok:
                guest.invited_at = datetime.datetime.utcnow()
                db.commit()

    db.close()
    log.info("Done.")


if __name__ == "__main__":
    main()
