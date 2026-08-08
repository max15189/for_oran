"""Shared pipeline logic used by both the scheduler and the one-shot CLI."""

import logging
import os

import yaml

import db
from matcher import filter_and_sort
from scrapers import build_scrapers

log = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def load_config(path: str = CONFIG_PATH) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Config file not found: {path}\n"
            "Copy config.example.yaml to config.yaml and edit your criteria."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def scrape_all(config: dict) -> list:
    """Run every enabled scraper and return the combined list of listings."""
    all_listings = []
    for scraper in build_scrapers(config):
        try:
            all_listings.extend(scraper.fetch())
        except Exception as exc:  # noqa: BLE001 — never let one source kill the run
            log.exception("Scraper '%s' failed: %s", getattr(scraper, "name", "?"), exc)
    return all_listings


def find_matches(config: dict) -> list:
    """Scrape all sources and return matching listings, newest first."""
    listings = scrape_all(config)
    criteria = config.get("search") or {}
    notify_unknown = config.get("notify_unknown_furnished", True)
    matches = filter_and_sort(listings, criteria, notify_unknown)
    log.info("Matched %d of %d scraped listings", len(matches), len(listings))
    return matches


def run_cycle(config: dict, notifier=None, dry_run: bool = False) -> list:
    """One full cycle: scrape -> store -> notify new matches.

    Returns the list of listings that were newly matched this cycle. When
    ``dry_run`` is True nothing is written to the DB and nothing is sent.
    """
    matches = find_matches(config)

    if dry_run:
        return matches

    db.init_db()
    newly_notified = []
    for listing in matches:
        is_new = db.upsert_listing(listing)
        if is_new:
            if notifier is not None and notifier.notify(listing):
                db.mark_notified(listing.uid)
            newly_notified.append(listing)
    log.info("Cycle complete: %d new matching listings", len(newly_notified))
    return newly_notified
