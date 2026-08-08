"""Scraper plug-ins.

Each source is a subclass of ``BaseScraper``. Register new scrapers in
``build_scrapers`` so the orchestrator picks them up automatically.
"""

from .base import BaseScraper
from .yad2 import Yad2Scraper


def build_scrapers(config: dict) -> list:
    """Return the list of enabled scrapers based on config.

    Adding a new source (e.g. Facebook) later means importing it and appending
    one line here — nothing else in the pipeline changes.
    """
    scrapers = [Yad2Scraper(config.get("yad2") or {})]
    return scrapers


__all__ = ["BaseScraper", "Yad2Scraper", "build_scrapers"]
