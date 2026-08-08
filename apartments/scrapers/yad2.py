"""Yad2 rental scraper.

Queries Yad2's internal rent feed (the ``feed-search-legacy/realestate/rent``
JSON endpoint) with browser-like headers and maps each feed item into a
:class:`~models.Listing`.

Notes / known limitations
-------------------------
* Yad2 filters by NUMERIC location codes (city / area / neighborhood), not
  names. See ``config.example.yaml`` for how to find them.
* Yad2 sits behind PerimeterX bot protection. This scraper uses a realistic
  browser ``User-Agent`` and referer, which is enough for light personal
  polling. If Yad2 starts returning HTML challenge pages instead of JSON, the
  fallback is to fetch through Playwright (Chromium is available in this
  environment) — the parsing below can be reused as-is on the JSON payload.
* The feed's field names drift over time, so every field is read defensively
  with fallbacks and the whole item is kept in ``Listing.raw``.
"""

import logging
import re
from datetime import datetime, timezone

import requests

from models import Listing
from scrapers.base import BaseScraper

log = logging.getLogger(__name__)

FEED_URL = "https://gw.yad2.co.il/feed-search-legacy/realestate/rent"
ITEM_URL = "https://www.yad2.co.il/item/{token}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.yad2.co.il/realestate/rent",
    "Origin": "https://www.yad2.co.il",
}


def _to_number(value):
    """Extract the first number from a value that may be an int, float, or a
    string like '5,500 ₪' or '3.5 חדרים'. Returns None if nothing numeric."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"\d+(?:[.,]\d+)?", str(value).replace(",", ""))
    return float(match.group()) if match else None


def _detect_furnished(text: str):
    """Best-effort furnished detection from Hebrew/English text.

    Returns True / False / None(unknown). Checks the negative form first so
    'לא מרוהט' is not mistaken for 'מרוהט'.
    """
    low = (text or "").lower()
    if "לא מרוהט" in low or "unfurnished" in low:
        return False
    if "מרוהט" in low or "furnished" in low:
        return True
    return None


def _parse_date(item: dict):
    """Try the common Yad2 date fields; return a tz-aware datetime or None."""
    for key in ("date_added", "date", "updated_at", "AdDate"):
        raw = item.get(key)
        if not raw:
            continue
        text = str(raw)
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(text[: len(fmt) + 2], fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _extract_images(item: dict) -> list:
    imgs = item.get("images") or item.get("images_urls") or {}
    if isinstance(imgs, dict):
        # Yad2 sometimes returns {"concat": "url1,url2", "images_urls": [...]}
        if isinstance(imgs.get("images_urls"), list):
            return [u for u in imgs["images_urls"] if u]
        concat = imgs.get("concat")
        if isinstance(concat, str):
            return [u for u in concat.split(",") if u]
    if isinstance(imgs, list):
        return [u for u in imgs if isinstance(u, str)]
    img = item.get("img_url") or item.get("image")
    return [img] if isinstance(img, str) and img else []


class Yad2Scraper(BaseScraper):
    name = "yad2"

    #: Config keys (from the ``yad2:`` block) that map onto feed query params.
    _PARAM_KEYS = ("city", "area", "neighborhood", "property_group", "rooms", "price")

    def __init__(self, config: dict | None = None, max_pages: int = 3):
        super().__init__(config)
        self.max_pages = max_pages

    def _params(self, page: int) -> dict:
        params = {"page": page, "forceLdLoad": "true"}
        for key in self._PARAM_KEYS:
            value = self.config.get(key)
            if value not in (None, "", []):
                params[key] = value
        return params

    def _fetch_page(self, session: requests.Session, page: int) -> list:
        try:
            resp = session.get(FEED_URL, params=self._params(page), timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except ValueError:
            log.warning(
                "Yad2 page %d did not return JSON — likely a bot-protection "
                "challenge. Consider the Playwright fallback (see module docstring).",
                page,
            )
            return []
        except requests.RequestException as exc:
            log.error("Yad2 page %d request failed: %s", page, exc)
            return []

        feed = (data.get("data") or {}).get("feed") or {}
        return feed.get("feed_items") or []

    def _to_listing(self, item: dict):
        # Skip non-listing rows (Yad2 injects ads/banners into the feed).
        if item.get("type") and item.get("type") not in ("ad", "listing", None):
            return None
        source_id = str(
            item.get("id") or item.get("link_token") or item.get("ad_number")
            or item.get("AdNumber") or ""
        ).strip()
        if not source_id:
            return None

        token = item.get("link_token") or item.get("id")
        url = ITEM_URL.format(token=token) if token else "https://www.yad2.co.il/realestate/rent"

        title = " ".join(
            str(item.get(k, "")).strip()
            for k in ("title_1", "title_2")
            if item.get(k)
        ).strip() or str(item.get("title") or item.get("row_1") or "").strip()

        description = str(
            item.get("search_text") or item.get("info_text") or item.get("row_4") or ""
        )

        rooms = _to_number(
            item.get("Rooms_text") or item.get("rooms") or item.get("Rooms")
        )
        sqm = _to_number(
            item.get("square_meters") or item.get("SquareMeter") or item.get("square_meter_build")
        )
        floor = _to_number(item.get("floor") or item.get("Floor_text") or item.get("Floor"))

        text_blob = " ".join(
            str(x) for x in (title, description, item.get("row_2"), item.get("row_3"))
        )

        return Listing(
            source=self.name,
            source_id=source_id,
            url=url,
            title=title,
            price=_to_number(item.get("price") or item.get("Price")),
            currency="ILS",
            city=str(item.get("city") or item.get("City") or "").strip(),
            neighborhood=str(
                item.get("neighborhood") or item.get("Neighborhood") or ""
            ).strip(),
            rooms=rooms,
            sqm=sqm,
            floor=int(floor) if floor is not None else None,
            furnished=_detect_furnished(text_blob),
            description=description,
            image_urls=_extract_images(item),
            posted_at=_parse_date(item),
            lat=_to_number((item.get("coordinates") or {}).get("latitude"))
            if isinstance(item.get("coordinates"), dict) else None,
            lon=_to_number((item.get("coordinates") or {}).get("longitude"))
            if isinstance(item.get("coordinates"), dict) else None,
            raw=item,
        )

    def fetch(self) -> list:
        session = requests.Session()
        session.headers.update(HEADERS)
        listings = []
        seen = set()
        for page in range(1, self.max_pages + 1):
            items = self._fetch_page(session, page)
            if not items:
                break
            new_on_page = 0
            for item in items:
                if not isinstance(item, dict):
                    continue
                listing = self._to_listing(item)
                if listing is None or listing.uid in seen:
                    continue
                seen.add(listing.uid)
                listings.append(listing)
                new_on_page += 1
            if new_on_page == 0:
                break
        log.info("Yad2: collected %d listings", len(listings))
        return listings
