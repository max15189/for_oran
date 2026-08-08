"""Base scraper interface — the plug-in point for every source."""

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Contract every source scraper must implement.

    A scraper is given its own slice of config at construction time and is asked
    to ``fetch`` a list of normalized :class:`~models.Listing` objects. It should
    swallow its own network/parse errors and return whatever it managed to get
    (an empty list on total failure) so one broken source never takes down the
    whole run.
    """

    #: Short, stable identifier used as ``Listing.source`` and in logs.
    name: str = "base"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def fetch(self) -> list:
        """Return a list of :class:`~models.Listing` for this source."""
        raise NotImplementedError
