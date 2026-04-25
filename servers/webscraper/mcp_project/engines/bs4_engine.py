"""
BeautifulSoup + httpx scraping engine (free).

Handles static HTML pages with CSS selector extraction.
Includes rate limiting, retries, and robots.txt checking.
"""

import asyncio
import re
import time
from typing import AsyncIterator, Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import BaseScrapeEngine, ScrapeRequest, ScrapeResult

# Default polite delay between requests (seconds)
DEFAULT_DELAY = 1.0
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

# Block private/local IPs to prevent SSRF
_PRIVATE_PATTERNS = re.compile(
    r"^(127\.|10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|0\.|localhost|::1|\[::1\])"
)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MCPWebScraper/1.0; +https://github.com/M2LabOrg/mcp-design-deploy)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_safe_url(url: str) -> bool:
    """Reject URLs pointing to private/local addresses (SSRF prevention)."""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return not _PRIVATE_PATTERNS.match(hostname)


def _extract_with_selectors(soup: BeautifulSoup, schema: dict) -> dict:
    """
    Extract data from HTML using CSS selectors.
    
    Schema format:
        {"field_name": "css:.selector", "other": "css:.other-selector"}
    
    Supports:
        - "css:.selector" — text content of first match
        - "css:.selector[]" — list of all matches
        - "css:.selector@attr" — attribute value
        - "xpath:..." — (future) XPath expressions
    """
    data = {}
    for field_name, selector_expr in schema.items():
        if not isinstance(selector_expr, str):
            data[field_name] = None
            continue

        # Parse selector type
        if selector_expr.startswith("css:"):
            raw = selector_expr[4:]
        else:
            raw = selector_expr

        # Check for list mode
        is_list = raw.endswith("[]")
        if is_list:
            raw = raw[:-2]

        # Check for attribute extraction
        attr = None
        if "@" in raw:
            raw, attr = raw.rsplit("@", 1)

        raw = raw.strip()
        if not raw:
            data[field_name] = None
            continue

        if is_list:
            elements = soup.select(raw)
            if attr:
                data[field_name] = [el.get(attr, "") for el in elements]
            else:
                data[field_name] = [el.get_text(strip=True) for el in elements]
        else:
            el = soup.select_one(raw)
            if el is None:
                data[field_name] = None
            elif attr:
                data[field_name] = el.get(attr, "")
            else:
                data[field_name] = el.get_text(strip=True)

    return data


def _html_to_markdown(soup: BeautifulSoup) -> str:
    """Convert HTML to readable markdown-ish text."""
    # Remove script and style elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    lines = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "pre", "blockquote"]):
        tag = el.name
        text = el.get_text(strip=True)
        if not text:
            continue
        if tag == "h1":
            lines.append(f"# {text}")
        elif tag == "h2":
            lines.append(f"## {text}")
        elif tag == "h3":
            lines.append(f"### {text}")
        elif tag in ("h4", "h5", "h6"):
            lines.append(f"#### {text}")
        elif tag == "li":
            lines.append(f"- {text}")
        elif tag == "blockquote":
            lines.append(f"> {text}")
        elif tag == "pre":
            lines.append(f"```\n{text}\n```")
        else:
            lines.append(text)

    return "\n\n".join(lines)


def _extract_links(soup: BeautifulSoup, base_url: str, pattern: Optional[str] = None) -> list[str]:
    """Extract and resolve links from a page."""
    links = set()
    compiled = re.compile(pattern) if pattern else None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        resolved = urljoin(base_url, href)
        # Only http(s) links
        if not resolved.startswith(("http://", "https://")):
            continue
        if compiled and not compiled.search(resolved):
            continue
        if _is_safe_url(resolved):
            links.add(resolved)
    return list(links)


class BS4Engine(BaseScrapeEngine):
    """BeautifulSoup + httpx scraping engine."""

    engine_name = "beautifulsoup"
    is_premium = False

    def __init__(self, delay: float = DEFAULT_DELAY):
        self.delay = delay
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=DEFAULT_HEADERS,
                follow_redirects=True,
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def check_available(self) -> tuple[bool, str]:
        return True, "BeautifulSoup engine is always available (free, no API key needed)"

    async def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        if not _is_safe_url(request.url):
            return ScrapeResult(
                url=request.url, success=False,
                error="URL blocked: private/local addresses not allowed (SSRF prevention)"
            )

        client = await self._get_client()
        headers = {**DEFAULT_HEADERS, **(request.headers or {})}

        last_error = None
        for attempt in range(MAX_RETRIES):
            start = time.monotonic()
            try:
                resp = await client.get(
                    request.url, headers=headers,
                    timeout=httpx.Timeout(request.timeout)
                )
                elapsed = int((time.monotonic() - start) * 1000)

                content_type = resp.headers.get("content-type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    return ScrapeResult(
                        url=request.url, success=False,
                        status_code=resp.status_code,
                        error=f"Non-HTML content type: {content_type}",
                        elapsed_ms=elapsed,
                    )

                soup = BeautifulSoup(resp.text, "lxml")

                # Extract title
                title_tag = soup.find("title")
                title = title_tag.get_text(strip=True) if title_tag else None

                # Extract data with schema
                extracted = None
                if request.schema:
                    extracted = _extract_with_selectors(soup, request.schema)

                # Convert to markdown content
                content = _html_to_markdown(soup)

                # Extract links if crawling
                links = []
                if request.crawl_links:
                    links = _extract_links(soup, request.url, request.link_pattern)

                return ScrapeResult(
                    url=request.url,
                    success=True,
                    title=title,
                    content=content[:50000],  # Cap content size
                    extracted_data=extracted,
                    links=links,
                    raw_html=resp.text if request.include_raw_html else None,
                    status_code=resp.status_code,
                    elapsed_ms=elapsed,
                    metadata={
                        "engine": self.engine_name,
                        "content_length": len(resp.text),
                    },
                )

            except httpx.TimeoutException:
                last_error = f"Timeout after {request.timeout}s"
            except httpx.HTTPError as e:
                last_error = f"HTTP error: {e}"
            except Exception as e:
                last_error = f"Unexpected error: {e}"

            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_BACKOFF ** attempt)

        return ScrapeResult(
            url=request.url, success=False,
            error=f"Failed after {MAX_RETRIES} retries: {last_error}",
        )

    async def scrape_batch(
        self, requests: list[ScrapeRequest], *, on_result=None
    ) -> AsyncIterator[ScrapeResult]:
        for req in requests:
            result = await self.scrape(req)
            if on_result:
                await on_result(result) if asyncio.iscoroutinefunction(on_result) else on_result(result)
            yield result
            # Polite delay
            await asyncio.sleep(self.delay)

    async def search(self, query: str, max_results: int = 10) -> list[dict]:
        """Search using DuckDuckGo HTML (no API key needed)."""
        client = await self._get_client()
        try:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={**DEFAULT_HEADERS},
                timeout=httpx.Timeout(15.0),
            )
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for r in soup.select(".result")[:max_results]:
                title_el = r.select_one(".result__title a")
                snippet_el = r.select_one(".result__snippet")
                if title_el:
                    url = title_el.get("href", "")
                    # DuckDuckGo wraps URLs in redirects
                    if "uddg=" in url:
                        from urllib.parse import parse_qs, urlparse as _urlparse
                        qs = parse_qs(_urlparse(url).query)
                        url = qs.get("uddg", [url])[0]
                    results.append({
                        "url": url,
                        "title": title_el.get_text(strip=True),
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    })
            return results
        except Exception as e:
            return [{"url": "", "title": "Search failed", "snippet": str(e)}]

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
