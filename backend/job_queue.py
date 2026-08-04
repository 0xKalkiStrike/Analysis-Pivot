"""Background job queue for async analysis using Redis."""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from ..core.logger import get_logger

log = get_logger(__name__)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    job_id: str
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0  # 0-100
    stage: str = ""
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    estimated_time_remaining: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class JobQueue:
    """In-memory job queue for local deployment (can be swapped with Redis)."""

    def __init__(self):
        self._jobs: dict[str, JobResult] = {}
        self._queued: list[str] = []

    def enqueue(self, job_id: str | None = None) -> str:
        """Add job to queue."""
        jid = job_id or str(uuid.uuid4())
        result = JobResult(job_id=jid)
        self._jobs[jid] = result
        self._queued.append(jid)
        log.info(f"Job enqueued: {jid}")
        return jid

    def get_job(self, job_id: str) -> JobResult | None:
        """Get job status."""
        return self._jobs.get(job_id)

    def update_progress(
        self,
        job_id: str,
        progress: float,
        stage: str = "",
        status: JobStatus = JobStatus.RUNNING,
    ) -> None:
        """Update job progress."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.progress = min(100.0, max(0.0, progress))
            job.stage = stage
            job.status = status
            job.updated_at = time.time()

    def complete_job(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark job as completed."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.progress = 100.0
            job.result = result
            job.updated_at = time.time()
            if job_id in self._queued:
                self._queued.remove(job_id)
            log.info(f"Job completed: {job_id}")

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            job.status = JobStatus.FAILED
            job.error = error
            job.updated_at = time.time()
            if job_id in self._queued:
                self._queued.remove(job_id)
            log.error(f"Job failed: {job_id} - {error}")

    def cancel_job(self, job_id: str) -> None:
        """Cancel a queued job."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            if job.status in (JobStatus.QUEUED, JobStatus.RUNNING):
                job.status = JobStatus.CANCELLED
                if job_id in self._queued:
                    self._queued.remove(job_id)
                log.info(f"Job cancelled: {job_id}")

    def next_job(self) -> str | None:
        """Get next job from queue."""
        if self._queued:
            jid = self._queued[0]
            self._queued.pop(0)
            self._jobs[jid].status = JobStatus.RUNNING
            return jid
        return None

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> None:
        """Remove completed jobs older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        expired = [
            jid for jid, job in self._jobs.items()
            if job.status == JobStatus.COMPLETED and job.created_at < cutoff
        ]
        for jid in expired:
            del self._jobs[jid]
        if expired:
            log.info(f"Cleaned up {len(expired)} old jobs")


class ProgressTracker:
    """Helper for tracking multi-stage job progress."""

    def __init__(
        self,
        job_queue: JobQueue,
        job_id: str,
        stages: list[str],
    ):
        self.queue = job_queue
        self.job_id = job_id
        self.stages = stages
        self.current_stage = 0
        self.stage_start = time.time()

    def advance_stage(self, stage_name: str | None = None) -> None:
        """Move to next stage."""
        if self.current_stage < len(self.stages):
            self.current_stage += 1
            self.stage_start = time.time()

        stage = stage_name or (self.stages[self.current_stage] if self.current_stage < len(self.stages) else "")
        progress = (self.current_stage / max(1, len(self.stages))) * 100.0
        self.queue.update_progress(self.job_id, progress, stage)

    def set_progress(self, percent: float, stage: str | None = None) -> None:
        """Set progress within current stage."""
        if stage is None:
            stage = self.stages[self.current_stage] if self.current_stage < len(self.stages) else ""
        self.queue.update_progress(self.job_id, percent, stage)

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time for current stage."""
        return time.time() - self.stage_start
