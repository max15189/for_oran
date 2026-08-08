"""One-shot CLI for testing.

    python run_once.py --dry-run   # scrape + filter + print, no DB, no WhatsApp
    python run_once.py             # full cycle: store to DB and send WhatsApp
    python run_once.py --limit 5   # cap how many are printed

Use --dry-run first to confirm scraping and filtering before wiring up sends.
"""

import argparse
import logging

from dotenv import load_dotenv

load_dotenv()

import notifier  # noqa: E402
from pipeline import load_config, run_cycle  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)


def _print_listing(listing, index: int) -> None:
    posted = listing.posted_at.strftime("%Y-%m-%d %H:%M") if listing.posted_at else "?"
    price = f"{listing.price:,.0f} {listing.currency}" if listing.price else "?"
    rooms = f"{listing.rooms:g}" if listing.rooms is not None else "?"
    sqm = f"{listing.sqm:g}" if listing.sqm is not None else "?"
    furn = {True: "furnished", False: "unfurnished", None: "furnished?"}[listing.furnished]
    location = " / ".join(p for p in (listing.city, listing.neighborhood) if p) or "?"
    print(f"\n[{index}] {listing.title or '(no title)'}")
    print(f"    {price} | {rooms} rooms | {sqm} sqm | {furn} | {location}")
    print(f"    posted {posted} | {listing.url}")


def main():
    parser = argparse.ArgumentParser(description="Run the apartment scraper once.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scrape, filter and print only. No DB writes, no WhatsApp messages.",
    )
    parser.add_argument(
        "--limit", type=int, default=20, help="Max listings to print (default 20).",
    )
    args = parser.parse_args()

    config = load_config()

    if args.dry_run:
        results = run_cycle(config, notifier=None, dry_run=True)
        print(f"\n=== DRY RUN: {len(results)} matching listing(s) ===")
    else:
        notifier.validate_env()
        results = run_cycle(config, notifier=notifier, dry_run=False)
        print(f"\n=== {len(results)} NEW matching listing(s) notified ===")

    for i, listing in enumerate(results[: args.limit], start=1):
        _print_listing(listing, i)

    if len(results) > args.limit:
        print(f"\n… and {len(results) - args.limit} more.")


if __name__ == "__main__":
    main()
