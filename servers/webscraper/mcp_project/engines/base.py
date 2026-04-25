"""
Abstract base class for scraping engines.

All engines must implement this interface to be interchangeable.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional


@dataclass
class ScrapeRequest:
    """Parameters for a single scrape operation."""
    url: str
    schema: Optional[dict] = None          # Fields to extract: {"name": "css:.title", ...}
    wait_for: Optional[str] = None         # CSS selector to wait for (JS pages)
    timeout: int = 30                       # Seconds
    headers: Optional[dict] = None
    include_raw_html: bool = False
    crawl_links: bool = False               # Follow links on page
    link_pattern: Optional[str] = None      # Regex to filter links
    max_depth: int = 1                      # Crawl depth
    max_pages: int = 10                     # Max pages to crawl


@dataclass
class ScrapeResult:
    """Result from scraping a single page."""
    url: str
    success: bool
    title: Optional[str] = None
    content: Optional[str] = None           # Markdown or text content
    extracted_data: Optional[dict] = None   # Schema-extracted fields
    links: list = field(default_factory=list)
    raw_html: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    elapsed_ms: Optional[int] = None
    metadata: dict = field(default_factory=dict)


class BaseScrapeEngine(ABC):
    """Abstract scraping engine interface."""

    engine_name: str = "base"
    is_premium: bool = False

    @abstractmethod
    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """Scrape a single URL and return results."""
        ...

    @abstractmethod
    async def scrape_batch(
        self, requests: list[ScrapeRequest], *, on_result=None
    ) -> AsyncIterator[ScrapeResult]:
        """
        Scrape multiple URLs, yielding results as they complete.
        
        Args:
            requests: List of scrape requests.
            on_result: Optional callback(ScrapeResult) for streaming.
        """
        ...

    @abstractmethod
    async def check_available(self) -> tuple[bool, str]:
        """Check if this engine is available and return (available, message)."""
        ...

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search the web for URLs matching a query.
        Returns list of {"url": ..., "title": ..., "snippet": ...}.
        Default implementation raises NotImplementedError.
        """
        raise NotImplementedError(f"{self.engine_name} does not support search")
