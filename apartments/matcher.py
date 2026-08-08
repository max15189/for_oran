"""Filter listings against user criteria and sort by date.

Matching is done locally on the normalized ``Listing`` objects, so it behaves
identically no matter which source produced them.
"""

from datetime import datetime, timezone
from typing import Optional

from models import Listing


def _passes_range(value: Optional[float], lo: Optional[float], hi: Optional[float]) -> bool:
    """A value passes if it's within [lo, hi]. Unknown values (None) pass, so a
    missing field never silently excludes a listing on a numeric filter."""
    if value is None:
        return True
    if lo is not None and value < lo:
        return False
    if hi is not None and value > hi:
        return False
    return True


def _matches_any(text: str, needles: list) -> bool:
    """True if the text contains any of the (case-insensitive) needles."""
    if not needles:
        return True
    low = text.lower()
    return any(str(n).lower() in low for n in needles)


def matches(listing: Listing, criteria: dict, notify_unknown_furnished: bool = True) -> bool:
    """Return True if a listing satisfies the search criteria."""
    # Price
    if not _passes_range(listing.price, criteria.get("min_price"), criteria.get("max_price")):
        return False
    # Rooms
    if not _passes_range(listing.rooms, criteria.get("min_rooms"), criteria.get("max_rooms")):
        return False
    # Square meters
    if not _passes_range(listing.sqm, criteria.get("min_sqm"), criteria.get("max_sqm")):
        return False

    # City (substring, case-insensitive). Empty list = accept any.
    cities = criteria.get("cities") or []
    if cities and not _matches_any(listing.city, cities):
        return False

    # Neighborhood (substring). Empty list = accept any.
    neighborhoods = criteria.get("neighborhoods") or []
    if neighborhoods and not _matches_any(listing.neighborhood, neighborhoods):
        return False

    # Furnished
    want_furnished = criteria.get("furnished")
    if want_furnished is not None:
        if listing.furnished is None:
            if not notify_unknown_furnished:
                return False
        elif listing.furnished != want_furnished:
            return False

    # Required keywords: all must appear somewhere in the listing text.
    must_include = criteria.get("must_include") or []
    if must_include:
        low = listing.haystack
        if not all(str(k).lower() in low for k in must_include):
            return False

    # Excluded keywords: none may appear.
    must_exclude = criteria.get("must_exclude") or []
    if must_exclude and _matches_any(listing.haystack, must_exclude):
        return False

    return True


def _sort_key(listing: Listing) -> datetime:
    return listing.posted_at or listing.scraped_at or datetime.min.replace(tzinfo=timezone.utc)


def filter_and_sort(
    listings: list, criteria: dict, notify_unknown_furnished: bool = True
) -> list:
    """Return matching listings, newest first."""
    matched = [l for l in listings if matches(l, criteria, notify_unknown_furnished)]
    return sorted(matched, key=_sort_key, reverse=True)
