"""
Job Manager — Lifecycle management for scraping jobs.

Handles: creation, persistence, pause/resume, crash recovery,
progress tracking, and checkpoint management.
"""

import asyncio
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class JobConfig:
    """Scraping job configuration."""
    urls: list[str]
    engine: str = "beautifulsoup"  # "firecrawl" or "beautifulsoup"
    schema: Optional[dict] = None
    crawl_links: bool = False
    link_pattern: Optional[str] = None
    max_depth: int = 1
    max_pages: int = 50
    include_raw_html: bool = False
    search_query: Optional[str] = None  # If job started from search
    firecrawl_api_key: Optional[str] = None


@dataclass
class JobProgress:
    """Progress tracking for a scraping job."""
    total_urls: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    failed_urls: list[dict] = field(default_factory=list)  # [{url, error}]


@dataclass
class JobCheckpoint:
    """Checkpoint for crash recovery."""
    last_url_index: int = -1
    completed_urls: list[str] = field(default_factory=list)


@dataclass
class ScrapeJob:
    """A complete scraping job with state."""
    job_id: str
    name: str
    status: JobStatus
    config: JobConfig
    progress: JobProgress
    checkpoint: JobCheckpoint
    project_path: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
    results_file: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "job_id": self.job_id,
            "name": self.name,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "config": asdict(self.config) if hasattr(self.config, '__dataclass_fields__') else self.config,
            "progress": asdict(self.progress) if hasattr(self.progress, '__dataclass_fields__') else self.progress,
            "checkpoint": asdict(self.checkpoint) if hasattr(self.checkpoint, '__dataclass_fields__') else self.checkpoint,
            "project_path": self.project_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "results_file": self.results_file,
            "error": self.error,
        }
        # Strip API key from serialized output
        if isinstance(d["config"], dict):
            d["config"].pop("firecrawl_api_key", None)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ScrapeJob":
        config = d.get("config", {})
        progress = d.get("progress", {})
        checkpoint = d.get("checkpoint", {})
        return cls(
            job_id=d["job_id"],
            name=d.get("name", "Untitled"),
            status=JobStatus(d.get("status", "pending")),
            config=JobConfig(**config) if isinstance(config, dict) else config,
            progress=JobProgress(**progress) if isinstance(progress, dict) else progress,
            checkpoint=JobCheckpoint(**checkpoint) if isinstance(checkpoint, dict) else checkpoint,
            project_path=d.get("project_path"),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            completed_at=d.get("completed_at"),
            results_file=d.get("results_file"),
            error=d.get("error"),
        )


class JobManager:
    """Manages scraping job lifecycle and persistence."""

    def __init__(self, storage_dir: Optional[str] = None):
        self._storage_dir = Path(storage_dir) if storage_dir else Path("scrape_jobs")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: dict[str, ScrapeJob] = {}
        self._pause_events: dict[str, asyncio.Event] = {}  # job_id → Event (set=running, clear=paused)
        self._stop_flags: dict[str, bool] = {}
        self._load_jobs()

    def _load_jobs(self):
        """Load all job state files from disk."""
        for f in self._storage_dir.glob("*.json"):
            if f.name.endswith("_data.json"):
                continue  # Skip data files
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                job = ScrapeJob.from_dict(data)
                # Mark previously running jobs as failed (crash recovery)
                if job.status == JobStatus.RUNNING:
                    job.status = JobStatus.PAUSED
                    job.error = "Job was interrupted (server restart). Resume to continue."
                self._jobs[job.job_id] = job
            except Exception:
                pass  # Skip corrupt files

    def _save_job(self, job: ScrapeJob):
        """Persist job state to disk."""
        job.updated_at = datetime.utcnow().isoformat() + "Z"
        path = self._storage_dir / f"{job.job_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(job.to_dict(), f, indent=2, default=str)

    def _get_data_path(self, job_id: str) -> Path:
        return self._storage_dir / f"{job_id}_data.json"

    # ── Job CRUD ──

    def create_job(
        self,
        urls: list[str],
        name: str = "",
        engine: str = "beautifulsoup",
        schema: Optional[dict] = None,
        project_path: Optional[str] = None,
        **kwargs,
    ) -> ScrapeJob:
        job_id = str(uuid.uuid4())[:12]
        now = datetime.utcnow().isoformat() + "Z"

        if not name:
            name = f"Scrape {len(urls)} URL(s) — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

        config = JobConfig(
            urls=urls,
            engine=engine,
            schema=schema,
            **{k: v for k, v in kwargs.items() if k in JobConfig.__dataclass_fields__},
        )

        # Determine results file location and create job folder
        if project_path:
            # Create a job-specific folder within the project
            job_slug = name.lower().replace(' ', '_').replace('-', '_')[:30]
            job_folder = Path(project_path) / f"scrape_{job_id[:8]}_{job_slug}"
            results_dir = job_folder / "output"
            results_dir.mkdir(parents=True, exist_ok=True)
            # Save job metadata to folder
            with open(job_folder / "job_info.json", "w", encoding="utf-8") as f:
                json.dump({
                    "job_id": job_id,
                    "name": name,
                    "urls": urls,
                    "engine": engine,
                    "created_at": now,
                }, f, indent=2)
        else:
            results_dir = self._storage_dir
            results_dir.mkdir(parents=True, exist_ok=True)
        results_file = str(results_dir / f"scrape_{job_id}.json")

        job = ScrapeJob(
            job_id=job_id,
            name=name,
            status=JobStatus.PENDING,
            config=config,
            progress=JobProgress(total_urls=len(urls)),
            checkpoint=JobCheckpoint(),
            project_path=project_path,
            created_at=now,
            updated_at=now,
            results_file=results_file,
        )

        self._jobs[job_id] = job
        self._pause_events[job_id] = asyncio.Event()
        self._pause_events[job_id].set()  # Start in running state
        self._stop_flags[job_id] = False
        self._save_job(job)

        # Initialize empty results file
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({"job_id": job_id, "results": []}, f, indent=2)

        return job

    def get_job(self, job_id: str) -> Optional[ScrapeJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, project_path: Optional[str] = None) -> list[dict]:
        jobs = self._jobs.values()
        if project_path:
            jobs = [j for j in jobs if j.project_path == project_path]
        return [j.to_dict() for j in sorted(jobs, key=lambda j: j.created_at, reverse=True)]

    def delete_job(self, job_id: str) -> bool:
        job = self._jobs.pop(job_id, None)
        if not job:
            return False
        # Remove state file
        state_path = self._storage_dir / f"{job_id}.json"
        if state_path.exists():
            os.remove(state_path)
        # Remove data file
        data_path = self._get_data_path(job_id)
        if data_path.exists():
            os.remove(data_path)
        # Remove results file
        if job.results_file and os.path.exists(job.results_file):
            os.remove(job.results_file)
        self._pause_events.pop(job_id, None)
        self._stop_flags.pop(job_id, None)
        return True

    # ── Job Control ──

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status != JobStatus.RUNNING:
            return False
        job.status = JobStatus.PAUSED
        if job_id in self._pause_events:
            self._pause_events[job_id].clear()
        self._save_job(job)
        return True

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status not in (JobStatus.PAUSED, JobStatus.FAILED):
            return False
        job.status = JobStatus.RUNNING
        job.error = None
        if job_id not in self._pause_events:
            self._pause_events[job_id] = asyncio.Event()
        self._pause_events[job_id].set()
        self._stop_flags[job_id] = False
        self._save_job(job)
        return True

    def stop_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status not in (JobStatus.RUNNING, JobStatus.PAUSED):
            return False
        self._stop_flags[job_id] = True
        # Unblock pause so the loop can see the stop flag
        if job_id in self._pause_events:
            self._pause_events[job_id].set()
        job.status = JobStatus.STOPPED
        self._save_job(job)
        return True

    def is_paused(self, job_id: str) -> bool:
        return not self._pause_events.get(job_id, asyncio.Event()).is_set()

    def is_stopped(self, job_id: str) -> bool:
        return self._stop_flags.get(job_id, False)

    async def wait_if_paused(self, job_id: str):
        """Block until job is unpaused. Called from scraping loop."""
        evt = self._pause_events.get(job_id)
        if evt and not evt.is_set():
            await evt.wait()

    # ── Results Management ──

    def append_result(self, job_id: str, result: dict):
        """Append a single scraped result to the results file."""
        job = self._jobs.get(job_id)
        if not job or not job.results_file:
            return
        try:
            with open(job.results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["results"].append(result)
            with open(job.results_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def get_results(
        self, job_id: str, page: int = 1, page_size: int = 50, search: Optional[str] = None
    ) -> dict:
        """Get paginated results for a job."""
        job = self._jobs.get(job_id)
        if not job or not job.results_file or not os.path.exists(job.results_file):
            return {"results": [], "total": 0, "page": page, "page_size": page_size}

        with open(job.results_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        results = data.get("results", [])

        # Apply search filter
        if search:
            search_lower = search.lower()
            results = [
                r for r in results
                if search_lower in json.dumps(r, default=str).lower()
            ]

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "results": results[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def update_record(self, job_id: str, record_index: int, updates: dict) -> bool:
        """Update a specific record in the results."""
        job = self._jobs.get(job_id)
        if not job or not job.results_file:
            return False
        try:
            with open(job.results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            results = data.get("results", [])
            if 0 <= record_index < len(results):
                results[record_index].update(updates)
                results[record_index]["_updated_at"] = datetime.utcnow().isoformat() + "Z"
                with open(job.results_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                return True
        except Exception:
            pass
        return False

    def delete_record(self, job_id: str, record_index: int) -> bool:
        """Delete a specific record from results."""
        job = self._jobs.get(job_id)
        if not job or not job.results_file:
            return False
        try:
            with open(job.results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            results = data.get("results", [])
            if 0 <= record_index < len(results):
                results.pop(record_index)
                with open(job.results_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, default=str)
                return True
        except Exception:
            pass
        return False

    def update_checkpoint(self, job_id: str, url_index: int, url: str):
        """Update job checkpoint for crash recovery."""
        job = self._jobs.get(job_id)
        if not job:
            return
        job.checkpoint.last_url_index = url_index
        if url not in job.checkpoint.completed_urls:
            job.checkpoint.completed_urls.append(url)
        self._save_job(job)

    def mark_complete(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow().isoformat() + "Z"
            self._save_job(job)

    def mark_failed(self, job_id: str, error: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            self._save_job(job)

    def mark_running(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.RUNNING
            if job_id not in self._pause_events:
                self._pause_events[job_id] = asyncio.Event()
            self._pause_events[job_id].set()
            self._stop_flags[job_id] = False
            self._save_job(job)
