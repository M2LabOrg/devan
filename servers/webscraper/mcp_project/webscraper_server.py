"""
MCP Server for Intelligent Web Scraping

Provides tools for:
- Web search and URL discovery
- Single-page and batch scraping (Firecrawl premium or BeautifulSoup free)
- Structured data extraction with CSS selectors or AI schemas
- Job management: create, pause, resume, stop, restart
- CRUD operations on scraped data
- Export to JSON, CSV, Excel, SQLite, Markdown

Engine selection:
- Firecrawl: JS rendering, anti-bot, AI extraction (requires API key)
- BeautifulSoup: Free, static HTML, CSS selectors
"""

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from engines.base import ScrapeRequest, ScrapeResult
from engines.bs4_engine import BS4Engine
from engines.firecrawl_engine import FirecrawlEngine
from exporters import EXPORT_FORMATS, export_results
from job_manager import JobManager, JobStatus, ScrapeJob

# ── Initialize ──
mcp = FastMCP("webscraper")

# Default storage for jobs when no project path is specified
DEFAULT_STORAGE = os.environ.get("SCRAPE_STORAGE", "scrape_jobs")

# Engine instances
_bs4_engine = BS4Engine()
_firecrawl_engine = FirecrawlEngine()
_job_manager = JobManager(DEFAULT_STORAGE)


def _get_engine(name: str = "beautifulsoup"):
    if name == "firecrawl":
        return _firecrawl_engine
    return _bs4_engine


# ═══════════════════════════════════════════
#  DISCOVERY & PLANNING TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def search_urls(query: str, engine: str = "beautifulsoup", max_results: int = 10) -> str:
    """
    Search the web for URLs matching a query.
    
    Args:
        query: Search query (e.g., "renewable energy companies Norway")
        engine: "beautifulsoup" (free, DuckDuckGo) or "firecrawl" (premium)
        max_results: Maximum results to return (default 10)
    
    Returns:
        JSON list of {url, title, snippet} results.
    """
    eng = _get_engine(engine)
    try:
        results = await eng.search(query, max_results=max_results)
        return json.dumps({
            "engine": engine,
            "query": query,
            "results": results,
            "count": len(results),
        }, indent=2)
    except NotImplementedError:
        return json.dumps({"error": f"Search not supported by {engine} engine"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def analyze_page(url: str) -> str:
    """
    Preview a page's structure before scraping. Returns title, headings,
    detected data patterns, and available links.
    
    Args:
        url: The page URL to analyze.
    
    Returns:
        JSON analysis of the page structure.
    """
    result = await _bs4_engine.scrape(ScrapeRequest(
        url=url, crawl_links=True, include_raw_html=False
    ))
    if not result.success:
        return json.dumps({"error": result.error, "url": url})

    # Parse structure from content
    from bs4 import BeautifulSoup
    import httpx
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "lxml")

    # Detect tables
    tables = []
    for i, table in enumerate(soup.find_all("table")):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        row_count = len(table.find_all("tr"))
        tables.append({"index": i, "headers": headers[:10], "rows": row_count})

    # Detect lists
    lists = []
    for ul in soup.find_all(["ul", "ol"]):
        items = [li.get_text(strip=True)[:80] for li in ul.find_all("li", recursive=False)]
        if len(items) >= 3:
            lists.append({"items_count": len(items), "sample": items[:3]})

    # Detect forms
    forms = []
    for form in soup.find_all("form"):
        inputs = [inp.get("name", inp.get("id", "unnamed")) for inp in form.find_all("input")]
        forms.append({"action": form.get("action", ""), "inputs": inputs[:10]})

    # Headings
    headings = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        headings.append({"level": h.name, "text": h.get_text(strip=True)[:100]})

    return json.dumps({
        "url": url,
        "title": result.title,
        "headings": headings[:20],
        "tables": tables[:10],
        "lists": lists[:10],
        "forms": forms[:5],
        "links_count": len(result.links),
        "sample_links": result.links[:10],
        "content_preview": (result.content or "")[:500],
    }, indent=2)


@mcp.tool()
async def suggest_schema(url: str) -> str:
    """
    Analyze a page and suggest extraction schema (CSS selectors for key data).
    
    Args:
        url: URL to analyze.
    
    Returns:
        JSON with suggested extraction fields and selectors.
    """
    import httpx
    from bs4 import BeautifulSoup

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)
        soup = BeautifulSoup(resp.text, "lxml")

    suggestions = {}

    # Title
    title_el = soup.find("title")
    if title_el:
        suggestions["page_title"] = "css:title"

    # Main headings
    h1 = soup.find("h1")
    if h1:
        class_str = ".".join(h1.get("class", [])) if h1.get("class") else ""
        selector = f"css:h1.{class_str}" if class_str else "css:h1"
        suggestions["main_heading"] = selector

    # Tables — suggest column extraction
    tables = soup.find_all("table")
    if tables:
        for i, table in enumerate(tables[:3]):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            if headers:
                for j, h in enumerate(headers[:5]):
                    safe_name = h.lower().replace(" ", "_").replace("/", "_")[:30]
                    suggestions[f"table{i}_{safe_name}"] = f"css:table:nth-of-type({i+1}) td:nth-of-type({j+1})[]"

    # Repeated items (likely data lists)
    for parent in soup.find_all(["ul", "ol", "div"]):
        children = parent.find_all(recursive=False)
        if len(children) >= 5:
            child_tag = children[0].name
            child_classes = children[0].get("class", [])
            if child_classes:
                sel = f"css:{child_tag}.{'.'.join(child_classes)}"
                suggestions["repeated_items"] = f"{sel}[]"
                break

    # Links
    suggestions["all_links"] = "css:a@href[]"

    # Meta description
    meta = soup.find("meta", attrs={"name": "description"})
    if meta:
        suggestions["meta_description"] = "css:meta[name='description']@content"

    return json.dumps({
        "url": url,
        "suggested_schema": suggestions,
        "note": "Modify selectors as needed. Use [] for lists, @attr for attributes.",
    }, indent=2)


# ═══════════════════════════════════════════
#  SCRAPING TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def scrape_url(
    url: str,
    engine: str = "beautifulsoup",
    schema: Optional[str] = None,
    include_raw_html: bool = False,
) -> str:
    """
    Scrape a single URL and extract data.
    
    Args:
        url: The URL to scrape.
        engine: "beautifulsoup" (free) or "firecrawl" (premium, JS support).
        schema: JSON string of extraction schema, e.g. '{"title": "css:h1", "prices": "css:.price[]"}'
        include_raw_html: Whether to include the raw HTML in results.
    
    Returns:
        JSON with scraped content and extracted data.
    """
    parsed_schema = None
    if schema:
        try:
            parsed_schema = json.loads(schema)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid schema JSON: {schema}"})

    eng = _get_engine(engine)
    request = ScrapeRequest(
        url=url,
        schema=parsed_schema,
        include_raw_html=include_raw_html,
    )
    result = await eng.scrape(request)

    return json.dumps({
        "url": result.url,
        "success": result.success,
        "title": result.title,
        "content_preview": (result.content or "")[:2000],
        "extracted_data": result.extracted_data,
        "status_code": result.status_code,
        "elapsed_ms": result.elapsed_ms,
        "error": result.error,
        "engine": engine,
    }, indent=2, default=str)


@mcp.tool()
async def scrape_batch(
    urls: str,
    engine: str = "beautifulsoup",
    schema: Optional[str] = None,
    job_name: str = "",
    project_path: Optional[str] = None,
) -> str:
    """
    Start a batch scraping job for multiple URLs. Results stream progressively.
    
    Args:
        urls: JSON array of URLs, e.g. '["https://example.com", "https://other.com"]'
        engine: "beautifulsoup" (free) or "firecrawl" (premium).
        schema: JSON extraction schema (applied to all URLs).
        job_name: Human-readable name for this job.
        project_path: Project folder path (for output storage).
    
    Returns:
        JSON with job_id and status. Use get_job_status to track progress.
    """
    try:
        url_list = json.loads(urls)
    except json.JSONDecodeError:
        return json.dumps({"error": "urls must be a valid JSON array of strings"})

    if not isinstance(url_list, list) or not url_list:
        return json.dumps({"error": "urls must be a non-empty list"})

    parsed_schema = None
    if schema:
        try:
            parsed_schema = json.loads(schema)
        except json.JSONDecodeError:
            return json.dumps({"error": f"Invalid schema JSON"})

    # Create job
    job = _job_manager.create_job(
        urls=url_list,
        name=job_name,
        engine=engine,
        schema=parsed_schema,
        project_path=project_path,
    )

    # Run scraping in background
    asyncio.create_task(_run_batch_job(job.job_id))

    return json.dumps({
        "job_id": job.job_id,
        "name": job.name,
        "status": job.status.value,
        "total_urls": len(url_list),
        "engine": engine,
        "message": f"Job started. Use get_job_status('{job.job_id}') to track progress.",
    }, indent=2)


async def _run_batch_job(job_id: str):
    """Background task that executes a batch scraping job."""
    job = _job_manager.get_job(job_id)
    if not job:
        return

    _job_manager.mark_running(job_id)
    engine = _get_engine(job.config.engine)
    start_index = job.checkpoint.last_url_index + 1

    try:
        for i, url in enumerate(job.config.urls[start_index:], start=start_index):
            # Check stop flag
            if _job_manager.is_stopped(job_id):
                break

            # Wait if paused
            await _job_manager.wait_if_paused(job_id)
            if _job_manager.is_stopped(job_id):
                break

            # Skip already completed URLs
            if url in job.checkpoint.completed_urls:
                job.progress.skipped += 1
                continue

            # Scrape
            request = ScrapeRequest(url=url, schema=job.config.schema)
            result = await engine.scrape(request)

            # Store result
            record = {
                "index": i,
                "url": result.url,
                "success": result.success,
                "title": result.title,
                "content_preview": (result.content or "")[:1000],
                "extracted_data": result.extracted_data,
                "status_code": result.status_code,
                "elapsed_ms": result.elapsed_ms,
                "error": result.error,
                "scraped_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
            }
            _job_manager.append_result(job_id, record)

            # Update progress
            if result.success:
                job.progress.completed += 1
            else:
                job.progress.failed += 1
                job.progress.failed_urls.append({"url": url, "error": result.error})

            _job_manager.update_checkpoint(job_id, i, url)

        # Mark complete if not stopped
        if not _job_manager.is_stopped(job_id):
            _job_manager.mark_complete(job_id)

    except Exception as e:
        _job_manager.mark_failed(job_id, str(e))


@mcp.tool()
async def crawl_site(
    url: str,
    engine: str = "firecrawl",
    max_pages: int = 10,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    job_name: str = "",
    project_path: Optional[str] = None,
) -> str:
    """
    Crawl a website following links, extracting content from multiple pages.
    
    Args:
        url: Starting URL for the crawl.
        engine: "firecrawl" recommended for crawling. "beautifulsoup" for simple sites.
        max_pages: Maximum pages to crawl (cost control).
        include_pattern: Regex pattern for URLs to include.
        exclude_pattern: Regex pattern for URLs to exclude.
        job_name: Human-readable name.
        project_path: Project folder path.
    
    Returns:
        JSON with job details. Use get_job_status to track.
    """
    # For BS4, we do a simple breadth-first crawl
    # For Firecrawl, use their crawl API

    job = _job_manager.create_job(
        urls=[url],
        name=job_name or f"Crawl: {url}",
        engine=engine,
        project_path=project_path,
        crawl_links=True,
        link_pattern=include_pattern,
        max_pages=max_pages,
    )

    asyncio.create_task(_run_crawl_job(job.job_id, max_pages, include_pattern, exclude_pattern))

    return json.dumps({
        "job_id": job.job_id,
        "name": job.name,
        "status": "running",
        "start_url": url,
        "max_pages": max_pages,
        "engine": engine,
    }, indent=2)


async def _run_crawl_job(job_id: str, max_pages: int, include_pattern, exclude_pattern):
    """Background crawl execution."""
    job = _job_manager.get_job(job_id)
    if not job:
        return

    _job_manager.mark_running(job_id)

    try:
        if job.config.engine == "firecrawl":
            results = await _firecrawl_engine.crawl_site(
                job.config.urls[0],
                max_pages=max_pages,
                include_pattern=include_pattern,
                exclude_pattern=exclude_pattern,
            )
            for r in results:
                record = {
                    "url": r.url,
                    "success": r.success,
                    "title": r.title,
                    "content_preview": (r.content or "")[:1000],
                    "error": r.error,
                }
                _job_manager.append_result(job_id, record)
                if r.success:
                    job.progress.completed += 1
                else:
                    job.progress.failed += 1
        else:
            # BS4 breadth-first crawl
            visited = set()
            queue = [job.config.urls[0]]
            pages_scraped = 0

            while queue and pages_scraped < max_pages:
                if _job_manager.is_stopped(job_id):
                    break
                await _job_manager.wait_if_paused(job_id)

                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)

                result = await _bs4_engine.scrape(ScrapeRequest(
                    url=url, schema=job.config.schema,
                    crawl_links=True, link_pattern=include_pattern,
                ))

                record = {
                    "url": result.url,
                    "success": result.success,
                    "title": result.title,
                    "content_preview": (result.content or "")[:1000],
                    "extracted_data": result.extracted_data,
                    "error": result.error,
                }
                _job_manager.append_result(job_id, record)

                if result.success:
                    job.progress.completed += 1
                    # Add discovered links to queue
                    for link in result.links:
                        if link not in visited:
                            queue.append(link)
                else:
                    job.progress.failed += 1

                pages_scraped += 1
                job.progress.total_urls = pages_scraped + len(queue)
                _job_manager.update_checkpoint(job_id, pages_scraped, url)

                await asyncio.sleep(_bs4_engine.delay)

        if not _job_manager.is_stopped(job_id):
            _job_manager.mark_complete(job_id)

    except Exception as e:
        _job_manager.mark_failed(job_id, str(e))


# ═══════════════════════════════════════════
#  JOB MANAGEMENT TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def list_jobs(project_path: Optional[str] = None) -> str:
    """
    List all scraping jobs with their current status.
    
    Args:
        project_path: Filter by project folder (optional).
    
    Returns:
        JSON list of jobs with id, name, status, progress.
    """
    jobs = _job_manager.list_jobs(project_path=project_path)
    return json.dumps({"jobs": jobs, "count": len(jobs)}, indent=2)


@mcp.tool()
async def get_job_status(job_id: str) -> str:
    """
    Get detailed status and progress of a scraping job.
    
    Args:
        job_id: The job identifier.
    
    Returns:
        JSON with full job details including progress and checkpoint.
    """
    job = _job_manager.get_job(job_id)
    if not job:
        return json.dumps({"error": f"Job not found: {job_id}"})
    return json.dumps(job.to_dict(), indent=2)


@mcp.tool()
async def pause_job(job_id: str) -> str:
    """
    Pause a running scraping job. Can be resumed later.
    
    Args:
        job_id: The job to pause.
    """
    success = _job_manager.pause_job(job_id)
    if success:
        return json.dumps({"status": "paused", "job_id": job_id, "message": "Job paused. Use resume_job to continue."})
    return json.dumps({"error": "Cannot pause job (not running or not found)"})


@mcp.tool()
async def resume_job(job_id: str) -> str:
    """
    Resume a paused or failed scraping job from where it stopped.
    
    Args:
        job_id: The job to resume.
    """
    job = _job_manager.get_job(job_id)
    if not job:
        return json.dumps({"error": f"Job not found: {job_id}"})

    if job.status not in (JobStatus.PAUSED, JobStatus.FAILED):
        return json.dumps({"error": f"Cannot resume job with status: {job.status.value}"})

    _job_manager.resume_job(job_id)

    # Restart the background task
    asyncio.create_task(_run_batch_job(job_id))

    return json.dumps({
        "status": "running",
        "job_id": job_id,
        "resumed_from": job.checkpoint.last_url_index + 1,
        "remaining": job.progress.total_urls - job.progress.completed - job.progress.failed,
    })


@mcp.tool()
async def cancel_job(job_id: str) -> str:
    """
    Stop a running or paused job. Partial results are kept.
    
    Args:
        job_id: The job to cancel.
    """
    success = _job_manager.stop_job(job_id)
    if success:
        return json.dumps({"status": "stopped", "job_id": job_id, "message": "Job stopped. Partial results preserved."})
    return json.dumps({"error": "Cannot stop job (not running/paused or not found)"})


@mcp.tool()
async def delete_job(job_id: str) -> str:
    """
    Delete a job and all its data permanently.
    
    Args:
        job_id: The job to delete.
    """
    success = _job_manager.delete_job(job_id)
    if success:
        return json.dumps({"status": "deleted", "job_id": job_id})
    return json.dumps({"error": f"Job not found: {job_id}"})


# ═══════════════════════════════════════════
#  DATA / CRUD TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def get_results(
    job_id: str,
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
) -> str:
    """
    Get scraped results for a job (paginated).
    
    Args:
        job_id: The job identifier.
        page: Page number (1-based).
        page_size: Results per page.
        search: Full-text search filter.
    
    Returns:
        JSON with results array, total count, pagination info.
    """
    data = _job_manager.get_results(job_id, page=page, page_size=page_size, search=search)
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def update_record(job_id: str, record_index: int, updates: str) -> str:
    """
    Update a specific scraped record (e.g., add notes, correct data).
    
    Args:
        job_id: The job identifier.
        record_index: 0-based index of the record to update.
        updates: JSON string of fields to update, e.g. '{"notes": "verified"}'
    """
    try:
        update_dict = json.loads(updates)
    except json.JSONDecodeError:
        return json.dumps({"error": "updates must be valid JSON"})

    success = _job_manager.update_record(job_id, record_index, update_dict)
    if success:
        return json.dumps({"status": "updated", "record_index": record_index})
    return json.dumps({"error": "Record not found or update failed"})


@mcp.tool()
async def delete_record(job_id: str, record_index: int) -> str:
    """
    Delete a specific record from job results.
    
    Args:
        job_id: The job identifier.
        record_index: 0-based index of the record to delete.
    """
    success = _job_manager.delete_record(job_id, record_index)
    if success:
        return json.dumps({"status": "deleted", "record_index": record_index})
    return json.dumps({"error": "Record not found or delete failed"})


@mcp.tool()
async def search_results(job_id: str, query: str) -> str:
    """
    Full-text search across all scraped data in a job.
    
    Args:
        job_id: The job identifier.
        query: Search text.
    
    Returns:
        JSON with matching results.
    """
    data = _job_manager.get_results(job_id, page=1, page_size=100, search=query)
    return json.dumps({
        "query": query,
        "matches": data["total"],
        "results": data["results"],
    }, indent=2, default=str)


# ═══════════════════════════════════════════
#  EXPORT TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def get_export_formats() -> str:
    """
    List available export formats with descriptions.
    """
    formats = {k: v["description"] for k, v in EXPORT_FORMATS.items()}
    return json.dumps({"formats": formats}, indent=2)


@mcp.tool()
async def export_job_results(
    job_id: str,
    format: str = "json",
    filename: Optional[str] = None,
) -> str:
    """
    Export job results to a file.
    
    Args:
        job_id: The job to export.
        format: One of "json", "csv", "excel", "sqlite", "markdown".
        filename: Output filename (without extension). Auto-generated if omitted.
    
    Returns:
        JSON with the exported file path.
    """
    job = _job_manager.get_job(job_id)
    if not job:
        return json.dumps({"error": f"Job not found: {job_id}"})

    # Load all results
    all_data = _job_manager.get_results(job_id, page=1, page_size=999999)
    results = all_data.get("results", [])

    if not results:
        return json.dumps({"error": "No results to export"})

    # Determine output directory
    if job.project_path:
        output_dir = str(Path(job.project_path) / "exports")
    else:
        output_dir = str(Path(DEFAULT_STORAGE) / "exports")

    try:
        path = export_results(results, format=format, output_dir=output_dir, filename=filename)
        return json.dumps({
            "status": "exported",
            "format": format,
            "path": path,
            "records": len(results),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Export failed: {e}"})


# ═══════════════════════════════════════════
#  CONFIGURATION TOOLS
# ═══════════════════════════════════════════

@mcp.tool()
async def configure_engine(
    engine: str = "firecrawl",
    api_key: Optional[str] = None,
) -> str:
    """
    Configure a scraping engine (e.g., set Firecrawl API key).
    
    Args:
        engine: Engine to configure ("firecrawl").
        api_key: API key to set.
    """
    if engine == "firecrawl" and api_key:
        _firecrawl_engine.set_api_key(api_key)
        available, msg = await _firecrawl_engine.check_available()
        return json.dumps({
            "engine": "firecrawl",
            "configured": True,
            "available": available,
            "message": msg,
        })
    return json.dumps({"error": "Provide engine name and api_key"})


@mcp.tool()
async def get_engine_status() -> str:
    """
    Check availability and status of all scraping engines.
    """
    bs4_ok, bs4_msg = await _bs4_engine.check_available()
    fc_ok, fc_msg = await _firecrawl_engine.check_available()

    return json.dumps({
        "engines": {
            "beautifulsoup": {
                "available": bs4_ok,
                "message": bs4_msg,
                "premium": False,
                "features": ["Static HTML", "CSS selectors", "Free", "No JS rendering"],
            },
            "firecrawl": {
                "available": fc_ok,
                "message": fc_msg,
                "premium": True,
                "features": ["JS rendering", "Anti-bot bypass", "AI extraction", "Managed rate limits"],
            },
        }
    }, indent=2)


# ═══════════════════════════════════════════
#  SERVER ENTRY POINT
# ═══════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
