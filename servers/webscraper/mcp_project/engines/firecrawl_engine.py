"""
Firecrawl scraping engine (premium).

Uses the Firecrawl API for JavaScript rendering, anti-bot bypass,
and AI-powered structured extraction.
"""

import asyncio
import os
import time
from typing import AsyncIterator, Optional

from .base import BaseScrapeEngine, ScrapeRequest, ScrapeResult

# Firecrawl SDK import — optional at module level
try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False


class FirecrawlEngine(BaseScrapeEngine):
    """Firecrawl API scraping engine."""

    engine_name = "firecrawl"
    is_premium = True

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ.get("FIRECRAWL_API_KEY", "")
        self._app: Optional[object] = None

    def _get_app(self):
        if not FIRECRAWL_AVAILABLE:
            raise RuntimeError(
                "firecrawl-py package not installed. Run: pip install firecrawl-py"
            )
        if not self._api_key:
            raise RuntimeError(
                "Firecrawl API key not configured. Set FIRECRAWL_API_KEY or provide via UI."
            )
        if self._app is None:
            self._app = FirecrawlApp(api_key=self._api_key)
        return self._app

    def set_api_key(self, api_key: str):
        """Update the API key (e.g., from user configuration)."""
        self._api_key = api_key
        self._app = None  # Reset to pick up new key

    async def check_available(self) -> tuple[bool, str]:
        if not FIRECRAWL_AVAILABLE:
            return False, "firecrawl-py package not installed"
        if not self._api_key:
            return False, "No Firecrawl API key configured"
        # Test with a lightweight call
        try:
            app = self._get_app()
            # Scrape a minimal page to validate the key
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: app.scrape_url("https://example.com", params={"formats": ["markdown"]}),
            )
            if result:
                return True, "Firecrawl API key is valid and working"
            return False, "Firecrawl returned empty response"
        except Exception as e:
            return False, f"Firecrawl error: {e}"

    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        start = time.monotonic()
        try:
            app = self._get_app()

            params = {"formats": ["markdown"]}

            # Add extract schema if provided
            if request.schema:
                params["formats"].append("extract")
                params["extract"] = {"schema": request.schema}

            if request.include_raw_html:
                params["formats"].append("html")

            if request.wait_for:
                params["waitFor"] = request.wait_for

            if request.timeout:
                params["timeout"] = request.timeout * 1000  # ms

            # Run in executor since firecrawl SDK is synchronous
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: app.scrape_url(request.url, params=params),
            )

            elapsed = int((time.monotonic() - start) * 1000)

            if not result:
                return ScrapeResult(
                    url=request.url, success=False,
                    error="Firecrawl returned empty response",
                    elapsed_ms=elapsed,
                )

            # Extract data from Firecrawl response
            metadata = result.get("metadata", {})
            content = result.get("markdown", "")
            extracted = result.get("extract", None)
            raw_html = result.get("html", None) if request.include_raw_html else None
            title = metadata.get("title", "")
            status_code = metadata.get("statusCode", 200)

            # Extract links if crawling requested
            links = []
            if request.crawl_links and "links" in result:
                links = result["links"]

            return ScrapeResult(
                url=request.url,
                success=True,
                title=title,
                content=content[:50000],
                extracted_data=extracted,
                links=links,
                raw_html=raw_html,
                status_code=status_code,
                elapsed_ms=elapsed,
                metadata={
                    "engine": self.engine_name,
                    "source_url": metadata.get("sourceURL", request.url),
                    "language": metadata.get("language", ""),
                },
            )

        except Exception as e:
            elapsed = int((time.monotonic() - start) * 1000)
            return ScrapeResult(
                url=request.url, success=False,
                error=str(e), elapsed_ms=elapsed,
            )

    async def scrape_batch(
        self, requests: list[ScrapeRequest], *, on_result=None
    ) -> AsyncIterator[ScrapeResult]:
        for req in requests:
            result = await self.scrape(req)
            if on_result:
                await on_result(result) if asyncio.iscoroutinefunction(on_result) else on_result(result)
            yield result
            # Firecrawl has its own rate limiting, small delay for safety
            await asyncio.sleep(0.5)

    async def crawl_site(
        self,
        url: str,
        max_pages: int = 10,
        include_pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        on_result=None,
    ) -> list[ScrapeResult]:
        """Use Firecrawl's crawl endpoint for multi-page crawling."""
        try:
            app = self._get_app()

            params = {
                "limit": max_pages,
                "scrapeOptions": {"formats": ["markdown"]},
            }
            if include_pattern:
                params["includePaths"] = [include_pattern]
            if exclude_pattern:
                params["excludePaths"] = [exclude_pattern]

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: app.crawl_url(url, params=params, poll_interval=2),
            )

            results = []
            pages = result.get("data", []) if isinstance(result, dict) else []
            for page in pages:
                sr = ScrapeResult(
                    url=page.get("metadata", {}).get("sourceURL", url),
                    success=True,
                    title=page.get("metadata", {}).get("title", ""),
                    content=page.get("markdown", "")[:50000],
                    metadata={"engine": self.engine_name},
                )
                results.append(sr)
                if on_result:
                    await on_result(sr) if asyncio.iscoroutinefunction(on_result) else on_result(sr)

            return results

        except Exception as e:
            return [ScrapeResult(url=url, success=False, error=str(e))]

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Use Firecrawl's search endpoint."""
        try:
            app = self._get_app()
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: app.search(query, params={"limit": max_results}),
            )
            results = []
            data = result.get("data", []) if isinstance(result, dict) else result if isinstance(result, list) else []
            for item in data:
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("description", item.get("markdown", ""))[:200],
                })
            return results
        except Exception as e:
            return [{"url": "", "title": "Search failed", "snippet": str(e)}]

    async def close(self):
        pass  # Firecrawl SDK doesn't need cleanup
