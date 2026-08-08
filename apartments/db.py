"""SQLite storage for listings: dedup, new-vs-seen tracking, notify flag.

Uses only the stdlib ``sqlite3`` so there is no extra dependency. The database
file lives next to this module (``listings.db``) and is gitignored.
"""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from models import Listing

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "listings.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    uid          TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    source_id    TEXT NOT NULL,
    url          TEXT,
    title        TEXT,
    price        REAL,
    currency     TEXT,
    city         TEXT,
    neighborhood TEXT,
    rooms        REAL,
    sqm          REAL,
    floor        INTEGER,
    furnished    INTEGER,          -- 1 / 0 / NULL(unknown)
    description  TEXT,
    image_urls   TEXT,             -- JSON array
    posted_at    TEXT,             -- ISO8601
    scraped_at   TEXT,             -- ISO8601
    first_seen   TEXT,             -- ISO8601, when WE first stored it
    lat          REAL,
    lon          REAL,
    raw          TEXT,             -- JSON
    notified     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_listings_posted_at ON listings(posted_at);
CREATE INDEX IF NOT EXISTS idx_listings_notified ON listings(notified);
"""


def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)


def _furnished_to_db(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


def upsert_listing(listing: Listing, db_path: str = DB_PATH) -> bool:
    """Insert a listing if unseen, or refresh mutable fields if seen.

    Returns True if this listing was NOT in the database before (i.e. it is
    genuinely new to us), False otherwise. The ``notified`` flag is never reset
    on update, so an already-notified listing won't be re-sent.
    """
    row = listing.to_row()
    now_iso = datetime.now(timezone.utc).isoformat()
    with _connect(db_path) as conn:
        existing = conn.execute(
            "SELECT uid FROM listings WHERE uid = ?", (row["uid"],)
        ).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO listings (
                    uid, source, source_id, url, title, price, currency, city,
                    neighborhood, rooms, sqm, floor, furnished, description,
                    image_urls, posted_at, scraped_at, first_seen, lat, lon, raw
                ) VALUES (
                    :uid, :source, :source_id, :url, :title, :price, :currency, :city,
                    :neighborhood, :rooms, :sqm, :floor, :furnished, :description,
                    :image_urls, :posted_at, :scraped_at, :first_seen, :lat, :lon, :raw
                )
                """,
                {**row, "furnished": _furnished_to_db(listing.furnished), "first_seen": now_iso},
            )
            return True
        # Seen before: refresh fields that may change (price, description, etc.)
        conn.execute(
            """
            UPDATE listings SET
                url = :url, title = :title, price = :price, currency = :currency,
                city = :city, neighborhood = :neighborhood, rooms = :rooms,
                sqm = :sqm, floor = :floor, furnished = :furnished,
                description = :description, image_urls = :image_urls,
                posted_at = :posted_at, scraped_at = :scraped_at,
                lat = :lat, lon = :lon, raw = :raw
            WHERE uid = :uid
            """,
            {**row, "furnished": _furnished_to_db(listing.furnished)},
        )
        return False


def mark_notified(uid: str, db_path: str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.execute("UPDATE listings SET notified = 1 WHERE uid = ?", (uid,))


def get_unnotified(db_path: str = DB_PATH) -> list:
    """Return rows that have not been notified yet, newest first."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM listings WHERE notified = 0 "
            "ORDER BY COALESCE(posted_at, first_seen) DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def list_recent(limit: int = 50, db_path: str = DB_PATH) -> list:
    """Return the most recent listings by post date, for browsing."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM listings "
            "ORDER BY COALESCE(posted_at, first_seen) DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def count(db_path: str = DB_PATH) -> int:
    with _connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM listings").fetchone()["c"]
