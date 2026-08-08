"""Scheduled runner: polls every source on an interval and pushes new matches
to WhatsApp. Mirrors the loop style of the root project's whatsapp_sender.py.
"""

import logging
import time

import schedule
from dotenv import load_dotenv

load_dotenv()

import notifier  # noqa: E402  (import after load_dotenv so env is available)
from pipeline import load_config, run_cycle  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("apartments.log"),
    ],
)
log = logging.getLogger(__name__)


def main():
    notifier.validate_env()
    config = load_config()
    poll_minutes = int(config.get("poll_minutes", 15))

    log.info("Apartment scraper started. Polling every %d minute(s).", poll_minutes)

    def cycle():
        try:
            run_cycle(config, notifier=notifier)
        except Exception as exc:  # noqa: BLE001 — keep the scheduler alive
            log.exception("Run cycle failed: %s", exc)

    # Run once immediately, then on the configured interval.
    cycle()
    schedule.every(poll_minutes).minutes.do(cycle)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
