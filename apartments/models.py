"""Normalized listing schema shared by every scraper."""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Listing:
    """A single rental listing, normalized across all sources.

    Every scraper is responsible for mapping its raw payload into this shape so
    the rest of the pipeline (dedup, matching, notifying) is source-agnostic.
    """

    source: str                 # e.g. "yad2"
    source_id: str              # stable id within that source
    url: str
    title: str = ""
    price: Optional[float] = None
    currency: str = "ILS"
    city: str = ""
    neighborhood: str = ""
    rooms: Optional[float] = None
    sqm: Optional[float] = None
    floor: Optional[int] = None
    furnished: Optional[bool] = None       # None = unknown / not stated
    description: str = ""
    image_urls: list = field(default_factory=list)
    posted_at: Optional[datetime] = None
    scraped_at: datetime = field(default_factory=_now)
    lat: Optional[float] = None
    lon: Optional[float] = None
    raw: dict = field(default_factory=dict)

    @property
    def uid(self) -> str:
        """Stable, globally-unique key used for deduplication."""
        return f"{self.source}:{self.source_id}"

    @property
    def haystack(self) -> str:
        """Lower-cased text blob used for keyword matching."""
        return " ".join(
            str(x) for x in (self.title, self.description, self.neighborhood, self.city)
        ).lower()

    def to_row(self) -> dict:
        """Flatten into a dict suitable for the SQLite layer."""
        row = asdict(self)
        row["image_urls"] = json.dumps(self.image_urls, ensure_ascii=False)
        row["raw"] = json.dumps(self.raw, ensure_ascii=False, default=str)
        row["posted_at"] = self.posted_at.isoformat() if self.posted_at else None
        row["scraped_at"] = self.scraped_at.isoformat() if self.scraped_at else None
        row["uid"] = self.uid
        return row
